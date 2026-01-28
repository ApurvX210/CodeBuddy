from dataclasses import dataclass
import os
from prompts.system import get_system_prompt
from utils.text import count_token

@dataclass
class MessageItem:
    role : str
    content : str
    token_count : int | None = None

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