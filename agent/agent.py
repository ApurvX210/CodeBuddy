from __future__ import annotations
from typing import AsyncGenerator
from agent.events import AgentEvent, AgentEventType
from client.llm import LLM
from client.response import StreamEventType


class Agent:
    def __init__(self):
        self.llm = LLM()


    async def run(self,message:str) -> AsyncGenerator[AgentEvent]:
        yield AgentEvent.agent_start(message=message)
        #To Do - Update context
        final_response = None
        async for event in self._agentic_loop():
            if event.type == AgentEventType.TEXT_COMPLETE:
                final_response = event.data.get("content")
            yield event

        yield AgentEvent.agent_end(response=final_response)
                

    async def _agentic_loop(self) -> AsyncGenerator[AgentEvent]:
        messages = [
            {
                "role":"user",
                "content":"Hello How are you"
            }
        ]

        response_text = ""
        async for event in self.llm.chatCompletion(messages=messages,stream=True):
            if event.type == StreamEventType.TEXT_DELTA:
                # print(event)
                if event.text_delta:
                    content = event.text_delta.content
                    response_text += content
                    yield AgentEvent.text_delta(content=content)
            elif event.type == StreamEventType.ERROR:
                error = event.error if event.error else "Unknown Error Occured"
                yield AgentEvent.agent_error(error=error)
            
        if response_text:
            yield AgentEvent.text_complete(content=response_text)

    async def __aenter__(self) -> Agent:
        return self
    
    async def __aexit__(self,exc_type, exc_val,exc_tb) -> Agent:
        if self.llm:
            await self.llm.close()
            self.llm = None