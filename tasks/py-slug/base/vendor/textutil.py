"""Vendored from another team: do not edit."""

import re


def squash(text):
    return re.sub(r"[^a-z0-9]", "-", text)
