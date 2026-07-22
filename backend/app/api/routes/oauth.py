from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import uuid4

import logging

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.models.workspace_account import WorkspaceAccount
from app.services.auth_service import AuthService, get_current_user_optional
from app.services.google.oauth_service import GoogleOAuthService
from app.services.workspace_service import WorkspaceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/oauth", tags=["oauth"])

auth_service = AuthService()


def _create_oauth_state_token(state_id: str, redirect_target: str, code_verifier: str) -> str:
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET must be configured to generate OAuth state tokens.")

    now = datetime.now().timestamp()
    payload = {
        "sub": state_id,
        "redirect_target": redirect_target,
        "code_verifier": code_verifier,
        "iat": int(now),
        "exp": int(now) + 300,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _decode_oauth_state_token(state_token: str) -> dict[str, str] | None:
    if not settings.jwt_secret:
        logger.error("JWT_SECRET is not configured for state token validation")
        return None

    try:
        payload = jwt.decode(state_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if not isinstance(payload, dict):
            return None
        return {
            "redirect_target": payload.get("redirect_target", settings.frontend_url),
            "code_verifier": payload.get("code_verifier", ""),
        }
    except jwt.PyJWTError as exc:
        logger.error("OAuth state token validation failed: %s", exc)
        return None


def _replace_state_in_authorization_url(authorization_url: str, state_value: str) -> str:
    parsed = urlsplit(authorization_url)
    query_params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query_params["state"] = state_value
    return urlunsplit(parsed._replace(query=urlencode(query_params)))


def _log_oauth_start(state_id: str, redirect_target: str, callback_url: str, authorization_url: str, state_token: str) -> None:
    logger.info("Google OAuth start generated state_id=%s redirect_target=%s callback_url=%s", state_id, redirect_target, callback_url)
    logger.debug("Google OAuth start authorization_url=%s", authorization_url)
    logger.debug("Google OAuth start state_token_shorthand=%s...", state_token[:16] if state_token else "")


@router.get("/google")
def google_oauth_start(request: Request, next: str | None = Query(default=None)) -> JSONResponse:
    service = GoogleOAuthService()
    if not service.is_configured():
        return JSONResponse(
            {
                "status": "oauth-flow-ready",
                "instructions": "Provide Google OAuth credentials to enable live Google Workspace access.",
            }
        )

    redirect_target = f"{settings.frontend_url}/login"
    if next and next.startswith("/"):
        redirect_target = f"{settings.frontend_url}{next}"

    state_id = str(uuid4())
    runtime_callback_url = request.url_for("google_oauth_callback")
    configured_callback_url = settings.google_redirect_uri
    if runtime_callback_url != configured_callback_url:
        logger.warning(
            "Google OAuth callback URL mismatch: runtime=%s configured=%s",
            runtime_callback_url,
            configured_callback_url,
        )
    authorization_url, code_verifier = service.build_auth_url(state_id, redirect_uri=configured_callback_url)
    state_token = _create_oauth_state_token(state_id, redirect_target, code_verifier)
    auth_url = _replace_state_in_authorization_url(authorization_url, state_token)

    _log_oauth_start(state_id, redirect_target, configured_callback_url, auth_url, state_token)

    response = JSONResponse({"status": "oauth-flow-ready", "authorization_url": auth_url, "state": state_token})
    return response


@router.get("/google/callback", response_model=None)
async def google_oauth_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> Response:
    logger.info("[1] Callback received")
    logger.debug("Callback request query: %s", dict(request.query_params))
    logger.debug(
        "Callback request metadata host=%s scheme=%s path=%s client=%s accept=%s cookie=%s",
        request.url.hostname,
        request.url.scheme,
        request.url.path,
        request.client,
        request.headers.get("accept"),
        request.headers.get("cookie"),
    )

    if not code:
        logger.error("[2] Missing OAuth code")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing OAuth code")
    logger.info("[2] Authorization code received")

    service = GoogleOAuthService()
    if not service.is_configured():
        logger.error("[3] Google OAuth not configured")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Google OAuth is not configured")

    if not state:
        logger.error("[3] Invalid or missing OAuth state: %s", state)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or missing OAuth state")

    state_data = _decode_oauth_state_token(state)
    if state_data is None:
        logger.error("[3] Invalid or missing OAuth state: %s", state)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or missing OAuth state")

    try:
        code_verifier = state_data.get("code_verifier")
        if not code_verifier:
            logger.error("[4] Missing code verifier in OAuth state token")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state payload")

        runtime_callback_url = request.url_for("google_oauth_callback")
        configured_callback_url = settings.google_redirect_uri
        if runtime_callback_url != configured_callback_url:
            logger.warning(
                "Google OAuth callback URL mismatch on callback: runtime=%s configured=%s",
                runtime_callback_url,
                configured_callback_url,
            )
        logger.info("[4] Exchanging code for access token... redirect_uri=%s", configured_callback_url)
        result = service.exchange_code(
            code,
            redirect_uri=configured_callback_url,
            code_verifier=code_verifier,
        )
        logger.info("[5] Access token received")
        logger.debug("Exchange result: %s", result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("[4] Google token exchange failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Google token exchange failed: {exc.__class__.__name__}: {exc}",
        ) from exc

    email = result.get("email")
    if not email:
        logger.error("[5] Missing email in Google profile: %s", result)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to verify Google email")

    profile_picture = result.get("picture")
    token_expiry = datetime.fromisoformat(result["expiry"]) if result.get("expiry") else None
    refresh_token = result.get("refresh_token")
    access_token_value = result.get("token")

    google_user_id = result.get("google_user_id")
    if not google_user_id:
        logger.error("[5] Missing Google user id in profile: %s", result)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to verify Google user id")

    try:
        logger.info("[6] Creating/finding user...")
        account = await WorkspaceService(session).connect_account(
            google_user_id=google_user_id,
            email=email,
            name=result.get("name"),
            profile_picture=profile_picture,
            access_token=access_token_value,
            refresh_token=refresh_token,
            token_expiry=token_expiry,
        )
        logger.info("[7] User account created/updated: %s", account.id)
    except Exception as exc:
        logger.exception("[7] Failed to save OAuth account")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to save Google account: {exc.__class__.__name__}: {exc}",
        ) from exc

    try:
        logger.info("[8] Creating JWT/session...")
        access_token = auth_service.create_access_token(
            account.id,
            extra_claims={"name": result.get("name"), "picture": profile_picture, "email": email},
        )
        logger.info("[9] JWT created")
    except Exception as exc:
        logger.exception("[8] JWT creation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to create authentication token: {exc.__class__.__name__}: {exc}",
        ) from exc

    redirect_url = state_data.get("redirect_target", settings.frontend_url)
    if redirect_url.startswith("/"):
        redirect_url = f"{settings.frontend_url}{redirect_url}"
    if not redirect_url.startswith(("http://", "https://")):
        redirect_url = f"{settings.frontend_url}/{redirect_url.lstrip('/')}"

    parsed = urlsplit(redirect_url)
    query_params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query_params.update({"connected": "1", "token": access_token})
    redirect_target = urlunsplit(parsed._replace(query=urlencode(query_params)))
    logger.info("[10] Redirecting to frontend: %s", redirect_target)
    if request is not None and "text/html" in request.headers.get("accept", "").lower():
        return RedirectResponse(redirect_target, status_code=302)

    return JSONResponse({
        "status": "connected",
        "state": state,
        "access_token": access_token,
        "token_type": "bearer",
        "redirect_url": redirect_target,
    })


@router.get("/google/status")
async def google_oauth_status(
    current_user: WorkspaceAccount | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    service = GoogleOAuthService(current_user.id if current_user else None, session if current_user else None)
    if current_user is not None:
        await service.load_user_tokens()
    status_payload = service.status()
    response = {
        "configured": status_payload["configured"],
        "connected": status_payload["connected"],
    }
    if current_user is not None:
        response["email"] = current_user.user_email
        response["name"] = current_user.name
    return response
