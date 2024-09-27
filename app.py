from contextlib import asynccontextmanager

from fastapi import Depends
from fastapi import FastAPI
from fastapi import File, UploadFile
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware  # Import CORSMiddleware

from auth import admin_auth_required
from database import Base, engine
from logger_config import setup_logger
from routers import user, dictionary, bloom_api, symspell_api, user_added_words_api
from routers.bloom_api import bloom_initialization, bloom_reinitialization
from symspell.sym_spell import symspell_initialization
from utilities.read_file_content import filter_words_from_file

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

# Allow CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can specify allowed origins here
    allow_credentials=True,
    allow_methods=["*"],  # You can specify allowed methods here
    allow_headers=["*"],  # You can specify allowed headers here
)

# Include the routers from the modules
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(dictionary.router, prefix="/dictionary/api/v1", tags=["Dictionary"])
app.include_router(bloom_api.router, prefix="/bloom/api/v1", tags=['BLOOM API'])
app.include_router(symspell_api.router, prefix="/symspell/api/v1", tags=['SymSpell API'])
app.include_router(user_added_words_api.router, prefix="/user-added/api/v1", tags=['User Added'])


@app.get("/")
def read_root():
    return {"message": "Welcome to the API"}


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


if __name__ == "__main__":
    print("Running app with uvicorn...")
