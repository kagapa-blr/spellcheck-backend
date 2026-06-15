from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from sqlalchemy import inspect
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from app.config.database import init_engine, get_engine
from app.config.logger_config import setup_logger
from app.routes.api_routes.admin_activities import admin_activities_router
from app.routes.api_routes.bloom_filter_routes import (
    bloom_initialization,
    bloom_router,
)
from app.routes.api_routes.dictionary_routes import dictionary_router
from app.routes.api_routes.manage_admins import manage_admin_router
from app.routes.api_routes.symspell_routes import symspell_router
from app.routes.web_routes.error_routes import setup_error_handlers
from app.routes.web_routes.swagger_routes import swagger_router
from app.services.security_service.app_security import add_security_middleware
from app.services.security_service.auth import create_default_admin
from app.services.symspell_service.symspell_service import symspell_initialization

# --------------------------------------------------
# Paths
# --------------------------------------------------

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

APP_DIR = os.path.join(ROOT_DIR, "app")

STATIC_DIR = os.path.join(APP_DIR, "static")
ASSETS_DIR = os.path.join(STATIC_DIR, "assets")
IMAGES_DIR = os.path.join(STATIC_DIR, "images")
TEMPLATES_DIR = os.path.join(APP_DIR, "templates")

# --------------------------------------------------
# Logger
# --------------------------------------------------

logger = setup_logger(__name__)


# --------------------------------------------------
# Lifespan
# --------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Initialize DB engine and sessionmaker before using DB
        init_engine()
        inspector = inspect(get_engine())

        if not inspector.get_table_names():
            raise RuntimeError("Database has no tables. Run Alembic migrations first.")

        # Database engine/session initialized. Schedule heavy background
        # initializations (BLOOM, SymSpell) to run asynchronously so startup
        # is not blocked. These will run after DB is ready.

        loop = asyncio.get_event_loop()

        # Run initializations sequentially in a background task so startup isn't blocked.
        # Delay between stages can be configured via INIT_DELAY_SECONDS env var.
        try:
            init_delay = int(os.getenv("INIT_DELAY_SECONDS", "2"))
        except Exception:
            init_delay = 2

        loop.create_task(_run_init_sequence(init_delay))

        logger.info("Database engine initialized; scheduled background initializations")

        yield

    finally:
        logger.info("Application shutdown complete")


async def _safe_run_async(name: str, coro_func):
    try:
        await coro_func()
        logger.info(f"Background init '{name}' completed successfully")
    except Exception as e:
        logger.error(f"Background init '{name}' failed: {e}", exc_info=True)


async def _safe_run_thread(name: str, func):
    try:
        await asyncio.to_thread(func)
        logger.info(f"Background init '{name}' completed successfully")
    except Exception as e:
        logger.error(f"Background init '{name}' failed: {e}", exc_info=True)


async def _run_init_sequence(delay_seconds: int = 2):
    """Run Bloom initialization, wait `delay_seconds`, then run SymSpell init."""
    try:
        logger.info(
            "Starting sequential background initialization: Bloom -> sleep -> SymSpell"
        )

        # Ensure default admin exists before other inits
        try:
            await create_default_admin()
            logger.info("Default admin creation/verification completed")
        except Exception as e:
            logger.error(f"Default admin creation failed: {e}", exc_info=True)

        # Bloom (async)
        try:
            await bloom_initialization()
            logger.info("Bloom initialization completed in sequence")
        except Exception as e:
            logger.error(f"Bloom initialization failed in sequence: {e}", exc_info=True)

        # Wait a bit to let resources stabilize
        if delay_seconds > 0:
            logger.info(
                f"Waiting {delay_seconds}s before starting SymSpell initialization"
            )
            await asyncio.sleep(delay_seconds)

        # SymSpell (run in thread to avoid blocking)
        try:
            await asyncio.to_thread(symspell_initialization)
            logger.info("SymSpell initialization completed in sequence")
        except Exception as e:
            logger.error(
                f"SymSpell initialization failed in sequence: {e}", exc_info=True
            )

        logger.info("Sequential background initialization finished")
    except Exception as e:
        logger.error(f"Error in initialization sequence: {e}", exc_info=True)


# --------------------------------------------------
# FastAPI App
# --------------------------------------------------

app = FastAPI(
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    title="Spellcheck",
    description="Spellcheck application for Kannada language",
)

# --------------------------------------------------
# Static Files
# --------------------------------------------------

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

# --------------------------------------------------
# Templates
# --------------------------------------------------

templates = Jinja2Templates(directory=TEMPLATES_DIR)

# --------------------------------------------------
# Middleware
# --------------------------------------------------

add_security_middleware(app)

# --------------------------------------------------
# Error Handlers / Swagger
# --------------------------------------------------

setup_error_handlers(app)


# --------------------------------------------------
# Routers
# --------------------------------------------------

app.include_router(manage_admin_router, prefix="/admin/api/v1", tags=["ADMINS"])
app.include_router(dictionary_router, prefix="/dictionary/api/v1", tags=["Dictionary"])
app.include_router(bloom_router, prefix="/bloom/api/v1", tags=["BLOOM API"])
app.include_router(symspell_router, prefix="/symspell/api/v1", tags=["SymSpell API"])
app.include_router(
    admin_activities_router, prefix="/admin/api/v1/activity", tags=["Admin Activities"]
)
app.include_router(swagger_router,prefix="/documentation",tags=["Swagger"])


# --------------------------------------------------
# Home Page
# --------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


# --------------------------------------------------
# Startup
# --------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        reload=False,
    )
