"""Scenario: Complaint 382 in a game. Over two years of a rich household's game (so that wages and the state's pay reach the
people's purses), all purses together plus all named edges together stay what they were, money moved
through named edges, and the founder's payroll and the state's pay reach the people's purses. The scan of the source for
one-sided postings and the edge's arithmetic are in test_every_posting_names_a_counterparty."""
from .harness import *  # noqa: F401,F403

from sim.agents.purses import COIN, EDGE_OUTSIDE

def purses(game):
    book = game.state.actors.purses.book
    return sum(book.balance(account, COIN) for account in book.agents() if not account.startswith("edge:"))


def edges(game):
    book = game.state.actors.purses.book
    return sum(book.balance(account, COIN) for account in book.agents()
               if account.startswith("edge:") and account != EDGE_OUTSIDE)


def ask(game, **command):
    return S._agent_dispatch(game, NODES, command)


# the people's purses receive wages and the state's pay only from the second year, so the rich game plays two
for label, capital, years in (("a rich household", 300_000.0, 2),):
    game = sim(capital=capital, manual=False, events=True)
    game.end_year = game.cfg["start_year"] + game.cfg["horizon_years"]
    if capital > 100_000.0:
        rich_game = game
    opening = purses(game) + edges(game)
    for _year in range(years):
        ask(game, cmd="step", years=1)
    total = purses(game) + edges(game)
    check("%s: all purses and all named edges together stay what they were over %d year(s)" % (label, years),
          abs(total - opening) <= 1e-6 * max(1.0, abs(opening)), (opening, total))
    crossed = game.state.actors.purses.book.edge_agents()
    check("%s: money moved through named edges" % label, bool(crossed), crossed)
    check("%s: every edge is named" % label, all(name.startswith("edge:") for name in crossed), crossed)

# step 2: wages and the state's pay land in the people's purses
# the rich household's game, already stepped, is the one read
strata = [record for record in rich_game.state.actors.records.values() if record.stratum and record.country is None]
received = {label for record in strata for label in record.income if label != "edge:economy"}
check("the home country has strata", bool(strata), len(strata))
# not text: ledger posting reasons are recorded labels
check("the founder's payroll and the state's pay reach the people's purses",
      "living costs" in received and ("army" in received or "administration" in received), sorted(received))
