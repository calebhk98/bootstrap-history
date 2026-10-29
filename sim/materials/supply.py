"""What the seat can get of a material: its own workings and woodland, the market's standing offer, what a trading partner
brings, and what that does to the price. All of it in tonnes a year."""
import collections
import math
from typing import Any, Dict, List, Optional, Set, Tuple

from . import capacity, rules
from .constants import (FIREWOOD_PER_CHARCOAL_MASS_RATIO, GENERIC_MARKET_SHARE_LEDGER_FALLBACK, MARKET_SHARE,
                        MATERIAL_CHECKS, MATERIAL_PRICE_DEMAND_SHARE_CAP, MATERIAL_PRICE_PRESSURE_SCALE)


class Supply:
    """Needs: civilisation, tiles_listed_by, forest_increment, commodity_record, commodity_country_output, material_commodity_map,
    material_prices, mine_works_materials, empire_output, pop_scale, mineral_scale, found_deposits, agent_producer_capacity,
    price_epoch, producers_stamp, running_stamp, effect_best, mechanic, running, forest_hectares,
    nitre_beds, mine_capacity, mine_depletion, partner_import, foreign_supply_tonnes, can_be_bought, goods_stock,
    held_goods, goods_quote, tree_nodes, visibility, material_freight_factor."""

    # ---- the catalogue of what a material is ----

    def material_pool(self, material: str) -> Tuple[str, str]:
        """(commodity, supply-pool tag) a raw material key draws on: the tracked pair, else its curated commodity, else
        itself as a one-member commodity."""
        return rules.tag_of(material, MATERIAL_CHECKS, self.needs.material_commodity_map())

    def material_checks(self) -> Dict[str, Tuple[str, str]]:
        return MATERIAL_CHECKS

    def commodity_known(self, commodity: str) -> bool:
        return bool(self.needs.commodity_record[commodity])

    def normalized_material(self, material: Any) -> str:
        """The key a name means: the short curated name a mine has always used, or the exact key the tree uses."""
        return rules.normalized(material, self.needs.mine_works_materials(), self.needs.material_prices(),
                                self.commodity_known)

    def charcoal_per_hectare(self) -> float:
        """Tonnes of charcoal a year a hectare of coppice yields: the stem wood the home forest grows a hectare a year, all
        cut and burned at the wood-to-charcoal ratio."""
        tiles = tuple(self.needs.tiles_listed_by(self.needs.civilisation()))
        cached = self._coppice
        if cached is None or cached[0] != tiles:
            cached = self._coppice = (tiles, self.needs.forest_increment(tiles))
        return cached[1] / FIREWOOD_PER_CHARCOAL_MASS_RATIO

    # ---- memos that hold while what is built and run is unchanged ----

    def done_memo(self, name: str, key: Any, compute: Any) -> Any:
        """`compute()` remembered per (name, key) while the techniques held, the techniques in use, the price level and the
        economy's producers are unchanged."""
        done = self.needs.techniques_held()
        stamp = (self.needs.price_epoch(), len(done), self.needs.producers_stamp())
        memo = self._done_memo
        if memo is None or memo[0] != stamp or memo[1] is not done:
            memo = self._done_memo = (stamp, done, {})
        table = memo[2]
        entry = (name, key)
        if entry not in table:
            table[entry] = compute()
        return table[entry]

    def running_kept(self, name: str) -> Dict[Any, Any]:
        """A dict for derived values that depend only on which nodes are built, granted and operating; it starts empty
        whenever that changes."""
        projects, stamp, nodes = self.needs.running_stamp()
        kept = self._running_tables
        if kept is None or kept[0] is not projects or kept[1] != stamp or kept[2] is not nodes:
            kept = self._running_tables = (projects, stamp, nodes, {})
        return kept[3].setdefault(name, {})

    # ---- what a society brings to market ----

    def producer_capacity_tonnes(self, material: str) -> float:
        """Tonnes a year the agent economy's producers can make of `material`; zero while it opens."""
        tonnes = self.needs.agent_producer_capacity[material]
        return 0.0 if tonnes is None else tonnes

    def generic_national_output(self, commodity: str) -> float:
        return self.done_memo("national_output", commodity, lambda: self.generic_national_output_uncached(commodity))

    def generic_national_output_uncached(self, commodity: str) -> float:
        """Tonnes a year the society can bring to market of a material with no curated figure: a commodity the catalogue
        defines reads its own output, any other is what the deposits on the tiles held can yield plus what the producers'
        plants make."""
        if self.commodity_known(commodity):
            return self.needs.commodity_country_output(commodity)
        return (capacity.mined_capacity_tonnes(self.needs.found_deposits[commodity])
                + self.producer_capacity_tonnes(commodity))

    def national_output_tonnes(self, commodity: str) -> float:
        """Tonnes a year the whole society produces of `commodity`: the resource table where it names one, else the
        generic estimate."""
        entry = self.needs.empire_output().get(commodity)
        return entry.get("t_per_yr", 0) if entry is not None else self.generic_national_output(commodity)

    def output_scale(self, commodity: str) -> float:
        """What the national output of `commodity` is scaled by to reach this society: a curated figure is the reference
        empire's, so it scales with population (charcoal) or with the mineral tiles held; a capacity read from the
        society's own deposits and producers is already its own."""
        if (commodity not in self.needs.empire_output() and commodity != "charcoal"
                and not self.commodity_known(commodity)):
            return 1.0
        return self.needs.pop_scale() if commodity == "charcoal" else self.needs.mineral_scale[commodity]

    def society_output_tonnes(self, commodity: str) -> float:
        """What the society's own producers can bring to market a year: the national output scaled to the territory held."""
        return self.national_output_tonnes(commodity) * self.output_scale(commodity)

    def generic_market_share(self, commodity: str) -> float:
        return self.done_memo("market_share", commodity, lambda: self.generic_market_share_uncached(commodity))

    def generic_market_share_uncached(self, commodity: str) -> float:
        """The fraction of the society's output an ordinary buyer can reach for a material the tracked table has no
        figure for: a catalogued commodity's own market share, else the declared open share."""
        if self.commodity_known(commodity):
            return float(self.needs.commodity_record[commodity].get("market_share", GENERIC_MARKET_SHARE_LEDGER_FALLBACK))
        return capacity.DEFAULT_MARKET_SHARE_OF_CAPACITY

    def import_tonnes(self, commodity: str) -> float:
        """Tonnes a year a trading partner can still bring of `commodity`; zero when the home society is its seller or no
        one is. A route with no lift limit brings what the partner makes."""
        seller, left = self.needs.partner_import[commodity]
        if seller is None or left is None:
            return 0.0
        if not math.isfinite(left):
            left = self.needs.foreign_supply_tonnes(seller, commodity)
        return left if math.isfinite(left) else 0.0

    def own_material_supply(self, tag: str) -> float:
        """Tonnes a year of a tracked pool the seat supplies itself, not bought from anyone: mines it sank, woodland it
        bought, nitre beds it built. Workings yield after depletion, not the tonnage sunk."""
        if tag == "forest1":
            return self.needs.forest_hectares() * self.charcoal_per_hectare()
        if tag == "forest4":
            return self.needs.forest_hectares() * self.charcoal_per_hectare() * FIREWOOD_PER_CHARCOAL_MASS_RATIO
        if tag == "nitre":
            nitre = self.needs.nitre_beds()
            return nitre["square_metres"] * nitre["tonnes_per_square_metre"]
        if tag.startswith("mine:"):
            material = tag[5:]
            return self.needs.mine_capacity().get(material, 0.0) * self.needs.mine_depletion[material]
        return 0.0

    def market_tonnes(self, commodity: str) -> float:
        """Tonnes a year of `commodity` the market will sell the seat at its standing: the tracked share (else the generic
        one) of the national output scaled to the territory held, widened by what its standing commands, plus a sea route's
        tonnage and what a trading partner brings."""
        national = self.national_output_tonnes(commodity)
        share = MARKET_SHARE.get(commodity)
        if share is None:
            share = self.generic_market_share(commodity)
        kept = self.running_kept("market_tonnes")
        standing_factor = None
        if commodity != "charcoal":
            if "favour" not in kept:
                kept["favour"] = self.needs.effect_best("market_standing")
            favour = kept["favour"]
            if favour is not None:
                standing_factor = favour[1]["factor"]
        scale = self.output_scale(commodity)
        routes = kept.get(commodity)
        if routes is None:
            sea_routes = self.needs.mechanic["supplies_material_by_sea_route"]
            routes = kept[commodity] = sum(
                1 for node_id in sea_routes if commodity in sea_routes[node_id]["materials"] and self.needs.running[node_id])
        return rules.market_tonnes(national, share, commodity == "charcoal", standing_factor, scale, routes,
                                   self.import_tonnes(commodity))

    def own_production_tags(self) -> Set[Tuple[str, str]]:
        """(commodity, tag) for every material the seat produces itself, whether or not anything demands it this year."""
        out = {(material, "mine:" + material) for material, capacity_ in self.needs.mine_capacity().items() if capacity_ > 0}
        if self.needs.forest_hectares() > 0:
            out.add(("charcoal", "forest1"))
            out.add(("charcoal", "forest4"))
        if self.needs.nitre_beds()["square_metres"] > 0:
            out.add(("saltpetre", "nitre"))
        return out

    # ---- the price demand leans on ----

    def material_price_factor(self, commodity: str) -> float:
        """What buying more of this commodity costs beyond the flat catalogue price: how hard the seat's demand leans on the
        market's standing offer, less what its own supply covers, times what the freight from the nearest source adds."""
        market = self.market_tonnes(commodity)
        demands = [(need, self.own_material_supply(tag)) for tag, need in self.demand_by_commodity().get(commodity, ())]
        worst = rules.scarcity_factor(demands, market, MATERIAL_PRICE_DEMAND_SHARE_CAP, MATERIAL_PRICE_PRESSURE_SCALE)
        return worst * self.needs.material_freight_factor[commodity]

    def material_market_summary(self) -> Optional[str]:
        """The line on every raw material carrying a price premium because the seat's own demand leans on the market, or None."""
        demand = self.cached_demand()
        if not demand:
            return None
        rows, seen = [], set()
        for material in sorted(demand):
            if demand[material] <= 0:
                continue
            commodity = self.material_pool(material)[0]
            if commodity in seen:
                continue
            seen.add(commodity)
            factor = self.material_price_factor(commodity)
            if factor > 1.05:
                rows.append((commodity, factor))
        return rules.premium_sentence(rows)

    def material_shortfall(self, material: str, by_tag: Any = None) -> float:
        """Tonnes a year of `material` demand that neither the seat's own workings nor the market cover: the one shortfall
        figure the capacity rows and the remedy text both use."""
        if by_tag is None:
            by_tag = self.demand_by_supply_tag(self.annual_material_demand())
        need, own = rules.demand_and_own_supply(by_tag, self.own_material_supply).get(material, (0.0, 0.0))
        if need <= 0.0:
            return 0.0
        return rules.shortfall(need, own, self.market_tonnes(material))

    def demand_by_supply_tag(self, demand: Any) -> collections.Counter:
        """Demand grouped by the (commodity, tag) pool it draws on, so materials that share a pool add up."""
        return rules.demand_by_tag(demand, self.material_pool)

    def own_supply_by_commodity(self, by_tag: Any) -> Dict[str, Tuple[float, float]]:
        """{commodity: (demand, own supply)} for a grouping by pool; tags that share one land base are in the units of the
        reference tag."""
        return rules.demand_and_own_supply(by_tag, self.own_material_supply)

    # ---- how a material reaches the seat ----

    def makers_of(self, material: str) -> List[str]:
        """Ids of the technology-tree concerns whose output includes `material`, sorted."""
        return sorted(node_id for node_id, node in self.needs.tree_nodes().items()
                      if material in (node.get("_output_per_year") or {}))

    def material_supply_route(self, material: str) -> Dict[str, Any]:
        """{"route", "makers"} for a material key: held, market, imported, makeable or unavailable, and the concerns of the
        tree that would make it."""
        commodity, tag = self.material_pool(material)
        route = rules.supply_route(self.needs.goods_stock[commodity], self.own_material_supply(tag),
                                   self.market_tonnes(commodity), self.import_tonnes(commodity),
                                   self.needs.can_be_bought[material])
        return {"route": route, "makers": self.makers_of(material)}

    def material_unsupplied_sentence(self, material: str) -> str:
        """One sentence on why nothing of `material` reaches the seat, or "" when something does."""
        reach = self.material_supply_route(material)
        makers = [node_id for node_id in reach["makers"] if self.needs.visibility(node_id, None)]   # fog: only known concerns
        done = self.needs.techniques_held()
        return rules.unsupplied_sentence(material, reach["route"], makers, [node_id for node_id in makers if node_id in done])

    def materials_report(self) -> List[Dict[str, Any]]:
        """Stocks, annual flows, demand and current trade values of every tracked commodity."""
        demand = self.demand_by_commodity()
        materials = set(self.needs.held_goods()) | {pair[0] for pair in MATERIAL_CHECKS.values()}
        materials |= {commodity for commodity in self.needs.mine_capacity()}
        rows = []
        for material in sorted(materials):
            quote = self.needs.goods_quote[material]
            if not quote:
                continue
            annual_demand = sum(value for _tag, value in demand.get(material, ()))
            own = sum(self.own_material_supply(tag) for commodity, tag in self.own_production_tags() if commodity == material)
            stock = self.needs.goods_stock[material]
            rows.append({**quote, "stock_on_hand_tonnes": stock,
                         "own_production_tonnes_per_year": own,
                         "current_demand_tonnes_per_year": annual_demand,
                         "stock_covers_years_at_current_demand": stock / annual_demand if annual_demand > 1e-9 else None})
        return rows
