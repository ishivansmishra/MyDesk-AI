from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import text
from app.core.database import engine
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/live")
def liveness() -> dict[str, str]:
    # Liveness probe - returns 200 if app process is alive
    return {"status": "alive"}


@router.get("/ready")
async def readiness() -> dict[str, str]:
    # Readiness probe - verify DB connectivity
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DB unavailable: {exc}")
    return {"status": "ready"}


@router.get("/metrics")
def metrics() -> Response:
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
