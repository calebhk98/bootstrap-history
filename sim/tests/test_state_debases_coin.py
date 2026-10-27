"""Complaints 272 and 624: the cut a struck-coin state decides on is a recoinage. The coin struck again holds
less metal, the same metal makes more coin, and the new coin goes to the issuer; a state that cuts nothing
leaves the coin alone. Complaint 640: the recoinage is called on a book and a coin built here; the yearly
wiring is below; the price effect has no unit test (Complaint 624)."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from types import SimpleNamespace

from sim.agents.api import COIN_RESTRIKE_SHARE_PER_YEAR
from sim.economy import currency
from sim.economy.accounts import Book
from sim.economy.economy import Economy
from sim.economy.types import EDGE_MINT, Transfer
from sim.markets.port_year import AgentEconomy
from sim.tests.ui_stand_in import Game


spec = currency.currency_from_coin_standard("realm", {"regime": "struck_coin", "material": "silver_kg",
                                                      "kg_per_unit": 0.0027, "source": "test"}, "denarius", issuer="state")
SUPPLY = 1000.0
struck = currency.units_struck_by_cut(spec, SUPPLY, 0.2, 0.1)
check("coin struck again at a cut yields the coin its saved metal makes", abs(struck - SUPPLY * 0.1 * 0.2 / 0.8) < 1e-12, struck)
lighter = currency.debase_by_cut(spec, SUPPLY, 0.2, 0.1)
check("the metal is conserved: more coin, each holding less",
      abs(lighter.backing_per_unit * (SUPPLY + struck) - spec.backing_per_unit * SUPPLY) < 1e-12, lighter)
check("no cut leaves the coin as it was", currency.debase_by_cut(spec, SUPPLY, 0.0, 0.1) == spec)
fiat = currency.currency_from_coin_standard("x", {"regime": "fiat"}, "note", issuer="state")
check("a coin that is not struck is left alone", currency.debase_by_cut(fiat, SUPPLY, 0.2, 0.1) == fiat)
check("a coin that is not struck yields nothing", currency.units_struck_by_cut(fiat, SUPPLY, 0.2, 0.1) == 0.0)


def economy_holding(supply):
    """A stand-in economy with only what `strike_lighter_coin` reads: a book holding `supply` coin and the coin."""
    book = Book()
    book.transfer(Transfer(EDGE_MINT, "holder", spec.currency_id, supply, "opening"))
    return SimpleNamespace(record=SimpleNamespace(book=book, currency=spec))


def strike(economy, cut):
    Economy.strike_lighter_coin(economy, cut, COIN_RESTRIKE_SHARE_PER_YEAR)
    return economy.record


untouched = economy_holding(SUPPLY)
record = strike(untouched, 0.0)
check("a state that cuts nothing leaves the metal in the coin", record.currency == spec, record.currency)
check("a state that cuts nothing mints nothing", record.book.money_supply(spec.currency_id) == SUPPLY)

cutting = economy_holding(SUPPLY)
record = strike(cutting, 0.2)
check("the state's cut lowers the metal in the coin once, the coin it saves struck as more coin",
      abs(record.currency.backing_per_unit / spec.backing_per_unit - 1.0 / (1.0 + 0.2 * COIN_RESTRIKE_SHARE_PER_YEAR / 0.8)) < 1e-9,
      record.currency)
check("the coin saved is new money in circulation",
      abs(record.book.money_supply(spec.currency_id) - (SUPPLY + currency.units_struck_by_cut(spec, SUPPLY, 0.2, COIN_RESTRIKE_SHARE_PER_YEAR))) < 1e-9,
      record.book.money_supply(spec.currency_id))
check("the new coin goes to the issuer", record.book.balance(spec.issuer, spec.currency_id) > 0.0)
check("the metal in all the coin is what it was", abs(record.currency.backing_per_unit * record.book.money_supply(spec.currency_id)
                                                      - spec.backing_per_unit * SUPPLY) < 1e-9)

fiat_economy = SimpleNamespace(record=SimpleNamespace(book=economy_holding(SUPPLY).record.book, currency=fiat))
check("a coin that is not struck is left alone by the yearly recoinage", strike(fiat_economy, 0.2).currency == fiat)


class Recorder:
    def __init__(self):
        self.calls = []

    def strike_lighter_coin(self, cut, restrike_share):
        self.calls.append((cut, restrike_share))


port = SimpleNamespace(_sim=Game(state_treasury=lambda: SimpleNamespace(record=SimpleNamespace(coin_cut_share=0.15))),
                       _floor_costs={"stale": 1.0})
recorder = Recorder()
AgentEconomy._strike_state_coin(port, recorder)
check("the year strikes the cut the home state decided on, at the restrike share",
      recorder.calls == [(0.15, COIN_RESTRIKE_SHARE_PER_YEAR)], recorder.calls)
check("a recoinage clears the cached floor costs", port._floor_costs == {})
