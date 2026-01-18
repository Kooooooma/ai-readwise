"""
AI-Readwise Web Application

A web application for managing and reading PDF books converted to markdown.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import uvicorn
import logging

from backend.api import router as api_router, extract_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup: clean up any unfinished tasks from previous run
    logger.info("[App] Starting up, cleaning unfinished tasks...")
    cleaned = extract_service.cleanup_on_shutdown()
    if cleaned > 0:
        logger.info(f"[App] Cleaned up {cleaned} unfinished task(s) from previous run")
    
    yield  # Application is running
    
    # Shutdown: clean up any in-progress tasks
    logger.info("[App] Shutting down, cleaning up extraction tasks...")
    extract_service.cleanup_on_shutdown()
    logger.info("[App] Cleanup complete")


# Create FastAPI app with lifespan
app = FastAPI(
    title="AI-Readwise",
    description="PDF to Markdown reading application",
    version="1.0.0",
    lifespan=lifespan
)

# Include API routes
app.include_router(api_router)

# Serve frontend static files
FRONTEND_DIR = Path(__file__).parent / "frontend" / "dist"

if FRONTEND_DIR.exists():
    # Serve static assets
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")
    
    # Serve index.html for all non-API routes (SPA support)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the SPA for all non-API routes."""
        # Don't serve index.html for API routes
        if full_path.startswith("api/"):
            return {"error": "Not found"}
        
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"error": "Frontend not built. Run 'cd frontend && npm run build'"}
else:
    @app.get("/")
    async def root():
        """Root endpoint when frontend is not built."""
        return {
            "message": "AI-Readwise API",
            "docs": "/docs",
            "note": "Frontend not built. Run 'cd frontend && npm run build'"
        }


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
