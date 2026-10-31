import pytest

from duration import parse_duration


@pytest.mark.parametrize("text, want", [
    ("1h30m", 5400),
    ("45s", 45),
    ("2h5s", 7205),
    ("1h1m1s", 3661),
    (" 10m ", 600),
])
def test_valid(text, want):
    assert parse_duration(text) == want


@pytest.mark.parametrize("text", ["", "   ", "abc", "10", "1x", "1h junk", "h"])
def test_invalid(text):
    with pytest.raises(ValueError):
        parse_duration(text)
