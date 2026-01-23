from typing import Any
from agent.agent import Agent
from client.llm import LLM
import asyncio
import click

class CLI:
    def __init__(self):
        self.agent : Agent | None = None

    async def run_single(self):
        async with Agent() as agent:
            self.agent = agent


async def run(messages : dict[str,Any]):
    llm = LLM()
    async for event in llm.chatCompletion(messages=messages,stream=False):
        print(event)

@click.command()
@click.argument("prompt",required=False)
def main(prompt : str | None):
    messages = [
        {
            "role":"user",
            "content":prompt
        }
    ]
    asyncio.run(run(messages=messages))
    print("Done")

if __name__ == "__main__":
    main()