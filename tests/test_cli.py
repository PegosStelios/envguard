import json
import subprocess
import sys
from pathlib import Path


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "envguard.cli", *args],
        capture_output=True, text=True, cwd=cwd,
    )


def test_version_flag():
    r = run("--version")
    assert r.returncode == 0
    assert "0.1.2" in r.stdout


def test_scan_clean_exits_zero(tmp_path: Path):
    (tmp_path / "ok.py").write_text("x = 1\n")
    r = run("scan", "--path", str(tmp_path))
    assert r.returncode == 0


def test_scan_dirty_exits_one(tmp_path: Path):
    (tmp_path / "leak.py").write_text(
        "xx = 'ghp_abcdefghijklmnopqrstuvwxyz0123456789'\n"
    )
    r = run("scan", "--path", str(tmp_path))
    assert r.returncode == 1
    assert "github_pat" in r.stdout


def test_parity_detects_drift(tmp_path: Path):
    (tmp_path / ".env").write_text("FOO=1\nBAR=2\n")
    (tmp_path / ".env.example").write_text("FOO=placeholder\nBAZ=placeholder\n")
    r = run("parity", "--env", str(tmp_path / ".env"),
            "--example", str(tmp_path / ".env.example"))
    assert r.returncode == 1
    assert "BAR" in r.stdout
    assert "BAZ" in r.stdout


def test_parity_skipped_when_env_missing(tmp_path: Path):
    (tmp_path / ".env.example").write_text("FOO=placeholder\n")
    r = run("parity", "--env", str(tmp_path / ".env"),
            "--example", str(tmp_path / ".env.example"))
    assert r.returncode == 0
    assert "skipped" in r.stdout.lower() or "clean" in r.stdout.lower()


def test_check_combines_scan_and_parity(tmp_path: Path):
    (tmp_path / "leak.py").write_text(
        "xx = 'ghp_abcdefghijklmnopqrstuvwxyz0123456789'\n"
    )
    (tmp_path / ".env").write_text("FOO=1\n")
    (tmp_path / ".env.example").write_text("BAR=placeholder\n")
    r = run("check", "--path", str(tmp_path),
            "--env", str(tmp_path / ".env"),
            "--example", str(tmp_path / ".env.example"))
    assert r.returncode == 1


def test_json_format(tmp_path: Path):
    (tmp_path / "leak.py").write_text(
        "xx = 'ghp_abcdefghijklmnopqrstuvwxyz0123456789'\n"
    )
    r = run("scan", "--path", str(tmp_path), "--format", "json")
    data = json.loads(r.stdout)
    assert data["scan"]["findings"][0]["rule"] == "github_pat"


def test_write_baseline_then_clean(tmp_path: Path):
    (tmp_path / "leak.py").write_text(
        "xx = 'ghp_abcdefghijklmnopqrstuvwxyz0123456789'\n"
    )
    baseline = tmp_path / ".envguard-baseline"
    r1 = run("scan", "--path", str(tmp_path), "--write-baseline", str(baseline))
    assert r1.returncode == 0
    assert baseline.exists()
    r2 = run("scan", "--path", str(tmp_path), "--baseline", str(baseline))
    assert r2.returncode == 0


def test_usage_error_exits_two():
    r = run("scan", "--bogus-flag")
    assert r.returncode == 2
