from client.llm import LLM
import asyncio
async def main():
    llm = LLM()
    messages = [
        {
            "role":"user",
            "content":"What's up"
        }
    ]
    async for event in llm.chatCompletion(messages=messages,stream=False):
        print(event)
    print("Done")

if __name__ == "__main__":
    asyncio.run(main())