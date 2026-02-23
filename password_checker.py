"""Password strength checker module."""

import re


def check_password_strength(password: str) -> int:
    """
    Check the strength of a password and return a score from 0 to 100.

    Criteria evaluated:
    - Length (minimum 8 characters required, bonus for longer)
    - Contains uppercase letters
    - Contains lowercase letters
    - Contains numbers
    - Contains special characters

    Args:
        password: The password string to evaluate.

    Returns:
        An integer score from 0 to 100 indicating password strength.
    """
    if not password:
        return 0

    score = 0

    # Length scoring (max 40 points)
    length = len(password)
    if length >= 8:
        score += 20
    if length >= 12:
        score += 10
    if length >= 16:
        score += 10

    # Character type checks (15 points each, max 60 points)
    if re.search(r"[A-Z]", password):
        score += 15

    if re.search(r"[a-z]", password):
        score += 15

    if re.search(r"[0-9]", password):
        score += 15

    if re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:'\",.<>?/\\`~]", password):
        score += 15

    return min(score, 100)


if __name__ == "__main__":
    # Quick test
    test_passwords = [
        "",
        "short",
        "password",
        "Password1",
        "Password1!",
        "MyStr0ng!Pass#2024",
    ]
    for pwd in test_passwords:
        print(f"{pwd!r:25} -> {check_password_strength(pwd)}")
