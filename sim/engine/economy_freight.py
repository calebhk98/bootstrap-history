"""Freight: moving a material from where it comes from to the buyer, and
what the market actually charges once scarcity, standing and distance
are all folded together.

Every method here answers what a tonne of a
tracked material actually costs to land at this household, given the
material's own scarcity (material_price_factor(), reading the demand
grouping _cached_material_demand()/_cached_demand_by_tag() prepare) and
the real, physical distance an ox-cart has to haul it from the nearest
region that has it (_land_freight_physical_inputs()/
_material_source_regions()/material_freight_distance_km()/
material_freight_cost_per_kg()/material_freight_factor() - see the
freight section below for sim/world/transport.py's own physics and
what this crossing deliberately does and does not cover). Covers, in
addition: material_price_factor()/_demand_by_emp_key()/
material_market_factor()/material_market_summary() (the price a
project actually pays, and the report of it); wire_chain_report()
(the wire-specific worked example); build_nitre() (buying down a
saltpetre shortage, the one material this file's own MARKET_SHARE
holds at zero because there is no open market for it); and
shortage_remedy() (what a player is told when something is binding).

FreightMixin is composed into EconomyMixin (economy.py) alongside the
other economy sub-mixins; see that file for the composition and for
the grouping evidence. CLAUDE.md's naming/heuristic-labelling
conventions apply here exactly as they do everywhere else in the
engine, regardless of which file a method lives in.

_cached_material_demand()/_cached_demand_by_tag() live here, not in
economy_electricity.py: every actual caller of either method -
material_price_factor() via _demand_by_emp_key(), and
material_market_summary() - lives in THIS file, and their own
docstrings say so explicitly (material_market_factor() calling
material_price_factor() "several times for one project_cost() call" is
exactly the freight-pricing hot path _cached_demand_by_tag()'s
docstring describes grouping the demand dict for). resource_throttle()
in economy_electricity.py only WRITES the cache these two read
(self.household._material_demand_cache); it never calls either. These
two methods are grouped by what actually calls them, not by where they
might look like they belong at a glance.

THE CLASS-LEVEL CACHE. _land_freight_physical_inputs() caches its
answer on the bare class object FreightMixin itself
(`getattr(FreightMixin, "...", None)` / `FreightMixin._foo = ...`),
not on self, because the ox/cart/dirt-track physical inputs it computes
never differ between one Sim instance and the next in the same
process - the same reasoning economy_materials.py's own CLASS-LEVEL
CACHE note gives for its three caches.

TRAP: the literal class name in that getattr/setattr MUST match
whatever class actually holds this method. If it is ever moved to a
different class or file, the cache key has to move with it - a
mismatch breaks the cache silently, invisible to import, to `validate`
and to compilation, surfacing only when a command that needs a
material price first runs and finds a cache that was never populated.
See economy_materials.py's own CLASS-LEVEL CACHE note for the fuller
account of this hazard.
"""
import math

from .data import haversine_km, WAGES
from . import commodities as _commod
from constants import declare
from sim.unit_conversions import KILOGRAMS_PER_TONNE

