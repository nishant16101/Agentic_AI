from fastapi import APIRouter,HTTPException,Depends
from pydantic import BaseModel

from ...services.agent_orchestrator import AgentOrchestrator
from ...utils.logger import get_logger
from ...models.schemas import ChatResponse

router = APIRouter()
logger = get_logger(__name__)

class ChatRequest(BaseModel):
    message:str

def get_orchestrator()->AgentOrchestrator:
    return AgentOrchestrator()


@router.post("",response_model=ChatResponse)
async def post_chat_message(
    request:ChatRequest,
    orchestrator:AgentOrchestrator = Depends(get_orchestrator)

):
    """Sends a message to the agent and gets a response, potentially triggering a Google Workspace action via tool"""
    try:
        response = orchestrator.orchestrate_chat(user_message=request.message)
        return response
    except PermissionError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Unauthorized: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {str(e)}"
        )
