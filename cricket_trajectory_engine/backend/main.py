"""
FastAPI Backend Application Entrypoint.
Serves REST APIs and the interactive WebGL Three.js frontend.
"""

import os
import sys

# Ensure root directory is on PYTHONPATH:
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from cricket_trajectory_engine.backend.api.simulation_api import router as simulation_router
from cricket_trajectory_engine.backend.api.experiments_api import router as experiments_router
from cricket_trajectory_engine.backend.api.fielding_api import router as fielding_router
from cricket_trajectory_engine.backend.api.comparison_api import router as comparison_router

app = FastAPI(
    title="Interactive 3D Cricket Ball Trajectory Platform",
    description="Scientifically grounded cricket trajectory simulator, experimentation engine, and formula explorer.",
    version="2.0.0",
)

# Enable CORS:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST Routers:
app.include_router(simulation_router)
app.include_router(experiments_router)
app.include_router(fielding_router)
app.include_router(comparison_router)

# Mount Experiments artifact folder for video & CSV streaming:
experiments_dir = os.path.abspath("experiments")
os.makedirs(experiments_dir, exist_ok=True)
app.mount("/artifacts", StaticFiles(directory=experiments_dir), name="artifacts")

# Mount Frontend static directory:
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
os.makedirs(frontend_dir, exist_ok=True)

# Mount /assets if present (for production bundle and public assets):
dist_assets = os.path.join(frontend_dir, "dist", "assets")
if os.path.exists(dist_assets):
    app.mount("/assets", StaticFiles(directory=dist_assets), name="assets")
elif os.path.exists(os.path.join(frontend_dir, "public", "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dir, "public", "assets")), name="assets")


@app.on_event("startup")
def ensure_real_deliveries_seeded():
    """Ensures all 10 real deliveries across CAM1 and CAM2 are populated into experiments archive."""
    try:
        from cricket_trajectory_engine.import_real_deliveries import import_all_real_deliveries
        existing_deliveries = [d for d in os.listdir("experiments") if d.startswith("DELIVERY_")]
        if len(existing_deliveries) < 20:
            print("[Startup] Seeding real deliveries into experiment archive...")
            import_all_real_deliveries()
            print(f"[Startup] Real delivery seeding complete ({len(existing_deliveries)} -> 20 deliveries).")
    except Exception as e:
        print(f"[Startup Warning] Could not auto-seed real deliveries: {e}")


@app.get("/")
def serve_frontend_index():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Cricket Trajectory Platform API operational", "docs": "/docs"}


if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


def start_server(host: str = None, port: int = None):
    import uvicorn
    if host is None:
        host = os.getenv("HOST", "0.0.0.0")
    if port is None:
        port = int(os.getenv("PORT", "8000"))
    reload_flag = os.getenv("RELOAD", "true").lower() in ("true", "1", "yes")
    uvicorn.run("cricket_trajectory_engine.backend.main:app", host=host, port=port, reload=reload_flag)


if __name__ == "__main__":
    start_server()

