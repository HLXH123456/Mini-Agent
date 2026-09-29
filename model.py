from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from openai import OpenAI


@dataclass
class ToolCall:
    id: str
    name: str
    argument: str

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