import inspect
import random
import time

import pytest

import report
import textstats
from textstats import tokenize, top_words


@pytest.mark.parametrize("text, want", [
    ("", []),
    ("   \n\t ", []),
    ("Hello, hello WORLD", ["hello", "hello", "world"]),
    ("snake_case x_y", ["snake", "case", "x", "y"]),
    ("rock'n'roll", ["rock'n'roll"]),
    ("'tis the dogs' bone", ["tis", "the", "dogs", "bone"]),
    ("a''b", ["a", "b"]),
    ("it's", ["it's"]),
    ("don't 'quote' ", ["don't", "quote"]),
    ("Straße STRASSE", ["strasse", "strasse"]),
    ("naïve Привет ПРИВЕТ", ["naïve", "привет", "привет"]),
    ("x2 2x 22", ["x2", "2x", "22"]),
    ("Ⅷ ² é", ["²", "e"]),
    ("end'", ["end"]),
])
def test_tokenize(text, want):
    assert tokenize(text) == want


@pytest.mark.parametrize("text, n, want", [
    ("", 5, []),
    ("a b a", 0, []),
    ("a b a", -3, []),
    ("a b a", 100, [("a", 2), ("b", 1)]),
    ("b a b a c", 3, [("b", 2), ("a", 2), ("c", 1)]),
    ("c b a", 3, [("c", 1), ("b", 1), ("a", 1)]),
    ("Straße STRASSE strasse x", 2, [("strasse", 3), ("x", 1)]),
    ("z y z y x", 2, [("z", 2), ("y", 2)]),
])
def test_top_words(text, n, want):
    assert top_words(text, n) == want


def test_default_n_is_ten():
    text = " ".join(f"w{i}" for i in range(15))
    assert len(top_words(text)) == 10


def test_interface_unchanged():
    assert str(inspect.signature(top_words)) == "(text: str, n: int = 10) -> list[tuple[str, int]]"
    assert str(inspect.signature(tokenize)) == "(text: str) -> list[str]"
    assert all(isinstance(p, tuple) for p in top_words("a a b"))


def test_report_unchanged():
    assert report.format_report("b a b a c", 2) == "b: 2\na: 2"


def test_matches_reference_on_random_text():
    rng = random.Random(7)
    alphabet = list("abcAB_ '-ßSsé2") + ["\n", "'"]
    text = "".join(rng.choice(alphabet) for _ in range(3000))
    words = tokenize(text)
    expected = {}
    for w in words:
        expected[w] = expected.get(w, 0) + 1
    order = {w: i for i, w in enumerate(dict.fromkeys(words))}
    want = sorted(expected.items(), key=lambda kv: (-kv[1], order[kv[0]]))
    assert top_words(text, 50) == want[:50]


def test_large_input_is_fast():
    rng = random.Random(1)
    text = " ".join(f"w{rng.randrange(20000)}" for _ in range(60000))
    start = time.perf_counter()
    result = top_words(text, 10000)
    elapsed = time.perf_counter() - start
    assert len(result) == 10000
    assert elapsed < 1.0, f"{elapsed:.1f}s"


def test_module_still_has_helpers():
    assert hasattr(textstats, "tokenize")
