import asyncio

from model import OpenAIModel
from runtime import Runtime


async def main():
    runtime = Runtime(
        OpenAIModel(model="deepseek-flash"),
    )
    msg = list()
    while True:
        user_input = input("user:")
        if not user_input:
            continue
        if user_input == 'q':
            break
        msg.append(
            {"role": "user", "content": user_input}
        )
        resp = await runtime.run(
            instructions="你是Mini，一个AI智能体",
            input=msg
        )
        msg.append(
            {"role": "assistant", "content": resp.text}
        )
        print(resp.text)
        print()


if __name__ == '__main__':
    asyncio.run(main())
