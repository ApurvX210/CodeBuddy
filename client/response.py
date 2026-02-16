from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import json
@dataclass
class TextDelta:
    content: str
    def __str__(self):
        return self.content

class StreamEventType(str,Enum):
    TEXT_DELTA = "text_delta"
    MESSAGE_COMPLETE = "message_complete"
    ERROR = "error"
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_DELTA = "tool_call_delta"
    TOOL_CALL_COMPLETE = "tool_call_complete"

@dataclass
class TokenUsage:
    completion_tokens:int = 0
    prompt_tokens:int = 0
    total_tokens:int = 0
    cached_token:int = 0

    def __add__(self,other: TokenUsage):
        return TokenUsage(
            completion_tokens = self.completion_tokens + other.completion_tokens,
            prompt_tokens = self.prompt_tokens + other.prompt_tokens,
            total_tokens = self.total_tokens + other.total_tokens,
            cached_token = self.cached_token + other.cached_token,
        )
        
@dataclass
class ToolCall:
    call_id : str
    name : str
    arguments : str = ""

@dataclass
class ToolCallDelta:
    call_id : str
    name : str | None = None
    arguments_delta : str = ""


@dataclass
class StreamEvent:
    type: StreamEventType
    text_delta: TextDelta | None = None
    error: str | None = None
    finish_reason: str | None = None
    usage: TokenUsage | None = None
    tool_call : ToolCall | None = None
    tool_call_delte : ToolCallDelta | None = None

def parse_tool_call_arguments(argument_str : str) -> dict[str,Any]:
    if not argument_str:
        return {}
    
    try:
        return json.loads(argument_str)
    except json.JSONDecodeError:
        return {'raw_arguments':argument_str}
