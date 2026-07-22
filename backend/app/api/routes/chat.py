import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.agent_service import AgentService
from app.services.auth_service import get_bearer_token, get_current_user_id
from app.services.google.oauth_service import GoogleOAuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])
agent_service = AgentService()


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request, session: AsyncSession = Depends(get_session)) -> ChatResponse:
    get_bearer_token(request)
    if not payload.message.strip():
        return ChatResponse(reply="Please provide a message.", intent="unknown")

    user_id = get_current_user_id(request)
    intent = agent_service.get_intent(payload.message)
    logger.info("Chat request intent=%s user_id=%s", intent, user_id)

    google_service = GoogleOAuthService(user_id, session)
    required = agent_service.required_services(user_id, payload.message)
    calendar_service = None
    tasks_service = None

    if required.get("calendar"):
        calendar_service = await google_service.get_calendar_service()
    if required.get("tasks"):
        tasks_service = await google_service.get_tasks_service()

    result = agent_service.handle(
        payload.message,
        context={"user_id": payload.user_id or user_id},
        calendar_service=calendar_service,
        tasks_service=tasks_service,
    )

    return ChatResponse(
        reply=result.get("reply", "I didn't understand that request."),
        intent=result.get("intent", "assistant"),
        result=result.get("result"),
    )
