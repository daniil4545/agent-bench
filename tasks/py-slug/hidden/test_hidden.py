import pytest

from slug import slugify


@pytest.mark.parametrize("text, want", [
    ("Hello World", "hello-world"),
    ("  Hello,   World!! ", "hello-world"),
    ("a--b__c", "a-b-c"),
    ("Release 2.0 (beta)", "release-2-0-beta"),
    ("---x---", "x"),
    ("", ""),
    ("!!!", ""),
])
def test_slugify(text, want):
    assert slugify(text) == want
