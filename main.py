from model import OpenAIModel
from runtime import Runtime

if __name__ == '__main__':
    runtime = Runtime(
        OpenAIModel(model="qwen3.8-flash"),
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
        resp = runtime.run(
            instructions="你是GD-code，一个编程助手",
            input=msg
        )
        msg.append(
            {"role": "assistant", "content": resp.text}
        )
        print(resp.text)
        print()