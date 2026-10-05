from pathlib import Path

from pydantic import BaseModel

from tools import tool
from tools.sandbox import current


class EditArgs(BaseModel):
    path: Path | str
    old_content: str
    new_content: str


@tool(
    name="edit",
    description="编辑文件中的内容",
    args_model=EditArgs
)
def edit(path: Path | str, old_content: str, new_content: str) -> None:
    real = current().check_write(path)
    content = real.read_text(encoding="utf-8")
    if old_content not in content:
        raise ValueError(f"未找到待替换内容: {old_content[:50]!r}")
    real.write_text(content.replace(old_content, new_content), encoding="utf-8")
