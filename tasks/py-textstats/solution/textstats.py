"""Word statistics.

Specification (the current behaviour; it must not change):

* A word character is a character for which `str.isalpha()` or `str.isdigit()` is true.
* A word is a maximal run of word characters. A single apostrophe (') directly between
  two word characters belongs to the word ("rock'n'roll" is one word); any other
  apostrophe is a separator.
* Words are compared and reported case-folded (`str.casefold`).
* `top_words` returns at most `n` pairs `(word, count)`, most frequent first. Words with the
  same count keep the order of their first occurrence in the text. `n <= 0` gives `[]`.
"""


def _is_word_char(ch: str) -> bool:
    return ch.isalpha() or ch.isdigit()


def tokenize(text: str) -> list[str]:
    words = []
    start = None
    for i, ch in enumerate(text):
        if _is_word_char(ch):
            if start is None:
                start = i
        elif ch == "'" and start is not None and i + 1 < len(text) and _is_word_char(text[i + 1]):
            continue
        elif start is not None:
            words.append(text[start:i])
            start = None
    if start is not None:
        words.append(text[start:])
    return [w.casefold() for w in words]


def count_words(words: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for w in words:
        counts[w] = counts.get(w, 0) + 1
    return counts


def rank(counts: dict[str, int], n: int) -> list[tuple[str, int]]:
    if n <= 0:
        return []
    return sorted(counts.items(), key=lambda kv: -kv[1])[:n]


def top_words(text: str, n: int = 10) -> list[tuple[str, int]]:
    return rank(count_words(tokenize(text)), n)
