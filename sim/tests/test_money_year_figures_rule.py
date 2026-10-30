"""Complaint 473: the spin-up trace's money columns are read from the year's money audit (`money_year_figures`: coin worn,
coin struck net of melting, the stock's change, the metal the mint holds), and a game reads how its opening's spin-up ended
from the saved record. Both are called on stand-ins carrying only what they read. Whether a long spin-up's mint keeps up with
wear is measured by `python3 sim/simulator.py spin-up-trace` and `opening-checks` (Complaint 473)."""

QUICK_TOPIC = True

from types import SimpleNamespace
from unittest import mock

from .harness import check

from sim.economy import api as economy_api
from sim.economy.types import EDGE_MINT, EDGE_WEAR
from sim.markets.port import EconomyPort
from sim.markets.port_year import AgentEconomy

read_saved_result = AgentEconomy.spin_up_result
read_game_result = EconomyPort.spin_up_result


def stand_in(edge_net, supply_change, backing_good=""):
    spec = SimpleNamespace(currency_id="denarius", backing_good=backing_good)
    return (SimpleNamespace(record=SimpleNamespace(currency=spec)),
            SimpleNamespace(money_audit=SimpleNamespace(edge_net=edge_net, supply_change=supply_change)))


economy, outcome = stand_in({EDGE_WEAR: {"denarius": -30.0}, EDGE_MINT: {"denarius": 12.0}}, {"denarius": -18.0})
figures = economy_api.money_year_figures(economy, outcome)
check("wear is the coin worn away, as a positive amount", figures["wear"] == 30.0, figures)
check("struck is the mint's net payout and change is the audit's supply change",
      figures["struck"] == 12.0 and figures["change"] == -18.0, figures)
check("a coin with no backing metal holds none", figures["metal_held"] == 0.0, figures)

economy, outcome = stand_in({}, {})
figures = economy_api.money_year_figures(economy, outcome)
check("a year with no edge flows reads zero wear, strikes and change",
      (figures["wear"], figures["struck"], figures["change"]) == (0.0, 0.0, 0.0), figures)

economy, outcome = stand_in({}, {}, backing_good="silver")
with mock.patch.object(economy_api, "account_holdings",
                       return_value={"goods": {"silver": {"tile_a": 5.0, "tile_b": -2.0, "tile_c": 1.5}}}) as holdings:
    figures = economy_api.money_year_figures(economy, outcome)
check("the metal the mint holds sums the positive holdings of the backing good", figures["metal_held"] == 6.5, figures)
check("the holdings are those of the mint", holdings.call_args.args[1] == EDGE_MINT, holdings.call_args)

saved = {"settled": True, "years": 12, "gap": 0.01}
read = read_saved_result(SimpleNamespace(stored={"record": {"spin_up_result": saved}}))
check("the agent economy reads the saved first-stage result as a copy", read == saved and read is not saved, read)
check("before the opening is saved the result is empty", read_saved_result(SimpleNamespace(stored={})) == {})
check("a game with no agent economy has no spin-up result", read_game_result(SimpleNamespace(agent=None)) == {})
check("a game reports what its agent economy saved",
      read_game_result(SimpleNamespace(agent=SimpleNamespace(spin_up_result=lambda: saved))) == saved)
