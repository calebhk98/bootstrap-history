"""Electricity as a physical quantity, not a capability flag - plus the
worst-binding-constraint material throttle that folds it in.

Every method here answers how many kilowatts a
household can actually generate and actually needs, and, together with
the material stock/flow accounting economy_materials.py owns, how much
of a year's planned work that combination of watts and tonnes actually
supports. Covers: generation_breakdown_kw()/generation_capacity_kw()
(what you can generate, by source); _electricity_load_node_ids()/
_node_annual_tonnes()/_electricity_demand_kw() (what draws on it, and
how much); and resource_throttle()/project_resource_throttle() (the
single worst-binding-constraint fraction - electricity or any one
material - that a year's or one project's work actually clears).

ElectricityMixin is composed into EconomyMixin (economy.py) alongside
the other economy sub-mixins; see that file for the composition, the
grouping evidence, and for why this lives in a separate file. CLAUDE.md's
naming/heuristic-labelling conventions apply here the same as everywhere
else in the engine, regardless of which file a number or a comment lives
in.
"""
from .data import hard_pre
from sim.constants import declare
from sim.unit_conversions import KILOGRAMS_PER_TONNE


class ElectricityMixin:

    # ---- electricity: a physical quantity, not a capability flag ----------
    #
    # THE GAP THIS CLOSES. cap_power_electric, cap_power_grid, cap_power_steam
    # and cap_power_water are capability nodes whose own NAMES narrate a scale
    # ("kW scale", "MW scale", "portable, hundreds of kW", "tens of kW on one
    # shaft" - see tech_tree.json), and nothing turns that prose into a
    # tracked watt without this. Two consequences follow if it is not
    # tracked: a generation/demand/reserve-margin display cannot be given
    # (the `capacity` command's power section has nothing to show), and -
    # worse - electrolytic aluminium, the electric arc furnace, zone
    # refining and a zinc smelter's own ancillary load all list `power_grid`
    # in their `pre` and would be charged nothing whatsoever for the
    # electricity that prerequisite implies they need. The aluminium/
    # rubber/etc. MATERIAL gating audit (MATERIAL_GATING.md) closes exactly
    # this shape of hole for MATERIALS; this closes it for the one input
    # that check does not see, because a material key has always been
    # something `mat` can name and a watt never was.
    #
    # THE MODEL. Two sides, matched the way every other tracked commodity in
    # this file is: GENERATION (a rated kW contributed by every prime-mover
    # and generator node you have actually finished building - see
    # generation_breakdown_kw) and DEMAND (a kW drawn by every operating or
    # under-construction concern whose own prerequisite closure requires
    # cap_power_electric, cap_power_grid, or the literal power_grid node -
    # see _electricity_demand_kw). resource_throttle() below folds the two
    # together into the SAME worst-binding-constraint arithmetic iron and
    # copper already use, rather than inventing a second scarcity vocabulary:
    # electricity can become `self.household.binding`, appears in `self.household.shortages` the
    # same way "iron" or "saltpetre" already do, and reports itself through
    # the same `throttle_binding`/`why` machinery. It does NOT go through the
    # stock-banking half of that function (see the comment where it is
    # folded in, below) because a rated kilowatt is a RATE, not an inventory:
    # unlike a mine's unworked ore, a kilowatt of unused generating capacity
    # this year does not stockpile for next year, and unlike every other
    # tracked commodity, there is no market anywhere in this model that will
    # sell you a shortfall of electricity - you either generated it or you
    # did not.
    #
    # WHERE THE NUMBERS CAME FROM, AND WHERE THEY ARE A JUDGEMENT CALL.
    #
    # GENERATION: the tree's OWN cap_power_* names/notes state an order of
    # magnitude, never an exact figure - "tens of kW", "kW scale", "hundreds
    # of kW", "MW scale" (see POWER_ANCHOR_KW immediately below). Turning
    # "tens" into 30, "hundreds" into 300 and "MW scale" into 3,000 is a
    # judgement call, made explicitly here rather than smuggled into a bare
    # number with no comment: each is the geometric-ish midpoint of the
    # decade the tree's own prose names. cap_power_electric's "kW scale" is
    # deliberately smaller than cap_power_water's "tens of kW", not a
    # contradiction: cap_power_electric's own note is "one dynamo on the
    # millpond shaft you already built... enough for arc lights,
    # electroplating, a laboratory" - a small slice of an existing shaft's
    # mechanical output diverted through a dynamo, not the shaft's whole
    # output turned electrical. Every node in GENERATION_LOCAL_NODES/
    # GENERATION_GRID_NODES/TRANSMISSION_NODES/MECHANICAL_PRIME_MOVER_CHAINS
    # was found by grepping the whole tree for every node whose id, name or
    # `cat` names a prime mover or an electrical generator (water_prime,
    # steam_prime, electrical_gen, wind_prime, power_station, grid_operations,
    # plus the dynamo/alternator family by name) - a closed, enumerable set
    # today the way the tech tree's material keys (159 today) MATERIAL_CHECKS
    # started against never was, so curating it by hand here costs the same one line per
    # future generation node that MATERIAL_CHECKS already costs per future
    # tracked commodity. Deliberately EXCLUDED from that set: dynamo/
    # alternator WINDING VARIANTS (el2_dynamo_series/shunt/compound_wound,
    # el2_alternator_rotating_field) and small auxiliary machines (en_exciter,
    # en_three_phase_gen, en_rotary_converter) - these refine or condition an
    # existing generator's output (regulation, phase, AC/DC conversion) and
    # do not represent a second, additional installation; counting them
    # would double the same generator's rating for every regulation upgrade
    # bought on top of it. Also excluded, for the mirror-image reason: the
    # water-wheel/turbine and steam-turbine FAMILIES are each a linear
    # upgrade chain at one site (undershot -> overshot -> breastshot ->
    # poncelet -> fourneyron -> francis -> kaplan; impulse -> curtis ->
    # reaction), not seven separate wheels - MECHANICAL_PRIME_MOVER_CHAINS
    # reports whichever is the BEST one you have finished, not their sum,
    # and (see generation_breakdown_kw's own note) is informational only:
    # it is not summed into electrical generation at all, because a bare
    # water wheel or steam turbine with no dynamo or alternator attached
    # turns nothing electrical, and that gate is already the existing `pre`
    # graph's job (dynamo's own prerequisites already include
    # water_power_scale; en_alternator's already include cap_power_steam).
    #
    # DEMAND: only two nodes get an individually-researched, real-world-cited
    # specific energy (ELECTRICAL_PROCESSES) - Hall-Heroult aluminium
    # electrolysis (13-17 kWh per kg of aluminium, historical/modern range;
    # applied to electrolysis_industrial's own bauxite_kg draw at a 4.5:1
    # bauxite-to-aluminium mass ratio, Bayer process) and a submerged-arc
    # ferroalloy/carbide furnace (several thousand kWh per tonne of product
    # is the real range; applied to arc_furnace_ferroalloys' own iron_ore_kg
    # draw at a simplifying 1:1 ore-to-product mass assumption, since the
    # tree carries no separate output-mass field for this node - flagged
    # here as the one approximation in this pair). Everything else this
    # file found gated on cap_power_electric/cap_power_grid/power_grid in
    # its own prerequisite closure (81 further nodes: workshop electronics,
    # vacuum-tube and radio equipment, welding, battery charging, the
    # semiconductor line itself, and zinc_industry_scale's own ancillary
    # load, whose actual smelting energy is charcoal/coal-fired per its own
    # note, not electrical - see GENERIC_ELECTRIC_LOAD_KW) gets ONE shared,
    # flat, modest figure rather than a hand-picked number apiece - the same
    # curate-the-important-cases-and-generalise-the-rest shape
    # _generic_market_share/_generic_national_output_t_per_yr already use
    # for materials, chosen so this file does not re-acquire the "13 hand-
    # named commodities out of 162" gap COMMODITY_DYNAMISM.md measured (159
    # material keys today - see economy_materials.py's own GENERALISING
    # BEYOND THE 9 HAND-NAMED COMMODITIES comment for the re-count), in a
    # new unit.
    #
    # NOTES TOO VAGUE TO USE, NAMED HONESTLY: no node anywhere in the tree
    # carries a wattage or an output-mass figure for zone_refining, mfg_
    # anodising, met_electro_refining, or any of the mt2_*_electrolysis/
    # electrowinning nodes - their own `mat` dicts name reagents (graphite,
    # sulfuric acid, sulfur, lime) at bench-to-pilot quantities, not a
    # product mass a specific-energy figure could be applied to
    # defensibly. Each falls back to GENERIC_ELECTRIC_LOAD_KW rather than a
    # number invented to look more precise than the data supports.
    HOURS_PER_YEAR = declare(
        "HOURS_PER_YEAR", 8760.0, kind="physical_constant",
        unit="hours/year (365-day year)", source="365 days x 24 hours.",
        confidence="A",
        why="Converts an average continuous kilowatt draw into an annual "
            "energy total (and back), the same role HOURS_PER_DAY plays in "
            "sim/world/agriculture.py. Deliberately the plain 365-day "
            "figure, not 365.25: this file has no use for leap-year "
            "precision at kilowatt-scale estimates.")

    _POWER_ANCHOR_WHY = (
        "Turns the tech tree's own prose description of a generation "
        "node's scale ('tens of kW', 'kW scale', 'hundreds of kW', 'MW "
        "scale' - see tech_tree.json) into an actual kilowatt figure "
        "resource_throttle() can compare demand against. Each is the "
        "geometric-ish midpoint of the decade the tree's own note names - "
        "a judgement call made explicitly, per the class comment above, "
        "rather than a specific rated capacity for any specific machine.")
    POWER_ANCHOR_KW_WATER = declare(
        "POWER_ANCHOR_KW_WATER", 30.0, kind="temporary_heuristic",
        unit="kW", source="tech_tree.json note: 'tens of kW on one shaft'.",
        confidence="D", why=_POWER_ANCHOR_WHY)
    POWER_ANCHOR_KW_ELECTRIC = declare(
        "POWER_ANCHOR_KW_ELECTRIC", 10.0, kind="temporary_heuristic",
        unit="kW", source="tech_tree.json note: 'kW scale' - smaller "
               "than cap_power_water's own because this node is one "
               "dynamo diverting a slice of an existing shaft's output, "
               "not the shaft's whole output turned electrical (see "
               "the class comment above).",
        confidence="D", why=_POWER_ANCHOR_WHY)
    POWER_ANCHOR_KW_STEAM = declare(
        "POWER_ANCHOR_KW_STEAM", 300.0, kind="temporary_heuristic",
        unit="kW", source="tech_tree.json note: 'portable, hundreds of kW'.",
        confidence="D", why=_POWER_ANCHOR_WHY)
    POWER_ANCHOR_KW_GRID = declare(
        "POWER_ANCHOR_KW_GRID", 3000.0, kind="temporary_heuristic",
        unit="kW", source="tech_tree.json note: 'MW scale'.",
        confidence="D", why=_POWER_ANCHOR_WHY)
    POWER_ANCHOR_KW = {
        'cap_power_water': POWER_ANCHOR_KW_WATER,
        'cap_power_electric': POWER_ANCHOR_KW_ELECTRIC,
        'cap_power_steam': POWER_ANCHOR_KW_STEAM,
        'cap_power_grid': POWER_ANCHOR_KW_GRID,
    }

    # Standalone local generators: each an actual, distinct machine, so
    # multiple different ones (a dynamo AND a wind generator) add.
    GENERATION_LOCAL_NODES = {
        "dynamo": "cap_power_electric",
        "en_wind_electric": "cap_power_electric",
        "en_alternator": "cap_power_steam",
    }
    # Grid-scale generating STATIONS (power_station category) - distinct
    # from power_grid itself, which is transmission/distribution only (its
    # own `pre` is wires, substations, transformers and steel; no generator
    # anywhere in it - confirmed by reading it).
    GENERATION_GRID_NODES = {
        "en_hydroelectric_station": "cap_power_grid",
        "en_thermal_station": "cap_power_grid",
    }
    TRANSMISSION_NODES = {
        "power_grid": "cap_power_grid",
    }
    # Mechanical prime movers, informational only (see the class comment):
    # each list is one upgrade CHAIN at a single site, so only the best
    # member you have finished counts, never the sum of the chain.
    MECHANICAL_PRIME_MOVER_CHAINS = {
        "water": (("en_undershot_wheel", "en_overshot_wheel", "en_breastshot_wheel",
                   "en_poncelet_wheel", "en_fourneyron_turbine", "en_francis_turbine",
                   "en_kaplan_turbine", "en_pelton_wheel"), "cap_power_water"),
        "steam": (("en_steam_turbine_impulse", "en_steam_turbine_curtis",
                   "en_steam_turbine_reaction"), "cap_power_steam"),
    }

    def generation_breakdown_kw(self):
        """What this civilisation can actually generate and transmit, in
        real kilowatts, right now - local (workshop-scale) generation, grid-
        scale generating stations, grid transmission capacity, and the best
        mechanical prime mover on each site (informational; see the class
        comment above for why mechanical power is never summed into
        electrical generation directly). `total_kw` - local plus grid - is
        what resource_throttle() checks electrical demand against.
        """
        done = self.state.projects.done
        local_kw = sum(self.POWER_ANCHOR_KW[tier]
                       for nid, tier in sorted(self.GENERATION_LOCAL_NODES.items())
                       if nid in done)
        grid_kw = sum(self.POWER_ANCHOR_KW[tier]
                      for nid, tier in sorted(self.GENERATION_GRID_NODES.items())
                      if nid in done)
        transmission_kw = sum(self.POWER_ANCHOR_KW[tier]
                              for nid, tier in sorted(self.TRANSMISSION_NODES.items())
                              if nid in done)
        mechanical_kw = {}
        for fam, (chain, tier) in sorted(self.MECHANICAL_PRIME_MOVER_CHAINS.items()):
            mechanical_kw[fam] = (self.POWER_ANCHOR_KW[tier]
                                  if any(nid in done for nid in chain) else 0.0)
        sources_kw = {}
        for node_id in sorted(done):
            generator = self.nodes.get(node_id, {}).get("electricity_generation") or {}
            if generator:
                source = generator.get("source")
                capacity_kw = float(generator.get("capacity_kw", 0.0))
                if not source or capacity_kw < 0:
                    raise ValueError("%s has invalid electricity_generation data" % node_id)
                sources_kw[source] = sources_kw.get(source, 0.0) + capacity_kw
        mod_generation_kw = sum(sources_kw.values())
        return {
            "local_kw": local_kw,
            "grid_kw": grid_kw,
            "transmission_kw": transmission_kw,
            "mechanical_kw": mechanical_kw,
            "sources_kw": sources_kw,
            "total_kw": local_kw + grid_kw + mod_generation_kw,
        }

    def generation_capacity_kw(self):
        """The one number resource_throttle() needs: total_kw, cached."""
        return self.generation_breakdown_kw()["total_kw"]

    # Hall-Heroult aluminium electrolysis: 13-17 kWh/kg aluminium is the
    # historical-to-modern range; 15 (the midpoint) is used. Bayer process
    # bauxite yield is roughly 4-5 t bauxite per t aluminium (ore grade and
    # process losses vary); 4.5 (the midpoint) is used, so the constant
    # below is kWh per kg of BAUXITE (electrolysis_industrial's own `mat`
    # key), not per kg of aluminium the tree never states a mass for.
    ALUMINIUM_KWH_PER_KG = declare(
        "ALUMINIUM_KWH_PER_KG", 15.0, kind="engineering_estimate",
        unit="kWh/kg aluminium",
        source="Hall-Heroult aluminium electrolysis: 13-17 kWh/kg is the "
               "historical-to-modern range; taken at the midpoint.",
        confidence="B",
        why="Specific energy of electrolytic aluminium production, applied "
            "to electrolysis_industrial's own bauxite draw via "
            "BAUXITE_PER_ALUMINIUM_KG to give electrical demand per kg of "
            "bauxite, the tree's own material key for this node.")
    BAUXITE_PER_ALUMINIUM_KG = declare(
        "BAUXITE_PER_ALUMINIUM_KG", 4.5, kind="engineering_estimate",
        unit="kg bauxite per kg aluminium",
        source="Bayer process bauxite yield is roughly 4-5 t bauxite per t "
               "aluminium, varying with ore grade and process losses; "
               "taken at the midpoint.",
        confidence="B",
        why="Converts aluminium's own specific energy (ALUMINIUM_KWH_PER_KG) "
            "into energy per kg of BAUXITE, since electrolysis_industrial's "
            "own `mat` dict draws bauxite_kg, not an aluminium mass the "
            "tree never states.")
    # Submerged-arc ferroalloy/carbide furnaces: several thousand kWh per
    # tonne of product is the real range for this FAMILY of processes
    # (ferrosilicon, ferrochrome, calcium carbide - all listed in
    # arc_furnace_ferroalloys' own note) - far higher than plain scrap-steel
    # EAF remelting (a few hundred kWh/t), because this node is specifically
    # the carbide/ferroalloy family, not steel remelting. Applied to the
    # node's own iron_ore_kg draw at a simplifying 1:1 ore-to-product mass
    # assumption - the one approximation in this pair, disclosed because the
    # tree carries no separate output-mass field for this node.
    FERROALLOY_KWH_PER_KG_ORE = declare(
        "FERROALLOY_KWH_PER_KG_ORE", 5.0, kind="engineering_estimate",
        unit="kWh/kg ore (1:1 ore-to-product mass assumed)",
        source="Submerged-arc ferroalloy/carbide furnaces run several "
               "thousand kWh per tonne of product for this process FAMILY "
               "(ferrosilicon, ferrochrome, calcium carbide); several "
               "thousand kWh/t is roughly several kWh/kg.",
        confidence="C",
        why="Specific energy for arc_furnace_ferroalloys, applied to its "
            "own iron_ore_kg draw at a simplifying 1:1 ore-to-product mass "
            "assumption - the disclosed approximation in this pair, since "
            "the tree carries no separate output-mass field for this node.")
    # Anything else gated on cap_power_electric/cap_power_grid/power_grid
    # that this file cannot characterise individually - a modest generic
    # workshop load, the same order of magnitude as cap_power_electric's own
    # anchor and a full order of magnitude under the two curated heavy loads
    # above, so an uncharacterised node's demand is present but never
    # dominant.
    GENERIC_ELECTRIC_LOAD_KW = declare(
        "GENERIC_ELECTRIC_LOAD_KW", 15.0, kind="temporary_heuristic",
        unit="kW", source=None, confidence="D",
        why="Flat electrical demand assumed for any node gated on "
            "generated electricity that this file cannot characterise "
            "individually (see ELECTRICAL_PROCESSES for the two that are). "
            "Deliberately modest - the same order as cap_power_electric's "
            "own anchor, a full order of magnitude under the two curated "
            "heavy loads - so an uncharacterised node's demand is present "
            "but never dominant. Not measured for any specific process.")

    ELECTRICAL_PROCESSES = {
        "electrolysis_industrial": ("bauxite_kg",
                                    ALUMINIUM_KWH_PER_KG / BAUXITE_PER_ALUMINIUM_KG),
        "arc_furnace_ferroalloys": ("iron_ore_kg", FERROALLOY_KWH_PER_KG_ORE),
    }

    # cap_power_electric/cap_power_grid are the CAPABILITY flags; power_grid
    # is the literal transmission node some tier-5 process nodes name in
    # `pre` directly without ever naming the capability flag too (arc_
    # furnace_ferroalloys, zinc_industry_scale - see the class comment).
    # All three are treated as "this node needs generated electricity",
    # because that is what each one actually means physically, regardless
    # of which of the three a given node's author happened to write down.
    _ELECTRICITY_GATE_TOKENS = frozenset(
        {"cap_power_electric", "cap_power_grid", "power_grid"})

    def _electricity_load_node_ids(self):
        """Every node id whose own prerequisite closure needs generated
        electricity - computed once, from self.nodes (the static tree, not
        this run's state), and cached for the Sim's whole life; nothing
        here changes as a run progresses. A single memoised recursion over
        hard_pre(), not one closure() walk per candidate node: this file's
        own MATERIAL_GATING precedent (a cycle-safe visited-set walk of the
        whole tree once) is the reused shape, not the per-node closure()
        calls _power_status/_material_capacity_rows make elsewhere for a
        handful of rows at a time.
        """
        cached = getattr(self, "_electricity_load_ids_cache", None)
        if cached is not None:
            return cached
        tokens = self._ELECTRICITY_GATE_TOKENS
        memo = {}

        def gated(node_id, on_stack):
            if node_id in memo:
                return memo[node_id]
            if node_id in tokens:
                memo[node_id] = True
                return True
            if node_id in on_stack or node_id not in self.nodes:
                # Cycle guard: hard_pre's own single-option req_any edges are
                # acyclic tree-wide (see closure()'s own comment), but this
                # walk is defensive of that invariant rather than trusting
                # it silently - an unexpected cycle answers "not gated"
                # rather than recursing forever.
                return False
            on_stack.add(node_id)
            result = any(gated(parent_id, on_stack) for parent_id in hard_pre(self.nodes, node_id))
            on_stack.discard(node_id)
            memo[node_id] = result
            return result

        # UPKEEP IS NOT THE TEST OF WHETHER WORK DRAWS POWER. This required
        # up > 0 as a proxy for "a real installation rather than a technique",
        # which was reasonable on its own and wrong in combination with an
        # earlier decision: upkeep was deliberately stripped from 1,096
        # technique nodes, because a technique is not a going concern you
        # maintain. The two together hid 118 electricity-gated nodes that draw
        # material - MORE than the 111 that were kept - including
        # zone_refining, single_crystal and mfg_anodising, which are about as
        # electrical as this tree gets and sit squarely on the road to the
        # goal. A zone refiner melting a germanium boat by induction is
        # consuming kilowatts whether or not the tree charges it rent.
        #
        # The upkeep test survives where it is genuinely the right question -
        # see the caller, which applies it to the STANDING draw of something
        # already built and running. Work in hand draws power because the work
        # is happening, not because it pays rent.
        ids = {node_id for node_id, node in self.nodes.items()
              if node.get("mat") and gated(node_id, set())}
        self._electricity_load_ids_cache = ids
        return ids

    def _node_annual_tonnes(self, node_id, mat_key):
        """Tonnes/yr of mat_key ONE node draws, using the exact per-node
        annualisation annual_material_demand() applies when it sums this
        across every node in one pass - factored out so the curated
        electrical processes below can ask for a single node's own draw
        (electrolysis_industrial's bauxite, not the tree-wide bauxite total
        - iron_ore_kg in particular is drawn by many non-electrical nodes,
        and reusing the tree-wide total would attribute every blast furnace
        and forge's ore to arc_furnace_ferroalloys' electric arc)."""
        node = self.nodes.get(node_id)
        if node is None:
            return 0.0
        quantity = float((node.get("mat") or {}).get(mat_key, 0.0))
        if quantity <= 0:
            return 0.0
        span = max(1.0, float(node.get("build_yrs") or node.get("yrs") or 1.0))
        projects = self.state.projects
        if node_id in projects.active:
            return quantity / span / KILOGRAMS_PER_TONNE
        if node_id in projects.done and float(node.get("up") or 0) > 0:
            return self.STANDING_MATERIAL_DRAW_SHARE * quantity / span / KILOGRAMS_PER_TONNE
        return 0.0

    def _electricity_demand_kw(self):
        """Average continuous kW drawn by work in hand - the electrical
        mirror of annual_material_demand(), in kilowatts instead of tonnes.
        `sorted()` throughout: this feeds a float sum, and set/dict
        iteration order is not guaranteed stable across PYTHONHASHSEED
        values (see this file's own determinism convention elsewhere)."""
        total = 0.0
        curated = self.ELECTRICAL_PROCESSES
        for node_id, (mat_key, kwh_per_kg) in sorted(curated.items()):
            t_per_yr = self._node_annual_tonnes(node_id, mat_key)
            if t_per_yr <= 0:
                continue
            total += (t_per_yr * KILOGRAMS_PER_TONNE * kwh_per_kg) / self.HOURS_PER_YEAR
        for node_id in sorted(self._electricity_load_node_ids() - set(curated)):
            node = self.nodes.get(node_id)
            if node is None:
                continue
            projects = self.state.projects
            if node_id in projects.active:
                total += self.GENERIC_ELECTRIC_LOAD_KW
            elif (node_id in projects.done and float(node.get("up") or 0) > 0
                  and node_id in getattr(projects, "operating", ())):
                # STANDING draw, where upkeep IS the right question: a thing
                # that costs nothing to keep is not an installation humming
                # away in the background, and one that is built but shut draws
                # nothing either.
                total += self.STANDING_MATERIAL_DRAW_SHARE * self.GENERIC_ELECTRIC_LOAD_KW
        return total

    RESOURCE_THROTTLE_FLOOR = declare(
        "RESOURCE_THROTTLE_FLOOR", 0.05, kind="temporary_heuristic",
        unit="fraction of full pace (minimum)", source=None,
        confidence="D",
        why="A material or electricity shortfall slows work rather than "
            "stopping it dead - a shortage is a real cost, not a wall a "
            "player cannot work around at all. The floor's own level (work "
            "always creeps forward at at least 5% pace) is a game-design "
            "choice, not derived from any real bound on how slow "
            "under-resourced work can go.")

    def resource_throttle(self):
        """How much of this year's planned work the materials will actually support.

        Charcoal is the one that bites, because it is not mined, it is GROWN.
        A hectare of coppice yields about 0.75 tonnes of charcoal a year, and a
        single blast furnace making 300 tonnes of iron eats 900 tonnes of it. If
        you have not bought the woodland, the furnace idles.
        """
        # CACHED for material_price_factor(). project_cost() now calls that
        # once for every candidate node `available` considers, every year,
        # for every active project, and annual_material_demand() is
        # O(active + done); recomputing it from scratch on every one of those
        # calls is the quadratic blowup this codebase already had to fix once
        # for done_in_order() (see its own comment). Good for one step(): a
        # query between steps reads the demand as of the last one, which is
        # already true of price_index, self.economy and self.household.throttle itself.
        self.household._material_demand_cache = self.annual_material_demand()
        industrial, lab = self._throttle_demand_split(self.household._material_demand_cache)
        stock = self._material_stock()
        # IDEMPOTENT WHEN NOTHING HAS ACTUALLY CHANGED. protocol.py's own
        # `why` handler calls this twice in a row to build one message
        # (sim.binding, then sim.resource_throttle() again for the percentage)
        # with nothing mutated in between - read-only from its point of
        # view, which it always was before this, because there was nothing
        # here a second call could consume. Now there is: the stock this
        # function draws down must be spent once per genuine recomputation,
        # not once per CALL, or a query asked twice double-depletes it and
        # answers its own two calls with two different numbers. Keyed on the
        # CONTENT that feeds the computation below, including the year. A new
        # year is a new production flow and must bank another year's unused
        # mine output; repeated queries within that year must not. A test,
        # or a player, building a mine or a nitre bed mid-year and asking
        # again in the SAME year must see the new answer immediately, not a
        # stale replay - see test_regressions.py's own
        # "...and stops once your own supply covers the need", which does
        # exactly that). Unchanged content means replaying the cached
        # (worst, who) is not a shortcut, it is the actual answer.
        # ELECTRICITY. Computed here, not inside the stock loop below (see
        # the class comment on _electricity_demand_kw/generation_breakdown_kw
        # for why it never touches `stock`), but its have/need both have to
        # be part of the signature: dynamo, en_alternator and the other
        # generation nodes all carry mat={} (a capability/machine node, not
        # a material purchase), so finishing one changes generation_capacity_
        # kw without changing `industrial`/`lab`/mine_capacity/forest_ha/
        # nitre_bed_m2/stock at all - the exact case the cache below would
        # otherwise silently replay a now-stale (worst, who) for.
        elec_need = self._electricity_demand_kw()
        elec_have = self.generation_capacity_kw()
        economy = self.state.economy
        scenario = self.state.scenario
        sig = (scenario.year, tuple(sorted(industrial.items())), tuple(sorted(lab.items())),
               tuple(sorted(self.mine_capacity.items())), economy.forest_ha,
               economy.nitre_bed_m2, tuple(sorted(stock.items())),
               elec_need, elec_have)
        if sig == getattr(self.household, "_stock_throttle_sig", None):
            economy.throttle, economy.binding = self.household._stock_throttle_cache
            return economy.throttle
        worst, who = 1.0, None
        # RESOURCE_THROTTLE_FLOOR (declared below): work never fully stops
        # for a shortage - a shortfall slows a project instead of halting
        # it dead, so a bottleneck is a real cost rather than a stuck game.
        if elec_need > 1e-9 and elec_have < elec_need:
            fraction = max(self.RESOURCE_THROTTLE_FLOOR, elec_have / elec_need)
            if fraction < worst:
                worst, who = fraction, "electricity"
        all_tags = set(industrial) | set(lab) | self._own_production_tags()
        for emp_key, tag in sorted(all_tags):
            ind_need = industrial.get((emp_key, tag), 0.0)
            lab_need = lab.get((emp_key, tag), 0.0)
            # Two different things, kept separate on purpose: OWN_AND_STOCK
            # is physically yours - a bed you built, a mine you sank, a
            # surplus banked from an earlier year - and can BANK again if
            # unused this year. `market` is a standing offer (how much the
            # empire's market would sell you, not what you bought), and
            # choosing not to buy it this year does not make it yours to
            # keep: banking unused MARKET headroom as though it were
            # inventory was the bug this split exists to avoid (a material
            # with a large generic market figure and no demand for years
            # would otherwise accumulate thousands of tonnes nobody ever
            # produced or paid for).
            own_and_stock = stock.get(emp_key, 0.0) + self._own_material_supply(tag)
            have = own_and_stock + self._material_market_tonnes(emp_key)
            # Lab-scale first, and unconditionally: drawn from whatever is
            # banked or flowing in this year, topped up by a direct purchase
            # this function never checks capacity for - "I would just buy
            # 20 grams," exactly. It can never be what sets `worst`/`who`.
            lab_drawn = min(lab_need, have)
            have -= lab_drawn
            consumed_ind = 0.0
            if ind_need > 1e-12:
                if have < ind_need:
                    fraction = max(self.RESOURCE_THROTTLE_FLOOR, have / ind_need)
                    if fraction < worst:
                        worst, who = fraction, emp_key
                    consumed_ind = have
                else:
                    consumed_ind = ind_need
            # BANK THE REST OF WHAT WAS YOURS. Own production (and prior
            # stock) this year that neither draw actually touched goes back
            # into stock rather than evaporating - the other half of the fix
            # (DOCS_VS_ENGINE.md #3). Capped at own_and_stock, never at the
            # larger `have`, for exactly the reason in the comment above.
            stock[emp_key] = max(0.0, own_and_stock - lab_drawn - consumed_ind)
        economy.throttle, economy.binding = worst, who
        # Stored AFTER mutation, against stock as this call actually left
        # it - so an immediate repeat call's sig (computed from that same,
        # now-settled stock) matches and replays rather than spending again.
        self.household._stock_throttle_sig = (sig[0], sig[1], sig[2], sig[3], sig[4],
                                     sig[5], tuple(sorted(stock.items())),
                                     sig[7], sig[8])
        self.household._stock_throttle_cache = (worst, who)
        if who:
            economy.shortages[who] += 1
        return worst

    def project_resource_throttle(self, node_id):
        """Material throttle applicable to one active project.

        ``resource_throttle`` still performs the portfolio-level supply and
        stock accounting and identifies the binding pool.  The resulting
        scarcity must only slow work that draws from that pool, however; paper
        research does not become short of saltpetre because a gunpowder project
        is.  Consumers of the scarce pool share its aggregate factor, while
        projects with no matching input retain their full labour pace.
        """
        factor = self.resource_throttle()
        binding = self.state.economy.binding
        if factor >= 0.999 or not binding:
            return 1.0
        if binding == "electricity":
            return factor if node_id in self._electricity_load_node_ids() else 1.0
        node = self.nodes.get(node_id) or {}
        coke = self.chosen_fuel(node_id) == "coke"
        for mat in (node.get("mat") or {}):
            effective_mat = ("coal_kg" if coke
                             and mat in ("charcoal_kg", "firewood_kg") else mat)
            # Gram-scale purchases never participate in the flow throttle.
            if effective_mat.endswith(self.LAB_SCALE_SUFFIX) \
                    and not effective_mat.endswith("_kg"):
                continue
            if self._material_tag(effective_mat)[0] == binding:
                return factor
        return 1.0
