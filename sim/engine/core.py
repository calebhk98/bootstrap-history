"""The simulation itself: what one year does, and the loop over years."""
import collections, json, math, os, random, sys

from constants import declare
from .data import *          # the shared tables and loaders
from .data import (ANNUAL_WAGE, DEFAULTS, WAGES, load_civ, load_geography,
                   load_resources, trade_family)

# sim/world/demography.py imports `sim.constants` fully-qualified (see that
# module's own header), which only resolves if the REPOSITORY ROOT is on
# sys.path so `sim` itself is importable as a namespace package (it has no
# __init__.py - see sim/test_regressions.py's own comment on that). Whatever
# put `sim/` itself on sys.path (simulator.py, cli.py, or sim/tests/harness.py
# for the test suite) does not also add the repository root, so this file
# adds it itself rather than relying on the entry point to have done so -
# see docs/architecture/WIRING_MILESTONE_4.md SS6, Commit 1, for why a bare
# `from ..world import demography` fails outright: this module loads as
# top-level `engine.core`, not `sim.engine.core` (`engine` has no parent
# package under simulator.py's existing sys.path scheme), so a leading `..`
# has nowhere to go. Guarded and deduplicated, the same pattern
# sim/test_regressions.py already uses for its own `_ROOT`.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
# Bare, not `sim.world.demography` - matching this package's own existing
# style (`from constants import declare` above, not `from ..constants`),
# and relying on `sim/` itself already being on sys.path by the time this
# module loads (true for every real entry point today).
from world import demography
# WIRING MILESTONE 4's parallel track (docs/architecture/WIRING_MILESTONE_4.md
# SS6, "Agriculture wiring is a parallel track"): `sim/world/agriculture.py`'s
# land/labour/weather harvest model, imported the same bare, same-sys.path
# way as demography just above.
from world import agriculture
# WIRING TWO (Complaints/47-one-weather-draw-for-a-continent.md): READ ONLY.
# This file does not own sim/world/land.py (see this task's own brief) and
# changes nothing in it - `cultivable_land_for_civilization` is called
# exactly the way `demography`/`agriculture` above already are, as a
# pre-existing module this engine reads from rather than a mechanism this
# wiring invents. What it is used for: each home region's SHARE of this
# civilisation's cultivable land, so a weather draw can be pooled across
# regions weighted by how much land each one actually holds, rather than
# by an unweighted headcount of regions (see _compute_farm_region_weights).
from world import land


from .economy import EconomyMixin
from .fog import FogMixin
from .geography import GeographyMixin
from .labour import LabourMixin
from .projects import ProjectsMixin
from .society import SocietyMixin
from .actors import Household


