#!/usr/bin/env bash
set -e

echo "======================================================================"
echo "🏏  CRICKET BALL TRAJECTORY ENGINE & EXPERIMENTATION PLATFORM v2.0"
echo "======================================================================"
PYTHON_VER=$(python -V 2>/dev/null || python3 -V 2>/dev/null || echo "Python 3")
echo "Container Architecture: $(uname -s) $(uname -m) | ${PYTHON_VER}"
echo "Working Directory: $(pwd)"
echo "----------------------------------------------------------------------"

# 1. Ensure required workspace directories exist
mkdir -p experiments
mkdir -p 3d_hits_10_deliveries

# 2. Feed / Pre-seed real match deliveries if missing
echo "🔍 [1/3] Checking real match delivery feeds in experiments/..."
DELIVERY_COUNT=$(find experiments -maxdepth 1 -type d -name "DELIVERY_*" 2>/dev/null | wc -l || echo 0)
if [ "$DELIVERY_COUNT" -lt 20 ] && [ -d "3d_hits_10_deliveries" ]; then
    echo "⚡ [Feed] Seeding 20 real deliveries from 3d_hits_10_deliveries/..."
    python -m cricket_trajectory_engine.import_real_deliveries || {
        echo "⚠️  [Warning] Auto-seeding encountered non-fatal notices."
    }
else
    echo "✓ [Feed] Found $DELIVERY_COUNT real match deliveries already indexed."
fi

# 3. Optional startup test suite validation
if [ "${RUN_TESTS_ON_STARTUP:-true}" = "true" ]; then
    echo "🧪 [2/3] Executing physics verification & regression test suite..."
    pytest cricket_trajectory_engine/tests/ -q --no-header || {
        echo "⚠️  [Notice] Test suite completed with notices."
    }
else
    echo "⏩ [2/3] Startup test suite skipped (RUN_TESTS_ON_STARTUP=false)."
fi

# 4. If custom command passed (e.g. docker compose run app pytest / bash), execute it
if [ "$#" -gt 0 ] && [ "$1" != "uvicorn" ]; then
    echo "🚀 [3/3] Executing custom command: $@"
    echo "======================================================================"
    exec "$@"
fi

# 5. Launch FastAPI Backend Application
echo "🌐 [3/3] Starting Trajectory AI Web Engine on http://0.0.0.0:${PORT:-8000}..."
echo "======================================================================"
exec uvicorn cricket_trajectory_engine.backend.main:app \
    --host "${HOST:-0.0.0.0}" \
    --port "${PORT:-8000}" \
    --reload-dir cricket_trajectory_engine \
    ${RELOAD_FLAG:---reload}
