from dataclasses import dataclass, field
from pathlib import Path


class SandboxViolation(PermissionError):
    """路径不在沙箱允许范围内"""


@dataclass
class FileSandbox:
    work_path: Path | str = field(default_factory=lambda: Path.cwd().resolve())
    read_path: tuple[Path | str, ...] = ()
    protect_path: tuple[Path | str, ...] = ()
    _work: Path = field(init=False, repr=False)
    _reads: tuple[Path, ...] = field(init=False, repr=False)
    _protects: tuple[Path, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._work = Path(self.work_path).resolve()
        self._reads = tuple(
            (p if p.is_absolute() else self._work / p).resolve()
            for p in map(Path, self.read_path)
        )
        self._protects = tuple(  # ← 和 _reads 完全同构
            (p if p.is_absolute() else self._work / p).resolve()
            for p in map(Path, self.protect_path)
        )

    def _resolve(self, path: Path | str) -> Path:
        p = Path(path)
        if not p.is_absolute():
            p = self._work / p
        return p.resolve()

    def is_work_path(self, path: Path | str) -> bool:
        return self._resolve(path).is_relative_to(self._work)

    def check_read(self, path: Path | str) -> Path:
        real = self._resolve(path)
        if not any(real.is_relative_to(a) for a in (self._work, *self._reads)):
            raise SandboxViolation(f"读取被拒绝，路径不在沙箱内: {real}")
        return real

    def check_write(self, path: Path | str) -> Path:
        real = self._resolve(path)
        if not real.is_relative_to(self._work):
            raise SandboxViolation(f"写入被拒绝，路径不在工作区内: {real}")
        if any(real.is_relative_to(p) for p in self._protects):
            raise SandboxViolation(f"写入被拒绝，该路径只读: {real}")
        return real


_default: FileSandbox | None = None
AGENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTECT = (
    AGENT_ROOT / "prompt.md",
    AGENT_ROOT / "tools",
    AGENT_ROOT / "model.py",
    AGENT_ROOT / "runtime.py",
    AGENT_ROOT / "main.py",
)


def configure(sandbox: FileSandbox | None = None) -> FileSandbox:
    global _default
    _default = sandbox
    return current()


def current() -> FileSandbox:
    global _default
    if _default is None:
        _default = FileSandbox(protect_path=DEFAULT_PROTECT)
    return _default
