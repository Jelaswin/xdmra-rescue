from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.database import engine, Base
from app.api import router as api_router
from app.api.command import router as command_router
from app.seed import seed_db

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="X-DMRA Rescue API")

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(command_router, prefix="/api")

@app.on_event("startup")
def on_startup():
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        seed_db(db)
    finally:
        db.close()