from world import transport as freight_physics


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
        same defence `sim/engine/proto/nodes.py`'s own id()-keyed cache
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

    # ---- freight: moving a material from where it comes from to you ------
    #
    # sim/world/transport.py derives what an ox team hauling a cart actually
    # costs per tonne-km from animal metabolism, rolling resistance and a
    # road surface - real physics, no price anywhere in it (see that
    # module's own NOT A MONEY FIGURE section for why). Until now nothing in
    # this engine ever called it: material_price_factor() below priced every
    # tracked material purely on SCARCITY (demand pressing on the empire's
    # market) and never asked how far the marginal tonne actually had to
    # travel to reach this household. CLAUDE.md SS3.1's own worked example -
    # a Roman soldier's cost must fall out of, among other things, transport,
    # not be looked up - is exactly this gap: Egypt's grain and Rome's grain
    # were the same book price here regardless of the thousand-odd
    # kilometres of open water between them.
    #
    # THE CROSSING. geography.json's own per-region `minerals` table (read
    # by mineral_scale()/_compute_mineral_scale() in geography.py to decide
    # how much of iron/coal/copper/lead/tin/silver/saltpetre you can BUY)
    # already says which of this game's 22 regions actually produce each of
    # those seven materials, with real latitude/longitude on every region.
    # This is the first place that same geography is also asked what buying
    # the material should COST: find the nearest region that has it, price
    # an ordinary ox-cart haul from there with transport.py's own per-
    # tonne-km figures, and fold the result into material_price_factor() as
    # a markup on the book price - see material_freight_factor()'s own
    # docstring for exactly why a markup, not an added denarii figure.
    #
    # WHY THIS MATERIAL SET AND NOT OTHERS. Extending this to gold, or to
    # commodities.json's own curated wool/cotton/coffee, was deliberately
    # left alone: geography.json's `minerals` table is the ONLY per-region
    # location data this engine carries at global (not just Roman-province)
    # coverage - commodities.json's "regions" field for those was written
    # Rome-centric (its `iron` entry alone lists only Roman provinces, none
    # of geography.json's other 16 regions, even though geography.json's own
    # `minerals` table credits China with more iron abundance than any
    # Roman province has) - using it for a non-Roman civilization would
    # invent a worse-than-nothing answer ("Han China must import all its
    # iron from across the world") from data that was never meant to
    # describe Han China at all. One clean, globally-consistent source beats
    # a wider crossing built on a source that only covers part of the map.
    #
    # WHAT THIS DELIBERATELY DOES NOT DO. It does not touch located_
    # materials (gutta percha, natural rubber, platinum) - geography.
    # material_cost_factor() already prices those from geography.json's own
    # reach-based multiplier (see project_cost()'s use of it above), and
    # that crossing is not flat or absent, only differently sourced (a
    # hand-set multiplier calibrated to Rome rather than transport.py's
    # physics); redoing it was out of this task's scope and out of
    # geography.py, which this file does not own. It does not model sea
    # freight at all, even though the whole reason this task exists is that
    # water is roughly an order of magnitude cheaper than land per tonne-
    # mile: transport.py has no seagoing-hull mode (its CALM_WATER surface
    # is an animal-towed canal or river barge, explicitly not a sailing
    # ship - see that module's own WHAT THIS MODULE DOES NOT DO), so a
    # region reachable only across open water is still charged the full
    # land-cart rate for the whole great-circle distance - a real
    # overstatement for a genuinely coastal shipment, and a named
    # limitation rather than a hidden one: inventing a sea-lane network and
    # a hull that does not exist in this project would be exactly the
    # "made-up distance... wearing a plausible face" CLAUDE.md SS3.1 warns
    # against. Left for the module that eventually gives transport.py a
    # real seagoing-hull mode. It also does not amortise the cart's own
    # capital cost or wear (transport.py's own vehicle_wear_fraction_per_
    # tonne_km) into the price: there is no market price for a cart
    # anywhere in prices.json to convert that fraction into denarii, so
    # this prices feed and driver time only, which UNDERSTATES the true
    # cost - a conservative simplification, named per CLAUDE.md SS3.4, not
    # a hidden one.

    LAND_FREIGHT_TEAM_SIZE = declare(
        "LAND_FREIGHT_TEAM_SIZE", 2.0, kind="engineering_estimate",
        unit="draught oxen",
        source="transport.py's own headline example throughout that "
               "module's docstring, __main__ block and test suite "
               "(draught_freight_physical_inputs(OX, 2, CART, ...)); reused "
               "here rather than a second, unrelated team size invented for "
               "this one crossing.",
        confidence="C",
        why="How many oxen pull the cart this crossing prices ordinary "
            "market freight with. Paired with DIRT_TRACK, not PAVED_ROAD or "
            "MUD, because transport.py's own docstring calls dirt track "
            "'the ordinary, unimproved-road case most freight in this "
            "period actually moved over' - the middle case, not either "
            "extreme.")

    # Which existing book price and wage this crossing reuses to turn
    # transport.py's physical quantities (feed kilograms, driver hours) into
    # denarii - see material_freight_cost_per_kg()'s own docstring for why
    # each was chosen and what it approximates. Plain strings, not declare()
    # (declare() is for numbers; these are which EXISTING number to read).
    FREIGHT_FEED_PRICE_MATERIAL = "wheat_kg"
    FREIGHT_DRIVER_WAGE_TRADE = "labourer"

    def _land_freight_physical_inputs(self):
        """Cached FreightPhysicalInputs for LAND_FREIGHT_TEAM_SIZE oxen
        pulling a two-wheeled cart on an ordinary dirt track - see the class
        comment above for why this specific team/vehicle/surface. Cached on
        the CLASS, the same pattern _material_prices() above already uses:
        none of animal, vehicle, surface or team size changes during a run,
        so there is nothing here to recompute per call."""
        cached = getattr(FreightMixin, "_land_freight_inputs_cache", None)
        if cached is None:
            cached = FreightMixin._land_freight_inputs_cache = (
                freight_physics.draught_freight_physical_inputs(
                    freight_physics.OX, int(self.LAND_FREIGHT_TEAM_SIZE),
                    freight_physics.CART, freight_physics.DIRT_TRACK))
        return cached

    def _material_source_regions(self, material):
        """Regions geography.json's own per-region `minerals` table credits
        with real abundance of `material` (iron, coal, copper, lead, tin,
        silver, saltpetre - mineral_scale()'s own tracked set; see
        geography.py's _compute_mineral_scale, which reads this exact same
        field for the QUANTITY question). Nothing here is invented for
        freight: it is the same geology this file already uses to decide
        how much of a material you can buy, now also asked what buying it
        should cost."""
        return [region_id for region_id, region in self._regions.items()
                if float((region.get("minerals") or {}).get(material, 0.0)) > 0.0]

    def material_freight_distance_km(self, material):
        """Great-circle kilometres from this civilization's own home
        centroid to the NEAREST region that actually produces `material` -
        the same "source from the easiest deposit, not a fixed one" logic
        material_reach() already uses for located materials, reused here
        rather than reinvented.

        Zero if any region this civilization already HOLDS produces the
        material at all: "home is home", exactly region_reach()'s own rule
        for a home region regardless of geometry, applied here to the same
        effect - a material you already mine somewhere in your own
        territory costs nothing extra to move WITHIN it, by this module's
        simplification.

        None if geography.json has no located-region data for `material` at
        all (everything outside the seven tracked minerals - see
        _material_source_regions). CLAUDE.md SS3.1 is explicit that an
        unknown distance is not licence to invent one, so this returns
        "unknown" rather than a guess, and material_freight_cost_per_kg()
        charges nothing rather than something imaginary when it sees that.

        Cached on the household: this civilization's geography does not
        change during a run, so the underlying haversine arithmetic only
        needs to happen once per material, not once per project per year -
        the same reasoning _material_stock()'s own lazy cache uses, next to
        it in this file."""
        cache = getattr(self.household, "_freight_distance_km_cache", None)
        if cache is None:
            cache = self.household._freight_distance_km_cache = {}
        if material in cache:
            return cache[material]
        regions = self._material_source_regions(material)
        if not regions:
            distance_km = None
        else:
            home_regions = set(self.civ.get("home_regions") or [])
            if home_regions & set(regions):
                distance_km = 0.0
            else:
                home_lat, home_lon = self._home_centroid
                distance_km = min(
                    haversine_km(home_lat, home_lon,
                                 self._regions[region_id]["lat"],
                                 self._regions[region_id]["lon"])
                    for region_id in regions)
        cache[material] = distance_km
        return distance_km

    def material_freight_cost_per_kg(self, material):
        """Denarii per kilogram to haul `material` from the nearest place it
        actually comes from to this household, by two-ox cart on an
        ordinary dirt track. Zero if material_freight_distance_km() cannot
        place the material at all, or places it at distance zero (already
        produced somewhere this civilization holds) - see that method's own
        docstring for both cases.

        THE MONEY CONVERSION transport.py deliberately leaves undone (see
        its own NOT A MONEY FIGURE section): feed_kg_per_tonne_km times a
        book price for animal feed, plus driver_hours_per_tonne_km times an
        unskilled wage, both read from this file's OWN existing book-price
        and wage tables rather than new ones invented for this crossing -
        the same numeraire (an hour of unskilled labour) sim/solve_prices.py
        already uses, per transport.py's own docstring pointing at it.

        FEED PRICE IS A LABELLED STAND-IN. transport.py's own FEED_ENERGY_
        DENSITY_KCAL_PER_KG declaration describes the ration it costs
        against as hay-heavy, and this project has no hay or fodder price
        anywhere in prices.json - FREIGHT_FEED_PRICE_MATERIAL (wheat_kg) is
        the closest book price that exists, and wheat is dearer per
        kilogram than real fodder, so this reads as a conservative
        (upper-bound), not measured, feed cost.

        VEHICLE WEAR/CAPITAL IS NOT INCLUDED. transport.py's own vehicle_
        wear_fraction_per_tonne_km has no market price to convert it into
        money - nothing in prices.json prices a cart - so this understates
        the true cost of the haul. Named here and in the class comment
        above, not hidden.
        """
        distance_km = self.material_freight_distance_km(material)
        if not distance_km:
            return 0.0
        inputs = self._land_freight_physical_inputs()
        feed_price_per_kg = self._book_price_per_kg(self.FREIGHT_FEED_PRICE_MATERIAL) or 0.0
        driver_wage_per_hour = WAGES.get(self.FREIGHT_DRIVER_WAGE_TRADE, 0.0)
        denarii_per_tonne_km = (inputs.feed_kg_per_tonne_km * feed_price_per_kg
                                 + inputs.driver_hours_per_tonne_km * driver_wage_per_hour)
        denarii_per_tonne = denarii_per_tonne_km * distance_km
        return denarii_per_tonne / KILOGRAMS_PER_TONNE

    def material_freight_factor(self, emp_key):
        """Multiplicative markup material_price_factor() applies on top of
        its scarcity curve, from what transport.py's freight physics say it
        costs to haul `emp_key` here - see material_freight_cost_per_kg()'s
        own docstring for the mechanism, and material_freight_distance_km()'s
        for why an unlocated material gets exactly 1.0, never a guess.

        A MARKUP ON THE BOOK PRICE (1.0 + freight / book_price), not a
        standalone added charge, because a markup is what project_cost()
        and material_trade_quote() both actually multiply against: node
        `_total_cost` and a material's per_kg are already the RAW book
        value, and every other adjustment this file stacks onto that value
        (civ_cost_factor(), material_cost_factor(), this function's own
        scarcity curve) is exactly this shape - a factor, not an addend -
        so freight has to enter the same way to compose correctly rather
        than silently double- or under-counting when several of these
        multiply together in project_cost().
        """
        book_price_per_kg = self._book_price_per_kg(emp_key)
        if not book_price_per_kg or book_price_per_kg <= 0:
            return 1.0
        freight_per_kg = self.material_freight_cost_per_kg(emp_key)
        if freight_per_kg <= 0:
            return 1.0
        return 1.0 + freight_per_kg / book_price_per_kg

    def material_price_factor(self, emp_key):
        """What buying MORE of this tracked commodity costs beyond the flat
        catalogue price, from how hard current demand leans on the empire's
        market for it, versus how much of your own supply makes that market
        unnecessary, TIMES what transport.py's freight physics say it costs
        to haul it here from the nearest place it actually comes from (see
        material_freight_factor() above - 1.0, no change, for a material
        this civilization already produces somewhere in its own territory,
        or that geography.json has no location data for at all).

        FINDINGS_ROUND2 section R: MARKET_SHARE was a supply ceiling with no
        price response at all -- buying up to it cost the same per tonne as
        buying one kilogram -- and nothing made owning your own supply make
        the material CHEAPER, only available. Both halves are here: `need`
        and `_material_market_tonnes(emp_key)` are resource_throttle()'s own
        figures, so demand approaching the market ceiling raises the price on
        the same saturating curve labour_price_factor uses (negligible at a
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
        worst = 1.0
        # GROUPED BY emp_key, ONCE A TICK, not scanned-and-filtered from the
        # whole by-tag dict on every one of THIS function's own calls. See
        # _demand_by_emp_key's comment: this is the same "called once per
        # material a project buys, once per candidate node, every year"
        # volume _cached_demand_by_tag() was already added to answer, one
        # level further in. Only max() is taken below, order-independent,
        # so - as with _cached_demand_by_tag's own dict - no sort is needed
        # for the result to be deterministic.
        for tag, need in self._demand_by_emp_key().get(emp_key, ()):
            if need <= 0:
                continue
            supply = max(1e-9, self._own_material_supply(tag) + market)
            share = min(self.MATERIAL_PRICE_DEMAND_SHARE_CAP, need / supply)
            worst = max(worst, 1.0 + self.MATERIAL_PRICE_PRESSURE_SCALE * share * share)
        return worst * self.material_freight_factor(emp_key)

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
    NITRE_COST_PER_M2 = declare(
        "NITRE_COST_PER_M2", 2.0, kind="temporary_heuristic",
        unit="denarii/square metre", source=
        "The figure step() used before this was given a proper `quote` "
        "path (spend / 2.0), carried forward unchanged so buying a bed the "
        "new way costs exactly what the old automatic policy always paid.",
        confidence="D",
        why="Cost to lay one square metre of nitre bed. Not sourced to any "
            "attested saltpetre-works price; a carried-forward implementation "
            "constant.")
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
        if cost > self.household.capital:
            return 0.0
        self.household.capital -= cost
        self.household.nitre_bed_m2 += square_metres
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

    def shortage_remedy(self, binding):
        """One sentence on what would end this shortage, in things you can type.

        Must say what fixes it, not only the material and the percentage:
        naming a shortage without a remedy tells a player they are stuck
        without telling them it is fixable. Every binding constraint in
        the model has exactly one answer; this is that answer, said out
        loud.
        """
        if not binding:
            return ""
        if binding == "charcoal":
            need = max(0.0, self.annual_material_demand().get("charcoal_kg", 0.0)
                       / KILOGRAMS_PER_TONNE - self.household.forest_ha * self.CHARCOAL_PER_HA)
            hectares_needed = max(1.0, round(need / max(self.CHARCOAL_PER_HA, 1e-9)))
            return ("Charcoal is grown, not bought: about %s more hectare%s of "
                    "coppice would cover it ('buy forest %d', roughly %s "
                    "denarii). Ask the price first with 'quote forest %d'."
                    % ("{:,.0f}".format(hectares_needed), "" if hectares_needed == 1 else "s", hectares_needed,
                       "{:,.0f}".format(hectares_needed * self.FOREST_COST_PER_HA * self.price_index),
                       hectares_needed))
        if binding == "saltpetre":
            demand = self.annual_material_demand().get("saltpetre_kg", 0.0) / KILOGRAMS_PER_TONNE
            available = (self.household.nitre_bed_m2 * self.NITRE_YIELD_T_PER_M2
                         + self._material_market_tonnes("saltpetre")
                         + self._material_stock().get("saltpetre", 0.0))
            deficit = max(0.0, demand - available)
            # Twenty per cent headroom prevents a tiny change in the portfolio
            # putting the player straight back into shortage, without turning a
            # one-tonne deficit into the old fixed sixteen-tonne recommendation.
            square_meters = max(100, int(math.ceil(
                deficit * self.NITRE_SHORTAGE_SAFETY_BUFFER
                / max(self.NITRE_YIELD_T_PER_M2, 1e-12) / 100.0)) * 100)
            return ("Saltpetre is made in nitre beds, not mined: you are about "
                    "%.2f tonnes/year short. With a 20%% safety buffer, 'buy "
                    "nitre %d' lays enough bed at %.4f tonnes per square metre "
                    "per year (about %s denarii)."
                    % (deficit, square_meters, self.NITRE_YIELD_T_PER_M2,
                       "{:,.0f}".format(square_meters * self.NITRE_COST_PER_M2
                                       * self.price_index)))
        if binding in self.MINE_CAPEX_PER_T_YR:
            dem = self.annual_material_demand()
            # SAME GROUPING resource_throttle() uses (_demand_by_supply_tag):
            # copper's shortfall can now come from copper_wire_kg or
            # wire_drawn_kg as much as from copper_kg itself (36 electrical
            # nodes draw drawn wire), and this sentence would otherwise name
            # a "you are X tonnes short" figure that silently excluded them.
            keys = {"coal": ("coal_kg",), "iron": ("iron_bar_kg", "iron_ore_kg"),
                    "copper": ("copper_kg", "copper_wire_kg", "wire_drawn_kg"),
                    "lead": ("lead_kg",), "tin": ("tin_kg",),
                    "silver": ("silver_kg",),
                    "gold": ("gold_kg",)}.get(binding, ())
            short = max(0.0, sum(dem.get(material_key, 0.0) for material_key in keys)
                        - self.mine_capacity.get(binding, 0.0))
            tonnes_short = max(1.0, round(short))
            return ("The market will not sell you enough %s, so you have to dig "
                    "it: %s. 'quote mine %s %d' for the price, then 'buy mine "
                    "%s %d'. A shaft takes a few years to come into production."
                    % (binding,
                       ("you are about %s tonnes a year short"
                        % "{:,.0f}".format(short)) if short >= 1.0
                       else "your own workings already cover the demand you have "
                            "today, so this is the market, not you",
                       binding, tonnes_short, binding, tonnes_short))
        return ("Nothing you own supplies %s and the market is out of it; the "
                "work waits until something upstream of it is built."
                % binding)
