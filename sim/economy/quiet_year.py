"""Answers read from an economy between two of its steps, kept until it next steps.

The home port calls `settle` once a step has returned: from then until the economy steps again its record moves only by
the market memory's writes (counted by `market_memory.written_stamp`) and by a new setup (`Economy.change_setup`), and
both are checked here. Before any settled step (a loaded game's first year, a spin-up) nothing is kept."""
from typing import Any, Callable, Dict

from .market_memory import written_stamp

_settled: Dict[str, Any] = {"economy": None, "year": None}
_kept: Dict[str, Any] = {"economy": None, "setup": None, "writes": None, "year": None, "answers": {}}


def settle(economy) -> None:
    """The economy has just finished a step: its figures hold until the next one."""
    _settled["economy"], _settled["year"] = economy, economy.years_stepped


def is_settled(economy) -> bool:
    return _settled["economy"] is economy and _settled["year"] == economy.years_stepped


def kept(economy, key, compute: Callable[[], Any]) -> Any:
    """`compute()` once per `key` while the economy stays settled, the same object for every caller (copy it before
    handing it on); computed every time when it is not settled."""
    if not is_settled(economy):
        return compute()
    state = _kept
    if (state["economy"] is not economy or state["setup"] is not economy.setup or state["writes"] != written_stamp()
            or state["year"] != economy.years_stepped):
        state.update(economy=economy, setup=economy.setup, writes=written_stamp(), year=economy.years_stepped, answers={})
    answers = state["answers"]
    if key not in answers:
        answers[key] = compute()
    return answers[key]
