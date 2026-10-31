from fastapi import FastAPI

from app.database import Base, engine
from app.models.user import User

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SIVAMANI API",
    description="Backend API powered by FastAPI and PostgreSQL",
    version="1.0.0"
)


@app.get("/")
def home():
    return {"message": "SIVAMANI API is running"}


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected"
    }