import math
import re
from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern


@dataclass(frozen=True)
class Match:
    rule: str
    start: int
    end: int
    text: str


RULES: tuple[Rule, ...] = (
    Rule("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    Rule("github_pat",     re.compile(r"ghp_[A-Za-z0-9]{36}")),
    Rule("slack_token",    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    Rule("private_key",    re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA |)PRIVATE KEY-----")),
    Rule("generic_secret", re.compile(
        r"(?i)(?:api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"\n]{8,}"
    )),
)


def find_matches(line: str) -> list[Match]:
    out: list[Match] = []
    for rule in RULES:
        for m in rule.pattern.finditer(line):
            out.append(Match(rule=rule.name, start=m.start(), end=m.end(), text=m.group(0)))
    return out


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())
