"""Parse short durations like "1h30m" into seconds."""

import re

UNITS = {"h": 3600, "m": 60, "s": 1}


def parse_duration(text: str) -> int:
    text = text.strip()
    if not re.fullmatch(r"(\d+[hms])+", text):
        raise ValueError(f"bad duration: {text!r}")
    return sum(int(v) * UNITS[u] for v, u in re.findall(r"(\d+)([hms])", text))
