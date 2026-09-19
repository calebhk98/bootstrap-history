"""The simulation itself: what one year does, and the loop over years."""
import collections, math, os, random, sys

from constants import declare
from .data import (DEFAULTS, load_civ, load_geography, load_resources,
                   TECH_EFFECTS)

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
# WIRING THREE (Complaints/50-one-label-draws-one-coin.md) REPLACES WIRING
# TWO'S OWN `from world import land` HERE. WIRING TWO (Complaints/47) read
# sim/world/land.py's `cultivable_land_for_civilization` for each home
# REGION's share of cultivable land; Complaints/50 measured that "region"
# to be the wrong unit of area (a region record is not one weather system,
# and two region records are not independent draws - see that complaint)
# and replaced it with a draw per GEOGRAPHY.JSON TILE instead (see
# `_compute_farm_weather_cells` below), which reads geography.json's own
# `land_tiles` block directly rather than land.py's region-parcel
# abstraction. land.py is consequently no longer imported by this file -
# nothing else here used it - and this task's own ownership boundary
# (sim/engine/core.py, sim/world/shared_constants.py - see this task's own
# brief) still holds: sim/world/land.py itself is untouched, this file
# simply stopped being one of its callers.
#
# Imported FULLY QUALIFIED (`sim.world.shared_constants`), not the bare
# `from world import X` style `agriculture`/`demography` above use, and
# deliberately so: `agriculture` and `land` (sim/world/) both already do
# `from sim.world.shared_constants import (...)` at their own top (see that
# file's own "HOW A CONSUMER USES ONE OF THESE" section), so by the time
# this line runs, `sim.world.shared_constants` already exists in
# sys.modules as ONE object. A bare `from world import shared_constants`
# here would load `world/shared_constants.py` a SECOND time under a
# DIFFERENT sys.modules key (`world.shared_constants`, not
# `sim.world.shared_constants`) - the exact "same file, two module
# objects" trap CLAUDE.md SS6 records for `world.agriculture` vs
# `sim.world.agriculture`, avoided here on purpose rather than repeated.
from sim.world.shared_constants import (
    GROWING_SEASON_WEATHER_DECORRELATION_LENGTH_KM)
# Same fully-qualified convention as shared_constants.py just above, for the
# same reason - see sim/unit_conversions.py's own "HOW A CONSUMER USES ONE
# OF THESE" section.
from sim.unit_conversions import PERCENT_SCALE


from .economy import EconomyMixin
from .fog import FogMixin
from .geography import GeographyMixin
from .labour import LabourMixin
from .projects import ProjectsMixin
from .society import SocietyMixin
from .core_properties import ForwardingPropertiesMixin
from .core_step_phases import StepPhasesMixin
from .actors import Household


_EARTH_RADIUS_KM = 6371.0
# Same figure `haversine_km` (sim/engine/data.py) already uses for great-
# circle distance - not re-declared as a physical constant of its own (a
# planet's radius is a fact of nature, not a modelling choice this project
# has any latitude over), just given a private module-level name here
# rather than a bare literal, since `_cell_chordal_position_km` below needs
# it and this file does not own sim/engine/data.py to add a shared export
# there instead.

def _cell_chordal_position_km(lat_degrees, lon_degrees):
    """A cell's lat/lon centroid, converted to (x, y, z) kilometres on a
    sphere of Earth's radius - the CHORDAL (straight-line) position two
    cells' positions are differenced to get a chordal DISTANCE from, inside
    `Sim._compute_farm_weather_correlation_cholesky`.

    WHY THIS EXISTS ALONGSIDE `haversine_km` RATHER THAN JUST CALLING IT.
    `haversine_km` (defined in `engine/data.py`, and imported by the
    geography and economy mixins rather than by this file) gives the
    GREAT-CIRCLE distance between two
    lat/lon points - the right answer for `region_reach`/`material_reach`'s
    travel-time modelling, which is what it was built for. It is the WRONG
    choice for a spatial correlation kernel's distance argument: an
    isotropic exponential kernel of great-circle distance is not
    guaranteed positive semi-definite for an arbitrary set of points on a
    sphere (a known result in the spatial-statistics literature on
    covariance functions on spheres - see Cholesky's own docstring for the
    fuller version of this argument), while the SAME kernel of CHORDAL
    (straight-line, through-the-earth) distance is - it is an ordinary
    Euclidean-space Matern kernel, valid in any dimension. Returning
    Cartesian positions here, rather than a distance function directly,
    lets the caller build every pairwise distance from `len(cells)`
    conversions instead of `len(cells) ** 2`.
    """
    lat_radians = math.radians(lat_degrees)
    lon_radians = math.radians(lon_degrees)
    return (_EARTH_RADIUS_KM * math.cos(lat_radians) * math.cos(lon_radians),
            _EARTH_RADIUS_KM * math.cos(lat_radians) * math.sin(lon_radians),
            _EARTH_RADIUS_KM * math.sin(lat_radians))


