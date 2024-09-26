from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import Base, engine
from routers import user, dictionary, get_api_router, post_api_router, bloom_api, symspell_api
from routers.bloom_api import bloom_initialization
from suggestion.sym_spell import symspell_initialization


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
app.include_router(get_api_router.router, tags=['GET API'])
app.include_router(post_api_router.router, tags=['POST API'])
app.include_router(bloom_api.router, prefix="/bloom/api/v1", tags=['BLOOM API'])
app.include_router(symspell_api.router, prefix="/symspell/api/v1", tags=['SymSpell API'])


@app.get("/")
def read_root():
    return {"message": "Welcome to the API"}


if __name__ == "__main__":
    print("Running app with uvicorn...")
