from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
@dataclass
class TextDelta:
    content: str
    def __str__(self):
        return self.content

@dataclass
class EventType(str,Enum):
    TEXT_DELTA = "text_delta"
    MESSAGE_COMPLETE = "message_complete"
    ERROR = "error"

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
class StreamEvent:
    type: EventType
    text_delta: TextDelta | None = None
    error: str | None = None
    finish_reason: str | None = None
    usage: TokenUsage | None = None