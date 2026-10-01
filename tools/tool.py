import asyncio
import inspect
from dataclasses import dataclass
from typing import Callable, Any

from pydantic import BaseModel

_UNSET = object()


class UnknownToolError(Exception):
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"unknown tool '{name}'")


@dataclass
class ToolSpec:
    name: str
    func: Callable[..., Any]
    args_model: type[BaseModel] | None


class ToolRegistry:
    def __init__(self, default_timeout: float | None | object = _UNSET) -> None:
        self._spec: dict[str, ToolSpec] = {}
        self._schemas: dict[str, dict[str, Any]] = {}
        if default_timeout is _UNSET:
            self.default_timeout = 30.0
        else:
            self.default_timeout = default_timeout

    def register(
            self,
            name: str,
            description: str,
            args_model: type[BaseModel] | None = None
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decoration(func: Callable[..., Any]) -> Callable[..., Any]:
            if name in self._spec:
                raise ValueError(f"duplicate tool name '{name}'")
            if args_model is not None:
                schema = args_model.model_json_schema()
                schema.pop("title", None)
                for prop in schema.get("properties", {}).values():
                    prop.pop("title", None)
            else:
                schema = {"type": "object", "properties": {}}
            self._spec[name] = ToolSpec(name=name, func=func, args_model=args_model)
            self._schemas[name] = {
                "type": "function",
                "name": name,
                "description": description,
                "parameters": schema
            }
            return func

        return decoration

    def tools_schema(self) -> list[dict[str, Any]]:
        return list(self._schemas.values())

    async def invoke(self, name: str, arguments: dict[str, Any]) -> Any:
        spec = self._spec.get(name)
        if not spec:
            raise UnknownToolError(name)
        if spec.args_model is None:
            kwargs: dict[str, Any] = {}
        else:
            validated = spec.args_model.model_validate_json(arguments or "{}")
            kwargs = validated.model_dump(by_alias=True)
        result = spec.func(**kwargs)
        if inspect.isawaitable(result):
            if self.default_timeout is None:
                result = await result
            else:
                result = await asyncio.wait_for(result, timeout=self.default_timeout)
        return result


registry = ToolRegistry()


def tool(
        name: str,
        description: str,
        args_model: type[BaseModel] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """给工具模块用的装饰器入口"""
    return registry.register(name=name, description=description, args_model=args_model)


def bind_tool_schema() -> list[dict[str, Any]]:
    return registry.tools_schema()
