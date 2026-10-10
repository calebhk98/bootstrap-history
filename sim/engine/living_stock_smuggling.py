"""Taking stock from a partner that will not sell it: smuggling, with the risk of being caught.

Any actor that can reach a partner may try it. The partner must hold the stock and refuse to sell it (if
it sells, the actor buys). The taker pays to carry it, the agents at the two ends and the freight over the
route, and what the route loses on the way is lost. The partner's state catches it with the chance its
reach gives (the way a state catches an unlicensed operator of a patented concern), the likelier the
bigger the bite out of its holding. Caught, the haul is seized, the carrying is not refunded, the state
shuts its markets to the taker for some years (its own decision, kept in its record), and the taker's
scandal rises. Not caught, the stock is delivered and the partner has that much less to sell.
"""
import hashlib

from sim.constants import declare
from sim.world import stock_dynamics

from .data import load_civ
from .material_units import tonnes_per_unit
from .theft_exposure import visibility_factor

SMUGGLING_CLOSURE_YEARS = declare(
    "STOCK_SMUGGLING_CLOSURE_YEARS", 10, kind="temporary_heuristic", unit="years", source=None, confidence="D",
    why="Years a partner's state keeps its markets shut to an actor caught smuggling its stock. Stands in for "
        "the diplomatic and customs memory of a state, which the model does not yet have; a round figure, "
        "not measured.")

SMUGGLING_SCANDAL = declare(
    "STOCK_SMUGGLING_SCANDAL", 4, kind="temporary_heuristic", unit="scandal points", source=None, confidence="D",
    why="Scandal at home when a smuggler is caught and named. The size of a patron's death in the same "
        "units, which is a real but minor bump; not measured.")


class LivingStockSmugglingMixin:

    def _partner_taken(self, civilization_id, material):
        """Units of a material already taken from the partner by smugglers."""
        government = self.partner_government(civilization_id)
        return 0.0 if government is None else float(government.record.stock_taken.get(material, 0.0))

    def _smuggling_chance(self, civilization_id, material, units):
        """Chance the partner's state finds the taking out: its reach times how much of what it holds goes."""
        holding = max(1e-12, self._partner_holding(civilization_id, material))
        capacity = float(load_civ(civilization_id).get("state_capacity", self.STATE_CAPACITY_DEFAULT))
        return stock_dynamics.catch_chance(capacity, visibility_factor(units / holding))

    def stock_smuggle_quote(self, material, units, partner=None):
        """What taking `units` of a stock material from a partner that will not sell it costs and risks:
        {"ok": True, partner, units, tonnes, cost, chance_caught, arrives_units}, else {"ok": False, "error"}."""
        units = float(units)
        if units <= 0.0:
            return {"ok": False, "error": "take a positive amount of %s" % material}
        trading = self.foreign_economies()
        if partner and partner not in trading:
            return {"ok": False, "error": "%s is not trading with you this year; those that are: %s"
                    % (partner, ", ".join(trading) or "none")}
        reasons = []
        for candidate in ([partner] if partner else trading):
            reached = self.partner_gate_refusal(candidate)
            refusal = self.partner_refusal(candidate, material)
            holding = self._partner_holding(candidate, material)
            if reached:
                reasons.append(reached)
            elif refusal is None:
                reasons.append("%s sells %s; buy it" % (candidate, material))
            elif holding <= 0.0 or units > holding + 1e-9:
                reasons.append("%s holds only %.6g %s" % (candidate, holding, material))
            else:
                return self._smuggle_terms(material, units, candidate)
        return {"ok": False, "error": (reasons or ["no partner you trade with holds %s" % material])[0]}

    def _smuggle_terms(self, material, units, civilization_id):
        facts = self._foreign_economy_facts(civilization_id)
        tonnes = units * tonnes_per_unit(material)
        carry_per_tonne = self._agent_cost_per_tonne(civilization_id, facts["route"]) + facts["freight_per_tonne"]
        lost = self._cargo_lost_share(facts["route"], material, civilization_id)
        return {"ok": True, "material": material, "units": units, "partner": civilization_id, "tonnes": tonnes,
                "cost": carry_per_tonne * tonnes, "arrives_units": units * (1.0 - lost),
                "chance_caught": self._smuggling_chance(civilization_id, material, units)}

    def _smuggling_draw(self, terms):
        """A draw in 0..1 fixed by the attempt (year, taker, partner, stock, size and the purse the carrying
        has just left), so a save and a load cannot change the outcome and a repeat is a new draw."""
        key = "|".join(str(part) for part in (
            self.state.scenario.year, self.goods_market.acting_party_id, terms["partner"], terms["material"],
            terms["units"], round(self.capital, 6)))
        return int(hashlib.sha256(key.encode()).hexdigest()[:13], 16) / float(16 ** 13)

    def settle_stock_smuggle(self, terms):
        """Carry the stock out: pay the carrying, then draw for the state's catching. Returns the terms with
        `caught`, `delivered_units` and, when caught, `closed_until`; False when the taker cannot pay."""
        buyer = self.goods_market.acting
        if not buyer.can_pay(terms["cost"]):
            return False
        buyer.pay(terms["cost"], "stock smuggled")
        caught = stock_dynamics.is_caught(self._smuggling_draw(terms), terms["chance_caught"])
        government = self.partner_government(terms["partner"])
        outcome = dict(terms, caught=caught, delivered_units=0.0, closed_until=None)
        if caught:
            self._punish_smuggler(government, outcome)
            return outcome
        outcome["delivered_units"] = terms["arrives_units"]
        buyer.take_delivery(self._stock_key(terms["material"]), terms["arrives_units"] * tonnes_per_unit(terms["material"]))
        if government is not None:
            taken = government.record.stock_taken
            taken[terms["material"]] = taken.get(terms["material"], 0.0) + terms["units"]
        return outcome

    def _punish_smuggler(self, government, outcome):
        """The state's answer to a caught smuggler: it shuts its markets to the taker, and the scandal is
        the taker's at home."""
        if government is not None:
            until = self.state.scenario.year + SMUGGLING_CLOSURE_YEARS
            government.close_markets_to(self.goods_market.acting_party_id, until)
            outcome["closed_until"] = until
        self.scandal += SMUGGLING_SCANDAL
        if self.scandal_last_year is not None:
            self.scandal_last_year += SMUGGLING_SCANDAL

    def smuggle_stock_from_partner(self, material, units, civilization_id=None):
        """Try to take units of a stock material from a partner that will not sell it; the units that arrived
        (0 when refused, unaffordable or caught)."""
        terms = self.stock_smuggle_quote(material, units, civilization_id)
        if not terms["ok"]:
            return 0.0
        outcome = self.settle_stock_smuggle(terms)
        return outcome["delivered_units"] if outcome else 0.0
