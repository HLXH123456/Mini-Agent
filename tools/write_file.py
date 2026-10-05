from pathlib import Path

from pydantic import BaseModel

from tools import tool
from tools.sandbox import current


class WriteArgs(BaseModel):
    path: Path | str
    content: str
    is_append: bool = False


@tool(
    name="write",
    description="将内容写入文件里",
    args_model=WriteArgs
)
def write(path: Path | str, content: str, is_append: bool = False) -> None:
    real = current().check_write(path)
    real.parent.mkdir(parents=True, exist_ok=True)
    if not is_append:
        real.write_text(content, encoding="utf-8")
    else:
        with real.open("a", encoding="utf-8") as f:
            f.write(content)
