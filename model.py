import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from anthropic import Anthropic
from openai import OpenAI

from tools import ToolDef


@dataclass
class ToolCall:
    id: str
    name: str
    argument: str


@dataclass(frozen=True)
class ToolResult:
    call_id: str
    output: str
    is_error: bool = False

@dataclass
class ModelResponse:
    text: str | None
    tool_calls: list[ToolCall]
    raw: Any = None

class Model(ABC):

    @abstractmethod
    def generate(
            self,
            instruction: str | None,
            input: list,
            tools: list[dict] | None = None,
            ) -> ModelResponse:
        raise NotImplementedError

    @abstractmethod
    def tools_payload(self, defs: list[ToolDef]) -> list[dict] | None:
        raise NotImplementedError

    @abstractmethod
    def tool_result(self, response: ModelResponse, outputs: list[ToolResult]) -> list[dict]:
        raise NotImplementedError


"""OpenAI"""
class OpenAIModel(Model):

    def __init__(
            self,
            model: str,
            client: OpenAI | None = None
    ):
        self.model = model
        self.client = client or OpenAI()

    def generate(
            self,
            instruction: str | None,
            input: list,
            tools: list[dict] | None = None,
            ) -> ModelResponse:
        response = self.client.responses.create(
            model=self.model,
            instructions=instruction,
            input=input,
            tools=tools
        )
        tool_calls = []

        for item in response.output:
            if item.type == "function_call":
                tool_calls.append(
                    ToolCall(
                        id=item.call_id,
                        name=item.name,
                        argument=item.arguments
                    )
                )
        return ModelResponse(
            text=response.output_text,
            tool_calls=tool_calls,
            raw=response
        )

    def tools_payload(self, defs: list[ToolDef]) -> list[dict] | None:
        if not defs:
            return None
        return [
            {"type": "function", "name": d.name, "description": d.description,
             "parameters": d.input_schema}
            for d in defs
        ]

    def tool_result(self, response: ModelResponse, outputs: list[ToolResult]) -> list[dict]:
        return list(response.raw.output) + [
            {
                "type": "function_call_output",
                "call_id": output.call_id,
                "output": output.output
            }
            for output in outputs
        ]


"""Anthropic"""
class AnthropicModel(Model):

    def __init__(
            self,
            model: str,
            client: Anthropic | None = None
    ):
        self.model = model
        self.client = client or Anthropic()

    def generate(self, instruction: str | None, input: list, tools: list[dict] | None = None) -> ModelResponse:
        response = self.client.messages.create(
            model=self.model,
            messages=input,
            system=instruction,
            tools=tools,
            max_tokens=4096
        )
        tool_calls = []
        text = None
        for item in response.content:
            if item.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=item.id,
                        name=item.name,
                        argument=json.dumps(item.input, ensure_ascii=False)
                    )
                )
            if item.type == "text":
                text = item.text
        return ModelResponse(
            text=text or "",
            tool_calls=tool_calls,
            raw=response
        )

    def tools_payload(self, defs: list[ToolDef]) -> list[dict] | None:
        if not defs:
            return None
        return [
            {"name": d.name, "description": d.description, "input_schema": d.input_schema}
            for d in defs
        ]

    def tool_result(self, response: ModelResponse, outputs: list[ToolResult]) -> list[dict]:
        return [
            {"role": "assistant", "content": response.raw.content},
            {"role": "user", "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": output.call_id,
                    "content": output.output,
                    "is_error": output.is_error
                }
                for output in outputs
            ]}
        ]
