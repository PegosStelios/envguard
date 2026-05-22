import re
from dataclasses import dataclass
from pathlib import Path

import pathspec

from envguard.patterns import RULES, find_matches, shannon_entropy


DEFAULT_SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}
ENTROPY_THRESHOLD = 4.5
ENTROPY_MIN_LEN = 20
ENTROPY_TOKEN_RE = re.compile(r"['\"]([A-Za-z0-9+/=_-]{20,})['\"]")


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    rule: str
    match: str


def mask(text: str) -> str:
    if len(text) <= 4:
        return "***MASKED"
    return f"{text[:4]}***MASKED"


def _is_binary(path: Path) -> bool:
    try:
        chunk = path.open("rb").read(8192)
    except OSError:
        return True
    return b"\x00" in chunk


def _load_gitignore(root: Path) -> pathspec.PathSpec | None:
    gi = root / ".gitignore"
    if not gi.is_file():
        return None
    return pathspec.PathSpec.from_lines("gitwildmatch", gi.read_text().splitlines())


def _iter_files(root: Path, ignore_globs: list[str]) -> list[Path]:
    if root.is_file():
        return [root]
    gi_spec = _load_gitignore(root)
    user_spec = pathspec.PathSpec.from_lines("gitwildmatch", ignore_globs) if ignore_globs else None
    out: list[Path] = []
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        rel = p.relative_to(root)
        if any(part in DEFAULT_SKIP_DIRS for part in rel.parts):
            continue
        rel_str = str(rel)
        if gi_spec and gi_spec.match_file(rel_str):
            continue
        if user_spec and user_spec.match_file(rel_str):
            continue
        out.append(p)
    return out


def _scan_file(path: Path, entropy: bool) -> list[Finding]:
    if _is_binary(path):
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    findings: list[Finding] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for m in find_matches(line):
            findings.append(Finding(path=path, line=lineno, rule=m.rule, match=m.text))
        if entropy:
            for em in ENTROPY_TOKEN_RE.finditer(line):
                token = em.group(1)
                if len(token) >= ENTROPY_MIN_LEN and shannon_entropy(token) >= ENTROPY_THRESHOLD:
                    findings.append(Finding(path=path, line=lineno, rule="high_entropy", match=token))
    return findings


def scan(
    target: Path,
    ignore: list[str] | None = None,
    entropy: bool = False,
    baseline: set[tuple[str, int, str]] | None = None,
) -> list[Finding]:
    target = Path(target)
    files = _iter_files(target, ignore or [])
    findings: list[Finding] = []
    for f in files:
        findings.extend(_scan_file(f, entropy=entropy))
    if baseline:
        findings = [
            f for f in findings
            if (str(f.path), f.line, f.rule) not in baseline
        ]
    return findings
