from __future__ import annotations
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel,Field, model_validator

class MCPServerConfig(BaseModel):
    enabled: bool = True
    startup_timeout_sec: float = 10

    # stdio transport
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    env: dict[str,str] = Field(default_factory=dict)
    cwd: Path | None = None

    # http/sse transport
    url: str | None = None

    @model_validator
    def validate_transport(self) -> MCPServerConfig:
        has_command = self.command is not None
        has_url = self.url is not None

        if not has_command and not has_url:
            raise ValueError("MCP Server must have either 'command' (stdio) or 'url' (http/sse)")
        
        if has_command and has_url:
            raise ValueError("MCP Server cannot have both 'command' (stdio) or 'url' (http/sse)")

        return self
class ModelConfig(BaseModel):
    name: str
    temperature: float = Field(default=1,ge=0.0,le=2.0) #Used to define creativity of model
    context_window:int = 256000

class ShellEnvironmentPolicy(BaseModel):
    ignore_default_excludes: bool = False
    exclude_pattern: list[str] = Field(default_factory=lambda : ["*KEY*","*TOKEN*","*SECRET*"])
    set_vars: dict[str,str] = Field(default_factory=dict)

class Config(BaseModel):
    model: ModelConfig = Field(default_factory=ModelConfig)
    cwd: Path = Field(default_factory=Path.cwd())
    shell_environment: ShellEnvironmentPolicy = Field(default_factory=ShellEnvironmentPolicy)
    max_turns: int = 100
    mcp_servers: dict[str,MCPServerConfig] = Field(default_factory=dict)
    allowed_tools: list[str] | None = Field(
        None,description="if set, only these tools will be available to agents"
    )
    max_tool_output_tokens: int = 50000

    developer_instructions: str | None = None
    user_instructions: str | None = None

    debug: bool = False

    @property
    def api_key(self) -> str | None:
        return os.getenv("LLM_API_KEY")
    
    @property
    def base_url(self) -> str | None:
        return os.getenv("BASE_URL")
    
    @property
    def model_name(self) -> str | None:
        return self.model.name
    
    @model_name.setter
    def model_name(self,value:str) -> None:
        self.model.name = value
    
    @property
    def temperature(self) -> float:
        return self.model.temperature
    
    @model_name.setter
    def temperature(self,value:float) -> None:
        self.model.temperature = value

    def validate(self) -> list[str]:
        errors: list[str] = []

        if not self.api_key:
            errors.append("No Api key found. Set LLM_API_KEY in environment variables")

        if not self.cwd.exists():
            errors.append(f"Working directory does not exist: {self.cwd}")

        return errors
    
    def to_dict(self) -> dict[str,Any]:
        return self.model_dump(mode='json')