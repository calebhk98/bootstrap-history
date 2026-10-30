"""Trade that actors (the traders) carry between this society and a partner, as the partner's market sees it.

A cargo sold to a partner is extra supply in that partner's book, and a cargo bought there is extra demand, so the gap the
traders serve narrows over the years. Actors tally the year's cargo here (`NoteActorTrade`); the partner's books close on it at
the year's end (`ClosePartnerBooks`). A good the actors carry in a direction this year is theirs: the engine's aggregate
foreign flow and the agent economy's stand-in external orders leave that direction alone (`actors_carry`).

(needs: partner_price_level, market_rate, material_commodity, commodity_record, market_floor_ratio)"""
from typing import Any, Dict, Optional, Tuple

from sim.world import market
from sim.world.material_units import tonnes_per_unit

from . import rules
from .constants import BOUGHT, SOLD


class ActorTrade:

    def apply_note_actor_trade(self, command: Any) -> None:
        rules.note_actor_trade(self.world.actor_trade, command.partner, command.material, command.tonnes,
                               command.to_partner, command.landed_cost)

    def apply_note_actor_home_trade(self, command: Any) -> None:
        rules.note_home_trade(self.world.home_actor_trade, command.material, command.tonnes, command.landing)

    def actor_home_trade(self, material: str) -> Tuple[float, float]:
        """(tonnes landed in the home market, tonnes taken out of it) by actors so far this year."""
        return rules.home_trade(self.world.home_actor_trade, material)

    def actors_carry(self, material: str, to_partner: bool, partner: Optional[str] = None) -> bool:
        """Whether actors have carried the material this year toward (or from) a partner, any partner by default."""
        return rules.actors_carry(self.world.actor_trade, material, to_partner, partner)

    def landed_cost(self, paid: float, carriage: float) -> float:
        """What a cargo costs its carrier on landing: the purchase, a year's return on it (the carrier's margin) and the
        carriage with its dues."""
        return rules.landed_cost(paid, carriage, self.needs.market_rate())

    def partner_price_per_unit(self, partner: str, material: str) -> Optional[float]:
        """A partner's price of a material in home money: its solved cost, at its coin's price level and the price its own
        market has reached; None when the partner prices nothing of it."""
        price = self.partner_facts(partner)["prices_in_home_money"].get(material)
        if not price:
            return None
        entry = self.world.market_book.get(partner, {}).get(self.needs.material_commodity[material])
        ratio = entry["price_ratio"] if entry else 1.0
        return rules.partner_price(price, self.needs.partner_price_level[partner], ratio)

    def _import_offers(self, partner: str, cargo_by_material: Dict[str, Dict[str, float]]) -> Tuple[Dict[str, list], Dict[str, float]]:
        """The cargo landed at a partner as offers at its landed cost; cargo with no landed cost noted is a price taker."""
        if not cargo_by_material:
            return {}, {}
        facts = self.partner_facts(partner)
        commodity_of = {material: self.needs.material_commodity[material] for material in cargo_by_material}
        tonnes_each = {material: tonnes_per_unit(material) for material in cargo_by_material}
        return rules.import_offers(cargo_by_material, commodity_of, tonnes_each, facts["prices_in_home_money"],
                                   self.needs.partner_price_level[partner])

    def _partner_outcome(self, entry: Dict[str, float], commodity: str, sold: float, bought: float, imports: Any = ()) -> Any:
        """The partner's market for a commodity cleared on `sold` tonnes landed there at no ask, `imports` landed at their
        landed cost, and `bought` taken from it."""
        record = self.needs.commodity_record[commodity]
        return rules.clear_partner(entry, self.needs.market_floor_ratio[commodity],
                                   float(record.get("price_ceiling_factor", market.DEFAULT_CEILING_RATIO)), sold, bought, imports)

    def partner_price_response(self, partner: str, material: str, tonnes: float, landing: bool) -> float:
        """Factor on a partner's price of a material once `tonnes` more are landed there (`landing`) or taken from it, on top
        of the year's cargo so far; one where the partner has no book for it."""
        commodity = self.needs.material_commodity[material]
        entry = self.partner_entry(partner, commodity, self.partner_facts(partner))
        if entry is None or not entry["price_ratio"] > 0.0:
            return 1.0
        flow = self.world.actor_trade.get(partner, {}).get(material, {SOLD: 0.0, BOUGHT: 0.0})
        sold, bought = flow[SOLD] + (tonnes if landing else 0.0), flow[BOUGHT] + (0.0 if landing else tonnes)
        return rules.price_response(entry, self._partner_outcome(entry, commodity, sold, bought).price_ratio)

    def apply_close_partner_books(self, command: Any) -> None:
        """Clear each commodity in each partner's book on the year's actor cargo (none for most), so the partner's capacity
        follows its price and the price follows the cargo; then clear the tally."""
        tally = self.world.actor_trade
        book = self.world.market_book
        self.world.home_actor_trade.clear()
        for partner in sorted(set(tally) | set(book)):
            facts = self.partner_facts(partner)
            cargo: Dict[str, list] = {}
            imports, price_taking = self._import_offers(partner, tally.get(partner, {}))
            for material, flow in tally.get(partner, {}).items():
                sold_bought = cargo.setdefault(self.needs.material_commodity[material], [0.0, 0.0])
                sold_bought[0] += flow[SOLD]
                sold_bought[1] += flow[BOUGHT]
            for commodity in sorted(set(book.get(partner, {})) | set(cargo)):
                entry = self.partner_entry(partner, commodity, facts)
                if entry is None:
                    continue
                sold, bought = cargo.get(commodity, (0.0, 0.0))
                outcome = self._partner_outcome(entry, commodity, price_taking.get(commodity, 0.0), bought,
                                                imports.get(commodity, ()))
                rules.close_entry(entry, outcome, sold, bought)
        tally.clear()
        self.bump("books")
