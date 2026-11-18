import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { formatTimestamp, getOutcomeClass, getOutcomeBadgeColor, isDeliveryRecord } from '../src/utils/formatters.js';
import { anglesToCartesian, cartesianToAngles, calculateDerivedBallProperties, normalizeTrajectory } from '../src/utils/math.js';
import { quickScenarios, turfPresets, fieldingPresetsData } from '../src/services/presets.js';

describe('Frontend Formatters', () => {
  test('formatTimestamp handles valid ISO strings and empties', () => {
    assert.equal(formatTimestamp(''), 'Just now');
    assert.equal(formatTimestamp(null), 'Just now');
    const res = formatTimestamp('2026-11-05T08:58:49Z');
    assert.match(res, /2026/);
  });

  test('getOutcomeClass returns appropriate badge classes', () => {
    assert.ok(getOutcomeClass('SIX').includes('outcome-six'));
    assert.ok(getOutcomeClass('FOUR (BOUNDARY)').includes('outcome-four'));
    assert.ok(getOutcomeClass('CAUGHT').includes('outcome-out'));
    assert.ok(getOutcomeClass('IN_PLAY').includes('outcome-inplay'));
  });

  test('isDeliveryRecord accurately detects seeded deliveries', () => {
    assert.equal(isDeliveryRecord({ id: 'DELIVERY_01_CAM1' }), true);
    assert.equal(isDeliveryRecord({ is_seeded_delivery: true }), true);
    assert.equal(isDeliveryRecord({ tags: ['real_delivery'] }), true);
    assert.equal(isDeliveryRecord({ id: 'SIM_9921' }), false);
  });
});

describe('Frontend Math & Kinematics', () => {
  test('anglesToCartesian accurately converts speed and angles', () => {
    // 30 m/s at 0 deg elevation and 0 deg azimuth -> vx=30, vy=0, vz=0
    const res = anglesToCartesian(30.0, 0.0, 0.0);
    assert.ok(Math.abs(res.vx - 30.0) < 1e-4);
    assert.ok(Math.abs(res.vy) < 1e-4);
    assert.ok(Math.abs(res.vz) < 1e-4);

    // 30 m/s at 90 deg elevation -> vx=0, vy=0, vz=30
    const vert = anglesToCartesian(30.0, 90.0, 0.0);
    assert.ok(Math.abs(vert.vx) < 1e-4);
    assert.ok(Math.abs(vert.vz - 30.0) < 1e-4);
  });

  test('cartesianToAngles accurately reverses cartesian vectors', () => {
    const a = cartesianToAngles(26.49, 0.0, 14.08);
    assert.ok(Math.abs(a.speed - 30.0) < 0.2);
    assert.ok(Math.abs(a.elevation - 28.0) < 0.5);
  });

  test('calculateDerivedBallProperties computes radius, area, and MOI', () => {
    const props = calculateDerivedBallProperties(0.156, 0.072);
    assert.equal(props.radius, 0.036);
    assert.ok(Math.abs(props.crossSectionArea - Math.PI * 0.036 * 0.036) < 1e-6);
    assert.ok(Math.abs(props.momentOfInertia - 0.4 * 0.156 * 0.036 * 0.036) < 1e-7);
  });

  test('normalizeTrajectory standardizes trajectory objects into 8-tuples', () => {
    const rawObjs = [
      { t: 0.0, x: 0.0, y: 0.0, z: 0.9, vx: 30, vy: 0, vz: 10, phase: 0 },
      { t: 0.1, x: 3.0, y: 0.0, z: 1.8, vx: 29, vy: 0, vz: 8, phase: 0 },
    ];
    const norm = normalizeTrajectory(rawObjs);
    assert.equal(norm.length, 2);
    assert.deepEqual(norm[0], [0.0, 0.0, 0.0, 0.9, 30, 0, 10, 0]);
  });
});

describe('Presets and Fielding Rules', () => {
  test('fieldingPresetsData contains standard presets with 11 fielders each', () => {
    assert.equal(fieldingPresetsData.powerplay.length, 11);
    assert.equal(fieldingPresetsData.attacking.length, 11);
    assert.equal(fieldingPresetsData.middle_overs.length, 11);
    assert.equal(fieldingPresetsData.death_overs.length, 11);
  });

  test('quickScenarios contains 4 standard scenarios', () => {
    assert.ok(quickScenarios.straight_six);
    assert.ok(quickScenarios.cover_boundary);
    assert.ok(quickScenarios.skier_catch);
    assert.ok(quickScenarios.deep_sweep);
  });
});
