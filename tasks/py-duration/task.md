`parse_duration` in `duration.py` does not understand seconds and silently returns 0 on garbage input.

Required:
1. Support the unit `s` ("45s" is 45, "1h1m1s" is 3661). Whitespace around the string is allowed.
2. An empty string, a string without units, an unknown unit or any extra characters raise `ValueError`.
3. Add tests for the new behaviour to `test_duration.py`; `python3 -m pytest -q` must pass.

Scope: change only `duration.py` and `test_duration.py`. Do not touch `vendor/`.
