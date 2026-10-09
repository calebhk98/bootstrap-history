"""The year's cargo of the trader actors, kept as legs until the home market has cleared, then settled once.

A trader decides a cargo at the year's start against quotes and is booked at them. The partner's side is real money
at once (the foreign coin ledger and the route's carriers); the home side is whatever the agent economy's book gave
the cargo (`economy_port_cargo.py`), or the quote while the agent economy is off. Settling trues the trader's purse
up from the booking to the result and closes the partner's tally on what really crossed.
A leg is a plain dict kept in `state.economy.agent_economy["cargo"]`, so a save carries it.
"""
from sim.agents.api import edges, ledger

from .data import load_civ

LANDING, TAKING, THROUGH = "in", "out", "through"
SETTLEMENT = "edge:market settlement"


class TraderCargoMixin:

    def cargo_legs(self):
        """The legs noted since the last settlement, in a stable order."""
        return [leg for _id, leg in sorted(self.state.economy.agent_economy.get("cargo", {}).items())]

    def note_cargo_leg(self, trader_id, material, tonnes, source, destination, paid, received, carriage, home):
        """Note a cargo a trader shipped; the same trader, route and good in one year is one leg."""
        kind = LANDING if destination == home else TAKING if source == home else THROUGH
        partner = source if kind == LANDING else destination
        leg_id = "cargo:%s:%s:%s:%s" % (trader_id, partner if kind != THROUGH else source + ">" + destination,
                                        material, kind)
        leg = self.state.economy.agent_economy.setdefault("cargo", {}).setdefault(leg_id, {
            "id": leg_id, "trader": trader_id, "kind": kind, "source": source, "destination": destination,
            "partner": partner, "material": material, "tonnes": 0.0, "paid": 0.0, "received": 0.0, "carriage": 0.0})
        leg["tonnes"] += tonnes
        leg["paid"] += paid
        leg["received"] += received
        leg["carriage"] += carriage

    def _money_per_partner_coin(self, partner):
        standard = load_civ(partner)["coin_standard"]
        metal_price = self._coin_metal_price(standard["material"])
        return standard["kg_per_unit"] * metal_price if metal_price else None

    def _pay_partner(self, partner, tonnes_signed, value):
        """Settle one side of a cargo with a partner in coin, and count it against the route's carriers."""
        per_coin = self._money_per_partner_coin(partner)
        if per_coin and value > 0.0:
            self._settle_flow(partner, tonnes_signed, value, per_coin)
        self._record_lift(partner, self._foreign_economy_facts(partner)["route"], tonnes_signed, 0.0)

    def settle_trader_cargo(self, results):
        """Settle every noted leg. `results` is what the book gave each leg that entered it
        ({leg id: {"tonnes", "money"}}, see economy_port_cargo.close_cargo_accounts); a leg it did not take is
        settled at its quote, as is every leg when `results` is None (no book)."""
        results = results or {}
        for leg in self.cargo_legs():
            kind, tonnes, partner = leg["kind"], leg["tonnes"], leg["partner"]
            result = results.get(leg["id"])
            delta = 0.0
            if kind == LANDING:
                self._pay_partner(partner, tonnes, leg["paid"])
                if result is not None:
                    delta = result["money"] - leg["received"]
            elif kind == TAKING:
                share = 1.0
                if result is not None:
                    share = min(1.0, result["tonnes"] / tonnes) if tonnes > 0.0 else 0.0
                    delta = leg["received"] * (share - 1.0) + result["money"]
                    if share < 1.0:
                        self.note_actor_trade(partner, leg["material"], -tonnes * (1.0 - share), True)
                self._pay_partner(partner, -tonnes * share, leg["received"] * share)
            else:
                self._pay_partner(leg["source"], tonnes, leg["paid"])
                self._pay_partner(leg["destination"], -tonnes, leg["received"])
            self._true_up_trader(leg["trader"], delta)
        self.state.economy.agent_economy.pop("cargo", None)

    def _true_up_trader(self, trader_id, delta):
        """The trader's purse and margin follow what a cargo really made against what it was booked at."""
        trader = self.actors.actors.get(trader_id)
        if trader is None or delta == 0.0:
            return
        market = self.edge(edges.EDGE_MARKET)
        if delta > 0.0:
            ledger.transfer(market, trader, delta, SETTLEMENT)
        else:
            ledger.transfer(trader, market, -delta, SETTLEMENT)
        trader.record.last_margin += delta
