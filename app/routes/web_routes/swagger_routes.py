from __future__ import annotations

from fastapi import FastAPI, Depends
from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html, get_redoc_html

from app.services.security_service.auth import admin_auth_required


def setup_swagger_routes(app: FastAPI):
    """Setup custom Swagger and ReDoc routes for the FastAPI app."""
    
    @app.get("/swagger", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=str(app.openapi_url),
            title=f"{app.title} - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="/static/js/swagger-ui-bundle.js",
            swagger_css_url="/static/css/swagger-ui.css",
        )

    @app.get(str(app.swagger_ui_oauth2_redirect_url), include_in_schema=False)
    async def swagger_ui_redirect():
        return get_swagger_ui_oauth2_redirect_html()

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=str(app.openapi_url),
            title=f"{app.title} - ReDoc",
            redoc_js_url="/static/js/swagger-ui-bundle.js",
        )
