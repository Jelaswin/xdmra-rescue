from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.database import engine, Base
from app.api import router as api_router
from app.api.command import router as command_router
from app.api.evaluation import router as evaluation_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.seed import seed_db

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="X-DMRA Rescue API")

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
allowed_origins = os.getenv("ALLOWED_ORIGINS", frontend_origin).split(",")

if "*" in allowed_origins and os.getenv("ENVIRONMENT", "").lower() not in ("development", "dev", "test"):
    allowed_origins = [o for o in allowed_origins if o != "*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(command_router, prefix="/api")
app.include_router(evaluation_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")

@app.on_event("startup")
def on_startup():
    if os.getenv("ENVIRONMENT", "").lower() not in ("production", "prod"):
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            seed_db(db)
        finally:
            db.close()
