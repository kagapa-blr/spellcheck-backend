from __future__ import annotations

from fastapi import APIRouter, Request, Depends
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
    get_redoc_html,
)

from app.config.logger_config import setup_logger
from app.dbmodels.models import User
from app.services.security_service.auth import login_required

swagger_router = APIRouter()

logger = setup_logger(module_name=__name__)


@swagger_router.get("/swagger", include_in_schema=False)
async def custom_swagger_ui_html(
        request: Request,
        current_user: User = Depends(login_required),
):
    app = request.app

    logger.info(
        f"Swagger page accessed by {current_user.username}"
    )

    return get_swagger_ui_html(
        openapi_url=str(app.openapi_url),
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/js/swagger-ui-bundle.js",
        swagger_css_url="/static/css/swagger-ui.css",
    )


@swagger_router.get(
    "/docs/oauth2-redirect",
    include_in_schema=False,
)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@swagger_router.get("/redoc", include_in_schema=False)
async def redoc_html(request: Request):
    app = request.app

    return get_redoc_html(
        openapi_url=str(app.openapi_url),
        title=f"{app.title} - ReDoc",
        redoc_js_url="/static/js/redoc.standalone.js",
    )
