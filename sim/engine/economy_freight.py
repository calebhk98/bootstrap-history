"""What the market charges for a tracked material once scarcity, standing and distance are folded together, and what a
shortage of it tells the player.

material_price_factor() reads the demand grouping _cached_material_demand()/_cached_demand_by_tag() prepare, times the
freight markup the freight module publishes (`material_freight_factor`). Covers, in addition:
_demand_by_emp_key()/material_market_factor()/material_market_summary() (the price a project actually pays, and the
report of it); wire_chain_report() (the wire-specific worked example); build_nitre() (buying down a saltpetre
shortage, the one material this file's own MARKET_SHARE holds at zero because there is no open market for it); and
shortage_remedy() (what a player is told when something is binding).

FreightMixin is composed into EconomyMixin (economy.py) alongside the other economy sub-mixins. Carriage itself
(routes, carriers, dues) is the freight module (sim/freight/).

_cached_material_demand()/_cached_demand_by_tag() live here, not in economy_electricity.py: every caller of either
lives in THIS file. resource_throttle() in economy_electricity.py only WRITES the cache these two read
(self.household._material_demand_cache); it never calls either.
"""
import math

from . import commodities as _commod
from sim.constants import declare
from . import money_units
from . import purchase_rule
from .material_scarcity import scarcity_factor
from .units_prose import area_text, mass_per_area_text, mass_rate_text, money_text
from .shortage_sizing import mine_shortfall_after_sinking, mine_size_tonnes, nitre_bed_square_metres, nitre_deficit_tonnes
from sim.unit_conversions import KILOGRAMS_PER_TONNE

from sim.agents.api import edges


