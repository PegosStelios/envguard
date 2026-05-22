import pytest
from envguard.patterns import RULES, shannon_entropy, find_matches


@pytest.mark.parametrize("rule_name,text", [
    ("aws_access_key", "AKIAIOSFODNN7EXAMPLE"),
    ("github_pat",     "ghp_abcdefghijklmnopqrstuvwxyz0123456789"),
    ("slack_token",    "xoxb-1234567890-abcdefghij"),
    ("private_key",    "-----BEGIN RSA PRIVATE KEY-----"),
    ("generic_secret", "API_KEY = 'supersecretvalue'"),
])
def test_rules_match_known_secrets(rule_name, text):
    rule = next(r for r in RULES if r.name == rule_name)
    assert rule.pattern.search(text) is not None


def test_rules_do_not_match_innocuous_text():
    text = "hello world, nothing to see here"
    for rule in RULES:
        assert rule.pattern.search(text) is None


def test_find_matches_returns_rule_name_and_span():
    line = "token = 'ghp_abcdefghijklmnopqrstuvwxyz0123456789'"
    matches = find_matches(line)
    names = {m.rule for m in matches}
    assert "github_pat" in names


def test_shannon_entropy_high_for_random_string():
    assert shannon_entropy("Zk3$f@p9Lq2!xV7nB1cR") > 4.0


def test_shannon_entropy_low_for_repetitive():
    assert shannon_entropy("aaaaaaaaaaaaaaaa") < 1.0
