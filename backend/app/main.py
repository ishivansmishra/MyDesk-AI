from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings, validate_required_settings
from app.core.database import init_db
from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.oauth import router as oauth_router
from app.api.routes.calendar import router as calendar_router
from app.api.routes.tasks import router as tasks_router
from app.core.logging_config import configure_logging
from app.core.middleware import RequestIDMiddleware, AccessLogMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate required settings and fail fast in production
    validate_required_settings()
    configure_logging(debug=settings.debug)
    await init_db()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

# Security: CORS - restrict to configured origins plus localhost variants
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list + ["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID and access logging
app.add_middleware(RequestIDMiddleware)
app.add_middleware(AccessLogMiddleware)

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(oauth_router, prefix="/api/v1")
app.include_router(calendar_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")


@app.get("/")
def root() -> dict[str, str]:
    return {"service": settings.app_name, "status": "running"}
