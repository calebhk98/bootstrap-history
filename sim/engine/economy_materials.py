"""Raw-material supply: the nine hand-named commodities, and the generic
mechanism that covers the other ~150 (159 distinct material keys in
data/tech_tree.json today minus the 9 named ones; see the
GENERALISING BEYOND THE 9 HAND-NAMED COMMODITIES comment below for the
precise 146-of-159 count against the 13 MATERIAL_CHECKS keys).

Every method here answers how much of a raw
material - ore, charcoal, saltpetre, or any of the 159 material
keys - you can actually get your hands on this year, whether that is
your own production, a purchase against the empire's market, or stock
carried over from an earlier year. Covers: CHARCOAL_PER_HA/MARKET_SHARE
(the nine curated commodities' own supply figures); the generic
fallback that fits an output-vs-price curve from those nine so that
every OTHER material key behaves correctly without anyone having
curated it by hand (_commodity_ledger()/_material_commodity_map()/
_material_prices()/_book_price_per_kg()/_material_tag()/
_generic_national_output_t_per_yr()/_generic_market_share()/
_normalize_material_name()); chosen_fuel() and annual_material_demand()
(what a year's building programme actually needs); _own_material_supply()/
_material_market_tonnes()/_demand_by_supply_tag() (what you can supply
yourself versus buy); and the stock-versus-flow half - _material_stock()/
material_stock_t()/material_trade_quote()/buy_material_stock()/
sell_material_stock()/materials_report()/_throttle_demand_split()/
_own_production_tags() - a running balance in tonnes, carried across
years, separate from any one year's flow; see the stock-vs-flow section
below for why stock and flow must be kept apart.

MaterialSupplyMixin is composed into EconomyMixin (economy.py) alongside
the other economy sub-mixins; see that file for the composition and for
the grouping evidence. CLAUDE.md's naming/heuristic-labelling conventions
apply here exactly as they do everywhere else in the engine, regardless
of which file a method lives in.

THE CLASS-LEVEL CACHE. _commodity_ledger(), _material_commodity_map()
and _material_prices() each cache their answer on the bare class object
MaterialSupplyMixin itself (`getattr(MaterialSupplyMixin, "...", None)`
/ `MaterialSupplyMixin._foo = ...`), not on self, because none of a
CommodityLedger, the mat-key-to-commodity-id map, or prices.json's own
figures differ between one Sim instance and the next in the same
process - they are read from disk once and shared, deliberately, the
same lazy-on-the-class pattern _land_freight_physical_inputs() in
economy_freight.py uses for the same reason.

TRAP: the literal class name in that getattr/setattr MUST match whatever
class actually holds these three methods. If they are ever moved to a
different class or file, the cache key has to move with them - a
mismatch breaks the cache silently, invisible to import, to `validate`
and to compilation, surfacing only when a command that reads a material
price first runs and finds a cache that was never populated. See
economy.py's own CRITICAL note on this file's history for the fuller
account.
"""
import collections, json, os

from . import commodities as _commod
from sim.constants import declare
from sim.unit_conversions import KILOGRAMS_PER_TONNE


