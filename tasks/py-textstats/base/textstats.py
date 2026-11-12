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


def tokenize(text: str) -> list[str]:
    words = []
    current = ""
    for i, ch in enumerate(text):
        if ch.isalpha() or ch.isdigit():
            current += ch
        elif ch == "'" and current and i + 1 < len(text) and (text[i + 1].isalpha() or text[i + 1].isdigit()):
            current += ch
        elif current:
            words.append(current)
            current = ""
    if current:
        words.append(current)
    return [w.casefold() for w in words]


def top_words(text: str, n: int = 10) -> list[tuple[str, int]]:
    counts = []
    for w in tokenize(text):
        for pair in counts:
            if pair[0] == w:
                pair[1] += 1
                break
        else:
            counts.append([w, 1])
    result = []
    remaining = list(counts)
    while remaining and len(result) < n:
        best = remaining[0]
        for p in remaining[1:]:
            if p[1] > best[1]:
                best = p
        remaining.remove(best)
        result.append((best[0], best[1]))
    return result
