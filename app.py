from fastapi import FastAPI
from database import Base, engine
from routers import user, dictionary,get_api_router,post_api_router

app = FastAPI()

# Include the routers from the modules
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(dictionary.router, prefix="/dictionary", tags=["Dictionary"])
app.include_router(get_api_router.router, tags=['GET API'])
app.include_router(post_api_router.router, tags=['POST API'])
@app.get("/")
def read_root():
    return {"message": "Welcome to the API"}

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)  # Ensure tables are created on startup

if __name__ == "__main__":
    print("Running app with uvicorn...")
