import json
from typing import Dict,Any,List

from ..mcp_servers.gmail_server import GmailMCPServer
from ..mcp_servers.gdocs_server import GDocsMCPServer 
from ..mcp_servers.gcalender_server import GCalendarMCPServer
from ..mcp_servers.gsheets_server import GSheetsMCPServer
from ..mcp_servers.gforms_server import GFormsMCPServer

from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

class MCPService:
    def __init__(self):
        self._tool_definitions= self._tool_definitions()
        self._mcp_servers = {
            "gmail":GmailMCPServer(),
            "gdocs":GDocsMCPServer(),
            "gcalendar":GCalendarMCPServer(),
            "gsheets":GSheetsMCPServer(),
            "gforms":GFormsMCPServer()

        }

    def _tool_definitions(self)->List[Dict[str,Any]]:
        """Load tool definitions from JSON file."""
        try:
            with open(settings.TOOL_DEFINITION_PATH,'r') as f:
                data = json.load(f)
                return data.get("tools",[])
        except FileNotFoundError:
            logger.error(f"Tool definition file not found at {settings.TOOL_DEFINITION_PATH}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from tool definition file: {e}")
            return []
    def get_tool_definitions(self)->List[Dict[str,Any]]:
        return self._tool_definitions
    def execute_tool(self,tool_name:str,args:Dict[str,Any])->Dict[str,Any]:
       
        try:
           parts = tool_name.split("_",1)
           if len(parts) <2:
               raise ValueError("Invalid tool name format.")
           server_name,action = parts
           server = self._mcp_servers.get(server_name)
           if not server:
               raise ValueError(f"No MCP server found for {server_name}")
           
           #get the function/method on the server object
           tool_function = getattr(server,action,None)
           if not tool_function:
               raise ValueError(f"No action '{action}' found on server '{server_name}'")
           result = tool_function(**args)
           logger.info(f"Executed tool {tool_name} with args {args}, result: {result}")
           return result
        except Exception as e:
            logger.error(f"Failed to execute tool '{tool_name}': {e}", exc_info=True)
            return {"status": "error", "message": f"Tool execution failed: {str(e)}"}
            