from fastapi import FastAPI

from app.api import auth, health, ocr, schedules, shares, users
from app.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api")
    app.include_router(schedules.router, prefix="/api")
    app.include_router(ocr.router, prefix="/api")
    app.include_router(users.router, prefix="/api")
    app.include_router(shares.router, prefix="/api")
    return app


app = create_app()
