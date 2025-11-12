import json
from typing import Any,Dict,List
from openai import OpenAI
from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

class LLMService:
    def __init__(self,provider:str=settings.LLM_PROVIDER):
        self.provider = provider.lower()
        self.model = settings.LLM_MODEL
        self.client = OpenAI()

        if self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API key is not set in environment variables.")
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
        

    def _format_messages(self,user_message:str,tool_outputs:List[Dict[str,Any]] |None = None)->List[Dict[str,str]]:
        messages = [{"role":"user","content":user_message}]
        if tool_outputs:
            for output in tool_outputs:
                if self.provider == "openai":
                    messages.append({
                        "role":"tool",
                        "tool_call_id":output["tool_call_id"],
                        "content":json.dumps(output["output"])
                    })
        return messages
    def get_chat_completion(self,user_message:str,tools:List[Dict[str,Any]]) ->Dict[str,Any]:
        messages = self._format_messages(user_message)
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model = self.model,
                    messages = messages,
                    toola = tools,
                    tool_choice = "auto"
                )
                choice = response.choices[0].message
                return {
                    "text":choice.content,
                    "tool_calls":choice.tool_calls
                }
        except Exception as e:
            logger.error(f"Error getting chat completion: {e}")
            raise
        except Exception as e:
            logger.error("General error in LLMService: {e}")
            raise
    
    def get_final_response_with_tool_outputs(self,user_message:str,tool_calls:List[Any],tool_outputs:List[Dict[str,Any]]) ->Dict[str,Any]:
        """performs the second chat completion with tool results"""
        messages = [{"role":"user","content":user_message}]
        if self.provider == "openai":
            messages.appened({
                "role":"assistant",
                "tool_calls":[call for call in tool_calls]
            })
        for output in tool_outputs:
            if self.provider == "openai":
                messages.append({
                    "role":"tool",
                    "tool_call_id":output["tool_call_id"],
                    "content":json.dumps(output["output"])

                })
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model = self.model,
                    messages = messages,
                    tools = self.mcp_service.get_tool_definitions(),
                    tool_choice = "auto"
                )
                return {"text":response.choices[0].message.content}
        except Exception as e:
            logger.error(f"Error getting final chat completion: {e}")
            raise
    def set_tool_definitions(self, tool_defs: List[Dict[str, Any]]):
        """Temporary method to resolve circular dependency for final call."""
        self.tool_definitions = tool_defs