"""Build URL slugs from titles."""

from vendor.textutil import squash


def slugify(title: str) -> str:
    return squash(title.lower())
