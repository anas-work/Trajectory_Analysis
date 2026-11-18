#!/usr/bin/env python3
"""Run the exported YOLOv9 pose ONNX model on one image and save a visualization.

Example:
    python infer_pose_onnx.py --image path/to/image.jpg
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort


ROOT = Path(__file__).resolve().parent
DEFAULT_MODEL = ROOT / "runs/train/yolov9s_pose_occluded_run1/weights/last_640.onnx"
CLASS_NAMES = ("player", "ball", "stumps")
KEYPOINT_COUNT = 17
KEYPOINT_OUTPUT_DIMS = 4

# =============================================================================
# IMPORTANT DEPLOYMENT THRESHOLDS
# =============================================================================
PLAYER_CLASS_ID = 0
# Player candidates below 0.10 are removed BEFORE player NMS.
PLAYER_CONF_THRESHOLD = 0.10
PLAYER_NMS_IOU_THRESHOLD = 0.70
# One findability threshold is shared by all keypoints within each class.
PLAYER_KEYPOINT_FINDABLE_THRESHOLD = 0.634  # all 17 player keypoints
STUMP_KEYPOINT_FINDABLE_THRESHOLD = 0.784   # all 6 stump keypoints
# Visibility is independent: findable + not visible means occluded.
PLAYER_KEYPOINT_VISIBLE_THRESHOLD = 0.50
STUMP_KEYPOINT_VISIBLE_THRESHOLD = 0.50
# =============================================================================

OTHER_CONF_THRESHOLD = 0.25
OTHER_NMS_IOU_THRESHOLD = 0.70
MAX_DETECTIONS = 300

PLAYER_SKELETON = (
    (15, 13), (13, 11), (16, 14), (14, 12), (11, 12),
    (5, 11), (6, 12), (5, 6), (5, 7), (6, 8), (7, 9),
    (8, 10), (1, 2), (0, 1), (0, 2), (1, 3), (2, 4),
    (3, 5), (4, 6),
)
STUMP_SKELETON = ((1, 3), (0, 5), (2, 4))
COLORS = ((0, 200, 0), (0, 165, 255), (255, 100, 0))  # BGR
OCCLUDED_COLOR = (0, 255, 255)  # BGR yellow


def letterbox(image: np.ndarray, height: int, width: int):
    """Resize without distortion and pad to the model's fixed input shape."""
    original_h, original_w = image.shape[:2]
    gain = min(width / original_w, height / original_h)
    resized_w = int(round(original_w * gain))
    resized_h = int(round(original_h * gain))
    resized = cv2.resize(
        image,
        (resized_w, resized_h),
        interpolation=cv2.INTER_LINEAR if gain > 1 else cv2.INTER_AREA,
    )
    pad_w, pad_h = width - resized_w, height - resized_h
    left, right = int(round(pad_w / 2 - 0.1)), int(round(pad_w / 2 + 0.1))
    top, bottom = int(round(pad_h / 2 - 0.1)), int(round(pad_h / 2 + 0.1))
    padded = cv2.copyMakeBorder(
        resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114)
    )
    return padded, gain, (left, top)


def box_iou(one: np.ndarray, many: np.ndarray) -> np.ndarray:
    top_left = np.maximum(one[:2], many[:, :2])
    bottom_right = np.minimum(one[2:], many[:, 2:])
    intersection = np.prod(np.maximum(bottom_right - top_left, 0), axis=1)
    one_area = np.prod(np.maximum(one[2:] - one[:2], 0))
    many_area = np.prod(np.maximum(many[:, 2:] - many[:, :2], 0), axis=1)
    return intersection / np.maximum(one_area + many_area - intersection, 1e-7)


def nms(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float) -> np.ndarray:
    """Return kept indices for one class, highest confidence first."""
    order = scores.argsort()[::-1]
    keep = []
    while order.size:
        current = order[0]
        keep.append(current)
        if order.size == 1:
            break
        remaining = order[1:]
        order = remaining[box_iou(boxes[current], boxes[remaining]) <= iou_threshold]
    return np.asarray(keep, dtype=np.int64)


