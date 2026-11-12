from textstats import top_words


def test_basic():
    assert top_words("a b a", 1) == [("a", 2)]
