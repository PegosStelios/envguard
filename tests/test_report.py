import json
from pathlib import Path

from envguard.parity import Diff
from envguard.report import render_text, render_json
from envguard.scanner import Finding


def test_render_text_clean():
    out = render_text(findings=[], parity=Diff())
    assert "clean" in out.lower()


def test_render_text_shows_findings_and_masks_secrets():
    findings = [Finding(path=Path("src/x.py"), line=12, rule="github_pat",
                        match="ghp_abcdefghijklmnopqrstuvwxyz0123456789")]
    out = render_text(findings=findings, parity=Diff())
    assert "src/x.py" in out
    assert "12" in out
    assert "github_pat" in out
    assert "MASKED" in out
    assert "ghp_abcdefghij" not in out


def test_render_text_shows_parity_keys_only():
    parity = Diff(missing_in_example=["DATABASE_URL"], missing_in_env=["FEATURE_FLAG"], empty_in_env=["API_KEY"])
    out = render_text(findings=[], parity=parity)
    assert "DATABASE_URL" in out
    assert "FEATURE_FLAG" in out
    assert "API_KEY" in out


def test_render_json_structure():
    findings = [Finding(path=Path("src/x.py"), line=12, rule="github_pat",
                        match="ghp_abcdefghijklmnopqrstuvwxyz0123456789")]
    parity = Diff(missing_in_example=["DB"])
    out = render_json(findings=findings, parity=parity)
    data = json.loads(out)
    assert data["scan"]["findings"][0] == {
        "path": "src/x.py", "line": 12, "rule": "github_pat",
        "match": "ghp_***MASKED",
    }
    assert data["parity"]["missing_in_example"] == ["DB"]
    assert data["parity"]["missing_in_env"] == []
    assert data["parity"]["empty_in_env"] == []
