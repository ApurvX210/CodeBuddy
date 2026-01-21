import os
import asyncio
from typing import Any, AsyncGenerator
from openai import AsyncOpenAI

from client.response import EventType, StreamEvent, TextDelta, TokenUsage

class LLM:
    def __init__(self) -> None:
        self._LLM_API_KEY = os.getenv(key="LLM_API_KEY")
        self._BASE_URL = os.getenv(key="BASE_URL")
        self._MODEL = os.getenv(key="MODEL_NAME")
        self._client : AsyncOpenAI | None = None
        

    def getClient(self) -> AsyncOpenAI:
        if self._client is None:
            self._client =  AsyncOpenAI(
                api_key=self._LLM_API_KEY,
                base_url=self._BASE_URL
            )
        
        return self._client
    
    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    async def chatCompletion(self,messages:list[dict[str,Any]], stream : bool = True) -> AsyncGenerator[StreamEvent,None]:
        client = self.getClient()
        kwargs = {
            "model" : self._MODEL,
            "messages" : messages,
            "stream" : stream
        }
        if stream:
            await self._streamResponse(client,kwargs)
        else:
            data = await self._nonStreamResponse(client,kwargs)
            yield data

        return

    async def _streamResponse(self, client:AsyncOpenAI, kwargs : dict[str,Any]):
        response = await client.chat.completions.create(**kwargs)

    async def _nonStreamResponse(self, client:AsyncOpenAI, kwargs : dict[str,Any]) -> StreamEvent:
        response = await client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        message = choice.message
        text_delta = None
        if message.content:
            text_delta = TextDelta(content=message.content)

        usage = None
        if response.usage:
            usage = TokenUsage(
                completion_tokens=response.usage.completion_tokens,
                prompt_tokens=response.usage.prompt_tokens,
                total_tokens=response.usage.total_tokens,
                cached_token=response.usage.prompt_tokens_details.cached_tokens
            )

        return StreamEvent(
            type=EventType.MESSAGE_COMPLETE,
            text_delta=text_delta,
            finish_reason=choice.finish_reason,
            usage=usage
        )