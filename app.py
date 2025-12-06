"""
Author       : Ravikumar Pawar
Email        : ravi.ravipawar17@gmail.com
Application  : Kannada Spellcheck Application
Description  : Kannada language spellchecking backend using FastAPI. Supports
               file uploads, SymSpell/BLOOM integration, and user management.
"""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI, Request, File, UploadFile, HTTPException
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
    get_redoc_html,
)
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from config.database import Base, engine
from config.logger_config import setup_logger
from routers import (
    user,
    dictionary,
    bloom_api,
    symspell_api,
    user_added_words_api,
)
from routers.bloom_api import bloom_initialization, bloom_reinitialization
from security.app_security import add_security_middleware
from security.auth import admin_auth_required, create_default_admin
from symspell.sym_spell import symspell_initialization
from utilities.read_file_content import filter_words_from_file, count_word_frequency

# -----------------------------
# Logger
# -----------------------------
logger = setup_logger(__name__)
logger.info("Application initializing...")

# -----------------------------
# FastAPI Lifespan
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Ensure DB tables exist
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified.")

        # Initialize BLOOM
        await bloom_initialization()
        logger.info("BLOOM initialized.")

        # Initialize SymSpell
        symspell_initialization()
        logger.info("SymSpell initialized.")

        # Create default admin if not exists
        await create_default_admin()
        logger.info("Default admin ensured.")

        yield
    finally:
        logger.info("Application shutdown complete.")


# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI(
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    title="Spellcheck",
    description="Spellcheck application for Kannada language",
    root_path="/kaagunitha",
)

# -----------------------------
# Swagger & ReDoc
# -----------------------------
@app.get("/swagger", include_in_schema=False, dependencies=[Depends(admin_auth_required)])
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/kaagunitha/static/js/swagger-ui-bundle.js",
        swagger_css_url="/kaagunitha/static/css/swagger-ui.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="/kaagunitha/static/js/swagger-ui-bundle.js",
    )


# -----------------------------
# Middleware
# -----------------------------
add_security_middleware(app)

# -----------------------------
# Routers
# -----------------------------
app.include_router(user.router, prefix="/user/api/v1", tags=["User"])
app.include_router(dictionary.router, prefix="/dictionary/api/v1", tags=["Dictionary"])
app.include_router(bloom_api.router, prefix="/bloom/api/v1", tags=["BLOOM API"])
app.include_router(symspell_api.router, prefix="/symspell/api/v1", tags=["SymSpell API"])
app.include_router(user_added_words_api.router, prefix="/user-added/api/v1", tags=["User Added"])

# -----------------------------
# Static & Template Setup
# -----------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")

templates = Jinja2Templates(directory="templates")


# -----------------------------
# Routes
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/admin/reload", dependencies=[Depends(admin_auth_required)])
async def reload_bloom_symspell():
    logger.info("Admin triggered BLOOM and SymSpell reload.")
    await bloom_reinitialization()
    symspell_initialization()
    return {"message": "BLOOM and SymSpell reinitialized successfully"}


@app.get("/admin/validate", dependencies=[Depends(admin_auth_required)])
async def validate_admin():
    logger.info("Admin validated successfully.")
    return {"message": "Admin authentication successful"}


@app.post("/upload/", response_model=dict)
async def upload_file(file: UploadFile = File(...)):
    """Upload a text or DOCX file and extract words."""
    try:
        words = await filter_words_from_file(file)
        logger.info(f"File uploaded: {file.filename}, extracted {len(words)} words.")
        return {"wrong_words": words}
    except Exception as e:
        logger.exception("Error processing uploaded file.")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@app.post("/word-frequency/data", dependencies=[Depends(admin_auth_required)], response_model=dict)
async def word_frequency(file: UploadFile = File(...)):
    """Upload a file and compute word frequencies."""
    try:
        freq_data = await count_word_frequency(file)
        logger.info(f"Word frequency computed for file: {file.filename}")
        return freq_data
    except Exception as e:
        logger.exception("Error computing word frequency.")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


# -----------------------------
# Custom 404 Handler
# -----------------------------
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    original_path = request.url.path
    redirect_url = f"/#/not-found{original_path}"
    logger.warning(f"404 Not Found: {original_path}")
    return RedirectResponse(url=redirect_url)


# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    #uvicorn.run("app:app", host="0.0.0.0", port=8443, reload=True)
    print("Running app with uvicorn...")
