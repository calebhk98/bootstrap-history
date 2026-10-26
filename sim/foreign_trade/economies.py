"""Other economies as participants in the home society's markets: who they are, what they sell and why they refuse.

An economy named in the foreign-economies data has its own solved long-run costs (its civilisation file's technologies, wage
and coin), a population that sizes its market, and a place on the map. For each commodity it keeps a book like the society's
(capacity, stock, price ratio) and clears it every year together with the home market, so imports cap a home shortage and
exports lift the price abroad. Prices of both sides are compared in home money: a foreign price in its own coin is worth the
coin's metal at the home price of that metal.

(needs: foreign_economy_records, civilisation, civilisation_record, partner_own_economy, year, acting_seat, techniques_held,
material_prices, home_unit_price, household_prices, material_commodity, commodity_record, partner_reached,
legacy_actor_registry, foreign_route, route_freight_per_tonne)"""
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from sim.agents.api import GOVERNMENT_PREFIX, exports_allowed
from sim.refusal import Refusal

from . import rules


class Economies:

    def partners(self) -> List[str]:
        """Every economy enabled for this year, sorted by id: those trading by the partner books and those that are part of
        the agent economy."""
        civilisation = self.needs.civilisation()
        return rules.partner_countries(self.needs.foreign_economy_records(), self.needs.year(), civilisation.get("id"),
                                       civilisation.get("variant_of"))

    def partners_in_agent_economy(self) -> List[str]:
        """The enabled economies whose tiles, people and producers are in the agent economy itself."""
        inside = rules.agent_economy_ids(self.needs.foreign_economy_records())
        return [partner for partner in self.partners() if partner in inside]

    def foreign_economies(self) -> List[str]:
        """Economies trading with this society this year by the partner books, sorted by id: the enabled ones that are not
        themselves in the agent economy."""
        inside = set(self.partners_in_agent_economy())
        return [partner for partner in self.partners() if partner not in inside]

    def partner_civ(self, civilization_id: str) -> Dict[str, Any]:
        """The civilisation `civilization_id` as its file gives it (mods applied, checked), loaded once and kept for the
        game. Read-only: a caller that changes a record takes its own copy."""
        record = self._partner_civs.get(civilization_id)
        if record is None:
            record = self._partner_civs[civilization_id] = self.needs.civilisation_record[civilization_id]
        return record

    def partner_government(self, civilization_id: str) -> Any:
        """The actor that is the partner country's state, or None before the roster is seeded."""
        return self.needs.legacy_actor_registry().get(GOVERNMENT_PREFIX + civilization_id)

    def partner(self, civilization_id: str) -> Dict[str, Any]:
        """{civ: the partner's civilisation record, has_government, stock_taken: {material: units smugglers took}}."""
        government = self.partner_government(civilization_id)
        return {"civ": self.partner_civ(civilization_id), "has_government": government is not None,
                "stock_taken": {} if government is None else dict(government.record.stock_taken)}

    def partner_coin_standard(self, civilization_id: str) -> Dict[str, Any]:
        return self.partner_civ(civilization_id)["coin_standard"]

    def partner_opening_facts(self, civilization_id: str) -> Dict[str, Any]:
        """{population, money_per_labour_hour}: what a partner's opening coin stock is sized from."""
        return {"population": self.partner_civ(civilization_id).get("population"),
                "money_per_labour_hour": self.needs.partner_own_economy[civilization_id]["money_per_labour_hour"]}

    def partner_gate(self, civilization_id: str) -> Optional[Refusal]:
        """Why trade with a partner some action returns cannot begin yet, else None. A partner no action returns is open from
        the start."""
        if self.needs.partner_reached(civilization_id):
            return None
        return Refusal("partner_not_reached", "you have not yet reached %s" % civilization_id)

    def partner_refusal(self, civilization_id: str, material: str) -> Optional[Refusal]:
        """Why the partner will not sell the material, else None. The partner's state decides: it has shut its markets to the
        buyer, or its export policy holds the good back. Before the roster is seeded the same policy answers from the
        country's data, which is the state's starting condition."""
        gate = self.partner_gate(civilization_id)
        if gate:
            return gate
        civilization = self.partner_civ(civilization_id)
        name = civilization.get("name", civilization_id)
        government = self.partner_government(civilization_id)
        if government is None:
            government = SimpleNamespace(record=SimpleNamespace(
                state_monopolies=set(civilization.get("state_monopolies") or ())), decision_policy=None)
        else:
            reopens = government.markets_closed_until(self.needs.acting_seat(), self.needs.year())
            if reopens:
                return Refusal("partner_market_shut", "%s has shut its markets to you until %d" % (name, reopens))
        if material not in exports_allowed(government, [material]):
            return Refusal("partner_export_held_back", "%s will not sell %s" % (name, material))
        return None

    def partner_facts(self, civilization_id: str) -> Dict[str, Any]:
        """Population, route and prices of one foreign economy in home money, remembered until the home price table changes
        or the year turns (freight follows last year's flows, the market rate and wages). A partner is named by id in the
        foreign-economies data; the home society is always the civilisation."""
        prices = self.needs.material_prices()
        cache = self._facts_cache.setdefault(self.clock.acting_seat, {})
        cached = cache.get(civilization_id)
        known_techs = (len(self.needs.techniques_held()), self.needs.year())
        civilization = self.partner_civ(civilization_id)
        coin = civilization["coin_standard"]
        coin_price = self.needs.home_unit_price[coin["material"]]
        if cached is not None and cached[0] is prices and cached[2] == known_techs and cached[3] == coin_price:
            return cached[1]
        own_economy = self.needs.partner_own_economy[civilization_id]
        foreign_prices = {}
        if coin_price:
            home_money_per_coin = coin["kg_per_unit"] * coin_price
            foreign_prices = {material: price * home_money_per_coin for material, price
                              in own_economy["prices_in_own_coin"].items()}
        route = self.needs.foreign_route(civilization, None, "goods")
        facts = {"solved_materials": own_economy["solved_materials"],
                 "population": float(civilization.get("population") or 0.0),
                 "prices_in_home_money": foreign_prices,
                 "route": route,
                 "freight_per_tonne": self.needs.route_freight_per_tonne(civilization, None)}
        cache[civilization_id] = (prices, facts, known_techs, coin_price)
        return facts

    def partner_route(self, civilization_id: str) -> Any:
        """The route the partner's economy facts hold for the year, or None."""
        return self.partner_facts(civilization_id)["route"]

    def commodity_materials(self, commodity: str) -> List[str]:
        """Material keys that count as the commodity: the commodity's own name, the ledger's grouping and every material the
        engine files under it that has a seller in reach. Remembered until the offers change."""
        prices = self.needs.household_prices()
        seat = self.clock.acting_seat
        cache = self._materials_cache.get(seat)
        if cache is None or cache[0] is not prices:
            cache = self._materials_cache[seat] = (prices, {})
        keys = cache[1].get(commodity)
        if keys is None:
            if "members" not in cache[1]:
                grouped: Dict[str, set] = {}
                for material in prices:
                    grouped.setdefault(self.needs.material_commodity[material], set()).add(material)
                cache[1]["members"] = grouped
            members = set(cache[1]["members"].get(commodity, ()))
            members.update(self.needs.commodity_record[commodity].get("material_keys", []))
            keys = cache[1][commodity] = [commodity] + sorted(members - {commodity})
        return keys
