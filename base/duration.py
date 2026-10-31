"""Parse short durations like "1h30m" into seconds."""

import re

UNITS = {"h": 3600, "m": 60}


def parse_duration(text: str) -> int:
    total = 0
    for value, unit in re.findall(r"(\d+)([hm])", text):
        total += int(value) * UNITS[unit]
    return total
