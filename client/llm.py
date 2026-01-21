import os
import asyncio
from typing import Any
from openai import AsyncOpenAI

class LLM:
    def __init__(self) -> None:
        self._LLM_API_KEY = os.getenv(key="LLM_API_KEY")
        self._BASE_URL = os.getenv(key="BASE_URL")
        self._MODEL = os.getenv(key="MODEL_NAME")
        self._client : AsyncOpenAI | None = None
        

    def getClient(self) -> AsyncOpenAI:
        if self._client is None:
            print(self._BASE_URL,self._LLM_API_KEY,self._MODEL)
            self._client =  AsyncOpenAI(
                api_key=self._LLM_API_KEY,
                base_url=self._BASE_URL
            )
        
        return self._client
    
    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    async def chatCompletion(self,messages:list[dict[str,Any]], stream : bool = True):
        client = self.getClient()
        kwargs = {
            "model" : self._MODEL,
            "messages" : messages,
            "stream" : stream
        }
        if stream:
            await self._streamResponse()
        else:
            await self._nonStreamResponse(client,kwargs)

    async def _streamResponse(self):
        pass

    async def _nonStreamResponse(self, client:AsyncOpenAI, kwargs : dict[str,Any]):
        response = await client.chat.completions.create(**kwargs)
        print(response)