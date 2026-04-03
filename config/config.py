import os
from pathlib import Path

from pydantic import BaseModel,Field

class ModelConfig(BaseModel):
    name: str
    temperature: float = Field(default=1,ge=0.0,le=2.0) #Used to define creativity of model
    context_window:int = 256000

class Config(BaseModel):
    model: ModelConfig = Field(default_factory=ModelConfig)
    cwd: Path = Field(default_factory=Path.cwd())

    max_turns: int = 100
    max_tool_output_tokens: int = 50000

    developer_instruction: str | None = None
    user_instruction: str | None = None

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