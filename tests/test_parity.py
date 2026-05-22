from pathlib import Path
from envguard.parity import parse_env, diff, Diff


def test_parse_env_handles_comments_and_blanks(tmp_path: Path):
    p = tmp_path / ".env"
    p.write_text("# comment\n\nFOO=1\nBAR=hello world\n")
    assert parse_env(p) == {"FOO": "1", "BAR": "hello world"}


def test_parse_env_strips_quotes(tmp_path: Path):
    p = tmp_path / ".env"
    p.write_text("FOO=\"quoted\"\nBAR='single'\n")
    assert parse_env(p) == {"FOO": "quoted", "BAR": "single"}


def test_parse_env_ignores_malformed_lines(tmp_path: Path):
    p = tmp_path / ".env"
    p.write_text("FOO=1\nnot a kv line\nBAR=2\n")
    assert parse_env(p) == {"FOO": "1", "BAR": "2"}


def test_diff_finds_each_category():
    env =     {"A": "1", "B": "", "C": "3"}
    example = {"A": "placeholder", "B": "placeholder", "D": "placeholder"}
    d = diff(env, example)
    assert d == Diff(
        missing_in_example=["C"],
        missing_in_env=["D"],
        empty_in_env=["B"],
    )


def test_diff_sorted_output():
    d = diff({"Z": "1", "A": "1"}, {})
    assert d.missing_in_example == ["A", "Z"]
