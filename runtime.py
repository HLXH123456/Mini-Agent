from model import Model


class Runtime:
    def __init__(self, model: Model):
        self.model = model

    def run(
            self,
            instructions: str | None,
            input: list,
            tools: list[dict] | None = None
    ):
        return self.model.generate(
            instruction=instructions,
            input=input,
            tools=tools
        )
