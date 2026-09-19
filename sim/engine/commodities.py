"""Commodities as first-class things: iron, wool, coffee, copper, gold...

THIS MODULE IS NOW IMPORTED. `economy.py`'s `wire_chain_report()` calls
`CommodityLedger.propagate_demand()` -- the one mechanism here with no
analogue anywhere in the existing code (COMMODITIES.md section 7: a
recipe-chain demand walk that names WHICH link broke, not one flat
throttle) -- handed THIS CIVILISATION'S ACTUAL copper numbers via
`supply_override` below, instead of the independent national estimate
`commodities.json` would otherwise guess. `core.py` still does not import
this module and `Sim` still has no inventory (`Ledger`, the stock-tracking
class below, is exercised by the demo and the regression suite only): see
`data/world/COMMODITIES.md` section "What was decided" for why a full
swap of `resource_throttle()`/`MARKET_SHARE`/`material_price_factor()` for
this module's OWN (separately-sourced) price/national-output machinery was
rejected, and what was taken instead.

Read `COMMODITIES.md` first. It explains every field in `commodities.json`
and the reasoning behind every function below; the comments here point back
to it rather than repeating it.

Everything is a FLOW (tonnes per year), except `Ledger`, which is the one
piece of this file that tracks a STOCK ("how much you have" as a running
balance, as opposed to "how much you produce a year"). See COMMODITIES.md
section 8.
"""
import collections
import json
import math
import os
import random
from typing import (Any, cast, Dict, Iterable, List, Optional, Protocol,
                     TypedDict)

# Imported fully qualified (sim.unit_conversions, not a bare
# unit_conversions) rather than this package's usual bare sibling-import
# style, matching sim/engine/core.py's own documented choice to import
# sim/world/shared_constants.py the same way - see either module's own "HOW
# A CONSUMER USES ONE OF THESE" section for why one spelling everywhere
# avoids this file loading a second time under a second sys.modules key.
# Unlike core.py (which is only ever reached through an entry point that
# has already put the repository root on sys.path - simulator.py, cli.py,
# sim/tests/harness.py), this file is also imported directly by sim/
# demo_commodities.py, whose own sys.path setup adds sim/ and sim/engine/
# but not the repository root - so this file adds it itself, the same
# guarded, idempotent snippet core.py uses, rather than depending on every
# caller to have done it first. (`os` is already imported above; only `sys`
# is new here.)
import sys
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
from sim.unit_conversions import KILOGRAMS_PER_TONNE


class _RandomSource(Protocol):
    """What `price_with_noise`/`price_series` actually need from `rng`: a
    `gauss(mu, sigma)` method. Both a `random.Random` instance (what
    `price_series`'s own fallback, `random.Random(1)`, passes down) and the
    bare `random` MODULE (what `price_with_noise`'s own fallback, `rng or
    random`, uses when called directly) satisfy this - the module exposes
    the same functions as free functions bound to its own internal default
    instance. `random.Random` itself is not a supertype of the module, so
    this Protocol, not that class, is the true shared type of what these
    two methods accept."""
    def gauss(self, mu: float, sigma: float) -> float: ...

# A commodity record (commodities.json's own per-commodity block) and the
# tech-tree node records this class optionally reads `mat`/`up`/`build_yrs`/
# `yrs` off of. Both stay `Dict[str, Any]` rather than a TypedDict: this
# module is deliberately STANDALONE (no relative import of sim/engine/data.py
# or anywhere else - see the module docstring's own account of what imports
# it and what it does not import), so it never sees `data.py`'s own `Node`
# alias, and COMMODITIES.md documents a genuinely per-commodity-kind schema
# (a mined commodity's block and a manufactured one's do not share every
# field) the same way `sim/engine/data.py`'s own Node comment explains for
# tech-tree nodes - see that file for the fuller version of this reasoning.
JSONDict = Dict[str, Any]
Commodities = Dict[str, JSONDict]
NodeMap = Dict[str, JSONDict]


class TradePartners(TypedDict):
    """`trade_partners()`'s own return shape - fixed at exactly these four
    keys, spelled out in that method's own dict literal and nowhere else."""
    regions: List[str]
    cost_multiplier: Optional[float]
    reach_adjusted: bool
    note: str


