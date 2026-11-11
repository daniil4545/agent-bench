`slugify` in `slug.py` should turn a title into a URL slug: lowercase, words joined by a single
dash, no leading or trailing dash. Today `slugify("  Hello,   World!! ")` returns
`"-hello-world-"`; it must return `"hello-world"`. Any run of characters other than letters and
digits counts as one separator.

Fix `slugify` and add tests to `test_slug.py`; `python3 -m pytest -q` must pass.

Scope: change only `slug.py` and `test_slug.py`. Everything else, including `vendor/`, is off
limits.
