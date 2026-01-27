from typing import Any
from agent.agent import Agent
from agent.events import AgentEventType
from client.llm import LLM
import asyncio
import click

class CLI:
    def __init__(self):
        self.agent : Agent | None = None

    async def run_single(self,message : str):
        async with Agent() as agent:
            self.agent = agent
            self._process_message(message)

    async def _process_message(self, message : str) -> str | None:
        if not self.agent:
            return None
        
        async for event in self.agent.run(message=message):
            if event.type == AgentEventType.TEXT_DELTA:
                content = event.data.get("content","")


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
    asyncio.run(cli.run_single(messages=messages))
    print("Done")

if __name__ == "__main__":
    main()