class PropagationNode(TypedDict):
    """One node of the tree `propagate_demand()` returns - fixed at exactly
    the eight fields that method's own docstring documents by name, one
    bullet per key. `children` recurses (a manufactured commodity's own
    inputs, each itself one of these), which is why this class refers to
    its own name in a quoted forward reference rather than needing
    `from __future__ import annotations`."""
    commodity: str
    requested_t: float
    own_capacity_t: float
    upstream_capacity_t: float
    delivered_t: float
    met_fraction: float
    bottleneck: Optional[str]
    children: Dict[str, "PropagationNode"]


class CommodityExplanation(TypedDict):
    """`explain()`'s own return shape - "the brief's own bullet list...
    answered in one call," fixed at exactly the keys that method's own
    dict literal builds."""
    commodity: str
    you_produce_t_per_yr: float
    you_can_buy_t_per_yr: float
    country_produces_t_per_yr: float
    produced_by: List[JSONDict]
    consumed_by: Dict[str, Dict[str, float]]
    trade_partners: TradePartners
    monopoly_possible: bool
    demand_t_per_yr: float
    price_denarii_per_kg: float
    base_price_denarii_per_kg: Optional[float]


HERE = os.path.dirname(os.path.abspath(__file__))        # sim/engine
SIMDIR = os.path.dirname(HERE)                            # sim
ROOT = os.path.dirname(SIMDIR)                            # rome
COMMODITIES_FILE = os.path.join(ROOT, "data", "world", "commodities.json")


def load_commodities() -> Commodities:
    """The commodities table, keyed by commodity id. See commodities.json's
    own `_doc` for what each field means, and COMMODITIES.md for why."""
    return json.load(open(COMMODITIES_FILE))["commodities"]


