# app.py
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, File, UploadFile, HTTPException
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from security.app_security import add_security_middleware
from security.auth import admin_auth_required
from config.database import Base, engine
from config.logger_config import setup_logger
from routers import user, dictionary, bloom_api, symspell_api, user_added_words_api
from routers.bloom_api import bloom_initialization, bloom_reinitialization
from symspell.sym_spell import symspell_initialization
from utilities.read_file_content import filter_words_from_file, count_word_frequency

# Set up logger with the module name
logger = setup_logger(__name__)
logger.info('Initializing')


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # Ensure tables are created on startup
    await bloom_initialization()
    # Load the dictionary into SymSpell on startup
    symspell_initialization()
    yield
    print("application stopped")


app = FastAPI(lifespan=lifespan)

# Add security middleware
add_security_middleware(app)

# Include the routers from the modules
app.include_router(user.router, prefix="/user/api/v1", tags=["User"])
app.include_router(dictionary.router, prefix="/dictionary/api/v1", tags=["Dictionary"])
app.include_router(bloom_api.router, prefix="/bloom/api/v1", tags=['BLOOM API'])
app.include_router(symspell_api.router, prefix="/symspell/api/v1", tags=['SymSpell API'])
app.include_router(user_added_words_api.router, prefix="/user-added/api/v1", tags=['User Added'])

# Serve static files from the 'static' directory
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up the Jinja2 templates directory
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/admin/reload", dependencies=[Depends(admin_auth_required)])
async def reload_bloom_symspell():
    logger.info('bloom and sysmpell reload triggered')
    await bloom_reinitialization()
    # Load the dictionary into SymSpell on startup
    symspell_initialization()
    return {"message": "Bloom and SymSpell reinitialized successfully"}


@app.get('/admin/validate', dependencies=[Depends(admin_auth_required)])
async def validate_admin():
    return {"message": "Admin authentication successful"}


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)) -> dict:
    """
    Endpoint to upload a .txt or .docx file and extract words from it.

    Args:
        file (UploadFile): The uploaded file.

    Returns:
        dict: A JSON object containing the list of words extracted from the file.
    """
    try:
        data = await filter_words_from_file(file)
        return {"wrong_words": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@app.post('/word-frequency/data')
async def word_frequency(file: UploadFile = File(...)) -> dict:
    """
    Endpoint to upload a.txt or.docx file and calculate word frequencies.

    Args:
        file (UploadFile): The uploaded file.

    Returns:
        dict: A JSON object containing the word frequencies.
    """
    try:
        data = await count_word_frequency(file)
        if data:
            return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


if __name__ == "__main__":
    print("Running app with uvicorn...")
