"""Auth module for golden demo — contains a deliberate bug."""


def normalize_token(token: str) -> str:
    # Bug: should strip surrounding whitespace before validation.
    return token.lower()