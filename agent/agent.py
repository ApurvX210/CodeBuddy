from __future__ import annotations
import json
from pathlib import Path
from typing import AsyncGenerator, List
from agent.events import AgentEvent, AgentEventType
from client.llm import LLM
from client.response import StreamEventType, ToolCall, ToolResultMessage
from config.config import Config
from context.contextManager import ContextManager
from tools.registery import create_default_registry


class Agent:
    def __init__(self,config: Config):
        self.config = config
        self.llm = LLM(config=config)
        self.contextManager = ContextManager(config=config)
        self.tool_registry = create_default_registry()

    async def run(self,message:str) -> AsyncGenerator[AgentEvent]:
        yield AgentEvent.agent_start(message=message)
        self.contextManager.add_user_message(content=message)
        final_response = None
        async for event in self._agentic_loop():
            if event.type == AgentEventType.TEXT_COMPLETE:
                final_response = event.data.get("content")
            yield event
        self.contextManager.add_assistant_message(content=final_response)
        yield AgentEvent.agent_end(response=final_response)
                

    async def _agentic_loop(self) -> AsyncGenerator[AgentEvent]:
        tool_schemas = self.tool_registry.getSchemas()
        response_text = ""
        tool_calls : List[ToolCall] = []
        async for event in self.llm.chatCompletion(messages=self.contextManager.get_message(),stream=True,tools=tool_schemas if tool_schemas else None):
            if event.type == StreamEventType.TEXT_DELTA:
                if event.text_delta:
                    content = event.text_delta.content
                    response_text += content
                    yield AgentEvent.text_delta(content=content)
            elif event.type == StreamEventType.TOOL_CALL_COMPLETE:
                if event.tool_call:
                    tool_calls.append(event.tool_call)
            elif event.type == StreamEventType.ERROR:
                error = event.error if event.error else "Unknown Error Occured"
                yield AgentEvent.agent_error(error=error)
        
        self.contextManager.add_assistant_message(
            content=response_text or "",
            tool_calls=[
                {
                    "id" : tc.call_id,
                    "type" : "function",
                    "function" : {
                        "name" : tc.name,
                        "arguments" : json.dumps(tc.arguments),
                    }
                }
                for tc in tool_calls
            ] if tool_calls else None
        )
        if response_text:
            yield AgentEvent.text_complete(content=response_text)

        tool_call_result : list[ToolResultMessage] = []
        for tool_call in tool_calls:
            yield AgentEvent.tool_call_start(call_id=tool_call.call_id,name=tool_call.name,arguments=tool_call.arguments)

            result = await self.tool_registry.invoke(name=tool_call.name,params=tool_call.arguments,cwd=Path.cwd())

            yield AgentEvent.tool_call_complete(call_id=tool_call.call_id,name=tool_call.name,result=result)

            tool_call_result.append(ToolResultMessage(
                tool_call_id=tool_call.call_id,
                content=result.to_model_output(),
                is_error= not result.success
            ))
        
        for tool_result in tool_call_result:
            self.contextManager.add_tool_result(
                tool_result.tool_call_id,
                tool_result.content
            )

    async def __aenter__(self) -> Agent:
        return self
    
    async def __aexit__(self,exc_type, exc_val,exc_tb) -> Agent:
        if self.llm:
            await self.llm.close()
            self.llm = None