from __future__ import annotations

from fastapi import FastAPI, Request
from starlette.responses import RedirectResponse
from app.config.logger_config import setup_logger

logger = setup_logger(__name__)
router = None  # This module doesn't use a router


def setup_error_handlers(app: FastAPI):
    """Setup custom error handlers for the FastAPI app."""
    
    @app.exception_handler(404)
    async def custom_404_handler(request: Request, exc):
        original_path = request.url.path
        redirect_url = f"/#/not-found{original_path}"
        logger.warning(f"404 Not Found: {original_path}")
        return RedirectResponse(url=redirect_url)

