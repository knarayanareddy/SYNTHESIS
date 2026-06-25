"""Test file for golden demo — contains a failing test for normalize_token."""
from src.auth import normalize_token


def test_token_normalization_strips_whitespace():
    assert normalize_token("  ABC  ") == "abc"