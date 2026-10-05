from pathlib import Path

from pydantic import BaseModel

from tools import tool
from tools.sandbox import current


class ReadArgs(BaseModel):
    path: Path | str


@tool(
    name="read",
    description="读取工作区里的文件",
    args_model=ReadArgs
)
def read(path: Path | str) -> str:
    return current().check_read(path).read_text(encoding="utf-8")
