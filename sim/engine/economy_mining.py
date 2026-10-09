"""Mining, ore depletion and the land a mine or a coppice stands on.

Split out of economy.py (see that file's own docstring for why): every
method here answers "how much of a raw material could you physically
pull out of the ground (or the woodland) this year, and at what cost",
as opposed to economy_materials.py's "what does the market charge for
it now" - the two halves of raw-material economics COMMODITY_DYNAMISM.md
and MATERIAL_GATING.md describe. Four subjects, in the order they
appear below:

  - the generic capex/opex lever every mineable material shares
    (_mine_capex_opex and friends, mineable(), mine_catalog_hint());
  - LAND: how large a standing mine (mine_land_ceiling) or coppice
    (forest_land_ceiling, buy_forest, home_land_area_km2) your standing
    and state can ever support;
  - DEPLETION: a worked deposit's yield falling as intensity-years of
    mining accumulate against that land ceiling; and
  - TECHNOLOGY: the pump, the railway, black powder and dynamite that
    push depletion and cost back the other way, and the per-working
    machinery (open/close/commission/mothball a working, quote it,
    charge its standing operating cost) that all of the above feeds.

MiningMixin is composed into EconomyMixin (economy.py) alongside the
other economy sub-mixins; see that file for the composition and for the
grouping evidence.
"""
import functools

from sim.constants import declare
from . import money_units
from sim.unit_conversions import KILOGRAMS_PER_TONNE
from sim.world import deposits as deposit_model, mine_technique
from sim.geography.api import mine_demand_goods, parameter_value, tile_facts, tiles_held, works_priced_from_deposits
from . import purchase_rule
from .mine_deposits import MineDepositsMixin, NO_DEPOSIT_TEXT
from sim.agents.api import edges


@functools.lru_cache(maxsize=None)
def _works_priced_materials(world_map):
    return works_priced_from_deposits(world_map)


@functools.lru_cache(maxsize=None)
def _demand_goods_by_material(world_map):
    return mine_demand_goods(world_map)


def mine_catalog_hint_for(materials):
    """The hint naming the materials whose workings are priced from deposits, and the generic fallback."""
    return ("well-known workings: %s - or any other material key the "
            "tree uses (for example aluminium_kg), priced from its own "
            "book price if nothing more specific is known about it"
            % ", ".join(sorted(materials)))


