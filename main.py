import sys
from typing import Any
from agent.agent import Agent
from agent.events import AgentEventType
from client.llm import LLM
import asyncio
import click

from ui.renderer import AgentUI, get_console

console = get_console()
class CLI:
    def __init__(self):
        self.agent : Agent | None = None
        self.agentUi = AgentUI(console=console)

    async def run_single(self,message : str) ->str:
        async with Agent() as agent:
            self.agent = agent
            return await self._process_message(message)

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
                print("Yash")
                final_response = event.data.get("content","")
                assistant_streaming = False
                self.agentUi.end_assistant()
        
        return final_response

async def run(messages : dict[str,Any]):
    llm = LLM()
    async for event in llm.chatCompletion(messages=messages,stream=False):
        print(event)

@click.command()
@click.argument("prompt",required=False)
def main(prompt : str | None):
    cli = CLI()
    messages = [
        {
            "role":"user",
            "content":prompt
        }
    ]
    result = asyncio.run(cli.run_single(message=messages))
    if result is None:
        sys.exit(1)

if __name__ == "__main__":
    main()