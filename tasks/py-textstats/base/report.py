"""Plain-text report built on textstats. Other code depends on this module."""

from textstats import top_words


def format_report(text: str, n: int = 3) -> str:
    return "\n".join(f"{word}: {count}" for word, count in top_words(text, n))
