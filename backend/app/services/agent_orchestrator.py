# backend/app/services/agent_orchestrator.py

import json
from typing import Any, Dict
from openai import OpenAI
from anthropic import Anthropic

from ..config import settings
from ..models.schemas import ChatResponse
from .llm_service import LLMService
from .mcp_service import MCPService
from ..utils.logger import get_logger

logger = get_logger(__name__)

class AgentOrchestrator:
    def __init__(self):
        self.llm_service = LLMService(settings.LLM_PROVIDER)
        self.mcp_service = MCPService()
        self.tool_definitions = self.mcp_service.get_tool_definitions()

    def _format_function_call(self, tool_call: Any) -> Dict[str, Any]:
        """Formats the LLM's tool call into a standardized dictionary."""
        
        # OpenAI format
        return {
            "id": tool_call.id,
            "function": {
                "name": tool_call.function.name,
                "arguments": tool_call.function.arguments
            }
        }

    def orchestrate_chat(self, user_message: str) -> ChatResponse:
        """
        The main orchestration loop for the agent.
        1. Calls LLM with message and tool definitions.
        2. If tool is called, execute tool via MCP.
        3. Calls LLM again with tool output.
        4. Returns final LLM response.
        """
        logger.info(f"Starting orchestration for: {user_message}")
        
        # 1. Initial LLM call
        response = self.llm_service.get_chat_completion(
            user_message=user_message,
            tools=self.tool_definitions
        )
        
        # Check for tool calls
        tool_calls = response.get('tool_calls', [])
        
        # 2. If no tool is called, return the LLM's text response
        if not tool_calls:
            logger.info("No tool call detected. Returning direct response.")
            return ChatResponse(
                message=response.get('text', 'No response.'), 
                tool_executed=False,
                tool_details=None
            )

        # 3. Process Tool Calls
        tool_outputs = []
        for call in tool_calls:
            formatted_call = self._format_function_call(call)
            tool_name = formatted_call["function"]["name"]
            tool_args_str = formatted_call["function"]["arguments"]
            
            try:
                tool_args = json.loads(tool_args_str)
                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                
                # Execute tool via MCP
                tool_result = self.mcp_service.execute_tool(tool_name, tool_args)
                
                tool_outputs.append({
                    "tool_call_id": formatted_call["id"],
                    "output": tool_result
                })
                
            except Exception as e:
                error_output = f"Error executing tool '{tool_name}': {e}. Raw Arguments: {tool_args_str}"
                logger.error(error_output)
                tool_outputs.append({
                    "tool_call_id": formatted_call["id"],
                    "output": {"status": "error", "message": error_output}
                })

        # 4. Final LLM call with tool outputs
        logger.info("Calling LLM with tool outputs for final response.")
        final_response = self.llm_service.get_final_response_with_tool_outputs(
            user_message=user_message,
            tool_calls=tool_calls,
            tool_outputs=tool_outputs
        )
        
        # Summarize tool execution for the user
        tool_summary = f"Tool(s) executed: {', '.join([c['name'] for c in tool_calls])}."
        
        # Return final response
        return ChatResponse(
            message=final_response.get('text', 'Could not generate a final response after tool execution.'),
            tool_executed=True,
            tool_details=tool_outputs # Can include more structured details here
        )