class MaterialSupplyMixin:

    # ---- raw material supply ------------------------------------------------
    CHARCOAL_PER_HA = declare(
        "CHARCOAL_PER_HA", 0.75, kind="engineering_estimate",
        unit="tonnes charcoal/hectare/year, sustainable coppice yield",
        source="Order-of-magnitude figure for a sustainably managed "
               "coppice under traditional charcoal-burning practice; the "
               "same figure this module's own resource_throttle() "
               "docstring cites ('a hectare of coppice yields about 0.75 "
               "tonnes of charcoal a year').",
        confidence="C",
        why="Converts hectares of owned woodland into tonnes/year of "
            "charcoal - the single binding constraint that decides whether "
            "a blast furnace can run at all, per this file's own charcoal "
            "commentary.")
    # How much of the empire's annual output you can actually BUY. This is not
    # one number: charcoal is bulky, crumbles when carted, and is therefore a
    # LOCAL commodity no matter how much of it the empire makes in total, while
    # coal is barely used by anyone so you can have almost all of it.
    # gold's 0.01 is not re-guessed: it is commodities.json's own gold entry
    # (market_share, already reasoned there against the same imperial-mint
    # scarcity that makes MARKET_SHARE["silver"] this low), so the two files
    # agree on how tightly a private buyer can get at the metalla's gold.
    _MARKET_SHARE_WHY = (
        "What fraction of the empire's whole annual national output of "
        "this material an ordinary buyer with no special standing can "
        "actually reach, before patronage multipliers (see "
        "_material_market_tonnes) apply. Bulk, transportability and how "
        "concentrated ownership of the resource is (imperial mints and "
        "metalla versus an ordinary quarry) all matter physically, but no "
        "attested Roman market-share figure exists for any of these "
        "materials; each is reasoned by hand from those physical "
        "properties, not measured.")
    MARKET_SHARE_CHARCOAL = declare(
        "MARKET_SHARE_CHARCOAL", 0.002, kind="temporary_heuristic",
        unit="fraction of national output", source=None,
        confidence="D",
        why=_MARKET_SHARE_WHY + " Charcoal specifically is bulky and "
            "crumbles when carted, so it is treated as almost entirely "
            "a local commodity regardless of total empire-wide output.")
    MARKET_SHARE_IRON = declare(
        "MARKET_SHARE_IRON", 0.03, kind="temporary_heuristic",
        unit="fraction of national output", source=None,
        confidence="D", why=_MARKET_SHARE_WHY)
    MARKET_SHARE_COPPER = declare(
        "MARKET_SHARE_COPPER", 0.03, kind="temporary_heuristic",
        unit="fraction of national output", source=None,
        confidence="D", why=_MARKET_SHARE_WHY)
    MARKET_SHARE_LEAD = declare(
        "MARKET_SHARE_LEAD", 0.03, kind="temporary_heuristic",
        unit="fraction of national output", source=None,
        confidence="D", why=_MARKET_SHARE_WHY)
    MARKET_SHARE_TIN = declare(
        "MARKET_SHARE_TIN", 0.05, kind="temporary_heuristic",
        unit="fraction of national output", source=None,
        confidence="D", why=_MARKET_SHARE_WHY)
    MARKET_SHARE_SILVER = declare(
        "MARKET_SHARE_SILVER", 0.01, kind="temporary_heuristic",
        unit="fraction of national output", source=None,
        confidence="D",
        why=_MARKET_SHARE_WHY + " Held low specifically because "
            "silver mining was heavily imperial-mint property, which "
            "MARKET_SHARE_GOLD's own sourced figure also reflects.")
    MARKET_SHARE_COAL = declare(
        "MARKET_SHARE_COAL", 0.50, kind="temporary_heuristic",
        unit="fraction of national output", source=None,
        confidence="D",
        why=_MARKET_SHARE_WHY + " Held high specifically because coal "
            "was barely used by anyone in this period, so almost all "
            "of the (small) national output is available to a buyer.")
    MARKET_SHARE_SALTPETRE = declare(
        "MARKET_SHARE_SALTPETRE", 0.0, kind="temporary_heuristic",
        unit="fraction of national output", source=None,
        confidence="D",
        why=_MARKET_SHARE_WHY + " Zero specifically because there is "
            "no open saltpetre market at all in this period; it is "
            "made in nitre beds, not bought (see build_nitre).")
    MARKET_SHARE_GOLD = declare(
        "MARKET_SHARE_GOLD", 0.01, kind="temporary_heuristic",
        unit="fraction of national output",
        source="commodities.json's own gold entry (market_share), "
               "already reasoned there against imperial-mint scarcity - "
               "reused here rather than re-guessed so the two files "
               "agree on how tightly a private buyer can reach the "
               "metalla's gold.",
        confidence="C", why=_MARKET_SHARE_WHY)
    MARKET_SHARE = {
        'charcoal': MARKET_SHARE_CHARCOAL,
        'iron': MARKET_SHARE_IRON,
        'copper': MARKET_SHARE_COPPER,
        'lead': MARKET_SHARE_LEAD,
        'tin': MARKET_SHARE_TIN,
        'silver': MARKET_SHARE_SILVER,
        'coal': MARKET_SHARE_COAL,
        'saltpetre': MARKET_SHARE_SALTPETRE,
        'gold': MARKET_SHARE_GOLD,
    }

    # ---- GENERALISING BEYOND THE 9 HAND-NAMED COMMODITIES --------------------
    #
    # data/review/COMMODITY_DYNAMISM.md, an audit run directly against
    # this engine, found 149 of the then 162 distinct material keys the
    # tech tree used (about 92%) had a price read once from prices.json at
    # load time and never revisited for scarcity, surplus or anything else,
    # because MATERIAL_CHECKS/MARKET_SHARE above only ever named 13 keys by
    # hand. The tree has since dropped to 159 distinct material keys, all
    # 13 MATERIAL_CHECKS keys still among them, so the live count today is
    # 146 of 159 (still about 92%) - counted by intersecting MATERIAL_CHECKS
    # against every `mat` key in data/tech_tree.json; COMMODITY_DYNAMISM.md's
    # own audit script is not committed to the repo (same status as
    # NAMING_PLAN.md's scanner), so this is measured, not scriptable here.
    # Its own worked case was aluminium: "no mine, no supply lever of any
    # kind... nothing in economy.py even contains the string aluminium."
    #
    # The fix below is NOT a per-material rule. It is a generic fallback that
    # activates for any material key this file has no curated entry for,
    # using the one number every material already has: its own book price in
    # prices.json (every material key a node's `mat` dict names MUST have a
    # prices.json entry already, or data.py's own load() would have raised
    # building `_material_cost` in the first place - so this genuinely
    # covers all 159, not just the ones anyone thought to add). A cheap,
    # plentiful material gets assumed to have a large national output and a
    # wide buyable share; a dear, rare one gets less of both - fitted, not
    # guessed, from the curated figures the 9 tracked commodities already
    # carry: iron (1.0 den/kg) is rated 82,500 t/yr, copper (4.0) 15,000,
    # gold (3,440) 9. log(output) against log(price) across those three
    # (four orders of magnitude in price) fits close to output =
    # 82,500 / price**1.1 - which reproduces gold's real 9 t/yr to within
    # 20% despite the fit never having seen gold's number, because scarcity
    # and price genuinely do move together, not because gold is special.
    # This is exactly the standard COMMODITY_DYNAMISM.md sets: "a commodity
    # nobody anticipated must behave correctly because the mechanism is
    # supply and demand, not because somebody wrote a rule for it."
    GENERIC_OUTPUT_ANCHOR_T_PER_YR = declare(
        "GENERIC_OUTPUT_ANCHOR_T_PER_YR", 82500.0, kind="engineering_estimate",
        unit="tonnes/year at price=1 denarius/kg", source=
        "Fitted (log-log regression) from resources.json's own curated "
        "empire outputs for iron (1.0 den/kg -> 82,500 t/yr), copper "
        "(4.0 -> 15,000 t/yr) and gold (3,440 -> 9 t/yr) - see the class "
        "comment above for the fit and its cross-check against gold's own "
        "number, which the fit never saw.",
        confidence="C",
        why="The anchor point of a fitted output-vs-price curve used to "
            "guess national output for any of the 146 material keys this "
            "file has no curated resources.json figure for. A real answer "
            "needs an actual output figure per material, which is exactly "
            "what data/production/'s coverage work is building toward "
            "replacing this fallback with.")
    GENERIC_OUTPUT_PRICE_EXPONENT = declare(
        "GENERIC_OUTPUT_PRICE_EXPONENT", 1.1, kind="hardcoded_outcome",
        unit="dimensionless exponent on price", source=
        "Same three-point log-log fit as GENERIC_OUTPUT_ANCHOR_T_PER_YR.",
        confidence="C",
        why="How fast national output falls as a material's own book price "
            "rises, in the fitted fallback curve - scarcity and price "
            "moving together is a real, general economic regularity; this "
            "specific exponent is fitted to three commodities and "
            "extrapolated to every other material, which is the honest "
            "limit of what three points can support.")
    GENERIC_OUTPUT_FLOOR_T_PER_YR = declare(
        "GENERIC_OUTPUT_FLOOR_T_PER_YR", 5.0, kind="temporary_heuristic",
        unit="tonnes/year (minimum)", source=None, confidence="D",
        why="Safety floor so an extremely expensive material's fitted "
            "output never rounds to a market that supplies literally "
            "nothing. Not fitted; a defensive bound on the formula above.")
    GENERIC_OUTPUT_CEILING_T_PER_YR = declare(
        "GENERIC_OUTPUT_CEILING_T_PER_YR", 400000.0, kind="temporary_heuristic",
        unit="tonnes/year (maximum)", source=None, confidence="D",
        why="Safety ceiling so an extremely cheap material's fitted output "
            "never runs away to an implausible national output. Not "
            "fitted; a defensive bound on the formula above.")

    def _commodity_ledger(self):
        """The 9 curated commodities from commodities.json, as a
        CommodityLedger, cached on the CLASS (not the instance): the file
        does not change mid-run and building it involves a JSON load, the
        same reasoning _material_commodity_map below uses. Used two ways:
        as the reverse index from a material key to a curated commodity id
        (cast_iron_kg means "iron" there even though MATERIAL_CHECKS has
        never listed it), and, for the 4 curated-but-never-priced
        commodities this file's own MARKET_SHARE has never named (cloth,
        wool, cotton, copper_wire), as the SOURCE of national output and
        market share instead of the generic price-only guess below - see
        _generic_national_output_t_per_yr's own comment for why real,
        sourced data beats a formula wherever it already exists."""
        cached = getattr(MaterialSupplyMixin, "_commod_ledger_cache", None)
        if cached is None:
            cached = MaterialSupplyMixin._commod_ledger_cache = _commod.CommodityLedger()
        return cached

    def _material_commodity_map(self):
        """material key -> curated commodity id, from commodities.json's
        own material_keys lists. Cached on the class for the same reason
        as _commodity_ledger."""
        cached = getattr(MaterialSupplyMixin, "_material_commod_map_cache", None)
        if cached is None:
            cached = {}
            for commodity_id, commodity in self._commodity_ledger().commodities.items():
                for material_key in commodity.get("material_keys", []):
                    cached[material_key] = commodity_id
            MaterialSupplyMixin._material_commod_map_cache = cached
        return cached

    def _material_prices(self):
        """The flat per-kg book price for every material key in
        prices.json, read directly rather than threaded through Sim's
        constructor - the same pattern commodities.py's own
        load_commodities() already uses for its own file. Cached on the
        class: prices.json does not change mid-run."""
        cached = getattr(MaterialSupplyMixin, "_material_prices_cache", None)
        if cached is None:
            raw = json.load(open(os.path.join(_commod.ROOT, "data", "prices.json")))
            cached = {material_key: value["p"] for material_key, value in raw["purchase_prices_denarii"].items()
                     if isinstance(value, dict) and "p" in value}
            MaterialSupplyMixin._material_prices_cache = cached
        return cached

    def _book_price_per_kg(self, tag):
        """Denarii/kg for a raw material key (aluminium_kg, straight out of
        prices.json) or a curated commodity id (cloth, straight out of
        commodities.json's own base_price - the two files agree by
        construction, see commodities.json's own `_doc.reused_from`). None
        if this file cannot price it at all, which should not happen for
        any material key the tech tree actually uses (see the class
        comment above)."""
        prices = self._material_prices()
        if tag in prices:
            return prices[tag]
        commodity = self._commodity_ledger().commodities.get(tag)
        if commodity:
            price = float(commodity.get("base_price_denarii_per_kg", 0.0) or 0.0)
            return price or None
        return None

    def _material_tag(self, mat_key):
        """Which (commodity id, supply-pool tag) a raw material key draws
        on, generalised beyond the 13 keys MATERIAL_CHECKS names by hand.

        Three tiers, most-specific first: MATERIAL_CHECKS (the 9 originally
        tracked commodities, unchanged); commodities.json's own
        material_keys grouping (iron_bloom_kg and cast_iron_kg both mean
        "iron" there, cloth_bag_kg and linen_kg both mean "cloth," though
        none of MATERIAL_CHECKS above has ever listed any of them); and,
        for the material nothing has ever named, its own bare material key
        as a one-member commodity of itself - "aluminium_kg" becomes the
        commodity "aluminium_kg" (its own price identifies it; no reverse
        lookup needed). This is the actual generalisation
        COMMODITY_DYNAMISM.md's finding describes: 149 of the then 162
        material keys got no price response at all because nothing but
        membership in a 13-entry hand list was ever asked - 146 of 159
        today (see the GENERALISING BEYOND THE 9 HAND-NAMED COMMODITIES
        comment earlier in this file for how that re-count was done).
        """
        pair = self.MATERIAL_CHECKS.get(mat_key)
        if pair:
            return pair
        cid = self._material_commodity_map().get(mat_key, mat_key)
        return (cid, "mine:" + cid)

    def _generic_national_output_t_per_yr(self, tag):
        """National output for a commodity/material this file has no
        curated resources.json figure for - the MARKET half of supply (see
        _material_market_tonnes). Prefers real data over a guess wherever
        real data exists: if `tag` is one of the 4 commodities.json defines
        but MARKET_SHARE has never priced (cloth, wool, cotton,
        copper_wire), this reads THAT commodity's own national/manufacturing
        output through CommodityLedger.country_output() - which already
        knows a built power loom raises cloth output, or cyanidation raises
        gold's, per commodities.json's own `produced_by` multipliers. That
        is COMMODITY_DYNAMISM.md's own third finding wired in for real:
        "a genuinely general elasticity-based price function... sitting
        unconnected." Only a material with no curated home at all (silk,
        glass, the acids and dyes and alloys) falls through to the generic
        price-derived formula documented on GENERIC_OUTPUT_ANCHOR_T_PER_YR
        above."""
        ledger = self._commodity_ledger()
        if tag in ledger.commodities:
            return ledger.country_output(tag, built=self.household.done)
        price = self._book_price_per_kg(tag)
        if price is None or price <= 0:
            return self.GENERIC_OUTPUT_CEILING_T_PER_YR
        out = self.GENERIC_OUTPUT_ANCHOR_T_PER_YR / (price ** self.GENERIC_OUTPUT_PRICE_EXPONENT)
        return max(self.GENERIC_OUTPUT_FLOOR_T_PER_YR,
                   min(self.GENERIC_OUTPUT_CEILING_T_PER_YR, out))

    def _generic_market_share(self, tag):
        """What fraction of _generic_national_output_t_per_yr an ordinary
        buyer (no special standing) can reach, for a commodity/material
        MARKET_SHARE has no curated figure for. Same two-tier preference as
        the output figure: a commodities.json commodity's own market_share
        (cloth 0.5, wool 0.4, cotton 1.0 trade-only, copper_wire 0.6) where
        one exists; otherwise a generic curve fitted the same way
        GENERIC_OUTPUT was - rarer, dearer materials are held closer (gold
        0.01, silver 0.01) and cheap bulk ones are wide open (coal 0.50) -
        clamped well inside that observed range since this is a default
        for a material nobody has separately reasoned about, not a
        specific claim."""
        ledger = self._commodity_ledger()
        if tag in ledger.commodities:
            return float(ledger.commodities[tag].get(
                "market_share", self.GENERIC_MARKET_SHARE_LEDGER_FALLBACK))
        price = self._book_price_per_kg(tag)
        if price is None or price <= 0:
            return self.GENERIC_MARKET_SHARE_NO_PRICE_FALLBACK
        return max(self.GENERIC_MARKET_SHARE_FLOOR,
                   min(self.GENERIC_MARKET_SHARE_CEILING,
                       self.GENERIC_MARKET_SHARE_SCALE
                       / (max(price, 0.01) ** self.GENERIC_MARKET_SHARE_PRICE_EXPONENT)))

    GENERIC_MARKET_SHARE_LEDGER_FALLBACK = declare(
        "GENERIC_MARKET_SHARE_LEDGER_FALLBACK", 0.03, kind="temporary_heuristic",
        unit="fraction of national output", source=None, confidence="D",
        why="Fallback market share for a curated commodities.json commodity "
            "that names no market_share field of its own - a middling, "
            "unremarkable buyable fraction picked so a missing field does "
            "not silently become 'unbuyable' or 'unlimited'.")
    GENERIC_MARKET_SHARE_NO_PRICE_FALLBACK = declare(
        "GENERIC_MARKET_SHARE_NO_PRICE_FALLBACK", 0.20, kind="temporary_heuristic",
        unit="fraction of national output", source=None, confidence="D",
        why="Fallback market share for a material this file cannot even "
            "price at all - deliberately generous (wide open) since a "
            "material with no price data has no basis for restricting it "
            "either; a placeholder rather than a reasoned figure.")
    GENERIC_MARKET_SHARE_SCALE = declare(
        "GENERIC_MARKET_SHARE_SCALE", 0.08, kind="engineering_estimate",
        unit="dimensionless scale on the price-fitted market-share curve",
        source="Fitted the same way GENERIC_OUTPUT_ANCHOR_T_PER_YR was, "
               "against the curated MARKET_SHARE figures for gold/silver "
               "(0.01, rare and dear) and coal (0.50, cheap and open).",
        confidence="C",
        why="Scale of the price-fitted curve giving a generic material's "
            "market share when nothing more specific is known. Same honest "
            "limit as the output fit: three curated points fitted and "
            "extrapolated, not a measurement for any specific material.")
    GENERIC_MARKET_SHARE_PRICE_EXPONENT = declare(
        "GENERIC_MARKET_SHARE_PRICE_EXPONENT", 0.4, kind="engineering_estimate",
        unit="dimensionless exponent on price", source=
        "Same three-point fit as GENERIC_MARKET_SHARE_SCALE.",
        confidence="C",
        why="How fast a generic material's buyable share shrinks as its "
            "price rises - rarer, dearer materials are held closer by "
            "whoever controls them, a real and general pattern; the "
            "specific exponent is fitted to three commodities.")
    GENERIC_MARKET_SHARE_FLOOR = declare(
        "GENERIC_MARKET_SHARE_FLOOR", 0.01, kind="temporary_heuristic",
        unit="fraction of national output (minimum)", source=None,
        confidence="D",
        why="Clamp so the fitted generic market-share curve never reaches "
            "a literal zero for an ordinary buyer, however dear the "
            "material - a defensive bound, not a reasoned floor.")
    GENERIC_MARKET_SHARE_CEILING = declare(
        "GENERIC_MARKET_SHARE_CEILING", 0.35, kind="temporary_heuristic",
        unit="fraction of national output (maximum)", source=None,
        confidence="D",
        why="Clamp so the fitted generic market-share curve stays well "
            "inside the observed range of the curated figures it was "
            "fitted from, per this method's own docstring ('a default for "
            "a material nobody has separately reasoned about, not a "
            "specific claim') - a defensive bound, not a reasoned ceiling.")

    def _normalize_material_name(self, mat):
        """Accept either spelling when a player names a material: the
        short curated name a mine has always used ("iron"), or the exact
        material key the tree itself uses ("aluminium_kg") - a player who
        has only ever seen `why` quote "aluminium_kg" in a bill of
        materials should not have to guess it needs no suffix, and the
        seven original short names must keep working exactly as before."""
        mat = str(mat or "").strip().lower()
        if not mat or mat in self.MINE_CAPEX_PER_T_YR:
            return mat
        prices = self._material_prices()
        if mat in prices or mat in self._commodity_ledger().commodities:
            return mat
        for suffix in ("_kg", "_g"):
            cand = mat + suffix
            if cand in prices:
                return cand
        return mat

    # Coke and charcoal are not interchangeable at one kg for one kg. A charcoal
    # blast furnace burns about 3 kg of charcoal per kg of iron; a coke furnace
    # burns about 1.6 kg of coke, and coke is about 1.6 kg of coal, so 2.56 kg
    # of coal. Switching fuel therefore MOVES the demand to a different material
    # at 0.85 of the mass, and that is the whole reason coke mattered: not that
    # it is better fuel, but that coal is dug and charcoal has to be grown.
    COKE_PER_CHARCOAL = declare(
        "COKE_PER_CHARCOAL", 0.85, kind="engineering_estimate",
        unit="kg coal-equivalent demand per kg of charcoal it replaces",
        source="Blast-furnace fuel consumption ratios: roughly 3 kg "
               "charcoal per kg of iron by the charcoal route, versus "
               "roughly 1.6 kg coke (itself roughly 1.6 kg of coal) per kg "
               "of iron by the coke route - see the comment above for the "
               "arithmetic (2.56 kg coal / 3 kg charcoal is approximately "
               "0.85).",
        confidence="C",
        why="Converts a node's charcoal demand into the equivalent coal "
            "demand when coke is the chosen fuel - the actual substitution "
            "that decided whether an industrialising civilisation is bound "
            "by grown fuel or dug fuel.")

    def chosen_fuel(self, node_id):
        """Which fuel this node would actually burn, given what you have.

        Must actually swap the material demand, not only a quality factor:
        a fuel OR-group where picking coke changes the quality factor but
        leaves the charcoal demand untouched can never show the one
        substitution that actually decided industrial history.
        """
        for group in (self.nodes[node_id].get("req_any") or []):
            if "fuel" not in str(group.get("group", "")).lower():
                continue
            best, pick = 0.0, None
            for opt, qual in (group.get("options") or {}).items():
                have = opt in self.household.done or opt not in self.nodes
                if have and float(qual) > best:
                    best, pick = float(qual), opt
            if pick and ("coke" in pick or "coal" in pick):
                return "coke"
        return "charcoal"

    def annual_material_demand(self):
        """Tonnes per year of the materials that actually bind, from work in hand."""
        # Cached value: collections.Counter of annual material requirements
        # Dependencies: household active projects (_active_ver), completed projects (_done_ver)
        # Invalidated by: _active_changed(), _done_changed()
        # Nested mutation concerns: tracked via recursive _InvalidatingDict wrapping on household.active
        # Serialized: no
        cache_key = (
            getattr(self.household, "_active_ver", 0),
            getattr(self.household, "_done_ver", 0),
        )
        cache = getattr(self.household, "_annual_mat_demand_cache", None)
        if cache is not None and cache[0] == cache_key:
            return cache[1].copy()

        demand = collections.Counter()
        for node_id in sorted(self.household.active):
            node = self.nodes[node_id]
            span = max(1.0, float(node.get("build_yrs") or node.get("yrs") or 1.0))
            coke = self.chosen_fuel(node_id) == "coke"
            for material, quantity in node["mat"].items():
                if coke and material in ("charcoal_kg", "firewood_kg"):
                    demand["coal_kg"] += float(quantity) * self.COKE_PER_CHARCOAL / span / KILOGRAMS_PER_TONNE
                    continue
                demand[material] += float(quantity) / span / KILOGRAMS_PER_TONNE     # kg -> tonnes per year
        # A furnace does not eat charcoal only while it is being built. It eats
        # charcoal every year it runs, forever. Omitting that was why forest
        # ownership never mattered in the model and always mattered in reality.
        for node_id in self.done_in_order():
            node = self.nodes[node_id]
            if node["up"] <= 0 or not node["mat"]:
                continue
            span = max(1.0, float(node.get("build_yrs") or node.get("yrs") or 1.0))
            coke = self.chosen_fuel(node_id) == "coke"
            for material, quantity in node["mat"].items():
                if coke and material in ("charcoal_kg", "firewood_kg"):
                    demand["coal_kg"] += (self.STANDING_MATERIAL_DRAW_SHARE * float(quantity)
                                           * self.COKE_PER_CHARCOAL / span / KILOGRAMS_PER_TONNE)
                    continue
                demand[material] += self.STANDING_MATERIAL_DRAW_SHARE * float(quantity) / span / KILOGRAMS_PER_TONNE
        self.household._annual_mat_demand_cache = (cache_key, demand)
        return demand.copy()

    STANDING_MATERIAL_DRAW_SHARE = declare(
        "STANDING_MATERIAL_DRAW_SHARE", 0.5, kind="temporary_heuristic",
        unit="fraction of a node's build-time material draw rate, per year "
             "of standing operation", source=None, confidence="D",
        why="A finished, running installation - a furnace, a workshop - "
            "goes on consuming its listed material every year it operates, "
            "not only while being built (see the comment above: 'a furnace "
            "does not eat charcoal only while it is being built'). This is "
            "the ongoing rate as a fraction of the build-time rate, reused "
            "identically for electrical demand in _electricity_demand_kw() "
            "and _node_annual_tonnes() below. The DIRECTION is a real "
            "physical claim (standing operation consumes fuel/electricity "
            "continuously); the specific half-rate is an invented "
            "placeholder - a real figure needs a per-process duty cycle or "
            "throughput figure this tree does not carry.")

    # Which raw material keys (as they appear in a node's `mat` dict) draw on
    # which tracked commodity, and how "your own supply of it" is computed.
    # Factored out of resource_throttle so material_price_factor() below reads
    # the identical figures rather than a second guess at them.
    #
    # copper_wire_kg and wire_drawn_kg were UNTHROTTLED before this: 36 real
    # nodes (the whole el2_ electrical branch, plus gp_magnet_wire_enamelled,
    # hom_piano, en_rotary_converter...) drew drawn copper wire and none of it
    # ever competed with copper_kg for the same finite copper supply. This is
    # precisely the gap COMMODITIES.md section 7 names as "the real test":
    # wire is copper, drawn, and data/world/commodities.json's own
    # copper_wire recipe (a 5% drawing loss) already says so -- see
    # wire_chain_report() below, which asks that exact question against this
    # civilisation's real copper numbers via commodities.py's
    # propagate_demand(). gold_kg (fin_central_bank's 1000 kg, tx2_watch_case,
    # the gold-leaf electroscope) was also untracked despite Sim.open_mine
    # already supporting a gold mine (MINE_CAPEX_PER_T_YR) and
    # resources.json already carrying an empire gold figure (9 t/yr) --
    # nothing wired the two together. gold_g (LEDs, transistors: 1-20 grams)
    # is NOT added here, still: annual_material_demand() assumes every *_kg
    # key is kilograms, so a *_g key divided by 1000 would read as a
    # thousandth of what it is. resource_throttle() routes every *_g key
    # through the LAB-SCALE stock path instead (see its own comment and
    # LAB_SCALE_SUFFIX below), which corrects the grams/kilograms reading
    # at the one place that reads it, rather than by adding gold_g to this
    # dict (that would make grams of gold compete with fin_central_bank's
    # tonnes for the same ANNUAL FLOW, which is precisely the stock-vs-flow
    # confusion this path exists to undo).
    MATERIAL_CHECKS = {
        "charcoal_kg": ("charcoal", "forest1"),
        "firewood_kg": ("charcoal", "forest4"),
        "iron_bar_kg": ("iron", "mine:iron"),
        "iron_ore_kg": ("iron", "mine:iron"),
        "coal_kg":     ("coal", "mine:coal"),
        "copper_kg":       ("copper", "mine:copper"),
        "copper_wire_kg":  ("copper", "mine:copper"),
        "wire_drawn_kg":   ("copper", "mine:copper"),
        "lead_kg":     ("lead", "mine:lead"),
        "tin_kg":      ("tin", "mine:tin"),
        "silver_kg":   ("silver", "mine:silver"),
        "gold_kg":     ("gold", "mine:gold"),
        "nitre_kg":    ("saltpetre", "nitre"),
    }

    FIREWOOD_PER_CHARCOAL_MASS_RATIO = declare(
        "FIREWOOD_PER_CHARCOAL_MASS_RATIO", 4.0, kind="engineering_estimate",
        unit="kg raw firewood per kg-equivalent of charcoal (dimensionless)",
        source="Traditional charcoal-burning loses most of the wood's mass "
               "as volatiles and water during carbonisation; a roughly "
               "four-to-one wood-to-charcoal mass ratio is the commonly "
               "cited order of magnitude for earth-kiln and pit methods.",
        confidence="C",
        why="A hectare of coppice yields several times more mass as raw, "
            "unconverted firewood (the 'forest4' tag, firewood_kg's supply) "
            "than it does as charcoal (the 'forest1' tag) from the SAME "
            "wood, because charcoal-making itself consumes most of the "
            "mass. This is the ratio between those two yields.")

    def _own_material_supply(self, tag):
        """Tonnes a year of a tracked commodity you supply yourself, not
        bought from anyone: mines you sank, woodland you bought, nitre beds
        you built. See MATERIAL_CHECKS for which tag means what."""
        if tag == "forest1":
            return self.household.forest_ha * self.CHARCOAL_PER_HA
        if tag == "forest4":
            return self.household.forest_ha * self.CHARCOAL_PER_HA * self.FIREWOOD_PER_CHARCOAL_MASS_RATIO
        if tag == "nitre":
            return self.household.nitre_bed_m2 * self.NITRE_YIELD_T_PER_M2
        if tag.startswith("mine:"):
            mat = tag[5:]
            # DEPLETION AND TECHNOLOGY, not the nominal tonnage you sank
            # capital into. mine_capacity is a historical record of what
            # you PAID for; what a working actually YIELDS this year is
            # that, discounted by how worked-out it is and multiplied by
            # whatever mining technology has done to counter that -- see
            # mine_depletion_factor() and mining_tech()'s own comments.
            yld, _cost = self.mining_tech(mat)
            return (self.mine_capacity.get(mat, 0.0)
                    * self.mine_depletion_factor(mat) * yld)
        return 0.0

    def _material_market_tonnes(self, emp_key):
        """Tonnes a year of `emp_key` the empire's market will sell you, at
        your current standing. The MARKET half of resource_throttle()'s
        `supply`; material_price_factor() reads it too.

        GENERALISED: resources.json's empire_output_100ad table and this
        file's own MARKET_SHARE only ever name a handful of materials by
        hand. A real figure, when one exists, is used unchanged;
        _generic_national_output_t_per_yr and _generic_market_share supply
        a reasoned default for everything else, so a material nobody named
        still has a market rather than an actual hard zero.
        """
        emp = self.res["empire_output_100ad"]
        entry = emp.get(emp_key)
        national = entry.get("t_per_yr", 0) if entry is not None else (
                   self._generic_national_output_t_per_yr(emp_key))
        share = self.MARKET_SHARE.get(emp_key)
        if share is None:
            share = self._generic_market_share(emp_key)
        # How much of a market you can command is a function of STANDING, not
        # just of money. A stranger buys at the margin; a man with senatorial
        # backing buys through their agents; a holder of imperial patronage
        # has the fiscus itself as a supplier, and the metalla were largely
        # imperial property. Charcoal is exempt because no amount of standing
        # makes a bulky crumbling fuel travel further than it can travel.
        if emp_key != "charcoal":
            if self.running("patron_imperial"):     share *= self.MARKET_STANDING_PATRON_IMPERIAL
            elif self.running("patron_senatorial"): share *= self.MARKET_STANDING_PATRON_SENATORIAL
            elif self.has("citizenship"):       share *= self.MARKET_STANDING_CITIZENSHIP
            share = min(share, self.MARKET_STANDING_SHARE_CEILING)
        # GEOLOGY, NOT DEMOGRAPHY: mineral availability must scale with
        # mineral_scale() - the regions this civilization actually holds
        # and can trade with (see _compute_mineral_scale) - not with
        # self.pop_scale. A coalfield does not care how many people live
        # near it; England in 1300 gets a large share of Europe's coal
        # market because England is where the coal is, independent of its
        # population. Charcoal stays on pop_scale: it is not mined, it is
        # a local wood market, and THAT genuinely does track how much
        # local economic activity there is to buy firewood from.
        scale = self.pop_scale if emp_key == "charcoal" else self.mineral_scale(emp_key)
        market = national * share * scale
        # Bengal saltpetre: an existing annual sea route, not a nitre bed.
        # This is the single most useful thing in the geography file.
        if emp_key == "saltpetre" and self.running("exp_trade_route_extend"):
            market += self.SALTPETRE_TRADE_ROUTE_TONNES_PER_YR
        return market

    MARKET_STANDING_PATRON_IMPERIAL = declare(
        "MARKET_STANDING_PATRON_IMPERIAL", 6.0, kind="temporary_heuristic",
        unit="multiple on buyable market share", source=None,
        confidence="D",
        why="How much further an imperial patron's standing opens the "
            "market for a tracked material, on the reasoning that the "
            "fiscus itself becomes a supplier and the metalla were largely "
            "imperial property. The direction is a real institutional "
            "fact; the sixfold size is tuned game balance, not derived "
            "from any attested imperial-supply share.")
    MARKET_STANDING_PATRON_SENATORIAL = declare(
        "MARKET_STANDING_PATRON_SENATORIAL", 2.5, kind="temporary_heuristic",
        unit="multiple on buyable market share", source=None,
        confidence="D",
        why="As MARKET_STANDING_PATRON_IMPERIAL, for a senatorial patron - "
            "buying through their agents rather than the fiscus itself. "
            "Tuned, not derived.")
    MARKET_STANDING_CITIZENSHIP = declare(
        "MARKET_STANDING_CITIZENSHIP", 1.4, kind="temporary_heuristic",
        unit="multiple on buyable market share", source=None,
        confidence="D",
        why="What plain citizenship, with no patron at all, is worth over "
            "a stranger buying at the margin. Tuned, not derived.")
    MARKET_STANDING_SHARE_CEILING = declare(
        "MARKET_STANDING_SHARE_CEILING", 0.60, kind="temporary_heuristic",
        unit="fraction of national output (maximum, any buyer)",
        source=None, confidence="D",
        why="However much standing multiplies a buyer's reach, nobody but "
            "the state itself commands the whole national market for a "
            "material - this caps even an imperial patron's buyer well "
            "short of monopolising it. The cap's own level is a plausible "
            "round number, not derived from an attested ceiling.")
    SALTPETRE_TRADE_ROUTE_TONNES_PER_YR = declare(
        "SALTPETRE_TRADE_ROUTE_TONNES_PER_YR", 60.0, kind="temporary_heuristic",
        unit="tonnes/year", source=
        "geography.json's Bengal saltpetre sea-route entry, reused here as "
        "'the single most useful thing in the geography file' per the "
        "comment above - the ROUTE'S existence is a geography fact, but "
        "this file has no independent attested annual tonnage for it.",
        confidence="D",
        why="How much extra saltpetre a year an extended trade route to "
            "Bengal makes available, on top of the ordinary market. The "
            "route is real; the specific tonnage is an invented, plausible "
            "figure standing in for an actual historical trade-volume "
            "record.")

    def _demand_by_supply_tag(self, demand):
        """Group MATERIAL_CHECKS demand by (emp_key, tag) -- i.e. by which
        SHARED supply it actually draws on -- instead of leaving it split by
        raw material key.

        Materials that draw on the SAME supply pool must be summed
        together, not checked independently against the whole pool each:
        checking iron_bar_kg's need against the full iron supply, then
        iron_ore_kg's need against that SAME full supply again, would treat
        each as though it had the pool to itself - a plan needing 5 t/yr of
        ore and 4 t/yr of bar against a 6 t/yr supply would pass both
        checks (neither 5 nor 4 alone exceeds 6) while actually needing 9,
        fifty per cent more than there is. Grouping by (emp_key, tag) sums every
        material key that draws on the SAME pool (iron_bar_kg + iron_ore_kg;
        copper_kg + copper_wire_kg + wire_drawn_kg) while keeping
        charcoal_kg and firewood_kg separate, because they draw on the same
        forest at DIFFERENT yields per hectare (forest1 vs forest4, see
        _own_material_supply) and are not simply additive tonne-for-tonne.
        sorted(): a Counter keyed by tuples is still a dict, and the
        determinism convention here is to iterate sorted regardless of
        whether dict insertion order already happens to be safe, so a caller
        cannot inherit a bug by copying this pattern into a place where it
        is not.

        GENERALISED: must iterate over every material key `demand` itself
        carries, not just MATERIAL_CHECKS's own 13 keys - looking each of
        the 13 up in `demand` would leave any OTHER key `demand` carried
        silently unconsulted, the exact gap COMMODITY_DYNAMISM.md measures
        (146 of 159 material keys today). annual_material_demand() is
        already generic over every material key a node's `mat` dict names;
        this routes each one through _material_tag (curated grouping where
        one exists, the material's own bare key otherwise) to match.
        """
        by_tag = collections.Counter()
        for mat, amt in sorted(demand.items()):
            if amt:
                by_tag[self._material_tag(mat)] += amt
        return by_tag

    # ---- stock vs flow -----------------------------------------------------
    #
    # Requiring 20 grams of gold for a device must not require building a
    # tonne/year mining operation; realistically that gets bought outright.
    # Stock inventories have to be separate from annual production capacity
    # for exactly this reason.
    #
    # Everything above this point (MATERIAL_CHECKS, _own_material_supply,
    # _material_market_tonnes) answers in TONNES PER YEAR, a flow, and
    # nothing anywhere carried a balance across years: a mine's surplus
    # output in excess of what that year's building programme used simply
    # evaporated rather than banking (the gap DOCS_VS_ENGINE.md ranked #3,
    # "nothing you produce outlives the year you produced it"). That is one
    # half of the fix - a running stock, in tonnes, that PRODUCTION and
    # MARKET PURCHASES feed and CONSUMPTION draws down, carried on the Sim
    # instance across the whole run (lazily, like _material_demand_cache
    # below it: MaterialSupplyMixin does not own Sim.__init__).
    #
    # The other half: a handful of material keys in this tree are authored
    # in GRAMS, not kilograms
    # (caesium_g, diamond_g, germanium_g, gold_g, indium_g,
    # phosphor_bronze_g, platinum_g - every *_g key in use, see
    # COMMODITY_DYNAMISM's audit), because whoever wrote chm_catalyst_concept
    # or point_contact_transistor meant a benchtop quantity, not a shipment.
    # No list of "laboratory materials" is hand-picked here - the *_kg/*_g
    # distinction is the tree's OWN, already-general convention for exactly
    # this (see the MATERIAL_CHECKS comment above), so it generalises the
    # same way _material_tag already does: any future node that needs a
    # gram-scale quantity of anything gets this for free by being written
    # with a *_g key, the same way it already gets priced by
    # _book_price_per_kg without anyone adding it to a list. A *_g key's
    # demand is met from stock - and, whatever stock cannot cover, bought
    # outright on the spot, uncapped by mine or market flow - and NEVER sets
    # `binding`: buying a gram of something is a purchase, not a capacity
    # call, so it is never the reason a year's work is throttled. A *_kg
    # key's demand is unchanged in kind: it still has to clear the same
    # flow check as before, just against a supply that now includes
    # whatever is banked in stock, not only this year's flow.
    LAB_SCALE_SUFFIX = "_g"

    def _material_stock(self):
        """Tonnes of each tracked commodity (by emp_key) carried over from
        previous years - the stock half of stock vs flow. Lazily created on
        first use and then kept for the life of the Sim: MaterialSupplyMixin is a
        mixin, not __init__, and a fresh Counter is exactly what a household
        that has banked nothing yet should read as having. It is included in
        save_state()'s SAVE_FIELDS, so a resumed household retains the tonnes
        it actually produced or purchased.

        Deliberately a plain Counter, not commodities.py's own `Ledger`
        (also "a stock, not a flow," by its own docstring): Ledger works in
        kilograms and by commodity id, keyed for a module core.py still does
        not import; everything around resource_throttle() already works in
        TONNES and by emp_key, and the accounting below (own production vs
        market headroom, lab-scale vs industrial) needs that arithmetic
        inline, not behind add()/remove(). Reaching for Ledger here would
        buy a second unit system and a cross-module dependency, not a
        simpler mechanism - the "what was decided" COMMODITIES.md already
        documents for why commodities.py stays a library Sim calls into for
        specific answers (wire_chain_report's propagate_demand) rather than
        a second source of truth Sim's own state has to agree with."""
        stock = getattr(self.household, "_material_stock_ledger", None)
        if stock is None:
            stock = self.household._material_stock_ledger = collections.Counter()
        elif not isinstance(stock, collections.Counter):
            # A RESUMED SAVE HANDS THIS BACK AS A PLAIN DICT. It is in
            # SAVE_FIELDS so that a reloaded game is the same game - without it
            # a resume silently restarted at zero stock and played differently
            # from the run that was saved, the same class of fault as a fog
            # that could be rewound by reloading. JSON has no Counter, so
            # promote whatever came back before anything adds to it.
            stock = self.household._material_stock_ledger = collections.Counter(stock)
        return stock

    def material_stock_t(self, emp_key):
        """Tonnes of `emp_key` currently banked - the STOCK half of stock vs
        flow, which is the thing a player asking "how much iron do I actually
        own" wants. The `materials` command, trading actions, and resource
        throttle all read this same ledger.
        """
        return self._material_stock().get(emp_key, 0.0)

    MATERIAL_TRADE_SELL_SHARE_OF_BUY = declare(
        "MATERIAL_TRADE_SELL_SHARE_OF_BUY", 0.80, kind="temporary_heuristic",
        unit="fraction of the buy price (dimensionless)", source=None,
        confidence="D",
        why="The bid-ask spread on trading a raw material back to the "
            "market - a merchant's margin, real in kind (nobody buys and "
            "sells at the identical price) but not sized against any "
            "attested pre-industrial commodity spread.")

    def material_trade_quote(self, material):
        """Current buy/sell quote for one tonne of a material commodity."""
        material = str(material or "").strip().lower()
        per_kg = self._book_price_per_kg(material)
        if per_kg is None:
            return None
        buy = per_kg * KILOGRAMS_PER_TONNE * self.price_index * self.material_price_factor(material)
        return {"material": material, "buy_per_tonne": buy,
                "sell_per_tonne": buy * self.MATERIAL_TRADE_SELL_SHARE_OF_BUY,
                "market_available_tonnes_per_year": self._material_market_tonnes(material)}

    def buy_material_stock(self, material, tonnes):
        quote = self.material_trade_quote(material)
        tonnes = float(tonnes)
        if not quote or tonnes <= 0:
            return 0.0
        # The market figure is an annual flow ceiling, not an infinite shop.
        tonnes = min(tonnes, quote["market_available_tonnes_per_year"])
        cost = tonnes * quote["buy_per_tonne"]
        if tonnes <= 0 or cost > self.household.capital:
            return 0.0
        self.household.capital -= cost
        self._material_stock()[quote["material"]] += tonnes
        self.household._stock_throttle_sig = None
        return tonnes

    def sell_material_stock(self, material, tonnes):
        quote = self.material_trade_quote(material)
        tonnes = float(tonnes)
        if not quote or tonnes <= 0:
            return 0.0
        sold = min(tonnes, self.material_stock_t(quote["material"]))
        if sold <= 0:
            return 0.0
        self._material_stock()[quote["material"]] -= sold
        self.household.capital += sold * quote["sell_per_tonne"]
        self.household._stock_throttle_sig = None
        return sold

    def materials_report(self):
        """Stocks, annual flows, demand, and current trade values."""
        demand = self._demand_by_emp_key()
        materials = set(self._material_stock()) | {pair[0] for pair in self.MATERIAL_CHECKS.values()}
        materials |= {commodity for commodity in self.mine_capacity}
        rows = []
        for material in sorted(materials):
            quote = self.material_trade_quote(material)
            if not quote:
                continue
            annual_demand = sum(value for _tag, value in demand.get(material, ()))
            own = sum(self._own_material_supply(tag) for emp, tag in self._own_production_tags()
                      if emp == material)
            rows.append({**quote, "stock_on_hand_tonnes": self.material_stock_t(material),
                         "own_production_tonnes_per_year": own,
                         "current_demand_tonnes_per_year": annual_demand,
                         "stock_covers_years_at_current_demand": (
                             self.material_stock_t(material) / annual_demand
                             if annual_demand > 1e-9 else None)})
        return rows

    def _throttle_demand_split(self, demand):
        """`demand` (annual_material_demand()'s raw material-key Counter)
        split into two (emp_key, tag) -> tonnes/yr Counters: industrial
        (unchanged from before - still a flow demand that has to clear
        _own_material_supply + _material_market_tonnes, now plus stock) and
        lab (drawn from stock or bought outright, never throttled - see the
        class comment on LAB_SCALE_SUFFIX above).

        Deliberately NOT _demand_by_supply_tag(): that function is also read
        by material_price_factor() and everything built on it
        (material_market_factor, material_market_summary, wire_chain_report)
        for PRICING, which this pass does not touch - a gram of gold still
        nudges the price of gold exactly as much as it did before. Only the
        CAPACITY question (can this be done at all, or does it wait on a
        mine) changes here, so only resource_throttle() reads this. Fixes,
        in passing, the *_g unit bug the MATERIAL_CHECKS comment names:
        annual_material_demand() divides every raw key by 1000 assuming
        kilograms, which is correct for a *_kg key and 1000x too large for a
        *_g one (a bare quantity already in grams) - corrected here, once,
        at the one place that was ever misreading it.
        """
        industrial, lab = collections.Counter(), collections.Counter()
        for mat, amt in sorted(demand.items()):
            if not amt:
                continue
            tag = self._material_tag(mat)
            if mat.endswith(self.LAB_SCALE_SUFFIX) and not mat.endswith("_kg"):
                lab[tag] += amt / KILOGRAMS_PER_TONNE
            else:
                industrial[tag] += amt
        return industrial, lab

    def _own_production_tags(self):
        """(emp_key, tag) for every material you currently produce yourself,
        whether or not anything is demanding it THIS year.

        Without this, a mine sunk ahead of need - dug this year for a
        furnace that starts next year - never appears in `industrial` or
        `lab` at all (both are built from DEMAND, and there is none yet),
        so resource_throttle()'s own loop never visits its tag and its
        output is never banked: the exact evaporation DOCS_VS_ENGINE.md's
        #3 describes, just the zero-demand edge of it rather than the
        partially-used one the main loop already banks correctly.
        `self.mine_capacity` is keyed by emp_key already (core.py's own
        auto-mine opens `self.household.binding`, which IS an emp_key - see
        MATERIAL_CHECKS), so "mine:" + that key is exactly the tag
        _own_material_supply already knows how to read, curated commodity
        or not."""
        out = {(material, "mine:" + material) for material, capacity in self.mine_capacity.items() if capacity > 0}
        if self.household.forest_ha > 0:
            out.add(("charcoal", "forest1"))
            out.add(("charcoal", "forest4"))
        if self.household.nitre_bed_m2 > 0:
            out.add(("saltpetre", "nitre"))
        return out

