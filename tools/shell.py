import subprocess

from pydantic import BaseModel

from tools.tool import tool


class ShellArgs(BaseModel):
    command: str


@tool(
    name="shell",
    description="在终端执行 Shell 命令",
    args_model=ShellArgs
)
async def shell(command: str) -> dict:
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        timeout=180,
    )
    return {
        "return_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
