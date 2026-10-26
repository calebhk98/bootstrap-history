"""Getting living stock from a partner economy: buying what it sells (one quote, the same figure charged) and
smuggling what it will not sell, with the risk of being caught.

A partner sells a stock material it holds and makes, at its price in home money plus the merchants' terms and the
route's freight, unless its own policy refuses. Any actor that can reach a partner may smuggle: the partner must hold
the stock and refuse to sell it (if it sells, the actor buys). The taker pays to carry it, and what the route loses on
the way is lost. The partner's state catches it with the chance its reach gives, the likelier the bigger the bite out
of its holding. Caught, the haul is seized, the carrying is not refunded, the state shuts its markets to the taker for
some years, and the taker's scandal rises. Not caught, the stock is delivered and the partner has that much less to sell."""
from sim.agents.api import edges
from sim.constants import declare
from sim.foreign_trade.api import CloseMarketsTo, RecordStockTaken, SettleFlow
from sim.ledger.api import ChangeStock, PayEdge
from sim.polity.api import ChangeStanding
from sim.refusal import Refusal, cause_of
from sim.world import stock_dynamics
from sim.world.material_units import tonnes_per_unit

from . import rules

SMUGGLING_CLOSURE_YEARS = declare(
    "STOCK_SMUGGLING_CLOSURE_YEARS", 10, kind="temporary_heuristic", unit="years", source=None, confidence="D",
    why="Years a partner's state keeps its markets shut to an actor caught smuggling its stock. Stands in for "
        "the diplomatic and customs memory of a state, which the model does not yet have; a round figure, "
        "not measured.")

SMUGGLING_SCANDAL = declare(
    "STOCK_SMUGGLING_SCANDAL", 4, kind="temporary_heuristic", unit="scandal points", source=None, confidence="D",
    why="Scandal at home when a smuggler is caught and named. The size of a patron's death in the same "
        "units, which is a real but minor bump; not measured.")


