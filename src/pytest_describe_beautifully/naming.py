"""Human-readable name formatting for pytest-describe nodes."""


def humanize_describe_name(name: str) -> str:
    """Convert a describe block name to a human-readable display name.

    - "describe_MyClass" → "MyClass" (preserves CamelCase)
    - "describe_my_feature" → "my feature" (snake_case → spaces)
    - "describe_" prefix is stripped; if remainder has no underscores and
      starts with uppercase, it's treated as a class name and returned as-is.
    """
    # Strip all known describe prefixes
    stripped = name
    for prefix in ("describe_", "Describe_"):
        if stripped.startswith(prefix):
            stripped = stripped[len(prefix) :]
            break

    if not stripped:
        return name

    # If it looks like CamelCase (starts uppercase, no underscores), preserve it
    if stripped[0].isupper() and "_" not in stripped:
        return stripped

    # Otherwise treat as snake_case → spaces
    return stripped.replace("_", " ")


def humanize_test_name(name: str) -> str:
    """Convert a test function name to a human-readable display name.

    - "it_does_something" → "it does something"
    - "they_are_equal" → "they are equal"
    """
    return name.replace("_", " ")


def format_duration(seconds: float) -> str:
    """Format a duration in seconds to a human-readable string.

    - < 1s: "123ms"
    - 1s to < 60s: "2.50s"
    - >= 60s: "2m 5.0s"
    """
    if seconds < 1.0:
        ms = seconds * 1000
        return f"{ms:.0f}ms"
    if seconds < 60.0:
        return f"{seconds:.2f}s"
    minutes = int(seconds // 60)
    remaining = seconds - minutes * 60
    return f"{minutes}m {remaining:.1f}s"
