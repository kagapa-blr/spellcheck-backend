from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import Base, engine
from routers import user, dictionary, bloom_api, symspell_api, user_added_words_api
from routers.bloom_api import bloom_initialization, bloom_reinitialization
from symspell.sym_spell import symspell_initialization


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # Ensure tables are created on startup
    await bloom_initialization()
    # Load the dictionary into SymSpell on startup
    symspell_initialization()
    yield
    print("application stopped")


app = FastAPI(lifespan=lifespan)
# Include the routers from the modules
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(dictionary.router, prefix="/dictionary/api/v1", tags=["Dictionary"])
app.include_router(bloom_api.router, prefix="/bloom/api/v1", tags=['BLOOM API'])
app.include_router(symspell_api.router, prefix="/symspell/api/v1", tags=['SymSpell API'])
app.include_router(user_added_words_api.router, prefix="/user-added/api/v1", tags=['User Added'])


@app.get("/")
def read_root():
    return {"message": "Welcome to the API"}


@app.get("/admin/reload")
async def reload_bloom_symspell():
    await bloom_reinitialization()
    # Load the dictionary into SymSpell on startup
    symspell_initialization()
    return {"message": "Bloom and SymSpell reinitialized successfully"}


if __name__ == "__main__":
    print("Running app with uvicorn...")
