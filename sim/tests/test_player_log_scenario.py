"""SCENARIO: the policy screen and the concern ledger on a real game. The log's own rules are in test_player_log."""
from .harness import *  # noqa: F401,F403


def ask(game, **command):
    return S._agent_dispatch(game, NODES, command)


# --- The automatic behaviours are approximations, and every switch says what it does.
game = sim()
_policy = ask(game, cmd="policy")
check("the policy screen says these are approximations, not optimal play",
      bool(_policy.get("these_are_approximations_not_optimal_play")), _policy.keys())
check("...and every switch the game offers says what it does",
      not [name for name in _policy["policy"] if not (_policy.get("what_each_does") or {}).get(name)],
      [name for name in _policy["policy"] if not (_policy.get("what_each_does") or {}).get(name)])

# --- The ledger's parts add up to the total, with an aged loom among the concerns.
ledger = sim(civ="rome_100ad", capital=500000.0)
ledger.done.add("tex_power_loom")
ledger.done_year["tex_power_loom"] = 100
ledger._done_changed()
ledger.artisans = ledger.scholars = 80.0
ledger.employees["carpenter"] = 1.0
ledger.year = 100
ledger.open_venture("tex_power_loom")
ledger.year = 300
_sources = ledger.revenue_sources()
check("the ledger's parts still add up to the revenue it states, with an aged goods concern running",
      abs(sum(_sources.values()) - ledger.revenue()) < 1.0, (sum(_sources.values()), ledger.revenue()))
