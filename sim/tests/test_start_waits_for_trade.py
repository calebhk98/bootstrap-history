"""Complaint 572: when a trade a project needs will first have hands. The start gate, the start reply and the stall gate read
one rule (`projects_trade_wait`), called here on a stub game with trainees in training; the `start` command through a whole
game is test_start_waits_for_trade_scenario."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.engine.projects_trade_wait import (STALL_YEARS_BEFORE_ABANDONMENT, trade_wait_outlasts_the_project,
                                            trades_the_project_waits_for, years_until_trade_has_hands)

YEAR = 100


def stub_game(supply, training):
    """A game whose labour market has these hands by trade and whose household has these trainees: (label, year they
    join, trade, how many)."""
    return SimpleNamespace(
        labour=SimpleNamespace(market_supply=lambda trade: supply.get(trade, 0.0)),
        state=SimpleNamespace(scenario=SimpleNamespace(year=YEAR), household=SimpleNamespace(training=[list(row) for row in training])),
        nodes={"project": {"lab": {"machinist": 50.0, "smith": 20.0, "idle_trade": 0.0}}})


# ---- years until a trade has hands --------------------------------------------------------------------------------
check("a trade with hands now waits no time",
      years_until_trade_has_hands(stub_game({"smith": 2.0}, []), "smith") == 0.0)
check("a trade nobody holds and nobody is learning waits for ever",
      years_until_trade_has_hands(stub_game({}, []), "machinist") is None)
check("a trade being learned waits until the soonest trainees join",
      years_until_trade_has_hands(stub_game({}, [("t", YEAR + 3, "machinist", 1), ("t", YEAR + 2, "machinist", 1)]), "machinist") == 2.0)
check("trainees who have already joined count as no wait, and trainees of another trade or none do not count",
      years_until_trade_has_hands(stub_game({}, [("t", YEAR - 1, "machinist", 1)]), "machinist") == 0.0
      and years_until_trade_has_hands(stub_game({}, [("t", YEAR + 1, "smith", 1), ("t", YEAR + 1, "machinist", 0)]), "machinist") is None)

# ---- the trades a project waits for -----------------------------------------------------------------------------------
game = stub_game({"smith": 2.0}, [("t", YEAR + 2, "machinist", 1)])
check("a project names each trade it owes hours to that nobody holds yet, with the wait",
      trades_the_project_waits_for(game, "project") == {"machinist": 2.0}, trades_the_project_waits_for(game, "project"))
check("a trade nobody is learning is named with no end to the wait",
      trades_the_project_waits_for(stub_game({"smith": 2.0}, []), "project") == {"machinist": None})
check("a trade the project owes no hours to is never waited for",
      "idle_trade" not in trades_the_project_waits_for(stub_game({}, []), "project"))
check("a project whose trades all have hands waits for nothing",
      trades_the_project_waits_for(stub_game({"smith": 1.0, "machinist": 1.0}, []), "project") == {})

# ---- the stall gate -------------------------------------------------------------------------------------------------------
check("trainees who arrive before the stall gate would abandon the project are waited for",
      not trade_wait_outlasts_the_project(stub_game({}, [("t", YEAR + STALL_YEARS_BEFORE_ABANDONMENT - 2, "machinist", 1)]), "machinist"))
check("trainees who arrive after it are not",
      trade_wait_outlasts_the_project(stub_game({}, [("t", YEAR + STALL_YEARS_BEFORE_ABANDONMENT, "machinist", 1)]), "machinist"))
check("a trade nobody is learning outlasts the project", trade_wait_outlasts_the_project(stub_game({}, []), "machinist"))
check("a trade with hands never does", not trade_wait_outlasts_the_project(stub_game({"smith": 1.0}, []), "smith"))
