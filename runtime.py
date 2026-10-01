from model import Model
from tools.tool import ToolRegistry, registry


class Runtime:
    def __init__(self, model: Model, tool_registry: ToolRegistry = registry):
        self.model = model
        self.tool_registry = tool_registry

    async def run(
            self,
            instructions: str | None,
            input: list
    ):
        while True:
            response = self.model.generate(
                instruction=instructions,
                input=input,
                tools=self.tool_registry.tools_schema()
            )
            if not response.tool_calls:
                return response
            input.extend(response.raw.output)
            for tool_call in response.tool_calls:
                try:
                    result = await self.tool_registry.invoke(tool_call.name, tool_call.argument)
                    output = str(result)
                except Exception as e:
                    output = f"Tool execution failed: {e}"
                input.append(
                    {
                        "type": "function_call_output",
                        "call_id": tool_call.id,
                        "output": output,
                    })
