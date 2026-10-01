import asyncio

from tools.shell import shell

print(asyncio.run(shell("echo hello")))
