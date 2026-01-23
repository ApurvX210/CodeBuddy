from typing import AsyncGenerator

from agent.events import AgentEvent
from client.llm import LLM
from client.response import StreamEventType


class Agent:
    def __init__(self):
        self.llm = LLM()


    async def run(self,message:str) -> AsyncGenerator[AgentEvent]:
        yield AgentEvent.agent_start(message=message)
        #To Do - Update context
        async for event in self._agentic_loop():
            yield event

    async def _agentic_loop(self) -> AsyncGenerator[AgentEvent]:
        messages = [
            {
                "role":"user",
                "content":"Hello How are you"
            }
        ]
        async for event in self.llm.chatCompletion(messages=messages,stream=False):
            if event.type == StreamEventType.TEXT_DELTA:
                content = event.text_delta.content
                yield AgentEvent.text_delta(content=content)
            elif event.type == StreamEventType.ERROR:
                error = event.error if event.error else "Unknown Error Occured"
                yield AgentEvent.agent_error(error=error)
            # elif event.type == StreamEventType.MESSAGE_COMPLETE:
            #     content = event.text_delta.content
            #     yield AgentEvent.agent_end(me)