def postprocess(prediction: np.ndarray):
    """Apply class-specific confidence filtering before class-aware NMS."""
    prediction = prediction.T  # [anchors, 4 + classes + 17*4]
    expected_channels = 4 + len(CLASS_NAMES) + KEYPOINT_COUNT * KEYPOINT_OUTPUT_DIMS
    if prediction.shape[1] != expected_channels:
        raise ValueError(
            f"Expected {expected_channels} output channels with keypoint layout "
            f"[x, y, findable, visible], got {prediction.shape[1]}"
        )
    xywh = prediction[:, :4]
    class_scores = prediction[:, 4:7]
    keypoints = prediction[:, 7:].reshape(-1, KEYPOINT_COUNT, KEYPOINT_OUTPUT_DIMS)

    boxes = np.empty_like(xywh)
    boxes[:, 0] = xywh[:, 0] - xywh[:, 2] / 2
    boxes[:, 1] = xywh[:, 1] - xywh[:, 3] / 2
    boxes[:, 2] = xywh[:, 0] + xywh[:, 2] / 2
    boxes[:, 3] = xywh[:, 1] + xywh[:, 3] / 2

    detections = []
    for class_id in range(len(CLASS_NAMES)):
        # This is deliberately done before NMS. For players, the value is 0.10.
        confidence_threshold = (
            PLAYER_CONF_THRESHOLD if class_id == PLAYER_CLASS_ID else OTHER_CONF_THRESHOLD
        )
        iou_threshold = (
            PLAYER_NMS_IOU_THRESHOLD if class_id == PLAYER_CLASS_ID else OTHER_NMS_IOU_THRESHOLD
        )
        scores = class_scores[:, class_id]
        candidates = np.flatnonzero(scores >= confidence_threshold)
        if not candidates.size:
            continue
        kept = candidates[nms(boxes[candidates], scores[candidates], iou_threshold)]
        detections.extend(
            (boxes[index], float(scores[index]), class_id, keypoints[index]) for index in kept
        )

    detections.sort(key=lambda item: item[1], reverse=True)
    return detections[:MAX_DETECTIONS]


def restore_coordinates(detections, gain: float, pad, image_shape):
    """Map boxes and keypoints from letterboxed input back to the source image."""
    image_h, image_w = image_shape[:2]
    for box, _, _, keypoints in detections:
        box[[0, 2]] = (box[[0, 2]] - pad[0]) / gain
        box[[1, 3]] = (box[[1, 3]] - pad[1]) / gain
        box[[0, 2]] = box[[0, 2]].clip(0, image_w - 1)
        box[[1, 3]] = box[[1, 3]].clip(0, image_h - 1)
        keypoints[:, 0] = ((keypoints[:, 0] - pad[0]) / gain).clip(0, image_w - 1)
        keypoints[:, 1] = ((keypoints[:, 1] - pad[1]) / gain).clip(0, image_h - 1)


def keypoint_states(class_id: int, keypoints: np.ndarray):
    """Return active, visible, and occluded masks for one detection."""
    if class_id == PLAYER_CLASS_ID:
        point_count = 17
        skeleton = PLAYER_SKELETON
        findable_threshold = PLAYER_KEYPOINT_FINDABLE_THRESHOLD
        visible_threshold = PLAYER_KEYPOINT_VISIBLE_THRESHOLD
    elif class_id == 2:
        point_count = 6
        skeleton = STUMP_SKELETON
        findable_threshold = STUMP_KEYPOINT_FINDABLE_THRESHOLD
        visible_threshold = STUMP_KEYPOINT_VISIBLE_THRESHOLD
    else:
        point_count = 0
        skeleton = ()
        findable_threshold = visible_threshold = 1.0

    points = keypoints[:point_count]
    findable = points[:, 2] >= findable_threshold
    visible = findable & (points[:, 3] >= visible_threshold)
    occluded = findable & ~visible
    return points, skeleton, findable, visible, occluded


def draw(image: np.ndarray, detections) -> np.ndarray:
    output = image.copy()
    for box, score, class_id, keypoints in detections:
        color = COLORS[class_id]
        x1, y1, x2, y2 = np.rint(box).astype(int)
        cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            output, f"{CLASS_NAMES[class_id]} {score:.2f}", (x1, max(y1 - 7, 18)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA,
        )

        points, skeleton, findable, visible, occluded = keypoint_states(class_id, keypoints)
        if not len(points):
            continue
        for first, second in skeleton:
            if findable[first] and findable[second]:
                start = tuple(np.rint(points[first, :2]).astype(int))
                end = tuple(np.rint(points[second, :2]).astype(int))
                cv2.line(output, start, end, color, 2, cv2.LINE_AA)
        for index in np.flatnonzero(visible):
            point = tuple(np.rint(points[index, :2]).astype(int))
            cv2.circle(output, point, 3, color, -1, cv2.LINE_AA)
        for index in np.flatnonzero(occluded):
            point = tuple(np.rint(points[index, :2]).astype(int))
            cv2.circle(output, point, 4, OCCLUDED_COLOR, -1, cv2.LINE_AA)
    return output