class Sim(EconomyMixin, FogMixin, GeographyMixin, LabourMixin,
          ProjectsMixin, SocietyMixin):
    STATE_CAPACITY_DEFAULT = declare(
        "STATE_CAPACITY_DEFAULT", 0.7, kind="temporary_heuristic",
        unit="dimensionless (0..1)", source=None, confidence="D",
        why="Fallback state_capacity for a civilisation file that does not "
            "set its own - every shipped civ file does set one, so this "
            "only matters for one that omits it. A mid-high default so a "
            "missing field does not silently cripple every state-notice "
            "mechanic; not fitted to any specific state.")
    DEFAULT_POPULATION_100AD = declare(
        "DEFAULT_POPULATION_100AD", 65e6, kind="initial_condition",
        unit="people", source="Widely cited estimate of the Roman Empire's "
             "population around 100 AD.",
        confidence="C",
        why="Fallback starting population, and the reference population "
            "pop_scale=1.0 is defined against, for a civilisation file "
            "that does not set its own `population` field. Every shipped "
            "civ file does set one; this is the scenario's own initial "
            "condition, not a tuned game-balance number.")
    FOUNDER_MIN_REMAINING_LIFE_YEARS = declare(
        "FOUNDER_MIN_REMAINING_LIFE_YEARS", 5, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="Floor on the founder's gaussian-drawn remaining lifespan, so "
            "an unlucky draw does not end a run in its first years before "
            "anything is possible. Round guard value, not a mortality "
            "estimate.")
    POP_SCALE_FLOOR = declare(
        "POP_SCALE_FLOOR", 0.05, kind="temporary_heuristic",
        unit="dimensionless (minimum pop_scale)", source=None,
        confidence="D",
        why="Floor under pop_scale so a tiny starting civilisation "
            "population never divides a formula by something vanishingly "
            "small. Guard value, not a demographic claim.")

    # WIRING ONE (Complaints/48-technology-cannot-stop-people-dying-young.md):
    # the eight _TECH_EFFECTS.json entries whose `population` weight is a
    # DISEASE effect rather than a FOOD one, and so are the only entries
    # `_disease_burden` below is allowed to sum. _TECH_EFFECTS.json also
    # carries a `population` field on crop_rotation, fud_three_field_
    # rotation, fud_seed_drill, mat_newworld_crops and ag2_canning - all
    # five are calories reaching more mouths, not fewer infections, and
    # summing them into a disease-burden calculation would be exactly the
    # mistake the stakeholder's own brief warns against. This selection
    # (which of _TECH_EFFECTS.json's `population` entries counts as
    # "medical") is a classification a human made when writing that file,
    # not something this engine derives - it is reused here, not invented.
    # NOT a `declare()`d constant: it is a set of node ids, not a physical
    # quantity or a tuned parameter.
    DISEASE_BURDEN_TECH_IDS = (
        "germ_theory", "sanitation_antisepsis", "med_aqueducts_latrines",
        "med_quarantine_sanitation", "med_vector_control",
        "med_obstetric_antisepsis", "med_asepsis_antisepsis",
        "med_vaccination_progression",
    )

    def __init__(self, nodes, order, rng, events=True, cfg=None, verbose=False,
                 bounty_set=None, civ=None, manual=False):
        self.nodes = nodes
        # PRECOMPUTED ONCE: which node ids carry a `win_condition` at all,
        # sorted for the same reproducibility reason _check_win_conditions
        # (below) needs a fixed order. self.nodes is the loaded tech tree -
        # assigned exactly once, right here, and never reassigned or mutated
        # (checked: `grep -rn "self\.nodes\[.*\]\[.*\] *="` across every file
        # in this package turns up nothing, and every other write of
        # `self.nodes` anywhere is a *different* class's unrelated attribute
        # of the same name in commodities.py's CommodityLedger). So a node's
        # win_condition membership can never change after this point, and
        # this list can be built once here rather than every single year:
        # _check_win_conditions used to do `for k in sorted(self.nodes)`,
        # re-sorting all ~2,849 node ids from scratch every year to reach
        # the handful that actually carry a win_condition.
        self._win_condition_keys = sorted(
            node_id for node_id, node in nodes.items() if node.get("win_condition"))
        self.order = list(order)
        self.rng = rng
        self.events = events
        self.cfg = dict(DEFAULTS, **(cfg or {}))
        self.verbose = verbose
        self.bounty_set = set(bounty_set or ())
        self.civ = civ or load_civ()
        # MANUAL MODE: the optimizer in step() 4b never starts anything on its
        # own. The only projects that ever become active are ones something
        # called start_project() on, i.e. a human or an agent choosing them.
        # See the comment on step() 4b and on start_project() for why this
        # exists: without it, "choosing" a node in `play` was cosmetic.
        self.manual = bool(manual)
        self.w = self.civ["values"]
        # A civilization brings its own date, its own price level and its own
        # capacity to fund things. Norse Scandinavia does not start in 100 AD.
        self.cfg["start_year"] = int(self.civ.get("year", self.cfg["start_year"]))
        self.price_index = float(self.civ.get("price_index", 1.0))
        self._wage_index_base = float(self.civ.get("wage_index", 1.0))
        self.state_capacity = float(self.civ.get("state_capacity", self.STATE_CAPACITY_DEFAULT))
        # A PLAGUE IS A HIT TO THE WHOLE LABOUR MARKET, NOT ONLY TO YOU. A
        # playtester watched the Black Death take a third of their own staff
        # and nothing else happen to the world around them, and asked why a
        # mortality event this size left everybody ELSE's wages untouched.
        # self._pop_scale_base is this civilisation's OWN trend size - its
        # configured population against the same 65,000,000 reference every
        # downstream formula was calibrated to (see pop_scale's own comment
        # below) - nudged upward over time by population-raising technology
        # and food-diffusion (apply_tech_effects/_advance_food_diffusion_
        # population, society.py). Those two write sites do not yet feed
        # self.population itself (Commit 4's own open question - see
        # docs/architecture/WIRING_MILESTONE_4.md SS1.3), so nothing reads
        # this attribute back in Commit 3 - see wage_index's own comment for
        # why it deliberately does NOT compare against this mutable value.
        # self.pop_scale itself (read everywhere else in the engine) is a
        # COMPUTED PROPERTY off self.population, not stored here - see
        # WIRING MILESTONE 4, COMMIT 3 below for why: a staff_loss hazard in
        # _shocks() (society.py) now cuts self.population's cohorts directly
        # instead of touching a scalar deficit.
        self._pop_scale_base = max(
            self.POP_SCALE_FLOOR,
            float(self.civ.get("population", self.DEFAULT_POPULATION_100AD))
            / self.DEFAULT_POPULATION_100AD)
        # WIRING MILESTONE 4 (docs/architecture/WIRING_MILESTONE_4.md SS6): an
        # age-cohort population, built and proven standalone in
        # sim/world/demography.py. Commit 1 only constructed this and read it
        # nowhere else (provably inert - a scenario run before and after that
        # commit alone came back byte-identical under sim/perf_fingerprint.py);
        # Commit 3 is what made pop_scale/wage_index (below) and _shocks()
        # (society.py) actually read and mutate it, which is expected to move
        # every fingerprint scenario from year index 0 - see WIRING_MILESTONE_
        # 4.md SS5 for why that is the predicted, correct result rather than a
        # regression. `Population.stationary()` finds the model's OWN stable
        # age structure for a population of this civilisation's configured
        # size, rather than an independently invented split - see that
        # method's own docstring for why.
        #
        # SEEDED, DELIBERATELY NOT FROM self.rng: Population owns its own
        # generator (for the `jitter=True` path only - see demography.py's
        # NUTRITION_YEAR_TO_YEAR_NOISE_STD), and nothing in this engine ever
        # passes jitter=True (see _advance_population below), so this seed
        # never actually gets drawn from. It is derived from the
        # civilisation's own id, not Python's randomised string hash() (which
        # would depend on PYTHONHASHSEED and break determinism across
        # processes), purely so two civilisations do not happen to share one.
        _population_seed = sum((index + 1) * ord(character) for index, character
                               in enumerate(str(self.civ.get("id", "civ")))) % (2 ** 32)
        self.population = demography.Population.stationary(
            float(self.civ.get("population", self.DEFAULT_POPULATION_100AD)),
            seed=_population_seed)
        # WIRING MILESTONE 4'S OTHER HALF (docs/architecture/
        # WIRING_MILESTONE_4.md SS6, "Agriculture wiring is a parallel
        # track"): how much arable land this civilisation starts with.
        # `agriculture.farmland_for_population` sizes a `Land` so that, at
        # DEFAULT crop/soil/rotation/toolkit and an AVERAGE weather year,
        # the farm workforce that fraction implies can feed exactly this
        # starting population - i.e. the civilisation starts neither
        # land-rich nor land-starved, which is the only starting point that
        # does not itself hand a fresh run a scripted feast or a scripted
        # famine. This is an INITIAL CONDITION (how much land is already
        # cleared and worked - CLAUDE.md SS3.1's own allowed category,
        # alongside the starting population above), not a result computed
        # from anything the game measures: `farm_land.hectares` is fixed
        # for the life of a run, exactly like `_pop_scale_base`'s reference
        # denominator above, and needs no SAVE_FIELDS entry for the same
        # reason - `Sim.__init__` recomputes it identically, from
        # `self.civ`'s own unchanging config, on every construction,
        # before `load_state` (if any) runs. See `_demographic_recovery`
        # for the one thing this initial condition deliberately does NOT
        # do: grow as the population does. A civilisation whose population
        # outgrows this fixed endowment gets LESS food per head over time
        # from ordinary diminishing returns to labour on fixed land (see
        # agriculture.py's `gross_harvest_kg`), not from any mechanism
        # added here - the extensive margin (bringing more land under the
        # plough) is real future work agriculture.py's own docstring names
        # as missing mechanism (b), not something invented in this file.
        self.farm_land = agriculture.farmland_for_population(
            self._adult_equivalent_population(self.population))
        # WIRING TWO (Complaints/47-one-weather-draw-for-a-continent.md): each
        # home region this civilisation holds gets its OWN weather draw
        # (`_demographic_recovery` below), pooled weighted by that region's
        # own share of the cultivable land - see `_compute_farm_region_
        # weights`'s own docstring. Precomputed ONCE here, not every year:
        # `home_regions` and each region's `arable_iugera` are both fixed
        # for the life of a run (the same reasoning `farm_land` just above
        # is precomputed for), so recomputing this every
        # `_demographic_recovery` call would rebuild the identical list 100
        # times over a century for nothing. Needs no SAVE_FIELDS entry for
        # the same reason `farm_land` needs none: `Sim.__init__`
        # reconstructs it identically, from `self.civ`'s own unchanging
        # `home_regions`, on every construction, before `load_state` runs.
        self._farm_region_weights = self._compute_farm_region_weights()
        # THE GRANARY (Complaints/45-no-granary-so-the-baseline-collapses.md).
        # Started at zero, not at some invented reserve: this is an INITIAL
        # CONDITION (CLAUDE.md SS3.1's own allowed category, same as
        # `farm_land` just above), and the honest initial condition for "how
        # much surplus this civilisation has banked at the moment the
        # simulation begins observing it" is "none recorded" rather than a
        # figure picked to soften the first few years - see
        # GRANARY_CAPACITY_YEARS_OF_DEMAND's own declaration (agriculture.py)
        # for where a sourced, physically-grounded number DOES enter this
        # mechanism (the CEILING on how large a buffer can grow, not the
        # starting point). What actually fixes Complaints/45 is not this
        # starting value - it is that `_demographic_recovery` below now
        # carries whatever THIS ATTRIBUTE holds forward from year to year,
        # instead of rebuilding an `agriculture.Storage` at stock_kg=0.0
        # every single year regardless of what the previous year harvested.
        # SAVE_FIELDS ("farm_stock_kg", sim/engine/proto/saveload.py) is
        # what makes that survive a --session save/load, exactly the same
        # concern `pop_children`/`pop_working_age`/`pop_elderly` were added
        # for a milestone earlier - state a hazard or a harvest can move
        # away from its constructor default has to round-trip, or a player
        # who saves and resumes plays a quietly different, easier game than
        # one who does not.
        self.farm_stock_kg = 0.0
        # Diagnostic only - see `_demographic_recovery`'s own comment on
        # `_last_farm_year` for why this is not a SAVE_FIELDS member.
        self._last_farm_year = None
        self._last_demographic_step = None
        # Population-raising technologies (sanitation, antisepsis, crop
        # rotation, canning...) queue their effect here instead of applying
        # it the year they complete - see apply_tech_effects in society.py.
        # Each entry is [fraction-of-baseline added per year, years left to
        # add it]: a lower death rate shows up in a headcount a generation
        # later, not the day a latrine opens. STILL DRAINED INTO
        # `_pop_scale_base` (unchanged) rather than into `self.population`
        # directly - giving a technology an actual per-instance effect on
        # this civilisation's mortality/fertility needs a mechanism
        # sim/world/demography.py does not have yet (its rates are module-
        # level constants), which is Commit 4's own open design question in
        # docs/architecture/WIRING_MILESTONE_4.md SS1.3/SS6, deliberately
        # left undone by this milestone's Commit 3.
        self._pop_tech_pending = []
        self.year = self.cfg["start_year"]
        config = self.cfg
        # THE FOUNDER'S HOUSEHOLD: money, staff, knowledge, plant and standing,
        # as its own object rather than eighty-odd attributes of this one. See
        # sim/engine/actors/household.py for what it holds and
        # docs/architecture/HOUSEHOLD_EXTRACTION.md for why: making this an
        # object of its own, rather than more state on `Sim`, is what would let
        # a government, a rival household or a firm exist someday, each owning
        # its own purse and its own knowledge instead of sharing this one.
        #
        # AT THIS SOCIETY'S PRICES, like everything else you will spend it on.
        # The kits are quoted in Rome 100 AD denarii, and once revenue and
        # living costs started converting (see economy.living_cost) leaving the
        # purse flat meant "four hundred denarii" bought a third more months of
        # bread in Luoyang than in Scandinavia, silently, for no modelled
        # reason. A kit is "a few months' subsistence", and a few months'
        # subsistence costs what it costs where you are. Computed here, where
        # `price_index` is in scope, and handed in as a plain number: a
        # Household should not need to know the shape of a run's config dict
        # to be built.
        #
        # `operating_changed=self._operating_changed`: `self` (this Sim) is
        # fully allocated already, even this early in `__init__` - Python
        # hands `__init__` a real, if not-yet-populated, instance - so a bound
        # method of it can be passed down right now. See Household.__init__'s
        # own docstring for why the callback travels this way instead of the
        # household reaching back up for it.
        self.household = Household(
            starting_capital=float(config["start_capital"]) * self.price_index,
            operating_changed=self._operating_changed)
        # EVERY AUTOMATIC BEHAVIOUR, IN ONE PLACE, SWITCHABLE.
        #
        # A tester's objection, and the right one: "everything that is automatic
        # should be controllable by players, allowing them to enable/disable
        # that, as well as manually doing it". Each of these was a thing the
        # engine did on its own with no way to stop it and, in several cases, no
        # log line saying it had happened. Defaults differ between the optimizer
        # and a human: the optimizer has to run unattended, so it manages its own
        # household; a player is handed nothing they did not ask for.
        #
        # STAYS ON `Sim`, NOT ON `Household` - see household.py's module
        # docstring: one key, auto_court_heir, is written for succession after
        # a mortal owner's death, and the rest of the dict is not worth
        # splitting away from it for that.
        self.policy = {
            "auto_hire":     not manual,   # grow the staff toward what you can support
            # ON for the optimizer, OFF for a player, and that distinction is the
            # whole of what the tester actually objected to. Their complaint was
            # not that the model has slavery, it was that it bought people on
            # THEIR behalf, in a game they were playing by hand, with no prompt
            # and no line in the log. An unattended run of a slave economy that
            # says "bought 6 people for the workshop" in its log is modelling the
            # thing; a player who never typed the command and finds twenty people
            # in their household is being lied to.
            "auto_buy_people": not manual,
            "auto_manumit":  not manual,
            "auto_train":    not manual,   # teach trades this society does not have
            "auto_mine":     not manual,   # sink shafts when a material binds
            "auto_forest":   not manual,   # buy coppice when charcoal binds
            "auto_mothball": True,         # stop working what you cannot pay for
            # OFF FOR A PLAYER, like every other automation, and on for the
            # optimizer, which the long civilisation runs are calibrated
            # against. This is the most consequential thing the game does
            # without being asked: it discards technologies you built, which
            # under fog are the only score there is. A break tester found it on
            # by default and quietly deleting their work. Nothing stops a
            # player shedding a loss-maker by hand - `mothball` does exactly
            # that, and gets it back with `restore`.
            "auto_shed":     not manual,
            # Open every concern that plainly pays for itself. On for the
            # optimizer, whose long runs are calibrated against a household
            # that does run what it builds, and off for a player, for whom
            # deciding what to actually operate is the point.
            "auto_open":     not manual,
            "auto_court_heir": not manual,  # court a dead patron's successor
            # Buy a job from an outside shop when a few pairs of hands are the
            # only thing standing between you and something you need.
            "auto_commission": not manual,
            "auto_bribe":    not manual,   # pay your way out of a scandal
        }
        # A HANDFUL OF "LAST TIME I SAID/DID X" TRACKERS, GIVEN A REAL
        # STARTING VALUE HERE INSTEAD OF SPRINGING INTO EXISTENCE ON FIRST
        # USE. Each of these used to be read exclusively through
        # `getattr(self, name, default)`, in a path that runs every single
        # step (some in step() itself, some in SocietyMixin's per-year
        # calls) with no assignment anywhere that could run before the
        # first possible read - so every read paid a dict-and-default
        # lookup to reconstruct a value this constructor can just set once.
        # Every default below is exactly the getattr default already in use
        # at every call site, so this cannot change behaviour... PROVIDED
        # the attribute is not also one perf_fingerprint.py hashes: that
        # tool hashes protocol.py's SAVE_FIELDS list at year 0, and several
        # of ITS OWN comments say a save MISSING one of those fields reads
        # back as "has never happened yet" (None) - a state distinct from
        # an explicit zero or sentinel. Giving such a field a real value
        # here would make year 0's hash disagree with a baseline recorded
        # before this field existed, and that is exactly what happened the
        # first time this was tried: all nine fingerprint scenarios
        # diverged at year 0, every one of them tracing back to a
        # SAVE_FIELDS member.
        #
        # ONLY THE FIELDS THAT STAYED ON `Sim` remain here after the household
        # extraction - the household's own equivalents of this same pattern
        # (`insolvent_years`, `wage_hours_this_year`, `_said_deputies`, and
        # the rest) moved to Household.__init__ along with everything else it
        # owns; see that constructor's own copy of this comment. What is left
        # below is WORLD state (a shock or a debasement is something that
        # happened to the whole society, not to this household alone) and so
        # was never a candidate to move.
        self._said_wage_cascade = -999     # last year a wage-cascade note was printed; -999 guarantees the first qualifying year always warns
        self._literacy_said = -999            # last year a literacy-census note was printed
        self._food_diffusion_said = -999      # last year a food-diffusion note was printed
        self._said_condition = set()          # hazard-condition messages already printed once
        # THE FOLLOWING EIGHT FIELDS ARE BIOGRAPHICAL TO ONE MORTAL PERSON, not
        # to a household in general, and stay on `Sim` for exactly that reason
        # - see household.py's module docstring for the full argument. Moving
        # them would mean deciding, right now, with no second example to
        # design against, what death, personal hours or a patron mean for a
        # firm or a government; that is a real design question and this
        # extraction does not answer it by default.
        self.founder_alive = True
        self.dead_reason = None
        self.director_hours_spent_founder = 0.0
        # founder remaining lifespan, elite male already aged 35
        self.life_left = (1e9 if self.cfg["immortal"]
                          else max(self.FOUNDER_MIN_REMAINING_LIFE_YEARS,
                                    rng.gauss(self.cfg["founder_life_mean"],
                                              self.cfg["founder_life_sd"])))
        self.living_cost_paid = 0.0
        # WORLD state: monetary and real facts about the whole civilisation,
        # not about this household. money_real is currency debasement;
        # economy/output_factor are the size and health of the whole imperial
        # economy relative to 100 AD, crushed by war and plague, not by any
        # one household's fortunes.
        self.money_real = 1.0     # purchasing power of a denarius, 1.0 at 100 AD
        self.economy = 1.0        # size of the imperial economy relative to 100 AD
        self.output_factor = 1.0  # real output, crushed by war and plague, not by debasement
        # --- RAW MATERIAL QUANTITIES -------------------------------------
        # Until this existed the model assumed that if a material existed
        # anywhere you had unlimited quantities of it. That was the largest
        # remaining falsehood in the simulation.
        self.res = load_resources()
        # --- GEOGRAPHY: where things are, FOR THE CIVILIZATION IN PLAY -----
        # geography.json used to give every region one Rome-centric `reach`
        # and nothing in this file ever read it. See load_geography() and
        # region_reach()/material_reach() below for the fix: real coordinates,
        # a reach computed from THIS civ's own home ground, and a material
        # cost that follows from it. All of the below depends only on the
        # civ file and the (static) geography file, so it is computed once.
        self.geo = load_geography()
        self._regions = {region_id: value for region_id, value in (self.geo.get("regions") or {}).items()
                          if not region_id.startswith("_")}
        self._home_centroid = self._compute_home_centroid()
        # node id -> located_materials key. Lets material_cost_factor() find
        # the geography entry for a location-gated tech node (mat_gutta_percha,
        # mat_natural_rubber, ...) without the tech tree needing to know
        # anything about geography itself.
        self._mat_unlock = {}
        for material_key, material_data in (self.geo.get("located_materials") or {}).items():
            if material_key.startswith("_"):
                continue
            for nid in (material_data.get("unlocks") or []):
                self._mat_unlock[nid] = material_key
        # Mineral market access used to be `self.pop_scale`, i.e. "how much
        # coal can you buy" scaled by HOW MANY PEOPLE YOU HAVE. That is wrong
        # in both directions: Norse Scandinavia got 2.3% of Rome's coal
        # because it has 2.3% of the people, and England in 1300 got 7%,
        # when England is precisely where the coal actually IS. Geology is
        # not demography. See _compute_mineral_scale() for the replacement.
        # It depends only on home_regions and reach, neither of which change
        # during a run, so it is computed once here rather than every year.
        self._mineral_scale = {material: self._compute_mineral_scale(material)
                                for material in ("iron", "coal", "copper", "lead",
                                          "tin", "silver", "saltpetre")}
        # Whatever this civilization already has is free and already done, and it
        # is GRANTED, not earned. A playtester pointed out that these were being
        # counted in done_earned as though the founder had built them, which both
        # flatters the player and, worse, exposed a society's own ancestral
        # crafts to being "forgotten" in a sacking. Han China does not forget how
        # to cast iron because your workshop burned down.
        #
        # Populates self.household.done/.granted, not a fresh set here, and
        # stays on Sim rather than moving into Household.__init__ because it
        # needs the loaded tree and civ record to validate against (and to
        # raise ValueError on an unknown starting technology) - state this
        # class deliberately does not hold a reference to.
        starting_techs = self.civ["starting_techs"]
        missing = sorted(tech_id for tech_id in starting_techs if tech_id not in self.nodes)
        if missing:
            # Refuse a corrupt opening rather than merely warning and running a
            # different scenario. Eight ids were once silently dropped across
            # three civilizations, including four of the Mexica's five.
            raise ValueError("civilization %r lists unknown starting technologies: %s"
                             % (self.civ.get("id", "?"), ", ".join(missing)))
        for tech_id in starting_techs:
            self.household.done.add(tech_id)
            self._done_changed()
            self.household.granted.add(tech_id)
        # Starting ownership is deliberately exhausted by starting_techs.
        # Tier and zero cost describe a node's position in the universal graph;
        # they do not mean every society on Earth already owns it.  In
        # particular, never infer Roman materials or institutions for another
        # civilization from those fields.

    # ---- OUTSIDE-SURFACE PROPERTIES FOR THE EXTRACTED HOUSEHOLD ----------
    #
    # Everything below is a thin, single-line forward to `self.household`,
    # for the JSON protocol, save/load, the CLI and the tests - none of them
    # hot, all of them outside the engine. See
    # docs/architecture/HOUSEHOLD_EXTRACTION.md section 2 for why this is a
    # property here and a rewritten call site (`self.household.x`) inside the
    # six mixins and core.py's own methods, rather than one convenient
    # `__getattr__` covering both: measured at 51x slower per access than the
    # rewrite, and slow exactly on the path - `self.x` succeeding today,
    # `__getattr__` firing only on failure - that is the COMMON case for every
    # one of these once the field lives on `household` instead of `self`.
    #
    # Every getter is exactly one attribute access and nothing else, on
    # purpose (see the same section): a bug inside a longer property body
    # would raise its own AttributeError, indistinguishable from the
    # intentional one below, and get silently swallowed by any caller using
    # `getattr(sim, name, default)`.
    #
    # LAZY FIELDS (the household never assigns these until something actually
    # happens worth recording) are marked below: the getter raises
    # AttributeError exactly when `self.household` does not have the
    # attribute yet, ON PURPOSE - it supplies no default of its own, so
    # `getattr(sim, name, default)` still sees the field's true, possibly-
    # absent, state, exactly as it did before this field moved. See
    # sim/ARCHITECTURE.md for the one time promoting a lazily-created field
    # to a real attribute passed the whole suite while silently breaking
    # this exact contract.

    @property
    def _cap_factor(self):
        return self.household._cap_factor

    @_cap_factor.setter
    def _cap_factor(self, value):
        self.household._cap_factor = value

    @property
    def _done_seq(self):
        return self.household._done_seq

    @_done_seq.setter
    def _done_seq(self, value):
        self.household._done_seq = value

    @property
    def _said_confiscation_band(self):
        return self.household._said_confiscation_band

    @_said_confiscation_band.setter
    def _said_confiscation_band(self, value):
        self.household._said_confiscation_band = value

    @property
    def _said_eminence(self):
        return self.household._said_eminence

    @_said_eminence.setter
    def _said_eminence(self, value):
        self.household._said_eminence = value

    @property
    def _said_notice_approach(self):
        return self.household._said_notice_approach

    @_said_notice_approach.setter
    def _said_notice_approach(self, value):
        self.household._said_notice_approach = value

    @property
    def _said_requisition(self):
        return self.household._said_requisition

    @_said_requisition.setter
    def _said_requisition(self, value):
        self.household._said_requisition = value

    @property
    def _spend_this_year(self):
        return self.household._spend_this_year

    @_spend_this_year.setter
    def _spend_this_year(self, value):
        self.household._spend_this_year = value

    @property
    def _staff_scale(self):
        return self.household._staff_scale

    @_staff_scale.setter
    def _staff_scale(self, value):
        self.household._staff_scale = value

    @property
    def active(self):
        return self.household.active

    @active.setter
    def active(self, value):
        self.household.active = value

    @property
    def artisans(self):
        return self.household.artisans

    @artisans.setter
    def artisans(self, value):
        self.household.artisans = value

    @property
    def atrocity(self):
        return self.household.atrocity

    @atrocity.setter
    def atrocity(self, value):
        self.household.atrocity = value

    @property
    def binding(self):
        return self.household.binding

    @binding.setter
    def binding(self, value):
        self.household.binding = value

    @property
    def bondage_debt(self):
        return self.household.bondage_debt

    @bondage_debt.setter
    def bondage_debt(self, value):
        self.household.bondage_debt = value

    @property
    def bondage_years_left(self):
        return self.household.bondage_years_left

    @bondage_years_left.setter
    def bondage_years_left(self, value):
        self.household.bondage_years_left = value

    @property
    def bountied(self):
        return self.household.bountied

    @bountied.setter
    def bountied(self, value):
        self.household.bountied = value

    @property
    def bounties_paid(self):
        return self.household.bounties_paid

    @bounties_paid.setter
    def bounties_paid(self, value):
        self.household.bounties_paid = value

    @property
    def bribes_ytd(self):
        return self.household.bribes_ytd

    @bribes_ytd.setter
    def bribes_ytd(self, value):
        self.household.bribes_ytd = value

    @property
    def capital(self):
        return self.household.capital

    @capital.setter
    def capital(self, value):
        self.household.capital = value

    @property
    def commissioned(self):
        return self.household.commissioned

    @commissioned.setter
    def commissioned(self, value):
        self.household.commissioned = value

    @property
    def contract_hours(self):
        return self.household.contract_hours

    @contract_hours.setter
    def contract_hours(self, value):
        self.household.contract_hours = value

    @property
    def contract_projects(self):
        return self.household.contract_projects

    @contract_projects.setter
    def contract_projects(self, value):
        self.household.contract_projects = value

    @property
    def credit_frozen_until(self):
        return self.household.credit_frozen_until

    @credit_frozen_until.setter
    def credit_frozen_until(self, value):
        self.household.credit_frozen_until = value

    @property
    def directors_extra(self):
        return self.household.directors_extra

    @directors_extra.setter
    def directors_extra(self, value):
        self.household.directors_extra = value

    @property
    def done(self):
        return self.household.done

    @done.setter
    def done(self, value):
        self.household.done = value

    @property
    def eminence(self):
        return self.household.eminence

    @eminence.setter
    def eminence(self, value):
        self.household.eminence = value

    @property
    def employees(self):
        return self.household.employees

    @employees.setter
    def employees(self, value):
        self.household.employees = value

    @property
    def failed_attempts(self):
        return self.household.failed_attempts

    @failed_attempts.setter
    def failed_attempts(self, value):
        self.household.failed_attempts = value

    @property
    def familiarity(self):
        return self.household.familiarity

    @familiarity.setter
    def familiarity(self, value):
        self.household.familiarity = value

    @property
    def forest_ha(self):
        return self.household.forest_ha

    @forest_ha.setter
    def forest_ha(self, value):
        self.household.forest_ha = value

    @property
    def forgotten(self):
        return self.household.forgotten

    @forgotten.setter
    def forgotten(self, value):
        self.household.forgotten = value

    @property
    def freedmen(self):
        return self.household.freedmen

    @freedmen.setter
    def freedmen(self, value):
        self.household.freedmen = value

    @property
    def goal_year(self):
        return self.household.goal_year

    @goal_year.setter
    def goal_year(self, value):
        self.household.goal_year = value

    @property
    def gov(self):
        return self.household.gov

    @gov.setter
    def gov(self, value):
        self.household.gov = value

    @property
    def granted(self):
        return self.household.granted

    @granted.setter
    def granted(self, value):
        self.household.granted = value

    @property
    def hour_allocations(self):
        return self.household.hour_allocations

    @hour_allocations.setter
    def hour_allocations(self, value):
        self.household.hour_allocations = value

    @property
    def last_military_demand(self):
        return self.household.last_military_demand

    @last_military_demand.setter
    def last_military_demand(self, value):
        self.household.last_military_demand = value

    @property
    def last_settlement(self):
        return self.household.last_settlement

    @last_settlement.setter
    def last_settlement(self, value):
        self.household.last_settlement = value

    @property
    def last_taught(self):
        return self.household.last_taught

    @last_taught.setter
    def last_taught(self, value):
        self.household.last_taught = value

    @property
    def log(self):
        return self.household.log

    @log.setter
    def log(self, value):
        self.household.log = value

    @property
    def manumitted_total(self):
        return self.household.manumitted_total

    @manumitted_total.setter
    def manumitted_total(self, value):
        self.household.manumitted_total = value

    @property
    def market_pressure(self):
        return self.household.market_pressure

    @market_pressure.setter
    def market_pressure(self, value):
        self.household.market_pressure = value

    @property
    def mine_cost_paid(self):
        return self.household.mine_cost_paid

    @mine_cost_paid.setter
    def mine_cost_paid(self, value):
        self.household.mine_cost_paid = value

    @property
    def mine_pending(self):
        return self.household.mine_pending

    @mine_pending.setter
    def mine_pending(self, value):
        self.household.mine_pending = value

    @property
    def mine_ready(self):
        return self.household.mine_ready

    @mine_ready.setter
    def mine_ready(self, value):
        self.household.mine_ready = value

    @property
    def mine_tranches(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.mine_tranches

    @mine_tranches.setter
    def mine_tranches(self, value):
        self.household.mine_tranches = value

    @property
    def mines(self):
        return self.household.mines

    @mines.setter
    def mines(self, value):
        self.household.mines = value

    @property
    def mothballed(self):
        return self.household.mothballed

    @mothballed.setter
    def mothballed(self, value):
        self.household.mothballed = value

    @property
    def nitre_bed_m2(self):
        return self.household.nitre_bed_m2

    @nitre_bed_m2.setter
    def nitre_bed_m2(self, value):
        self.household.nitre_bed_m2 = value

    @property
    def opened_year(self):
        return self.household.opened_year

    @opened_year.setter
    def opened_year(self, value):
        self.household.opened_year = value

    @property
    def operating(self):
        return self.household.operating

    @operating.setter
    def operating(self, value):
        self.household.operating = value

    @property
    def paid_towards(self):
        return self.household.paid_towards

    @paid_towards.setter
    def paid_towards(self, value):
        self.household.paid_towards = value

    @property
    def protection(self):
        return self.household.protection

    @protection.setter
    def protection(self, value):
        self.household.protection = value

    @property
    def reputation(self):
        return self.household.reputation

    @reputation.setter
    def reputation(self, value):
        self.household.reputation = value

    @property
    def scandal(self):
        return self.household.scandal

    @scandal.setter
    def scandal(self, value):
        self.household.scandal = value

    @property
    def scholars(self):
        return self.household.scholars

    @scholars.setter
    def scholars(self, value):
        self.household.scholars = value

    @property
    def shortages(self):
        return self.household.shortages

    @shortages.setter
    def shortages(self, value):
        self.household.shortages = value

    @property
    def slaves(self):
        return self.household.slaves

    @slaves.setter
    def slaves(self, value):
        self.household.slaves = value

    @property
    def stalled(self):
        return self.household.stalled

    @stalled.setter
    def stalled(self, value):
        self.household.stalled = value

    @property
    def teaching_hours_this_year(self):
        return self.household.teaching_hours_this_year

    @teaching_hours_this_year.setter
    def teaching_hours_this_year(self, value):
        self.household.teaching_hours_this_year = value

    @property
    def throttle(self):
        return self.household.throttle

    @throttle.setter
    def throttle(self, value):
        self.household.throttle = value

    @property
    def total_spend(self):
        return self.household.total_spend

    @total_spend.setter
    def total_spend(self, value):
        self.household.total_spend = value

    @property
    def trade_hours_used(self):
        return self.household.trade_hours_used

    @trade_hours_used.setter
    def trade_hours_used(self, value):
        self.household.trade_hours_used = value

    @property
    def trade_introduced_year(self):
        return self.household.trade_introduced_year

    @trade_introduced_year.setter
    def trade_introduced_year(self, value):
        self.household.trade_introduced_year = value

    @property
    def trades_created(self):
        return self.household.trades_created

    @trades_created.setter
    def trades_created(self, value):
        self.household.trades_created = value

    @property
    def trades_endemic(self):
        return self.household.trades_endemic

    @trades_endemic.setter
    def trades_endemic(self, value):
        self.household.trades_endemic = value

    @property
    def training(self):
        return self.household.training

    @training.setter
    def training(self, value):
        self.household.training = value

    @property
    def wages_paid(self):
        return self.household.wages_paid

    @wages_paid.setter
    def wages_paid(self, value):
        self.household.wages_paid = value

    @property
    def wages_prepaid(self):
        return self.household.wages_prepaid

    @wages_prepaid.setter
    def wages_prepaid(self, value):
        self.household.wages_prepaid = value

    @property
    def work_trade(self):
        return self.household.work_trade

    @work_trade.setter
    def work_trade(self, value):
        self.household.work_trade = value

    @property
    def _dashboard_history(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._dashboard_history

    @_dashboard_history.setter
    def _dashboard_history(self, value):
        self.household._dashboard_history = value

    @property
    def _demand_by_emp_key_cache(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._demand_by_emp_key_cache

    @_demand_by_emp_key_cache.setter
    def _demand_by_emp_key_cache(self, value):
        self.household._demand_by_emp_key_cache = value

    @property
    def _demand_by_tag_cache(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._demand_by_tag_cache

    @_demand_by_tag_cache.setter
    def _demand_by_tag_cache(self, value):
        self.household._demand_by_tag_cache = value

    @property
    def _goods_cat_state_cache(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._goods_cat_state_cache

    @_goods_cat_state_cache.setter
    def _goods_cat_state_cache(self, value):
        self.household._goods_cat_state_cache = value

    @property
    def _labour_pressure(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._labour_pressure

    @_labour_pressure.setter
    def _labour_pressure(self, value):
        self.household._labour_pressure = value

    @property
    def _last_buy_refusal(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._last_buy_refusal

    @_last_buy_refusal.setter
    def _last_buy_refusal(self, value):
        self.household._last_buy_refusal = value

    @property
    def _last_subst_gap(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._last_subst_gap

    @_last_subst_gap.setter
    def _last_subst_gap(self, value):
        self.household._last_subst_gap = value

    @property
    def _material_demand_cache(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._material_demand_cache

    @_material_demand_cache.setter
    def _material_demand_cache(self, value):
        self.household._material_demand_cache = value

    @property
    def _material_stock_ledger(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._material_stock_ledger

    @_material_stock_ledger.setter
    def _material_stock_ledger(self, value):
        self.household._material_stock_ledger = value

    @property
    def _operating_ver(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._operating_ver

    @_operating_ver.setter
    def _operating_ver(self, value):
        self.household._operating_ver = value

    @property
    def _practice_cache(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._practice_cache

    @_practice_cache.setter
    def _practice_cache(self, value):
        self.household._practice_cache = value

    @property
    def _rev_up_candidates_cache(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._rev_up_candidates_cache

    @_rev_up_candidates_cache.setter
    def _rev_up_candidates_cache(self, value):
        self.household._rev_up_candidates_cache = value

    @property
    def _said_autoopen(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._said_autoopen

    @_said_autoopen.setter
    def _said_autoopen(self, value):
        self.household._said_autoopen = value

    @property
    def _said_deputies(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._said_deputies

    @_said_deputies.setter
    def _said_deputies(self, value):
        self.household._said_deputies = value

    @property
    def _said_near_limit(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._said_near_limit

    @_said_near_limit.setter
    def _said_near_limit(self, value):
        self.household._said_near_limit = value

    @property
    def _said_parallelism(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._said_parallelism

    @_said_parallelism.setter
    def _said_parallelism(self, value):
        self.household._said_parallelism = value

    @property
    def _said_scandal(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._said_scandal

    @_said_scandal.setter
    def _said_scandal(self, value):
        self.household._said_scandal = value

    @property
    def _said_stack_caution(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._said_stack_caution

    @_said_stack_caution.setter
    def _said_stack_caution(self, value):
        self.household._said_stack_caution = value

    @property
    def _stock_throttle_cache(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._stock_throttle_cache

    @_stock_throttle_cache.setter
    def _stock_throttle_cache(self, value):
        self.household._stock_throttle_cache = value

    @property
    def _stock_throttle_sig(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._stock_throttle_sig

    @_stock_throttle_sig.setter
    def _stock_throttle_sig(self, value):
        self.household._stock_throttle_sig = value

    @property
    def done_year(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.done_year

    @done_year.setter
    def done_year(self, value):
        self.household.done_year = value

    @property
    def farm_hectares(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.farm_hectares

    @farm_hectares.setter
    def farm_hectares(self, value):
        self.household.farm_hectares = value

    @property
    def granted_staff(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.granted_staff

    @granted_staff.setter
    def granted_staff(self, value):
        self.household.granted_staff = value

    @property
    def insolvent_years(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.insolvent_years

    @insolvent_years.setter
    def insolvent_years(self, value):
        self.household.insolvent_years = value

    @property
    def inst_units(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.inst_units

    @inst_units.setter
    def inst_units(self, value):
        self.household.inst_units = value

    @property
    def interest_paid(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.interest_paid

    @interest_paid.setter
    def interest_paid(self, value):
        self.household.interest_paid = value

    @property
    def last_withdrawal(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.last_withdrawal

    @last_withdrawal.setter
    def last_withdrawal(self, value):
        self.household.last_withdrawal = value

    @property
    def scandal_last_year(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.scandal_last_year

    @scandal_last_year.setter
    def scandal_last_year(self, value):
        self.household.scandal_last_year = value

    @property
    def shut_for_staff(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.shut_for_staff

    @shut_for_staff.setter
    def shut_for_staff(self, value):
        self.household.shut_for_staff = value

    @property
    def spend_last_year(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.spend_last_year

    @spend_last_year.setter
    def spend_last_year(self, value):
        self.household.spend_last_year = value

    @property
    def trade_schools(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.trade_schools

    @trade_schools.setter
    def trade_schools(self, value):
        self.household.trade_schools = value

    @property
    def wage_hours_this_year(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.wage_hours_this_year

    @wage_hours_this_year.setter
    def wage_hours_this_year(self, value):
        self.household.wage_hours_this_year = value

    @property
    def wages_earned(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.wages_earned

    @wages_earned.setter
    def wages_earned(self, value):
        self.household.wages_earned = value

    @property
    def worker_housing_places(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.worker_housing_places

    @worker_housing_places.setter
    def worker_housing_places(self, value):
        self.household.worker_housing_places = value

    @property
    def revealed(self):
        # LAZY, AND A RATCHET, NOT A DEFAULT: the real ratchet logic
        # (union-only writes) lives on Household.revealed, moved there with
        # the rest of fog-of-war visibility - see fog.py's FogMixin comment
        # and sim/engine/actors/household.py. This is a plain forward, not
        # a second ratchet: assigning through it calls Household's setter
        # exactly once.
        return self.household.revealed

    @revealed.setter
    def revealed(self, value):
        self.household.revealed = value

    # WIRING MILESTONE 4, COMMIT 2 (docs/architecture/WIRING_MILESTONE_4.md
    # SS3, SS6): three forwarding properties, same shape as the household
    # ones just above, so `self.population`'s three cohort floats each get a
    # SAVE_FIELDS slot without a save format that has ever seen a nested
    # object (see that section for why three flat floats, not one struct).
    # Before this, none of the nine attributes _demographic_recovery's
    # scalar model used were ever saved at all - a live, currently-shipping
    # bug (a --session game silently wiped a demographic shock's wage
    # premium on the very next command, because cli.py reconstructs a fresh
    # Sim and load_state()s the save over it) which this fixes for the
    # REPLACEMENT model rather than reproducing it. `Population` itself is
    # never constructed by `load_state` - `Sim.__init__` already built one
    # (with the civilisation's UNSHOCKED baseline size) before load_state
    # runs, and these three setters overwrite its cohort counts in place
    # with whatever the save recorded, the same "setattr over a live
    # default" shape every other field in SAVE_FIELDS already uses.
    @property
    def pop_children(self):
        return self.population.children

    @pop_children.setter
    def pop_children(self, value):
        self.population.children = float(value)

    @property
    def pop_working_age(self):
        return self.population.working_age

    @pop_working_age.setter
    def pop_working_age(self, value):
        self.population.working_age = float(value)

    @property
    def pop_elderly(self):
        return self.population.elderly

    @pop_elderly.setter
    def pop_elderly(self, value):
        self.population.elderly = float(value)

    WAGE_SCARCITY_ELASTICITY = declare(
        "WAGE_SCARCITY_ELASTICITY", 0.9, kind="hardcoded_outcome",
        unit="dimensionless (wage premium per unit of population shortfall)",
        source="Phelps Brown and Hopkins' English real-wage index shows "
             "roughly a doubling across the century after 1348.",
        confidence="C",
        why="How much scarcer labour raises its own price - see pop_scale/"
            "wage_index below: at this elasticity, a Black-Death-sized "
            "shortfall reproduces roughly the cited real-wage doubling over "
            "the timescale sim/world/demography.py's own vital rates take "
            "to close it. FLAGGED AS A CLAUDE.md SS3.1/3.2 RISK: chosen "
            "specifically to land in the range that reproduces a known "
            "historical wage-index outcome (Phelps Brown and Hopkins), "
            "rather than derived from labour supply and demand "
            "fundamentals - the same shape as economy.py's DEBT_BASE_RATE, "
            "a real attested figure standing in for a market mechanism "
            "this project has not built. It is not fitted to the series "
            "numerically, but it was picked because it lands near the "
            "answer, which is the thing SS3.2 asks a baseline to reach "
            "independently rather than by construction.")

    # WIRING MILESTONE 4, COMMIT 3 (docs/architecture/WIRING_MILESTONE_4.md
    # SS6): `pop_scale` and `wage_index` are COMPUTED PROPERTIES now, not
    # stored attributes a hand-written recovery clock advanced. This is the
    # "one new attribute plus two computed properties" shape that section's
    # own SS7 recommends, precedented by the household extraction's own
    # forwarding properties - it lets the ~19+16 call sites across economy/
    # labour/geography/projects that already read `self.pop_scale`/
    # `self.wage_index` keep doing so, unchanged, while what backs them
    # changes underneath.
    #
    # WHAT THIS REPLACES, AND WHY IT IS DELETED RATHER THAN KEPT ALONGSIDE:
    # `_demographic_recovery` used to decay a hand-set `pop_deficit` on a
    # fixed exponential clock (`_pop_recovery_years`, `MIN_RECOVERY_TAU_
    # YEARS`, `DEMOGRAPHIC_RECOVERY_TIME_CONSTANTS` - all now gone, along
    # with `PLAGUE_RECOVERY_YEARS_REFERENCE`/`_REFERENCE_SEVERITY` in
    # society.py). sim/world/demography.py's OWN test suite falsifies that
    # shape directly: two populations that lose an identical 30% in one
    # year, one sparing working-age adults and one not, diverge sharply
    # afterwards, which a scalar deficit decaying on a clock that knows
    # nothing about WHO was lost cannot ever produce. `self.population`
    # (sim/world/demography.py's `Population`, constructed in __init__,
    # Commit 1) tracks who is what age, so this replaces the recovery clock
    # rather than adding a second mechanism beside it.
    #
    # `pop_scale` keeps the SAME reference constant
    # (`DEFAULT_POPULATION_100AD`, 65,000,000 - Rome's own configured
    # population) that every downstream formula calibrated against, so
    # `pop_scale == 1.0` still means "a Rome-sized labour market" exactly as
    # before - only the numerator changed, from a hand-multiplied scalar to
    # `self.population.total`, the age-cohort model's own running headcount.
    @property
    def pop_scale(self):
        return max(self.POP_SCALE_FLOOR, self.population.total / self.DEFAULT_POPULATION_100AD)

    # `wage_index`: LABOUR SCARCER, SO DEARER, exactly as before, but the
    # scarcity signal is now "how far the age-cohort model's actual
    # `pop_scale` sits below this civilisation's UNSHOCKED starting trend"
    # rather than a hand-decayed deficit fraction. A hazard no longer needs
    # to touch `wage_index` at all: cutting `self.population`'s cohorts (see
    # `_apply_population_mortality_shock` below) lowers `pop_scale`
    # directly, and this property reads the gap that opens.
    #
    # DELIBERATELY NOT `self._pop_scale_base` - a real trap this milestone's
    # own Commit 3 found and is recorded here rather than left for Commit 4
    # to rediscover. `_pop_scale_base` is still incremented by population-
    # raising technology and food-technology diffusion (`_pop_tech_pending`/
    # `_advance_food_diffusion_population`, society.py), UNCHANGED, but
    # those two write sites do not yet feed `self.population` itself
    # (that rewiring is Commit 4's own open design question - see
    # docs/architecture/WIRING_MILESTONE_4.md SS1.3). Reading the mutable
    # `_pop_scale_base` here would have made a population-raising
    # technology look like it made labour SCARCER, not more abundant: it
    # would raise the trend line that `pop_scale` is compared against
    # while `pop_scale` itself (self.population.total, untouched by these
    # two mechanisms in Commit 3) stays exactly where it was, widening
    # the apparent shortfall instead of leaving it alone. Comparing
    # against this civilisation's ORIGINAL configured trend instead - the
    # same expression `_pop_scale_base` was seeded with in __init__, before
    # any technology could touch it - keeps those two write sites
    # genuinely inert with respect to wage_index until Commit 4 gives them
    # a real effect on self.population to be inert ABOUT.
    #
    # RECOVERY IS NOW EMERGENT, NOT A CLOCK: as `self.population.step()`
    # (called once a year, below) runs its own births and deaths on the
    # SURVIVING cohort structure, `pop_scale` moves back toward this trend
    # (or does not, if the surviving population's own vital rates do not
    # support catch-up growth above replacement - which is itself a real,
    # checkable prediction of the demographic model rather than a number
    # this engine asserts) - see WIRING_MILESTONE_4.md SS5 for the
    # fingerprint behaviour this predicts.
    @property
    def wage_index(self):
        unshocked_trend = max(
            self.POP_SCALE_FLOOR,
            float(self.civ.get("population", self.DEFAULT_POPULATION_100AD))
            / self.DEFAULT_POPULATION_100AD)
        shortfall = max(0.0, 1.0 - self.pop_scale / unshocked_trend)
        return self._wage_index_base * (1.0 + self.WAGE_SCARCITY_ELASTICITY * shortfall)

    def _apply_population_mortality_shock(self, raw):
        """Cut `self.population`'s cohorts by `raw` (a fraction of the whole,
        e.g. 0.45 for the Black Death), unevenly by age - called from
        _shocks() (society.py) in place of the old scalar `pop_deficit`
        accumulation.

        AGE-DIFFERENTIATED BY THE SAME STARVATION_VULNERABILITY_* RATIOS
        sim/world/demography.py already declares for its own nutrition-
        driven excess mortality (children hit 1.6x as hard as working-age
        adults, the elderly 1.4x - see that module for the sourcing), scaled
        so the POPULATION-WEIGHTED AVERAGE loss equals `raw` exactly. This
        is what makes two equal-headcount losses diverge afterward depending
        on who survived - the property sim/tests/test_demography.py's own
        falsification test demands and the scalar model this replaces could
        never produce (see the comment above pop_scale).

        TEMPORARY_HEURISTIC (CLAUDE.md SS3.4), and flagged as such rather
        than presented as settled: STARVATION_VULNERABILITY_* was sourced
        for CALORIC shortfall (Watkins & Menken 1985), not epidemic disease
        or war mortality, which is what most staff_loss hazards actually
        are. The direction (children and the elderly are more vulnerable
        than working-age adults to most mass-mortality events, disease
        included) is well supported in the historical demography literature
        generally; reusing this SPECIFIC magnitude for a non-caloric shock
        is the invented part. docs/architecture/WIRING_MILESTONE_4.md SS1.3
        names the more principled alternative - routing a food-availability
        hazard through `Population.step`'s own nutrition_ratio and letting
        excess mortality fall out of THAT, instead of cutting cohorts
        directly - as future work, once a hazard can be expressed in
        calories rather than in a bare staff_loss fraction.
        """
        population = self.population
        weighted = (population.children * demography.STARVATION_VULNERABILITY_CHILD
                   + population.working_age * demography.STARVATION_VULNERABILITY_WORKING_AGE
                   + population.elderly * demography.STARVATION_VULNERABILITY_ELDERLY)
        if weighted <= 0.0 or raw <= 0.0:
            return
        scale = raw * population.total / weighted
        population.children -= population.children * min(
            1.0, scale * demography.STARVATION_VULNERABILITY_CHILD)
        population.working_age -= population.working_age * min(
            1.0, scale * demography.STARVATION_VULNERABILITY_WORKING_AGE)
        population.elderly -= population.elderly * min(
            1.0, scale * demography.STARVATION_VULNERABILITY_ELDERLY)

    def _adult_equivalent_population(self, population):
        """`population`'s food need in ADULT-EQUIVALENT units - the same
        weighting demography.py's own `Population.nutrition_ratio` (and,
        via `_subsistence_food`, `Population.stationary`) already use
        internally: a child counts as `CHILD_CALORIE_EQUIVALENT` of an
        adult, an elderly person as `ELDERLY_CALORIE_EQUIVALENT`, exactly
        so this file never has its own, second opinion on what a "person"
        is worth in calories.

        WIRING_MILESTONE_4.md SS4.3's UNIT MISMATCH, AND HOW THIS RESOLVES
        IT. `agriculture.Storage.step` takes a plain `population` argument
        and uses it exactly once: `food_demand_kg = population *
        annual_food_demand_kg_per_person(crop)`. Nothing in agriculture.py
        assumes that number is a flat headcount beyond that one line - it
        is "however many ration-equivalents need feeding" - so the fix
        needs no change to agriculture.py's signature at all: this engine
        computes the SAME adult-equivalent number demography.py already
        relies on and hands THAT to `Storage.step`'s `population` argument
        instead of `self.population.total`. Checked against SS4.3's own
        worked example: if the harvest fed in is exactly enough to meet
        `food_demand_kg` computed this way, then (since
        `HUMAN_ENERGY_REQUIREMENT_KCAL_PER_ADULT_DAY` and
        `SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY` are the same 2,200
        kcal/day figure, declared independently in each module for exactly
        this reason - see either module's own comment) `food_available_
        kcal_per_day` comes back at precisely `adult_equivalent_population
        * 2,200`, which is exactly the denominator `nutrition_ratio`
        divides by - so an exactly-met harvest reads back as
        `nutrition_ratio == 1.0`, not persistently 10-15% "too generous",
        by construction rather than by a tuned fudge factor. The SAME
        method also sizes `farm_land` at `__init__` and the farm workforce
        every year in `_demographic_recovery`, so all three uses of
        "how big is this population" at the agriculture boundary agree.
        """
        return (population.children * demography.CHILD_CALORIE_EQUIVALENT
                + population.working_age
                + population.elderly * demography.ELDERLY_CALORIE_EQUIVALENT)

    def _farm_year_weather_seed(self, yr, region=None):
        """A deterministic seed for one year's harvest weather draw, a pure
        function of this civilisation's id, an optional region, and the
        calendar year - NOT one long-lived `random.Random` advanced
        sequentially year over year.

        WHY THIS STAYS A PURE FUNCTION OF (CIVILISATION ID, REGION, YEAR)
        RATHER THAN A STORED GENERATOR, EVEN NOW THAT THE GRANARY ITSELF
        DOES PERSIST (see `_demographic_recovery` and `farm_stock_kg` below
        - Complaints/45 is what made the stock persist; the weather draw
        never needed to). A seed computed fresh from `(civilisation id,
        region, year)` has no sequential state to lose in the first place:
        year N's harvest draws the same weather whether it is reached by
        one unbroken run or by N separate `--session` commands, which is
        what actually matters, and it costs nothing to guarantee - so there
        was never a reason to give the weather generator itself a
        `SAVE_FIELDS` slot, independent of whatever else about a year's
        harvest does or does not round-trip. `self.farm_stock_kg` is the
        thing that actually needed one, and now has it (see
        `sim/engine/proto/saveload.py`'s `SAVE_FIELDS` tuple).

        Multiplier/offset are arbitrary mixing constants (not physical
        facts), chosen only so two different years, two regions, or two
        civilisations whose ids happen to share a common prefix, do not
        collide - the same non-`declare()`d role `_population_seed`'s own
        formula plays just above in `__init__`.

        WIRING TWO (Complaints/47-one-weather-draw-for-a-continent.md):
        `region` defaults to `None`, reproducing the OLD (civilisation id,
        year) seed bit for bit - every caller that predates per-region
        weather (there are none left in this engine, but a test or a
        future caller that wants "the" seed for a civilisation without
        naming a region still gets a well-defined answer) is unaffected.
        Passing a region name mixes it in as a THIRD independent
        ingredient, not a substitute for the civilisation id - two
        civilisations that happen to share a home region (a later
        conquest/contested-territory mechanism) still draw DIFFERENT
        weather for it, because the civilisation id is still in the mix.
        """
        civ_component = sum((index + 1) * ord(character) for index, character
                            in enumerate(str(self.civ.get("id", "civ"))))
        region_component = 0 if region is None else sum(
            (index + 1) * ord(character) for index, character
            in enumerate(str(region)))
        return (civ_component * 1000003 + region_component * 7919
                + int(yr) * 97) % (2 ** 32)

    def _compute_farm_region_weights(self):
        """[(region_id, weight), ...] over this civilisation's own
        `home_regions`, weight being that region's SHARE of the total
        cultivable land (`arable_iugera`, sim/world/land.py) among the
        regions this civilisation actually holds - Complaints/47's own
        "a region's harvest should scale with that region's own share of
        the cultivable land... or a tiny province counts as much as
        Egypt" requirement, checked directly against the measured
        arable-land figures rather than assumed equal.

        READS sim/world/land.py, DOES NOT MODIFY IT (this task's own
        ownership boundary) - `cultivable_land_for_civilization` is called
        exactly the way `demography`/`agriculture` are already imported
        and read from above, a pre-existing module this engine consumes.

        USES THE EXISTING 21 `home_regions`, NOT THE 1,139 `land_tiles` -
        see this method's own call site in `__init__` and this task's own
        brief for why: civilisations still name `home_regions`, and
        `economy.py`'s own `len(home_regions)` forest-ceiling scaling would
        silently multiply about thirteenfold if this reached for tile
        granularity instead. Tiles are a later change with their own
        before-and-after measurement, not something to fold in here.

        Falls back to an EQUAL split across `home_regions` if geography.json
        carries no arable-land figure for any region this civilisation
        holds (should not happen for any of the 21 shipped regions, all of
        which carry a `land` block - see land.py's own module docstring -
        but a future or test civilisation naming an unlisted region should
        degrade rather than crash). A civilisation with no `home_regions`
        at all gets an empty list, which `_pooled_farm_weather_multiplier`
        below reads as "fall back to the old civilisation-wide draw".
        """
        home_regions = list(self.civ.get("home_regions") or [])
        if not home_regions:
            return []
        civ_id = self.civ.get("id", "civ")
        parcels = land.cultivable_land_for_civilization(
            civ_id, civilizations={civ_id: self.civ})
        arable_iugera_by_region = {
            parcel.region: parcel.arable_iugera for parcel in parcels}
        total_arable_iugera = sum(arable_iugera_by_region.values())
        if total_arable_iugera > 0.0:
            return [(region, arable_iugera_by_region[region] / total_arable_iugera)
                    for region in home_regions if region in arable_iugera_by_region]
        equal_weight = 1.0 / len(home_regions)
        return [(region, equal_weight) for region in home_regions]

    def _pooled_farm_weather_multiplier(self, yr, weather_stdev_fraction=None):
        """This year's harvest weather multiplier, pooled across this
        civilisation's own home regions instead of one draw for the whole
        territory - Complaints/47-one-weather-draw-for-a-continent.md.

        Each region in `self._farm_region_weights` draws its OWN
        independent `agriculture.draw_weather_multiplier`, seeded from
        `_farm_year_weather_seed(yr, region=...)` (still a pure function of
        civilisation id, region and year - see that method's own docstring
        on why this has to stay true for determinism), and the civilisation
        as a whole gets the ARABLE-LAND-SHARE-WEIGHTED AVERAGE of those
        draws, not an unweighted one - a tiny province's weather does not
        get to count as much as Egypt's.

        A civilisation with no region weights at all (empty `home_regions`,
        or none of them carry land data - see `_compute_farm_region_
        weights`) falls back to exactly the OLD behaviour: one draw, seeded
        from `_farm_year_weather_seed(yr)` with no region, applied to the
        whole territory. This is what keeps a civilisation file this
        wiring was never meant to touch (one with no `home_regions` at all)
        running exactly as before rather than silently losing its harvest
        variance.

        LABELLED APPROXIMATION (CLAUDE.md SS3.4): this treats every
        region's weather draw as INDEPENDENT of every other region's. Real
        regions do not draw independently - a drought over Italia is not
        statistically unrelated to one over Greece, and neighbouring
        regions genuinely do share weather systems. Averaging N
        independent draws divides the effective standard deviation by
        sqrt(N) (Complaints/47's own measurement table), which is the
        correct answer for N independent regions and an OPTIMISTIC one for
        N correlated, geographically compact regions - the real benefit of
        holding a spread-out empire sits somewhere between "one draw" and
        "N independent draws", closer to the independent end the more the
        regions are climatically unrelated (Britannia and Mesopotamia)
        and closer to the one-draw end the more they neighbour each other
        (Gaul and Hispania). A distance-based correlation, sitting on
        geography.json's own region centroids, is the fix Complaints/47
        names and defers - not built here, so this number is real
        directionally (pooling territory is a genuine, historically
        attested risk-reducing mechanism - the Roman grain fleet existed
        for exactly this reason) but somewhat too generous in magnitude
        until that correlation exists.
        """
        soil = agriculture.DEFAULT_SOIL
        stdev = (soil.weather_stdev_fraction if weather_stdev_fraction is None
                 else weather_stdev_fraction)
        weights = self._farm_region_weights
        if not weights:
            # No usable region weights - the old, single-draw behaviour,
            # bit-identical to what this engine did before Complaints/47.
            return agriculture.draw_weather_multiplier(
                random.Random(self._farm_year_weather_seed(yr)), stdev)
        return sum(
            weight * agriculture.draw_weather_multiplier(
                random.Random(self._farm_year_weather_seed(yr, region=region)), stdev)
            for region, weight in weights)

    def _demographic_recovery(self, yr):
        """Advance `self.population` by one year, from a REAL harvest, and
        let population-raising technologies build their queued gain into
        `_pop_scale_base` - the same two jobs the old scalar
        `_demographic_recovery` did, now with the age-cohort model doing
        the population half and `agriculture.py` doing the food half.

        WIRING MILESTONE 4'S SPECIFIC HOLE, NOW CLOSED: this used to feed
        `self.population` exactly enough calories to sit at
        nutrition_ratio == 1.0 every year, computed from the cohort counts
        themselves - "is there enough food" was assumed, not simulated, so
        a famine could not happen for a physical reason at all. It now
        computes one year of `agriculture.Storage.step` - land, labour and
        an independent weather draw - and feeds ITS
        `food_available_kcal_per_day` to `Population.step` instead. A bad
        weather draw (or, later, a hazard that damages farmland or labour)
        can now leave `food_demand_kg` short, which lowers
        `nutrition_ratio` below 1.0, which raises mortality and lowers
        fertility through `Population.step`'s own, already-existing
        machinery - no new "famine" code path, exactly as demography.py's
        own module docstring requires (CLAUDE.md SS3.1).

        THE GRANARY NOW CARRIES OVER BETWEEN YEARS - Complaints/45-no-
        granary-so-the-baseline-collapses.md, closed by this change.
        `agriculture.Storage` was always built to bank a good year's
        surplus against a future bad one (see its own class docstring), but
        until now each year threw that away and constructed a fresh
        `Storage` at stock_kg=0.0 regardless of what the previous year
        harvested. That is not a harmless simplification: demography.py's
        own `NUTRITION_YEAR_TO_YEAR_NOISE_STD` declaration names exactly
        this failure mode by name (Jensen's inequality on a one-sided
        response curve) - mortality and fertility both floor at
        nutrition_ratio == 1.0, so a good year's excess calories buy
        nothing while a bad year's shortfall costs real people in full,
        and averaging weather that is symmetric around 1.0 over a
        population that responds asymmetrically to it manufactures a
        ONE-DIRECTIONAL decline with no scripted cause. This engine's own
        per-year weather draw (`_farm_year_weather_seed`) hit that same
        failure mode through a different door than the `jitter` flag
        demography.py guards it behind - the guard was bypassed, not
        removed, and Complaints/45 measured the result: rome_100ad with
        events=False fell to 21.9% of its starting population over a
        century with no hazard of any kind. Real agrarian societies damp
        exactly this with grain storage; this wiring now has it.

        `self.farm_stock_kg` (`SAVE_FIELDS`, sim/engine/proto/saveload.py)
        is the persisted state: each year's `Storage` is constructed at
        THAT stock, not zero, and whatever it holds after this year's
        sowing/harvest/consumption/spoilage/reseeding is written back to it
        - capped at `agriculture.granary_capacity_kg` (see that function
        and GRANARY_CAPACITY_YEARS_OF_DEMAND's own declaration in
        agriculture.py for the physical basis of the cap: a granary is a
        built structure with a finite floor area, not an unlimited ledger,
        and the cap is sized off documented historical grain-reserve
        targets, not off whatever makes the population curve look right -
        CLAUDE.md SS3.1). The cap is applied HERE, at the engine boundary,
        never inside `Storage.step` itself, so that class's own one-year
        conservation identity (sim/tests/test_agriculture.py's own check)
        is untouched: what changes is how much of one year's `stock_after_
        kg` the civilisation's actual storage infrastructure lets survive
        into next year's opening stock, not anything about how one year's
        flows balance.

        WHAT THIS DOES NOT CLAIM TO FIX, UPDATED FOR Complaints/45's
        FOLLOW-UP ("with 0 large events, you shouldn't have a population
        decline over a century"). demography.py's `_fertility_multiplier`
        now DOES ramp fertility up above nutrition_ratio == 1.0 (a bounded,
        Hutterite-anchored ceiling - see its own docstring and
        FERTILITY_SURPLUS_CEILING_MULTIPLIER's declaration; checked against
        the stakeholder's own biological growth-rate ceiling in
        sim/tests/test_demography.py's `GrowthCeilingTests`, which measures
        ~2.1%/year under literally unlimited food against a ~9.06%/year
        ceiling). `_excess_mortality_multiplier` remains floored at 1.0 -
        no sourced biological limit on how far mortality can fall below an
        already-observed subsistence baseline was found; see that
        function's own docstring for what was checked and why it came up
        empty.

        UPDATE - THE PARAGRAPH THAT USED TO STAND HERE IS NOW WRONG, AND IS
        REPLACED RATHER THAN LEFT TO MISLEAD THE NEXT READER (CLAUDE.md's
        own rule that a comment stating a fixed bug in the past tense reads
        as current unless it says plainly that it no longer is one). It used
        to say `Storage.step` capped consumption at bare subsistence NO
        MATTER HOW MUCH was banked, so nutrition_ratio could structurally
        never exceed 1.0 and demography.py's own above-1.0 fertility ramp
        was dead code from this call site's point of view. `agriculture.py`
        (still not this task's ownership) has since grown exactly the
        mechanism that claim said was missing: `reserve_target_kg`, passed
        to `farm_storage.step` below, lets a population eat beyond
        subsistence once its granary holds more than its own reserve
        target - see that call's own comment for the mechanism. So
        nutrition_ratio CAN and DOES exceed 1.0 now, in a good year with a
        full granary, and the fertility ramp is live, not dead.

        WIRING TWO (Complaints/47-one-weather-draw-for-a-continent.md) is
        what makes this matter in practice rather than only in principle.
        Under the OLD single civilisation-wide weather draw, a granary
        rarely stayed above its reserve target for long: the next bad year
        was drawn from the same wide (0.20 relative stdev) distribution
        that emptied it in the first place, so "eating well" was real but
        rare (measured before this wiring: nutrition_ratio's mean stayed at
        or below 1.0 - see the now-updated sim/tests/test_agriculture_
        wiring.py and sim/tests/test_granary_persistence.py comments for
        the exact pre-wiring figures). Pooling weather across home regions
        lowers the EFFECTIVE variance a granary actually experiences (see
        `_pooled_farm_weather_multiplier`'s own docstring), so the granary
        sits above its reserve far more of the time and "eating well"
        stops being rare - this is the direct mechanism, not a side effect,
        by which WIRING TWO raises the unshocked century's ending
        population above its starting one: it is not only that catastrophic
        province-wide famines become rarer, it is also that a pooled
        empire's surplus years are now allowed to actually feed people.

        THE UNSHOCKED CENTURY, MEASURED AT EACH STAGE (rome_100ad,
        events=False, 100 years, starting population 65,000,000):
        Complaints/47 measured 76.0% before the granary/reserve work above
        existed; Complaints/48 measured 85.51% once it did, with disease
        burden and per-region weather both still unwired; wiring
        `_disease_burden` through (WIRING ONE) is a proven no-op on this
        specific measurement, since Rome starts with none of the eight
        medical technologies and this scenario completes no technology at
        all (manual=True, no autopilot); wiring per-region pooled weather
        through (WIRING TWO, this method) is what actually moves it, past
        100% of starting population - see this task's own report for the
        exact figure, which will drift slightly as the rest of the engine
        (agriculture.py, land.py) continues to change and should be
        re-measured rather than read off this comment.

        LABOUR AND LAND UNIT DECISIONS (WIRING_MILESTONE_4.md SS4.1/4.2),
        MADE HERE RATHER THAN LEFT IMPLICIT. The farm workforce is sized
        every year as `agriculture.farm_workers_fte_for_population` of
        THIS YEAR'S adult-equivalent population (see
        `_adult_equivalent_population` - resolves SS4.1: no separate
        dependency-ratio correction is needed at this boundary because
        that helper's numerator and denominator are already anchored to
        the same convention once an adult-equivalent count, not a flat
        headcount, is what goes in).

        RESOLVES SS4.2 MORE COMPLETELY THAN "PICK 1,400 OVER 2,000" DOES.
        The first version of this wiring did exactly that - fed
        `farm_workers_fte * agriculture.ANNUAL_LABOUR_HOURS_PER_FARM_WORKER`
        to `Storage.step` as `labour_hours` - and it was WRONG, not merely
        using the less-preferred of two constants: `agriculture.py`'s own
        `gross_harvest_kg` reads `labour_hours` TWICE, for two DIFFERENT
        purposes that do not share a convention. `_max_hectares_
        harvestable_by_labour` divides it by `ANNUAL_LABOUR_HOURS_PER_
        FARM_WORKER` to recover a worker count for the harvest-window cap
        (a 1,400-hours-per-worker convention); the Cobb-Douglas labour
        term is calibrated against `REFERENCE_LABOUR_HOURS_PER_HECTARE`
        (150) - HOURS ACTUALLY WORKED PER HECTARE, not hours per worker-
        year - exactly the reference-labour-intensity convention sim/
        tests/test_agriculture.py's own HarvestWindowBindsGrossHarvestTests
        uses. Those two per-worker figures (1,400 and, at this module's own
        binding harvest-window ceiling, 150 x 2.1 = 315) disagree by the
        same ~4.4x the module's own docstring names as "the annual-hours
        ceiling is slack by more than four to one" - so a `labour_hours`
        pool built the first way satisfies the CAP's convention while
        overshooting the LABOUR TERM's, inflating a year's harvest by
        roughly the square root of that gap (confirmed empirically: at
        Rome's own population this produced a harvest 2-3x the reference
        figure `farmland_for_population` was sized against, in EVERY
        weather draw, never binding a famine at all - wrong-different, not
        right-different, and caught by exactly the probe this task asked
        for).

        THE FIX uses `gross_harvest_kg`'s `worker_count` parameter (added
        to this module by this same change) to stop asking it to guess a
        workforce back out of `labour_hours` at all: `worker_count=
        farm_workers_fte` decides the harvest-window cap directly, from
        the actual number this engine already computed, and `labour_hours`
        is built the OTHER function's way instead - REFERENCE_LABOUR_
        HOURS_PER_HECTARE times `hectares_worked`, the hectares this many
        workers can actually crop (capped at whatever `farm_land` physically
        holds). The two agree by construction: at the population `farm_land`
        was originally sized for, `hectares_worked == farm_land.hectares`
        exactly, reproducing `fraction_of_population_that_must_farm`'s own
        reference yield bit for bit (before weather is applied) - this is
        the "right-different" identity the module's own calibration function
        implies, now actually reproduced by the engine call site rather than
        only by the closed-form calibration check. `agriculture.py`'s
        `ANNUAL_LABOUR_HOURS_PER_FARM_WORKER` (1,400) still governs
        `hectares_cropped_per_farm_worker` internally (and so still decides
        whether the harvest window or the annual-hours ceiling binds); what
        this resolves is that NEITHER it nor economy.py's own
        `HOURS_PER_PERSON_YEAR` (2,000) is used to build the `labour_hours`
        crossing this boundary - only a worker COUNT crosses it, and
        agriculture.py's own functions decide, on their own terms, how many
        hours that implies for each of the two different things it is used
        for. `farm_land` itself is NOT resized here - see its own
        construction comment in `__init__` for why fixed land, not fixed
        workforce share, is what is allowed to be a hard constraint: once
        `farm_workers_fte` implies more hectares than `farm_land` holds,
        `hectares_worked` saturates at `farm_land.hectares` and additional
        population stops buying this civilisation any more food from
        agriculture at all - a harder ceiling than ordinary diminishing
        returns would give, and an honest consequence of not (yet) modelling
        within-hectare labour intensification beyond reference technique.
        """
        if self._pop_tech_pending:
            still = []
            for per_year, years_left in self._pop_tech_pending:
                self._pop_scale_base += per_year
                if years_left > 1:
                    still.append((per_year, years_left - 1))
            self._pop_tech_pending = still

        adult_equivalent_population = self._adult_equivalent_population(self.population)
        farm_workers_fte = agriculture.farm_workers_fte_for_population(
            adult_equivalent_population)
        hectares_worked = min(
            self.farm_land.hectares,
            farm_workers_fte * agriculture.hectares_cropped_per_farm_worker())
        farm_labour_hours = hectares_worked * agriculture.REFERENCE_LABOUR_HOURS_PER_HECTARE
        # SEED IS SOWN ON WHAT GETS WORKED, NOT ON `farm_land`'S FULL FIXED
        # AREA. `Storage.step` charges seed (and next year's seed reservation)
        # against `land.hectares` directly, with no cap of its own - it is
        # meant to be handed exactly the area actually being cropped. Passing
        # `self.farm_land` itself here, unshrunk, would sow (and pay for)
        # seed across this civilisation's FULL historical endowment even in
        # a year `hectares_worked` is far smaller (a population that has lost
        # people has fewer hands, not less land per surviving hand) - a real
        # bug this task's own probe caught: population fell, workers_fte and
        # therefore `hectares_worked` fell with it, but an EARLIER version of
        # this method still sowed the whole original `farm_land.hectares`
        # every year regardless, so the seed bill outgrew the shrinking
        # workforce's own shrinking harvest and manufactured a runaway
        # collapse that had nothing to do with weather - the textbook
        # wrong-different result this task's fingerprint probe exists to
        # catch. A `Land` sized to `hectares_worked` (this year's actually-
        # cropped area) fixes it: unworked land beyond that is fallow-by-
        # absence-of-hands, not sown, not seed-costed, not harvested.
        worked_land = agriculture.Land(hectares_worked, quality=self.farm_land.quality)
        # THE GRANARY: opens the year at whatever `self.farm_stock_kg`
        # carried in from last year's close, not at zero - see this
        # method's own docstring section on Complaints/45 for why that
        # single word ("carried" rather than "constructed fresh") is the
        # entire fix, and `farm_stock_kg` in SAVE_FIELDS
        # (sim/engine/proto/saveload.py) for why it survives a save.
        # `seed=` HERE IS NOW DEFENSIVE, NOT LOAD-BEARING: `farm_storage.
        # step` below is always given an explicit `weather_multiplier`
        # (WIRING TWO, Complaints/47), so `Storage`'s own internal
        # `self._random`/`draw_weather_multiplier` path this seed feeds is
        # never actually reached from this call site any more. Still
        # passed, rather than left at the constructor's own `None` default,
        # so this stays deterministic even if a future edit here ever stops
        # passing `weather_multiplier` - the same "belt and braces" spirit
        # as the civ-wide fallback inside `_pooled_farm_weather_multiplier`
        # itself.
        farm_storage = agriculture.Storage(
            stock_kg=self.farm_stock_kg, seed=self._farm_year_weather_seed(yr))
        # `reserve_target_kg` is the SAME figure the carry-forward is capped
        # at below, and passing it is what lets a population eat above bare
        # subsistence in a good year. Without it, Storage.step reverts to
        # min(demand, stock): people eat subsistence or less, never more,
        # so the nutrition ratio handed to demography cannot exceed 1.0 and
        # a good year buys nothing while a bad one still costs lives. The
        # granary alone did not fix that - it banked the grain and then
        # forbade anyone to eat it. Filling the reserve first is what stops
        # this becoming a feast that empties the granary: only grain already
        # beyond the reserve is eaten, which is grain that would otherwise
        # have sat there and spoiled.
        reserve_target_kg = agriculture.granary_capacity_kg(
            adult_equivalent_population * agriculture.annual_food_demand_kg_per_person())
        # WIRING TWO (Complaints/47-one-weather-draw-for-a-continent.md):
        # THE PER-REGION WEATHER DRAW. `_pooled_farm_weather_multiplier`
        # draws one independent weather multiplier per home region this
        # civilisation holds and returns the arable-land-share-weighted
        # average - see that method's own docstring for the mechanism, the
        # independence approximation it flags, and the land.py functions it
        # reads from (never modifies). Passed in explicitly rather than
        # left for `Storage.step` to draw internally, which is what turns
        # "one weather draw for a continent" into "N independent draws,
        # pooled" without agriculture.py needing to know anything about
        # civilisations, home regions or land shares at all - it just
        # receives a number, exactly as it always has.
        farm_year = farm_storage.step(
            worked_land, farm_labour_hours, adult_equivalent_population,
            worker_count=farm_workers_fte,
            reserve_target_kg=reserve_target_kg,
            weather_multiplier=self._pooled_farm_weather_multiplier(yr))
        # CLOSE THE YEAR: write what this year's Storage call actually
        # leaves on hand back as next year's opening stock, capped at what
        # this civilisation's storage infrastructure can physically hold
        # (agriculture.granary_capacity_kg - see GRANARY_CAPACITY_YEARS_OF_
        # DEMAND's own declaration in agriculture.py for the physical basis
        # of the cap, and this method's docstring for why the cap is
        # applied HERE rather than inside Storage.step).
        #
        # `agriculture.stock_to_carry_forward_kg`, NOT `farm_year.stock_
        # after_kg` ALONE - see that function's own docstring and Storage.
        # step's docstring section on carrying stock across years for why:
        # `stock_after_kg` has already had NEXT year's seed reservation
        # (`seed_retained_kg`) removed from it, so persisting `stock_after_
        # kg` alone throws that reserved seed away and then charges an
        # identical amount again as next year's `seed_sown_kg` - a genuine
        # bug this task's own fingerprint probe caught empirically (a
        # near-total-extinction result on ordinary weather, no fingerprint
        # divergence a hazard or land loss would explain) the first time
        # persistence was tried without this correction. Adding
        # `seed_retained_kg` back in is what makes the two calls agree:
        # what THIS call earmarked for sowing is exactly what NEXT call's
        # own `seed_sown_kg` computation will draw down, once and only
        # once.
        #
        # `min()` only clips the UPPER side - a negative carry-forward
        # (this year ate into seed corn it did not have; see Storage.
        # step's own docstring on why that is allowed to happen rather
        # than being silently floored at zero) passes through unclipped
        # and genuinely carries into next year's sowing, which is
        # Storage's own documented "one bad harvest becomes two" mechanism
        # actually operating across years for the first time - a real
        # behavioural change from before this fix, and a correct one: it
        # was always the model's own intended design (Storage.step's class
        # docstring), just inert while every year discarded the previous
        # year's ending stock outright.
        capacity_kg = agriculture.granary_capacity_kg(farm_year.food_demand_kg)
        self.farm_stock_kg = min(
            agriculture.stock_to_carry_forward_kg(farm_year), capacity_kg)
        # Kept for tests and diagnostics only (e.g. `state`'s founder-facing
        # reply never reads this) - NOT a SAVE_FIELDS member and does not
        # need to be one: it is recomputed fresh every year from state that
        # already round-trips (self.population, self.farm_land, self.civ),
        # so a stale or missing value right after a fresh `Sim()` (before
        # this method has run once) costs nothing correctness-sensitive.
        self._last_farm_year = farm_year

        # Same diagnostic-only status as `_last_farm_year` just above (not a
        # SAVE_FIELDS member, recomputed fresh every year) - kept so a test
        # or a future player-facing message can read THIS year's
        # nutrition_ratio without re-deriving it from the cohort counts by
        # hand a second time.
        self._last_demographic_step = self.population.step(
            farm_year.food_available_kcal_per_day, jitter=False,
            disease_burden=self._disease_burden())
        self._refresh_demographic_indexes(yr)

    def _disease_burden(self):
        """WIRING ONE (Complaints/48-technology-cannot-stop-people-dying-
        young.md): this civilisation's CURRENT disease burden, 1.0 being
        the full pre-industrial infectious environment sim/world/
        demography.py already assumes by default, 0.0 being clean water,
        sanitation, germ-theory hygiene and vaccination all present -
        `demography.py`'s own module docstring names the derivation this
        reuses rather than inventing: sum the `population` weights of
        whichever of `DISEASE_BURDEN_TECH_IDS` (above) this civilisation
        currently holds (`self.has`, which `starting_techs` and completed
        nodes both feed - see Household.__init__'s own comment), and
        express that as a fraction of ALL EIGHT unlocked (rather than
        hardcoding the 0.15 those eight happen to sum to today, so this
        stays correct if `_TECH_EFFECTS.json` ever reweights them):

            disease_burden = 1.0 - unlocked_weight / total_weight

        LIVE, NOT QUEUED: read fresh every call from `self.has(...)`
        rather than accumulated into `_pop_tech_pending` the way these same
        eight entries' `population` field used to be (see `apply_tech_
        effects`, society.py) - a technology's disease effect is a
        standing fact about this civilisation ("it now boils its water"),
        not a one-off pulse that ramps in over POP_TECH_RAMP_YEARS and is
        done. `apply_tech_effects` no longer feeds these eight into
        `_pop_tech_pending` at all (see its own comment) specifically so
        the same tree-author weight is not doing two jobs at once, one of
        which (`_pop_tech_pending` draining into `_pop_scale_base`, which
        WIRING_MILESTONE_4.md SS1.3 established is read by nothing) was
        already known-inert. The five FOOD entries that also carry a
        `population` field (crop_rotation, fud_three_field_rotation,
        fud_seed_drill, mat_newworld_crops, ag2_canning) are calorie
        effects, not disease ones, and are deliberately excluded by
        construction: only `DISEASE_BURDEN_TECH_IDS`'s own eight ids are
        ever summed here.

        Clamped to [0, 1] defensively (a total of exactly 0.15 measured
        directly against `_TECH_EFFECTS.json` today makes this unreachable
        in practice, but a future edit to that file changing the eight
        weights' sum should not be able to hand `demography.Population.
        step` a burden outside the range it declares valid).
        """
        unlocked_weight = sum(
            TECH_EFFECTS[tech_id].get("population", 0.0)
            for tech_id in self.DISEASE_BURDEN_TECH_IDS if self.has(tech_id))
        total_weight = sum(
            TECH_EFFECTS[tech_id].get("population", 0.0)
            for tech_id in self.DISEASE_BURDEN_TECH_IDS)
        if total_weight <= 0.0:
            return demography.PRE_INDUSTRIAL_DISEASE_BURDEN
        return max(0.0, min(1.0, 1.0 - unlocked_weight / total_weight))

    def _refresh_demographic_indexes(self, yr):
        """Say why the wage bill moved, if it moved enough to be worth
        saying - the only job left here once pop_scale/wage_index became
        computed properties (see above). Kept as its own method, called
        both after a year's ordinary advance and immediately after a
        hazard fires, for the same reason it always was: a shock's
        announced effects should be visible immediately, not lag a step.
        """
        premium = (self.wage_index / self._wage_index_base - 1.0) * 100
        # The message wants the SAME shortfall wage_index's own property
        # just computed, not a second, separately-derived copy of it - see
        # wage_index's own comment for why it is measured against this
        # civilisation's unshocked configured trend rather than the
        # (still tech-mutable) `_pop_scale_base`. Recovered algebraically
        # from `premium` rather than recomputed, so the two can never drift
        # apart: premium == elasticity * shortfall * 100, by construction.
        shortfall = (premium / 100.0) / self.WAGE_SCARCITY_ELASTICITY if self.WAGE_SCARCITY_ELASTICITY else 0.0
        if premium > 0.5 and yr - self._said_wage_cascade >= 15:
            self._said_wage_cascade = yr
            self.household.log.append((yr, "population still %d%% below trend: wages "
                                 "(and anything billed in them) are running "
                                 "%d%% above normal for here, and will ease "
                                 "as the population does"
                             % (round(shortfall * 100), round(premium))))

    # -- helpers ------------------------------------------------------------

    # Years between one automatic teaching of a trade and the next. Long
    # enough that restoring a lost trade is an event rather than a habit.
    RETEACH_EVERY = declare(
        "RETEACH_EVERY", 25, kind="temporary_heuristic", unit="years",
        source=None, confidence="D",
        why="Minimum gap between one automatic re-teaching of a lost "
            "trade and the next, so restoring it is an event rather than "
            "a habit the optimizer leans on every year. Round number, not "
            "measured.")

    def has(self, k):
        return k in self.household.done

    # THE ONE PLACE that answers "what is my corpus worth against a
    # sacking" - the sack in SocietyMixin._shocks and the `risk` reply in
    # FogMixin.knowledge_risk used to each carry their own copy of this
    # table, and they drifted: `risk` was fixed to read `has()` (a corpus
    # that is written and dispersed does not stop existing because the
    # scriptorium that produced it closed - copies already in other
    # people's hands are still in other people's hands), and the sack was
    # never brought along, so it kept reading `running()` and applied
    # corpus_written's weaker 0.45/0.22 to a household `risk` was telling,
    # in the same breath, it had corpus_dispersed's 0.12/0.08. A player
    # who trusted the screen lost nearly three times what they were told
    # to expect. Call this, from both places, rather than re-deriving it -
    # that is the only way to make the two screens unable to disagree
    # again.
    CORPUS_HEDGE_LOSS_CHANCE_DISPERSED = declare(
        "CORPUS_HEDGE_LOSS_CHANCE_DISPERSED", 0.12, kind="temporary_heuristic",
        unit="dimensionless (probability a sack takes any corpus at all)",
        source=None, confidence="D",
        why="Chance a sack takes any of the corpus at all once it is "
            "written and dispersed - lowest of the three hedge states, "
            "because copies already sit in other people's hands beyond "
            "this one site. Tuned, not measured.")
    CORPUS_HEDGE_FRACTION_LOST_DISPERSED = declare(
        "CORPUS_HEDGE_FRACTION_LOST_DISPERSED", 0.08, kind="temporary_heuristic",
        unit="dimensionless (fraction of losable technologies taken)",
        source=None, confidence="D",
        why="If a sack does take from the corpus while dispersed, how "
            "much of what is still losable it takes - smallest of the "
            "three states. Tuned, not measured.")
    CORPUS_HEDGE_LOSS_CHANCE_WRITTEN = declare(
        "CORPUS_HEDGE_LOSS_CHANCE_WRITTEN", 0.45, kind="temporary_heuristic",
        unit="dimensionless (probability a sack takes any corpus at all)",
        source=None, confidence="D",
        why="Chance a sack takes any of the corpus once it is merely "
            "written down (not yet dispersed) - one set of books in one "
            "place is still losable. Tuned, not measured.")
    CORPUS_HEDGE_FRACTION_LOST_WRITTEN = declare(
        "CORPUS_HEDGE_FRACTION_LOST_WRITTEN", 0.22, kind="temporary_heuristic",
        unit="dimensionless (fraction of losable technologies taken)",
        source=None, confidence="D",
        why="If a sack does take from the corpus while merely written, "
            "how much of what is still losable it takes. Tuned, not "
            "measured.")
    CORPUS_HEDGE_LOSS_CHANCE_NONE = declare(
        "CORPUS_HEDGE_LOSS_CHANCE_NONE", 0.80, kind="temporary_heuristic",
        unit="dimensionless (probability a sack takes any corpus at all)",
        source=None, confidence="D",
        why="Chance a sack takes any of the corpus with no written hedge "
            "at all - the founder's own head and workshop are the only "
            "copy. Tuned to make an unhedged corpus genuinely dangerous "
            "to hold; not measured.")
    CORPUS_HEDGE_FRACTION_LOST_NONE = declare(
        "CORPUS_HEDGE_FRACTION_LOST_NONE", 0.40, kind="temporary_heuristic",
        unit="dimensionless (fraction of losable technologies taken)",
        source=None, confidence="D",
        why="If a sack does take from an unhedged corpus, how much of "
            "what is still losable it takes - largest of the three "
            "states. Tuned, not measured.")

    def corpus_hedge(self):
        """(loss_chance, fraction_lost, hedge_name) a sacking faces right now.

        `has`, not `running`: see the comment above `has` itself and
        FogMixin.knowledge_risk for the fuller argument. `hedge_name` is
        None if neither corpus exists yet.
        """
        if self.has("corpus_dispersed"):
            return self.CORPUS_HEDGE_LOSS_CHANCE_DISPERSED, self.CORPUS_HEDGE_FRACTION_LOST_DISPERSED, "corpus_dispersed"
        if self.has("corpus_written"):
            return self.CORPUS_HEDGE_LOSS_CHANCE_WRITTEN, self.CORPUS_HEDGE_FRACTION_LOST_WRITTEN, "corpus_written"
        return self.CORPUS_HEDGE_LOSS_CHANCE_NONE, self.CORPUS_HEDGE_FRACTION_LOST_NONE, None

    # ---- GEOGRAPHY: reach and material cost, FOR THE CIVILIZATION IN PLAY --
    # geography.json used to hard-code one `reach` per region, measured from
    # Italy, and nothing in this file ever read it as a cost: `civs` printed
    # `base_reach` and that was the entire effect either number had. Play Han
    # China and the model still treated Chinese silk as three reach-steps
    # away and Malaya, which Chinese and Malay traders already sail to
    # routinely, as an exotic frontier, while Italy -- a place that
    # civilization has never seen -- was reach 0. That is backwards for
    # every civilization except Rome. Everything below computes reach from
    # the ACTUAL civilization's own home ground instead.

    STAFF_ATTRITION_RATE = declare(
        "STAFF_ATTRITION_RATE", 0.035, kind="temporary_heuristic",
        unit="dimensionless (yearly probability per person)", source=
        "Rough order-of-magnitude estimate combining Roman adult mortality "
        "with normal turnover (poaching, retirement).", confidence="C",
        why="Yearly chance any one employed person dies or leaves for a "
            "better offer - applied per whole person (see the comment "
            "below on why headcount is rolled discretely rather than "
            "smoothed). A plausible order of magnitude for a pre-modern "
            "adult workforce, not fitted to an attested Roman mortality "
            "table.")
    DIRECTORS_EXTRA_APPROACH_RATE = declare(
        "DIRECTORS_EXTRA_APPROACH_RATE", 0.12, kind="temporary_heuristic",
        unit="dimensionless (fraction of the gap to capacity closed per "
             "year)", source=None, confidence="D",
        why="How fast the household's deputy-director pool approaches "
            "what its institutions can support, net of the same "
            "STAFF_ATTRITION_RATE that thins ordinary staff. Tuned so "
            "deputies build up over several years rather than "
            "instantaneously; not measured.")

    AUTO_HIRE_CREDIT_ROOM_SHARE = declare(
        "AUTO_HIRE_CREDIT_ROOM_SHARE", 0.75, kind="temporary_heuristic",
        unit="dimensionless (share of credit_limit treated as still "
             "usable for growth)", source=None, confidence="D",
        why="How deep into arrears the automation will still hire, "
            "relative to the credit line - deep arrears means building, "
            "not growing, is the household's actual state (see comment "
            "above). Tuned, not measured.")
    AUTO_HIRE_SCHOLAR_EXTRA_SHARE = declare(
        "AUTO_HIRE_SCHOLAR_EXTRA_SHARE", 0.35, kind="temporary_heuristic",
        unit="dimensionless (share of supervision-room headroom spent on "
             "scholars)", source=None, confidence="D",
        why="How much of the household's extra supervision headroom is "
            "aimed at scholars versus artisans when auto_hire grows the "
            "staff. Tuned split, not measured.")
    AUTO_HIRE_SCHOLAR_APPROACH_RATE = declare(
        "AUTO_HIRE_SCHOLAR_APPROACH_RATE", 0.18, kind="temporary_heuristic",
        unit="dimensionless (fraction of the gap to target closed per "
             "year)", source=None, confidence="D",
        why="How fast the scholar pool approaches its target headcount "
            "under auto_hire - smoothed rather than instant so growth "
            "reads as hiring over years, not a single jump. Tuned, not "
            "measured.")
    AUTO_HIRE_ARTISAN_APPROACH_RATE = declare(
        "AUTO_HIRE_ARTISAN_APPROACH_RATE", 0.22, kind="temporary_heuristic",
        unit="dimensionless (fraction of the gap to target closed per "
             "year)", source=None, confidence="D",
        why="As AUTO_HIRE_SCHOLAR_APPROACH_RATE, for artisans - slightly "
            "faster, tuned rather than measured.")
    AUTO_HIRE_SLAVE_CRAFT_CREDIT = declare(
        "AUTO_HIRE_SLAVE_CRAFT_CREDIT", 0.7, kind="temporary_heuristic",
        unit="dimensionless (fraction of a slave counted as a craft "
             "worker already)", source=None, confidence="D",
        why="How much of the desired artisan headcount an existing slave "
            "is treated as already covering, before auto_hire tops up the "
            "generic craft bucket - slaves are not all doing craft work, "
            "so this is a partial credit rather than one-for-one. Tuned, "
            "not measured.")

    TRADE_REPLACEMENT_TARGET_HEADCOUNT = declare(
        "TRADE_REPLACEMENT_TARGET_HEADCOUNT", 2.0, kind="temporary_heuristic",
        unit="people", source=None, confidence="D",
        why="Minimum headcount auto_hire tries to keep in any trade the "
            "founder has ever taught, once attrition has thinned it - "
            "enough that a taught trade cannot silently vanish from a "
            "single death. Round number, not measured.")
    TRADE_REPLACEMENT_AFFORDABILITY_YEARS = declare(
        "TRADE_REPLACEMENT_AFFORDABILITY_YEARS", 6, kind="temporary_heuristic",
        unit="years of that trade's annual wage", source=None,
        confidence="D",
        why="How much spare capital (in years of the trade's own wage) "
            "the household must hold before auto_hire replaces a lost "
            "taught worker - a buffer so this does not spend the "
            "household into arrears over one specialist. Tuned, not "
            "measured.")

    AUTO_MANUMIT_ANNUAL_CHANCE = declare(
        "AUTO_MANUMIT_ANNUAL_CHANCE", 0.25, kind="temporary_heuristic",
        unit="dimensionless (yearly probability, optimizer only)",
        source=None, confidence="D",
        why="Yearly chance the optimizer's standing policy manumits some "
            "slaves, when it holds any. Invented frequency, not fitted to "
            "any attested manumission rate.")
    AUTO_MANUMIT_SHARE_DIVISOR = declare(
        "AUTO_MANUMIT_SHARE_DIVISOR", 4, kind="temporary_heuristic",
        unit="dimensionless (divisor; frees roughly a quarter)",
        source=None, confidence="D",
        why="How large a bite auto-manumission takes when it fires - "
            "roughly a quarter of current slaves, at least one. Tuned, "
            "not measured.")
    OUTPUT_RECOVERY_RATE = declare(
        "OUTPUT_RECOVERY_RATE", 0.006, kind="temporary_heuristic",
        unit="dimensionless per year (base recovery toward output_factor "
             "1.0)", source=None, confidence="D",
        why="Base yearly recovery rate of output_factor after a war or "
            "other output shock, doubled at full military leverage (see "
            "comment above) - an armed empire recovers roughly twice as "
            "fast as an unarmed one, not instantly. Tuned to make a war's "
            "damage linger for decades, not measured against any attested "
            "postwar recovery rate.")

    INSOLVENCY_FLOOR_MIN = declare(
        "INSOLVENCY_FLOOR_MIN", 4000.0, kind="temporary_heuristic",
        unit="denarii", source=None, confidence="D",
        why="Floor on how deep into arrears a household can sit before "
            "insolvency's staff bleed can begin, for a household with "
            "very low revenue - so a household earning almost nothing is "
            "not bled the instant it dips a denarius below zero. Round "
            "number, not measured.")
    INSOLVENCY_FLOOR_REVENUE_MULTIPLE = declare(
        "INSOLVENCY_FLOOR_REVENUE_MULTIPLE", 2.0, kind="temporary_heuristic",
        unit="years of revenue", source=None, confidence="D",
        why="How many years of revenue a household may sit in arrears "
            "before insolvency's staff bleed can begin, for a household "
            "with meaningful revenue - scales the floor to the "
            "household's own size rather than a flat number. Tuned, not "
            "measured.")
    INSOLVENCY_YEARS_BEFORE_BLEED = declare(
        "INSOLVENCY_YEARS_BEFORE_BLEED", 3, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="Consecutive years of genuine insolvency (income not "
            "covering costs, past INSOLVENCY_FLOOR_MIN/"
            "INSOLVENCY_FLOOR_REVENUE_MULTIPLE) before staff actually "
            "start leaving - a brief dip is not treated the same as "
            "sustained failure. Round number, not measured.")
    INSOLVENCY_BLEED_CAP = declare(
        "INSOLVENCY_BLEED_CAP", 0.15, kind="temporary_heuristic",
        unit="dimensionless (maximum fraction of staff lost per year)",
        source=None, confidence="D",
        why="Ceiling on how much of the artisan pool insolvency can bleed "
            "in a single year, however long the household has been "
            "insolvent - a floor against the doom loop this mechanism "
            "replaced (see comment above: a Norse run once sat insolvent "
            "for 495 years, bleeding without limit). Tuned, not measured.")
    INSOLVENCY_BLEED_RATE = declare(
        "INSOLVENCY_BLEED_RATE", 0.04, kind="temporary_heuristic",
        unit="dimensionless (fraction of staff lost per insolvent year)",
        source=None, confidence="D",
        why="How fast the insolvency bleed grows with consecutive "
            "insolvent years, capped at INSOLVENCY_BLEED_CAP. Tuned, not "
            "measured.")
    INSOLVENCY_ARTISAN_FLOOR = declare(
        "INSOLVENCY_ARTISAN_FLOOR", 3.0, kind="temporary_heuristic",
        unit="artisans", source=None, confidence="D",
        why="Minimum artisans an insolvent household keeps, however long "
            "it bleeds - a household that has shed everything else can "
            "still climb back rather than being erased outright. Round "
            "number, not measured.")
    INSOLVENCY_SCHOLAR_FLOOR = declare(
        "INSOLVENCY_SCHOLAR_FLOOR", 1.0, kind="temporary_heuristic",
        unit="scholars", source=None, confidence="D",
        why="Minimum scholars an insolvent household keeps, for the same "
            "reason as INSOLVENCY_ARTISAN_FLOOR. Round number, not "
            "measured.")
    INSOLVENCY_SCHOLAR_BLEED_DISCOUNT = declare(
        "INSOLVENCY_SCHOLAR_BLEED_DISCOUNT", 0.6, kind="temporary_heuristic",
        unit="dimensionless (fraction of the artisan bleed rate applied "
             "to scholars)", source=None, confidence="D",
        why="Scholars bleed slower than artisans under insolvency - "
            "tuned so a household in arrears keeps more of its scarce, "
            "harder-to-replace literate staff; not measured.")

    REPUTATION_DECAY_TOWARD_FLOOR = declare(
        "REPUTATION_DECAY_TOWARD_FLOOR", 0.97, kind="temporary_heuristic",
        unit="dimensionless (fraction of the gap above the standing floor "
             "kept per year)", source=None, confidence="D",
        why="How much of reputation's gap above the standing floor "
            "survives each year - reputation decays toward what a "
            "founder is actually known for (the floor), not toward zero "
            "(see comment above). A slow decay, tuned so novelty fades "
            "over decades rather than years; not measured against any "
            "attested reputation-decay rate.")
    FAMILIARITY_CEILING = declare(
        "FAMILIARITY_CEILING", 0.9, kind="temporary_heuristic",
        unit="dimensionless (0..1)", source=None, confidence="D",
        why="Ceiling on familiarity, however long or publicly the founder "
            "has worked - a society never becomes fully unable to be "
            "surprised. Round figure, not measured.")
    FAMILIARITY_PUBLICATION_WEIGHT = declare(
        "FAMILIARITY_PUBLICATION_WEIGHT", 0.5, kind="temporary_heuristic",
        unit="dimensionless (weight per spectacle/inexplicable node done)",
        source=None, confidence="D",
        why="How much each publicly astonishing thing the founder has "
            "done adds to familiarity's growth, relative to the passage "
            "of time (FAMILIARITY_TENURE_WEIGHT). Tuned, not measured.")
    FAMILIARITY_TENURE_WEIGHT = declare(
        "FAMILIARITY_TENURE_WEIGHT", 0.25, kind="temporary_heuristic",
        unit="dimensionless (weight per year since year 100)", source=None,
        confidence="D",
        why="How much the mere passage of time (being a known fixture) "
            "adds to familiarity's growth, relative to specific "
            "publications (FAMILIARITY_PUBLICATION_WEIGHT). Tuned, not "
            "measured.")
    MARKET_PRESSURE_DECAY = declare(
        "MARKET_PRESSURE_DECAY", 0.55, kind="temporary_heuristic",
        unit="dimensionless (fraction kept per year)", source=None,
        confidence="D",
        why="How much of last year's market pressure (the price bump a "
            "household's own buying caused) survives into this year - "
            "sellers restock, so the pressure fades. Tuned, not measured.")
    MARKET_PRESSURE_ANNUAL_FADE = declare(
        "MARKET_PRESSURE_ANNUAL_FADE", 2.0, kind="temporary_heuristic",
        unit="market-pressure points", source=None, confidence="D",
        why="Flat yearly reduction in market pressure on top of "
            "MARKET_PRESSURE_DECAY's proportional fade, so a small "
            "residual pressure reaches exactly zero rather than decaying "
            "forever. Tuned, not measured.")
    SCANDAL_DECAY_RATE = declare(
        "SCANDAL_DECAY_RATE", 0.90, kind="temporary_heuristic",
        unit="dimensionless (fraction kept per year)", source=None,
        confidence="D",
        why="How much of last year's scandal survives, absent any fresh "
            "cause or bribery - scandal fades on its own, slower than "
            "market pressure but faster than reputation moves toward its "
            "floor. Tuned, not measured.")
    EMINENCE_DECAY_RATE = declare(
        "EMINENCE_DECAY_RATE", 0.93, kind="temporary_heuristic",
        unit="dimensionless (fraction kept per year, before this year's "
             "hazard is added)", source=None, confidence="D",
        why="How much of last year's eminence survives before adding this "
            "year's prominence_hazard() - see society.py's eminence_report "
            "and prominence_hazard, which both reference this same rate "
            "(as self.EMINENCE_DECAY_RATE) so the reported settling value "
            "can never disagree with what actually accumulates here. "
            "Tuned so eminence settles at a level roughly proportionate to "
            "sustained hazard, not measured.")
    AUTO_BRIBE_SCANDAL_THRESHOLD = declare(
        "AUTO_BRIBE_SCANDAL_THRESHOLD", 8, kind="temporary_heuristic",
        unit="scandal points", source=None, confidence="D",
        why="Scandal level above which the optimizer's standing bribery "
            "policy actually starts spending - below it, scandal is not "
            "yet worth buying down. Tuned, not measured.")
    AUTO_BRIBE_CAPITAL_THRESHOLD = declare(
        "AUTO_BRIBE_CAPITAL_THRESHOLD", 2000, kind="temporary_heuristic",
        unit="denarii", source=None, confidence="D",
        why="Minimum capital before the optimizer's bribery policy will "
            "spend at all, so a poor household is not bled dry bribing "
            "away scandal it might survive anyway. Round number, not "
            "measured.")
    AUTO_BRIBE_CAPITAL_SHARE = declare(
        "AUTO_BRIBE_CAPITAL_SHARE", 0.12, kind="temporary_heuristic",
        unit="dimensionless (share of capital)", source=None,
        confidence="D",
        why="Ceiling on how much of current capital one year's bribery "
            "spend can be, so buying down scandal cannot alone bankrupt "
            "the household. Tuned, not measured.")
    AUTO_BRIBE_COST_PER_SCANDAL_POINT = declare(
        "AUTO_BRIBE_COST_PER_SCANDAL_POINT", 260, kind="temporary_heuristic",
        unit="denarii per scandal point", source=None, confidence="D",
        why="What buying down one point of scandal costs, capping total "
            "spend alongside AUTO_BRIBE_CAPITAL_SHARE. Invented figure, "
            "not sourced to any attested bribe schedule.")
    BRIBES_YTD_DECAY = declare(
        "BRIBES_YTD_DECAY", 0.7, kind="temporary_heuristic",
        unit="dimensionless (fraction kept per year)", source=None,
        confidence="D",
        why="How much of the running bribes_ytd total (itself the "
            "denominator update_protection() reads for the bribery "
            "protection term) survives into next year - a bribe's "
            "protective effect fades rather than accumulating forever. "
            "Tuned, not measured.")
    BRIBE_SCANDAL_REDUCTION_SCALE = declare(
        "BRIBE_SCANDAL_REDUCTION_SCALE", 300.0, kind="temporary_heuristic",
        unit="denarii per scandal point removed (before bribability)",
        source=None, confidence="D",
        why="How much bribery spend it takes to remove one point of "
            "scandal, scaled further by this society's own bribability "
            "weight. Invented figure, not sourced to any attested bribe "
            "schedule.")

    SCANDAL_HAZARD_SCALE = declare(
        "SCANDAL_HAZARD_SCALE", 60.0, kind="temporary_heuristic",
        unit="scandal points per unit of yearly denunciation probability",
        source=None, confidence="D",
        why="How much scandal above the danger line it takes to add a "
            "full 100% to this year's denunciation chance - shared with "
            "the 'YOU ARE BEING TALKED ABOUT' warning text so the number "
            "quoted there can never disagree with the one that fires. "
            "Tuned, not measured against any attested denunciation rate.")
    EMINENCE_CONFISCATION_CAPITAL_LOSS = declare(
        "EMINENCE_CONFISCATION_CAPITAL_LOSS", 0.55, kind="temporary_heuristic",
        unit="dimensionless (fraction of capital)", source=None,
        confidence="D",
        why="Fraction of capital the eminence-driven confiscation outcome "
            "takes - distinct from society.py's state-notice-driven "
            "CONFISCATION_CAPITAL_LOSS, this is the court's jealousy of a "
            "great man, unbribable by design (see prominence_hazard's own "
            "docstring). Tuned, not measured.")
    EMINENCE_CONFISCATION_REPUTATION_LOSS = declare(
        "EMINENCE_CONFISCATION_REPUTATION_LOSS", 18, kind="temporary_heuristic",
        unit="reputation points", source=None, confidence="D",
        why="Reputation lost to an eminence-driven confiscation and forced "
            "retirement - the largest single reputation hit in this file, "
            "reflecting public disgrace on top of the property loss. "
            "Tuned, not measured.")
    EMINENCE_CONFISCATION_RETENTION = declare(
        "EMINENCE_CONFISCATION_RETENTION", 0.45, kind="temporary_heuristic",
        unit="dimensionless (fraction of eminence kept)", source=None,
        confidence="D",
        why="Fraction of eminence kept after a confiscation and forced "
            "withdrawal - the outcome itself lowers prominence sharply. "
            "Tuned, not measured.")
    EMINENCE_PATRON_LOSS_RETENTION = declare(
        "EMINENCE_PATRON_LOSS_RETENTION", 0.5, kind="temporary_heuristic",
        unit="dimensionless (fraction of eminence kept)", source=None,
        confidence="D",
        why="Fraction of eminence kept after a patron is destroyed in "
            "someone else's quarrel - a smaller drop than "
            "EMINENCE_CONFISCATION_RETENTION since the founder's own "
            "position is not directly struck. Tuned, not measured.")
    EMINENCE_PATRON_LOSS_REPUTATION_LOSS = declare(
        "EMINENCE_PATRON_LOSS_REPUTATION_LOSS", 10, kind="temporary_heuristic",
        unit="reputation points", source=None, confidence="D",
        why="Reputation lost when a patron is destroyed - smaller than "
            "EMINENCE_CONFISCATION_REPUTATION_LOSS since the disgrace is "
            "the patron's, not directly the founder's. Tuned, not "
            "measured.")

    BONDAGE_LABOUR_SHARE = declare(
        "BONDAGE_LABOUR_SHARE", 0.75, kind="temporary_heuristic",
        unit="dimensionless (share of a founder-year's hours)",
        source=None, confidence="D",
        why="Share of a founder's yearly hours treated as owed labour "
            "while serving out a debt-bondage term. Tuned to leave some "
            "hours for the founder's own affairs even in bondage; not "
            "measured.")
    BONDAGE_LABOURER_WAGE_DEFAULT = declare(
        "BONDAGE_LABOURER_WAGE_DEFAULT", 0.075, kind="temporary_heuristic",
        unit="denarii/hour at price_index=1.0", source=None,
        confidence="D",
        why="Fallback labourer wage rate for computing bondage repayment "
            "if WAGES has no 'labourer' entry - WAGES normally does carry "
            "one, so this only matters as a defensive default.")
    BONDAGE_WAGE_MARKUP = declare(
        "BONDAGE_WAGE_MARKUP", 1.2, kind="temporary_heuristic",
        unit="dimensionless multiplier", source=None, confidence="D",
        why="Markup on the plain labourer wage used to value bonded "
            "labour toward debt repayment - bonded labour is valued a "
            "little above the cheapest free-market rate. Tuned, not "
            "measured.")
    SANITATION_LIFE_EXTENSION_YEARS = declare(
        "SANITATION_LIFE_EXTENSION_YEARS", 0.12, kind="temporary_heuristic",
        unit="years added per year of founder mortality roll",
        source=None, confidence="D",
        why="Extra expected lifespan per year once sanitation and "
            "antisepsis are known - 'you at least do not die of a septic "
            "cut'. A real effect in kind (antisepsis measurably cut "
            "mortality), invented in this specific magnitude; a real "
            "figure needs an actual survival-curve shift rather than a "
            "flat annual bonus.")
    DISSOLUTION_YEARS_BEFORE_FORGETTING = declare(
        "DISSOLUTION_YEARS_BEFORE_FORGETTING", 3, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="Years a founderless programme sits stalled before it starts "
            "actively forgetting technologies - a brief gap is not yet "
            "dissolution. Round number, not measured.")
    DISSOLUTION_FORGET_FRACTION_DIVISOR = declare(
        "DISSOLUTION_FORGET_FRACTION_DIVISOR", 6, kind="temporary_heuristic",
        unit="dimensionless (divisor; forgets roughly a sixth)",
        source=None, confidence="D",
        why="How large a bite a dissolving programme's forgetting takes "
            "each qualifying year - roughly a sixth of what remains "
            "losable. Tuned so full dissolution over "
            "DISSOLUTION_YEARS_UNTIL_END years is gradual, not "
            "instantaneous; not measured.")
    DISSOLUTION_YEARS_UNTIL_END = declare(
        "DISSOLUTION_YEARS_UNTIL_END", 12, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="Years a founderless, deputy-less programme can dissolve "
            "before the run ends outright - stated directly to the player "
            "('the programme goes on without you... over twelve years' / "
            "'the run ends at twelve'), so this number is quoted in "
            "several log messages as well as enforced here. Round number, "
            "not measured.")

    MAX_ACTIVE_PROJECTS_BASE = declare(
        "MAX_ACTIVE_PROJECTS_BASE", 2, kind="temporary_heuristic",
        unit="projects", source=None, confidence="D",
        why="Minimum number of projects a household can hold active at "
            "once, before scholars/artisans/director hours add more. "
            "Round number, not measured.")
    MAX_ACTIVE_PROJECTS_PER_DIRECTOR_HOURS = declare(
        "MAX_ACTIVE_PROJECTS_PER_DIRECTOR_HOURS", 2000.0, kind="temporary_heuristic",
        unit="founder-hours per extra active project", source=None,
        confidence="D",
        why="How many director-hours of capacity buy one more active "
            "project slot - see the comment above: doubling this whole "
            "formula was measured to make every civilisation worse (Rome "
            "fell from 33% of runs reaching the transistor to none), "
            "because more projects in hand divide the same purse into "
            "smaller annual payments. Kept at the value that measured "
            "better, not derived from a model of attention or budgeting.")
    MAX_ACTIVE_PROJECTS_PER_SCHOLAR = declare(
        "MAX_ACTIVE_PROJECTS_PER_SCHOLAR", 12.0, kind="temporary_heuristic",
        unit="scholars per extra active project", source=None,
        confidence="D",
        why="How many scholars buy one more active project slot. Tuned "
            "alongside MAX_ACTIVE_PROJECTS_PER_DIRECTOR_HOURS and "
            "MAX_ACTIVE_PROJECTS_PER_ARTISAN as one measured formula; not "
            "independently derived.")
    MAX_ACTIVE_PROJECTS_PER_ARTISAN = declare(
        "MAX_ACTIVE_PROJECTS_PER_ARTISAN", 25.0, kind="temporary_heuristic",
        unit="artisans per extra active project", source=None,
        confidence="D",
        why="How many artisans buy one more active project slot - see "
            "MAX_ACTIVE_PROJECTS_PER_DIRECTOR_HOURS's own comment for the "
            "measurement this whole formula was tuned and then held "
            "against.")

    WAGE_FALLBACK_MIN_HOURS = declare(
        "WAGE_FALLBACK_MIN_HOURS", 100.0, kind="temporary_heuristic",
        unit="founder-hours", source=None, confidence="D",
        why="Minimum unused hours before the optimizer's wage-work "
            "fallback bothers activating - not worth the overhead of "
            "selling a token amount. Round number, not measured.")
    WAGE_FALLBACK_LIVING_COST_YEARS = declare(
        "WAGE_FALLBACK_LIVING_COST_YEARS", 2, kind="temporary_heuristic",
        unit="years of living cost", source=None, confidence="D",
        why="How thin a cash buffer (in years of living cost) triggers "
            "the optimizer selling idle hours for wages rather than "
            "riding out a bad year - see comment above: without this, a "
            "single early fire could end a run in a handful of years. "
            "Tuned, not measured.")
    WAGE_FALLBACK_MAX_HOURS = declare(
        "WAGE_FALLBACK_MAX_HOURS", 1200.0, kind="temporary_heuristic",
        unit="founder-hours/year", source=None, confidence="D",
        why="Ceiling on how many hours a year the wage-work fallback will "
            "sell, so it cannot consume the entire year even when nothing "
            "else has any claim on the founder's time. Tuned, not "
            "measured.")

    def step(self):
        cfg = self.cfg
        year = self.year
        # WHERE SCANDAL STOOD WHEN THE PLAYER LAST LOOKED. `state` prints the
        # chance of being denounced from the CURRENT scandal, and scandal moves
        # DURING the step - so a break tester read "scandal 21.9 ... 0% chance
        # of being denounced this year", pressed step once, and the same batch
        # printed the first warning and "RUN ENDS: denounced: as a sorcerer".
        # The figure was never wrong; it was answering about a year that had
        # already gone. A player needs the direction as well as the level, and
        # this is the only place that knows both.
        self.household.scandal_last_year = self.household.scandal

        # 0. PEOPLE WHOSE APPRENTICESHIP ENDED. This block used to sit at the
        #    very BOTTOM of step(), after the year's work had already been
        #    handed out - so machinists promised "ready in 102" were not usable
        #    on anything until 103, and a break tester timed both the message
        #    and the ready_year and found each a year late. A man who finishes
        #    his training at the turn of the year works that year.
        # People bought this year are not artisans this year.
        if self.household.training:
            still = []
            for row in self.household.training:
                cap, ready = row[0], row[1]
                trade = row[2] if len(row) > 2 else None
                count = row[3] if len(row) > 3 else 0.0
                if self.year >= ready:
                    if trade:
                        # A trade you taught. They are now yours to pay, and
                        # they are that trade and no other.
                        self.household.employees[trade] = self.household.employees.get(trade, 0.0) + count
                        self.household.log.append((self.year, "%g %s%s finish their training"
                                         % (count, trade, "s" if count != 1 else "")))
                        self._resync_pools()
                    else:
                        # They are trained now, so _resync_pools counts them
                        # from the people you actually hold - see the note
                        # there about why adding to self.household.artisans directly was
                        # thrown away at the next call.
                        self.household.log.append((self.year,
                                         "%g of the people you bought finish "
                                         "learning the work" % round(cap / 0.55, 1)))
                else:
                    still.append(row)
            # BEFORE the resync, not after: _resync_pools counts who is still
            # learning off this very list, so recomputing while the matured row
            # was still on it cost a whole extra year of everybody's time.
            self.household.training = still
            self._resync_pools()


        # 1. staff. ATTRITION IS UNCONDITIONAL: people die, are poached and grow
        #    old whatever your policy is. GROWTH IS NOT. It used to be, and that
        #    was the same fault as buying people without being asked: a player
        #    who never issued a single command watched the staff climb on its own.
        #
        #    With auto_hire on (the default for the optimizer, off for a player)
        #    the old smoothing toward capacity runs as before, which is what the
        #    long civilization runs are calibrated against. With it off, the only
        #    things that change the staff are hire, fire, train, buy and manumit.
        sc_cap, ar_cap, di_cap = self.staff_capacity()
        ATTRITION = self.STAFF_ATTRITION_RATE
        # PEOPLE ARE WHOLE. This used to multiply every trade's headcount by
        # (1 - ATTRITION) and carry on, so ten smiths lost exactly 0.35 of a
        # smith and the engine went on holding the fraction: a household
        # could read "1.32 artisans" or "0.03 engineers" on its own roster,
        # the latter drawing 0.03 of a wage while supervising nothing. The
        # user's objection was exact: a death is a discrete thing that either
        # happens to a particular person this year or does not, so each of
        # the whole people actually on the books now gets their own yearly
        # roll against self.rng - sorted by trade name so the draws happen in
        # the same order whatever PYTHONHASHSEED the process started with,
        # which is what every other rng loop over this dict already does
        # (see the "cannot pay" shedding loop below). Summed over many
        # people this reproduces the same 3.5%-a-year average the smooth
        # version was tuned against; no single person is ever a third of a
        # casualty.
        _lost = {}
        for trade_id in sorted(self.household.employees):
            head = int(round(self.household.employees[trade_id]))
            survivors = sum(1 for _ in range(head) if self.rng.random() >= ATTRITION)
            if head - survivors > 0:
                _lost[trade_id] = head - survivors
            if survivors > 0:
                self.household.employees[trade_id] = float(survivors)
            else:
                self.household.employees.pop(trade_id)
        # AND SAY SO. Now that a death is a whole person rather than three
        # hundredths of one, it is a thing that HAPPENED, and it was happening
        # in complete silence. A break tester hired five scholars, stepped five
        # years, watched the payroll go five, four, three, three, two, and found
        # nothing in the log or the events to say why - so they reported it as
        # staff vanishing, which is exactly what it looks like from the chair.
        # The rate is right (measured at 0.825 survival over five years against
        # 0.837 expected, across forty seeds); the reporting was missing.
        if _lost:
            self.household.log.append((year, "you lose %s to death and to better offers"
                             % ", ".join("%d %s%s" % (count, trade_id, "" if count == 1 else "s")
                                         for trade_id, count in sorted(_lost.items()))))
        self._resync_pools()
        # A HOUSEHOLD THAT CANNOT PAY ITS PEOPLE LETS THEM GO. This is the whole
        # answer to "you built it from nothing, so you must be able to rebuild
        # it": the thing that kept a ruined run frozen for two centuries was a
        # payroll it could not carry and never reduced. A run that fired its
        # staff, lived cheaply and started again earned 300 technologies; the
        # same run holding on to eleven people it could not pay earned 18.
        # TWO THINGS WERE WRONG WITH HOW THIS USED TO DECIDE, and a break tester
        # found both at once: they hired six smiths with two thirds of their
        # credit line still unused, stepped one year, and every one of the six
        # was gone, with nothing whatever in the log to say so.
        #
        # 1. The trigger was `capital < 0`, which is being overdrawn, not being
        #    unable to pay. A household with credit left borrows and makes
        #    payroll; that is what credit is for, and enforce_credit_limit
        #    already models the point where it runs out. Letting your staff go
        #    the first year you dip a denarius below zero, with the lender still
        #    willing, is not what an enterprise does.
        # 2. The gap it tried to close was measured with living_cost(), which
        #    INCLUDES the wage bill, so the deficit being closed was the payroll
        #    PLUS the founder's own food, rent and appearances. Firing people
        #    cannot buy your own dinner. Whenever base living exceeded revenue -
        #    which it does in every early game - the loop ran off the end of the
        #    staff list and emptied it. And the log line sat inside `if net >=
        #    0`, so the one case that always happened was the one case that said
        #    nothing at all.
        #
        # The honest rule is that your people are paid out of what is left after
        # everything else, INCLUDING what somebody will still lend you, and you
        # shed only the part of the payroll that will not cover.
        payroll = self.wage_bill()
        other = (self.upkeep() + (self.living_cost() - payroll)
                 + self.mine_operating_cost())
        # capital is negative in arrears; credit_limit() is how far into arrears
        # anyone will let you go, so this is what you can actually still spend.
        headroom = max(0.0, self.household.capital + self.credit_limit())
        can_pay = self.revenue() - other + headroom
        # NOT GATED BY A POLICY, and this is the one automatic thing that is not.
        # A policy switch is for something the game decides FOR you - who to
        # hire, what to mothball - and every one of those is yours to turn off.
        # People leaving a household that has no money and no credit to pay them
        # is not a decision the game is making on your behalf, it is the world
        # answering one you already made, the same as the arrears bleed below.
        # The `policy` reply says so in as many words now, because the tester
        # read its promise as covering this and was entitled to.
        if payroll > can_pay and self.household.employees:
            short = payroll - can_pay
            gone = 0.0
            # shed, dearest first, until the wages you are left with fit
            for trade_id in sorted(self.household.employees, key=lambda t: -self.annual_wage(t)):
                if short <= 0:
                    break
                wage = self.annual_wage(trade_id)
                if wage <= 0:
                    continue
                # A WHOLE PERSON, ROUNDED UP. `short / wage` is a quantity of
                # wages, not a quantity of people, and cutting that fraction
                # straight used to leave "0.3 smiths" still on the books,
                # still drawing 0.3 of a wage nobody had just said could be
                # paid. Rounding up sheds one whole person too many at worst,
                # which is the safe direction for a household that genuinely
                # cannot make payroll.
                cut = min(self.household.employees[trade_id], math.ceil(short / wage - 1e-9))
                self.household.employees[trade_id] -= cut
                short -= cut * wage
                gone += cut
                if self.household.employees[trade_id] < 0.5:
                    self.household.employees.pop(trade_id)
            self._resync_pools()
            # ALWAYS, not only when it worked. Losing the staff you paid to hire
            # is more consequential than any of the flavour events that do get
            # logged, and a player who is not told has to notice their own wage
            # bill hit zero to find out.
            if gone > 0.005:
                self.household.log.append((year, "you cannot pay everyone: %.1f of your staff "
                                     "leave for work that pays" % gone))
        # NOT `capital > 0`. This is the same catch-22 auto_open_ventures was
        # already caught by and had fixed: a household in arrears could never
        # take on the people whose work is the only way out of arrears. And a
        # run that keeps a project going keeps a balance in the red almost
        # permanently, so the gate was not "you are ruined", it was "you are
        # building something". A Rome run traced for this comment sat at about
        # -5,000 against a credit line of 8,000 for five hundred years with a
        # clear surplus of 650 a year and hired NOBODY: zero scholars and zero
        # craftsmen in 600 AD, 387 technologies, no goal. Deep in arrears is
        # deep in arrears; the affordability arithmetic below - which already
        # subtracts living cost, upkeep and the wages you are carrying - is
        # what decides how many, and it correctly says nobody when there is
        # nothing spare.
        _hire_room = (self.household.capital >= 0
                      or -self.household.capital <= self.credit_limit() * self.AUTO_HIRE_CREDIT_ROOM_SHARE)
        if (self.policy.get("auto_hire", not self.manual) and _hire_room):
            # Scaled by the SAME affordability figure staff_capacity() just
            # used for sc_cap/ar_cap (see the comment there): supervision-room
            # headroom is not a free six people, it is six people you still
            # have to pay for.
            extra = self.supervision_room() * self.household._staff_scale
            # THE SAME WALL hire() AND train() ENFORCE. This used to smooth
            # self.household.scholars toward sc_cap directly, mutating the pool itself
            # with no call anywhere near literate_capacity() - the wall a
            # player typing `hire scholar 12` was refused at 5.9, "ever, at
            # any price". A break tester turned auto_hire on, came back forty
            # years later to the same civilisation, and found 146.4 scholars:
            # one rulebook at the keyboard and a twenty-five-times-larger one
            # for the automation, for the identical number. See
            # literate_capacity()'s own docstring for the other half of this
            # fix - widening the wall enough that clamping to it here does not
            # simply strand every long civilisation run short of what the
            # tree actually asks for (the goal wants 25; building the
            # institutions staff_capacity() already credits widens this same
            # wall past that well before the goal is in reach).
            target_sc = min(sc_cap + extra * self.AUTO_HIRE_SCHOLAR_EXTRA_SHARE, self.literate_capacity("scholar"))
            desired_sc = self.household.scholars + (target_sc - self.household.scholars) * self.AUTO_HIRE_SCHOLAR_APPROACH_RATE
            target_ar = ar_cap + extra
            desired_ar = self.household.artisans + (target_ar - self.household.artisans) * self.AUTO_HIRE_ARTISAN_APPROACH_RATE
            # Keep the per-trade books honest about the aggregate: staff taken on
            # for you are generic craftsmen and scribes, and that is all they are.
            craft = max(0.0, desired_ar - self.household.freedmen - self.household.slaves * self.AUTO_HIRE_SLAVE_CRAFT_CREDIT)
            generic = self.household.employees.get("artisan", 0.0)
            specials = sum(value for trade_id, value in self.household.employees.items()
                           if trade_id not in ("artisan", "scholar") and trade_family(trade_id) == "craft")
            # SPECIALISTS MUST NOT EAT THE GENERALISTS. The generic bucket was
            # the remainder after every taught trade had taken its share, so
            # once the top-up kept five specialist trades at two apiece the
            # artisans were squeezed to nothing - a play tester watched theirs
            # go 6.0 to 0.03 while scholars filled every place, and since
            # artisans are what supervise a concern, twenty-two concerns closed
            # and their net went from +8,010 a year to -3,027. A household of
            # nothing but specialists cannot keep its own doors open.
            #
            # PEOPLE ARE WHOLE. This was the other place "0.03 engineers"
            # actually came from: the smoothing above is a continuous
            # approach to a continuous target, by design, and writing that
            # target straight into `employees` handed a player a fractional
            # person every single year forever, never quite arriving.
            # _stochastic_round spends the fractional remainder as this
            # year's chance of the next whole hire, so the long-run average
            # this formula was tuned against is unchanged and every actual
            # year's headcount is an integer (see its own docstring).
            # THROUGH hire(), NOT AROUND IT. The user asked why this does not
            # simply call hire() and reuse the code, and the honest answer was
            # that there is no reason: it grew as a direct write to the pools
            # and every rule hire() enforces had to be re-enforced here by hand,
            # or silently was not. The literacy ceiling was the one that got
            # noticed (a player refused at 5.9 while this reached 146), and it
            # was fixed by duplicating the check rather than sharing the code,
            # which left the others. Measured, for four artisans: hire() takes
            # 1,000 denarii as a finder's fee and the first year in advance,
            # records it so the year is not billed twice, and bids that trade's
            # price up to 1.021. This took the same four people for nothing and
            # left the market at 1.000. The automation was cheaper than playing
            # by hand, which is exactly backwards from what `policy` promises.
            #
            # Routing through hire() makes all of that impossible by
            # construction rather than by vigilance: the advance, the household
            # room, the literacy wall, the price pressure and the refusals are
            # whatever hire() says they are, for player and optimizer alike. A
            # refusal here is not an error - it is the same wall a player hits -
            # so it is simply not acted on.
            def _grow_to(trade, want):
                have = self.household.employees.get(trade, 0.0)
                delta = self._stochastic_round(want) - have
                if delta >= 1.0:
                    self.hire(trade, int(delta))
                elif delta <= -1.0:
                    self.fire(trade, int(-delta))
            _grow_to("artisan", max(craft * 0.25, craft - specials))
            if desired_sc > 0:
                _grow_to("scholar", desired_sc)
            # REPLACE THE PEOPLE YOU LOSE, trade by trade. Attrition was eating
            # the taught trades (the engineers went from 1.9 to 0.3 over sixty
            # years) and nothing ever replaced them, because the top-up only knew
            # about the two generic buckets. A programme that trains the first
            # machinists in the world and then lets them die out has not trained
            # anybody.
            # FROM THE TRADES YOU TAUGHT, not from the keys that happen to be
            # left. A trade falls out of `employees` entirely once the last of
            # them drops below 0.05, and this loop only ever looked at the
            # keys - so the moment a taught trade went to nothing it stopped
            # being replaced, permanently. That is the leak behind a Rome run
            # that built 829 technologies and could not begin
            # precision_three_plate: not that machinists were never taught, but
            # that the last one died and the top-up had already forgotten they
            # existed.
            for trade_id in sorted(set(self.household.employees) | set(self.household.trades_created)):
                if trade_id in ("artisan", "scholar"):
                    continue
                have = self.household.employees.get(trade_id, 0.0)
                want = max(have, self.TRADE_REPLACEMENT_TARGET_HEADCOUNT if trade_id in self.household.trades_created else 0.0)
                short = want - have
                if short > 0.02 and self.household.capital > self.annual_wage(trade_id) * self.TRADE_REPLACEMENT_AFFORDABILITY_YEARS:
                    self.household.employees[trade_id] = have + short
                    self.household.capital -= short * self.annual_wage(trade_id)
            self._resync_pools()
        # BUY A JOB WHEN A HANDFUL OF HANDS IS THE ONLY THING IN THE WAY.
        # Letting contracted craftsmen count toward a project's staff
        # requirement fixed the Norse deadlock for a person at a keyboard and
        # not at all for the optimizer, because nothing in the engine had ever
        # called commission(). A run that can see the wall, has the money, and
        # has no way to spend it on the wall is the same dead end wearing a
        # different hat.
        if self.policy.get("auto_commission", not self.manual):
            self.auto_commission_for_blocked()
        self.household.directors_extra += (di_cap - self.household.directors_extra) * self.DIRECTORS_EXTRA_APPROACH_RATE - self.household.directors_extra * ATTRITION
        self.household.artisans = max(0.0, self.household.artisans)
        self.household.scholars = max(0.0, self.household.scholars)
        self.household.directors_extra = max(0.0, self.household.directors_extra)
        # SAY IT WHEN IT CROSSES A WHOLE PERSON. A play tester noticed "10,175
        # founder-hours free this year (2,000 of your own, plus 4.5 deputies at
        # 1,800 hours each)" by accident, after playing for a century on the
        # assumption that their year was two thousand hours and would stay
        # that way. The single largest change to the resource the whole game
        # is built on had never announced itself.
        _whole = int(self.household.directors_extra)
        if _whole > int(getattr(self.household, "_said_deputies", 0)):
            self.household._said_deputies = _whole
            self.household.log.append((year, "you now have %d deput%s directing work in "
                                 "your name: your year is %s hours instead of "
                                 "%s. They came with the institutions you built"
                             % (_whole, "y" if _whole == 1 else "ies",
                                "{:,.0f}".format(self.director_pool()),
                                "{:,.0f}".format(self.cfg["founder_hours_per_year"]))))

        # 2. money
        self.economy = self.economy_index()
        living_cost = self.living_cost()
        # THE YEAR YOU PAID FOR IN ADVANCE IS NOT BILLED AGAIN. `hire` takes a
        # finder's fee and the first year's wages up front, and living_cost()
        # carries the whole payroll, so a smith at 281 a year cost 566 in his
        # first year: the advance, then the identical year again at the next
        # step. A break tester found hire-then-fire in one turn burned the
        # advance for no work at all.
        prepaid = min(living_cost, self.household.wages_prepaid)
        living_cost -= prepaid
        self.household.wages_prepaid = 0.0
        self.living_cost_paid += living_cost
        mine_cost = self.mine_operating_cost()
        self.household.mine_cost_paid += mine_cost
        self.household.capital += self.revenue() - self.upkeep() - living_cost - mine_cost
        # A mine you cannot pay for is a mine you stop working. Without this the
        # opex accrued for ever against a bankrupt enterprise: the England run
        # sank a large mine, lost its revenue and then ran three centuries at
        # minus four million denarii, unable to afford anything at all, which
        # the log reported as being "blocked" on a treadle lathe.
        if self.household.capital < 0 and self.mine_capacity and self.policy.get("auto_mothball", True):
            self.mothball_mines()
        # A CONCERN NEEDS SOMEBODY WATCHING IT EVERY YEAR, not only on the day
        # you open it. `open` refused without supervisors and then nothing ever
        # looked again, so a break tester hired five craftsmen, opened eleven
        # concerns in one turn, fired all six people, and watched net income
        # RISE - "EMPLOY: 0 people" with seventeen concerns running, and the
        # same loom still paying 435 a year in 1800 with nobody employed,
        # straight through the Black Death.
        # THE OTHER HALF OF THE SAME RULE, and applied FIRST: staff hired or
        # taught this same year (the block just above) should get first claim
        # on reclaiming what attrition shut, before anything is judged still
        # short and closed again. See reopen_restaffed_ventures's own
        # docstring for why this is not gated by auto_open - three
        # playtesters spent most of a run on the treadmill this closes.
        self.reopen_restaffed_ventures(year)
        self.close_unstaffed_ventures(year)
        # Open what plainly pays for itself, before the books are struck: a
        # concern you opened this year is a concern that earns this year.
        if self.policy.get("auto_open", not self.manual):
            self.auto_open_ventures()
        self.charge_interest(year)
        if self.policy.get("auto_shed", True):
            self.shed_loss_makers(year)
        self.warn_near_the_limit(year)
        self.enforce_credit_limit(year)

        # INSOLVENCY. A playtester ran to minus 4.12 million denarii over eighty
        # years and nothing whatever happened: no event, no block, no attrition.
        # That is not a hard game made easy, it is an accounting fiction, and it
        # quietly made every cost in the model optional.
        #
        # The consequence is deliberately the realistic one rather than a
        # dramatic one. Nobody arrests you for debt. What happens is that people
        # you cannot pay stop turning up, and nobody will extend you credit for
        # something new while you are in arrears.
        if self.household.capital < 0:
            # BEING IN DEBT IS NOT THE SAME AS BEING INSOLVENT. This counted a
            # year of arrears for every year capital was below zero, whatever
            # the household was earning - so a Rome run with revenue of 1,006
            # against 470 of living costs, paying its debt down at 522 a year,
            # was still "in arrears 183 years" and still refused permission to
            # start anything, which is what kept it from ever climbing out. A
            # household running a surplus is paying its creditors, and nobody
            # calls that insolvency; what the counter is for is the household
            # whose income does not cover its costs.
            _net = (self.revenue() - self.upkeep() - self.living_cost()
                    - self.mine_operating_cost())
            if _net > 0:
                self.household.insolvent_years = 0
            else:
                self.household.insolvent_years = getattr(self.household, "insolvent_years", 0) + 1
            floor = -max(self.INSOLVENCY_FLOOR_MIN, self.revenue() * self.INSOLVENCY_FLOOR_REVENUE_MULTIPLE)
            if self.household.capital < floor and self.household.insolvent_years >= self.INSOLVENCY_YEARS_BEFORE_BLEED:
                # wages unpaid: freedmen leave first, they are free to
                # A FLOOR, because the first version was a doom loop. Staff bled
                # without limit, so fewer people earned less, which deepened the
                # arrears, which bled more people. One Norse run sat insolvent
                # for 495 years with 2.9 artisans left, unable to recover and
                # unable to end. Insolvency should cost you your expansion, not
                # trap you in a state you can never leave: a household that has
                # shed everything also stops paying for it, and can climb back.
                bleed = min(self.INSOLVENCY_BLEED_CAP, self.INSOLVENCY_BLEED_RATE * self.household.insolvent_years)
                self.household.artisans = max(self.INSOLVENCY_ARTISAN_FLOOR, self.household.artisans * (1.0 - bleed))
                self.household.scholars = max(self.INSOLVENCY_SCHOLAR_FLOOR, self.household.scholars * (1.0 - bleed * self.INSOLVENCY_SCHOLAR_BLEED_DISCOUNT))
                if self.household.insolvent_years in (3, 6, 12, 25):
                    self.household.log.append((year, "IN ARREARS for %d years: staff are leaving "
                                         "because you cannot pay them" % self.household.insolvent_years))
                # ABANDONMENT, and this is what makes insolvency survivable.
                # The failed Norse run carried 3,920 denarii of upkeep against
                # 3,134 of revenue: permanently underwater, floored at three
                # artisans, simulating 495 years of nothing and reporting it as
                # "ran out of horizon". An enterprise that cannot maintain its
                # works does not pay for them for five centuries. It lets them
                # go, and the buildings fall down. You lose what they gave you
                # and can rebuild later, which is a real cost and a real way out.
                net = (self.revenue() - self.upkeep() - self.living_cost()
                       - self.mine_operating_cost())
                # ONLY WORKS THAT COST MORE THAN THEY RETURN, and only if you let
                # it happen at all. Both halves were wrong and a tester called the
                # result "an unrecoverable softlock", correctly: the loop ran
                # until the books balanced rather than until shedding stopped
                # helping, so once the genuine loss-makers were gone it went on
                # to destroy eleven works earning 2,700 a year against 330 of
                # upkeep, each one making the deficit worse, for ever. And it did
                # it whether or not auto_shed was switched off, in a game whose
                # own help says "every one of them is a switch you control".
                if net < 0 and self.policy.get("auto_shed", True):
                    burden = sorted((node_id for node_id in self.household.done
                                     if self.nodes[node_id]["up"] > self.nodes[node_id]["rev"]
                                     and node_id not in self.household.granted
                                     and not self.never_abandon(node_id)),
                                    key=lambda k: (self.nodes[k]["rev"] - self.nodes[k]["up"]))
                    shed = []
                    for node_id in burden:
                        if net >= 0:
                            break
                        node = self.nodes[node_id]
                        net += node["up"] - node["rev"]
                        # CLOSE IT, DO NOT UNLEARN IT - and above all do not do
                        # both. Discarding from `done` while adding to
                        # `mothballed` produced a state no verb could clear: a
                        # play tester lost precision_three_plate to a sack, and
                        # `start` sent them to `restore`, `restore` said they no
                        # longer knew how, `open` said they had not built it and
                        # `mothball` said there was nothing to shut. That node
                        # gates the whole precision branch, so `available` read
                        # "0 startable now" for a hundred and eighty years while
                        # they sat on a quarter of a billion denarii. The same
                        # pair of lines was fixed in enforce_credit_limit and in
                        # shed_loss_makers and survived here.
                        self.household.operating.discard(node_id)
                        self.household.mothballed.add(node_id)   # you can buy it back
                        shed.append(node_id)
                    if shed:
                        # NAME THEM, for the same reason as shed_loss_makers and
                        # the creditors' seizure below: a bare count does not
                        # tell a player what they lost or why it later
                        # reappeared mothballed rather than gone for good.
                        self.household.log.append((year, "ABANDONED %d works you could no longer "
                                             "maintain; they have fallen into disrepair: %s"
                                             % (len(shed), ", ".join(shed))))
        else:
            self.household.insolvent_years = 0
        # A standing workforce policy, and ONLY when the optimizer is playing.
        #
        # This used to run in manual mode too, so a player who never issued a
        # buy command watched `slaves` climb on its own with no prompt and no log
        # line. A tester caught it and put the objection better than I can: the
        # game's own justification for modelling slavery at all is that "a model
        # that hides it lies about the cost of everything", and then it was
        # hiding the acquisition. Buying people on someone's behalf without
        # telling them is the worst version of that.
        if self.policy.get("auto_buy_people", False):
            if self.household.capital > 6000 and self.household.artisans < 12 and self.running("workshop_first"):
                got = self.buy_slaves(min(6, int(self.household.capital // 1500)))
                if got:
                    self.household.log.append((year, "bought %d people for the workshop" % got))
        if self.policy.get("auto_manumit", not self.manual) and self.household.slaves:
            if self.rng.random() < self.AUTO_MANUMIT_ANNUAL_CHANCE:
                freed = self.manumit(max(1, self.household.slaves // self.AUTO_MANUMIT_SHARE_DIVISOR))
                if freed:
                    self.household.log.append((year, "freed %d people" % freed))
        # currency debasement and war damage now come from the civilization's
        # own hazard list, not from Rome's dates baked into the engine
        if self.output_factor < 1.0:
            # A STATE THAT CAN DEFEND ITSELF REBUILDS FASTER. This used to be
            # a flat rate no matter what the founder had done about the war -
            # a civilization that built the whole military branch and one
            # that ignored it recovered from the SAME war at the SAME speed,
            # which is the finding that started this change: measured against
            # a founder with none of the tree's 111+ military nodes, nothing
            # about the state's fortunes moved at all. military_leverage() is
            # the same count update_protection() and
            # hazard_relief("output_factor") (society.py) already read off
            # self.household.done; at full leverage the recovery rate doubles, so an
            # armed empire is back to normal trade in roughly half the years
            # an unarmed one takes, not instantly - the war still happened
            # and the years it cost are not given back.
            self.output_factor = min(1.0, self.output_factor
                                     + self.OUTPUT_RECOVERY_RATE * (1.0 + self.military_leverage()))
        # Population and the wage premium it drives recover/build in on their
        # own clock too, and must run before this year's shocks get a chance
        # to add a fresh deficit - see _demographic_recovery for why.
        self._demographic_recovery(year)
        # Literacy and taught-trade naturalisation move on the same kind of
        # slow, generational clock as population above - see
        # SocietyMixin.advance_society (society.py) for the mechanism. Run
        # here, before 4a2's auto_train reads literate_capacity() below, so
        # a year's schooling gain is visible to this same year's teaching
        # decisions rather than lagging a full step behind them.
        self.advance_society(year)
        # 2c. THRESHOLD GOALS. A node carrying a `win_condition` (see
        # data.py's WIN_CONDITION_LABELS and tech_tree.json's own goals
        # using one) is never built - start_reason refuses it outright -
        # it completes itself the moment a live measurement crosses its
        # target. Checked here, right after the literacy/trade growth this
        # same measurement usually depends on has moved for the year, so a
        # threshold crossed this year is seen this year rather than lagging
        # a full step behind it.
        self._check_win_conditions(year)

        # 3. dated shocks
        if self.events:
            self._shocks(year)
            if self.dead_reason:
                return

        # 4a2. TEACH THE TRADES THIS SOCIETY DOES NOT HAVE. The optimizer has to
        #      do this for itself or half the tree is unreachable; a player does
        #      it with `train`, or turns this on.
        if self.policy.get("auto_train", not self.manual):
            want = {}
            # LOCAL, PER-YEAR MEMO for market_supply()/trade_available().
            # Both are pure functions of staff and trades_created, which this
            # whole block only READS - train(), below, adds to trades_created,
            # but that happens once, at the very end, after every use of these
            # memos - so the same handful of distinct trade names (maybe
            # thirty) get recomputed from scratch once per NODE that lists
            # them in `lab`, and hundreds of nodes across the tree share the
            # same absent trade (machinist, engineer, ...). This dict is a
            # plain local, created fresh every call and discarded when the
            # block ends, so it needs no invalidation logic at all: nothing
            # outside this block ever reads it, so it cannot go stale.
            _ms_memo, _ta_memo = {}, {}
            def _market_supply(t):
                value = _ms_memo.get(t)
                if value is None:
                    value = _ms_memo[t] = self.market_supply(t)
                return value
            def _trade_avail(t):
                value = _ta_memo.get(t)
                if value is None:
                    value = _ta_memo[t] = self.trade_available(t)
                return value
            # Anything already in hand that has lost its trade comes FIRST: those
            # projects are burning a slot and will be halted if nobody turns up.
            for node_id in self.household.active:
                for trade_id in self.nodes[node_id]["lab"]:
                    if _market_supply(trade_id) <= 0.0:
                        want[trade_id] = want.get(trade_id, 0) + 500
            # WORK THE PLAYER COULD START TODAY, not the whole tree. The old
            # test was "direct prerequisites satisfied", which is not "wanted":
            # it looked past cost, staff, state approval and every OTHER trade
            # a node needs, so it walked deep into the order training engineers,
            # then chemists, machinists and opticians, with no active project
            # asking for any of them. Its own description promises "when a
            # project needs them", and a project three tiers away with money
            # you do not have is not a project you need anything for yet.
            # ignore_trade asks the one question that answers that: if this
            # trade existed, would everything ELSE already let it start?
            # EXISTING IS NOT THE SAME AS ANYBODY BEING LEFT. A trade you
            # taught stays "available" for ever, so once the last machinist
            # had died of old age this loop skipped every node that needed
            # one and nobody was ever taught again. A Rome run built 829
            # technologies, sat on 31.9M denarii, and could not begin
            # precision_three_plate - which gates master_screw, the screw
            # lathe and the entire precision branch, ninety-nine of the
            # hundred and forty-six nodes on the road to the goal. This is
            # the same distinction start_reason learned an hour earlier.
            # Hoisted out of the loop below: it closes only over `self` and
            # the memos above, never over the loop variable `k`, so defining
            # it fresh on every one of ~2,800 iterations bought nothing.
            #
            # _gone(t) ITSELF IS NOW MEMOIZED TOO (_gone_memo), for the same
            # reason _market_supply/_trade_avail already are: it reads only
            # _trade_avail(t), _market_supply(t) and
            # self._trade_headcount_pending(t), and the last of those
            # (labour.py) reads only self.household.training and self.household.employees -
            # neither mutated anywhere in this block; train(), at the very
            # end of it, is the only thing that changes either, exactly as
            # the comment above already established for the other two. So
            # _gone(t) is just as pure a function of (staff, trades_created)
            # across this whole block as they are, and is safe to cache the
            # same way.
            #
            # That matters because this used to be a plain function called
            # through `any(_gone(t) for t in n["lab"])`, and the per-trade
            # RESULT (not just its two cheap sub-memos) was never cached -
            # so recomputing it, for the same handful of distinct trade
            # names, cost one Python function call for EVERY ONE of the
            # ~2,800 nodes in `order` that names them, even after the first
            # node had already worked out the answer. Profiling 150 years
            # found the `any()` generator alone at 895,244 calls / 0.83s
            # cumulative. _is_gone below answers the identical question,
            # through the identical `any()` (so a node whose FIRST lab
            # trade is already known gone, or one that fails
            # start_reason() right after, costs exactly what it always
            # did - no extra work done on the strength of a guess that it
            # would be needed), but every trade's verdict is computed once
            # and reused for every later node that names it, instead of
            # recomputing the same two calls from scratch each time.
            _gone_memo = {}
            def _is_gone(t):
                value = _gone_memo.get(t)
                if value is None:
                    value = _gone_memo[t] = (
                        not _trade_avail(t)
                        or (_market_supply(t) <= 0.0
                            and self._trade_headcount_pending(t) <= 0.0))
                return value
            for node_id in self.order:
                if node_id in self.household.done or node_id in self.household.active:
                    continue
                node = self.nodes[node_id]
                if not any(_is_gone(trade_id) for trade_id in node["lab"]):
                    continue
                if not self.start_reason(node_id, ignore_trade=True)[0]:
                    continue
                for trade_id in node["lab"]:
                    if _is_gone(trade_id):
                        want[trade_id] = want.get(trade_id, 0) + 1
            # NOT EVERY YEAR. Teaching two of a trade costs about nine hundred
            # of the founder's two thousand hours plus their keep, and once
            # re-teaching a lost trade was possible at all the loop did it
            # continuously: three Rome seeds fell from 829, 858 and 1,257
            # technologies to 229, 56 and 188, the whole difference going into
            # a teaching treadmill. A trade is worth restoring; it is not worth
            # half of every year for ever.
            _taught = self.household.last_taught
            want = {trade_id: value for trade_id, value in want.items()
                    if year - _taught.get(trade_id, -999) >= self.RETEACH_EVERY}
            # AND ONLY IF YOU CAN PAY THEM. train() checked hours, literacy and
            # household room and never once looked at money - so a Rome
            # household earning 1,232 a year taught itself two engineers at
            # 625 each, and every year after that its whole income went on
            # their wages. That is the poverty trap three separate testers
            # described from three directions: "auto_train bought me chemists,
            # engineers, machinists and opticians I had no work for", "-6,900
            # denarii in three steps", and a run that sat at 144 technologies
            # from 125 AD to 300. A trade you cannot pay for is not a trade you
            # have; it is a wage bill that stops you building anything.
            #
            # Two standards, because the two cases are not alike. A trade a
            # project ALREADY IN HAND is waiting on (scored 500 above) is worth
            # borrowing against: that work is paid for and stops without it.
            # A trade for something you might start one day has to come out of
            # what you are actually clearing.
            _spare_tr = self.revenue() - self.upkeep() - self.living_cost()
            for trade_id, _score in sorted(want.items(), key=lambda kv: (-kv[1], kv[0]))[:1]:
                _wages = 2.0 * self.annual_wage(trade_id)
                _budget = (max(0.0, _spare_tr) + max(0.0, self.household.capital) * 0.10
                           if _score >= 500 else max(0.0, _spare_tr) * 0.5)
                if _wages > _budget:
                    continue
                _first = trade_id not in self.household.trades_created
                ok, _msg = self.train(trade_id, 2)
                # THE COOLDOWN IS ON TEACHING, NOT ON TRYING. Recording the
                # attempt meant a refusal - no room in the household, no hours
                # left, nobody to teach from - burned the trade's whole
                # twenty-five years, so the run went on needing machinists and
                # never asked again.
                if ok:
                    _taught[trade_id] = year
                    self.household.log.append((year, "you begin teaching the first %ss this "
                                         "world has ever had" % trade_id if _first else
                                     "the last %ss are gone; you begin teaching "
                                     "more" % trade_id))

        # 4a(ii). THE STANDING "WORK" DIRECTIVE. `work` (protocol.py) sells
        # hours for wages the moment a player types it; `allocate` lets them
        # say "sell N hours a year this way" ONCE and have it happen every
        # year without retyping it, the same standing-instruction idea as
        # the project directives just below. Run BEFORE `pool` is struck so
        # director_hours_committed() (which counts wage hours already sold
        # this year) sees it, exactly as it would if the player had typed
        # `work` by hand a moment ago.
        #
        # TOPPED UP, NOT DOUBLED. A player who already called `work` by hand
        # earlier this same turn has already sold some of the hours this
        # directive wants; this only sells the remainder, never the whole
        # directive again on top of what was already sold.
        _wd = self.household.hour_allocations.get("work")
        if _wd and _wd > 0 and self.household.work_trade:
            _already = getattr(self.household, "wage_hours_this_year", 0.0)
            _want = max(0.0, _wd - _already)
            if _want > 0.5:
                _room = max(0.0, self.director_pool() - self.director_hours_committed())
                _take = min(_want, _room)
                _got = 0.0
                if _take > 0.5:
                    _pay, _werr = self.work_for_wages(self.household.work_trade, _take)
                    # pay > 0 with an error is a WARNING (a bad trade, or
                    # starving an active project of its last hours), not a
                    # refusal - see work_for_wages's own docstring. The sale
                    # happened either way; only a genuine refusal (pay <= 0)
                    # means none of it landed.
                    if _pay > 0 or not _werr:
                        _got = _take
                # SAY SO, THE SAME WAY AN UNHONOURED PROJECT DIRECTIVE DOES,
                # BELOW. A standing instruction nobody is told failed is the
                # same unfairness either way: the founder-hours it asked for
                # either went unsold or went somewhere the player never
                # chose.
                if _wd - (_already + _got) > 1.0:
                    self.household.log.append((year, "DIRECTED HOURS UNUSED: your standing "
                                         "order to sell %s hours a year as a "
                                         "%s only managed %s this year - %s. "
                                         "'allocate' changes or clears it"
                                     % ("{:,.0f}".format(_wd), self.household.work_trade,
                                        "{:,.0f}".format(_already + _got),
                                        "no more of your own hours were left "
                                        "to sell once your projects and "
                                        "training had theirs"
                                        if _room < _want else
                                        "nobody here will pay for that trade "
                                        "any longer" )))

        # 4b. start new projects
        pool = max(0.0, self.director_pool() - self.director_hours_committed())
        hired_left = self.hired_cap()
        # MANUAL MODE STOPS HERE. This loop is "the optimizer": it walks
        # `order` and starts whatever it judges best, which is exactly the
        # behaviour a free-choice player must NOT get. The old `play` command
        # let you type a node id, but that only did `order.remove/insert(0)`
        # a few lines above this loop's own input; the loop then ran anyway
        # and started other things you never asked for. `self.manual` cuts
        # that off at the root: nothing is ever added to `self.household.active` here,
        # so the only way anything starts is start_project(), called by a
        # human or a script. Everything below this block (materials, staff,
        # money, hazards, the calendar) is untouched by `manual` and keeps
        # running exactly as before.
        if not self.manual and year >= self.household.credit_frozen_until:
            # More directors means more things in hand at once, and a big trained staff
            # lets routine work proceed without the founder watching it.
            # How many things can be in hand at once. I tried doubling this on
            # the theory that money is now the real constraint and attention need
            # not stand in for a budget. It made every civilization worse,
            # including Rome, from 33% of runs reaching the transistor to none:
            # more projects in hand divide the same purse into smaller annual
            # payments, so everything crawls and nothing finishes. Spreading a
            # fixed budget across more work is not more work. Left as it was.
            max_active = int(self.MAX_ACTIVE_PROJECTS_BASE
                             + self.director_pool() / self.MAX_ACTIVE_PROJECTS_PER_DIRECTOR_HOURS
                             + self.household.scholars / self.MAX_ACTIVE_PROJECTS_PER_SCHOLAR
                             + self.household.artisans / self.MAX_ACTIVE_PROJECTS_PER_ARTISAN)
            # EARN A LIVING FIRST. Now that a project must actually be paid for,
            # a founder who arrives with 400 denarii and walks the goal-ordered
            # list starves: every human tester worked this out for themselves
            # within a few turns and went hunting for the cheap revenue nodes,
            # and the optimizer had no such instinct. When the surplus is thin,
            # prefer whatever pays best for what it costs; the goal order resumes
            # the moment there is money to pursue it with.
            fixed0 = self.upkeep() + self.living_cost() + self.mine_operating_cost()
            candidates = self.order
            if self.revenue() - fixed0 < max(400.0, fixed0 * 0.25):
                earners = [node_id for node_id in self.order
                           if self.nodes[node_id]["rev"] - self.nodes[node_id]["up"] > 0]
                earners.sort(key=lambda k: self.project_cost(k)
                             / max(1.0, self.nodes[k]["rev"] - self.nodes[k]["up"]))
                # `set(earners)` HOISTED OUT OF THE COMPREHENSION. Written
                # inline as `if k not in set(earners)`, this rebuilt the set
                # from scratch on every one of the 2,833 iterations of the
                # walk over self.order - one throwaway set per node, an
                # O(|order| x |earners|) rebuild for what a single set
                # covers in O(|order|). Profiling a 300-year single-seed run
                # found this one line costing 0.81s of self time over just
                # 21 calls - a tight-money branch, but each call did the
                # equivalent of an extra multi-hundred-thousand-item pass.
                # See PERFORMANCE.md.
                _earner_set = set(earners)
                candidates = earners + [node_id for node_id in self.order if node_id not in _earner_set]
            # INCREMENTAL COUNT, NOT A SET REBUILT PER ITERATION. Written as
            # `len(self.household.active) - len(self.household.bountied & set(self.household.active))`
            # inside the loop below, this rebuilt `set(self.household.active)` from
            # scratch on every one of the 2,849 iterations of `candidates` -
            # the identical mistake `_earner_set` (above) had already been
            # fixed for, 30 lines earlier in this same function. Unlike
            # `earners`, `self.household.active` IS mutated inside this loop (a normal
            # start at the bottom, or post_bounty() below, which adds to both
            # `self.household.active` and `self.household.bountied` at once), so the fix cannot
            # be "hoist one set outside the loop" - it has to track the two
            # mutations as they happen instead:
            #   - post_bounty(k) succeeding adds k to self.household.active AND to
            #     self.household.bountied together, so a bountied project never counts
            #     against max_active: _non_bountied_active is left unchanged.
            #   - a normal start only adds k to self.household.active, so
            #     _non_bountied_active goes up by one.
            # Nothing else in this loop's body (can_start, project_cost,
            # funding_capacity, committed_spend, bounty_eligible) touches
            # self.household.active or self.household.bountied - checked in projects.py and
            # economy.py - so these two increments are the only places the
            # tracked count can move, and it is computed once up front
            # (O(active), not O(order)) rather than every iteration.
            _non_bountied_active = len(self.household.active) - len(self.household.bountied & set(self.household.active))
            for node_id in candidates:
                if _non_bountied_active >= max_active:
                    break
                if not self.can_start(node_id):
                    continue
                node = self.nodes[node_id]
                # do not start something we cannot plausibly fund this decade.
                # material_cost_factor is geography.json's contribution: a
                # located material (mat_gutta_percha and the like) costs more
                # or less to reach depending on how far THIS civ actually is
                # from it, not on Rome's distance to it.
                # Do not begin what you cannot pay for. This used to allow three
                # times your capital plus six years of GROSS revenue, which was
                # harmless while the money was notional and the bill was quietly
                # forgiven at completion. Now that the bill has to be paid, the
                # same heuristic commits the household to more than it can ever
                # fund, the creditors halt everything, and the spend is lost.
                # INTEREST IS A FIXED COST, and leaving it out is how a
                # household in arrears decides it has a surplus. A Rome run
                # paying 552 a year of interest computed its five years of
                # headroom as though that money did not exist, committed
                # against it, and went from -369 to -7,827 in twenty-five
                # years - then bled for four centuries. Every other net in this
                # program was taught to count arrears; this one was missed
                # because it is not a net, it is a budget.
                #
                # funding_capacity()/committed_spend() (economy.py), NOT A
                # SECOND COPY OF THIS FORMULA. This heuristic is where the
                # formula was first worked out; it has since been factored
                # out so the player-facing aggregate warning in `start`
                # (protocol.py) answers the identical question with the
                # identical number, rather than risking the two quietly
                # drifting apart.
                room = self.funding_capacity() - self.committed_spend()
                if self.project_cost(node_id) > room:
                    continue
                if node_id in self.bounty_set and self.bounty_eligible(node_id) and self.post_bounty(node_id):
                    # post_bounty() just added k to both self.household.active and
                    # self.household.bountied - the count of NON-bountied active
                    # projects is unchanged.
                    continue
                # lab_left starts full here too, for the same reason
                # start_project (projects.py) sets it at creation rather than
                # leaving lab_year_draw to guess it from ph_left the first
                # time it runs - see the comment there.
                self.household.active[node_id] = dict(ph_left=float(node["ph"]), yrs=0.0, spent=0.0,
                                      cost_left=self.project_cost(node_id),
                                      lab_left=dict(node["lab"]))
                _non_bountied_active += 1

        # 4c. materials. Buy the woodland and dig the beds BEFORE the shortage
        #     bites, which is what a competent manager does and what the old
        #     model never had to think about at all.
        self.commission_mines()
        thr = self.resource_throttle()
        # THE GATE WAS THE DEADLOCK. `capital > 3000` was meant to stop this
        # spending a poor household's last coin, and instead it made charcoal
        # a wall nobody in arrears could ever climb: no woodland, so the
        # furnaces run at a fraction, so nothing is built, so no money, so
        # still no woodland. An England run measured 521 charcoal-short years
        # out of 700, ended on 31 technologies with 71 hectares of coppice and
        # -6,332 in hand, and settled its debts twenty-eight times.
        #
        # Coppice is the cheapest thing in the tree and the one that decides
        # whether a furnace runs at all, so what it is really gated on is
        # whether you can raise the price of some, which is what
        # spending_power says. Below that the branch does nothing anyway,
        # because buy_forest refuses what you cannot pay for.
        _can_raise = self.spending_power("buy")
        if (thr < 0.9 and _can_raise > self.FOREST_COST_PER_HA * self.price_index
                and (self.policy.get("auto_mine", not self.manual)
                     or self.policy.get("auto_forest", not self.manual))):
            # Charcoal is GROWN, so the answer is woodland. Everything else in
            # this list is DUG, so the answer is a mine, and the old model had
            # no answer at all for coal: the binding constraint fell through
            # both branches and the run simply sat throttled. That is why coal
            # showed 1,669 shortage-years in a 395 year run.
            if self.household.binding == "charcoal":
                if self.policy.get("auto_forest", not self.manual):
                    # SIZED FROM THE SHORTFALL, like the mine branch below,
                    # rather than from a flat share of cash. A tenth of a
                    # denarius of capital bought a ten-thousandth of a hectare
                    # while the demand was measured in hundreds of tonnes.
                    _need_t = (self.annual_material_demand().get("charcoal_kg", 0.0)
                               / 1000.0) - self.household.forest_ha * self.CHARCOAL_PER_HA
                    _want_ha = max(0.0, _need_t) / max(self.CHARCOAL_PER_HA, 1e-9)
                    _afford_ha = (_can_raise * 0.35
                                  / (self.FOREST_COST_PER_HA * self.price_index))
                    self.buy_forest(min(400.0, _want_ha, _afford_ha))
            elif (self.household.binding in self.MINE_CAPEX_PER_T_YR
                    and self.policy.get("auto_mine", not self.manual)):
                # Size the mine from ALL the material keys that feed this
                # bucket, not one of them. The throttle counted iron ore AND
                # iron bar against "iron"; the investment response looked only
                # at iron bar. A run needing 10,330 tonnes of ore a year sank a
                # mine sized for the 13 tonnes of bar, stayed throttled for
                # centuries, and ended with its capital untouched.
                dem = self.annual_material_demand()
                # DERIVED FROM MATERIAL_CHECKS, not a second hand-kept copy of
                # it. This was a literal dict, and the moment copper wire,
                # drawn wire and gold were added to MATERIAL_CHECKS - so that
                # 36 electrical nodes and the central bank's thousand
                # kilograms could be throttled at all - a Rome run died with
                # KeyError: 'gold' the first year gold was the binding
                # material. Two lists of the same thing is one list too many,
                # and the regression suite could not catch it because no check
                # runs a long enough optimizer game to make gold bind.
                # sorted(), because this feeds a float sum.
                keys = tuple(sorted(material for material, (bucket, _tag)
                                    in self.MATERIAL_CHECKS.items()
                                    if bucket == self.household.binding))
                short = sum(dem.get(material, 0.0) for material in keys)
                want = max(0.0, short - self.mine_capacity.get(self.household.binding, 0.0))
                self.open_mine(self.household.binding, min(want, self.household.capital * 0.25
                                                 / max(1.0, self.MINE_CAPEX_PER_T_YR[self.household.binding])))
                # Iron and the base metals are smelted with charcoal, so the
                # ore is only half the answer.
                if self.household.binding in ("iron", "copper", "lead"):
                    self.buy_forest(min(200.0, self.household.capital / 1800.0))
            elif (self.household.binding == "saltpetre"
                    and self.policy.get("auto_mine", not self.manual)):
                # GATED, like every other automatic purchase. This branch sat
                # outside the policy check and took five per cent of a manual
                # player's capital every year they were short of nitre,
                # without a line in the log and without anything they typed.
                # A FLAT CEILING, AND IT IS NOT AN OVERSIGHT. Sizing this to
                # the measured shortfall the way the mine branch above does
                # is the obvious symmetry, it was tried, and it measured
                # WORSE on every count: Rome's saltpetre shortage went from
                # 277 run-years to 678, its reputation from 99 to 31, and its
                # first blocked node regressed from point_contact_transistor -
                # the last step of the whole programme - back to
                # atomic_theory, which it had cleared in its third century.
                # Spending a quarter of capital a year against a shortfall
                # that beds cannot close at any affordable scale starves
                # everything else, and in a household that falls into arrears
                # the interest then pins it there. Two thousand denarii a year
                # is what leaves the rest of the programme funded.
                #
                # The shortage is real and unresolved; more money is not the
                # answer to it, and this comment is here so the next person to
                # notice the asymmetry does not spend the afternoon I did.
                spend = min(self.household.capital * 0.05, 2000)
                self.household.capital -= spend
                self.household.nitre_bed_m2 += spend / self.NITRE_COST_PER_M2
                self.household.log.append((year, "laid down %d square metres of nitre bed "
                                     "for %d denarii (auto_mine)"
                                 % (spend / self.NITRE_COST_PER_M2, spend)))
        if thr < 0.6 and self.household.binding:
            # SAY WHAT TO DO ABOUT IT. A play tester read "SHORT OF SALTPETRE:
            # work at 5% of plan" for thirty years and could not find out what
            # saltpetre was for, who wanted it, or what would fix it. A number
            # that low with no remedy attached reads as the game being stuck.
            self.household.log.append((year, "SHORT OF %s: work running at %d%% of plan. %s"
                             % (self.household.binding.upper(), thr * 100,
                                self.shortage_remedy(self.household.binding))))

        # 5. progress. Director hours go to the HIGHEST-PRIORITY active projects
        #    first, not spread evenly: a director who gives every project equal
        #    attention finishes nothing, which is a real failure mode but not the
        #    one we are trying to model here.
        #
        # ONLY THE HANDFUL OF KEYS active_sorted ACTUALLY NEEDS, NOT EVERY
        # NODE IN THE TREE. This used to be a bare
        # `{k: i for i, k in enumerate(self.order)}` - a fresh 2,849-entry
        # dict built from scratch every single year to answer `rank.get(k,
        # 9999)` for the at most a few dozen keys in self.household.active. Nothing
        # below reads `rank` for any node NOT in self.household.active (checked: its
        # only other use is the `_pool_rank` loop variable a few lines
        # further down, an unrelated name), so recording a position for
        # every other one of the ~2,849 nodes was pure waste - 0.64ms/year
        # of pure self time with nothing under it, since dict-comprehension
        # and enumerate are both C-level with no further calls to profile.
        # This still walks self.order and cannot skip any of it in the
        # worst case (an active key can be anywhere in `order`), so it is
        # not a complexity win - but it stops paying for ~2,849 dict
        # insertions when only a few dozen are ever read, and exits the
        # walk the moment every active key's position has been found
        # (start_project, in projects.py, moves a project to the FRONT of
        # `order` the instant a human starts it by hand, so active keys
        # skew early there in practice, though the automated 4b loop above
        # does not reorder `order` and gives no such guarantee - the early
        # exit is a bonus, not a requirement of correctness). Recomputed
        # fresh every call, exactly as before: no cache, no staleness risk.
        _active_left = set(self.household.active)
        rank = {}
        if _active_left:
            for i, node_id in enumerate(self.order):
                if node_id in _active_left:
                    rank[node_id] = i
                    _active_left.discard(node_id)
                    if not _active_left:
                        break
        # A STANDING ALLOCATION IS A PROMISE, NOT A PRIORITY BID. Without
        # this, a project the player explicitly told `allocate` to give 500
        # hours a year could still be starved by three higher-`order`
        # undirected projects taking the whole pool first - the exact
        # opposite of what asking for an explicit split means. Every project
        # the player has put a standing instruction on is moved to the
        # FRONT of the queue (still ordered among themselves by the usual
        # priority, so two directed projects do not disagree about which of
        # them goes first); everything without one shares whatever is left
        # exactly as it always has, by the same `order`-based priority. A
        # player who never calls `allocate` has an empty hour_allocations,
        # every project sorts into the same single undirected bucket it
        # always did, and this line changes nothing for them.
        active_sorted = sorted(
            self.household.active,
            key=lambda k: (0 if self.household.hour_allocations.get(k, 0.0) > 0 else 1,
                           rank.get(k, 9999)))
        remaining = pool
        self.household.trade_hours_used = {}
        # Summed as the loop runs, not re-read from self.household.active afterwards,
        # because a project that completes THIS year is popped from
        # self.household.active before we would get to it. See the hours_this_year
        # summary this feeds, below the loop.
        hours_effective_total = 0.0
        # NAMED, NOT JUST STORED ON THE PROJECT. `why_underfunded` (set below,
        # in the arrears branch) answered "why is this stalled" when a player
        # thought to ask `why` or `portfolio` - but a Rome playtester lost
        # several turns of confusion before finding it, and wrote that the
        # consequence "isn't obvious from any single screen... reads more
        # like flavor than a mechanical warning". Founder-hours are the one
        # resource that never banks: a year of them lost to arrears and never
        # announced is the least fair thing a status screen can leave out.
        # Collected here and logged once, after the loop, so a step that
        # starves three projects at once gets one clear line, not three.
        _arrears_hours_lost = []
        # AN ALLOCATION THE PLAYER EXPLICITLY ASKED FOR, AND DID NOT GET.
        # hour_allocations is a promise the player made about their OWN one
        # resource that never banks; silently handing back less than it
        # asked for - because the project's own pace, its trade, or its
        # money was the real ceiling, not the founder's hours - is the same
        # unfairness the arrears line above exists to stop, aimed at a
        # player who took the extra step of directing their hours on
        # purpose. Collected here, per project, and logged once below.
        _directed_hours_unused = []
        # WHY A PROJECT IS GETTING THE SHARE IT IS GETTING, STORED HERE AND
        # NOWHERE ELSE. A player who had already won the game asked for
        # exactly this: "this project is receiving 420 of your 25,000
        # available directed hours this year because 11 active projects are
        # sharing organizational attention" - and the only honest way to
        # print that sentence is to read the numbers this loop actually used,
        # never to guess at them again from outside. pool_total/active_count
        # are the same for every project processed this step; rank and
        # remaining_before are this project's own position in the queue and
        # what was left of the pool when its own turn came. _agent_state and
        # `portfolio` (protocol.py) read these fields back verbatim - they do
        # not, and must not, recompute a share that could then disagree with
        # what this loop actually handed out.
        _pool_total_this_year = pool
        _pool_active_count_this_year = len(active_sorted)
        for _pool_rank, node_id in enumerate(active_sorted, start=1):
                project_state = self.household.active[node_id]
                node = self.nodes[node_id]
                project_state["pool_total_this_year"] = _pool_total_this_year
                project_state["pool_active_count_this_year"] = _pool_active_count_this_year
                project_state["pool_rank_this_year"] = _pool_rank
                project_state["pool_remaining_before_this_year"] = round(remaining, 1)
                # IS THERE ANYBODY TO DO THE WORK? If a trade this project needs
                # has vanished since it started (the machinists you taught died
                # out, say), nothing can be done on it this year, and your own
                # hours should go somewhere they are useful rather than into a
                # project that cannot absorb them.
                #
                # This matters more than it sounds. Without it a project whose
                # trade had disappeared sat in `active` for ever: hours went in,
                # no money was spent because no work was done, so the bill was
                # never paid, so it could never complete, so it never released
                # the slot. Four of those deadlocked a run at 98 technologies for
                # two hundred and fifty years.
                #
                # ONLY A TRADE THIS PROJECT STILL OWES SOMETHING TO. This used to
                # test n["lab"]'s ORIGINAL total (`want > 0`), which never goes
                # back to zero no matter how much of that trade's hours the
                # project has already drawn - lab_year_draw and trade_draw_plan
                # both correctly stop asking a trade for more once lab_left hits
                # zero, but this check kept vetoing the project on it forever. A
                # Han playtester fired a specialist whose hired-labour line
                # already read "0% owed" - the trade had nothing left to give
                # this project - and the very next step killed it anyway with
                # "no engineer here", a reason `why` had never shown because
                # `_waiting_on` (protocol.py) already knew, correctly, that
                # lab_left made this trade a non-issue. Two places answering
                # "does this project still need this trade" differently; this
                # makes the stall check agree with the one that draws the hours.
                _lab_left = project_state.get("lab_left")
                if _lab_left is None:
                    _lab_left = node["lab"]
                blocked = [trade_id for trade_id, want in node["lab"].items()
                           if want > 0 and _lab_left.get(trade_id, want) > 0
                           and self.market_supply(trade_id) <= 0.0]
                if blocked:
                    project_state["stalled_years"] = project_state.get("stalled_years", 0) + 1
                    project_state["blocked_on_trades"] = blocked
                    if project_state["stalled_years"] >= 4:
                        self.household.log.append((year, "HALTED %s: there is nobody here who can "
                                             "do this work (%s). What you spent is lost"
                                         % (node_id, ", ".join(blocked[:2]))))
                        self.household.active.pop(node_id, None)
                        self.household.bountied.discard(node_id)
                    else:
                        # WARN BEFORE THE MONEY GOES. Six projects were wiped in
                        # one year for a play tester who had no way to list what
                        # was at risk: the countdown ran silently for three years
                        # and then took everything spent. Say it each year, with
                        # the number of years left and what would fix it.
                        _left = 4 - project_state["stalled_years"]
                        self.household.log.append((year, "%s cannot go on: no %s here. It has "
                                             "%d year%s before it is abandoned and "
                                             "what you spent on it is lost. Teach "
                                             "the trade, or 'stop %s' now and keep "
                                             "your hours"
                                         % (node_id, " or ".join(blocked[:2]), _left,
                                            "" if _left == 1 else "s", node_id)))
                        # Nothing happened here this year - say so, rather than
                        # leaving last year's hours_offered/effective sitting on
                        # the entry looking like they still applied.
                        project_state["hours_offered_this_year"] = 0.0
                        project_state["hours_effective_this_year"] = 0.0
                    continue
                project_state["stalled_years"] = 0
                # project_hour_pace (projects.py) is this same formula, read
                # rather than re-derived, so 'work's own pre-sale warning
                # about starving an active project can never disagree with
                # what this loop actually offers it.
                #
                # A STANDING ALLOCATION IS A CEILING, NOT A FLOOR. hour_
                # allocations.get(k) is only ever a THIRD candidate in this
                # min() - never a reason to offer MORE than remaining or the
                # project's own pace would otherwise allow - so a directed
                # project can still never outrun the pool it shares with
                # everything else, and never get hours faster than its own
                # calendar floor could ever use. What it changes is ORDER
                # (active_sorted, above) and that an undirected project
                # never crowds this one out of the share the player asked
                # for it to have.
                _dir_hours = self.household.hour_allocations.get(node_id)
                _pace_cap = self.project_hour_pace(node_id)
                _project_throttle = self.project_resource_throttle(node_id)
                if _dir_hours and _dir_hours > 0:
                    per = min(remaining, _pace_cap, _dir_hours) * _project_throttle
                else:
                    per = min(remaining, _pace_cap) * _project_throttle
                remaining -= per
                # WHAT WAS ACTUALLY TAKEN OFF, which is not the same as what was
                # offered: `per` is allowed to exceed ph_left (the max() above
                # offers a full year's worth even to a project with an hour to
                # run), and the subtraction clamps at zero. The refunds below
                # were computed from `per` regardless, so a project with 10
                # hours left could be offered 500, have its 10 taken, and be
                # handed 200 back - ending the year with twenty times the hours
                # it began with. A playtester found the far end of that: a
                # progress bar reading "-67% of your hours spent", with
                # founder_hours_left larger than founder_hours_total. You cannot
                # be refunded work you never did.
                spent_hours = min(per, project_state["ph_left"])
                project_state["ph_left"] = max(0.0, project_state["ph_left"] - per)
                self.director_hours_spent_founder += per if self.founder_alive else 0
                # Hours OFFERED this year vs hours that actually did anything.
                # `refunded` tracks the difference: hours credited back to
                # ph_left below because a trade or the money to pay for it
                # fell short. Four projects each showed EXACTLY HALF their
                # founder hours left after one year and a tester called it
                # "confusing and feels artificial" - it was: nothing told them
                # `per` had been offered in full and half of it handed straight
                # back. See hours_this_year in `state`.
                project_state["hours_offered_this_year"] = round(per, 1)
                # WHAT THE PLAYER ACTUALLY ASKED FOR, READ BACK AT THE END OF
                # THE YEAR - `portfolio` and `why` print this field verbatim,
                # same reasoning as pool_total_this_year and its neighbours
                # just above: never recompute a number a player is told,
                # always read the one this loop actually used.
                project_state["hours_directed_this_year"] = (round(_dir_hours, 1)
                                                  if _dir_hours else None)
                # SAY SO WHEN THE PROMISE ITSELF WAS NOT KEPT, before any
                # trade or money shortfall even has a chance to bite further
                # in. A directive can be cut short right here, two ways: the
                # POOL had already given the rest away (to a higher-priority
                # directed project, or simply was not big enough for every
                # standing order at once), or this project's OWN pace -
                # what is left to do, or its calendar floor - could not use
                # that many hours even with the whole pool behind it. Either
                # is a real, nameable reason; "it disappeared" is not.
                if _dir_hours and _dir_hours > 0 and _dir_hours - per > 1.0:
                    if (_project_throttle < 0.98 and self.household.binding
                            and _pace_cap >= _dir_hours - 0.5):
                        _directed_hours_unused.append((node_id, round(_dir_hours - per, 0),
                            "a shortage of %s has every project (this one "
                            "included) running at %d%% of the pace its "
                            "hours alone would allow"
                            % (self.household.binding, round(_project_throttle * 100))))
                    elif _pace_cap * _project_throttle < _dir_hours - 0.5:
                        _directed_hours_unused.append((node_id, round(_dir_hours - per, 0),
                            "its own pace this year - at most %s hours, set "
                            "by how much of it is left to do or its "
                            "calendar floor, not by your hours - could not "
                            "use the rest" % "{:,.0f}".format(
                                _pace_cap * _project_throttle)))
                    else:
                        _directed_hours_unused.append((node_id, round(_dir_hours - per, 0),
                            "your other standing allocations and active "
                            "work already claimed the rest of this year's "
                            "%s hours before this one's turn came"
                            % "{:,.0f}".format(_pool_total_this_year)))
                refunded = 0.0
                project_state["yrs"] += 1
                frac = min(1.0, 1.0 / max(1.0, node["yrs"]))
                # Diagnostic callers can construct active-project dictionaries
                # directly, so initialise an omitted bill defensively.
                if project_state.get("cost_left") is None:
                    project_state["cost_left"] = max(0.0, self.project_cost(node_id) - project_state["spent"])
                # LABOUR BY TRADE. The old model pooled every trade into one
                # bucket of hired hours, so 450 hours of engineer and 450 hours
                # of labourer were the same resource. They are not, and the wage
                # table has said so all along. What binds now is the scarcest
                # trade this project actually needs.
                #
                # HOURS ARE A TOTAL AND A CEILING NOW, NOT A FIXED ANNUAL TOLL.
                # See ProjectsMixin.lab_year_draw (projects.py) for the finding
                # that forced this and the reasoning behind the new shape; this
                # call site only has to act on what it returns.
                hired_hours, worst, frac, _abandon = self.lab_year_draw(node_id, project_state, frac, hired_left)
                if _abandon:
                    self.household.log.append((year, "ABANDONED %s: %s" % (node_id, _abandon)))
                    self.household.active.pop(node_id, None)
                    self.household.bountied.discard(node_id)
                    continue
                if worst < 1.0:
                    # NEVER ALL OF IT. The refund says "hours offered but not
                    # usable, because the trade was booked" - and with no floor
                    # under it, it could hand back every hour that had actually
                    # gone in. A break tester watched a project's founder-hours
                    # sit unchanged for ever because its scarcest trade was
                    # short, the bill fully paid, the calendar long past, making
                    # no progress at all while holding an entire trade's pool
                    # and freezing other projects behind it.
                    #
                    # If a fraction `worst` of the work could be done, then a
                    # fraction `worst` of it WAS done, and that much can never
                    # be given back. Progress is now strictly positive whenever
                    # anybody at all can be found.
                    give_back = min(spent_hours - refunded,
                                    per * 0.4 * (1.0 - worst),
                                    spent_hours * (1.0 - worst))
                    project_state["ph_left"] += max(0.0, give_back)
                    refunded += max(0.0, give_back)
                    # Remember it. A tester sat on 696,350 denarii watching three
                    # projects report waiting_on "money" with 2.3, 84 and 158
                    # denarii left to pay, and reasonably concluded the spend cap
                    # was broken. It was not: the trades those projects needed
                    # were fully booked, so almost nothing could be paid FOR. The
                    # mechanic was right and the label was a lie. (short_of_trade
                    # itself is now set inside lab_year_draw, against the same
                    # pace this comment describes.)
                if hired_hours > hired_left:
                    frac *= hired_left / max(hired_hours, 1e-9)
                    hired_hours = hired_left
                # THE INSTALMENT IS WHAT A CONSTRAINED YEAR CAN DO; THE BILL IS
                # WHAT IS LEFT. This used to work the payment out first and then
                # multiply it by each shortage in turn, so once the remaining
                # balance was smaller than a year's instalment you paid a
                # FRACTION OF WHAT WAS LEFT every year, for ever: a geometric
                # decay that approaches zero and never reaches it, while
                # completion needs the bill down to half a denarius. A
                # playtester watched one project sit at "71% done" for
                # twenty-five years with cash in hand and no idea why. Working
                # it out from the already-scaled `frac` means a shortage sets
                # how FAST you can pay and never stops the last payment landing.
                money = min(project_state["cost_left"], self.project_cost(node_id) * frac)
                hired_left -= hired_hours
                # You may spend into debt, up to what someone will lend you, and
                # no further. Beyond that the work simply does not get paid for
                # this year, and a year nobody was paid for is a year of little
                # progress. What must NOT happen is the bill being forgiven.
                #
                # The margin is deliberate. Spending to the last denarius of your
                # credit means next year's rent breaches the limit and the
                # creditors halt every project you have, which turns "I was
                # ambitious" into "everything I had in hand was destroyed". A
                # lender who will advance you a thousand will not let you draw
                # the last two hundred of it against a half-built balloon.
                # Reserve next year's fixed costs AND most of the credit line.
                # Drawing the line to its last denarius is how one ambitious
                # project destroyed everything else a tester had in hand: the
                # limit itself falls as reputation and revenue fall, so a balance
                # exactly at the limit this year is over it next year, and over
                # the line every project in progress is halted at once.
                # Reserve only the SHORTFALL, not the whole running cost. This
                # year's rent and wages have already been taken out of capital at
                # the top of step(); reserving them again left a household with
                # 6,670 in hand and 31,000 of costs covered by 31,600 of income
                # unable to spend a single denarius on its own projects, so four
                # of them sat unpayable and unfinished for two hundred years.
                fixed = self.living_cost() + self.upkeep() + self.mine_operating_cost()
                reserve = max(0.0, fixed - self.revenue())
                purse = self.household.capital + self.credit_limit() * 0.6 - reserve
                # NOTHING OWED IS NOT THE SAME AS NOTHING AFFORDABLE. A
                # project with cost_left already at zero asks for money=0
                # this year, and money(0) > purse was still true whenever
                # purse itself had gone negative - deep arrears, not this
                # project's own bill - so a FULLY PAID project, needing not
                # one more denarius, was refunded nearly all of per anyway
                # (funded_frac forced to 0.0 below whenever money <= 0) and
                # made zero hour progress purely calendar-waiting projects
                # should still be free to make. Three playtesters on three
                # civilisations hit this as "arrears freezes ALL
                # founder-hour progress, even on fully-paid work" - and they
                # were exactly right: the gate was on the household's purse,
                # not on whether this project needed anything from it.
                if money > 0 and money > purse:
                    # PROPORTIONAL, not a flat half. This used to refund
                    # exactly per*0.5 whenever the purse fell short AT ALL,
                    # whether by one denarius or by the whole bill, which is
                    # what produced the "exactly half" a tester flagged as
                    # arbitrary-looking: four unrelated projects each showing
                    # precisely half their founder hours left after one year
                    # is not a coincidence, it is this constant. A project
                    # funded to 95% of what it needed lost the same fixed
                    # half of its hour's progress as one funded to 5%; the
                    # trade-shortage case two blocks up already scales its
                    # refund by how much of the need went unmet (worst), and
                    # this should too.
                    funded_frac = 0.0 if money <= 0 else max(0.0, min(1.0, purse / money))
                    money = max(0.0, purse)
                    # Capped at what was actually taken off, and at what has not
                    # already been handed back by the trade-shortage refund
                    # above. See spent_hours: you cannot be refunded work you
                    # never did, and you cannot be refunded the same hour twice.
                    give_back = min(spent_hours - refunded, per * (1.0 - funded_frac))
                    project_state["ph_left"] += max(0.0, give_back)
                    refunded += max(0.0, give_back)
                    project_state["underfunded_this_year"] = True
                    # WHY, not just that. A playtester ran deep into debt and
                    # watched every project report hours "offered" and none
                    # "effective", with nothing in help, why, money or risk
                    # explaining it. Arrears are the reason: the purse a project
                    # may draw on is what you hold plus part of your credit,
                    # less what your fixed costs need, and in arrears that is
                    # nothing at all.
                    project_state["why_underfunded"] = (
                        "in arrears: after fixed costs there is nothing left to "
                        "draw on, so the hours offered this year did almost "
                        "nothing" if self.household.capital < 0 else
                        "this year's instalment is more than the purse will bear")
                    # SAY IT NOW, NOT ONLY WHEN ASKED. `why_underfunded` sits on
                    # the project and answers the question if a player thinks
                    # to check `why` or `portfolio` - but the founder-hours lost
                    # here never come back, whatever the player does next, and
                    # nothing prompted them to look. Recorded here (only the
                    # arrears case, only if it actually cost real hours) and
                    # logged once below, after the loop.
                    if self.household.capital < 0 and give_back > 1.0:
                        _arrears_hours_lost.append((node_id, round(give_back, 0)))
                else:
                    project_state.pop("underfunded_this_year", None)
                    project_state.pop("why_underfunded", None)
                self.household.capital -= money
                self.household.total_spend += money
                project_state["spent"] += money
                project_state["cost_left"] = max(0.0, project_state["cost_left"] - money)
                # spent_hours, NOT per. `per` is what was OFFERED, and it is
                # allowed to exceed the hours the project actually had left; the
                # refunds above are capped at spent_hours for exactly that
                # reason, and this line was left uncapped. A sweep of the
                # playtest notes found a project reporting 387.2 effective hours
                # a year for four consecutive years while founder_hours_left sat
                # unchanged at 112.8 - work reported that provably did not
                # happen, about the one resource the whole game is built on.
                project_state["hours_effective_this_year"] = round(max(0.0, spent_hours - refunded), 1)
                hours_effective_total += project_state["hours_effective_this_year"]
                # THE SECOND WAY A DIRECTIVE GOES UNHONOURED: OFFERED, THEN
                # HANDED BACK. Unlike the check above this one, it must NOT
                # fire just because spent_hours fell short of `per` - a
                # project a few hours from finished is offered a whole
                # year's pace and only needs a sliver of it, which is not a
                # shortage of anything, it is the project ending. Gated on
                # why_underfunded/short_of_trade actually being SET this
                # year - fields only the money and trade-shortage branches
                # above ever write - so this can only ever name a real
                # shortfall, never mistake "it finished" for one.
                if _dir_hours and _dir_hours > 0:
                    _inner_gap = project_state["hours_offered_this_year"] - project_state["hours_effective_this_year"]
                    # DEEP ARREARS ALREADY GETS ITS OWN LINE, BELOW - "IN
                    # ARREARS: ... did almost nothing this year" - and it is
                    # the sharper warning of the two. Saying the same
                    # shortfall twice in two different voices is not
                    # clearer, it is just noise; this fires only for the
                    # money-short case arrears does NOT already cover (the
                    # purse-can-only-absorb-so-much-a-year pace, which is
                    # real money trouble without capital actually being
                    # negative).
                    if _inner_gap > 1.0 and project_state.get("why_underfunded") and self.household.capital >= 0:
                        _directed_hours_unused.append(
                            (node_id, round(_inner_gap, 0), project_state["why_underfunded"]))
                    elif _inner_gap > 1.0 and project_state.get("short_of_trade"):
                        _directed_hours_unused.append((node_id, round(_inner_gap, 0),
                            "trade hours already booked: " + ", ".join(
                                sorted(project_state["short_of_trade"])[:2])))
                # Count it HERE, after the hired-hours scaling and the
                # affordability clamp, not before them. Accumulating the
                # notional figure made project_spend_last_year disagree with
                # the actual capital movement by a factor of 89, which a tester
                # caught by comparing three numbers in a single `state` reply.
                self.household._spend_this_year = self.household._spend_this_year + money
                # calendar_floor(k), NOT a second copy of this formula -
                # expected_calendar_years (projects.py) needs the identical
                # figure to project retries honestly, and a rule living in
                # two places is how this kind of arithmetic drifts apart.
                floor = self.calendar_floor(node_id)
                # THE BILL HAS TO BE PAID. Hours done and years elapsed are not
                # enough; if the money never arrived, the thing was never built.
                # HALF AN HOUR IS NOTHING LEFT TO DO. The give-back hands back a
                # fraction of what was offered, so on a throttled project
                # ph_left decays geometrically towards zero and never reaches
                # it: a break tester's `logarithms` sat at 1.29e-25 founder-hours
                # with the bill paid and thirty years elapsed, complete in every
                # sense except the comparison. The bill already had this exact
                # fix and this exact reason (see `money` just above, and
                # cost_left <= 0.5 on the same line); hours never got it.
                if project_state["ph_left"] < 0.5:
                    project_state["ph_left"] = 0.0
                if project_state["ph_left"] <= 0 and project_state["yrs"] >= floor and project_state["cost_left"] <= 0.5:
                    self._complete(node_id)
                elif project_state["ph_left"] <= 0 and project_state["yrs"] >= floor and project_state["cost_left"] > 0.5:
                    project_state["waiting_on_money"] = True

        # ARREARS COSTS YOU THE YEAR'S HOURS, NOT JUST THE MONEY - SAY SO. This
        # is the Rome playtester's sharpest complaint: "the arrears mechanic
        # silently wastes founder-hours, not just money", discovered only
        # after several turns of a project sitting at "did almost nothing"
        # with no explanation on the turn itself. Founder-hours are the one
        # resource in this whole model that never banks (see step 5b and
        # `state`'s free_hours_going_unused): a year of them lost silently is
        # worse than a year of money lost, because money can be earned back
        # on the same footing next year and this cannot be earned back at
        # all. Named per project, so 'why <id>' and this line never disagree
        # about which project or how much.
        if _arrears_hours_lost:
            _total_lost = sum(hours for _, hours in _arrears_hours_lost)
            _names = ", ".join("%s (%s hr)" % (node_id, "{:,.0f}".format(hours))
                                for node_id, hours in _arrears_hours_lost)
            self.household.log.append((year, "IN ARREARS: %s founder-hours meant for %s did "
                                 "almost nothing this year, on top of the money "
                                 "- that time does not come back, arrears or not. "
                                 "'work' sells idle hours for wages instead of "
                                 "losing them here; clearing the arrears is what "
                                 "stops it happening again"
                             % ("{:,.0f}".format(_total_lost), _names)))

        # A STANDING ALLOCATION THE PLAYER GAVE, AND DID NOT GET - SAID, NOT
        # LEFT FOR THEM TO NOTICE. `allocate` is a promise about the one
        # resource that never banks; silently falling short of it is the
        # same unfairness the arrears line above exists to stop, aimed at a
        # player who took the extra step of directing their hours on
        # purpose rather than leaving the split to priority order. Sorted
        # by id for a deterministic order across runs with the same seed -
        # several projects can be cut short in the same year.
        if _directed_hours_unused:
            for _node_id, _hr, _why in sorted(_directed_hours_unused):
                self.household.log.append((year, "DIRECTED HOURS UNUSED: you allocated hours "
                                     "to %s this year that it could not use - "
                                     "%s of them went begging because %s. "
                                     "'portfolio' shows the rest; 'allocate' "
                                     "changes or clears the standing order"
                                 % (self.nodes[_node_id]["name"],
                                    "{:,.0f}".format(_hr), _why)))

        # Snapshot BEFORE 5b spends more of `remaining` on wage work: otherwise
        # offered_to_projects below double-counts wage hours as though they had
        # been offered to projects too, since 5b draws from the same pool.
        remaining_after_projects = remaining

        # 5b. IF THERE IS NO WORK AND NO MONEY, TAKE A JOB. A man who arrives
        #     with four hundred denarii and a lens does not sit watching his
        #     savings run out; he teaches, or writes, or sets bones for money. It
        #     is in the protocol as `work` for a player and the optimizer had no
        #     equivalent, so a single bad year in the opening decade could end a
        #     run: one Rome seed earned four technologies in five hundred years
        #     because a fire in 103 took a fifth of everything it had.
        if (not self.manual and remaining > self.WAGE_FALLBACK_MIN_HOURS
                and (self.household.capital < self.living_cost() * self.WAGE_FALLBACK_LIVING_COST_YEARS
                     or not self.household.active)):
            trade = ("scholar" if self.effective_scholars() >= 1 else "scribe")
            hours = min(remaining, self.WAGE_FALLBACK_MAX_HOURS)
            # ONLY IF IT PAYS BETTER THAN THE PRACTICE IT DISPLACES. Wage hours
            # now cost you the share of your practice they were sold out of
            # (see practice_attention), and without this check the optimizer
            # went on taking a scribe's wage at the price of a physician's fee
            # and lost Rome a sixth of its runs. A man with a practice does not
            # go and copy documents for less than the practice earns; that is
            # the whole reason `work` is the thing you do BEFORE you have one.
            # NOT `pool`. That name already held the year's project budget,
            # computed at 4b, and reusing it here overwrote it - so
            # hours_this_year then reported "offered_to_projects" against the
            # WHOLE year instead of against the project budget. The year's
            # hours added up to 2,900 out of 2,000, which is exactly the sort
            # of arithmetic a player cannot argue with and cannot trust.
            year_hours = max(1.0, self.director_pool())
            practice_lost = self.revenue() * (hours / year_hours) * (
                1.0 if self.practice_attention() > 0 else 0.0)
            rate = (self.annual_wage(trade) / self.HOURS_PER_PERSON_YEAR
                    * (1.0 + min(self.WAGE_REPUTATION_BONUS_CAP,
                                 self.household.reputation / self.WAGE_REPUTATION_BONUS_SCALE)))
            if hours * rate > practice_lost:
                _, err = self.work_for_wages(trade, hours)
                # Kept in step with `remaining` so hours_this_year (below) does
                # not count hours sold for wages here as still unused.
                if err is None:
                    remaining -= hours

        # 6. reputation, familiarity, protection, scandal
        #
        # Reputation DECAYS TOWARD WHAT YOU ARE ACTUALLY KNOWN FOR, not toward
        # zero. Three testers independently reported the same thing: reputation
        # slid from 10 to 0.2 over a century and a half with no event ever
        # explaining it, and one called it "less like a lever I could manage and
        # more like a clock running out in the background". They were right, and
        # decaying to zero was also wrong on its own terms. A physician with a
        # practice, a school and a written corpus does not become a man nobody
        # has heard of because thirty quiet years passed. What fades is novelty;
        # what remains is the work.
        floor = self.standing_floor()
        self.household.reputation = floor + (self.household.reputation - floor) * self.REPUTATION_DECAY_TOWARD_FLOOR
        # ADAPTATION. Every year the world has known you, and every visible thing
        # you have already done, makes the next one less astonishing.
        pub = sum(1 for node_id in self.household.done
                  if set(self.nodes[node_id].get("traits", [])) & {"spectacle", "inexplicable"})
        self.household.familiarity = min(
            self.FAMILIARITY_CEILING,
            1.0 - math.exp(-self.w["adaptation_rate"]
                           * (self.FAMILIARITY_PUBLICATION_WEIGHT * pub
                              + self.FAMILIARITY_TENURE_WEIGHT * (self.year - 100))))
        # WHERE THE YEAR'S HOURS WENT. Four projects each showed exactly half
        # their founder hours left after one year, with 2,400 available and
        # only about 200 apparently spent, and a tester had no way to see why:
        # nothing in `state` accounted for a year's hours at all. Captured
        # here, before the tallies below reset for the next year, the same way
        # spend_last_year already captures the year's spending. See it as
        # `hours_this_year` in `state`.
        self.hours_this_year = {
            "available": round(self.director_pool(), 1),
            "wage_work": round(getattr(self.household, "wage_hours_this_year", 0.0), 1),
            "teaching": round(self.household.teaching_hours_this_year, 1),
            "offered_to_projects": round(max(0.0, pool - remaining_after_projects), 1),
            # OFFERED is what projects were given a shot at; EFFECTIVE is what
            # actually reduced their founder_hours_left. The gap between the
            # two is hours that went in and came straight back out again
            # because a trade or the money to pay for it fell short that year
            # - see hours_offered_this_year / hours_effective_this_year on
            # each project in `active`, and underfunded_this_year.
            "effective_on_projects": round(hours_effective_total, 1),
            "unused": round(max(0.0, remaining), 1),
        }
        # Reset AFTER the progress pass above, which is where the hours you sold
        # are subtracted from the hours you have left to direct.
        self.household.wage_hours_this_year = 0.0
        # Contracted work is bought for a year and expires with it: hours you
        # paid a shop for in 142 are not still sitting there in 143.
        self.household.contract_hours = {}
        self.household.teaching_hours_this_year = 0.0
        self.household.spend_last_year = self.household._spend_this_year
        self.household._spend_this_year = 0.0
        # Sellers restock, so the pressure your buying put on the market fades.
        self.household.market_pressure = max(0.0, self.household.market_pressure * self.MARKET_PRESSURE_DECAY - self.MARKET_PRESSURE_ANNUAL_FADE)
        # WARN BEFORE IT KILLS YOU. A play tester built 952 technologies, was
        # three nodes from the goal, and the run ended on a 2% roll against an
        # eminence of 28.2 - with no escalation of any kind beforehand, and
        # nothing in the log ever mentioning it. Their words: "no escalation on
        # the stat that ends the run". It is the one hazard that cannot be
        # bribed away and the one the player was never told was closing in.
        _danger = self.cfg["eminence_danger"]
        if self.household.eminence > _danger * 0.75:
            _said = self.household._said_eminence
            _band = int(self.household.eminence / max(1.0, _danger * 0.15))
            if _band > _said:
                self.household._said_eminence = _band
                self.household.log.append((year, "YOU ARE BECOMING CONSPICUOUS: eminence %.0f "
                                     "against a danger line of %.0f. This is the "
                                     "one thing no patron and no bribe protects "
                                     "you from, and it grows with reputation and "
                                     "visible wealth. A wide, dispersed "
                                     "institution is what survives you"
                                 % (self.household.eminence, _danger)))
        self.update_protection()
        # THE STATE NOTICES YOU. Requisition, the pressed office, a demand
        # for military supply, and the tail confiscation risk at the top of
        # the same scale - see SocietyMixin's own "THE STATE NOTICES YOU"
        # section (society.py) for the whole mechanic. Run after
        # update_protection() so this year's patronage and office standing
        # are what requisition/confiscation actually bargain against, and
        # before scandal/eminence below so a confiscation this mechanic
        # causes and the eminence-driven one further down are never
        # resolved in the same breath as two unrelated draws on the same
        # stale numbers.
        self._state_pressure(year)
        self.household.scandal *= self.SCANDAL_DECAY_RATE
        # Eminence accumulates in a SEPARATE pool, because bribery does not
        # touch it. You can buy a magistrate, an accuser and a jury. You cannot
        # buy an emperor's judgement that you have grown too large, and the
        # attempt is itself evidence against you.
        self.household.eminence = self.household.eminence * self.EMINENCE_DECAY_RATE + self.prominence_hazard()
        # you can buy your way out of trouble, and a sane player does
        if (self.household.scandal > self.AUTO_BRIBE_SCANDAL_THRESHOLD
                and self.household.capital > self.AUTO_BRIBE_CAPITAL_THRESHOLD
                and self.policy.get("auto_bribe", not self.manual)):
            spend = min(self.household.capital * self.AUTO_BRIBE_CAPITAL_SHARE,
                        self.household.scandal * self.AUTO_BRIBE_COST_PER_SCANDAL_POINT)
            self.household.capital -= spend
            self.household.bribes_ytd = self.BRIBES_YTD_DECAY * self.household.bribes_ytd + spend
            self.household.scandal -= spend / self.BRIBE_SCANDAL_REDUCTION_SCALE * self.w["bribability"]
        else:
            self.household.bribes_ytd *= self.BRIBES_YTD_DECAY
        self.household.scandal = max(0.0, self.household.scandal)
        # WARN, THE WAY EMINENCE DOES. Denunciation ends the run outright and
        # said nothing at all first: a break tester read "RUN ENDS: denounced:
        # as a sorcerer" after eleven quiet years, with `state` showing
        # "scandal 33.55" and no threshold, no probability and no note - on the
        # same screen where eminence carefully explains that it is "dangerous
        # above 26 ... 0% chance the run ENDS this year". Two hazards of the
        # same shape, one of them legible.
        _sd = cfg["suspicion_danger"]
        if self.household.scandal > _sd * 0.75:
            _band = int(self.household.scandal / max(1.0, _sd * 0.15))
            if _band > int(getattr(self.household, "_said_scandal", 0)):
                self.household._said_scandal = _band
                self.household.log.append((year, "YOU ARE BEING TALKED ABOUT: scandal %.0f "
                                     "against a line of %.0f. Past it you may be "
                                     "denounced, and that ends the run - about "
                                     "%.0f%% a year at this level. 'bribe' buys "
                                     "advocacy and piety; it falls a tenth a "
                                     "year on its own"
                                 % (self.household.scandal, _sd,
                                    100.0 * max(0.0, (self.household.scandal - _sd) / self.SCANDAL_HAZARD_SCALE))))
        elif self.household.scandal < _sd * 0.5:
            self.household._said_scandal = 0
        if self.events and self.household.scandal > cfg["suspicion_danger"]:
            probability = (self.household.scandal - cfg["suspicion_danger"]) / self.SCANDAL_HAZARD_SCALE
            if self.rng.random() < probability:
                self._catastrophe("denounced: %s" % ("as a sorcerer" if self.w["w_magic_fear"] > 0.5
                                                     else "as a subversive"))
        # The eminence hazard is separate and unbribable. Its usual outcome is a
        # bad year rather than a death: a confiscation, a patron destroyed in
        # someone else's quarrel, a forced withdrawal from public life.
        if self.events and self.household.eminence > cfg["eminence_danger"]:
            probability = (self.household.eminence - cfg["eminence_danger"]) / self.EMINENCE_HAZARD_SCALE
            if self.rng.random() < probability:
                roll = self.rng.random()
                if roll < self.EMINENCE_OUTCOME_CONFISCATION_SHARE:
                    take = self.household.capital * self.EMINENCE_CONFISCATION_CAPITAL_LOSS
                    self.household.capital -= take
                    self.household.reputation = max(0.0, self.household.reputation - self.EMINENCE_CONFISCATION_REPUTATION_LOSS)
                    self.household.eminence *= self.EMINENCE_CONFISCATION_RETENTION
                    self.household.log.append((year, "PROMINENCE: property confiscated, %d den lost, "
                                         "and you withdraw from public life for a while" % take))
                elif roll < (self.EMINENCE_OUTCOME_CONFISCATION_SHARE + self.EMINENCE_OUTCOME_PATRON_LOST_SHARE):
                    for pat in ("patron_imperial", "patron_senatorial"):
                        if pat in self.household.done:
                            self.household.done.discard(pat)
                            self._done_changed()
                            self.household.log.append((year, "PROMINENCE: your patron is destroyed in "
                                                 "someone else's quarrel and you lose %s" % pat))
                            break
                    self.household.eminence *= self.EMINENCE_PATRON_LOSS_RETENTION
                    self.household.reputation = max(0.0, self.household.reputation - self.EMINENCE_PATRON_LOSS_REPUTATION_LOSS)
                else:
                    self._catastrophe("too eminent: brought down not for what you built "
                                      "but for how large you had become")

        # 6b. serving out a debt. The hours you owe go to the creditor and the
        #     debt falls; when it is done you are free, and you keep everything
        #     you know.
        if self.household.bondage_years_left > 0:
            self.household.bondage_years_left -= 1
            paid = self.cfg["founder_hours_per_year"] * self.BONDAGE_LABOUR_SHARE * \
                (WAGES.get("labourer", self.BONDAGE_LABOURER_WAGE_DEFAULT) * self.BONDAGE_WAGE_MARKUP) * self.wage_index * self.price_index
            self.household.bondage_debt = max(0.0, self.household.bondage_debt - paid)
            if self.household.bondage_debt <= 0 and self.household.bondage_years_left > 0:
                self.household.bondage_years_left = 0     # paid early
            if self.household.bondage_years_left <= 0:
                self.household.bondage_years_left = 0.0
                self.household.bondage_debt = 0.0
                self.household.log.append((year, "your term is served and the debt is discharged; "
                                     "you are your own man again"))

        # 7. founder mortality
        if self.founder_alive:
            self.life_left -= 1
            if self.running("sanitation_antisepsis"):
                self.life_left += self.SANITATION_LIFE_EXTENSION_YEARS      # you at least do not die of a septic cut
            if self.life_left <= 0:
                self.founder_alive = False
                # SAY WHAT IT MEANS, not only that it happened. Two round-12
                # testers independently called this the worst thing in the
                # game: one wrote that a dead founder's run was "permanently
                # unwinnable from that point" with the game never saying so,
                # the other that a corpse went on being offered 69 startable
                # projects and actually accepted one. The engine is not in
                # fact silent about the consequence - deputies carry the work,
                # and with none the programme dissolves over twelve years - but
                # nothing ever told the player either half of that.
                _dep = self.household.directors_extra
                self.household.log.append((year, "THE FOUNDER DIES, aged about %d. %s"
                                 % (self.cfg["founder_arrival_age"] + year
                                    - self.cfg["start_year"],
                                    ("Your %.1f deputies direct the work in your "
                                     "name and the programme goes on without you: "
                                     "that is what training them was for."
                                     % _dep) if _dep >= 0.5 else
                                    "You trained no deputy, so there is nobody to "
                                    "direct anything. Nothing that needs your "
                                    "hours can ever be begun again, and what you "
                                    "built will be forgotten over the next twelve "
                                    "years unless a deputy appears. This run is "
                                    "effectively over; 'state' shows how far you "
                                    "got.")))
        # a programme with no director is not paused, it is dissolving
        if not self.founder_alive and self.household.directors_extra < 0.5:
            self.household.stalled += 1
            if self.household.stalled >= self.DISSOLUTION_YEARS_BEFORE_FORGETTING:
                losable = sorted(node_id for node_id in self.household.done if node_id not in self.household.granted)
                # sorted() matters: self.household.done is a SET, and a set iterates in an
                # order that depends on PYTHONHASHSEED, so feeding it unsorted to
                # rng.sample made the same --seed give a different answer on every
                # invocation. Every figure this project has reported was, strictly,
                # unreproducible.
                if losable:
                    for node_id in self.rng.sample(losable, max(1, len(losable) // self.DISSOLUTION_FORGET_FRACTION_DIVISOR)):
                        self.household.operating.discard(node_id)
                        self.household.done.discard(node_id)
                        self._done_changed()
            # COUNT IT DOWN WHERE THE PLAYER CAN SEE IT. Twelve years of a
            # dissolving programme passed with nothing said but the shedding
            # itself, so a tester read the losses as unexplained and the run as
            # merely unlucky rather than finished.
            if self.household.stalled in (3, 6, 9, 11):
                self.household.log.append((year, "THE PROGRAMME IS DISSOLVING: %d year(s) "
                                     "since the founder died with no deputy to "
                                     "take over. What you built is being "
                                     "forgotten. The run ends at twelve."
                                 % self.household.stalled))
            if self.household.stalled >= self.DISSOLUTION_YEARS_UNTIL_END:
                self._catastrophe("the founder died without training successors; "
                                  "the school dispersed and the work was forgotten")
        else:
            self.household.stalled = 0

        # 8. random events
        if self.events and not self.dead_reason:
            self._random_events(year)

        self.year += 1

    # ---- THRESHOLD GOALS: completed by measurement, not by labour ---------
    # A goal need not be a thing you build. "Raise literacy past a fifth" or
    # "cut what epidemics take by four-fifths" are states of the whole
    # society, not a project with hours and materials - see data/tech_tree.json
    # meta.goals and its own note on why a threshold is still modelled as a
    # node (so closure()/critical_path()/Sim.run() never need a second idea
    # of what a goal is) rather than as a second mechanism bolted on beside
    # the ordinary one.
    WIN_CONDITION_METRICS = frozenset(
        ("literacy_general", "literacy_elite", "epidemic_relief"))

    def _win_condition_value(self, metric):
        """The live number a win_condition's `metric` names, 0..1. Raises for
        a metric this engine does not know how to read - at load time, via
        `validate`, not mid-game - rather than silently reading 0 forever for
        a typo no playtest would otherwise catch."""
        if metric in ("literacy_general", "literacy_elite"):
            return float(self.civ.get(metric, 0.0))
        if metric == "epidemic_relief":
            # hazard_relief returns the SURVIVING fraction of the harm
            # (1.0 = no protection at all); relief is what is cut, the rest
            # of it - see society.py's own docstring on the diminishing,
            # never-quite-zero shape of that number.
            return 1.0 - self.hazard_relief("staff_loss")[0]
        raise ValueError("unknown win_condition metric %r" % metric)

    def _check_win_conditions(self, yr):
        """Once a year: every node carrying a `win_condition` that is not
        already done gets checked against the live measurement it names,
        and completes itself - exactly like a normal completion (done,
        done_year, the log, goal_year if it is the running goal) but with
        no cost charged and no `apply_tech_effects`/reputation/scandal call,
        because nobody did any work; a measurement crossed a line. Sorted
        so the order is reproducible under a fixed PYTHONHASHSEED, the same
        reasoning `topo_order` and the attrition loop above already give
        for walking `self.nodes`/`self.household.done` in id order rather than a bare
        set's own iteration order.

        Walks `self._win_condition_keys` (built once, in __init__, from the
        static node data - see the comment there), not `sorted(self.nodes)`:
        this used to re-sort every one of the ~2,849 node ids in the whole
        tree, every single year, to reach the handful that actually carry a
        win_condition at all - pure self time (`sorted` and dict-get, both
        C-level, nothing further to profile under it).
        """
        for node_id in self._win_condition_keys:
            if node_id in self.household.done:
                continue
            win_condition = self.nodes[node_id]["win_condition"]
            if not win_condition:
                continue
            val = self._win_condition_value(win_condition["metric"])
            comparison_op, target = win_condition["op"], win_condition["value"]
            met = (val >= target) if comparison_op == ">=" else (val <= target) if comparison_op == "<=" else False
            if not met:
                continue
            self.household.done.add(node_id)
            self._done_changed()
            self.household.done_year[node_id] = yr
            self.household.log.append((yr, "achieved: " + self.nodes[node_id]["name"]))
            if node_id == self.goal and self.household.goal_year is None:
                self.household.goal_year = yr

    def run(self, goal, horizon=None):
        self.goal = goal
        self.household.done_year = {}
        horizon = horizon or self.cfg["horizon_years"]
        end = self.cfg["start_year"] + horizon
        while self.year < end and not self.dead_reason and self.household.goal_year is None:
            self.step()
        return self


# ----------------------------------------------------------------------------
# Strategies
# ----------------------------------------------------------------------------
