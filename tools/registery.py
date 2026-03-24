from pathlib import Path
from typing import Any
from tools.base import Tool, ToolInvocation, ToolResult
import logging

from tools.builtin import get_all_builtin_tool

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
    
    async def invoke(self,name : str,params : dict[str,Any], cwd : Path | None) -> ToolResult:
        tool = self.get(name)
        if tool is None:
            return ToolResult.error_result(error=f"Unkown Tool {name}",metadata={
                "tool_name" : name
            })
        validation_errors = tool.validate_params(params=params)
        if validation_errors:
            return ToolResult.error_result(
                error=f"Invalid paramtres : {'; '.join(validation_errors)}",
                metadata={'tool_name':name,'validation_errors':validation_errors}
            )
        
        invocation = ToolInvocation(params=params,cwd=cwd)
        try:
            result = await tool.execute(invocation)
            return result
        except Exception as e:
            logger.exception(f"Tool {name} raised unexpected error")
            return ToolResult.error_result(
                f'Internal Error : {str(e)}',
                metadata={'tool_name',name}
            )
        
def create_default_registry() -> ToolRegistery:
    registry = ToolRegistery()

    for tool_class in get_all_builtin_tool():
        registry.register(tool_class())
    return registry
        