from pathlib import Path
from typing import Any
from tools.base import Tool
import logging

logger = logging.getLogger(__name__)

class ToolRegistery:
    def __init__(self):
        self._tools : dict[str,Tool] = {}

    def register(self,tool : Tool):
        if tool.name in self._tools:
            logger.warning(f"Overiting existoing tool : {tool.name}")

        self._tools[tool.name] = tool
        logger.debug(f"Registered the tool : {tool.name}")

    def unregister(self,tool : Tool) -> bool:
        if tool.name in self._tools:
            del self._tools[tool.name]
            return True

        return False
    
    def get(self,tool_name) -> Tool | None:
        if tool_name in self._tools:
            return self._tools[tool_name]
        
        return None
    
    def get_tools(self) -> list[Tool]:
        tools : list[Tool] = []

        for tool in self._tools.values():
            tools.append(tool)

        return tools
    
    def getSchemas(self) ->list[dict[str,Any]]:
        return [tool.to_openai_schema() for tool in self.get_tools()]
    
    async def invoke(self,name : str,params : dict[str,Any], path : Path | None):
        tool = self._tools[name]
        errors = tool.validate_params(params=params)
        if len(errors) > 0:

        