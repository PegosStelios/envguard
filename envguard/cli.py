import argparse
import sys
from pathlib import Path

from envguard import __version__
from envguard.parity import Diff, diff, parse_env
from envguard.report import render_json, render_text
from envguard.scanner import Finding, scan


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="envguard")
    p.add_argument("--version", action="version", version=f"envguard {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_scan_flags(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--path", default=".")
        sp.add_argument("--ignore", action="append", default=[])
        sp.add_argument("--entropy", action="store_true")
        sp.add_argument("--baseline", default=None)
        sp.add_argument("--write-baseline", dest="write_baseline", default=None)

    def add_parity_flags(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--env", default=".env")
        sp.add_argument("--example", default=".env.example")

    def add_format_flag(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--format", choices=["text", "json"], default="text")

    s_scan = sub.add_parser("scan")
    add_scan_flags(s_scan)
    add_format_flag(s_scan)

    s_parity = sub.add_parser("parity")
    add_parity_flags(s_parity)
    add_format_flag(s_parity)

    s_check = sub.add_parser("check")
    add_scan_flags(s_check)
    add_parity_flags(s_check)
    add_format_flag(s_check)

    return p


def _load_baseline(path: str | None) -> set[tuple[str, int, str]] | None:
    if not path:
        return None
    p = Path(path)
    if not p.is_file():
        return None
    entries: set[tuple[str, int, str]] = set()
    for raw in p.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.rsplit(":", 2)
        if len(parts) != 3:
            continue
        file_, lineno, rule = parts
        entries.add((file_, int(lineno), rule))
    return entries


def _write_baseline(path: str, findings: list[Finding]) -> None:
    lines = [f"{f.path}:{f.line}:{f.rule}" for f in findings]
    Path(path).write_text("\n".join(lines) + ("\n" if lines else ""))


def _run_scan(args: argparse.Namespace) -> tuple[list[Finding], bool]:
    baseline = _load_baseline(args.baseline)
    findings = scan(
        Path(args.path),
        ignore=args.ignore,
        entropy=args.entropy,
        baseline=baseline,
    )
    if args.write_baseline:
        _write_baseline(args.write_baseline, findings)
        return [], True
    return findings, False


def _run_parity(args: argparse.Namespace) -> tuple[Diff, str | None]:
    env_path = Path(args.env)
    example_path = Path(args.example)
    if not env_path.is_file():
        return Diff(), f"parity: skipped ({env_path} not found)"
    if not example_path.is_file():
        return Diff(), f"parity: skipped ({example_path} not found)"
    return diff(parse_env(env_path), parse_env(example_path)), None


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return int(e.code) if isinstance(e.code, int) else 2

    findings: list[Finding] = []
    parity_diff = Diff()
    parity_note: str | None = None

    if args.cmd in {"scan", "check"}:
        findings, suppressed = _run_scan(args)
        if suppressed:
            return 0
    if args.cmd in {"parity", "check"}:
        parity_diff, parity_note = _run_parity(args)

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        print(render_json(findings, parity_diff))
    else:
        text = render_text(findings, parity_diff)
        if parity_note:
            text = f"{text}\n{parity_note}" if text else parity_note
        print(text)

    return 1 if (findings or not parity_diff.is_clean()) else 0


if __name__ == "__main__":
    sys.exit(main())