def keypoint_payload(detections):
    """Serialize visible and occluded keypoints into separate lists."""
    output = []
    for box, score, class_id, keypoints in detections:
        points, _, _, visible, occluded = keypoint_states(class_id, keypoints)

        def records(mask):
            return [
                {
                    "index": int(index),
                    "x": float(points[index, 0]),
                    "y": float(points[index, 1]),
                    "findable_score": float(points[index, 2]),
                    "visible_score": float(points[index, 3]),
                }
                for index in np.flatnonzero(mask)
            ]

        output.append({
            "class_id": int(class_id),
            "class_name": CLASS_NAMES[class_id],
            "confidence": float(score),
            "box_xyxy": [float(value) for value in box],
            "visible_keypoints": records(visible),
            "occluded_keypoints": records(occluded),
        })
    return output


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True, help="One input image")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL, help="Exported ONNX model")
    parser.add_argument("--output", type=Path, help="Annotated image path")
    parser.add_argument(
        "--keypoints-output", type=Path,
        help="JSON output path (default: <image>_pose_keypoints.json)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    image = cv2.imread(str(args.image))
    if image is None:
        raise FileNotFoundError(f"Could not read image: {args.image}")
    if not args.model.is_file():
        raise FileNotFoundError(f"Could not find model: {args.model}")

    session = ort.InferenceSession(str(args.model), providers=["CPUExecutionProvider"])
    model_input = session.get_inputs()[0]
    _, channels, input_h, input_w = model_input.shape
    if channels != 3 or not isinstance(input_h, int) or not isinstance(input_w, int):
        raise ValueError(f"Expected a static NCHW image input, got {model_input.shape}")

    padded, gain, pad = letterbox(image, input_h, input_w)
    tensor = padded[:, :, ::-1].transpose(2, 0, 1)  # BGR HWC -> RGB CHW
    tensor = np.ascontiguousarray(tensor, dtype=np.float32)[None] / 255.0
    prediction = session.run(None, {model_input.name: tensor})[0][0]

    detections = postprocess(prediction)
    restore_coordinates(detections, gain, pad, image.shape)
    visualization = draw(image, detections)

    output = args.output or args.image.with_name(f"{args.image.stem}_pose.jpg")
    output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output), visualization):
        raise OSError(f"Could not write output image: {output}")
    keypoints_output = args.keypoints_output or args.image.with_name(
        f"{args.image.stem}_pose_keypoints.json"
    )
    keypoints_output.parent.mkdir(parents=True, exist_ok=True)
    payload = keypoint_payload(detections)
    with keypoints_output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    counts = {name: sum(item[2] == index for item in detections)
              for index, name in enumerate(CLASS_NAMES)}
    visible_count = sum(len(item["visible_keypoints"]) for item in payload)
    occluded_count = sum(len(item["occluded_keypoints"]) for item in payload)
    print(f"Saved: {output.resolve()}")
    print(f"Keypoints: {keypoints_output.resolve()}")
    print(f"Detections: {counts}")
    print(f"Keypoint states: visible={visible_count}, occluded={occluded_count}")
    print("IMPORTANT deployment thresholds:")
    print(f"Player confidence threshold before NMS: {PLAYER_CONF_THRESHOLD:.2f}")
    print(f"Player keypoint findable threshold: {PLAYER_KEYPOINT_FINDABLE_THRESHOLD:.3f}")
    print(f"Player keypoint visible threshold: {PLAYER_KEYPOINT_VISIBLE_THRESHOLD:.3f}")
    print(f"Stump keypoint findable threshold: {STUMP_KEYPOINT_FINDABLE_THRESHOLD:.3f}")
    print(f"Stump keypoint visible threshold: {STUMP_KEYPOINT_VISIBLE_THRESHOLD:.3f}")


if __name__ == "__main__":
    main()
