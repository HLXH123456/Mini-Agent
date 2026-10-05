import locale
import subprocess

from pydantic import BaseModel

from tools.tool import tool


class ShellArgs(BaseModel):
    command: str


def _decode(data: bytes | None) -> str:
    if not data:
        return ""
    for enc in ("utf-8", locale.getpreferredencoding(False)):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")

@tool(
    name="shell",
    description="在终端执行 Shell 命令",
    args_model=ShellArgs
)
def shell(command: str) -> dict:
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=False,
        stdin=subprocess.DEVNULL,
        timeout=180,
    )
    return {
        "return_code": result.returncode,
        "stdout": _decode(result.stdout),
        "stderr": _decode(result.stderr),
    }
