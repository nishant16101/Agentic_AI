from pydantic import BaseModel
from typing import List,Dict,Any,Optional

class ChatRequest(BaseModel):
    """Schema for incoming chat requests."""
    message:str

class ToolDetail(BaseModel):
    """Detail about single tool exceution"""
    tool_call_id:str
    output:Dict[str,Any]

class ChatResponse(BaseModel):
    """Schema for agent response"""
    message:str
    tool_executed:bool
    tool_details:Optional[List[ToolDetail]] = None


class FunctionCall(BaseModel):
    """LLM function call object"""
    name:str
    argumnets:Dict[str,Any]

class ToolCall(BaseModel):
    """LLM's tool call object wrapper."""
    id: str
    function: FunctionCall