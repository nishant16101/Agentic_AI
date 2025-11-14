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
        self.client = None 

        if self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API key is not set in environment variables.")
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
        
        # Placeholder for MCP Service instance to resolve potential circular dependency
        self.mcp_service = None 

    def _format_messages(self,user_message:str,tool_outputs:List[Dict[str,Any]] |None = None)->List[Dict[str,str]]:
        # This method seems unused based on the original structure, but kept for future refactoring.
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
    
    # Tool: get_chat_completion
    def get_chat_completion(self,user_message:str,tools:List[Dict[str,Any]]) ->Dict[str,Any]:
        """Performs the initial chat completion to determine if a tool call is necessary."""
        messages = [
            {"role": "system", "content": "You are an expert assistant for Google Workspace. Your goal is to use the available tools (Gmail, Calendar, Docs, Sheets, Forms) to fulfill the user's request. If a tool is necessary, ONLY respond with a tool call. If not, respond directly."},
            {"role":"user","content":user_message}
        ]
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto"
                )
                
                # Check for tool calls
                if response.choices[0].message.tool_calls:
                    return {"tool_calls": response.choices[0].message.tool_calls}
                
                # Check for direct text response
                elif response.choices[0].message.content:
                    return {"text": response.choices[0].message.content}
                else:
                    return {"text": "I received an empty response. Please try rephrasing your request."}
            # Add other provider logic here (e.g., Anthropic)
            else:
                return {"text": f"Unsupported provider {self.provider} for chat completion."}
        
        except Exception as e:
            logger.error(f"Error getting initial chat completion: {e}")
            raise
    
    # Tool: get_final_response_with_tool_outputs
    def get_final_response_with_tool_outputs(self,user_message:str,tool_calls:List[Any],tool_outputs:List[Dict[str,Any]]) ->Dict[str,Any]:
        """Performs the second chat completion with tool results to generate a final, human-readable response."""
        
        messages = [
            {"role": "system", "content": "You have just executed one or more Google Workspace actions. Your final response must clearly and concisely summarize the outcome of the action(s) for the user, drawing directly from the provided tool output results."},
            {"role":"user","content":user_message}
        ]
        
        if self.provider == "openai":
            # 1. Add the assistant's original tool call
            messages.append({
                "role":"assistant",
                "tool_calls":[call for call in tool_calls]
            })
            
            # 2. Add the tool results
            for output in tool_outputs:
                messages.append({ # Fix: messages.appened changed to messages.append
                    "role":"tool",
                    "tool_call_id":output["tool_call_id"],
                    "content":json.dumps(output["output"])
                })
        
        try:
            if self.provider == "openai":
                # Removed tools and tool_choice as the model's job is now only to summarize the output
                response = self.client.chat.completions.create(
                    model = self.model,
                    messages = messages,
                )
                return {"text":response.choices[0].message.content}
            # Add other provider logic here
            
        except Exception as e:
            logger.error(f"Error getting final chat completion: {e}")
            raise
            
    def set_tool_definitions(self, tool_defs: List[Dict[str, Any]]):
        """Temporary method to resolve circular dependency for final call. (Kept for compatibility)"""
        pass