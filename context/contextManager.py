from dataclasses import dataclass
import os
from typing import Any
from prompts.system import get_system_prompt
from utils.text import count_token

@dataclass
class MessageItem:
    role : str
    content : str
    token_count : int | None = None

    def to_dict(self) -> dict[str,Any]:
        result : dict[str,Any] = {
            "role" : self.role
        }

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
                token_count=count_token(content,self.model)
            )
        self._messages.append(messageItem)

    def add_assistant_message(self,content : str):
        messageItem = MessageItem(
                role="assistant",
                content=content,
                token_count=count_token(content,self.model)
            )
        self._messages.append(messageItem)

    def get_message(self) -> list[dict[str,Any]]:
        messages = []

        if self._system_prompt:
            messages.append(
                {
                    'system': self._system_prompt
                }
            )
        for messageItem in self._messages:
            messages.append(messageItem.to_dict())

        return messages