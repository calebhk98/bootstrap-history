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
from sim.constants import declare


class MiningMixin:
    MINE_OPEX_PER_T_COAL = declare(
        "MINE_OPEX_PER_T_COAL", 1.5, kind="engineering_estimate",
        unit="denarii per tonne extracted",
        source="Derived alongside MINE_CAPEX_PER_T_YR's own coal figure from the same wage evidence.",
        confidence='B', why="Recurring cost per tonne actually extracted from a working of this material, once sunk - derived alongside MINE_CAPEX_PER_T_YR's own figure from the same wage evidence, roughly a fifth of capex across the seven curated materials (see the GENERIC_MINE_OPEX_SHARE comment below for the exact ratios).")
    MINE_OPEX_PER_T_IRON = declare(
        "MINE_OPEX_PER_T_IRON", 12.0, kind="engineering_estimate",
        unit="denarii per tonne extracted",
        source="About a fifth of iron's own capex (12/60 = 0.20), the ratio GENERIC_MINE_OPEX_SHARE below generalises.",
        confidence='C', why="Recurring cost per tonne actually extracted from a working of this material, once sunk - derived alongside MINE_CAPEX_PER_T_YR's own figure from the same wage evidence, roughly a fifth of capex across the seven curated materials (see the GENERIC_MINE_OPEX_SHARE comment below for the exact ratios).")
    MINE_OPEX_PER_T_COPPER = declare(
        "MINE_OPEX_PER_T_COPPER", 55.0, kind="engineering_estimate",
        unit="denarii per tonne extracted",
        source="About a fifth of copper's own capex (55/240 = 0.229).",
        confidence='C', why="Recurring cost per tonne actually extracted from a working of this material, once sunk - derived alongside MINE_CAPEX_PER_T_YR's own figure from the same wage evidence, roughly a fifth of capex across the seven curated materials (see the GENERIC_MINE_OPEX_SHARE comment below for the exact ratios).")
    MINE_OPEX_PER_T_LEAD = declare(
        "MINE_OPEX_PER_T_LEAD", 18.0, kind="engineering_estimate",
        unit="denarii per tonne extracted",
        source="About a fifth of lead's own capex (18/80 = 0.225).",
        confidence='C', why="Recurring cost per tonne actually extracted from a working of this material, once sunk - derived alongside MINE_CAPEX_PER_T_YR's own figure from the same wage evidence, roughly a fifth of capex across the seven curated materials (see the GENERIC_MINE_OPEX_SHARE comment below for the exact ratios).")
    MINE_OPEX_PER_T_TIN = declare(
        "MINE_OPEX_PER_T_TIN", 95.0, kind="engineering_estimate",
        unit="denarii per tonne extracted",
        source="About a fifth of tin's own capex (95/420 = 0.226).",
        confidence='C', why="Recurring cost per tonne actually extracted from a working of this material, once sunk - derived alongside MINE_CAPEX_PER_T_YR's own figure from the same wage evidence, roughly a fifth of capex across the seven curated materials (see the GENERIC_MINE_OPEX_SHARE comment below for the exact ratios).")
    MINE_OPEX_PER_T_SILVER = declare(
        "MINE_OPEX_PER_T_SILVER", 2200.0, kind="engineering_estimate",
        unit="denarii per tonne extracted",
        source="About a fifth of silver's own capex (2200/9000 = 0.244).",
        confidence='C', why="Recurring cost per tonne actually extracted from a working of this material, once sunk - derived alongside MINE_CAPEX_PER_T_YR's own figure from the same wage evidence, roughly a fifth of capex across the seven curated materials (see the GENERIC_MINE_OPEX_SHARE comment below for the exact ratios).")
    MINE_OPEX_PER_T_GOLD = declare(
        "MINE_OPEX_PER_T_GOLD", 42000.0, kind="engineering_estimate",
        unit="denarii per tonne extracted",
        source="About a fifth of gold's own capex (42000/160000 = 0.2625).",
        confidence='C', why="Recurring cost per tonne actually extracted from a working of this material, once sunk - derived alongside MINE_CAPEX_PER_T_YR's own figure from the same wage evidence, roughly a fifth of capex across the seven curated materials (see the GENERIC_MINE_OPEX_SHARE comment below for the exact ratios).")
    MINE_OPEX_PER_T = {
        'coal': MINE_OPEX_PER_T_COAL,
        'iron': MINE_OPEX_PER_T_IRON,
        'copper': MINE_OPEX_PER_T_COPPER,
        'lead': MINE_OPEX_PER_T_LEAD,
        'tin': MINE_OPEX_PER_T_TIN,
        'silver': MINE_OPEX_PER_T_SILVER,
        'gold': MINE_OPEX_PER_T_GOLD,
    }
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

    # ---- A GENERIC PRODUCTION LEVER FOR ANY MATERIAL, NOT ONLY THESE SEVEN ---
    #
    # COMMODITY_DYNAMISM.md's aluminium test, verified by running the engine
    # directly: "no mine, no supply lever of any kind for it... Nothing in
    # economy.py even contains the string 'aluminium.' Producing an enormous
    # amount of it via electrolysis tech changes nothing." open_mine() used
    # to answer nothing at all (a bare `return 0.0`) for any material not in
    # MINE_CAPEX_PER_T_YR above - a literal seven-name dictionary, chosen
    # because those seven are real, well-sourced figures (Roman wage
    # evidence, attested workings) and they stay exactly as they are here.
    # For every other material - not just aluminium, whatever the tech tree
    # is ever extended to include - GENERALISE rather than special-case: the
    # seven curated figures already show capex tracking a material's own
    # book price closely (iron 1.0 den/kg -> capex 60, copper 4.0 -> 240,
    # both a 60x multiple; tin 10.0 -> 420, ~42x; silver 317 -> 9000, ~28x;
    # gold 3440 -> 160000, ~46x - a 30-60x band holding across four decades
    # of price). 50, the middle of that band, is the generic multiple.
    # Running cost tracks capex at close to a fifth across the same seven
    # (12/60=0.20, 55/240=0.229, 18/80=0.225, 95/420=0.226, 2200/9000=0.244,
    # 42000/160000=0.2625 - all 0.20-0.26), so generic opex is 0.22x generic
    # capex. This is a real, general production lever - sink capital, wait
    # out MINE_LEAD_YEARS, pay to keep it standing - for whatever material
    # an unanticipated recipe needs, not a rule written for aluminium by name.
    GENERIC_MINE_CAPEX_MULTIPLE = declare(
        "GENERIC_MINE_CAPEX_MULTIPLE", 50.0, kind="hardcoded_outcome",
        unit="denarii capex per denarius/kg of book price", source=
        "Fitted from the seven curated MINE_CAPEX_PER_T_YR figures against "
        "their own book prices: iron ~60x, copper ~60x, tin ~42x, silver "
        "~28x, gold ~46x - a 30-60x band across four decades of price; 50, "
        "the middle of that band, is used for any material without a "
        "curated figure.",
        confidence="C",
        why="Lets open_mine() offer standing production capacity for ANY "
            "priceable material, not only the seven hand-curated metals - "
            "the fix for the aluminium gap COMMODITY_DYNAMISM.md's audit "
            "found ('no mine, no supply lever of any kind for it'). Fitted "
            "to seven points and extrapolated, the same honest limit as "
            "GENERIC_OUTPUT_ANCHOR_T_PER_YR above.")
    GENERIC_MINE_OPEX_SHARE = declare(
        "GENERIC_MINE_OPEX_SHARE", 0.22, kind="engineering_estimate",
        unit="dimensionless (opex/capex)", source=
        "Running cost tracks capex at close to a fifth across the seven "
        "curated materials (0.20-0.26 across coal/iron/copper/lead/tin/"
        "silver/gold); 0.22 is the representative figure used generically.",
        confidence="C",
        why="Converts a generic material's fitted capex into its ongoing "
            "operating cost, for the same materials GENERIC_MINE_CAPEX_"
            "MULTIPLE covers.")
    GENERIC_MINE_CAPEX_FLOOR = declare(
        "GENERIC_MINE_CAPEX_FLOOR", 5.0, kind="temporary_heuristic",
        unit="denarii per tonne/year (minimum)", source=None,
        confidence="D",
        why="Safety floor so an extremely cheap material's fitted mine "
            "capex never rounds to effectively free capacity. A defensive "
            "bound, not a reasoned floor.")
    GENERIC_MINE_CAPEX_CEILING = declare(
        "GENERIC_MINE_CAPEX_CEILING", 400000.0, kind="temporary_heuristic",
        unit="denarii per tonne/year (maximum)", source=None,
        confidence="D",
        why="Safety ceiling so an extremely dear material's fitted mine "
            "capex never runs away to an implausible figure. A defensive "
            "bound, not a reasoned ceiling.")

    def _mine_capex_opex(self, mat):
        """(capex per t/yr to sink, opex per t/yr to run) for standing
        production of `mat` - the curated figure for the seven originally
        tracked metals, unchanged; a generic figure derived from the
        material's own book price (see the class comment above) for
        anything else this file can price at all. (None, None) for a name
        nothing prices - the only way this stays "no such material,"
        rather than an arbitrary string being accepted."""
        if mat in self.MINE_CAPEX_PER_T_YR:
            return self.MINE_CAPEX_PER_T_YR[mat], self.MINE_OPEX_PER_T.get(mat, 0.0)
        price = self._book_price_per_kg(mat)
        if price is None or price <= 0:
            return None, None
        capex = max(self.GENERIC_MINE_CAPEX_FLOOR,
                    min(self.GENERIC_MINE_CAPEX_CEILING,
                        self.GENERIC_MINE_CAPEX_MULTIPLE * price))
        return capex, capex * self.GENERIC_MINE_OPEX_SHARE

    def _mine_capex(self, mat):
        capex, _opex = self._mine_capex_opex(mat)
        return capex

    def _mine_opex(self, mat):
        _capex, opex = self._mine_capex_opex(mat)
        return 0.0 if opex is None else opex

    def mineable(self, mat):
        """Can you sink standing production capacity in this material at
        all? True for the seven curated metals and, generalised, for any
        material key or curated commodity id this file can find a book
        price for - which in practice is anything a node in the tech tree
        actually buys, since every one of those has a prices.json entry by
        construction (data.py's own load() could not have computed
        `_material_cost` otherwise). False only for a name that prices
        nothing at all: a typo, not a real gap."""
        return self._mine_capex(self._normalize_material_name(mat)) is not None

    def mine_catalog_hint(self):
        """What to tell a player who typed a material name this file
        cannot price. Names the seven hand-named metals (see
        COMMODITY_DYNAMISM.md) as well-sourced headline cases, and also
        points at the generic fallback below: not a hard, closed list.
        """
        named = ", ".join(sorted(self.MINE_CAPEX_PER_T_YR))
        return ("well-known workings: %s - or any other material key the "
                "tree uses (for example aluminium_kg), priced from its own "
                "book price if nothing more specific is known about it"
                % named)

    # ---- LAND: what is under your feet is geography, not standing --------
    #
    # open_mine()'s ceiling must not depend only on patronage and state
    # capacity, the SAME number for every material: a founder with an
    # imperial patron could otherwise sink exactly as large a tin mine as
    # an iron one, in a home province with no tin in it at all. Mines are
    # limited by land area and what is actually under it, the same as the
    # market half of supply is. geography.py's mineral_scale() ALREADY
    # answers "how much of this material's national output can THIS
    # civilisation reach," built from geography.json's per-region mineral
    # abundance and this civilization's own home_regions and reach (see
    # its own comment) -- and it already governs the MARKET half of supply
    # (_material_market_tonnes). Reusing it here, rather than inventing a
    # second geology signal, means a civ that
    # cannot buy much tin also cannot simply out-organise its way to
    # unlimited tin by sinking shafts instead -- the same ground is short
    # either way. Measured: a Rome run's mineral_scale sits at roughly
    # 1.0-1.2 for every metal but saltpetre (it controls most of its own
    # ore-bearing provinces); Mexica sits at 0.10-0.17 for iron and coal
    # (Mesoamerica genuinely worked neither) and 0.47 for copper (it did).
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
        times what mining technology currently lets a working pull out of a
        given deposit (mining_tech()'s own yield multiplier -- see its
        comment for why a pump or a railway belongs on THIS side of the
        ledger and not only on cost)."""
        state_capacity = float(self.civ.get("state_capacity", self.STATE_CAPACITY_DEFAULT_FALLBACK))
        if self.running("patron_imperial"):     base = self.MINE_CEILING_BASE_IMPERIAL + self.MINE_CEILING_STATE_SCALE_IMPERIAL * state_capacity
        elif self.running("patron_senatorial"): base = self.MINE_CEILING_BASE_SENATORIAL + self.MINE_CEILING_STATE_SCALE_SENATORIAL * state_capacity
        elif self.has("citizenship"):       base = self.MINE_CEILING_BASE_CITIZEN + self.MINE_CEILING_STATE_SCALE_CITIZEN * state_capacity
        else:                               base = self.MINE_CEILING_BASE_STRANGER + self.MINE_CEILING_STATE_SCALE_STRANGER * state_capacity
        base *= 1.0 + min(self.REVENUE_SCALE_CAP_MULTIPLE, max(0.0, self.revenue()) / self.REVENUE_SCALE_DENARII)
        geo = self.mineral_scale(mat)
        yld, _cost = self.mining_tech(mat)
        return base * geo * yld

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
    MINE_CEILING_BASE_SENATORIAL = declare(
        "MINE_CEILING_BASE_SENATORIAL", 9000.0, kind="temporary_heuristic",
        unit="tonnes/year (base)", source=None, confidence="D",
        why="As MINE_CEILING_BASE_IMPERIAL, for the senatorial-patron tier.")
    MINE_CEILING_STATE_SCALE_SENATORIAL = declare(
        "MINE_CEILING_STATE_SCALE_SENATORIAL", 20000.0, kind="temporary_heuristic",
        unit="tonnes/year per unit of state_capacity", source=None,
        confidence="D",
        why="As MINE_CEILING_STATE_SCALE_IMPERIAL, for the senatorial tier.")
    MINE_CEILING_BASE_CITIZEN = declare(
        "MINE_CEILING_BASE_CITIZEN", 6000.0, kind="temporary_heuristic",
        unit="tonnes/year (base)", source=None, confidence="D",
        why="As MINE_CEILING_BASE_IMPERIAL, for a citizen with no patron.")
    MINE_CEILING_STATE_SCALE_CITIZEN = declare(
        "MINE_CEILING_STATE_SCALE_CITIZEN", 8000.0, kind="temporary_heuristic",
        unit="tonnes/year per unit of state_capacity", source=None,
        confidence="D",
        why="As MINE_CEILING_STATE_SCALE_IMPERIAL, for the citizen tier.")
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
    REVENUE_SCALE_DENARII = declare(
        "REVENUE_SCALE_DENARII", 60000.0, kind="temporary_heuristic",
        unit="denarii/year of revenue for +100% ceiling", source=None,
        confidence="D",
        why="How much annual revenue it takes to double a standing "
            "ceiling via REVENUE_SCALE_CAP_MULTIPLE, reused identically in "
            "forest_land_ceiling() below. Tuned, not derived from any "
            "attested income-to-capacity relationship.")

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
    # (mining_tech(), below) raises that support, which is the whole of
    # "make depletion something you can fight."
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
            working["intensity_yrs"] = working.get("intensity_yrs", 0.0) + working["capacity"] / ceilings[mat]

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
    MINING_TECH_YIELD_MET_MINE_PUMPING = declare(
        "MINING_TECH_YIELD_MET_MINE_PUMPING", 1.4, kind="temporary_heuristic",
        unit="dimensionless multiple on extractable tonnage",
        source=None, confidence="D", why="How much this technology raises what a working can pull from the same deposit ('yield') and lowers the cost of sinking or running a tonne/year of capacity ('cost'). The MECHANISM and its direction are real historical claims, argued in the class comment above (a pump makes flooded ore reachable, blasting breaks rock faster, a railway makes distant ore worth lifting); the SPECIFIC multiplier is an invented, plausible size for that effect, not fitted to any output record for a specific mine or technology.")
    MINING_TECH_COST_MET_MINE_PUMPING = declare(
        "MINING_TECH_COST_MET_MINE_PUMPING", 0.85, kind="temporary_heuristic",
        unit="dimensionless multiple on cost per tonne/year",
        source=None, confidence="D", why="How much this technology raises what a working can pull from the same deposit ('yield') and lowers the cost of sinking or running a tonne/year of capacity ('cost'). The MECHANISM and its direction are real historical claims, argued in the class comment above (a pump makes flooded ore reachable, blasting breaks rock faster, a railway makes distant ore worth lifting); the SPECIFIC multiplier is an invented, plausible size for that effect, not fitted to any output record for a specific mine or technology.")
    # The Newcomen atmospheric engine, built specifically to drain flooding coal
    # and tin workings - a later, stronger tier on the same drainage problem as
    # met_mine_pumping, compounding with it.
    MINING_TECH_YIELD_STEAM_ATMOSPHERIC = declare(
        "MINING_TECH_YIELD_STEAM_ATMOSPHERIC", 1.6, kind="temporary_heuristic",
        unit="dimensionless multiple on extractable tonnage",
        source=None, confidence="D", why="How much this technology raises what a working can pull from the same deposit ('yield') and lowers the cost of sinking or running a tonne/year of capacity ('cost'). The MECHANISM and its direction are real historical claims, argued in the class comment above (a pump makes flooded ore reachable, blasting breaks rock faster, a railway makes distant ore worth lifting); the SPECIFIC multiplier is an invented, plausible size for that effect, not fitted to any output record for a specific mine or technology.")
    MINING_TECH_COST_STEAM_ATMOSPHERIC = declare(
        "MINING_TECH_COST_STEAM_ATMOSPHERIC", 0.65, kind="temporary_heuristic",
        unit="dimensionless multiple on cost per tonne/year",
        source=None, confidence="D", why="How much this technology raises what a working can pull from the same deposit ('yield') and lowers the cost of sinking or running a tonne/year of capacity ('cost'). The MECHANISM and its direction are real historical claims, argued in the class comment above (a pump makes flooded ore reachable, blasting breaks rock faster, a railway makes distant ore worth lifting); the SPECIFIC multiplier is an invented, plausible size for that effect, not fitted to any output record for a specific mine or technology.")
    # Black-powder blasting breaks rock faster per man-hour; it does not put new
    # ore in the ground, so cost only, no yield term.
    MINING_TECH_YIELD_MET_BLACK_POWDER_BLASTING = declare(
        "MINING_TECH_YIELD_MET_BLACK_POWDER_BLASTING", 1.0, kind="temporary_heuristic",
        unit="dimensionless multiple on extractable tonnage",
        source=None, confidence="D", why="How much this technology raises what a working can pull from the same deposit ('yield') and lowers the cost of sinking or running a tonne/year of capacity ('cost'). The MECHANISM and its direction are real historical claims, argued in the class comment above (a pump makes flooded ore reachable, blasting breaks rock faster, a railway makes distant ore worth lifting); the SPECIFIC multiplier is an invented, plausible size for that effect, not fitted to any output record for a specific mine or technology.")
    MINING_TECH_COST_MET_BLACK_POWDER_BLASTING = declare(
        "MINING_TECH_COST_MET_BLACK_POWDER_BLASTING", 0.85, kind="temporary_heuristic",
        unit="dimensionless multiple on cost per tonne/year",
        source=None, confidence="D", why="How much this technology raises what a working can pull from the same deposit ('yield') and lowers the cost of sinking or running a tonne/year of capacity ('cost'). The MECHANISM and its direction are real historical claims, argued in the class comment above (a pump makes flooded ore reachable, blasting breaks rock faster, a railway makes distant ore worth lifting); the SPECIFIC multiplier is an invented, plausible size for that effect, not fitted to any output record for a specific mine or technology.")
    # Dynamite blasting, a stronger version of the same black-powder effect; cost
    # only, no yield term.
    MINING_TECH_YIELD_MET_DYNAMITE_BLASTING = declare(
        "MINING_TECH_YIELD_MET_DYNAMITE_BLASTING", 1.0, kind="temporary_heuristic",
        unit="dimensionless multiple on extractable tonnage",
        source=None, confidence="D", why="How much this technology raises what a working can pull from the same deposit ('yield') and lowers the cost of sinking or running a tonne/year of capacity ('cost'). The MECHANISM and its direction are real historical claims, argued in the class comment above (a pump makes flooded ore reachable, blasting breaks rock faster, a railway makes distant ore worth lifting); the SPECIFIC multiplier is an invented, plausible size for that effect, not fitted to any output record for a specific mine or technology.")
    MINING_TECH_COST_MET_DYNAMITE_BLASTING = declare(
        "MINING_TECH_COST_MET_DYNAMITE_BLASTING", 0.65, kind="temporary_heuristic",
        unit="dimensionless multiple on cost per tonne/year",
        source=None, confidence="D", why="How much this technology raises what a working can pull from the same deposit ('yield') and lowers the cost of sinking or running a tonne/year of capacity ('cost'). The MECHANISM and its direction are real historical claims, argued in the class comment above (a pump makes flooded ore reachable, blasting breaks rock faster, a railway makes distant ore worth lifting); the SPECIFIC multiplier is an invented, plausible size for that effect, not fitted to any output record for a specific mine or technology.")
    # Rotary drilling speeds face advance; cost only, no yield term, the same
    # reasoning as blasting.
    MINING_TECH_YIELD_PWR_ROTARY_DRILLING = declare(
        "MINING_TECH_YIELD_PWR_ROTARY_DRILLING", 1.0, kind="temporary_heuristic",
        unit="dimensionless multiple on extractable tonnage",
        source=None, confidence="D", why="How much this technology raises what a working can pull from the same deposit ('yield') and lowers the cost of sinking or running a tonne/year of capacity ('cost'). The MECHANISM and its direction are real historical claims, argued in the class comment above (a pump makes flooded ore reachable, blasting breaks rock faster, a railway makes distant ore worth lifting); the SPECIFIC multiplier is an invented, plausible size for that effect, not fitted to any output record for a specific mine or technology.")
    MINING_TECH_COST_PWR_ROTARY_DRILLING = declare(
        "MINING_TECH_COST_PWR_ROTARY_DRILLING", 0.8, kind="temporary_heuristic",
        unit="dimensionless multiple on cost per tonne/year",
        source=None, confidence="D", why="How much this technology raises what a working can pull from the same deposit ('yield') and lowers the cost of sinking or running a tonne/year of capacity ('cost'). The MECHANISM and its direction are real historical claims, argued in the class comment above (a pump makes flooded ore reachable, blasting breaks rock faster, a railway makes distant ore worth lifting); the SPECIFIC multiplier is an invented, plausible size for that effect, not fitted to any output record for a specific mine or technology.")
    # A railway creates REACH, not extraction efficiency: ore too far from a
    # market to be worth carting becomes worth lifting once a railway can move it
    # - a yield (economically-reachable tonnage) effect, not a per-tonne cost
    # effect, reused from goods_reach_factor()'s own self.running("railway")
    # check.
    MINING_TECH_YIELD_RAILWAY = declare(
        "MINING_TECH_YIELD_RAILWAY", 1.3, kind="temporary_heuristic",
        unit="dimensionless multiple on extractable tonnage",
        source=None, confidence="D", why="How much this technology raises what a working can pull from the same deposit ('yield') and lowers the cost of sinking or running a tonne/year of capacity ('cost'). The MECHANISM and its direction are real historical claims, argued in the class comment above (a pump makes flooded ore reachable, blasting breaks rock faster, a railway makes distant ore worth lifting); the SPECIFIC multiplier is an invented, plausible size for that effect, not fitted to any output record for a specific mine or technology.")
    MINING_TECH_COST_RAILWAY = declare(
        "MINING_TECH_COST_RAILWAY", 1.0, kind="temporary_heuristic",
        unit="dimensionless multiple on cost per tonne/year",
        source=None, confidence="D", why="How much this technology raises what a working can pull from the same deposit ('yield') and lowers the cost of sinking or running a tonne/year of capacity ('cost'). The MECHANISM and its direction are real historical claims, argued in the class comment above (a pump makes flooded ore reachable, blasting breaks rock faster, a railway makes distant ore worth lifting); the SPECIFIC multiplier is an invented, plausible size for that effect, not fitted to any output record for a specific mine or technology.")
    MINING_TECH = {
        'met_mine_pumping': {"yield": MINING_TECH_YIELD_MET_MINE_PUMPING, "cost": MINING_TECH_COST_MET_MINE_PUMPING},
        'steam_atmospheric': {"yield": MINING_TECH_YIELD_STEAM_ATMOSPHERIC, "cost": MINING_TECH_COST_STEAM_ATMOSPHERIC},
        'met_black_powder_blasting': {"yield": MINING_TECH_YIELD_MET_BLACK_POWDER_BLASTING, "cost": MINING_TECH_COST_MET_BLACK_POWDER_BLASTING},
        'met_dynamite_blasting': {"yield": MINING_TECH_YIELD_MET_DYNAMITE_BLASTING, "cost": MINING_TECH_COST_MET_DYNAMITE_BLASTING},
        'pwr_rotary_drilling': {"yield": MINING_TECH_YIELD_PWR_ROTARY_DRILLING, "cost": MINING_TECH_COST_PWR_ROTARY_DRILLING},
        'railway': {"yield": MINING_TECH_YIELD_RAILWAY, "cost": MINING_TECH_COST_RAILWAY},
    }
    # The first step of cheap steel making low-grade ore worth digging - iron did
    # not change how ore comes out of the ground, it changed whether digging it
    # was worth doing at all (see the class comment above); for coal, the same
    # entry represents a cheap-steel industry becoming a coking-coal customer
    # large enough to justify the pit, drainage and rail spur a smaller demand
    # would not.
    MINING_TECH_STEEL_YIELD_BLAST_FURNACE = declare(
        "MINING_TECH_STEEL_YIELD_BLAST_FURNACE", 1.3, kind="temporary_heuristic",
        unit="dimensionless multiple on extractable tonnage",
        source=None, confidence="D", why="How much this technology raises what a working can pull from the same deposit ('yield') and lowers the cost of sinking or running a tonne/year of capacity ('cost'). The MECHANISM and its direction are real historical claims, argued in the class comment above (a pump makes flooded ore reachable, blasting breaks rock faster, a railway makes distant ore worth lifting); the SPECIFIC multiplier is an invented, plausible size for that effect, not fitted to any output record for a specific mine or technology.")
    MINING_TECH_STEEL_COST_BLAST_FURNACE = declare(
        "MINING_TECH_STEEL_COST_BLAST_FURNACE", 0.85, kind="temporary_heuristic",
        unit="dimensionless multiple on cost per tonne/year",
        source=None, confidence="D", why="How much this technology raises what a working can pull from the same deposit ('yield') and lowers the cost of sinking or running a tonne/year of capacity ('cost'). The MECHANISM and its direction are real historical claims, argued in the class comment above (a pump makes flooded ore reachable, blasting breaks rock faster, a railway makes distant ore worth lifting); the SPECIFIC multiplier is an invented, plausible size for that effect, not fitted to any output record for a specific mine or technology.")
    # Bessemer/open-hearth bulk steel, the second and further step of the same
    # effect as blast_furnace, further from ore than the last.
    MINING_TECH_STEEL_YIELD_MAT_BULK_STEEL = declare(
        "MINING_TECH_STEEL_YIELD_MAT_BULK_STEEL", 1.3, kind="temporary_heuristic",
        unit="dimensionless multiple on extractable tonnage",
        source=None, confidence="D", why="How much this technology raises what a working can pull from the same deposit ('yield') and lowers the cost of sinking or running a tonne/year of capacity ('cost'). The MECHANISM and its direction are real historical claims, argued in the class comment above (a pump makes flooded ore reachable, blasting breaks rock faster, a railway makes distant ore worth lifting); the SPECIFIC multiplier is an invented, plausible size for that effect, not fitted to any output record for a specific mine or technology.")
    MINING_TECH_STEEL_COST_MAT_BULK_STEEL = declare(
        "MINING_TECH_STEEL_COST_MAT_BULK_STEEL", 0.75, kind="temporary_heuristic",
        unit="dimensionless multiple on cost per tonne/year",
        source=None, confidence="D", why="How much this technology raises what a working can pull from the same deposit ('yield') and lowers the cost of sinking or running a tonne/year of capacity ('cost'). The MECHANISM and its direction are real historical claims, argued in the class comment above (a pump makes flooded ore reachable, blasting breaks rock faster, a railway makes distant ore worth lifting); the SPECIFIC multiplier is an invented, plausible size for that effect, not fitted to any output record for a specific mine or technology.")
    MINING_TECH_STEEL = {
        'blast_furnace': {"yield": MINING_TECH_STEEL_YIELD_BLAST_FURNACE, "cost": MINING_TECH_STEEL_COST_BLAST_FURNACE},
        'mat_bulk_steel': {"yield": MINING_TECH_STEEL_YIELD_MAT_BULK_STEEL, "cost": MINING_TECH_STEEL_COST_MAT_BULK_STEEL},
    }

    def mining_tech(self, mat):
        """(yield_mult, cost_mult) technology has bought this material's
        mining so far. yield_mult >= 1 raises what a working can pull out
        of the same deposit; cost_mult <= 1 lowers what getting it out
        costs. Capped/floored like every other compounding factor in this
        file (MARKET_SHARE, goods_reach_factor): a mine at three times the
        book yield is a real historical claim, thirty times is the
        abolished unobtainable category with its sign flipped."""
        yield_mult, cost_mult = 1.0, 1.0
        techs = self.MINING_TECH
        if mat in ("iron", "coal"):
            techs = dict(techs, **self.MINING_TECH_STEEL)
        for node in sorted(techs):
            if self.running(node):
                yield_mult *= techs[node]["yield"]
                cost_mult *= techs[node]["cost"]
        return min(yield_mult, self.MINING_TECH_YIELD_CEILING), max(self.MINING_TECH_COST_FLOOR, cost_mult)

    MINING_TECH_YIELD_CEILING = declare(
        "MINING_TECH_YIELD_CEILING", 3.0, kind="temporary_heuristic",
        unit="dimensionless multiple on extractable tonnage (maximum)",
        source=None, confidence="D",
        why="Cap on how far compounding every mining technology together "
            "can raise a deposit's yield - a mine at three times book "
            "yield is a real historical claim, per this method's own "
            "docstring; the specific ceiling is a defensive bound against "
            "the abolished 'unobtainable' category's mirror image, not a "
            "derived limit.")
    MINING_TECH_COST_FLOOR = declare(
        "MINING_TECH_COST_FLOOR", 0.35, kind="temporary_heuristic",
        unit="dimensionless multiple on cost per tonne/year (minimum)",
        source=None, confidence="D",
        why="Floor on how far compounding technology can cheapen mining - "
            "technology helps, but extraction is never free. A defensive "
            "bound, not a derived limit.")

    def mining_cost_scale(self, mat):
        """What sinking or running a tonne/yr of this material costs THIS
        YEAR, relative to MINE_CAPEX_PER_T_YR/MINE_OPEX_PER_T's own book
        price: technology (mining_tech's cost multiplier) against depletion
        (mine_depletion_factor, inverted -- the same effort recovers less
        from a half-worked deposit, so it costs proportionally more per
        tonne) pulling against each other. This is "deeper ones cost more"
        made concrete, and technology is the only thing that pushes back.
        Bounded to keep the tension a real decision rather than a runaway:
        a fully depleted, untooled working costs at most 2x book (not
        infinite), and full mining technology on a fresh deposit costs no
        less than 0.4x (not free)."""
        _year, cost = self.mining_tech(mat)
        return max(self.MINING_COST_SCALE_FLOOR,
                   min(self.MINING_COST_SCALE_CEILING, cost / self.mine_depletion_factor(mat)))

    def mining_cost_scale_for(self, working):
        """Same as mining_cost_scale(), but for what running THIS working
        costs this year, from ITS OWN depletion rather than its material's
        average - an old, half-worked shaft costs more per tonne to keep
        running than a fresh one of the same material, which the old
        material-level figure could not say because it had no idea which
        working was which."""
        _year, cost = self.mining_tech(working["material"])
        return max(self.MINING_COST_SCALE_FLOOR,
                   min(self.MINING_COST_SCALE_CEILING, cost / self.mine_depletion_factor_for(working)))

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
        OWN depletion and current mining technology."""
        yld, _cost = self.mining_tech(working["material"])
        return working["capacity"] * self.mine_depletion_factor_for(working) * yld

    def mine_operating_cost_for(self, working):
        """What THIS working costs to run this year, whether or not you use
        what it raises - mine_operating_cost()'s per-working figure, the one
        `mines` shows against each row."""
        mat = working["material"]
        return (working["capacity"] * self._mine_opex(mat) * self.price_index
                * self.mining_cost_scale_for(working))

    def mine_quote(self, mat, t_per_yr):
        """What a mine would cost, BEFORE you commit to it.

        Every other purchase in this game quotes before it charges, and a
        mine opened sight-unseen can sink far more than expected with no
        price shown and no way to ask beforehand.
        """
        mat = self._normalize_material_name(mat)
        cap, opex_per_t = self._mine_capex_opex(mat)
        if cap is None:
            return None
        tonnes = max(0.0, float(t_per_yr))
        scale = self.mining_cost_scale(mat)
        sink = tonnes * cap * self.price_index * scale
        opex = tonnes * opex_per_t * self.price_index * scale
        ceiling = self.mine_land_ceiling(mat)
        economy = self.state.economy
        household = self.state.household
        room = max(0.0, ceiling - self.mine_capacity.get(mat, 0.0)
                   - economy.mine_pending.get(mat, 0.0))
        depl = self.mine_depletion_factor(mat)
        note = ("The yearly cost is charged whether or not you use the "
                "output, and goes on until you close it. Mothballing is "
                "not free to reverse: the shaft floods and the crew "
                "disperses, so reopening means sinking it again.")
        if scale > 1.05:
            note += (" This costs %.0f%% of the book price: the easy ore "
                      "here is going, and nothing you have built yet cuts "
                      "the cost of getting at what is left (mine pumping, "
                      "blasting, or a railway would)." % (scale * 100))
        elif scale < 0.95:
            note += (" This costs %.0f%% of the book price: what you have "
                      "built has made this cheaper to get out of the "
                      "ground." % (scale * 100))
        return {"material": mat,
                "tonnes_per_year": round(tonnes, 3),
                "to_sink_it": round(sink, 1),
                "every_year_it_stands": round(opex, 1),
                "years_before_it_produces": self.MINE_LEAD_YEARS,
                "you_have": round(household.capital, 1),
                "you_could_raise": round(self.spending_power("buy"), 1),
                "you_can_afford_about": round(
                    self.spending_power("buy") / max(cap * self.price_index * scale, 1e-9), 3),
                "afford_means": "cash plus half the credit line, which is what "
                                "a lender will advance against a purchase",
                "the_ground_here_could_ever_support": round(ceiling, 1),
                "room_left_before_geology_stops_you": round(room, 1),
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

    def _mine_depletion_note_from(self, depl, yld):
        """Shared sentence-builder behind mine_depletion_note() (a
        material's average) and mine_depletion_note_for() (one working's
        own figures) - the same wording either way, just fed a different
        depletion fraction."""
        if abs(depl - 1.0) < 0.01 and abs(yld - 1.0) < 0.01:
            return None
        bits = []
        if depl < 0.999:
            bits.append("the easy ore here is %d%% worked out, so the same "
                        "shaft yields %d%% of its first-year tonnage"
                        % (round((1.0 - depl) * 100), round(depl * 100)))
        if yld > 1.001:
            bits.append("technology you have built raises that back up "
                        "%.1fx" % yld)
        elif depl < 0.999:
            bits.append("mine pumping, drilling or blasting would raise it "
                        "back up")
        return "; ".join(bits)

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
        yld, _cost = self.mining_tech(mat)
        return self._mine_depletion_note_from(self.mine_depletion_factor(mat), yld)

    def mine_depletion_note_for(self, working):
        """mine_depletion_note(), for one working's OWN depletion rather
        than its material's average across every working of it - the
        figure the `mines` row for this specific working should explain."""
        yld, _cost = self.mining_tech(working["material"])
        return self._mine_depletion_note_from(
            self.mine_depletion_factor_for(working), yld)

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
        economy = self.state.economy
        household = self.state.household
        scenario = self.state.scenario
        economy.mines = [working for working in (economy.mines or [])
                         if working.get("material") != mat]
        economy.mine_tranches = [tranche for tranche in (economy.mine_tranches or [])
                                 if tranche[0] != mat]
        household.log.append((scenario.year, "you close the %s workings" % mat))
        return True, ("the %s workings are closed. You stop paying %.0f a year. "
                      "What you spent sinking them is gone, and reopening means "
                      "sinking them again." % (mat, saved))

    def open_mine(self, mat, t_per_yr, partial=True):
        """Open your own workings.

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
        economy = self.state.economy
        household = self.state.household
        scenario = self.state.scenario
        t_per_yr = min(t_per_yr, max(0.0, ceiling - have_cap.get(mat, 0.0)
                                          - economy.mine_pending.get(mat, 0.0)))
        if t_per_yr <= 0:
            return 0.0
        # DEEPER ONES COST MORE. mining_cost_scale() is 1.0 on a fresh
        # deposit with no relevant technology, so this changes nothing for
        # an early game; it rises as a deposit already worked hard is asked
        # for more, and falls back down with mine pumping, drilling,
        # blasting or a railway -- see that method's own comment.
        scale = self.mining_cost_scale(mat)
        cost = t_per_yr * cap * self.price_index * scale
        if cost > household.capital:
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
            t_per_yr = household.capital / (cap * self.price_index * scale)
            cost = household.capital
        if t_per_yr <= 0:
            return 0.0
        household.capital -= cost
        # Each investment is its own working with its own sinking time.
        # Pooling them and taking the LATEST ready date would mean a
        # player who invests spare cash every year, which is exactly what
        # a poor civilization must do, pushes the finish line back
        # annually and never gets any capacity at all. It also means each tranche becomes its own
        # WORKING once it commissions (see commission_mines) rather than
        # being folded into one number for the material - `cost` is carried
        # along so that working can say what it actually cost to sink, not
        # a figure recomputed later against a price_index that has since moved.
        if economy.mine_tranches is None:
            economy.mine_tranches = []
        economy.mine_tranches.append([mat, t_per_yr, scenario.year + self.MINE_LEAD_YEARS, cost])
        economy.mine_pending[mat] = economy.mine_pending.get(mat, 0.0) + t_per_yr
        return t_per_yr

    def commission_mines(self):
        """Move finished tranches from pending into standing workings
        (self.state.economy.mines), tranche by tranche. Each tranche becomes exactly one
        working, commissioned in the year it actually came on stream (the
        tranche's own `ready` year, which is when its own depletion clock
        starts - see _advance_mine_depletion) - not merged into any other
        working of the same material, so a shaft opened in year 400 stays
        a distinct, unworn thing next to one opened three centuries before
        it."""
        economy = self.state.economy
        scenario = self.state.scenario
        if economy.mines is None:
            economy.mines = []
        still = []
        for tranche in (economy.mine_tranches or []):
            mat, amount, ready = tranche[0], tranche[1], tranche[2]
            # capex_paid: absent on a tranche written by a save from before
            # this field existed (see SAVE_FIELDS/load_state) - honestly
            # unknown, not fabricated, so 0.0 rather than a guess.
            capex_paid = tranche[3] if len(tranche) > 3 else 0.0
            if scenario.year >= ready:
                economy.mines.append({"material": mat, "capacity": amount,
                                   "opened_year": ready, "capex_paid": capex_paid,
                                   "intensity_yrs": 0.0})
                economy.mine_pending[mat] = max(0.0, economy.mine_pending.get(mat, 0.0) - amount)
                if economy.mine_pending.get(mat, 0.0) <= 0:
                    economy.mine_pending.pop(mat, None)
            else:
                still.append(tranche)
        economy.mine_tranches = still
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
        economy = self.state.economy
        scenario = self.state.scenario
        order = sorted(self.mine_capacity, key=lambda material: -self._mine_opex(material))
        for material in order:
            if household.capital >= 0:
                break
            kept = []
            for working in self._workings_of(material):
                cut = working["capacity"] * self.MOTHBALL_CUT_SHARE
                household.add_capital(cut * self._mine_opex(material) * self.price_index)
                working["capacity"] -= cut
                if working["capacity"] >= 1.0:
                    kept.append(working)
            economy.mines = [working for working in (economy.mines or [])
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
    # Land bounds woodland too, not only mines. geography.json carries no
    # per-region forest figure to read the way minerals has one, so this is
    # built from the signal that IS there: how much GROUND you actually hold
    # and how good your state is at organising land tenure at all
    # (state_capacity) -- a coppice is not a metalla, so no imperial
    # concession gates it, but fencing off and managing a woodland at scale
    # still takes an administration capable of holding the tenure.
    #
    # KEYED ON AREA (geography.json's own `land.land_area_km2` per home
    # region - see home_land_area_km2() below), NOT ON A COUNT OF REGION
    # LABELS (len(home_regions)): Complaint 46 names the same failure here
    # that it names for rent - a region is a filing label, not a unit of
    # area, and the labels range 86x in size (americas_north 19.8M km2
    # down to britannia's 230,000 -- data/world/geography.json). Keying
    # this on label count would let re-filing Rome's SAME seven regions
    # as, say, fourteen tiles double its woodland ceiling with no forest
    # gaining or losing a single hectare, while Han China's one enormous
    # but singular region (9.6M km2, bigger than Rome's whole seven put
    # together) would price out at less than a seventh of Rome's ceiling
    # for holding MORE ground - the map's filing system leaking into the
    # economics, exactly as Complaint 46 describes for rent.
    #
    # [C], sized against the one real anchor available: resources.json's
    # empire-wide 500,000 t/yr of charcoal implies roughly 667,000 ha under
    # management across the WHOLE Roman world (at CHARCOAL_PER_HA=0.75
    # t/ha/yr); Rome's own ceiling below tops out around 190,000 ha even at
    # full revenue-driven scale-up, comfortably under that -- no private
    # holding should rival the entire empire's own managed woodland. The
    # per-area rate is re-derived from that SAME anchor, using Rome's own
    # home land area (9.5175 million km2, from geography.json) as the one
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
        "regions, data/world/geography.json) as the calibration point, so "
        "that Rome's own pre-revenue ceiling is essentially unchanged by "
        "the switch from counting labels to reading area.",
        confidence="C",
        why="Base standing-woodland ceiling per million km2 of home land "
            "held, before state capacity is applied. geography.json carries "
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
        """Total land area, in km2, of this civilization's own home_regions --
        read from geography.json's per-region `land.land_area_km2`, not
        counted by how many region labels that ground happens to be filed
        under (see forest_land_ceiling()'s own comment for why the count
        was wrong). Falls back to Italia's area, the same fallback
        _compute_home_centroid() uses for a civ file with no valid
        home_regions at all, so this never divides by zero or crashes on a
        malformed civ file."""
        home = [region_id for region_id in (self.civ.get("home_regions") or []) if region_id in self._regions]
        area = sum(float((self._regions[region_id].get("land") or {}).get("land_area_km2", 0.0))
                   for region_id in home)
        if area > 0.0:
            return area
        fallback = self._regions.get("italia") or next(iter(self._regions.values()), {})
        return float((fallback.get("land") or {}).get("land_area_km2", 0.0)) or 1.0

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
        economy = self.state.economy
        household = self.state.household
        scenario = self.state.scenario
        room = max(0.0, self.forest_land_ceiling() - economy.forest_ha)
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
        if cost > household.capital:
            return 0.0
        household.capital -= cost
        economy.forest_ha += hectares
        return hectares