def _cell_morton_code(lat_degrees, lon_degrees, bits=16):
    """A Z-order (Morton) code for a lat/lon point. Used only by
    `Sim._cap_pooled_farm_weather_cells` to get a deterministic ordering
    that keeps geographically close cells close together in a 1-D
    sequence, so a contiguous run of that sequence is a genuine spatial
    neighbourhood rather than an arbitrary batch.

    Quantises latitude and longitude to `bits`-bit unsigned integers
    (65,536 steps each by default - about 0.0027 degrees, tens of metres,
    far finer than `land_tiles`' own 150,000 km2 cells, so this
    quantisation is not the limiting factor on locality) and interleaves
    their bits, the standard Z-order construction: reading the interleaved
    bits back out recovers alternating lat/lon bits from most to least
    significant, so two points near each other in BOTH lat and lon share
    long common high-bit prefixes and land near each other in the sorted
    1-D ordering.

    NOT a distance metric, and not used as one anywhere else in this file.
    `_compute_farm_weather_correlation_cholesky` still uses the real
    chordal distance (`_cell_chordal_position_km`) for every correlation
    value; this code only decides which raw cells get MERGED together
    before that calculation ever runs, when there are more of them than
    `FARM_WEATHER_POOLED_CELL_CAP` allows.
    """
    lat_fraction = (lat_degrees + 90.0) / 180.0
    lon_fraction = (lon_degrees + 180.0) / 360.0
    scale = 1 << bits
    lat_int = min(scale - 1, max(0, int(lat_fraction * scale)))
    lon_int = min(scale - 1, max(0, int(lon_fraction * scale)))
    code = 0
    for bit_index in range(bits):
        code |= ((lat_int >> bit_index) & 1) << (2 * bit_index)
        code |= ((lon_int >> bit_index) & 1) << (2 * bit_index + 1)
    return code


# STAKEHOLDER ITEM 7 ("the weather is currently O(n^3) initialization and
# O(n^2) per year to run... we currently are not able to go up to a 10k
# tile system, because of the weather"). Full measurement and the option
# comparison this constant implements are in docs/architecture/
# MAP_AND_WEATHER.md section 4.2 - "cap the number of pooled weather cells
# independently of how fine the map is", the document's own recommended
# option (4.6's comparison table: removes the O(n^3) exponent entirely,
# changes the answer only marginally and defensibly, violates no §3.1
# rule, needs no new dependency).
#
# WHY THIS IS SAFE ON THE MODEL'S OWN TERMS, NOT JUST A PERFORMANCE DODGE.
# `land_tiles` cells are already, at today's 150,000 km2 target size,
# well inside one GROWING_SEASON_WEATHER_DECORRELATION_LENGTH_KM (600 km)
# of most of their neighbours - MAP_AND_WEATHER.md section 3.4 measures a
# 115 km side length for a hypothetical 10,000-tile grid over the same
# land area, and exp(-115/600) = 0.83, i.e. two such cells would draw
# ALMOST the same weather anyway. A finer grid than the cap resolves
# detail the correlation kernel has no physical basis to treat as
# independent; capping cell count removes compute cost the model was
# never using for anything the kernel could tell apart.
#
# WHY 100, NOT A DERIVED FIGURE. A fully derived cap would come from a
# civilisation's own geographic extent divided by the decorrelation
# length (how many roughly-600-km-separated patches does this territory
# actually span), which needs a per-civilisation footprint measure this
# file does not compute today. That mechanism does not exist yet, so per
# CLAUDE.md section 3.4 this is labelled as what it is: a round number
# chosen to sit just above the largest cell count this project ships
# today - rome_100ad resolves to 88 land_tiles cells across its 7 home
# regions (sim/tests/test_growing_season_weather_correlation.py's own
# test_romes_seven_regions_resolve_to_88_land_tiles_cells), the largest
# of the five shipped civilisations (han_china_100ad 69, mexica_1500 32,
# norse_900ad 14, england_1300 13) - so every civilisation this project
# ships today keeps its EXACT current cell count and weather draw
# unchanged (100 >= 88), while a future finer `land_tiles` grid, or a
# civilisation with a larger territory than Rome's, is bounded rather
# than left to grow cubically. Not tuned to reproduce any price or
# population figure; tuned only to today's largest MEASURED cell count.
FARM_WEATHER_POOLED_CELL_CAP = declare(
    "FARM_WEATHER_POOLED_CELL_CAP", 100,
    kind="temporary_heuristic",
    unit="count (pooled growing-season weather cells per civilisation, an "
         "upper bound independent of land_tiles resolution)",
    source="Not a measured or published figure. Anchored to rome_100ad's "
           "own measured cell count today (88, the largest of the five "
           "shipped civilisations - see the comment above this "
           "declaration for the exact figures and the test that pins "
           "them) plus headroom, not derived from a formula relating cell "
           "count to GROWING_SEASON_WEATHER_DECORRELATION_LENGTH_KM.",
    confidence="D",
    why="Bounds the O(cell_count**3) one-time Cholesky factorisation in "
        "_compute_farm_weather_correlation_cholesky and the "
        "O(cell_count**2) per-simulated-year matrix-vector product in "
        "_pooled_farm_weather_multiplier to a constant cost regardless of "
        "how many land_tiles cells a civilisation's home_regions map to - "
        "the fix for stakeholder item 7 (a 10,000-tile map was otherwise "
        "unaffordable: measured directly, Rome's own cell count would "
        "grow from 88 to about 773 at that resolution, costing about "
        "3.5-4 seconds of factorisation per Sim() construction, and a "
        "default --mc 200 Monte Carlo run builds 200 of them, so roughly "
        "twelve minutes of pure matrix setup for one ordinary `run` "
        "invocation). At or under the cap nothing changes; above it, "
        "cells are MERGED (not dropped) into cap-many spatially-coherent "
        "pooled cells, each weighted by the summed arable land area of "
        "its members - see _cap_pooled_farm_weather_cells.")


