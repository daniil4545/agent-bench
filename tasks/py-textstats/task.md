`top_words` in `textstats.py` is correct but too slow: counting and ranking are quadratic, and
the whole thing is one long function. A report job on a 20,000-word text takes many seconds.

Refactor `textstats.py`:

1. Split the work into small functions (tokenizing, counting, ranking) and make `top_words` fast
   on large inputs: a text of tens of thousands of words, with thousands of distinct words, must
   take well under a second.
2. Behaviour must not change at all. The module docstring is the specification of the current
   behaviour; the existing results are the reference, including for empty input, non-ASCII text,
   ties and unusual characters.
3. Keep the public interface: the signatures and results of `tokenize` and `top_words`.
4. Add tests to `test_textstats.py`; `python3 -m pytest -q` must pass.

Scope: change only `textstats.py` and `test_textstats.py`. `report.py` and anything else must not
be touched.
