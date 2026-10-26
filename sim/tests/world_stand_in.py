"""The `needs` of an actors' world over plain values: a table view is given as its value (or a function of no arguments), a keyed view
as a dict (or a function of the key), a quote as a function of its arguments (see module_harness)."""
from typing import Any

from .module_harness import _FakeNeeds


def fake_needs(answers: Any = None, **views: Any) -> Any:
    """Views by name; `send` records the commands in `.sent` and answers as `answers` (command class -> reply or function) says."""
    return _FakeNeeds(views, answers or {})
