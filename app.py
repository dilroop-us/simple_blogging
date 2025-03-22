from fastapi import FastAPI
from database import initialize_global_data
from routes import users, blogs, favourites

# ✅ Initialize FastAPI App
app = FastAPI(
    title="Blogging API",
    description="A simple blogging API with JWT authentication and Firebase Firestore",
    version="1.0.0"
)

# ✅ Register Routes
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(favourites.router, prefix="/users", tags=["Favourites"])
app.include_router(blogs.router, prefix="/blogs", tags=["Blogs"])

# ✅ Startup Event: Ensure predefined categories exist
@app.on_event("startup")
def startup_event():
    initialize_global_data()

# ✅ Root Endpoint
@app.get("/")
def root():
    return {"message": "Welcome to the Blogging API"}
