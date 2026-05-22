# envguard — Design Spec

**Date:** 2026-05-22
**Status:** Draft (pending implementation plan)

## Purpose

`envguard` is a Python CLI that protects projects from two related risks:

1. **Leaked secrets** committed to source code (API keys, tokens, passwords).
2. **Drift between `.env` and `.env.example`** that breaks new contributors and CI.

It runs locally, as a pre-commit hook, or as a GitHub Action.

## Goals (v1)

- Detect common secret formats by regex.
- Optional high-entropy string detection.
- Verify `.env` ↔ `.env.example` key parity.
- Single CLI: `envguard scan`, `envguard parity`, `envguard check`.
- Human-readable and JSON output.
- Pre-commit hook integration.
- GitHub composite Action.
- pytest suite with fixtures.

## Non-Goals (v1)

- Deep AST analysis (Python/JS/etc.).
- Git history scanning (only working tree).
- Secret rotation or remediation.
- Custom plugin/rule loading at runtime (rules live in `patterns.py`; PRs add new ones).
- TruffleHog / gitleaks parity. This is a focused, opinionated tool.

## Architecture

Single Python package, focused modules:

```
envguard/
  __init__.py
  cli.py          # argparse entry, exit codes
  scanner.py      # file walk + regex + entropy detection
  parity.py       # .env vs .env.example diff
  patterns.py     # named secret regexes
  report.py       # text + JSON formatters
tests/
  test_scanner.py
  test_parity.py
  test_cli.py
  fixtures/
.pre-commit-hooks.yaml
.github/
  workflows/ci.yml
  action.yml      # composite action
README.md
pyproject.toml
LICENSE           # MIT
```

### Module responsibilities

| Module     | Responsibility                                                                 |
| ---------- | ------------------------------------------------------------------------------ |
| `cli`      | Parse args, dispatch to subcommand, set exit code.                             |
| `scanner`  | Walk a path, honor `.gitignore` and `--ignore`, skip binaries, run rules.      |
| `patterns` | Named regex rules + entropy helper.                                            |
| `parity`   | Parse env-style files, return `Diff` object.                                   |
| `report`   | Render findings as colored text or JSON.                                       |

Each module is importable and unit-testable in isolation.

## Detection Rules (v1)

Built-in named patterns in `patterns.py`:

| Name             | Regex                                                            |
| ---------------- | ---------------------------------------------------------------- |
| `aws_access_key` | `AKIA[0-9A-Z]{16}`                                               |
| `github_pat`     | `ghp_[A-Za-z0-9]{36}`                                            |
| `slack_token`    | `xox[baprs]-[A-Za-z0-9-]{10,}`                                   |
| `private_key`    | `-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----`                |
| `generic_secret` | `(?i)(api[_-]?key|secret|password|token)\s*=\s*['"][^'"\n]{8,}` |

Entropy rule (opt-in via `--entropy`):
- Shannon entropy ≥ 4.5 over a string of length ≥ 20, restricted to base64/hex character sets.

## CLI

```
envguard scan    [--path PATH] [--ignore GLOB ...] [--entropy]
                 [--baseline FILE] [--write-baseline FILE]
                 [--format text|json]
envguard parity  [--env FILE] [--example FILE] [--format text|json]
envguard check   [...all of the above...]   # runs scan + parity
envguard --version
```

**Defaults**: `--path .`, `--env .env`, `--example .env.example`, `--format text`.

**Baseline file**: line-oriented allowlist of `path:line:rule_name` entries; matching findings are suppressed. Generated via `envguard scan --write-baseline .envguard-baseline`.

**Parity when `.env` is absent** (typical in CI): if `--env` file does not exist, parity check is skipped with an info note (exit code unaffected). Hard error only when an explicitly passed path is missing.

**Exit codes**:
- `0` clean
- `1` findings present
- `2` usage / IO error

## Parity Logic

Parse both env files line-by-line (`KEY=VALUE`, ignore comments and blanks).

Produce a `Diff`:
- `missing_in_example`: keys in `.env` not in `.env.example`
- `missing_in_env`: keys in `.env.example` not in `.env`
- `empty_in_env`: keys present in `.env` with empty value but with placeholder in example

Values themselves are never compared or printed (avoid leaking secrets).

## Output

**Text** (colored, one finding per line):
```
findings: 2
.env.example: missing key DATABASE_URL (present in .env)
src/config.py:14  github_pat  ghp_****************************MASKED
```

**JSON**:
```json
{
  "scan": {
    "findings": [
      {"path": "src/config.py", "line": 14, "rule": "github_pat", "match": "ghp_***...MASKED"}
    ]
  },
  "parity": {
    "missing_in_example": ["DATABASE_URL"],
    "missing_in_env": [],
    "empty_in_env": []
  }
}
```

Secret values are always masked in output (first 4 chars + `***MASKED`).

## File Walking

- Start from `--path`.
- Skip binary files (null byte heuristic on first 8KB).
- Honor `.gitignore` via the `pathspec` library.
- Always skip: `.git/`, `node_modules/`, `.venv/`, `venv/`, `__pycache__/`, `dist/`, `build/`.
- Additional ignores via `--ignore GLOB` (repeatable).

## Pre-commit Hook

`.pre-commit-hooks.yaml`:

```yaml
- id: envguard
  name: envguard
  entry: envguard check
  language: python
  pass_filenames: false
  stages: [commit]
```

## GitHub Action

`action.yml` composite action:

```yaml
name: envguard
description: Scan for leaked secrets and .env parity drift.
inputs:
  path:
    default: .
runs:
  using: composite
  steps:
    - uses: actions/setup-python@v5
      with: { python-version: '3.11' }
    - run: pip install envguard
      shell: bash
    - run: envguard check --path ${{ inputs.path }} --format json
      shell: bash
```

CI workflow (`workflows/ci.yml`) runs pytest on push and PR.

## Testing

- **scanner**: fixtures containing planted fake secrets per rule; assert each rule fires exactly where expected and not elsewhere.
- **parity**: fixtures with constructed `.env` + `.env.example` pairs covering each diff category.
- **cli**: subprocess invocation; assert exit codes and JSON shape.
- **baseline**: write baseline, re-run scan, assert clean.

Target: > 90% line coverage on core modules.

## Packaging

- `pyproject.toml` with `hatchling` build backend.
- Console entry point: `envguard = envguard.cli:main`.
- Python ≥ 3.10.
- Dependencies: `pathspec`, `colorama` (Windows color). Stdlib otherwise.

## License

MIT.

## Open Questions

None at spec time.
