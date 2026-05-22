from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Diff:
    missing_in_example: list[str] = field(default_factory=list)
    missing_in_env: list[str] = field(default_factory=list)
    empty_in_env: list[str] = field(default_factory=list)

    def is_clean(self) -> bool:
        return not (self.missing_in_example or self.missing_in_env or self.empty_in_env)


def parse_env(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if not key:
            continue
        result[key] = value
    return result


def diff(env: dict[str, str], example: dict[str, str]) -> Diff:
    env_keys = set(env)
    example_keys = set(example)
    return Diff(
        missing_in_example=sorted(env_keys - example_keys),
        missing_in_env=sorted(example_keys - env_keys),
        empty_in_env=sorted(k for k in env_keys & example_keys if env[k] == ""),
    )
