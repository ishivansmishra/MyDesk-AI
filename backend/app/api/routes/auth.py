from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/logout")
def logout() -> dict[str, str]:
    return {"status": "logged_out"}
