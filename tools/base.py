from __future__ import annotations
import abc
from enum import Enum
from typing import Any

from pydantic import BaseModel

class ToolKind(str,Enum):
    READ = "read"
    WRITE = "write"
    SHELL = "shell"
    NETWORK = "network"
    MEMORY = "memory"
    MCP ="mcp"


# Defining abstract class
class Tool(abc.ABC):
    name: str = "base_tool"
    description: str = "Base tool"
    kind: ToolKind = ToolKind.READ

    def __init__(self) -> None:
        pass
    
    @property
    def schema(self) -> dict[str,Any] | type['BaseModel']:
        raise NotImplementedError("Tool must define schema property or class attribute")
    
    @abc.abstractmethod
    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        pass