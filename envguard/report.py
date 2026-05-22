import json
from typing import Iterable

from envguard.parity import Diff
from envguard.scanner import Finding, mask


def render_text(findings: Iterable[Finding], parity: Diff) -> str:
    findings = list(findings)
    lines: list[str] = []
    if not findings and parity.is_clean():
        return "envguard: clean"
    lines.append(f"findings: {len(findings)}")
    for f in findings:
        lines.append(f"{f.path}:{f.line}  {f.rule}  {mask(f.match)}")
    if not parity.is_clean():
        lines.append("parity:")
        for k in parity.missing_in_example:
            lines.append(f"  missing in .env.example: {k}")
        for k in parity.missing_in_env:
            lines.append(f"  missing in .env:         {k}")
        for k in parity.empty_in_env:
            lines.append(f"  empty in .env:           {k}")
    return "\n".join(lines)


def render_json(findings: Iterable[Finding], parity: Diff) -> str:
    payload = {
        "scan": {
            "findings": [
                {"path": str(f.path), "line": f.line, "rule": f.rule, "match": mask(f.match)}
                for f in findings
            ]
        },
        "parity": {
            "missing_in_example": parity.missing_in_example,
            "missing_in_env": parity.missing_in_env,
            "empty_in_env": parity.empty_in_env,
        },
    }
    return json.dumps(payload, indent=2)
