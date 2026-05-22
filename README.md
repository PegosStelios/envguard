# envguard

Scan repos for leaked secrets and verify `.env` / `.env.example` parity. Runs locally, as a pre-commit hook, or as a GitHub Action.

## Install

```bash
pip install envguard
```

## Usage

```bash
envguard scan                       # secret scan only
envguard parity                     # .env vs .env.example only
envguard check                      # both
envguard scan --format json
envguard scan --entropy             # opt-in high-entropy detection
envguard scan --write-baseline .envguard-baseline
envguard scan --baseline .envguard-baseline
```

Exit codes: `0` clean, `1` findings, `2` usage error.

## Pre-commit

```yaml
repos:
  - repo: https://github.com/<you>/envguard
    rev: v0.1.1
    hooks:
      - id: envguard
```

## GitHub Action

```yaml
- uses: <you>/envguard@v0.1.1
  with:
    path: .
```

## Detected secret patterns (v1)

- AWS access keys (`AKIA…`)
- GitHub personal access tokens (`ghp_…`)
- Slack tokens (`xoxb-…`, etc.)
- Private key headers (RSA / EC / OpenSSH / DSA)
- Generic `(api_key|secret|password|token) = '…'`
- High-entropy strings (opt-in via `--entropy`)

## License

MIT.
