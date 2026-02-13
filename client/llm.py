import os
import asyncio
from typing import Any, AsyncGenerator
from openai import APIConnectionError, AsyncOpenAI, RateLimitError

from client.response import StreamEventType, StreamEvent, TextDelta, TokenUsage

class LLM:
    def __init__(self) -> None:
        self._LLM_API_KEY = os.getenv(key="LLM_API_KEY")
        self._BASE_URL = os.getenv(key="BASE_URL")
        self._MODEL = os.getenv(key="MODEL_NAME")
        self._max_retries = int(os.getenv(key="MAX_RETRIES"))
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

    def _build_tools(self,tools : list[dict[str,Any]]):
        return [
            {
                'type' : 'function',
                'function' : {
                    'name' : tool['name'],
                    'description' : tool.get('description',""),
                    'parameters' : tool.get('parameters',{
                        'type' : 'object',
                        'properties' : {}
                    })
                }
            }
            for tool in tools
        ]

    async def chatCompletion(self,messages:list[dict[str,Any]], stream : bool = True,tools:list[dict[str,Any]] | None = None) -> AsyncGenerator[StreamEvent,None]:
        client = self.getClient()
        kwargs = {
            "model" : self._MODEL,
            "messages" : messages,
            "stream" : stream
        }
        if tools:
            kwargs["tools"] = self._build_tools(tools)
            kwargs["tool_choice"] = "auto"

        for attempt in range(self._max_retries+1):
            try:
                
                if stream:
                    async for event in self._streamResponse(client,kwargs):
                        yield event
                else:
                    data = await self._nonStreamResponse(client,kwargs)
                    yield data

                return
            except RateLimitError as e:
                # Exponential Backoff
                if attempt < self._max_retries:
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    yield StreamEvent(
                        type=StreamEventType.ERROR,
                        error= f"Rate Limit Exceeded : {e}"
                    )
            except APIConnectionError as e:
                # Exponential Backoff
                if attempt < self._max_retries:
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    yield StreamEvent(
                        type=StreamEventType.ERROR,
                        error= f"Rate Limit Exceeded : {e}"
                    )

    async def _streamResponse(self, client:AsyncOpenAI, kwargs : dict[str,Any]):
        response = await client.chat.completions.create(**kwargs)

        finish_reason: str | None = None
        usage: TokenUsage | None = None
        tool_calls : dict[int,dict[str,Any]] = {}
        async for chunk in response:
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            message = choice.delta

            if hasattr(chunk,"usage") and chunk.usage:
                if chunk.usage:
                    usage = TokenUsage(
                        completion_tokens=chunk.usage.completion_tokens,
                        prompt_tokens=chunk.usage.prompt_tokens,
                        total_tokens=chunk.usage.total_tokens,
                        cached_token=chunk.usage.prompt_tokens_details.cached_tokens
                    )
            if hasattr(choice,"finish_reason"):
                finish_reason = choice.finish_reason

            if message.content:
                yield StreamEvent(
                    type=StreamEventType.TEXT_DELTA,
                    text_delta=TextDelta(content=message.content),
                )
            
            if message.tool_calls:
                for tool_call_delta in message.tool_calls:
                    print(tool_call_delta)
                    idx = tool_call_delta.index
                    if idx not in tool_calls:
                        tool_calls[idx] = {
                            "id" : tool_call_delta.id or "",
                            "arguments" : "",
                            "name" : None
                        }
                    
                    if tool_call_delta.function and tool_call_delta.function.arguments:
                        tool_calls[idx]["arguments"] += tool_call_delta.function.arguments

                    if tool_call_delta.function and tool_call_delta.function.name:
                        tool_calls[idx]["name"] = tool_call_delta.function.name
                        yield StreamEvent(
                            type=StreamEventType.TOOL_CALL_START,
                            
                        )
        
        print(tool_calls)
        yield StreamEvent(
                type=StreamEventType.MESSAGE_COMPLETE,
                finish_reason=finish_reason,
                usage=usage
            )

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
            type=StreamEventType.MESSAGE_COMPLETE,
            text_delta=text_delta,
            finish_reason=choice.finish_reason,
            usage=usage
        )