class MiningMixin(MineDepositsMixin):
    mine_refusal = None   # why the last open_mine opened nothing, when a deposit was the reason

    @property
    def MINE_OPEX_MATERIALS(self):
        """Materials whose mine running cost comes from the deposits' physical works, from the map's catalogue."""
        return _works_priced_materials(self.world_map)

    def mine_demand_goods(self, material):
        """The goods whose annual demand a mine of `material` supplies: the catalogue row's list, else the key itself."""
        return _demand_goods_by_material(self.world_map).get(material, (material,))

    @property
    def MINE_OPEX_PER_T(self):
        """Running cost per tonne extracted, by material, in this civilisation's
        coin: the deposits' own extraction labour at the miner's wage."""
        return {material: self._mine_opex(material) for material in self.MINE_OPEX_MATERIALS}

    MINE_LEAD_YEARS = declare(
        "MINE_LEAD_YEARS", 3.0, kind="engineering_estimate",
        unit="years", source="Sinking a shaft, arranging drainage, "
             "building access roads and hiring a crew for a pre-modern "
             "working plausibly takes on this order of time; not tied to "
             "an attested figure for a specific Roman mine.",
        confidence="C",
        why="How long a new mining tranche takes to come into production "
            "after capital is committed - the delay that stopped a "
            "playtester from treating mine investment as instantaneous.")

    # ---- CAPEX AND OPEX FROM THE PHYSICAL WORKS, FOR ANY MINEABLE MATERIAL ----
    #
    # Capex per tonne/year is the labour to sink and equip the shafts that
    # tonne needs (sim.world.deposits), at the miner's wage. It never reads
    # the material's price. Capacity needs as many shafts as the rock to be
    # raised requires, so a lean ore costs more capex per tonne of metal.
    # The typical working of a metal is its named deposits weighted by
    # output; a material with no deposit data is worked as a shallow seam
    # of the material itself.
    GENERIC_MINE_DEPTH_CLASS = declare(
        "GENERIC_MINE_DEPTH_CLASS", "shallow_vein", kind="temporary_heuristic",
        unit="depth class of deposits.py", source=None, confidence="D",
        why="Depth of the workings assumed for a material with no named "
            "deposits; replace with per-material deposit data.")
    GENERIC_MINE_HARDNESS_CLASS = declare(
        "GENERIC_MINE_HARDNESS_CLASS", "medium", kind="temporary_heuristic",
        unit="hardness class of deposits.py", source=None, confidence="D",
        why="Rock hardness assumed for a material with no named deposits; "
            "replace with per-material deposit data.")
    @property
    def MINE_TRADE(self):
        """The trade whose wage prices mine labour, from the map's parameters."""
        return parameter_value("mining_trade", self.world_map)

    _MINE_PROFILE_CACHE = {}

    def _mine_reference_deposits(self, mat):
        """(deposit, weight) pairs describing a typical working of `mat`."""
        if mat in deposit_model.metals(self.world_map):
            pool = deposit_model.load_deposits(mat)
            total = sum(dep.quantity_tonnes_per_year for dep in pool)
            return [(dep, dep.quantity_tonnes_per_year / total) for dep in pool]
        seam = deposit_model.Deposit(
            name="generic_" + mat, metal=mat, tile="", material_moved="ore",
            ore_grade_kg_per_tonne=KILOGRAMS_PER_TONNE,
            depth_class=self.GENERIC_MINE_DEPTH_CLASS,
            hardness_class=self.GENERIC_MINE_HARDNESS_CLASS,
            quantity_tonnes_per_year=1.0, note="")
        return [(seam, 1.0)]

    def mine_works_effects(self):
        """What the running mining techniques change in the physical works
        (mine_technique.combine of every running node's `mine_works` spec)."""
        kept = self._running_kept("mine_works_effects")
        if "effects" not in kept:
            kept["effects"] = mine_technique.combine(
                spec for node_id, spec in self._effect_terms("mine_works")
                if self.running(node_id))
        return kept["effects"]

    def _mine_labour_hours_per_tonne(self, mat):
        """(build hours per tonne/year, running hours per tonne) of a typical
        working of `mat`, output-weighted across its deposits, under the
        running techniques' effects on the works."""
        effects = self.mine_works_effects()
        key = (mat, mine_technique.effects_key(effects))
        cached = self._MINE_PROFILE_CACHE.get(key)
        if cached is None:
            pairs = self._mine_reference_deposits(mat)
            build = sum(weight * deposit_model.build_cost_labour_hours_per_tonne_year(dep, effects)
                        for dep, weight in pairs)
            running = sum(weight * KILOGRAMS_PER_TONNE
                          * deposit_model.extraction_cost_labour_hours_per_kg(dep, effects)
                          for dep, weight in pairs)
            cached = self._MINE_PROFILE_CACHE[key] = (build, running)
        return cached

    def _mine_capex_opex(self, mat):
        """(capex per t/yr to sink, opex per t/yr to run) for standing
        production of `mat`, both from the deposits' physical works at the
        miner's wage. (None, None) for a name nothing prices."""
        if mat not in self.MINE_OPEX_MATERIALS:
            price = self._material_price_per_kg(mat)
            if price is None or price <= 0:
                return None, None
        wage = self.labour.wage_per_hour(self.MINE_TRADE)
        build_hours, running_hours = self._mine_labour_hours_per_tonne(mat)
        return build_hours * wage, running_hours * wage

    def _mine_capex(self, mat):
        capex, _opex = self._mine_capex_opex(mat)
        return capex

    def _mine_opex(self, mat):
        _capex, opex = self._mine_capex_opex(mat)
        return 0.0 if opex is None else opex

    def mineable(self, mat):
        """Can you sink standing production capacity in this material at
        all? True for the seven curated metals and, generalised, for any
        material key or curated commodity id this file can find a
        calculated price for - in practice anything a node in the tech tree
        buys, since the solver prices every material a recipe makes. False
        only for a name that prices nothing at all: a typo, not a real gap."""
        return self._mine_capex(self._normalize_material_name(mat)) is not None

    def mine_catalog_hint(self):
        """What to tell a player who typed a material name this file
        cannot price: the materials the deposits' works price on this
        game's map, and the generic fallback below. Not a closed list."""
        return mine_catalog_hint_for(self.MINE_OPEX_MATERIALS)

    @staticmethod
    def base_mine_catalog_hint():
        """The same hint on the base map, for help text written before any game exists."""
        return mine_catalog_hint_for(_works_priced_materials(None))


    # ---- LAND: what is under your feet is geography, not standing --------
    #
    # open_mine()'s ceiling must not depend only on patronage and state
    # capacity, the SAME number for every material: a founder with an
    # imperial patron could otherwise sink exactly as large a tin mine as
    # an iron one, in a home province with no tin in it at all. Mines are
    # limited by land area and what is actually under it, the same as the
    # market half of supply is. geography.py's mineral_scale() ALREADY
    # answers "how much of this material's national output can THIS
    # civilisation reach," built from the geography data's per-region mineral
    # abundance and this civilization's own home_regions and reach (see
    # its own comment) -- and it already governs the MARKET half of supply
    # (_material_market_tonnes). Reusing it here, rather than inventing a
    # second geology signal, means a civ that
    # cannot buy much tin also cannot simply out-organise its way to
    # unlimited tin by sinking shafts instead -- the same ground is short
    # either way. Measure it per civilisation with Geography.mineral_scale().
    STATE_CAPACITY_DEFAULT_FALLBACK = declare(
        "STATE_CAPACITY_DEFAULT_FALLBACK", 0.5, kind="initial_condition",
        unit="dimensionless state-capacity index (0-1 scale), fallback",
        source=None, confidence="D",
        why="Fallback state_capacity for a civilisation whose own data "
            "does not specify one - a middling value on the 0-1 scale "
            "civ.get('state_capacity', ...) otherwise reads from each "
            "civilisation's own file, used here for both the mine and "
            "forest land ceilings. Every shipped civilisation defines its "
            "own state_capacity (out of this file's scope); this is only "
            "the default a missing or hand-authored one would fall back "
            "to, not a claim about any specific society.")

    def mine_land_ceiling(self, mat):
        """The largest standing capacity of this material you could ever
        organise, in tonnes/yr: how big an enterprise your standing and
        state can run, times whether the ore is actually under your feet,
        (what technology lets a working raise per shaft is in the works cost,
        sim/world/deposits.py, not a multiple here)."""
        state_capacity = float(self.civ.get("state_capacity", self.STATE_CAPACITY_DEFAULT_FALLBACK))
        favour = self.effect_best("mine_ceiling")
        if favour is not None:
            base = favour[1]["base"] + favour[1]["state_scale"] * state_capacity
        else:
            base = self.MINE_CEILING_BASE_STRANGER + self.MINE_CEILING_STATE_SCALE_STRANGER * state_capacity
        base *= 1.0 + min(self.REVENUE_SCALE_CAP_MULTIPLE, max(0.0, self.revenue()) / self.REVENUE_SCALE_DENARII)
        geo = self.geography.mineral_scale(mat)
        return base * geo

    MINE_CEILING_BASE_IMPERIAL = declare(
        "MINE_CEILING_BASE_IMPERIAL", 20000.0, kind="temporary_heuristic",
        unit="tonnes/year (base, before state capacity and revenue scale)",
        source=None, confidence="D",
        why="Base standing-mine ceiling for an imperial patron before "
            "state capacity, geology and mining technology are applied. "
            "No fiscal or organisational-capacity data backs this figure; "
            "it is a tuned starting point for the four patronage tiers "
            "this method distinguishes.")
    MINE_CEILING_STATE_SCALE_IMPERIAL = declare(
        "MINE_CEILING_STATE_SCALE_IMPERIAL", 60000.0, kind="temporary_heuristic",
        unit="tonnes/year per unit of state_capacity", source=None,
        confidence="D",
        why="How much further a more capable state extends the imperial-"
            "tier ceiling. Tuned, not derived from any state-capacity "
            "output relationship.")
    MINE_CEILING_BASE_STRANGER = declare(
        "MINE_CEILING_BASE_STRANGER", 3000.0, kind="temporary_heuristic",
        unit="tonnes/year (base)", source=None, confidence="D",
        why="As MINE_CEILING_BASE_IMPERIAL, for a stranger with no "
            "citizenship or patron - still a real production ceiling, per "
            "this method's own docstring, so an unpatronised founder is "
            "never simply shut out of mining.")
    MINE_CEILING_STATE_SCALE_STRANGER = declare(
        "MINE_CEILING_STATE_SCALE_STRANGER", 4000.0, kind="temporary_heuristic",
        unit="tonnes/year per unit of state_capacity", source=None,
        confidence="D",
        why="As MINE_CEILING_STATE_SCALE_IMPERIAL, for the stranger tier.")
    REVENUE_SCALE_CAP_MULTIPLE = declare(
        "REVENUE_SCALE_CAP_MULTIPLE", 5.0, kind="temporary_heuristic",
        unit="multiple on the base ceiling (maximum)", source=None,
        confidence="D",
        why="How much a household's own revenue can multiply a standing "
            "ceiling (mine land or forest land) beyond its patronage-tier "
            "base, capped so a very rich household still cannot organise "
            "an unbounded enterprise from revenue alone. Reused identically "
            "for forest_land_ceiling() below. Tuned, not derived from any "
            "attested relationship between income and organisational "
            "capacity.")
    REVENUE_SCALE_LABOUR_HOURS = declare(
        "REVENUE_SCALE_LABOUR_HOURS", 1210000.0, kind="temporary_heuristic",
        unit="labour hours/year of revenue for +100% ceiling", source=None,
        confidence="D",
        why="Amount of labour, not of coin: it was a book-denarii figure and now follows what labour costs. "
            "How much annual revenue it takes to double a standing "
            "ceiling via REVENUE_SCALE_CAP_MULTIPLE, reused identically in "
            "forest_land_ceiling() below. Tuned, not derived from any "
            "attested income-to-capacity relationship.")
    REVENUE_SCALE_DENARII = money_units.PricedInLabourHours("REVENUE_SCALE_LABOUR_HOURS")

    # ---- DEPLETION: the easy seam runs out ---------------------------
    #
    # A tester's second question: "does mine production go down over time,
    # as you mine the easy stuff and it gets harder?" It did not -- output
    # was flat for ever, which is not how any real working behaves. What is
    # tracked is not raw tonnes extracted (an arbitrary absolute figure with
    # no natural scale to compare it to across seven wildly different
    # materials and five civilizations) but INTENSITY: how many YEARS you
    # have worked this material at what fraction of its own land ceiling.
    # Mining at 20% of what the ground could ever support barely touches the
    # easy ore; mining at 100% of it, continuously, is exactly the situation
    # that historically forced a working deeper, or somewhere else, inside a
    # few generations. DEPLETION_HALF_LIFE_YRS=120 is a [C] estimate at that
    # order of magnitude (roughly the span across which real long-worked
    # Old World deposits -- Rio Tinto's and Laurion's near-surface ore --
    # went from rich to markedly poorer and needed new technique, several
    # human generations, not one and not a thousand), chosen deliberately
    # round rather than fitted to any single citation. Floored at 0.5,
    # never lower: the easy half of a deposit running out does not mean the
    # hard half is worthless, and a floor that could reach zero would be the
    # abolished "unobtainable" category wearing a new name (see open_mine's
    # own comment on that history). This is intensity-years, not calendar
    # years, so it accrues faster the harder you lean on a given deposit
    # relative to what the ground can support -- and slower once technology
    # (the works techniques, sim/world/mine_technique.py) raises that
    # support, which is the whole of "make depletion something you can fight."
    DEPLETION_HALF_LIFE_YRS = declare(
        "DEPLETION_HALF_LIFE_YRS", 120.0, kind="temporary_heuristic",
        unit="intensity-years for yield to fall from 1.0 toward the floor",
        source="Order-of-magnitude anchor: real long-worked Old World "
               "deposits (Rio Tinto, Laurion's near-surface ore) went from "
               "rich to markedly poorer and needed new technique over "
               "several human generations, not one and not a thousand.",
        confidence="C",
        why="How many intensity-years of mining at full land-ceiling "
            "pace it takes a deposit's yield to visibly decline - see the "
            "class comment above for why this is INTENSITY-years (working "
            "hard relative to what the ground supports) rather than "
            "calendar years. Deliberately round rather than fitted to any "
            "single citation, per that comment.")
    DEPLETION_FLOOR = declare(
        "DEPLETION_FLOOR", 0.5, kind="temporary_heuristic",
        unit="fraction of day-one yield (minimum)", source=None,
        confidence="D",
        why="However worked-out a deposit gets, a working never falls "
            "below half its original yield - the easy half of a deposit "
            "running out does not mean the hard half is worthless. "
            "Deliberately never zero: see the class comment above for why "
            "a floor reaching zero would be the abolished 'unobtainable' "
            "category returning under a new name. The specific half-yield "
            "floor is chosen for that reason, not measured from any real "
            "deposit's long-run decline curve.")

    # ---- A WORKING IS A THING, NOT AN ENTRY IN A MATERIAL-KEYED DICT -------
    #
    # Answering which mine, rated capacity, actual output, cost,
    # utilisation, the year it came on stream, and whether it is a real
    # supply or merely an asset sitting on the books needs an actual "it":
    # a single float per material, aged as a WHOLE material at once, would
    # make a shaft opened in year 400 exactly as worked-out as one opened
    # three centuries earlier purely because they share a material key.
    # self.household.mines is a list of actual workings, each its own dict
    # with the material it raises, its rated capacity, the year it was
    # commissioned, what it cost to sink, and its OWN depletion clock
    # (intensity_yrs) running from that year, not from whenever the
    # material was first touched. self.mine_capacity below is a PROPERTY
    # summed over this list, never a second number tracked separately, so
    # it can be read everywhere it already was, with nothing able to
    # silently drift it out of step with the workings that actually make
    # it up.
    def _workings_of(self, mat):
        """This civilisation's own workings raising `mat`, in the order they
        were commissioned (self.household.mines is append-only in commission order,
        never hash-ordered, so this is deterministic across runs)."""
        return [working for working in getattr(self.household, "mines", ()) if working.get("material") == mat]

    @property
    def mine_capacity(self):
        """Rated capacity of your own workings, summed by material -
        DERIVED from self.household.mines, not a second number that has to agree with
        it. Read-only: opening, closing and mothballing a working all act
        on self.household.mines itself (see open_mine/commission_mines/close_mine/
        mothball_mines), and this recomputes from whatever that list says."""
        out = {}
        for working in getattr(self.household, "mines", ()):
            out[working["material"]] = out.get(working["material"], 0.0) + working["capacity"]
        return out

    def mine_depletion_factor_for(self, working):
        """Fraction of day-one yield THIS working still gets, from ITS OWN
        cumulative intensity since ITS OWN commissioning year (see the class
        comment above `_workings_of`) - the per-working half of the fix."""
        intensity_years = working.get("intensity_yrs", 0.0)
        return max(self.DEPLETION_FLOOR, 1.0 - intensity_years / self.DEPLETION_HALF_LIFE_YRS)

    def mine_depletion_factor(self, mat):
        """This material's CURRENT typical depletion, as the
        capacity-weighted average across your existing workings of it - used
        to price a NEW working before it has any history of its own (see
        mining_cost_scale/mine_quote/open_mine: the ground here is however
        worked-out your existing shafts say it is) and for the one-line
        summary mine_depletion_note() gives. A material with no workings yet
        has no history to weight, so this is 1.0: the book price, day one."""
        workings = self._workings_of(mat)
        total = sum(working["capacity"] for working in workings)
        if total <= 0:
            return 1.0
        return sum(self.mine_depletion_factor_for(working) * working["capacity"]
                   for working in workings) / total

    def _advance_mine_depletion(self):
        """One year of intensity for every working you currently hold,
        each aged from ITS OWN commissioning year rather than the
        material's. Called once a year from commission_mines(), which
        core.py's step() already calls exactly once a year -- see that
        function's own comment -- so this needed no new call site.

        Iterates self.household.mines (a list, in commission order) and caches
        mine_land_ceiling() per material seen rather than per working, so
        this is neither hash-ordered (self.household.mines is a list) nor quadratic in
        the number of workings of one material."""
        ceilings = {}
        for working in getattr(self.household, "mines", ()):
            mat = working["material"]
            if mat not in ceilings:
                ceilings[mat] = max(1.0, self.mine_land_ceiling(mat))
            self._draw_working(working)
            working["intensity_yrs"] = working.get("intensity_yrs", 0.0) + working["capacity"] / ceilings[mat]
        self._close_worked_out()

    def _draw_working(self, working):
        """This year's yield of a working comes out of the deposit it names."""
        if working.get("deposit"):
            self.draw_deposit(working["deposit"], self.mine_yield_t_for(working))

    def _close_worked_out(self):
        """Workings whose deposit has nothing left close."""
        holdings = self.state.holdings
        kept = []
        for working in holdings.mines or ():
            deposit_id = working.get("deposit")
            if deposit_id and self.deposit_remaining_tonnes(working["material"], deposit_id) <= 0.0:
                self.state.household.log.append((self.state.scenario.year, "the %s workings at %s are worked out and close"
                                                 % (working["material"], deposit_id)))
            else:
                kept.append(working)
        holdings.mines = kept

    # ---- TECHNOLOGY: the pump, the railway and cheap steel fight back -----
    #
    # A tester's third question, and the important one: does technology
    # raise yield? It did not, anywhere in the model, which is a real
    # modelling error -- industrialisation paid for itself largely because
    # the pumping engine, the railway and cheap steel made ore worth
    # lifting that was not worth lifting before. Each entry below is a real
    # node (grepped for steam/pump/newcomen/railway/blast/bessemer/
    # explosive/nitro/drill against the actual tree, not invented): `yield`
    # raises mine_land_ceiling() AND mine_depletion_factor()'s effective
    # output together (a pump does not just let you sink a new shaft, it
    # means the shaft you already have stops standing idle half-flooded);
    # `cost` lowers what sinking or running a tonne/yr costs (mining_cost_
    # scale(), below). Multipliers COMPOUND across every one built, the
    # same pattern best_multiplier() in commodities.py uses for gold's
    # pump-times-cyanidation ~20x, because pumping and blasting and a
    # railway are independent improvements, not alternatives.
    # Mechanical (water-wheel or animal) mine drainage - the first tier of the
    # pumping problem the class comment describes.
    def _running_kept(self, name):
        """A dict for derived values that depend only on which nodes are built, granted and
        operating (what `running` reads); it starts empty whenever that changes."""
        projects = self.state.projects
        stamp = (self.household.done_version, self.household.operating_version,
                 len(projects.done), len(projects.granted), len(projects.operating))
        kept = self.__dict__.get("_running_kept_tables")
        if kept is None or kept[0] is not projects or kept[1] != stamp or kept[2] is not self.nodes:
            kept = self.__dict__["_running_kept_tables"] = (projects, stamp, self.nodes, {})
        return kept[3].setdefault(name, {})

    def mining_cost_scale(self, mat):
        """What sinking or running a tonne/yr of this material costs THIS
        YEAR, relative to the derived capex and opex. The derived figures
        already carry what the running techniques do to the works
        (_mine_labour_hours_per_tonne), so this is depletion alone
        (mine_depletion_factor, inverted -- the same effort recovers less
        from a half-worked deposit, so it costs proportionally more per
        tonne). Bounded to keep it a real decision rather than a runaway."""
        return max(self.MINING_COST_SCALE_FLOOR,
                   min(self.MINING_COST_SCALE_CEILING, 1.0 / self.mine_depletion_factor(mat)))

    def mining_cost_scale_for(self, working):
        """Same as mining_cost_scale(), but for what running THIS working
        costs this year, from ITS OWN depletion rather than its material's
        average - an old, half-worked shaft costs more per tonne to keep
        running than a fresh one of the same material, which the old
        material-level figure could not say because it had no idea which
        working was which."""
        return max(self.MINING_COST_SCALE_FLOOR,
                   min(self.MINING_COST_SCALE_CEILING, 1.0 / self.mine_depletion_factor_for(working)))

    MINING_COST_SCALE_FLOOR = declare(
        "MINING_COST_SCALE_FLOOR", 0.4, kind="temporary_heuristic",
        unit="dimensionless multiple on book capex/opex (minimum)",
        source=None, confidence="D",
        why="However much mining technology cheapens a fresh deposit, it "
            "never costs less than 0.4x book, per this method's own "
            "docstring ('not free'). A defensive bound to keep the "
            "technology-versus-depletion tension a real decision rather "
            "than a runaway, not a derived limit.")
    MINING_COST_SCALE_CEILING = declare(
        "MINING_COST_SCALE_CEILING", 2.5, kind="temporary_heuristic",
        unit="dimensionless multiple on book capex/opex (maximum)",
        source=None, confidence="D",
        why="However depleted and untooled a working is, it never costs "
            "more than this multiple of book price, so a fully worked-out "
            "deposit is a real cost penalty rather than an effectively "
            "infinite one. A defensive bound, not a derived limit (this "
            "method's own docstring quotes 'at most 2x book' for the "
            "fully-depleted case, which is a description of the typical "
            "outcome, not this literal ceiling).")

    def mine_yield_t_for(self, working):
        """Tonnes a year THIS working actually raises this year, after ITS
        OWN depletion."""
        yield_t = working["capacity"] * self.mine_depletion_factor_for(working)
        if working.get("deposit"):
            yield_t = min(yield_t, self.deposit_remaining_tonnes(working["material"], working["deposit"]))
        return yield_t

    def mine_operating_cost_for(self, working):
        """What THIS working costs to run this year, whether or not you use
        what it raises - mine_operating_cost()'s per-working figure, the one
        `mines` shows against each row."""
        mat = working["material"]
        return (working["capacity"] * self._mine_opex(mat) * self.price_index
                * self.mining_cost_scale_for(working))

    def mine_operating_cost_new(self, mat, tonnes):
        """What a freshly commissioned working of `tonnes` will be charged a
        year, by the same function that charges every standing working."""
        return self.mine_operating_cost_for(
            {"material": mat, "capacity": tonnes, "intensity_yrs": 0.0})

    def mine_quote(self, mat, t_per_yr):
        """What a mine would cost, BEFORE you commit to it.

        Every other purchase in this game quotes before it charges, and a
        mine opened sight-unseen can sink far more than expected with no
        price shown and no way to ask beforehand.
        """
        mat = self._normalize_material_name(mat)
        cap, _opex_per_t = self._mine_capex_opex(mat)
        if cap is None:
            return None
        tonnes = max(0.0, float(t_per_yr))
        scale = self.mining_cost_scale(mat)
        sink = tonnes * cap * self.price_index * scale
        opex = self.mine_operating_cost_new(mat, tonnes)
        ceiling = self.mine_land_ceiling(mat)
        holdings = self.state.holdings
        household = self.state.household
        room = max(0.0, ceiling - self.mine_capacity.get(mat, 0.0)
                   - holdings.mine_pending.get(mat, 0.0))
        depl = self.mine_depletion_factor(mat)
        deposit_room = self.mine_room_in_deposits(mat)
        if deposit_room is not None:
            room = min(room, deposit_room)
        note = ("The yearly cost is charged whether or not you use the "
                "output, and goes on until you close it. Mothballing is "
                "not free to reverse: the shaft floods and the crew "
                "disperses, so reopening means sinking it again.")
        if scale > 1.05:
            note += (" This costs %.0f%% of the book price: the easy ore "
                     "here is going." % (scale * 100))
        return {"material": mat,
                "tonnes_per_year": round(tonnes, 3),
                "to_sink_it": round(sink, 1),
                "every_year_it_stands": round(opex, 1),
                "years_before_it_produces": self.MINE_LEAD_YEARS,
                "you_have": round(household.capital, 1),
                "you_could_raise": round(purchase_rule.purchase_budget(self), 1),
                "you_can_afford_about": min(room, purchase_rule.affordable_units(
                    self, cap * self.price_index * scale, decimals=3)),
                "afford_means": purchase_rule.afford_means(),
                "the_ground_here_could_ever_support": round(ceiling, 1),
                "room_left_before_geology_stops_you": round(room, 1),
                "deposits_you_have_found": [
                    {"id": row["id"], "tile": row["tile_id"], "room_t_per_year": round(row["room_tonnes_per_year"], 1),
                     "left_t": round(row["remaining_tonnes"])} for row in self.found_deposits(mat)],
                "current_yield_is_this_fraction_of_day_one": round(depl, 3),
                "note": note}

    def mine_yield_t(self, mat):
        """Tonnes a year ALL your workings of this material actually raise
        this year, after each one's OWN depletion and current technology --
        the number `mines` should show summed, not the nominal tonnage
        sunk. Same figure _own_material_supply("mine:"+mat) computes;
        exposed directly so a command surface does not have to know that
        tag-string convention to ask. Sums mine_yield_t_for() over
        _workings_of(mat), a list in commission order, so this needs no
        sorted() to stay deterministic across hash seeds."""
        return sum(self.mine_yield_t_for(working) for working in self._workings_of(mat))

    def _mine_depletion_note_from(self, depl):
        """Shared sentence-builder behind mine_depletion_note() (a
        material's average) and mine_depletion_note_for() (one working's
        own figures) - the same wording either way, just fed a different
        depletion fraction."""
        if abs(depl - 1.0) < 0.01:
            return None
        return ("the easy ore here is %d%% worked out, so the same shaft "
                "yields %d%% of its first-year tonnage; techniques that cut "
                "the labour of the works (drainage, hoisting, blasting, "
                "haulage) lower what the ore costs, not how much a shaft yields"
                % (round((1.0 - depl) * 100), round(depl * 100)))

    def mine_depletion_note(self, mat):
        """One sentence on why this material's workings, ON AVERAGE, yield
        less than the tonnage sunk into them - for the same reason
        goods_market_note() exists for a concern's revenue: a player whose
        coal yield has fallen over the decades must be able to find out why
        without guessing. None if there is nothing to explain (no workings,
        or a fresh one with no relevant technology). See
        mine_depletion_note_for() for the SAME sentence about one
        particular working rather than the material's blended average."""
        if not self._workings_of(mat):
            return None
        return self._mine_depletion_note_from(self.mine_depletion_factor(mat))

    def mine_depletion_note_for(self, working):
        """mine_depletion_note(), for one working's OWN depletion rather
        than its material's average across every working of it - the
        figure the `mines` row for this specific working should explain."""
        return self._mine_depletion_note_from(self.mine_depletion_factor_for(working))

    def close_mine(self, mat):
        """Shut your own workings down, on purpose.

        The engine mothballs mines it cannot pay for on its own, but a
        player also needs an explicit way to close one voluntarily -
        without this, a mine producing nothing can go on being billed
        forever with no way to stop it.
        """
        mat = self._normalize_material_name(mat)
        workings = self._workings_of(mat)
        pend = [tranche for tranche in getattr(self.household, "mine_tranches", []) if tranche[0] == mat]
        if not workings and not pend:
            return False, ("you have no %s workings, and none being sunk" % mat
                           if self.mineable(mat)
                           else "no such material: %s. %s"
                                % (mat, self.mine_catalog_hint()))
        # Each working's OWN cost, not the material average - closing two
        # workings of very different ages must save exactly what those two
        # were actually costing, not a figure blended across every shaft of
        # this material as if they were all worked equally hard.
        saved = sum(self.mine_operating_cost_for(working) for working in workings)
        holdings = self.state.holdings
        household = self.state.household
        scenario = self.state.scenario
        holdings.mines = [working for working in (holdings.mines or [])
                         if working.get("material") != mat]
        holdings.mine_tranches = [tranche for tranche in (holdings.mine_tranches or [])
                                 if tranche[0] != mat]
        household.log.append((scenario.year, "you close the %s workings" % mat))
        return True, ("the %s workings are closed. You stop paying %.0f a year. "
                      "What you spent sinking them is gone, and reopening means "
                      "sinking them again." % (mat, saved))

    def open_mine(self, mat, t_per_yr, partial=True, order="", deposit=None):
        """Open your own workings, each naming a deposit you have found (`deposit` picks one; otherwise the
        deposits with most room are worked first) and bounded by it. A material with no deposit data is
        bounded by the ceiling alone. When none has room, nothing opens and `mine_refusal` says why.

        The Empire's ATTESTED output is not a hard ceiling: a founder who
        needs twenty thousand tonnes of coal a year must not be throttled by
        it, or the game repeats the unobtainable fallacy in different
        clothes. Rome mined almost no coal because
        almost nobody wanted coal, not because the coal was not there: Britain,
        Gaul and Spain are sitting on it, and Roman engineers already sink
        shafts, drive adits and drain them with wheels at Rio Tinto and Las
        Medulas. If you know what coke is for, you open a mine.

        What it is NOT is free or instant. You pay to sink it, you wait for it,
        and you pay every year to work it.
        """
        self.mine_refusal = None
        if t_per_yr <= 0:
            return 0.0
        mat = self._normalize_material_name(mat)
        cap = self._mine_capex(mat)
        if cap is None:
            return 0.0
        # Scale beyond a local lease needs a concession, which in practice means
        # the fiscus. Metalla were largely imperial property.
        # The ceiling is about STANDING, STATE CAPACITY AND GEOLOGY -- see
        # mine_land_ceiling()'s own comment for why it is geology now, not
        # standing alone, and for why a society with little state capacity
        # genuinely cannot organise a very large mine while a chieftain who
        # can raise a crew can still do better than a foreigner with a local
        # lease. Without the state-capacity/revenue half of this the Norse
        # run ended with 259 million denarii unspent and no iron mine, capped
        # at 3,600 tonnes a year by institutions that civilization does not
        # have; without the geology half, a founder could sink a tin mine in
        # a province with no tin in it, at the same size as one with plenty.
        ceiling = self.mine_land_ceiling(mat)
        have_cap = self.mine_capacity
        holdings = self.state.holdings
        household = self.state.household
        scenario = self.state.scenario
        t_per_yr = min(t_per_yr, max(0.0, ceiling - have_cap.get(mat, 0.0)
                                          - holdings.mine_pending.get(mat, 0.0)))
        deposit_room = self.mine_room_in_deposits(mat, deposit)
        if deposit_room is not None:
            if deposit_room <= 0.0:
                self.mine_refusal = NO_DEPOSIT_TEXT % (mat, mat)
                return 0.0
            t_per_yr = min(t_per_yr, deposit_room)
        if t_per_yr <= 0:
            return 0.0
        # DEEPER ONES COST MORE. mining_cost_scale() is 1.0 on a fresh
        # deposit with no relevant technology, so this changes nothing for
        # an early game; it rises as a deposit already worked hard is asked
        # for more, and falls back down with mine pumping, drilling,
        # blasting or a railway -- see that method's own comment.
        scale = self.mining_cost_scale(mat)
        cost = t_per_yr * cap * self.price_index * scale
        # A shaft that costs nothing needs no budget check.
        if cost > 0 and not purchase_rule.can_pay(self, cost):
            # A COMMAND YOU TYPED IS NOT A STANDING ORDER TO SPEND EVERYTHING:
            # silently spending all available capital and handing back a
            # fraction of the mine actually asked for is not what a typed
            # command should do. `hire` refuses and quotes the price; so
            # should this. The automatic policy (auto_mine) still buys
            # what it can afford, because that is the whole of its job: it
            # is spending spare cash on a bottleneck, not answering a
            # request for a particular mine.
            if not partial:
                return 0.0
            t_per_yr = purchase_rule.affordable_units(
                self, cap * self.price_index * scale, decimals=6)
            cost = t_per_yr * cap * self.price_index * scale
        if t_per_yr <= 0:
            return 0.0
        self.pay_edge(edges.EDGE_BUILDERS, cost, "mines opened")
        # Each investment is its own working with its own sinking time.
        # Pooling them and taking the LATEST ready date would mean a
        # player who invests spare cash every year, which is exactly what
        # a poor civilization must do, pushes the finish line back
        # annually and never gets any capacity at all. It also means each tranche becomes its own
        # WORKING once it commissions (see commission_mines) rather than
        # being folded into one number for the material - `cost` is carried
        # along so that working can say what it actually cost to sink, not
        # a figure recomputed later against a price_index that has since moved.
        if holdings.mine_tranches is None:
            holdings.mine_tranches = []
        for deposit_id, tonnes in self.allocate_to_deposits(mat, t_per_yr, deposit):
            holdings.mine_tranches.append([mat, tonnes, scenario.year + self.MINE_LEAD_YEARS,
                                           cost * tonnes / t_per_yr, order, deposit_id])
        holdings.mine_pending[mat] = holdings.mine_pending.get(mat, 0.0) + t_per_yr
        return t_per_yr

    def commission_mines(self):
        """Move finished tranches from pending into standing workings
        (self.state.holdings.mines), tranche by tranche. Each tranche becomes exactly one
        working, commissioned in the year it actually came on stream (the
        tranche's own `ready` year, which is when its own depletion clock
        starts - see _advance_mine_depletion) - not merged into any other
        working of the same material, so a shaft opened in year 400 stays
        a distinct, unworn thing next to one opened three centuries before
        it."""
        holdings = self.state.holdings
        scenario = self.state.scenario
        if holdings.mines is None:
            holdings.mines = []
        still = []
        for tranche in (holdings.mine_tranches or []):
            mat, amount, ready = tranche[0], tranche[1], tranche[2]
            # capex_paid: absent on a tranche written by a save from before
            # this field existed (see SAVE_FIELDS/load_state) - honestly
            # unknown, not fabricated, so 0.0 rather than a guess.
            capex_paid = tranche[3] if len(tranche) > 3 else 0.0
            order = tranche[4] if len(tranche) > 4 else ""
            deposit_id = tranche[5] if len(tranche) > 5 else None
            if scenario.year >= ready:
                holdings.mines.append({"material": mat, "capacity": amount,
                                   "opened_year": ready, "capex_paid": capex_paid, "order": order,
                                   "intensity_yrs": 0.0, "deposit": deposit_id})
                holdings.mine_pending[mat] = max(0.0, holdings.mine_pending.get(mat, 0.0) - amount)
                if holdings.mine_pending.get(mat, 0.0) <= 0:
                    holdings.mine_pending.pop(mat, None)
            else:
                still.append(tranche)
        holdings.mine_tranches = still
        # ONE YEAR OF DEPLETION: core.py's step() calls commission_mines()
        # exactly once a year (see its own comment, "materials: buy the
        # woodland... before the shortage bites"), so depletion rides that
        # call rather than needing a call site of its own.
        self._advance_mine_depletion()

    MOTHBALL_CUT_SHARE = declare(
        "MOTHBALL_CUT_SHARE", 0.5, kind="temporary_heuristic",
        unit="fraction of capacity cut per mothballing pass", source=None,
        confidence="D",
        why="How much of a worst-value material's workings are cut in one "
            "mothballing pass, so the survivors keep their own real "
            "commissioning year and depletion clock rather than whole "
            "workings being arbitrarily chosen to survive or not (see this "
            "method's own docstring). A round fraction chosen for that "
            "property, not derived from any real decommissioning practice.")

    def mothball_mines(self):
        """Stop working what you cannot pay for, worst value first.

        Mothballing is not free to reverse: the shaft floods, the timbering
        rots and the crew disperses, so bringing capacity back means paying to
        sink it again through open_mine. That is the honest cost of having
        overbuilt. Cuts every working of the worst-value material by half
        rather than removing whole workings outright, so the ones that
        survive keep their own real commissioning year and depletion clock
        instead of the newest or oldest being arbitrarily preferred."""
        household = self.state.household
        holdings = self.state.holdings
        scenario = self.state.scenario
        order = sorted(self.mine_capacity, key=lambda material: -self._mine_opex(material))
        for material in order:
            if household.capital >= 0:
                break
            kept = []
            for working in self._workings_of(material):
                cut = working["capacity"] * self.MOTHBALL_CUT_SHARE
                self.receive_from_edge(edges.EDGE_SUPPLIERS, cut * self._mine_opex(material) * self.price_index, "mine running costs saved by mothballing")
                working["capacity"] -= cut
                if working["capacity"] >= 1.0:
                    kept.append(working)
            holdings.mines = [working for working in (holdings.mines or [])
                             if working.get("material") != material] + kept
            household.log.append((scenario.year, "MOTHBALLED half the %s workings; you could "
                                        "not pay to keep them running" % material))
        # DEBT IS WHATEVER THE ARITHMETIC SAYS IT IS: capital must not be
        # clamped to minus one year's revenue after mothballing, or that
        # would forgive debt the mothballing has not actually paid off.

    def mine_operating_cost(self):
        """Charged every year the workings stand, whether or not you use them.

        Each WORKING's own mining_cost_scale_for(): a shaft you have worked
        hard for a long time, with no pumping or drilling to show for it,
        costs more than book to keep running, exactly as sinking more of it
        now does in open_mine() - and, since this sums per working rather
        than per material average, two workings of the same material at
        different ages now cost what they actually, individually cost.
        Iterates self.household.mines, a list in commission order rather than a set
        or dict, so this stays deterministic across hash seeds with no
        sorted() needed."""
        return sum(self.mine_operating_cost_for(working) for working in getattr(self.household, "mines", ()))
    # Land bounds woodland too, not only mines. the geography data carries no
    # per-region forest figure to read the way minerals has one, so this is
    # built from the signal that IS there: how much GROUND you actually hold
    # and how good your state is at organising land tenure at all
    # (state_capacity) -- a coppice is not a metalla, so no imperial
    # concession gates it, but fencing off and managing a woodland at scale
    # still takes an administration capable of holding the tenure.
    #
    # KEYED ON AREA (the geography data's own `land.land_area_km2` per home
    # region - see home_land_area_km2() below), NOT ON A COUNT OF REGION
    # LABELS (len(home_regions)): Complaint 45 names the same failure here
    # that it names for rent - a region is a filing label, not a unit of
    # area, and the labels range 86x in size (americas_north 19.8M km2
    # down to britannia's 230,000 -- the map folder (data/world/geography/)). Keying
    # this on label count would let re-filing Rome's SAME seven regions
    # as, say, fourteen tiles double its woodland ceiling with no forest
    # gaining or losing a single hectare, while Han China's one enormous
    # but singular region (9.6M km2, bigger than Rome's whole seven put
    # together) would price out at less than a seventh of Rome's ceiling
    # for holding MORE ground - the map's filing system leaking into the
    # economics, exactly as Complaint 45 describes for rent.
    #
    # [C], sized against the one real anchor available: resources.json's
    # empire-wide 500,000 t/yr of charcoal implies roughly 667,000 ha under
    # management across the WHOLE Roman world (at CHARCOAL_PER_HA=0.75
    # t/ha/yr); Rome's own ceiling below tops out around 190,000 ha even at
    # full revenue-driven scale-up, comfortably under that -- no private
    # holding should rival the entire empire's own managed woodland. The
    # per-area rate is re-derived from that SAME anchor, using Rome's own
    # home land area (9.5175 million km2, from the geography data) as the one
    # data point available to convert "hectares per home region" into
    # "hectares per million km2 of home land" -- so Rome's own ceiling barely
    # moves (its real, mapped land area is what the old per-region figure was
    # already tuned against, just via the region count as a proxy for it),
    # while a civilization whose true land area disagrees sharply with its
    # region count moves a great deal, which is the entire point of the fix.
    FOREST_HA_PER_MILLION_KM2_BASE = declare(
        "FOREST_HA_PER_MILLION_KM2_BASE", 1100.0, kind="engineering_estimate",
        unit="hectares/(million km2 of home land) (base, before state capacity)",
        source=
        "Re-derived from the same empire-wide charcoal anchor as the old "
        "FOREST_HA_PER_REGION_BASE (500,000 t/yr implying ~667,000 ha "
        "managed empire-wide at CHARCOAL_PER_HA=0.75 t/ha/yr), converted "
        "from hectares-per-region to hectares-per-million-km2 using Rome's "
        "own home land area (9.5175 million km2 across its seven home "
        "regions, the map folder (data/world/geography/)) as the calibration point, so "
        "that Rome's own pre-revenue ceiling is essentially unchanged by "
        "the switch from counting labels to reading area.",
        confidence="C",
        why="Base standing-woodland ceiling per million km2 of home land "
            "held, before state capacity is applied. the geography data carries "
            "no per-region forest figure the way it does for minerals, so "
            "this is still built from a proxy and checked against the one "
            "real empire-wide anchor available, not measured region by "
            "region -- but the proxy is now land area (a physical quantity "
            "every region already carries) rather than a count of however "
            "many labels that area happens to be filed under.")
    FOREST_HA_PER_MILLION_KM2_PER_SC = declare(
        "FOREST_HA_PER_MILLION_KM2_PER_SC", 2575.0, kind="engineering_estimate",
        unit="hectares/(million km2 of home land) per unit of state_capacity",
        source="Same empire-wide charcoal anchor and Rome-area calibration "
        "as FOREST_HA_PER_MILLION_KM2_BASE.",
        confidence="C",
        why="How much a more capable state (able to hold woodland tenure "
            "at scale) extends the per-area woodland ceiling - checked "
            "against the same empire-wide total as the base figure, not "
            "independently measured.")

    def home_land_area_km2(self):
        """Total land area, in km2, of the tiles this civilization holds, not counted by how many
        region labels that ground is filed under (see forest_land_ceiling()). A civilisation holding
        no tile has none."""
        return sum(float(tile_facts(tile, self.world_map)["land_area_km2"])
                   for tile in tiles_held(self.civ, self.world_map))

    def forest_land_ceiling(self):
        """The largest standing coppice you could ever hold, in hectares."""
        home_land_million_km2 = self.home_land_area_km2() / 1.0e6
        state_capacity = float(self.civ.get("state_capacity", self.STATE_CAPACITY_DEFAULT_FALLBACK))
        base = ((self.FOREST_HA_PER_MILLION_KM2_BASE
                 + self.FOREST_HA_PER_MILLION_KM2_PER_SC * state_capacity) * home_land_million_km2)
        return base * (1.0 + min(self.REVENUE_SCALE_CAP_MULTIPLE,
                                  max(0.0, self.revenue()) / self.REVENUE_SCALE_DENARII))

    def buy_forest(self, hectares):
        """Coppice woodland, bought outright. The cheapest thing in the tree that
        nobody thinks to buy, and the one that decides whether a furnace runs."""
        holdings = self.state.holdings
        household = self.state.household
        scenario = self.state.scenario
        room = max(0.0, self.forest_land_ceiling() - holdings.forest_ha)
        if hectares > room:
            # SILENT TRUNCATION, not a refusal: open_mine's own ceiling does
            # the same (the tranche you get is the room there is, not zero),
            # and a log line, which the player DOES see, is the honest way
            # to say why the hectares bought were fewer than asked.
            household.log.append((scenario.year,
                             "you can hold at most %.0f hectares of coppice here; "
                             "bought %.0f, not %.0f" % (self.forest_land_ceiling(),
                                                        room, hectares)))
            hectares = room
        if hectares <= 0:
            return 0.0
        cost = hectares * self.FOREST_COST_PER_HA * self.price_index
        # A shaft that costs nothing needs no budget check.
        if cost > 0 and not purchase_rule.can_pay(self, cost):
            return 0.0
        self.pay_edge(edges.EDGE_LANDOWNERS, cost, "forest bought")
        holdings.forest_ha += hectares
        return hectares
