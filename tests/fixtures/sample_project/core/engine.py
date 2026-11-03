"""The engine: does the work, delegates formatting to utils."""

from .utils import format_result


def run() -> str:
    result = format_result("hello")
    return check_result(result)


def check_result(value: str) -> str:
    # Deliberately branchy so the hotspot detector has something to find.
    if not value:
        return "empty"
    if len(value) > 10:
        return "long"
    for char in value:
        if char == "x":
            return "has-x"
        while False:
            pass
    try:
        int(value)
    except ValueError:
        return "not-a-number"
    return value


def unused_engine_helper() -> None:
    """Nothing calls this — repoxray should flag it as dead code."""
