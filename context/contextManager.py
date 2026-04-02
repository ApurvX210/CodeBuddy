from dataclasses import dataclass, field
import os
from typing import Any
from prompts.system import get_system_prompt
from utils.text import count_token

@dataclass
class MessageItem:
    role : str
    content : str
    tool_call_id : str | None = None
    tool_calls: list[dict[str,Any]] = field(default_factory=list)
    token_count : int | None = None

    def to_dict(self) -> dict[str,Any]:
        result : dict[str,Any] = {
            "role" : self.role
        }

        if self.tool_call_id:
            result['tool_call_id'] = self.tool_call_id

        if self.tool_calls:
            result['tool_calls'] = self.tool_calls

        if self.content:
            result["content"] = self.content

        return result

class ContextManager:
    def __init__(self) -> None:
        # It tell llm how to behave
        self._system_prompt = get_system_prompt()
        self.model = os.getenv(key="MODEL_NAME")
        self._messages : list[MessageItem] = []

    def add_user_message(self,content : str):
        messageItem = MessageItem(
                role="user",
                content=content,
                token_count=count_token(content or "",self.model)
            )
        self._messages.append(messageItem)

    def add_assistant_message(self,content : str,tool_calls: list[dict[str,Any]] | None = None):
        messageItem = MessageItem(
                role="assistant",
                content=content,
                tool_calls=tool_calls or [],
                token_count=count_token(content or "",self.model)
            )
        self._messages.append(messageItem)

    def add_tool_result(self,tool_call_id: str,content: str) -> None:
        item = MessageItem(
            role="tool",
            content=content,
            tool_call_id=tool_call_id,
            token_count=count_token(content or "",self.model)
        )

        self._messages.append(item)

    def get_message(self) -> list[dict[str,Any]]:
        messages = []

        if self._system_prompt:
            messages.append(
                {
                    'role': "system",
                    'content': self._system_prompt
                }
            )
        for messageItem in self._messages:
            messages.append(messageItem.to_dict())

        return messages