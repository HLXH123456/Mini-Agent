import platform
from datetime import datetime
from pathlib import Path
from typing import Any

from model import Model, ToolResult
from tools import ToolRegistry, registry

PROMPT_FILE = Path(__file__).with_name("prompt.md")


def load_instruction(path: Path | None = None) -> str:
    """系统提示词从 prompt.md 读。锚定本文件所在目录，不受启动时 cwd 影响。"""
    text = (path or PROMPT_FILE).read_text(encoding="utf-8")
    append_text = f"\n当前系统: {platform.system()}，当前时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"
    if not text.strip():
        raise RuntimeError(f"提示词文件是空的: {path or PROMPT_FILE}")
    return text + append_text

class Runtime:
    def __init__(self, model: Model, tool_registry: ToolRegistry = registry):
        self.model = model
        self.tool_registry = tool_registry
        self.instruction = load_instruction()

    async def run(self, input: list) -> Any:
        while True:
            response = self.model.generate(
                instruction=self.instruction,
                input=input,
                tools=self.model.tools_payload(self.tool_registry.tools_schema())
            )
            if not response.tool_calls:
                return response
            tools_outputs = list()
            for tool_call in response.tool_calls:
                try:
                    print(f"调用工具:{tool_call.name} {tool_call.argument}")
                    result = await self.tool_registry.invoke(tool_call.name, tool_call.argument)
                    output = str(result)
                    is_error = False
                except Exception as e:
                    output = f"Tool execution failed: {e}"
                    is_error = True
                tools_outputs.append(
                    ToolResult(call_id=tool_call.id, output=output, is_error=is_error)
                )
            input.extend(self.model.tool_result(response, tools_outputs))


if __name__ == '__main__':
    print(load_instruction())