class Sim(EconomyMixin, FogMixin, GeographyMixin, LabourMixin,
          ProjectsMixin, SocietyMixin, ForwardingPropertiesMixin,
          StepPhasesMixin):
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
        # WIRING THREE (Complaints/50-one-label-draws-one-coin.md), REPLACING
        # WIRING TWO'S OWN `_farm_region_weights`/`_compute_farm_region_
        # weights` (Complaints/47): this civilisation's territory is broken
        # into geography.json `land_tiles` cells (see `_compute_farm_
        # weather_cells`'s own docstring for why tiles rather than region
        # records), each cell's SHARE of the civilisation's cultivable land,
        # and the CORRELATION between every pair of cells given how far
        # apart they sit - both precomputed ONCE here, not every year, for
        # the same reason `farm_land` just above is: `home_regions`, the
        # tile geometry and each tile's own arable-land figure are all fixed
        # for the life of a run, so recomputing either every
        # `_demographic_recovery` call would rebuild the identical result
        # 100 times over a century for nothing. The correlation step is the
        # expensive one of the two (a Cholesky factorisation, O(cells^3)),
        # which is exactly why it belongs here and not inside the per-year
        # draw. Needs no SAVE_FIELDS entry for the same reason `farm_land`
        # needs none: `Sim.__init__` reconstructs both identically, from
        # `self.civ`'s own unchanging `home_regions` and the geography data
        # file (neither of which a save mutates), on every construction,
        # before `load_state` runs.
        self._farm_weather_cells = self._compute_farm_weather_cells()
        self._farm_weather_correlation_cholesky = (
            self._compute_farm_weather_correlation_cholesky(self._farm_weather_cells))
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
    # Moved to sim/engine/core_properties.py's ForwardingPropertiesMixin:
    # 107 one-line @property forwards onto self.household/self.population
    # (capital, done, operating, log, and so on), plus the comment block
    # explaining why each is a property and never __getattr__. Sim still
    # inherits ForwardingPropertiesMixin below, so every name in that file
    # keeps resolving on a live Sim instance exactly as it did here.


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

        WIRING TWO (Complaints/closed/47-one-weather-draw-for-a-continent.md):
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

    _WeatherCell = collections.namedtuple(
        "_WeatherCell", ("cell_id", "lat", "lon", "weight"))
    # A cell's identity is its own `cell_id` string (a land_tiles tile id,
    # e.g. "italy_02" - already globally unique across every region, per
    # geography.json's own `land_tiles.tiles` keys), not a (region, index)
    # pair. That is what lets `_farm_year_weather_seed(yr, region=cell_id)`
    # below reuse that method completely unchanged (Complaints/47's WIRING
    # TWO): the parameter is documented there as "an optional region", but
    # nothing about the seed formula actually requires the string passed to
    # BE a region key - it only needs to uniquely name what is being drawn
    # weather for, which a tile id does exactly as well as a region key did.

    def _compute_farm_weather_cells(self):
        """[Sim._WeatherCell(cell_id, lat, lon, weight), ...] over this
        civilisation's own `home_regions`, broken into geography.json's
        150,000 km2 `land_tiles` cells rather than left as whole region
        records - Complaints/50-one-label-draws-one-coin.md, replacing
        Complaints/47's own `_compute_farm_region_weights`.

        WHY TILES, NOT "subdivide each region by area around its centroid"
        (this task's brief offered both). `land_tiles` already exists,
        already carries an independently-generated `arable_fraction` and
        `fertility_quality_multiplier` per cell (see tools/generate_
        geography_tiles.py's own generation_rule_summary, stored on the
        data file itself), and already covers every one of the 21 shipped
        regions via `land_tiles.region_to_tiles` - building a fresh
        centroid-radius subdivision here would either re-derive the same
        equal-area grid geography.json's own tiles already are (pure
        duplication) or invent a DIFFERENT one with no basis for choosing
        its cell size over 150,000 km2, which is itself an arbitrary but at
        least ALREADY-CHOSEN-BY-SOMEONE-ELSE constant this task does not
        need to relitigate. Weight is each cell's OWN arable land area
        (land_area_km2 * arable_fraction, i.e. the same physical quantity
        `_compute_farm_region_weights` weighted by, at tile grain instead
        of region grain) as a share of this civilisation's TOTAL cell
        arable land - so, exactly as before, a tiny cell does not count as
        much as a large fertile one, only now "large" is measured in
        actual square kilometres instead of in how many rows a region
        occupies in geography.json (Complaints/50's own finding: region
        count, not land area, was predicting the old mechanism's outcome).

        DOES NOT READ sim/world/land.py (WIRING TWO did; this file no
        longer imports it at all - see the import comment at this file's
        own top). `land.py`'s `arable_iugera` and geography.json's own
        `land`/`land_tiles` blocks are two independently-sourced estimates
        of the same physical quantity (arable land area) that happen to
        agree to within a fixed unit conversion for the 21 shipped regions
        (both ultimately cite the same `land_area_km2`/`arable_fraction`
        pair per region - see land.py's RegionLand and geography.json's own
        `land` block), so reading geography.json's tile-level breakdown
        directly, instead of land.py's region-level aggregate of the same
        numbers, does not introduce a second, independent estimate to drift
        out of step - it is the same source at finer grain.

        NOTE (per this task's own coordination thread, Complaints/52-every-
        civilisation-farms-italian-soil.md): these weights are PROPORTIONS
        that sum to 1.0 over one civilisation's own cells, so a
        civilisation's ABSOLUTE arable endowment cancels out of them
        entirely - two civilisations with wildly different total farmland
        can have identically-SHAPED weight lists. That is Complaints/52's
        own finding (farm_land's total SIZE not reflecting soil quality or
        real arable area), not a defect in this pooling mechanism, which
        only ever needed relative shares; left alone here, deliberately.

        Falls back to ONE cell at a region's own centroid, weighted by that
        region's own `land` block, for any home region NOT found in
        `land_tiles.region_to_tiles` (should not happen for any of the 21
        shipped regions - every one appears there - but a future or test
        civilisation naming an unmapped region should degrade rather than
        silently drop that region's harvest). If NO cell anywhere ends up
        with a positive arable-land figure (every candidate region missing
        both a tile mapping and a `land` block), falls back further to an
        EQUAL split across whatever cells were found. A civilisation with
        no `home_regions` at all gets an empty list, which
        `_pooled_farm_weather_multiplier` below reads as "fall back to the
        old, pre-Complaints/47 civilisation-wide single draw".
        """
        home_regions = list(self.civ.get("home_regions") or [])
        if not home_regions:
            return []
        # Loaded directly here, NOT via `self.geo` (set later in
        # `__init__`, after this method's own call site - see that call
        # site's comment): a second, independent `load_geography()` call is
        # a second cheap JSON parse, not a second SOURCE OF TRUTH, and
        # costs far less than reordering `__init__` while other agents are
        # concurrently editing this same method (this task's own file-
        # ownership note).
        geography = load_geography()
        land_tiles = geography.get("land_tiles") or {}
        tiles_by_id = land_tiles.get("tiles") or {}
        region_to_tiles = land_tiles.get("region_to_tiles") or {}
        regions = geography.get("regions") or {}
        raw_cells = []
        for region in home_regions:
            tile_ids = region_to_tiles.get(region) or []
            if tile_ids:
                for tile_id in tile_ids:
                    tile = tiles_by_id.get(tile_id)
                    if not tile:
                        continue
                    arable_km2 = (tile.get("land_area_km2", 0.0)
                                  * tile.get("arable_fraction", 0.0))
                    raw_cells.append(Sim._WeatherCell(
                        cell_id=tile_id, lat=tile["lat"], lon=tile["lon"],
                        weight=arable_km2))
            else:
                region_record = regions.get(region)
                if not region_record:
                    continue
                land_block = region_record.get("land") or {}
                arable_km2 = (land_block.get("land_area_km2", 0.0)
                              * land_block.get("arable_fraction", 0.0))
                raw_cells.append(Sim._WeatherCell(
                    cell_id=region, lat=region_record.get("lat", 0.0),
                    lon=region_record.get("lon", 0.0), weight=arable_km2))
        if not raw_cells:
            return []
        # STAKEHOLDER ITEM 7: cap cell count independently of how finely
        # land_tiles divides this civilisation's home_regions, BEFORE the
        # weight normalisation below - see FARM_WEATHER_POOLED_CELL_CAP's
        # own declaration (top of this file) for why, and
        # _cap_pooled_farm_weather_cells for how. A no-op whenever
        # len(raw_cells) is already at or under the cap, which is true for
        # every civilisation this project ships today.
        raw_cells = self._cap_pooled_farm_weather_cells(raw_cells)
        total_weight = sum(cell.weight for cell in raw_cells)
        if total_weight > 0.0:
            return [cell._replace(weight=cell.weight / total_weight)
                    for cell in raw_cells]
        equal_weight = 1.0 / len(raw_cells)
        return [cell._replace(weight=equal_weight) for cell in raw_cells]

    def _cap_pooled_farm_weather_cells(self, cells):
        """`cells`, unchanged if there are `FARM_WEATHER_POOLED_CELL_CAP`
        or fewer of them; otherwise merged down to exactly that many, so
        the cubic/quadratic cost below stops being a function of how
        finely `land_tiles` divides a civilisation's territory. See
        `FARM_WEATHER_POOLED_CELL_CAP`'s own declaration for the
        stakeholder item this exists for and why that number.

        WHY MERGE, NOT DROP. Each cell's `weight` here is still its own
        raw arable land area in km2 (this runs BEFORE the sum-to-1.0
        normalisation in `_compute_farm_weather_cells`). Simply keeping
        the `FARM_WEATHER_POOLED_CELL_CAP` largest-weight cells and
        discarding the rest would throw away real arable-weighted mass
        this civilisation actually has, and would also concentrate the
        survivors wherever the single largest cells happen to sit (see
        `_compute_farm_weather_cells`'s own docstring: `north_africa`
        alone supplies 47 of Rome's 88 raw cells by area) rather than
        representing the civilisation's full territory. Merging instead
        preserves every unit of arable land at coarser spatial grain, only
        where finer grain would exceed the cap - the same weighting
        principle `_compute_farm_weather_cells` already uses (arable km2),
        just applied to decide what gets pooled together rather than how
        much each pooled cell counts for.

        HOW "NEARBY" IS DECIDED, DETERMINISTICALLY. Cells are ordered
        along a Z-order (Morton) space-filling curve over their lat/lon
        (`_cell_morton_code`, module level) and split into
        `FARM_WEATHER_POOLED_CELL_CAP`-many contiguous runs of that
        ordering - a standard technique for linearising 2-D points while
        keeping the result in the same neighbourhood, so a contiguous run
        is a genuine spatial cluster rather than an arbitrary batch. Fully
        deterministic: same `cells` in (itself deterministic - see
        `_compute_farm_weather_cells`), same groups out, nothing here
        reads `self.rng` or constructs a `random.Random` - required by
        CLAUDE.md section 6's determinism rule and
        `sim/tests/test_determinism.py`.

        Each merged cell's `lat`/`lon` is the arable-weight-weighted
        centroid of its group (so `_compute_farm_weather_correlation_
        cholesky`'s kernel sees a position representative of where that
        group's arable land actually sits, not an unweighted midpoint);
        its `weight` is the group's summed arable km2 (so the total
        arable-weighted mass across all pooled cells is exactly what it
        was pre-merge - this changes spatial RESOLUTION, never the
        physical quantity being pooled); its `cell_id` is
        `"pooled_<group index>"`, deterministic given the deterministic
        ordering above, which is all `_farm_year_weather_seed` needs from
        it (see `_WeatherCell`'s own comment on why any unique string
        works there).
        """
        cap = int(FARM_WEATHER_POOLED_CELL_CAP)
        if len(cells) <= cap:
            return cells
        ordered = sorted(cells, key=lambda cell: _cell_morton_code(cell.lat, cell.lon))
        cell_count = len(ordered)
        merged = []
        start = 0
        for group_index in range(cap):
            # The remainder (cell_count % cap) is distributed as one extra
            # member each to the FIRST that-many groups, deterministically,
            # rather than left to pile onto whichever group floor-division
            # happens to process last.
            group_size = cell_count // cap + (1 if group_index < cell_count % cap else 0)
            group = ordered[start:start + group_size]
            start += group_size
            total_weight = sum(cell.weight for cell in group)
            if total_weight > 0.0:
                lat = sum(cell.lat * cell.weight for cell in group) / total_weight
                lon = sum(cell.lon * cell.weight for cell in group) / total_weight
            else:
                # Every member of this group happened to carry zero arable
                # weight - fall back to an unweighted centroid so the group
                # still gets a real position instead of pulling toward
                # (0.0, 0.0) for no physical reason.
                lat = sum(cell.lat for cell in group) / len(group)
                lon = sum(cell.lon for cell in group) / len(group)
            merged.append(Sim._WeatherCell(
                cell_id="pooled_%04d" % group_index, lat=lat, lon=lon,
                weight=total_weight))
        return merged

    def _compute_farm_weather_correlation_cholesky(self, cells):
        """The lower-triangular Cholesky factor `matrix_low` of this
        civilisation's cell-to-cell growing-season weather CORRELATION
        matrix, such that `matrix_low @ matrix_low_transpose` reproduces
        that correlation matrix exactly - the one-time linear-algebra setup
        `_pooled_farm_weather_multiplier` spends every year turning a
        vector of INDEPENDENT standard-normal draws into a vector of
        CORRELATED ones (see that method's own docstring for why that is
        the actual mechanism this task exists to build).

        THE KERNEL: correlation(cell_a, cell_b) = exp(-distance_km(cell_a,
        cell_b) / GROWING_SEASON_WEATHER_DECORRELATION_LENGTH_KM), i.e. an
        exponential (Matern, smoothness 1/2) spatial correlation kernel -
        the standard geostatistics choice for a field with no reason to
        expect it to be any smoother than that, and the same shape
        `sim/world/shared_constants.py`'s own declaration of that constant
        cites the empirical precipitation-correlation literature for.
        `distance_km` is the CHORDAL (straight-line, through-the-earth)
        distance between the two cells' lat/lon centroids projected onto a
        sphere of Earth's radius, DELIBERATELY NOT `haversine_km`'s
        great-circle distance despite that function already existing in
        the codebase (`engine/data.py`, called by the geography and economy
        mixins, never by this class):
        an isotropic exponential-family kernel of CHORDAL distance is
        guaranteed positive semi-definite for any configuration of points
        (it is an ordinary Euclidean-space Matern kernel, valid in any
        dimension including the 3-D space the sphere sits in), which the
        SAME kernel evaluated on great-circle distance is NOT guaranteed to
        be for an arbitrary set of points on a sphere (a known result in
        the spatial-statistics literature on covariance functions on the
        sphere) - a real risk here given some civilisations' cells are
        spread across a large fraction of a hemisphere. Chordal and
        great-circle distance agree closely at the scales any one
        civilisation's cells actually span (a few percent apart even at
        several thousand km), so this loses essentially nothing in
        practice while removing a genuine correctness risk in principle.

        NUMERICAL SAFETY NET, NOT A PHYSICAL MECHANISM: each diagonal pivot
        is floored at a tiny positive epsilon before the square root, so a
        configuration that is only PSD up to floating-point error (rather
        than not PSD at all) still factorises instead of crashing on a
        negative-square-root. This is standard "nugget" practice in
        geostatistics for exactly this situation, not a tuned fudge on the
        actual correlation values.

        `cells` is `self._farm_weather_cells`'s own return value, passed in
        (rather than read off `self` directly) so this method has no
        hidden dependency on init order - it only needs the list itself.
        An empty or single-cell list gets a trivial 0x0/1x1 factor; the
        caller (`_pooled_farm_weather_multiplier`) never asks for one
        unless `cells` is non-empty in the first place.

        COST: O(len(cells) ** 3) FLOPs, paid ONCE per `Sim.__init__` (see
        that method's own comment on why), not per year. `cells` here is
        `self._farm_weather_cells`, which `_compute_farm_weather_cells`
        already ran through `_cap_pooled_farm_weather_cells`, so
        `len(cells)` never exceeds `FARM_WEATHER_POOLED_CELL_CAP`
        regardless of how many `land_tiles` cells this civilisation's
        home_regions actually map to (stakeholder item 7 - see that
        constant's own declaration). The largest civ this project ships
        (rome_100ad, 7 home regions) resolves to 88 cells, under the
        cap - under 700,000 elementary operations, not a measurable cost
        against everything else `Sim.__init__` already does.
        """
        cell_count = len(cells)
        correlation = [[0.0] * cell_count for _ in range(cell_count)]
        positions_km = [_cell_chordal_position_km(cell.lat, cell.lon) for cell in cells]
        decorrelation_length_km = GROWING_SEASON_WEATHER_DECORRELATION_LENGTH_KM
        for row in range(cell_count):
            correlation[row][row] = 1.0
            row_x, row_y, row_z = positions_km[row]
            for col in range(row):
                col_x, col_y, col_z = positions_km[col]
                distance_km = math.sqrt((row_x - col_x) ** 2
                                         + (row_y - col_y) ** 2
                                         + (row_z - col_z) ** 2)
                value = math.exp(-distance_km / decorrelation_length_km)
                correlation[row][col] = value
                correlation[col][row] = value
        lower = [[0.0] * cell_count for _ in range(cell_count)]
        pivot_floor = 1e-12
        for row in range(cell_count):
            for col in range(row + 1):
                total = sum(lower[row][k] * lower[col][k] for k in range(col))
                if row == col:
                    pivot = correlation[row][row] - total
                    lower[row][col] = math.sqrt(max(pivot, pivot_floor))
                else:
                    lower[row][col] = (correlation[row][col] - total) / lower[col][col]
        return lower

    def _pooled_farm_weather_multiplier(self, yr, weather_stdev_fraction=None):
        """This year's harvest weather multiplier, pooled across this
        civilisation's own growing-season weather cells instead of one
        draw for the whole territory (Complaints/47-one-weather-draw-for-
        a-continent.md) and instead of one INDEPENDENT draw per home
        region record (Complaints/50-one-label-draws-one-coin.md, the
        replacement this method now is).

        THE MECHANISM, IN ONE SENTENCE: draw one independent standard-
        normal number per cell, CORRELATE them by distance using
        `self._farm_weather_correlation_cholesky`, turn each correlated
        number into a clipped yield multiplier the same way `agriculture.
        draw_weather_multiplier` would, and take the arable-land-share-
        weighted average - answering Complaints/50's own question ("over
        what distance does growing-season weather stop agreeing with
        itself?") with an actual number instead of the two hardcoded
        answers ("one region = perfectly correlated with itself, zero
        correlation with every other region") the old mechanism assumed.

        STEP BY STEP.
        1. `independent_draws[i] = Random(_farm_year_weather_seed(yr,
           region=cells[i].cell_id)).gauss(0.0, 1.0)` - one standard normal
           per cell, EACH ONE a pure function of (civilisation id, cell id,
           year), reusing `_farm_year_weather_seed` completely unchanged
           (see `_WeatherCell`'s own comment on why a tile id is a valid
           thing to pass as that method's `region` argument). This is
           still, exactly as before Complaints/50, "no long-lived
           generator, no `id()` as identity" (CLAUDE.md SS6): nothing here
           is constructed once and advanced across years or across cells:
           every single number is its own fresh `random.Random(seed)`.
        2. `correlated = cholesky_lower @ independent_draws` - a lower-
           triangular matrix-vector product (see `_compute_farm_weather_
           correlation_cholesky`'s own docstring for why this specific
           matrix reproduces the intended correlation structure exactly).
           `correlated[i]` is no longer standard normal in isolation - it
           is one COORDINATE of a draw from the multivariate normal whose
           correlation matches how far apart the cells actually are.
        3. Each cell's own multiplier is `clip(1.0 + stdev *
           correlated[i], WEATHER_FLOOR_MULTIPLIER, WEATHER_CEILING_
           MULTIPLIER)` - the same shape `agriculture.draw_weather_
           multiplier` uses (mean-1.0 Gaussian, same two clip constants,
           read directly off that module rather than re-declared here),
           just fed a correlated `z` instead of calling `rng.gauss` itself
           (drawing the pooled result FROM a raw `z` vector, rather than
           calling `draw_weather_multiplier` once per cell and then trying
           to correlate the results, is what lets the clip apply to each
           cell's OWN realistic multiplier before the weighted average, not
           to the average itself).
        4. The civilisation's pooled multiplier is the ARABLE-LAND-SHARE-
           WEIGHTED AVERAGE of those per-cell multipliers - unchanged from
           Complaints/47's own weighting principle, just computed over
           cells (`self._farm_weather_cells`) instead of region records.

        WHAT THIS FIXES, PRECISELY. The old mechanism's own docstring
        (still readable in this method's git history) admitted two errors
        in the same direction: (a) a region record was treated as ONE
        weather system regardless of its real size (Complaints/50: North
        Africa at 5,750,000 km2 is not one growing season, and neither is
        China at 9,597,000 km2 held as a single region), and (b) two
        region records were treated as fully INDEPENDENT regardless of how
        close they sit (Gaul and Hispania share weather; Britannia and
        Mesopotamia do not). Breaking territory into fixed-area cells fixes
        (a) - a civilisation's effective cell count now tracks its actual
        farmed area, not how many rows a data file happens to give it - and
        the distance-based correlation fixes (b) - two adjacent cells (or
        two cells in neighbouring regions) now draw NEARLY the same
        weather, while two cells continents apart draw NEARLY independent
        weather, exactly the "closer to one draw for Gaul/Hispania, closer
        to independent for Britannia/Mesopotamia" spectrum the old
        docstring named as the fix it was deferring.

        WHAT THIS DOES NOT CLAIM. `GROWING_SEASON_WEATHER_DECORRELATION_
        LENGTH_KM` (sim/world/shared_constants.py) is not a precisely
        measured figure for this exact quantity - see its own declaration
        for the chain of reasoning behind its value and this task's own
        report for a sensitivity sweep across its plausible range. This
        mechanism is only as good as that one number; it is a large
        improvement in KIND over "one region = one system, all regions
        independent" regardless of the exact figure, because unlike that
        assumption it can be checked and revised as a single number rather
        than by re-deriving the whole mechanism.

        A civilisation with no usable cells at all (empty `home_regions`,
        or `_compute_farm_weather_cells` otherwise came back empty) falls
        back to exactly the OLD, pre-Complaints/47 behaviour: one draw,
        seeded from `_farm_year_weather_seed(yr)` with no region, applied
        to the whole territory - unchanged from what Complaints/47's own
        fallback already did, kept here for the same reason (a civilisation
        file this wiring was never meant to touch runs exactly as before).
        """
        soil = agriculture.DEFAULT_SOIL
        stdev = (soil.weather_stdev_fraction if weather_stdev_fraction is None
                 else weather_stdev_fraction)
        cells = self._farm_weather_cells
        if not cells:
            # No usable cells - the old, single-draw behaviour, bit-
            # identical to what this engine did before Complaints/47.
            return agriculture.draw_weather_multiplier(
                random.Random(self._farm_year_weather_seed(yr)), stdev)
        independent_draws = [
            random.Random(self._farm_year_weather_seed(yr, region=cell.cell_id))
            .gauss(0.0, 1.0)
            for cell in cells]
        cholesky_lower = self._farm_weather_correlation_cholesky
        pooled_multiplier = 0.0
        for row, cell in enumerate(cells):
            correlated_z = sum(cholesky_lower[row][col] * independent_draws[col]
                                for col in range(row + 1))
            draw = 1.0 + stdev * correlated_z
            clipped = max(agriculture.WEATHER_FLOOR_MULTIPLIER,
                          min(agriculture.WEATHER_CEILING_MULTIPLIER, draw))
            pooled_multiplier += cell.weight * clipped
        return pooled_multiplier

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

        WIRING TWO (Complaints/closed/47-one-weather-draw-for-a-continent.md) is
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
        # WIRING TWO (Complaints/closed/47-one-weather-draw-for-a-continent.md):
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
        premium = (self.wage_index / self._wage_index_base - 1.0) * PERCENT_SCALE
        # The message wants the SAME shortfall wage_index's own property
        # just computed, not a second, separately-derived copy of it - see
        # wage_index's own comment for why it is measured against this
        # civilisation's unshocked configured trend rather than the
        # (still tech-mutable) `_pop_scale_base`. Recovered algebraically
        # from `premium` rather than recomputed, so the two can never drift
        # apart: premium == elasticity * shortfall * 100, by construction.
        shortfall = (premium / PERCENT_SCALE) / self.WAGE_SCARCITY_ELASTICITY if self.WAGE_SCARCITY_ELASTICITY else 0.0
        if premium > 0.5 and yr - self._said_wage_cascade >= 15:
            self._said_wage_cascade = yr
            self.household.log.append((yr, "population still %d%% below trend: wages "
                                 "(and anything billed in them) are running "
                                 "%d%% above normal for here, and will ease "
                                 "as the population does"
                             % (round(shortfall * PERCENT_SCALE), round(premium))))

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
        # WHERE SCANDAL STOOD WHEN THE PLAYER LAST LOOKED. `state` prints the
        # chance of being denounced from the CURRENT scandal, and scandal moves
        # DURING the step - so a break tester read "scandal 21.9 ... 0% chance
        # of being denounced this year", pressed step once, and the same batch
        # printed the first warning and "RUN ENDS: denounced: as a sorcerer".
        # The figure was never wrong; it was answering about a year that had
        # already gone. A player needs the direction as well as the level, and
        # this is the only place that knows both.
        self.household.scandal_last_year = self.household.scandal

        # step() is a readable sequence of phase calls, in the same order the
        # phases always ran in; the phases themselves are below, and each still
        # reads and writes exactly the self.* state it always did. Only a
        # handful of values flow forward between phases as arguments/returns
        # rather than through self.*: pool and hired_left (start_projects into
        # progress), and remaining/remaining_after_projects/hours_effective_total
        # (progress into wage_fallback and reputation).
        self._step_apprenticeships()          # 0.  people whose apprenticeship ended
        self._step_staff()                     # 1.  staff, attrition
        self._step_money()                     # 2.  money (and 2c. threshold goals)
        if self._step_dated_shocks():          # 3.  dated shocks
            return
        self._step_teach_trades()              # 4a. teach the trades this society does not have
        self._step_standing_work_directive()   # 4a(ii). the standing "work" directive
        pool, hired_left = self._step_start_projects()   # 4b. start new projects
        self._step_materials()                 # 4c. materials
        # 5. progress, director hours
        remaining, remaining_after_projects, hours_effective_total = (
            self._step_progress(pool, hired_left))
        # 5b. if there is no work and no money, take a job
        remaining = self._step_wage_fallback(remaining)
        # 6. reputation, familiarity, protection, scandal
        self._step_reputation(pool, remaining, remaining_after_projects, hours_effective_total)
        self._step_bondage()                   # 6b. serving out a debt
        self._step_founder_mortality()          # 7. founder mortality

        # 8. random events
        if self.events and not self.dead_reason:
            self._random_events(self.year)

        self.year += 1

    # ---- THE YEAR'S PHASES ------------------------------------------------
    # _step_apprenticeships through _step_founder_mortality - the fourteen
    # named phases step() calls above, in the same order - moved to
    # sim/engine/core_step_phases.py's StepPhasesMixin. Sim still inherits
    # StepPhasesMixin below, so step() calls self._step_whatever() exactly
    # as it did when these were defined here.



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
