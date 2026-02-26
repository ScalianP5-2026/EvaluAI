from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import api_router
from backend.app.config import settings

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", tags=["health"])
def root() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
    }


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "healthy"}
