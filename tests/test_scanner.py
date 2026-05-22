from pathlib import Path
from envguard.scanner import scan, Finding, mask


FIXTURES = Path(__file__).parent / "fixtures"


def test_scan_clean_file_returns_no_findings():
    findings = scan(FIXTURES / "clean.py")
    assert findings == []


def test_scan_dirty_file_finds_github_pat_and_generic_secret():
    findings = scan(FIXTURES / "dirty.py")
    rules = {f.rule for f in findings}
    assert "github_pat" in rules
    assert "generic_secret" in rules


def test_scan_directory_walks_and_skips_clean_files():
    findings = scan(FIXTURES)
    paths = {f.path.name for f in findings}
    assert "dirty.py" in paths
    assert "clean.py" not in paths


def test_scan_respects_ignore_globs(tmp_path: Path):
    f = tmp_path / "leak.py"
    f.write_text('TOKEN = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"\n')
    assert scan(tmp_path) != []
    assert scan(tmp_path, ignore=["*.py"]) == []


def test_scan_skips_binary_files(tmp_path: Path):
    f = tmp_path / "blob.bin"
    f.write_bytes(b"\x00\x01\x02" + b"ghp_abcdefghijklmnopqrstuvwxyz0123456789")
    assert scan(tmp_path) == []


def test_scan_skips_default_dirs(tmp_path: Path):
    bad_dir = tmp_path / ".git"
    bad_dir.mkdir()
    (bad_dir / "leak.py").write_text('TOKEN = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"\n')
    assert scan(tmp_path) == []


def test_finding_has_line_number(tmp_path: Path):
    f = tmp_path / "x.py"
    f.write_text("\n\nTOKEN = 'ghp_abcdefghijklmnopqrstuvwxyz0123456789'\n")
    findings = scan(tmp_path)
    assert findings[0].line == 3


def test_mask_preserves_prefix_only():
    assert mask("ghp_abcdefghijklmnopqrstuvwxyz0123456789").startswith("ghp_")
    assert "MASKED" in mask("ghp_abcdefghijklmnopqrstuvwxyz0123456789")


def test_scan_with_baseline_suppresses(tmp_path: Path):
    f = tmp_path / "x.py"
    f.write_text("xx = 'ghp_abcdefghijklmnopqrstuvwxyz0123456789'\n")
    baseline = {(str(f), 1, "github_pat")}
    assert scan(tmp_path, baseline=baseline) == []


def test_scan_entropy_off_by_default(tmp_path: Path):
    f = tmp_path / "x.py"
    f.write_text("noise = 'Zk3fp9Lq2xV7nB1cR8sT4dY6'\n")
    assert scan(tmp_path) == []


def test_scan_entropy_on_flags_high_entropy(tmp_path: Path):
    f = tmp_path / "x.py"
    f.write_text("noise = 'Zk3fp9Lq2xV7nB1cR8sT4dY6'\n")
    findings = scan(tmp_path, entropy=True)
    assert any(f.rule == "high_entropy" for f in findings)