class Trading:
    """The quotes and the two settlements (needs: partners, partner, partner_refusal, partner_gate,
    partner_landed_price, partner_carry, partner_catch_chance, can_pay, acting_balance, year; sends PayEdge,
    ChangeStock, SettleFlow, RecordStockTaken, CloseMarketsTo, ChangeStanding)."""

    def partner_holding(self, civilization_id, material):
        partner = self.needs.partner[civilization_id]
        started = (partner["civ"].get("opening_stock") or {}).get(material, 0.0)
        return rules.partner_holding(started, float(partner["stock_taken"].get(material, 0.0)))

    def stock_purchase_quote(self, material, units, partner=None):
        """What buying `units` of a stock material costs, from the named partner or the cheapest that sells it:
        {"ok": True, partner, units, tonnes, per_tonne, cost}, else {"ok": False, "error"}."""
        units = float(units)
        if units <= 0.0:
            return {"ok": False, "cause": "amount_not_positive", "error": "buy a positive amount of %s" % material}
        trading = self.needs.partners()
        if partner and partner not in trading:
            return rules.not_trading_reply(partner, trading)
        refusals, offers, holdings = [], [], []
        for candidate in ([partner] if partner else trading):
            refusal = self.needs.partner_refusal(candidate, material)
            per_tonne = None if refusal else self.needs.partner_landed_price(candidate, material)
            if refusal:
                refusals.append(refusal)
            elif per_tonne is not None and self.partner_holding(candidate, material) > 0.0:
                held_by_partner = self.partner_holding(candidate, material)
                if units > held_by_partner + 1e-9:
                    holdings.append(Refusal("partner_holds_less", "%s holds only %.6g %s" % (
                        candidate, held_by_partner, material)))
                else:
                    offers.append((per_tonne, candidate))
        if not offers:
            reason = (refusals or holdings
                      or [Refusal("no_partner_sells", "no partner you trade with sells %s" % material)])[0]
            return {"ok": False, "cause": cause_of(reason), "error": reason}
        per_tonne, seller = min(offers)
        tonnes = units * tonnes_per_unit(material)
        return {"ok": True, "material": material, "units": units, "partner": seller,
                "tonnes": tonnes, "per_tonne": per_tonne, "cost": per_tonne * tonnes}

    def buy_stock(self, command):
        """Pay a quote and receive the stock: True, or a refusal when the buyer cannot pay. The partner is paid in
        its own coin's metal, as every foreign payment is."""
        if not self.needs.can_pay(command.cost):
            return Refusal("cannot_afford", "cannot pay %.6g for %s" % (command.cost, command.material))
        self.needs.send(PayEdge(edges.EDGE_MARKET, command.cost, "stock bought abroad"))
        self.needs.send(ChangeStock(self.commodity_of(command.material), command.tonnes))
        self.needs.send(SettleFlow(command.partner, command.tonnes, command.cost))
        return True

    def stock_smuggle_quote(self, material, units, partner=None):
        """What taking `units` of a stock material from a partner that will not sell it costs and risks:
        {"ok": True, partner, units, tonnes, cost, chance_caught, arrives_units}, else {"ok": False, "error"}."""
        units = float(units)
        if units <= 0.0:
            return {"ok": False, "cause": "amount_not_positive", "error": "take a positive amount of %s" % material}
        trading = self.needs.partners()
        if partner and partner not in trading:
            return rules.not_trading_reply(partner, trading)
        reasons = []
        for candidate in ([partner] if partner else trading):
            reached = self.needs.partner_gate(candidate)
            refusal = self.needs.partner_refusal(candidate, material)
            holding = self.partner_holding(candidate, material)
            if reached:
                reasons.append(reached)
            elif refusal is None:
                reasons.append(Refusal("partner_sells", "%s sells %s; buy it" % (candidate, material)))
            elif holding <= 0.0 or units > holding + 1e-9:
                reasons.append(Refusal("partner_holds_less", "%s holds only %.6g %s" % (candidate, holding, material)))
            else:
                return self.smuggle_terms(material, units, candidate)
        reason = (reasons or [Refusal("no_partner_holds", "no partner you trade with holds %s" % material)])[0]
        return {"ok": False, "cause": cause_of(reason), "error": reason}

    def smuggle_terms(self, material, units, civilization_id):
        tonnes = units * tonnes_per_unit(material)
        carry_per_tonne, lost = self.needs.partner_carry(civilization_id, material)
        holding = max(1e-12, self.partner_holding(civilization_id, material))
        return {"ok": True, "material": material, "units": units, "partner": civilization_id, "tonnes": tonnes,
                "cost": carry_per_tonne * tonnes, "arrives_units": units * (1.0 - lost),
                "chance_caught": self.needs.partner_catch_chance(civilization_id, units / holding)}

    def smuggling_draw(self, terms):
        return rules.smuggling_draw((
            self.needs.year(), self.clock.acting_seat, terms["partner"], terms["material"], terms["units"],
            round(self.needs.acting_balance(), 6)))

    def smuggle_stock(self, command):
        """Carry the stock out: pay the carrying, then draw for the state's catching. Answers the terms with
        `caught`, `delivered_units` and, when caught, `closed_until`; a refusal when the taker cannot pay."""
        terms = {"material": command.material, "partner": command.partner, "units": command.units,
                 "tonnes": command.tonnes, "cost": command.cost, "arrives_units": command.arrives_units,
                 "chance_caught": command.chance_caught}
        if not self.needs.can_pay(command.cost):
            return Refusal("cannot_afford", "cannot pay %.6g to carry %s" % (command.cost, command.material))
        self.needs.send(PayEdge(edges.EDGE_MARKET, command.cost, "stock smuggled"))
        caught = stock_dynamics.is_caught(self.smuggling_draw(terms), command.chance_caught)
        has_government = self.needs.partner[command.partner]["has_government"]
        outcome = dict(terms, ok=True, caught=caught, delivered_units=0.0, closed_until=None)
        if caught:
            self.punish_smuggler(has_government, outcome)
            return outcome
        outcome["delivered_units"] = command.arrives_units
        self.needs.send(ChangeStock(self.commodity_of(command.material),
                                    command.arrives_units * tonnes_per_unit(command.material)))
        if has_government:
            self.needs.send(RecordStockTaken(command.partner, command.material, command.units))
        return outcome

    def punish_smuggler(self, has_government, outcome):
        """The state's answer to a caught smuggler: it shuts its markets to the taker, and the scandal is the
        taker's at home."""
        if has_government:
            until = self.needs.year() + SMUGGLING_CLOSURE_YEARS
            self.needs.send(CloseMarketsTo(outcome["partner"], self.clock.acting_seat, until))
            outcome["closed_until"] = until
        self.needs.send(ChangeStanding(scandal=SMUGGLING_SCANDAL))