class FreightMixin:

    def _cached_material_demand(self):
        """annual_material_demand(), reusing resource_throttle()'s cache when
        there is one. See the comment there."""
        cached = getattr(self.household, "_material_demand_cache", None)
        return cached if cached is not None else self.annual_material_demand()

    def _cached_demand_by_tag(self):
        """_demand_by_supply_tag() of the current cached demand, computed
        once and reused for the rest of this tick.

        material_market_factor() weighs EVERY material key a project
        buys, general rather than 13 hand-named keys (see its own comment
        on why it must), which means material_price_factor()
        can be called several times for one project_cost() call, and
        project_cost() itself is already called once per candidate node
        `available` considers, every year (see project_cost's own comment
        on why nothing here can afford to be quadratic). Grouping the
        demand dict is the one part of that path that is not already O(1),
        so it is done once per tick and kept, keyed by the demand dict's
        identity so a new tick (a new annual_material_demand() result)
        invalidates it automatically rather than by a second flag that
        could drift out of step with the first.

        THE CACHE ENTRY HOLDS `demand` ITSELF, NOT JUST `id(demand)` - the
        same defence `sim/ui/proto/nodes.py`'s own id()-keyed cache
        documents and takes, for the identical reason. `id()` is only
        unique among objects that are still alive: annual_material_demand()
        returns a brand-new Counter every call, the OLD one is dropped as
        soon as resource_throttle() overwrites self.household._material_demand_cache
        with the next year's, and CPython can hand a freed small object's
        address to the very next same-sized allocation, so a later tick's
        Counter can land at the exact address an earlier tick's had.
        `cached[0] == id(demand)` would then read as true for two
        DIFFERENT ticks' demand, quietly replaying a stale grouping under
        a fresh year - the same shape of bug `done_in_order()`'s own
        docstring documents other instances of. Comparing `is
        demand` against a STRONG REFERENCE kept alongside the cached
        result, instead of comparing two bare integers, keeps that old
        Counter alive for as long as this cache entry might still be
        checked against it, so its address cannot be recycled into a false
        match while the entry is live - the collision is structurally
        impossible, not just unlikely, exactly as the nodes.py comment
        argues for the same shape of cache.
        """
        demand = self._cached_material_demand()
        cached = getattr(self.household, "_demand_by_tag_cache", None)
        if cached is not None and cached[0] is demand:
            return cached[1]
        by_tag = self._demand_by_supply_tag(demand)
        self.household._demand_by_tag_cache = (demand, by_tag)
        return by_tag

    def material_price_factor(self, emp_key):
        """What buying MORE of this tracked commodity costs beyond the flat
        catalogue price, from how hard current demand leans on the empire's
        market for it, versus how much of your own supply makes that market
        unnecessary, TIMES what transport.py's freight physics say it costs
        to haul it here from the nearest place it actually comes from (see
        material_freight_factor, a view of the freight module - 1.0, no change, for a material
        this civilization already produces somewhere in its own territory,
        or that the geography data has no location data for at all).

        FINDINGS_ROUND2 section R: MARKET_SHARE was a supply ceiling with no
        price response at all -- buying up to it cost the same per tonne as
        buying one kilogram -- and nothing made owning your own supply make
        the material CHEAPER, only available. Both halves are here: `need`
        and `_material_market_tonnes(emp_key)` are resource_throttle()'s own
        figures, so demand approaching the market ceiling raises the price on
        the same saturating curve labour market price_factor uses (negligible at a
        fifth of the ceiling, roughly double at the whole of it); owning
        enough of your own extraction (mine_capacity, forest_ha,
        nitre_bed_m2) to cover the need removes the premium rather than
        merely making the tonnes exist. This is the actual mechanism behind
        "the price of iron fell because supply rose": opening a mine lowers
        what iron costs YOU, specifically because you stop having to buy it
        at the margin.

        Groups demand the same way resource_throttle() now does
        (_demand_by_supply_tag): the same "checked each key alone" gap
        applied here too, understating the price pressure of a wire-heavy
        electrical age on copper by looking at copper_kg's share in
        isolation from copper_wire_kg's.

        GENERALISED: must fall back through _material_market_tonnes' own
        generic default for any commodity id not already sitting in the
        hand-written MARKET_SHARE dict above, rather than returning exactly
        1.0 immediately - an early return there is the actual mechanism by
        which most material keys would never move at all
        (COMMODITY_DYNAMISM.md measures 146 of 159 today). `market` falling
        back this way lets an arbitrary commodity id (curated or not) reach
        the same saturating curve the 9 curated ones use.
        """
        market = self._material_market_tonnes(emp_key)
        # demands grouped by emp_key once a tick (_demand_by_emp_key), not scanned from the whole dict per call
        demands = [(need, self._own_material_supply(tag)) for tag, need in self._demand_by_emp_key().get(emp_key, ())]
        worst = scarcity_factor(demands, market, self.MATERIAL_PRICE_DEMAND_SHARE_CAP,
                                self.MATERIAL_PRICE_PRESSURE_SCALE)
        return worst * self.view("material_freight_factor")[emp_key]

    MATERIAL_PRICE_DEMAND_SHARE_CAP = declare(
        "MATERIAL_PRICE_DEMAND_SHARE_CAP", 1.5, kind="temporary_heuristic",
        unit="dimensionless (demand / available supply, maximum)",
        source=None, confidence="D",
        why="Ceiling on how far demand-over-supply can push the price "
            "pressure curve below, so a wildly oversubscribed material "
            "does not blow the price multiplier up without bound. A "
            "defensive cap, not a market-clearing figure.")
    MATERIAL_PRICE_PRESSURE_SCALE = declare(
        "MATERIAL_PRICE_PRESSURE_SCALE", 0.9, kind="temporary_heuristic",
        unit="dimensionless coefficient on (demand share)^2", source=None,
        confidence="D",
        why="How hard buying near or above the market's available supply "
            "of a material pushes its price up - a quadratic curve, per "
            "this method's own docstring, 'negligible at a fifth of the "
            "ceiling, roughly double at the whole of it'. The quadratic "
            "SHAPE is a real modelling choice (price pressure should "
            "accelerate near scarcity); the coefficient is tuned to hit "
            "that 'roughly double' target, not derived from an observed "
            "price-response curve for any real material market.")

    def _demand_by_emp_key(self):
        """_cached_demand_by_tag(), grouped by emp_key - the grouping
        material_price_factor() actually wants. Cached the same tick-
        scoped way _cached_demand_by_tag() itself is, INCLUDING keeping a
        strong reference to `demand` in the cache entry rather than
        comparing bare `id()` integers - see that method's own comment for
        why a bare id() is not safe here (a freed Counter's address gets
        reused often enough that two different ticks compared equal by
        allocator luck alone, which is what made this pair of caches the
        fourth `done_in_order()`-class non-determinism bug, not a
        hypothetical one). A new tick produces a new annual_material_demand()
        result, which invalidates both caches together automatically."""
        demand = self._cached_material_demand()
        cached = getattr(self.household, "_demand_by_emp_key_cache", None)
        if cached is not None and cached[0] is demand:
            return cached[1]
        grouped = {}
        for (emp_key, tag), need in self._cached_demand_by_tag().items():
            grouped.setdefault(emp_key, []).append((tag, need))
        self.household._demand_by_emp_key_cache = (demand, grouped)
        return grouped

    def material_market_factor(self, node_id):
        """A project's price pressure from the materials it buys, weighted
        by how many kilograms of each -- the same weighting `_material_cost`
        already uses implicitly by summing kilogram costs.

        GENERALISED: every material key a node names now gets weighed in,
        not only the 13 MATERIAL_CHECKS ever listed by hand. Before this,
        a project buying nothing but glass, silk or aluminium got exactly
        1.0 back - not a small effect, no effect, because the `continue`
        below skipped every one of them (see COMMODITY_DYNAMISM.md: "it
        simply skips any material key not in MATERIAL_CHECKS"). Skipping
        was correct only in the sense that this file could not yet answer
        a price for those materials; now it can (_material_tag /
        material_price_factor's own generalisation), so it does.
        """
        mat = self.nodes[node_id].get("mat") or {}
        if not mat:
            return 1.0
        total_kg, weighted = 0.0, 0.0
        for material, quantity in sorted(mat.items()):
            emp_key = self._material_tag(material)[0]
            quantity = float(quantity)
            total_kg += quantity
            weighted += quantity * self.material_price_factor(emp_key)
        return (weighted / total_kg) if total_kg else 1.0

    def material_market_summary(self):
        """Every raw material currently carrying a real price premium
        because your own demand is leaning on what the market will sell -
        the generalised, aggregate version of material_price_factor(), the
        way goods_market_summary() already is for goods_market_factor().

        A PLAYER MUST SEE IT. Every material key's price responds to demand
        (see material_price_factor's own comment), so a player whose
        project costs rose because they are buying a lot of one thing, or
        fell because they sank their own mine in it, needs a place that
        says so in aggregate, not just a per-project `why`.
        """
        demand = self._cached_material_demand()
        if not demand:
            return None
        rows, seen = [], set()
        for mat in sorted(demand):
            if demand[mat] <= 0:
                continue
            emp_key = self._material_tag(mat)[0]
            if emp_key in seen:
                continue
            seen.add(emp_key)
            factor = self.material_price_factor(emp_key)
            if factor > 1.05:
                rows.append((emp_key, factor))
        if not rows:
            return None
        rows.sort(key=lambda entry: -entry[1])
        worst = rows[0]
        return ("%d material%s trading above book price because your own "
                "demand is leaning on what the market will sell: worst is "
                "%s at %d%% of book. Sinking your own mine or production "
                "capacity in it brings this back down, the same way it "
                "does for iron - 'quote mine %s' shows the price"
                % (len(rows), "" if len(rows) == 1 else "s",
                   worst[0], round(worst[1] * 100), worst[0]))

    def wire_chain_report(self, wire_t_per_yr):
        """Would THIS shortfall in copper wire actually be a copper shortage,
        or is the wire-drawing bench itself the bottleneck? Named against a
        real link in the tree (el2_three_wire_distribution_system alone
        wants 5 t of copper_wire_kg in one build; the whole electrical
        branch wants far more), because resource_throttle()'s `binding` can
        only ever say "copper" -- it has no notion that copper_wire_kg is
        COPPER, manufactured, not a second independent shortage.

        This is `commodities.py`'s `CommodityLedger.propagate_demand()`
        (COMMODITIES.md section 7, "the real test": a chained shortage
        attributed to whichever link actually broke), handed THIS
        civilisation's actual reachable copper -- resource_throttle()'s own
        `_own_material_supply("mine:copper") + _material_market_tonnes
        ("copper")` -- via `supply_override`, instead of
        commodities.json's own separate national estimate. The two
        happen to agree for Rome (both read from the same
        resources.json/economy.py MARKET_SHARE figures) but would not for a
        civilization with a different mineral_scale, which is exactly why
        overriding with the live number rather than trusting the static one
        matters.
        """
        supply_t = (self._own_material_supply("mine:copper")
                    + self._material_market_tonnes("copper"))
        ledger = _commod.CommodityLedger(supply_override={"copper": supply_t})
        return ledger.propagate_demand("copper_wire", max(0.0, float(wire_t_per_yr)))

    # Two denarii the square metre, which is the figure step() has always used
    # (spend / 2.0) written down where a quote can read it. A nitre bed is a
    # heap of dung, straw and ash turned for two years; it is cheap to lay and
    # slow to yield, which is exactly why nobody builds one until they are
    # already short.
    NITRE_LABOUR_HOURS_PER_M2 = declare(
        "NITRE_LABOUR_HOURS_PER_M2", 40.0, kind="temporary_heuristic",
        unit="labour hours per square metre", source=
        "The figure step() used before this was given a proper `quote` "
        "path (spend / 2.0), carried forward unchanged so buying a bed the "
        "new way costs exactly what the old automatic policy always paid.",
        confidence="D",
        why="Cost to lay one square metre of nitre bed. Not sourced to any "
            "attested saltpetre-works price; a carried-forward implementation "
            "constant.")
    NITRE_COST_PER_M2 = money_units.PricedInLabourHours("NITRE_LABOUR_HOURS_PER_M2")
    NITRE_YIELD_T_PER_M2 = declare(
        "NITRE_YIELD_T_PER_M2", 0.0008, kind="temporary_heuristic",
        unit="tonnes saltpetre/square metre/year", source=None,
        confidence="D",
        why="How much saltpetre one square metre of nitre bed yields a "
            "year. No attested nitre-bed yield figure backs this; it is "
            "sized only to be 'cheap to lay and slow to yield' (see the "
            "comment above), a qualitative target rather than a measured "
            "rate.")

    def build_nitre(self, square_metres):
        """Lay down nitre beds. Saltpetre is not dug and not grown; it is made.

        There was no way for a player to do this at all. The only thing that
        laid a bed was step(), which took five per cent of your capital every
        year you were short, said nothing, and did it whether or not you had
        turned the automatic policies off. A shortage the game will not let you
        act on is not a constraint, it is a wall.
        """
        square_metres = float(square_metres)
        if square_metres <= 0:
            return 0.0
        cost = square_metres * self.NITRE_COST_PER_M2 * self.price_index
        if not purchase_rule.can_pay(self, cost):
            return 0.0
        self.pay_edge(edges.EDGE_BUILDERS, cost, "nitre beds laid down")
        self.state.holdings.nitre_bed_m2 += square_metres
        return square_metres

    NITRE_SHORTAGE_SAFETY_BUFFER = declare(
        "NITRE_SHORTAGE_SAFETY_BUFFER", 1.20, kind="temporary_heuristic",
        unit="multiple on the bare tonnage deficit", source=None,
        confidence="D",
        why="Extra bed recommended over the bare measured deficit, so a "
            "tiny later change in the portfolio does not put the player "
            "straight back into shortage. Twenty per cent is a round, "
            "plausible safety margin, not derived from how much the "
            "portfolio typically moves.")

    def material_shortfall_t(self, material, by_tag=None):
        """Tonnes per year of `material` demand that neither your own
        workings nor the market cover: the one shortfall figure the capacity
        rows and the remedy text both use."""
        if by_tag is None:
            by_tag = self._demand_by_supply_tag(self.annual_material_demand())
        need, own = self.demand_and_own_supply_by_material(by_tag).get(material, (0.0, 0.0))
        if need <= 0.0:
            return 0.0
        return max(0.0, need - own - self._material_market_tonnes(material))

    def shortage_remedy(self, binding, shortfall_t=None):
        """One sentence on what would end this shortage, in things you can type."""
        return self.shortage_remedy_plan(binding, shortfall_t)["text"]

    def shortage_remedy_plan(self, binding, shortfall_t=None):
        """{"text", "commands"} for what would end this shortage.

        Must say what fixes it, not only the material and the percentage:
        naming a shortage without a remedy tells a player they are stuck
        without telling them it is fixable. `shortfall_t` is the tonnes per
        year still uncovered (material_shortfall_t() when omitted); every
        command's size comes from it, so the suggestion covers the shortfall
        the capacity screen reports.
        """
        if not binding:
            return {"text": "", "commands": []}
        if binding == "charcoal":
            need = max(0.0, self.annual_material_demand().get("charcoal_kg", 0.0)
                       / KILOGRAMS_PER_TONNE - self.state.holdings.forest_ha * self.CHARCOAL_PER_HA)
            hectares_needed = max(1.0, round(need / max(self.CHARCOAL_PER_HA, 1e-9)))
            return {"text": (
                "Charcoal is grown, not bought: about %s more of "
                "coppice would cover it ('buy forest %d', roughly %s"
                "). Ask the price first with 'quote forest %d'."
                % (area_text(hectares_needed, self, grouped=True), hectares_needed,
                   money_text(hectares_needed * self.FOREST_COST_PER_HA * self.price_index, self, grouped=True),
                   hectares_needed)),
                "commands": ["quote forest %d" % hectares_needed, "buy forest %d" % hectares_needed]}
        if shortfall_t is None:
            shortfall_t = self.material_shortfall_t(binding)
        if binding == "saltpetre":
            demand = self.annual_material_demand().get("saltpetre_kg", 0.0) / KILOGRAMS_PER_TONNE
            deficit = nitre_deficit_tonnes(
                shortfall_t, demand, self.state.holdings.nitre_bed_m2, self.NITRE_YIELD_T_PER_M2,
                self._material_market_tonnes("saltpetre"), self._material_stock().get("saltpetre", 0.0))
            # Twenty per cent headroom prevents a tiny change in the portfolio
            # putting the player straight back into shortage, without turning a
            # one-tonne deficit into the old fixed sixteen-tonne recommendation.
            square_meters = nitre_bed_square_metres(deficit, self.NITRE_SHORTAGE_SAFETY_BUFFER, self.NITRE_YIELD_T_PER_M2)
            return {"text": (
                "Saltpetre is made in nitre beds, not mined: you are about "
                "%s short. With a 20%% safety buffer, 'buy "
                "nitre %d' lays enough bed at %s "
                "per year (about %s)."
                % (mass_rate_text(deficit, self, digits=2, short=False), square_meters,
                   mass_per_area_text(self.NITRE_YIELD_T_PER_M2, self, digits=4),
                   money_text(square_meters * self.NITRE_COST_PER_M2
                              * self.price_index, self, grouped=True))),
                "commands": ["buy nitre %d" % square_meters]}
        if binding in self.MINE_OPEX_MATERIALS:
            sinking_tonnes, ready_year, shortfall_t = mine_shortfall_after_sinking(
                binding, shortfall_t, self.state.holdings.mine_tranches)
            if sinking_tonnes > 0.0:
                sinking_text = ("A working of %s is already being sunk, ready in %d. "
                                % (mass_rate_text(sinking_tonnes, self, grouped=True, short=False), ready_year))
                if shortfall_t < 1.0:
                    return {"text": sinking_text + "It covers the shortfall; wait for it.", "commands": []}
            else:
                sinking_text = ""
            tonnes_short = mine_size_tonnes(shortfall_t)
            return {"text": sinking_text + (
                "The market will not sell you enough %s, so you have to dig "
                "it: %s. 'quote mine %s %d' for the price, then 'buy mine "
                "%s %d'. A shaft takes a few years to come into production."
                % (binding,
                   ("you are about %s short"
                    % mass_rate_text(shortfall_t, self, grouped=True, short=False)) if shortfall_t >= 1.0
                   else "your own workings already cover the demand you have "
                        "today, so this is the market, not you"
                   if self.mine_capacity.get(binding, 0.0) > 0.0
                   else "you have no working of it yet, so sink one",
                   binding, tonnes_short, binding, tonnes_short)),
                "commands": ["quote mine %s %d" % (binding, tonnes_short),
                             "buy mine %s %d" % (binding, tonnes_short)],
                "kind": "dig_mine", "has_working": self.mine_capacity.get(binding, 0.0) > 0.0,
                "short_tonnes": shortfall_t}
        return {"text": (
            self.material_unsupplied_sentence(binding)
            or "Nothing you own supplies %s and the market is out of it; the work waits until something "
               "upstream of it is built." % binding), "commands": []}
