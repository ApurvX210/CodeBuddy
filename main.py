from pathlib import Path
import sys
from typing import Any
from agent.agent import Agent
from agent.events import AgentEventType
from client.llm import LLM
import asyncio
import click

from config.config import Config
from config.loader import load_config
from ui.renderer import AgentUI, get_console

console = get_console()
class CLI:
    def __init__(self,config: Config):
        self.config : Config = config
        self.agent : Agent | None = None
        self.agentUi = AgentUI(console=console,config=config)

    async def run_single(self,message : str) ->str:
        async with Agent(self.config) as agent:
            self.agent = agent
            return await self._process_message(message)
        
    async def run_interactive(self) ->str:
        async with Agent(self.config) as agent:
            self.agent = agent
            self.agentUi.print_welcome(
                f"model: {self.agent.session.llm._MODEL}",
                lines=[
                f"cwd: {str(self.config.cwd)}",
                f"commands : /help /config /approval /model /exit"]
            )
            while True:
                try:
                    user_input = console.input("\n[user]>[/user] ").strip()
                    if not user_input:
                        continue
                    
                    await self._process_message(user_input)
                except KeyboardInterrupt:
                    console.print("\n[dim]Use /exit to quit[/dim]")
                except EOFError:
                    break

        console.print("\n[dim]Goodbye![/dim]")    
        
    def _get_tool_kind(self,tool_name: str) -> str | None:
        tool = self.agent.session.tool_registry.get(tool_name)
        tool_kind = None
        if not tool:
            tool_kind = None
        else:
            tool_kind = tool.kind.value

        return tool_kind

    async def _process_message(self, message : str) -> str | None:
        if not self.agent:
            return None
        assistant_streaming = False
        final_response = None
        async for event in self.agent.run(message=message):
            if event.type == AgentEventType.TEXT_DELTA:
                content = event.data.get("content","")
                if assistant_streaming == False:
                    self.agentUi.begin_assistant()
                    assistant_streaming = True
                self.agentUi.stream_assistant_delta(content=content)
            elif event.type == AgentEventType.TEXT_COMPLETE:
                final_response = event.data.get("content","")
                assistant_streaming = False
                self.agentUi.end_assistant()
            elif event.type == AgentEventType.AGENT_ERROR:
                error = event.data.get("error","Unkown Error")
                assistant_streaming = False
                self.agentUi.end_assistant(f"\n[error]Error : {error}[/error]")
            elif event.type == AgentEventType.TOOL_CALL_START:
                tool_name = event.data.get("name","unknown")
                tool_kind = self._get_tool_kind(tool_name)

                self.agentUi.tool_call_start(event.data.get("call_id"),
                                            tool_name,
                                            tool_kind,
                                            event.data.get("arguments"),
                                            )
            elif event.type == AgentEventType.TOOL_CALL_COMPLETE:
                tool_name = event.data.get("name","unknown")
                tool_kind = self._get_tool_kind(tool_name)

                self.agentUi.tool_call_complete(event.data.get("call_id"),
                                            tool_name,
                                            tool_kind,
                                            success=event.data.get("success",False),
                                            output=event.data.get("output",""),
                                            error=event.data.get("error",None),
                                            metadata=event.data.get("metadata",None),
                                            truncated=event.data.get("truncated",False),
                                            diff=event.data.get("diff",None)
                                            )
        
        return final_response

# async def run(messages : dict[str,Any]):
#     llm = LLM()
#     async for event in llm.chatCompletion(messages=messages,stream=False):
#         print(event)

@click.command()
@click.argument("prompt",required=False)
@click.option(
    '--cwd',
    '-c',
    type=click.Path(exists=True,file_okay=False,path_type=Path),
    help="Current working directory"
)
def main(prompt : str | None,cwd : Path | None):
    try:
        config = load_config(cwd=cwd)
    except Exception as e:
        console.print(f"[error]Configuration Error : {e}[/error]")
        sys.exit(1)

    errors = config.validate()

    if errors:
        for error in errors:
            console.print(f"[error]{error}[/error]")

        sys.exit(1)

    cli = CLI(config=config)
    if prompt:
        result = asyncio.run(cli.run_single(message=prompt))
        if result is None:
            sys.exit(1)
    else:
        asyncio.run(cli.run_interactive())
    

if __name__ == "__main__":
    main()