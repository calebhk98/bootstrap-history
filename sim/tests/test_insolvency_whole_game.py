"""Scenario (Complaint 640): a founder driven deep into debt climbs back and keeps what the goal needs. The rules of
default and settlement (a settlement never abandons a persona or institution, the debt after it is inside the
line) are tested one at a time in test_insolvency_rules.py; this keeps only the recovery over whole Rome years,
which reads the founder's money and so needs full steps
(python3 -m sim.tests --slow --only insolvency_whole_game --timing measures it)."""

from .harness import *  # noqa: F401,F403
from sim.engine.data import closure as data_closure

RUIN_YEARS = 5   # full market years after the ruin: the founder's money climbs back within them


def without_market(game):
    """`game` with the year's market close (nearly all of a step) left out of its steps."""
    game._step_market = lambda: None
    return game


# A founder driven deep into debt climbs back and keeps what the goal needs.
def _ruined_founder_run():
    ruined = sim(manual=False, capital=hours_money(20200000))
    ruined.labour.buy_slaves(400)
    ruined.start_project("identity_cover")
    without_market(ruined)
    for _ in range(3):   # until the persona is built
        ruined.step()
        if "identity_cover" in ruined.done:
            break
    del ruined._step_market   # the market closes again
    needed = data_closure(NODES, GOAL) & (ruined.done - ruined.granted)
    built_before = len(ruined.done - ruined.granted)
    ruined.capital = -3.0 * ruined.credit_limit()
    debt_over_limit = []
    capital_by_year = []
    for _ in range(RUIN_YEARS):
        ruined.step()
        debt_over_limit.append(-ruined.capital / ruined.credit_limit())
        capital_by_year.append(ruined.capital)
    return ruined, needed, built_before, debt_over_limit, capital_by_year


_RUIN = {}


def _ruin():
    if not _RUIN:
        _RUIN["run"] = _ruined_founder_run()
    return _RUIN["run"]


# the money climbs back at some point in the years; once it has, the founder may spend it on projects
slow_check("a ruined founder rebuilds rather than freezing",
           lambda: (max(_ruin()[4]) > _ruin()[4][0] and len(_ruin()[0].done - _ruin()[0].granted) >= _ruin()[2],
                    (_ruin()[4], _ruin()[2], len(_ruin()[0].done - _ruin()[0].granted))))
slow_check("ruin never deletes a step the goal needs",
           lambda: ("identity_cover" in _ruin()[0].done and _ruin()[1] <= _ruin()[0].done,
                    sorted(_ruin()[1] - _ruin()[0].done)[:5]))
