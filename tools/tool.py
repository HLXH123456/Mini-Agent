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
class ToolDef:
    name: str
    description: str
    func: Callable[..., Any]
    input_schema: dict[str, Any]
    args_model: type[BaseModel] | None

class ToolRegistry:
    def __init__(self, default_timeout: float | None | object = _UNSET) -> None:
        self._spec: dict[str, ToolDef] = {}
        if default_timeout is _UNSET:
            self.default_timeout = None
        else:
            self.default_timeout = default_timeout

    """工具注册装饰器"""
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
            self._spec[name] = ToolDef(name=name, description=description, func=func, input_schema=schema,
                                       args_model=args_model)
            return func
        return decoration

    """获取工具定义列表"""
    def tools_schema(self) -> list[dict[str, Any]]:
        return list(self._spec.values())

    """执行工具函数，返回工具调用结果"""
    async def invoke(self, name: str, arguments: dict[str, Any]) -> Any:
        spec = self._spec.get(name)
        if not spec:
            raise UnknownToolError(name)
        if spec.args_model is None:
            kwargs: dict[str, Any] = {}
        else:
            validated = spec.args_model.model_validate_json(arguments or "{}")
            kwargs = validated.model_dump(by_alias=True)
        if inspect.iscoroutinefunction(spec.func):
            work = spec.func(**kwargs)
        else:
            work = asyncio.to_thread(spec.func, **kwargs)
        if self.default_timeout is None:
            return await work
        return await asyncio.wait_for(work, timeout=self.default_timeout)

registry = ToolRegistry()

"""对外提供的工具注册装饰器"""
def tool(
        name: str,
        description: str,
        args_model: type[BaseModel] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """给工具模块用的装饰器入口"""
    return registry.register(name=name, description=description, args_model=args_model)

