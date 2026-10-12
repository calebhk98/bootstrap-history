"""Insolvency over whole Rome years: a settlement never abandons a persona or institution, and a founder driven
deep into debt stays inside the credit line, climbs back and keeps what the goal needs. The settlement and the
building of the persona do not depend on the market close, so those years leave it out; the ruined founder's
recovery reads the founder's money, which follows the market close, so its years are full steps
(python3 -m sim.tests --slow --only insolvency_whole_game --timing measures it)."""

from .harness import *  # noqa: F401,F403
from sim.engine.data import closure as data_closure

RUIN_YEARS = 3   # full market years after the ruin: the founder's money has turned round within them


def without_market(game):
    """`game` with the year's market close (nearly all of a step) left out of its steps."""
    game._step_market = lambda: None
    return game


# Rome carries no debt bondage, so a deep debt ends in a written-off settlement.
insolvent = without_market(sim(civ="rome_100ad", capital=1000000.0))
insolvent.start_project("identity_cover")
for _ in range(4):  # until the persona is built
    insolvent.step()
    if "identity_cover" in insolvent.done:
        break
persona_built = "identity_cover" in insolvent.done
insolvent.capital = -2.0 * insolvent.credit_limit()
for _ in range(2):  # until the settlement is logged
    insolvent.step()
    if any("INSOLVENCY SETTLED" in text for _, text in insolvent.state.household.log):
        break
settled = [text for _, text in insolvent.state.household.log if "INSOLVENCY SETTLED" in text]
check("an insolvency settlement never abandons a persona or institution",
      persona_built and settled and "identity_cover" in insolvent.done,
      (persona_built, len(settled), "identity_cover" in insolvent.done))

# A founder driven deep into debt stays inside the credit line, climbs back, and keeps what the goal needs.
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


slow_check("a ruined founder's debt stays inside the credit limit once the settlement has run",
           lambda: (max(_ruin()[3]) <= 1.0 and any("INSOLVENCY SETTLED" in text for _, text in _ruin()[0].state.household.log),
                    _ruin()[3]))
slow_check("a ruined founder rebuilds rather than freezing",
           lambda: (_ruin()[4][-1] > _ruin()[4][0] and len(_ruin()[0].done - _ruin()[0].granted) >= _ruin()[2],
                    (_ruin()[4], _ruin()[2], len(_ruin()[0].done - _ruin()[0].granted))))
slow_check("ruin never deletes a step the goal needs",
           lambda: ("identity_cover" in _ruin()[0].done and _ruin()[1] <= _ruin()[0].done,
                    sorted(_ruin()[1] - _ruin()[0].done)[:5]))
