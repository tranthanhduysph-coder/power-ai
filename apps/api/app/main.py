from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.release import LOCAL_RELEASE_VERSION

settings = get_settings()
app = FastAPI(title=settings.app_name, version=LOCAL_RELEASE_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"name": "POWER AI API", "version": LOCAL_RELEASE_VERSION, "docs": "/docs"}