class CommodityLedger:
    """Answers the brief's own bullet list for a set of commodities:

        how much you have, how much the country has, what produces it,
        what consumes it, who you can trade it for, market value for it
        (+/- fluctuation), and -- the hard case -- what happens to demand
        for a finished good when the raw material behind it runs short.

    Constructed from `commodities.json` (or a caller-supplied dict, for
    testing) and, optionally, the tech tree's node dict (id -> node) so it
    can read `mat` for consumption. Everything else (production multipliers,
    recipes, prices) lives in commodities.json and needs no tech tree at all.
    """

    def __init__(self, commodities: Optional[Commodities] = None,
                 nodes: Optional[NodeMap] = None,
                 supply_override: Optional[Dict[str, float]] = None) -> None:
        self.commodities: Commodities = commodities if commodities is not None else load_commodities()
        self.nodes: NodeMap = nodes or {}
        # A LIVE SIM KNOWS ITS OWN NUMBERS BETTER THAN THIS FILE DOES. Without
        # this, country_output() always answers from commodities.json's own
        # (separately-sourced) national_output_t_per_yr, which is a second
        # guess at a figure economy.py's MARKET_SHARE/mine_capacity/
        # mineral_scale already compute precisely for the seven materials
        # both files track -- exactly the drift section 10.1 of
        # COMMODITIES.md warns a real merge has to avoid. `supply_override`
        # is {commodity_id: tonnes_per_year}; when a commodity id is present
        # here, country_output() returns this number instead of deriving one,
        # so propagate_demand() reasons about THIS civilisation's actual
        # copper (say), not a flat Roman-wide estimate that cannot tell Rome
        # from the Norse. Absent for a commodity (wool, coffee, cotton...)
        # Sim does not track at all, so those fall back to commodities.json's
        # own figure exactly as before -- this is additive, not a takeover.
        self.supply_override: Dict[str, float] = supply_override or {}
        # Reverse index: a material key like "copper_kg" answers for at most
        # one commodity. Built once, not per call -- annual_material_demand()
        # in economy.py has the same shape of cache for the same reason.
        self._material_to_commodity: Dict[str, str] = {}
        for commodity_id, commodity in self.commodities.items():
            for material_key in commodity.get("material_keys", []):
                self._material_to_commodity[material_key] = commodity_id

    # ---- consumption: what a set of built/active nodes eats -------------
    #
    # This mirrors economy.py's annual_material_demand(): a node under
    # construction (`active_ids`) eats its whole bill of materials spread
    # over build_yrs; a node already standing with upkeep (`node_ids`, i.e.
    # `Sim.done`) eats HALF that again, every year, forever, because a
    # furnace does not stop burning charcoal once it is finished being
    # built. See economy.py's own comment on that halving for why.

    def material_kg_per_yr(self, node_ids: Iterable[str] = (),
                            active_ids: Iterable[str] = ()) -> Dict[str, float]:
        """Tonnes/yr of raw material KEYS (as they appear in `mat`, e.g.
        "copper_kg") demanded by these nodes. One level below commodities;
        commodity_demand() rolls this up."""
        # `Dict[str, float]`, not `collections.Counter[str]`: typeshed's own
        # `Counter` stub fixes VALUES at `int` (it models counting hashable
        # items), so a `Counter[str]` annotation would itself be false for
        # this accumulator, which only ever holds tonnes (`float`). The
        # object at runtime is still a real `collections.Counter` -
        # `Counter` IS a `dict` subclass, so nothing about `+=`, `.items()`
        # or any other call this file makes on it changes; `cast` is
        # type-checking only.
        material_tonnes: Dict[str, float] = cast(Dict[str, float], collections.Counter())
        for node_id in active_ids:
            node = self.nodes.get(node_id)
            if not node:
                continue
            span = max(1.0, float(node.get("build_yrs") or node.get("yrs") or 1.0))
            for material_key, quantity_kg in (node.get("mat") or {}).items():
                material_tonnes[material_key] += float(quantity_kg) / span / KILOGRAMS_PER_TONNE        # kg -> tonnes/yr
        for node_id in node_ids:
            node = self.nodes.get(node_id)
            if not node or float(node.get("up", 0) or 0) <= 0 or not node.get("mat"):
                continue
            span = max(1.0, float(node.get("build_yrs") or node.get("yrs") or 1.0))
            for material_key, quantity_kg in node["mat"].items():
                material_tonnes[material_key] += 0.5 * float(quantity_kg) / span / KILOGRAMS_PER_TONNE
        return material_tonnes

    def commodity_demand(self, node_ids: Iterable[str] = (),
                          active_ids: Iterable[str] = ()) -> Dict[str, float]:
        """Tonnes/yr of each tracked commodity DIRECTLY named in some node's
        `mat` dict. This is direct demand only: a node needing copper_wire_kg
        counts as demand for `copper_wire`, not (via the recipe) as demand
        for `copper` -- that indirect, chained demand is what
        propagate_demand() is for, deliberately kept separate. See
        COMMODITIES.md section 7."""
        commodity_totals: Dict[str, float] = cast(Dict[str, float], collections.Counter())  # see material_kg_per_yr's own comment on this annotation
        for material_key, tonnes in self.material_kg_per_yr(node_ids, active_ids).items():
            commodity_id = self._material_to_commodity.get(material_key)
            if commodity_id:
                commodity_totals[commodity_id] += tonnes
        return commodity_totals

    def commodity_consumers(self, commodity_id: str) -> Dict[str, Dict[str, float]]:
        """Every node id whose `mat` dict draws on this commodity, and the
        raw (un-annualised) kilograms it asks for. "What consumes it,"
        answered by name rather than by number."""
        keys = set(self.commodities[commodity_id].get("material_keys", []))
        consumers_by_node: Dict[str, Dict[str, float]] = {}
        for node_id, node in self.nodes.items():
            matched = {material_key: quantity_kg for material_key, quantity_kg in (node.get("mat") or {}).items() if material_key in keys}
            if matched:
                consumers_by_node[node_id] = matched
        return consumers_by_node

    # ---- production -------------------------------------------------------
    #
    # A commodity's `produced_by` list mixes two different kinds of entry,
    # and they combine differently:
    #   - ROUTE entries ("mine", "farm", "manufacture"): alternative ways to
    #     make the thing at all. Only the BEST built one counts (chosen_fuel()
    #     in economy.py is the same pattern: pick the best available option,
    #     don't stack every option you happen to also know).
    #   - MULTIPLIER entries ("multiplier"): a boost layered on top of
    #     whatever route you are using (a water pump, selective breeding).
    #     Every one you have built COMPOUNDS, because they are genuinely
    #     independent improvements, not alternatives to each other.
    # Gold's ~20x figure in the brief is METAL_PUMPING (3x) times CYANIDATION
    # (7x) = 21x, precisely because both are multiplier entries. See
    # commodities.json's gold.notes.

    def best_multiplier(self, commodity_id: str, built: Iterable[str]) -> float:
        """The output multiplier this commodity's production currently runs
        at, given a set of built node ids. 1.0 if nothing built changes it."""
        commodity = self.commodities[commodity_id]
        route_best = 1.0
        boost = 1.0
        built = set(built)
        for entry in commodity.get("produced_by", []):
            node = entry.get("node", "")
            is_built = node.startswith("mine:") or node in built
            if not is_built:
                continue
            mult = float(entry.get("output_multiplier", 1.0))
            if entry.get("kind") == "multiplier":
                boost *= mult
            else:
                route_best = max(route_best, mult)
        return route_best * boost

    def country_output(self, commodity_id: str, built: Iterable[str] = ()) -> float:
        """Tonnes/yr the WHOLE COUNTRY produces of this commodity: "how much
        the country has," as a flow (see COMMODITIES.md section 8 for why a
        flow and not a stockpile). For a manufactured commodity (one with a
        `recipe`) this is additionally capped by whatever its upstream
        commodities can actually supply nationally -- see
        _manufactured_output(). This is a rough NATIONAL aggregate; a
        specific player's own chain of demand should use propagate_demand()
        instead, which reasons about what YOU, specifically, can reach at
        each step rather than a flat national estimate."""
        if commodity_id in self.supply_override:
            return float(self.supply_override[commodity_id])
        commodity = self.commodities[commodity_id]
        if commodity.get("recipe"):
            return self._manufactured_output(commodity_id, built)
        base = commodity.get("national_output_t_per_yr")
        if base is None:
            base = commodity.get("import_capacity_t_per_yr", 0.0)
        return base * self.best_multiplier(commodity_id, built)

    def _manufacturing_capacity_t_per_yr(self, commodity_id: str, built: Iterable[str]) -> float:
        """The PLANT/LABOUR throughput ceiling alone, before any upstream
        material cap is applied. Used both by _manufactured_output() (for the
        national aggregate) and by propagate_demand() (for a player's own
        chain, where the upstream cap is computed by recursion instead, from
        real deliveries rather than a second national estimate -- see that
        function's own comment for why using country_output() there would
        double-count the upstream constraint)."""
        commodity = self.commodities[commodity_id]
        base = float(commodity.get("national_manufacturing_capacity_t_per_yr", 0.0))
        return base * self.best_multiplier(commodity_id, built)

    def _manufactured_output(self, commodity_id: str, built: Iterable[str]) -> float:
        commodity = self.commodities[commodity_id]
        cap = self._manufacturing_capacity_t_per_yr(commodity_id, built)
        recipe = commodity.get("recipe") or {}
        limits: List[float] = []
        for input_id, ratio in recipe.items():
            if ratio <= 0:
                continue
            limits.append(self.country_output(input_id, built) / ratio)
        return min([cap] + limits) if limits else cap

    def market_available(self, commodity_id: str, built: Iterable[str] = (),
                          standing_multiplier: float = 1.0) -> float:
        """Tonnes/yr an ORDINARY buyer (you, with no special standing) can
        actually purchase out of the country's output. `standing_multiplier`
        stands in for what economy.py's MARKET_SHARE escalation by patronage
        (patron_imperial, patron_senatorial, citizenship) does on a live Sim;
        this module has no Sim and no civilization, so it takes that factor
        as a plain number instead of re-deriving it from patronage flags.

        When `supply_override` names this commodity, THAT number already IS
        the reachable tonnage (a live Sim's own market-share/patronage/
        geology accounting already folded in), so it is returned as-is
        rather than having a SECOND share fraction applied on top of a
        figure that is not a raw national total to begin with."""
        if commodity_id in self.supply_override:
            return float(self.supply_override[commodity_id])
        commodity = self.commodities[commodity_id]
        share = float(commodity.get("market_share", 0.03))
        return self.country_output(commodity_id, built) * min(1.0, share * standing_multiplier)

    def player_supply(self, commodity_id: str, own_production_t: float = 0.0,
                       built: Iterable[str] = (),
                       standing_multiplier: float = 1.0) -> float:
        """What you can lay hands on this year: what you make yourself (a
        mine you sank, a farm you hold) plus what the market will sell you."""
        return own_production_t + self.market_available(commodity_id, built, standing_multiplier)

    # ---- price --------------------------------------------------------
    #
    # Symmetric, unlike economy.py's material_price_factor(), which is a
    # premium that can only rise. See COMMODITIES.md section 4.1 for why
    # that function cannot represent "automated looms make cloth cheaper,"
    # and section 4.2 for the worked example this enables.

    def price(self, commodity_id: str, demand_t: float, supply_t: float) -> float:
        """Denarii per kg, from how hard `demand_t` leans on `supply_t`,
        bounded by this commodity's own floor and ceiling (section 2's
        `price_floor_factor` / `price_ceiling_factor`)."""
        commodity = self.commodities[commodity_id]
        base = float(commodity.get("base_price_denarii_per_kg", 1.0))
        elastic = float(commodity.get("elasticity", 1.0))
        floor = float(commodity.get("price_floor_factor", 0.4))
        ceil_ = float(commodity.get("price_ceiling_factor", 6.0))
        ratio = demand_t / max(supply_t, 1e-9)
        factor = max(floor, min(ceil_, ratio ** elastic))
        return base * factor

    def price_with_noise(self, commodity_id: str, demand_t: float, supply_t: float,
                          rng: Optional[_RandomSource] = None, sigma: float = 0.08) -> float:
        """The same price, with a year's worth of ordinary market wobble on
        top: the "+/- fluctuation" the brief asks for, literally. See
        COMMODITIES.md section 4.3 for what this is (decoration on the
        fundamental) and 4.4 for what it deliberately is NOT (seasons,
        shocks)."""
        rng = rng or random
        commodity = self.commodities[commodity_id]
        base = float(commodity.get("base_price_denarii_per_kg", 1.0))
        floor = float(commodity.get("price_floor_factor", 0.4)) * base
        ceil_ = float(commodity.get("price_ceiling_factor", 6.0)) * base
        fundamental = self.price(commodity_id, demand_t, supply_t)
        noisy = fundamental * math.exp(rng.gauss(0.0, sigma))
        return max(floor, min(ceil_, noisy))

    def price_series(self, commodity_id: str, demand_t: float, supply_t: float,
                      years: int, rng: Optional[_RandomSource] = None,
                      sigma: float = 0.08) -> List[float]:
        """`years` of price_with_noise(), independently drawn each year
        around the same fundamental. A market under no shifting pressure
        still wobbles year to year rather than sitting on one number
        forever; a market under real pressure (rising demand_t, say) would
        need the caller to pass a different demand_t each year, which this
        function deliberately leaves to the caller rather than guessing a
        trend on its behalf."""
        rng = rng or random.Random(1)
        return [self.price_with_noise(commodity_id, demand_t, supply_t, rng, sigma)
                for _ in range(years)]

    # ---- monopoly -----------------------------------------------------

    def monopoly_price(self, commodity_id: str, marginal_cost: float,
                        alternative_price: Optional[float] = None,
                        max_margin: float = 6.0, min_margin: float = 1.1) -> float:
        """What a sole supplier charges: not the market-clearing price, but
        whatever a buyer with no alternative will pay, capped by the cost of
        their NEXT-BEST alternative (`alternative_price`), or by
        `max_margin` over your own cost if no alternative exists at all
        (`alternative_price=None`). See COMMODITIES.md section 5 for the
        coffee example this is built to answer, and why coffee itself is
        flagged anachronistic rather than deployed."""
        ceiling = alternative_price if alternative_price is not None else marginal_cost * max_margin
        return max(marginal_cost * min_margin, ceiling)

    # ---- trade ----------------------------------------------------------

    def trade_partners(self, commodity_id: str) -> TradePartners:
        """Regions this commodity can be had from, and the flat (Roman-
        calibrated) cost multiplier geography.json already carries for it.
        NOT adjusted for a specific civilization's reach -- that needs a
        live Sim's region_reach()/material_reach(), which this standalone
        module deliberately does not have. See COMMODITIES.md section 6."""
        commodity = self.commodities[commodity_id]
        return {
            "regions": list(commodity.get("regions", [])),
            "cost_multiplier": commodity.get("cost_multiplier"),
            "reach_adjusted": False,
            "note": ("Roman-calibrated multiplier from geography.json, not "
                     "adjusted for who is asking. A live Sim's material_reach() "
                     "would adjust this for a specific civilization; see "
                     "COMMODITIES.md section 6."),
        }

    # ---- demand propagation: the real test -------------------------------
    #
    # resource_throttle() in economy.py checks a FLAT list of material keys
    # against supply, each independently. It has no notion of one material
    # being manufactured from another, so it cannot say "wire-drawing
    # capacity is fine, copper is not, so wire is short despite nobody
    # lacking the ABILITY to draw it." This is the one mechanism in this
    # file with no analogue anywhere in the existing code. See
    # COMMODITIES.md section 7 for the full worked example.

    def propagate_demand(self, commodity_id: str, quantity_t: float,
                          built: Iterable[str] = (),
                          own_production: Optional[Dict[str, float]] = None,
                          standing_multiplier: float = 1.0) -> PropagationNode:
        """Ask for `quantity_t` tonnes/yr of `commodity_id`, and find out how
        much of it you can ACTUALLY get, walking the recipe graph down to raw
        materials and reporting back up which link broke.

        Returns a tree (dict) with one node per commodity touched:
            requested_t        what was asked of this commodity, this call
            own_capacity_t      this commodity's own ceiling (extraction/
                                 plant capacity you can reach), IGNORING what
                                 its own inputs can deliver
            upstream_capacity_t what its recipe inputs could actually
                                 deliver, translated back through the recipe
                                 ratio (inf for a commodity with no recipe)
            delivered_t          min(requested_t, own_capacity_t, upstream_capacity_t)
            met_fraction          delivered_t / requested_t
            bottleneck            this commodity's own id, IF its own
                                   capacity (not its inputs) is what is
                                   short -- so a copper shortage is reported
                                   against "copper," not against
                                   "copper_wire," even though copper_wire is
                                   also short. None if this commodity met the
                                   request or if the shortfall is inherited
                                   from upstream.
            children               {input_commodity_id: same structure}, for
                                    a manufactured commodity's recipe

        `own_capacity_t` deliberately does NOT call country_output() /
        market_available() for a manufactured commodity: those derive a
        NATIONAL estimate of the upstream cap from country_output() of the
        inputs, which would double-count the cap this function already
        derives from the actual recursive deliveries below. See
        _manufacturing_capacity_t_per_yr()'s own comment.
        """
        own_production = own_production or {}
        report: Dict[str, PropagationNode] = {}

        def own_capacity(cid: str) -> float:
            # A LEAF commodity named in supply_override skips this file's
            # own national-output guess entirely: economy.py's
            # wire_chain_report() passes THIS civilisation's actual copper
            # (mine_capacity plus its own market share at its own standing),
            # already reachable-tonnage, not a raw national total waiting for
            # a second share discount. See CommodityLedger's own comment.
            if cid in self.supply_override:
                return own_production.get(cid, 0.0) + float(self.supply_override[cid])
            commodity = self.commodities[cid]
            base: float
            if commodity.get("recipe"):
                base = self._manufacturing_capacity_t_per_yr(cid, built)
            else:
                national = commodity.get("national_output_t_per_yr")
                if national is None:
                    national = commodity.get("import_capacity_t_per_yr", 0.0)
                base = float(national) * self.best_multiplier(cid, built)
            share = float(commodity.get("market_share", 0.03))
            return own_production.get(cid, 0.0) + base * min(1.0, share * standing_multiplier)

        def visit(cid: str, requested_t: float) -> PropagationNode:
            commodity = self.commodities[cid]
            recipe = commodity.get("recipe") or {}
            children: Dict[str, PropagationNode] = {}
            upstream_cap_t = float("inf")
            for input_id, ratio in recipe.items():
                if ratio <= 0:
                    continue
                child = visit(input_id, requested_t * ratio)
                children[input_id] = child
                upstream_cap_t = min(upstream_cap_t, child["delivered_t"] / ratio)
            supply_t = own_capacity(cid)
            capacity_t = min(supply_t, upstream_cap_t)
            delivered_t = min(requested_t, capacity_t)
            met = (delivered_t / requested_t) if requested_t > 0 else 1.0
            bottleneck = cid if (supply_t < requested_t - 1e-9 and supply_t <= upstream_cap_t + 1e-9) else None
            node: PropagationNode = {
                "commodity": cid, "requested_t": requested_t, "own_capacity_t": supply_t,
                "upstream_capacity_t": upstream_cap_t, "delivered_t": delivered_t,
                "met_fraction": met, "bottleneck": bottleneck, "children": children,
            }
            report[cid] = node
            return node

        return visit(commodity_id, quantity_t)

    def bottlenecks(self, propagation_node: PropagationNode) -> List[str]:
        """Every commodity id propagate_demand() flagged as the ORIGIN of a
        shortfall (not merely a commodity that inherited one), in the order
        found."""
        out: List[str] = []

        def walk(n: PropagationNode) -> None:
            if n["bottleneck"]:
                out.append(n["bottleneck"])
            for child in n["children"].values():
                walk(child)

        walk(propagation_node)
        return out

    # ---- the one-call answer to the brief's own bullet list --------------

    def explain(self, commodity_id: str, built: Iterable[str] = (),
                own_production_t: float = 0.0, demand_t: Optional[float] = None,
                standing_multiplier: float = 1.0) -> CommodityExplanation:
        """"how much you have, how much the country has, what produces it,
        what consumes it, who can we trade it for, market value for it
        (+/- fluctuation)" -- in the brief's own words, answered in one call.

        `demand_t`, if not given, is read from commodity_demand() over
        `built` (direct demand only; see that method's own note about why
        this does not include chained demand from a recipe -- use
        propagate_demand() for that)."""
        commodity = self.commodities[commodity_id]
        if demand_t is None:
            demand_t = self.commodity_demand(node_ids=built).get(commodity_id, 0.0)
        supply_t = self.player_supply(commodity_id, own_production_t, built, standing_multiplier)
        return {
            "commodity": commodity_id,
            "you_produce_t_per_yr": own_production_t,
            "you_can_buy_t_per_yr": self.market_available(commodity_id, built, standing_multiplier),
            "country_produces_t_per_yr": self.country_output(commodity_id, built),
            "produced_by": commodity.get("produced_by", []),
            "consumed_by": self.commodity_consumers(commodity_id) if self.nodes else {},
            "trade_partners": self.trade_partners(commodity_id),
            "monopoly_possible": commodity.get("monopoly_possible", False),
            "demand_t_per_yr": demand_t,
            "price_denarii_per_kg": self.price(commodity_id, demand_t, supply_t),
            "base_price_denarii_per_kg": commodity.get("base_price_denarii_per_kg"),
        }


class Ledger:
    """A stock, not a flow: "how much you have," as a running balance.

    Nothing in the existing Sim tracks an inventory -- Sim nets annual flows
    against each other within the same year and keeps no stockpile across
    years. This is a minimal proof that the distinction is representable,
    for the demo; see COMMODITIES.md section 8 for why wiring this into Sim
    for real is second-pass work, not done here.
    """

    def __init__(self) -> None:
        # Dict[str, float], not Counter[str]: see material_kg_per_yr's own
        # comment above on why this file's own float-valued Counters are
        # annotated that way rather than with typeshed's int-only stub.
        self._stock: Dict[str, float] = cast(Dict[str, float], collections.Counter())

    def add(self, commodity_id: str, kg: float) -> None:
        self._stock[commodity_id] += kg

    def remove(self, commodity_id: str, kg: float) -> float:
        """Take up to `kg`; returns how much was actually available."""
        have = self._stock[commodity_id]
        taken = min(have, kg)
        self._stock[commodity_id] -= taken
        return taken

    def on_hand(self, commodity_id: str) -> float:
        return self._stock[commodity_id]
