from __future__ import annotations
import json
from typing import AsyncGenerator, List

from agent.events import AgentEvent, AgentEventType
from agent.session import Session

from client.response import StreamEventType, ToolCall, ToolResultMessage
from config.config import Config

class Agent:
    def __init__(self,config: Config):
        self.config = config
        self.session : Session | None = Session(config=config)

    async def run(self,message:str) -> AsyncGenerator[AgentEvent]:
        yield AgentEvent.agent_start(message=message)
        self.session.contextManager.add_user_message(content=message)
        final_response = None
        async for event in self._agentic_loop():
            if event.type == AgentEventType.TEXT_COMPLETE:
                final_response = event.data.get("content")
            yield event
        self.session.contextManager.add_assistant_message(content=final_response)
        yield AgentEvent.agent_end(response=final_response)
                

    async def _agentic_loop(self) -> AsyncGenerator[AgentEvent]:
        max_turn = self.config.max_turns
        tool_schemas = self.session.tool_registry.getSchemas()

        for turn in range(max_turn):
            self.session.increment_turn()
            response_text = ""
            tool_calls : List[ToolCall] = []
            
            async for event in self.session.llm.chatCompletion(messages=self.session.contextManager.get_message(),stream=True,tools=tool_schemas if tool_schemas else None):
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
                    
            
            self.session.contextManager.add_assistant_message(
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

            if not tool_calls:
                return
            
            tool_call_result : list[ToolResultMessage] = []
            for tool_call in tool_calls:
                yield AgentEvent.tool_call_start(call_id=tool_call.call_id,name=tool_call.name,arguments=tool_call.arguments)

                result = await self.session.tool_registry.invoke(name=tool_call.name,params=tool_call.arguments,cwd=self.config.cwd)

                yield AgentEvent.tool_call_complete(call_id=tool_call.call_id,name=tool_call.name,result=result)

                tool_call_result.append(ToolResultMessage(
                    tool_call_id=tool_call.call_id,
                    content=result.to_model_output(),
                    is_error= not result.success
                ))
            
            for tool_result in tool_call_result:
                self.session.contextManager.add_tool_result(
                    tool_result.tool_call_id,
                    tool_result.content
                )

    async def __aenter__(self) -> Agent:
        await self.session.initialize()
        return self
    
    async def __aexit__(self,exc_type, exc_val,exc_tb) -> Agent:
        if self.session and self.session.llm and self.session.mcp_manager:
            await self.session.llm.close()
            await self.session.mcp_manager.shutdown()
            self.session = None

        