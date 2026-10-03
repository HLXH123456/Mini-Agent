from typing import Any

from model import Model, ToolResult
from tools import ToolRegistry, registry


class Runtime:
    def __init__(self, model: Model, tool_registry: ToolRegistry = registry):
        self.model = model
        self.tool_registry = tool_registry
        self.instruction = "你是Mini-Agent，一个AI智能体。"

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
