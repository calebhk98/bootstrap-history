"""The simulation itself: what one year does, and the loop over years."""
import copy, os, sys

from sim.constants import declare
from sim.living_stock.api import GrantOpeningHerds, GrantOpeningStock
from . import money_units
from .mortality_shock import cut_cohorts
from .disease_burden import burden_from_holdings
from .wage_scarcity import wage_index_of
from sim.engine.state import SimulationState, ActiveProjectState
from sim.engine.state_seat import bind_seat
from .data import (DEFAULTS, kit_capital, load_civ, load_geography, load_resources,
                   nodes_in_civ_money, TECH_EFFECTS, TRADE_REGISTRY)

from sim.world import demography
from sim.world import agriculture
from sim.world import farming_technique
from sim.world import land
from sim.geography.api import regions, tiles_held
from sim.unit_conversions import PERCENT_SCALE


from .territory_required import require_territory
from .win_condition_rule import win_condition_met
from sim.knowledge.api import LearnTechnique, declared_starting_techs
from .economy import EconomyMixin
from .node_rederive import NodeRederiveMixin
from .market_clearing import MarketClearingMixin
from .forward_foreign_trade import ForwardForeignTradeMixin
from .food_eaten import FoodEatenMixin
from .demographic_recovery import DemographicRecoveryMixin
from .regional_people import RegionalPeopleMixin
from .urban_share import UrbanShareMixin
from .forward_agriculture import ForwardAgricultureMixin
from .forward_living_stock import ForwardLivingStockMixin
from .forward_reporting import ReportingForwardsMixin
from .forward_coin import ForwardCoinMixin
from .forward_campaigns import ForwardCampaignsMixin
from .forward_diffusion import DiffusionForwardsMixin
from .market_demand import MarketDemandMixin
from .concern_volume import ConcernVolumeMixin
from .concern_book_sales import ConcernBookSalesMixin
from .techniques_in_use import TechniquesInUseMixin
from .industry_concern import IndustryConcernMixin
from .industry_depth import IndustryDepthMixin
from .incumbent_prices import IncumbentPricesMixin
from .producer_costs import ProducerCostsMixin
from .fog import FogMixin
from .forward_mechanics import ForwardMechanicsMixin
from .forward_knowledge import ForwardKnowledgeMixin
from .disease_port import DiseasePortMixin
from .geography_port import GeographyPortMixin
from .labour_port import LabourPortMixin
from .projects import ProjectsMixin
from .core_seats import SeatMixin
from .year_run import run_year
from .seat_run import SeatRunMixin
from .seat_builds import SeatBuildsMixin
from .seat_sight import SeatSightMixin
from .forward_hazards import HazardsForwardsMixin
from .seat_defaults import default_policy
from .ways import WaysMixin
from .held_works import HeldWorksMixin
from .works import WorksMixin
from .society import SocietyMixin
from .society_actors import ActorsMixin
from .founder_sales import FounderSalesMixin
from .seat_dealings import SeatDealingsMixin
from .seat_bank import SeatBankMixin
from .interest_groups import InterestGroupsMixin
from .benefactions import BenefactionsMixin
from .forward_freight import ForwardFreightMixin
from .forward_resources import ForwardResourcesMixin
from .forward_materials import ForwardMaterialsMixin
from .mod_stores import ModStoresMixin
from .core_properties import ForwardingPropertiesMixin
from .goals import GoalsMixin
from .core_step_phases import StepContext, StepPhasesMixin
from .economy_port import EconomyPortMixin
from .data import trade_family
from .invariants import check_simulation_invariants
from sim.agents.api import Household
from .agents_port_household import HouseholdPort
from sim.reporting.api import RecordEvent
from sim.materials.api import RestoreReadings


class Sim(
        ModStoresMixin,
        ForwardMechanicsMixin,
        ForwardKnowledgeMixin,
        EconomyMixin,
        MarketClearingMixin,
        ForwardForeignTradeMixin,
        MarketDemandMixin,
        ConcernVolumeMixin,
        ConcernBookSalesMixin,
        TechniquesInUseMixin,
        IndustryDepthMixin,
        IndustryConcernMixin,
        IncumbentPricesMixin,
        ProducerCostsMixin,
        FogMixin,
        GeographyPortMixin,
        DiseasePortMixin,
        LabourPortMixin,
        ProjectsMixin,
        SeatMixin,
        SeatRunMixin,
        SeatBuildsMixin,
        SeatSightMixin,
        HazardsForwardsMixin,
        WaysMixin,
        WorksMixin,
        HeldWorksMixin,
        SocietyMixin,
        ActorsMixin,
        DiffusionForwardsMixin,
        FounderSalesMixin,
        SeatDealingsMixin,
        SeatBankMixin,
        InterestGroupsMixin,
        BenefactionsMixin,
        ForwardFreightMixin,
        ForwardingPropertiesMixin,
        GoalsMixin,
        StepPhasesMixin,
        ForwardLivingStockMixin,
        ReportingForwardsMixin,
        ForwardCoinMixin,
        ForwardAgricultureMixin,
        ForwardResourcesMixin,
        ForwardMaterialsMixin,
        FoodEatenMixin,
        DemographicRecoveryMixin,
        RegionalPeopleMixin,
        UrbanShareMixin,
        ForwardCampaignsMixin,
        EconomyPortMixin,
        NodeRederiveMixin,
):
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

    # DISEASE_BURDEN_TECH_IDS (nodes declaring the `disease_burden` mechanic) is
    # provided by the mechanics module (sim/mechanics); food techs in _TECH_EFFECTS.json do not declare it.

    def __init__(self, nodes, order, rng, events=True, cfg=None, verbose=False,
                 bounty_set=None, civ=None, manual=False, debug=None, defer_economy=False):
        self.nodes = nodes
        # PRECOMPUTED ONCE: which node ids carry a `win_condition` at all,
        # sorted for the same reproducibility reason _check_win_conditions
        # (below) needs a fixed order. self.nodes is the loaded tech tree -
        # assigned exactly once, right here, and never reassigned or mutated
        # (checked: `grep -rn "self\.nodes\[.*\]\[.*\] *="` across every file
        # in this package turns up nothing, and every other write of
        # `self.nodes` anywhere is a *different* class's unrelated attribute
        # of the same name in commodities.py's CommodityLedger). So a node's
        # win_condition membership can never change after this point, so this
        # list is built once here: `_check_win_conditions` only needs the
        # handful of node ids that carry a win_condition, and sorting all
        # ~2,849 node ids from `self.nodes` for that every single year would
        # be pure waste.
        self._win_condition_keys = sorted(
            node_id for node_id, node in nodes.items() if node.get("win_condition"))
        self.order = list(order)
        self.rng = rng
        self._agriculture = agriculture
        self._demography = demography
        self._tech_effects = TECH_EFFECTS
        self.step_context = StepContext(
            trade_family=trade_family,
            invariant_checker=check_simulation_invariants)
        self.debug = __debug__ if debug is None else bool(debug)
        self.events = events
        self.cfg = dict(DEFAULTS, **(cfg or {}))
        self.verbose = verbose
        self.bounty_set = set(bounty_set or ())
        self.civ = copy.deepcopy(civ or load_civ())
        self.start_civ = copy.deepcopy(self.civ)    # the opening values, kept while self.civ drifts
        self.nodes = nodes_in_civ_money(nodes, self.civ)
        self._remember_derived_gates(self.civ["starting_techs"])
        # Authoritative live SimulationState hierarchy
        from sim.engine.state import (
            SimulationState, HouseholdState, ProjectsState, ActorsState,
            EconomyState, GovernanceState, FounderState,
            ScenarioState, PopulationState
        )
        from . import game_assembly
        from .geography_port import MODS_DIR
        self.assembly = game_assembly.build(MODS_DIR, self.debug)
        self.state = SimulationState(
            household=HouseholdState(capital=0.0),
            projects=ProjectsState(),
            economy=EconomyState(),
            governance=GovernanceState(),
            founder=FounderState(),
            scenario=ScenarioState(),
            population=PopulationState(),
            actors=ActorsState(),
            _civ=self.civ.get("id"),
        )
        game_assembly.attach(self)   # the modules answer from here on: the opening below already sends commands
        # SET HERE SO EVERY READER CAN READ THEM DIRECTLY. Both are assigned
        # afterwards by whoever builds the game - cli_interactive, cli_agent,
        # sim/tests/fingerprint.py - and both round-trip through saveload's `_fog`
        # and `_goal` keys rather than through SAVE_FIELDS. Without these two
        # lines neither attribute exists until somebody assigns it, so all 44
        # readers had to supply a fallback of their own.
        #
        # A fallback written out at 44 call sites is 44 chances to write a
        # different one, and nothing compares them. Worse, a fallback turns a
        # misspelt or renamed attribute into a plausible answer where a
        # direct read would raise AttributeError on the first call. That is
        # not hypothetical here: a three-argument read of `w` survived the
        # rename of that attribute to `value_weights` and went on handing the
        # `values` command an empty dict for eight commits, with the whole
        # suite green.
        self.fog = False
        self.goal = None
        # MANUAL MODE: the optimizer in step() 4b never starts anything on its
        # own. The only projects that ever become active are ones something
        # called start_project() on, i.e. a human or an agent choosing them.
        # See the comment on step() 4b and on start_project() for why this
        # exists: without it, "choosing" a node in `play` was cosmetic.
        self.manual = bool(manual)
        self.value_weights = self.civ["values"]
        # A civilization brings its own date, its own price level and its own
        # capacity to fund things. Norse Scandinavia does not start in 100 AD.
        self.cfg["start_year"] = int(self.civ.get("year", self.cfg["start_year"]))
        self.price_index = float(self.civ.get("price_index", 1.0))
        self._wage_index_base = float(self.civ.get("wage_index", 1.0))
        # A PLAGUE IS A HIT TO THE WHOLE LABOUR MARKET, NOT ONLY TO YOU. A
        # mortality event large enough to take a third of one household's
        # own staff must not leave everybody ELSE's wages untouched, as if
        # the rest of the world's labour market saw nothing happen.
        # pop_scale is a computed property over the age-cohort population;
        # a mortality shock cuts the cohorts directly.
        # An age-cohort population (docs/architecture/WIRING_MILESTONE_4.md
        # SS6), built and proven standalone in sim/world/demography.py, and
        # read and mutated by pop_scale/wage_index (below) and by _shocks()
        # (society.py). `Population.stationary()` finds the model's OWN
        # stable age structure for a population of this civilisation's
        # configured size, rather than an independently invented split - see
        # that method's own docstring for why.
        #
        # SEEDED, DELIBERATELY NOT FROM self.rng: Population owns its own
        # generator (for the `jitter=True` path only - see self._demography.py's
        # NUTRITION_YEAR_TO_YEAR_NOISE_STD), and nothing in this engine ever
        # passes jitter=True (see _advance_population below), so this seed
        # never actually gets drawn from. It is derived from the
        # civilisation's own id, not Python's randomised string hash() (which
        # would depend on PYTHONHASHSEED and break determinism across
        # processes), purely so two civilisations do not happen to share one.
        _population_seed = sum((index + 1) * ord(character) for index, character
                               in enumerate(str(self.civ.get("id", "civ")))) % (2 ** 32)
        self.population = self._demography.Population.stationary(
            float(self.civ.get("population", self.DEFAULT_POPULATION_100AD)),
            seed=_population_seed)
        # Initial condition: cleared area is what feeds the starting
        # population given the yield of the best ground the held tiles
        # offer; later clearing works down the same best-first ladder.
        held_tiles = tiles_held(self.civ, self.world_map)
        require_territory(self.civ, held_tiles)
        territory = land.territory_cropland(self.farm_sites())
        self._farm_ladder = territory.ladder
        self._farm_arable_ceiling = territory.cropped_hectares
        self.labour.set_farm_area(self._agriculture.farmland_for_population(
            self._adult_equivalent_population(self.population), ladder=self._farm_ladder).hectares)
        self._opening_farmed_hectares = self.farm_land.hectares
        # the weather cells and their correlation are fixed for the life of a run: built now, from the territory as it opens
        self.view("farm_weather_cells")()
        # THE GRANARY (Complaints/44-no-granary-so-the-baseline-collapses.md).
        # Started at zero, not at some invented reserve: this is an INITIAL
        # CONDITION (CLAUDE.md SS3.1's own allowed category, same as
        # `farm_land` just above), and the honest initial condition for "how
        # much surplus this civilisation has banked at the moment the
        # simulation begins observing it" is "none recorded" rather than a
        # figure picked to soften the first few years - see
        # GRANARY_CAPACITY_YEARS_OF_DEMAND's own declaration (self._agriculture.py)
        # for where a sourced, physically-grounded number DOES enter this
        # mechanism (the CEILING on how large a buffer can grow, not the
        # starting point). What actually answers Complaints/44 is that
        # `_demographic_recovery` below carries whatever THIS ATTRIBUTE holds
        # forward from year to year: it must not rebuild an
        # `self._agriculture.Storage` at stock_kg=0.0 every single year regardless
        # of what the previous year harvested, or the starting value would
        # not matter.
        # SAVE_FIELDS ("farm_stock_kg", sim/engine/saveload.py) is
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
        self._last_farm_workers_fte = None
        self._farm_technique_this_year = farming_technique.DEFAULT_TECHNIQUE
        self.year = self.cfg["start_year"]
        config = self.cfg
        # THE FOUNDER'S HOUSEHOLD: money, staff, knowledge, plant and standing,
        # as its own object rather than eighty-odd attributes of this one. See
        # sim/agents/household.py for what it holds and
        # docs/architecture/HOUSEHOLD_EXTRACTION.md for why: making this an
        # object of its own, rather than more state on `Sim`, is what would let
        # a government, a rival household or a firm exist someday, each owning
        # its own purse and its own knowledge instead of sharing this one.
        #
        # AT THIS SOCIETY'S PRICES, like everything else you will spend it on.
        # The kits are stated in labourer-years; since revenue and
        # living costs convert through `price_index` (see
        # economy.living_cost), leaving the purse flat would mean "four
        # hundred denarii" buys a third more months of bread in Luoyang than
        # in Scandinavia, silently, for no modelled reason. A kit is "a few
        # months' subsistence", and a few months'
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
        start_money = config["start_capital"]
        if start_money is None:
            start_money = kit_capital(config["start_kit"], self.civ)
        self.household = Household(
            starting_capital=float(start_money) * self.price_index,
            operating_changed=self._operating_changed,
            active_changed=self._active_changed,
            workforce_changed=self._workforce_changed,
            state=self.state,
            port=HouseholdPort())
        self._seat_facades = {self.state.acting_seat: self.household}
        # EVERY AUTOMATIC BEHAVIOUR, IN ONE PLACE, SWITCHABLE.
        #
        # Everything automatic must be controllable: a player can enable or
        # disable it, or do it manually instead, and every automatic action
        # logs a line saying it happened. Defaults differ between the
        # optimizer and a human: the optimizer has to run unattended, so it
        # manages its own household; a player is handed nothing they did not
        # ask for.
        #
        # STAYS ON `Sim`, NOT ON `Household` - see household.py's module
        # docstring: one key, auto_court_heir, is written for succession after
        # a mortal owner's death, and the rest of the dict is not worth
        # splitting away from it for that.
        self.policy = default_policy(manual)
        # World-level "last time I said X" trackers; household ones live on HouseholdState.
        # THE FOLLOWING EIGHT FIELDS ARE BIOGRAPHICAL TO ONE MORTAL PERSON, not
        # to a household in general, and stay on `Sim` for exactly that reason
        # - see household.py's module docstring for the full argument. Moving
        # them would mean deciding, right now, with no second example to
        # design against, what death, personal hours or a patron mean for a
        # firm or a government; that is a real design question and this
        # extraction does not answer it by default.
        self.state.founder.founder_alive = True
        self.state.founder.dead_reason = None
        self.state.founder.director_hours_spent_founder = 0.0
        # founder remaining lifespan, elite male already aged 35
        self.state.founder.life_left = (1e9 if self.cfg["immortal"]
                          else max(self.FOUNDER_MIN_REMAINING_LIFE_YEARS,
                                    rng.gauss(self.cfg["founder_life_mean"],
                                              self.cfg["founder_life_sd"])))
        self.state.founder.living_cost_paid = 0.0
        self._spend_this_year = 0.0
        # --- RAW MATERIAL QUANTITIES -------------------------------------
        # How much of each material physically exists: a material's
        # existence somewhere does not mean an unlimited quantity of it is
        # available.
        self.res = load_resources()
        # --- GEOGRAPHY: where things are, FOR THE CIVILIZATION IN PLAY (computed once; see sim/geography/)
        self.geography.open(load_geography(self.world_map))
        # Whatever this civilization already has is free and already done, and it
        # is GRANTED, not earned: it must never count in done_earned as though
        # the founder had built it, and it must never be "forgotten" in a
        # sacking - Han China does not forget how to cast iron because your
        # workshop burned down.
        #
        # Populates self.household.done/.granted, not a fresh set here, and
        # stays on Sim rather than moving into Household.__init__ because it
        # needs the loaded tree and civ record to validate against (and to
        # raise ValueError on an unknown starting technology) - state this
        # class deliberately does not hold a reference to.
        starting_techs = declared_starting_techs(self.civ, self.nodes)
        for tech_id in starting_techs:
            self.send(LearnTechnique(tech_id, granted=True))
        self.send(GrantOpeningStock())
        # Starting ownership is deliberately exhausted by starting_techs.
        # Tier and zero cost describe a node's position in the universal graph;
        # they do not mean every society on Earth already owns it.  In
        # particular, never infer one civilization's materials or institutions for another
        # civilization from those fields.
        self.country_literacy()
        for field in ("literacy_general", "literacy_elite"):
            self.start_civ[field] = self.literacy(field)
        self.civ.pop("literacy_general", None)
        self.civ.pop("literacy_elite", None)
        self._reconnect_state_hooks()
        # opened now, not by the first question a screen or a cost asks: while it opens the engine's
        # own figures answer, and nothing computed from them may stay cached afterwards
        # a game about to load a save leaves it: the save holds the seats and the economy's record
        self._economy_deferred = bool(defer_economy)
        if not defer_economy:
            self.economy.open_agent()
            self.send(GrantOpeningHerds())
            self._done_changed()
            self.join_cast_seats()

    def _reconnect_state_hooks(self):
        """Reconnect transient cache state, version counters, and invalidating wrappers after save/load."""
        # Household façades first, so version bumps fired while reconnecting land on this state
        if hasattr(self, "household"):
            self.sync_seat_facades()
        self.state.attach_purses()
        self.state.actors.purses.observer = self.note_lender_posting
        acting = self.state.acting_seat
        try:
            for seat_id in self.state.seats:
                bind_seat(self.state, seat_id)
                self._wrap_seat_containers()
        finally:
            bind_seat(self.state, acting)
        cleared = getattr(self.state.holdings, "farm_cleared_hectares", None)
        if cleared is not None:
            self.labour.set_farm_area(cleared)
            self.refresh_farm_territory()
        # Synchronize demographic cohort floats
        if self.state.population is not None and hasattr(self, "population"):
            if self.state.population.pop_children or self.state.population.pop_working_age or self.state.population.pop_elderly:
                self.population.children = float(self.state.population.pop_children)
                self.population.working_age = float(self.state.population.pop_working_age)
                self.population.elderly = float(self.state.population.pop_elderly)
            else:
                self.state.population.pop_children = float(self.population.children)
                self.state.population.pop_working_age = float(self.population.working_age)
                self.state.population.pop_elderly = float(self.population.elderly)

        # Sync civ live state and metadata
        if self.state._weights:
            self.value_weights.update(self.state._weights)
        if self.state._rng is not None:
            rng_version, _keys, rng_gaussian = self.state._rng
            self.rng.setstate((rng_version, tuple(int(x) for x in _keys), rng_gaussian))

        # Reset transient caches
        self._reset_economic_caches()
        from . import game_assembly
        game_assembly.attach(self)
        # the demand the last throttle saw is read before the next one, so it is carried
        self.send(RestoreReadings())

    def _wrap_seat_containers(self):
        """Wrap the bound seat's mutation-aware containers and start its version counters."""
        from sim.engine.economy import _InvalidatingDict, _InvalidatingSet
        from sim.engine.state import ActiveProjectState
        self.state.projects.business.watch = self._operating_changed
        self.state.projects.active = _InvalidatingDict(
            {k: ActiveProjectState.from_dict(v if isinstance(v, dict) else v.to_canon_dict(), _on_change=self._active_changed)
             for k, v in (self.state.projects.active or {}).items()},
            on_change=self._active_changed
        )
        self.state.household.employees = _InvalidatingDict(
            self.state.household.employees or {},
            on_change=self._workforce_changed
        )
        self.household.start_version_counters(self.state)

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

    # `pop_scale` and `wage_index` are COMPUTED PROPERTIES, not stored
    # attributes advanced by a hand-written recovery clock (docs/
    # architecture/WIRING_MILESTONE_4.md SS6-SS7), the same "attribute plus
    # forwarding property" shape the household extraction uses. That lets
    # every call site across economy/labour/geography/projects that reads
    # `self.pop_scale`/`self.wage_index` keep doing so unchanged, while what
    # backs them can change underneath.
    #
    # `pop_scale` must be derived from `self.population`'s age-cohort model,
    # not from a hand-set scalar decaying on a fixed clock: sim/world/
    # self._demography.py's own test suite shows two populations that lose an
    # identical 30% in one year, one sparing working-age adults and one not,
    # diverge sharply afterwards - a result a scalar deficit decaying on a
    # clock that knows nothing about WHO was lost can never produce.
    #
    # `pop_scale` uses `DEFAULT_POPULATION_100AD` (the default scenario's
    # configured population) as its reference, so `pop_scale == 1.0` means
    # "a default-scenario-sized labour market" - every downstream formula is calibrated
    # against that. The numerator is `self.population.total`, the age-cohort
    # model's own running headcount.
    @property
    def pop_scale(self):
        return max(self.POP_SCALE_FLOOR, self.population.total / self.DEFAULT_POPULATION_100AD)

    # `wage_index`: LABOUR SCARCER, SO DEARER. The scarcity signal is how
    # far the age-cohort model's actual `pop_scale` sits below this
    # civilisation's UNSHOCKED starting trend. A hazard only needs to cut
    # `self.population`'s cohorts (see `_apply_population_mortality_shock`
    # below); that lowers `pop_scale` directly, and this property reads the
    # gap that opens - a hazard never touches `wage_index` itself.
    #
    # Recovery is emergent: the cohort model's own births and deaths move
    # pop_scale back toward the trend, or not, with no clock.
    @property
    def wage_index(self):
        unshocked_trend = max(
            self.POP_SCALE_FLOOR,
            float(self.civ.get("population", self.DEFAULT_POPULATION_100AD))
            / self.DEFAULT_POPULATION_100AD)
        return wage_index_of(self._wage_index_base, self.WAGE_SCARCITY_ELASTICITY, self.pop_scale, unshocked_trend)

    def _apply_population_mortality_shock(self, raw):
        """Cut `self.population`'s cohorts by `raw` (a fraction of the whole,
        e.g. 0.45 for the Black Death), unevenly by age - called from
        _shocks() (society.py).

        AGE-DIFFERENTIATED BY THE SAME STARVATION_VULNERABILITY_* RATIOS
        sim/world/demography.py already declares for its own nutrition-
        driven excess mortality (children hit 1.6x as hard as working-age
        adults, the elderly 1.4x - see that module for the sourcing), scaled
        so the POPULATION-WEIGHTED AVERAGE loss equals `raw` exactly. This
        is what makes two equal-headcount losses diverge afterward depending
        on who survived - the property sim/tests/test_self._demography.py's own
        falsification test demands, and a scalar deficit decaying on a fixed
        clock could never produce (see the comment above pop_scale).

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
        cut_cohorts(self.population, raw, self._demography.STARVATION_VULNERABILITY_CHILD,
                    self._demography.STARVATION_VULNERABILITY_WORKING_AGE,
                    self._demography.STARVATION_VULNERABILITY_ELDERLY)

    def _adult_equivalent_population(self, population):
        """`population`'s food need in ADULT-EQUIVALENT units - the same
        weighting self._demography.py's own `Population.nutrition_ratio` (and,
        via `_subsistence_food`, `Population.stationary`) already use
        internally: a child counts as `CHILD_CALORIE_EQUIVALENT` of an
        adult, an elderly person as `ELDERLY_CALORIE_EQUIVALENT`, exactly
        so this file never has its own, second opinion on what a "person"
        is worth in calories.

        WIRING_MILESTONE_4.md SS4.3's UNIT MISMATCH, AND HOW THIS RESOLVES
        IT. `self._agriculture.Storage.step` takes a plain `population` argument
        and uses it exactly once: `food_demand_kg = population *
        annual_food_demand_kg_per_person(crop)`. Nothing in self._agriculture.py
        assumes that number is a flat headcount beyond that one line - it
        is "however many ration-equivalents need feeding" - so the fix
        needs no change to self._agriculture.py's signature at all: this engine
        computes the SAME adult-equivalent number self._demography.py already
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
        return (population.children * self._demography.CHILD_CALORIE_EQUIVALENT
                + population.working_age
                + population.elderly * self._demography.ELDERLY_CALORIE_EQUIVALENT)

    def _disease_burden(self):
        """WIRING ONE (Complaints/closed/47-technology-cannot-stop-people-dying-
        young.md): this civilisation's CURRENT disease burden, 1.0 being
        the full pre-industrial infectious environment sim/world/
        self._demography.py already assumes by default, 0.0 being clean water,
        sanitation, germ-theory hygiene and vaccination all present -
        `self._demography.py`'s own module docstring names the derivation this
        reuses rather than inventing: sum the `population` weights of
        whichever of `DISEASE_BURDEN_TECH_IDS` (above) this civilisation
        currently holds (`self.has`, which `starting_techs` and completed
        nodes both feed - see Household.__init__'s own comment), and
        express that as a fraction of ALL EIGHT unlocked (rather than
        hardcoding the 0.15 those eight happen to sum to today, so this
        stays correct if `_TECH_EFFECTS.json` ever reweights them):

            disease_burden = 1.0 - unlocked_weight / total_weight

        Read fresh every call from `self.has(...)`: a standing fact about
        this civilisation ("it now boils its water"). Food technologies act
        through the farming technique instead (see `_farming_technique`).

        Clamped to [0, 1] defensively (a total of exactly 0.15 measured
        directly against `_TECH_EFFECTS.json` today makes this unreachable
        in practice, but a future edit to that file changing the eight
        weights' sum should not be able to hand `self._demography.Population.
        step` a burden outside the range it declares valid).
        """
        tech_ids = self.DISEASE_BURDEN_TECH_IDS
        return burden_from_holdings(
            {tech_id: self._tech_effects[tech_id].get("population", 0.0) for tech_id in tech_ids},
            {tech_id: self.disease_burden_held(tech_id) for tech_id in tech_ids})

    def _refresh_demographic_indexes(self, year):
        """Say why the wage bill moved, if it moved enough to be worth
        saying - the only job left here once pop_scale/wage_index became
        computed properties (see above). Kept as its own method, called
        both after a year's ordinary advance and immediately after a
        hazard fires, for the same reason it always was: a shock's
        announced effects should be visible immediately, not lag a step.
        """
        premium = (self.wage_index / self._wage_index_base - 1.0) * PERCENT_SCALE
        # Recover the shortfall from `premium` so the message and
        # wage_index cannot drift apart.
        shortfall = (premium / PERCENT_SCALE) / self.WAGE_SCARCITY_ELASTICITY if self.WAGE_SCARCITY_ELASTICITY else 0.0
        if premium > 0.5 and year - self.state.scenario._said_wage_cascade >= 15:
            self.state.scenario._said_wage_cascade = year
            self.send(RecordEvent.in_year(year, "wage_cascade", "population still %d%% below trend: wages "
                "(and anything billed in them) are running "
                "%d%% above normal for here, and will ease "
                "as the population does"
                % (round(shortfall * PERCENT_SCALE), round(premium)), population_below_trend_percent=round(shortfall * PERCENT_SCALE), wage_premium_percent=round(premium)))

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

    # ---- GEOGRAPHY: reach and material cost, FOR THE CIVILIZATION IN PLAY --
    # Reach must be computed from the ACTUAL civilization's own home
    # ground, never hard-coded from one fixed point such as Italy: a
    # single Italy-measured `reach` per region gets every civilization
    # except the one based there backwards - for example Han China would treat Chinese silk as three
    # reach-steps away and Malaya, which Chinese and Malay traders already
    # sail to routinely, as an exotic frontier, while Italy, a place that
    # civilization has never seen, would be reach 0. Everything below
    # computes reach from the ACTUAL civilization's own home ground.

    DIRECTORS_EXTRA_APPROACH_RATE = declare(
        "DIRECTORS_EXTRA_APPROACH_RATE", 0.12, kind="temporary_heuristic",
        unit="dimensionless (fraction of the gap to capacity closed per "
             "year)", source=None, confidence="D",
        why="How fast the household's deputy-director pool approaches "
            "what its institutions can support, net of the same "
            "working-age mortality that thins ordinary staff. Tuned so "
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
    INSOLVENCY_FLOOR_MIN_LABOUR_HOURS = declare(
        "INSOLVENCY_FLOOR_MIN_LABOUR_HOURS", 80600.0, kind="temporary_heuristic",
        unit="labour hours", source=None, confidence="D",
        why="Floor on how deep into arrears a household can sit before insolvency's"
            ' staff bleed can begin, for a household with very low revenue - so a '
            'household earning almost nothing is not bled the instant it dips a '
            'denarius below zero. Round number, not measured. How deep a debt a '
            'household can carry is the labour it would take to clear, so the floor'
            ' is hours of work, the same burden whatever the coin is worth.')
    INSOLVENCY_FLOOR_MIN = money_units.PricedInLabourHours("INSOLVENCY_FLOOR_MIN_LABOUR_HOURS")
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
    AUTO_BRIBE_CAPITAL_THRESHOLD_LABOUR_HOURS = declare(
        "AUTO_BRIBE_CAPITAL_THRESHOLD_LABOUR_HOURS", 40300.0, kind="temporary_heuristic",
        unit="labour hours", source=None, confidence="D",
        why="Minimum capital before the optimizer's bribery policy will spend at "
            'all, so a poor household is not bled dry bribing away scandal it might'
            ' survive anyway. Round number, not measured. Capital is a stock of '
            'labour-valued goods and coin, so the threshold is the hours of work it'
            ' represents.')
    AUTO_BRIBE_CAPITAL_THRESHOLD = money_units.PricedInLabourHours("AUTO_BRIBE_CAPITAL_THRESHOLD_LABOUR_HOURS")
    AUTO_BRIBE_CAPITAL_SHARE = declare(
        "AUTO_BRIBE_CAPITAL_SHARE", 0.12, kind="temporary_heuristic",
        unit="dimensionless (share of capital)", source=None,
        confidence="D",
        why="Ceiling on how much of current capital one year's bribery "
            "spend can be, so buying down scandal cannot alone bankrupt "
            "the household. Tuned, not measured.")
    AUTO_BRIBE_COST_LABOUR_HOURS_PER_SCANDAL_POINT = declare(
        "AUTO_BRIBE_COST_LABOUR_HOURS_PER_SCANDAL_POINT", 5240.0, kind="temporary_heuristic",
        unit="labour hours per scandal point", source=None, confidence="D",
        why='What buying down one point of scandal costs, capping total spend '
            'alongside AUTO_BRIBE_CAPITAL_SHARE. Invented figure, not sourced to '
            'any attested bribe schedule. An official accepts a payment worth the '
            'work and risk he gives up, so the sum is the hours of unskilled labour'
            ' it buys.')
    AUTO_BRIBE_COST_PER_SCANDAL_POINT = money_units.PricedInLabourHours("AUTO_BRIBE_COST_LABOUR_HOURS_PER_SCANDAL_POINT")
    BRIBES_YTD_DECAY = declare(
        "BRIBES_YTD_DECAY", 0.7, kind="temporary_heuristic",
        unit="dimensionless (fraction kept per year)", source=None,
        confidence="D",
        why="How much of the running bribes_ytd total (itself the "
            "denominator update_protection() reads for the bribery "
            "protection term) survives into next year - a bribe's "
            "protective effect fades rather than accumulating forever. "
            "Tuned, not measured.")
    BRIBE_SCANDAL_REDUCTION_LABOUR_HOURS_PER_POINT = declare(
        "BRIBE_SCANDAL_REDUCTION_LABOUR_HOURS_PER_POINT", 6050.0, kind="temporary_heuristic",
        unit="labour hours per scandal point removed (before bribability)", source=None, confidence="D",
        why='How much bribery spend it takes to remove one point of scandal, scaled'
            " further by this society's own bribability weight. Invented figure, "
            'not sourced to any attested bribe schedule. An official accepts a '
            'payment worth the work and risk he gives up, so the sum is the hours '
            'of unskilled labour it buys.')
    BRIBE_SCANDAL_REDUCTION_SCALE = money_units.PricedInLabourHours("BRIBE_SCANDAL_REDUCTION_LABOUR_HOURS_PER_POINT")

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
    DEPUTIES_CARRY_THE_WORK_FROM = declare(
        "DEPUTIES_CARRY_THE_WORK_FROM", 0.5, kind="temporary_heuristic",
        unit="deputies (continuous level of directors_extra)", source=None,
        confidence="D",
        why="How many deputies it takes before a programme can go on "
            "without its founder; below it the deputies still do real "
            "work but the dissolution clock keeps running. One rule, "
            "read by the death notice, the clock, hiring and `state`. "
            "Round number, not measured.")
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

    def view(self, name):
        """The published view `name` (call it, or index a keyed one); engine and UI code not in a module reads this way."""
        return self.assembly.views[name]

    def send(self, command):
        """Apply `command` through the module that owns it now; engine code not yet in a module sends this way."""
        return self.assembly.handlers[type(command)](command)

    def step(self):
        """Advance every seat one year (the order and what runs once or per seat: year_run.py)."""
        run_year(self)

    # ---- THE YEAR'S PHASES ------------------------------------------------
    # _step_apprenticeships through _step_founder_mortality - the fourteen
    # named phases step() calls above, in the same order - moved to
    # sim/engine/core_step_phases.py's StepPhasesMixin. Sim still inherits
    # StepPhasesMixin below, so step() calls self._step_whatever() exactly
    # as it did when these were defined here.



    # ---- THRESHOLD GOALS: completed by measurement, not by labour ---------
    # A goal need not be a thing you build. "Raise literacy past a fifth" or
    # "cut most of what epidemics take" are states of the whole
    # society, not a project with hours and materials - see data/branches/
    # meta.goals and its own note on why a threshold is still modelled as a
    # node (so closure()/critical_path()/Sim.run() never need a second idea
    # of what a goal is) rather than as a second mechanism bolted on beside
    # the ordinary one.
    WIN_CONDITION_METRICS = frozenset(
        ("literacy_general", "literacy_elite", "epidemic_relief"))

    def _win_condition_value(self, condition):
        """The live number a win_condition's `metric` names, 0..1. Raises for
        a metric this engine does not know how to read - at load time, via
        `validate`, not mid-game - rather than silently reading 0 forever for
        a typo no playtest would otherwise catch."""
        metric = condition.get("metric")
        if condition.get("source") == "attribute":
            path = condition.get("path")
            if not isinstance(path, str) or path.startswith("_") or "." in path:
                raise ValueError("invalid win_condition attribute path %r" % path)
            value = getattr(self, path, None)
            if not isinstance(value, (int, float)):
                raise ValueError("win_condition attribute %r is not numeric" % path)
            return float(value)
        if condition.get("source") == "generation_share":
            breakdown = self.generation_breakdown_kw()
            total = breakdown["total_kw"]
            return (breakdown["sources_kw"].get(condition.get("key"), 0.0) / total
                    if total else 0.0)
        if metric in ("literacy_general", "literacy_elite"):
            return self.literacy(metric)
        if metric == "epidemic_relief":
            # hazard_relief returns the SURVIVING fraction of the harm
            # (1.0 = no protection at all); relief is what is cut, the rest
            # of it - see society.py's own docstring on the diminishing,
            # never-quite-zero shape of that number.
            return 1.0 - self.hazard_relief("staff_loss")[0]
        raise ValueError("unknown win_condition metric %r" % metric)

    def _check_win_conditions(self, year):
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
        that avoids re-sorting every one of the ~2,849 node ids in the whole
        tree, every single year, to reach the handful that actually carry a
        win_condition at all - pure self time (`sorted` and dict-get, both
        C-level, nothing further to profile under it).
        """
        for node_id in self._win_condition_keys:
            if node_id in self.state.projects.done:
                continue
            win_condition = self.nodes[node_id]["win_condition"]
            if not win_condition:
                continue
            val = self._win_condition_value(win_condition)
            if not win_condition_met(win_condition, val):
                continue
            self.send(LearnTechnique(node_id, year=year))
            self.send(RecordEvent.in_year(year, "goal_achieved", "achieved: " + self.nodes[node_id]["name"]))
            self.record_goal_reached(node_id, year)

    def run(self, goal, horizon=None):
        self.goal = goal
        self.state.projects.done_year = {}
        horizon = horizon or self.cfg["horizon_years"]
        end = self.cfg["start_year"] + horizon
        while self.state.scenario.year < end and not self.run_over():
            self.step()
        return self


# ----------------------------------------------------------------------------
# Strategies
# ----------------------------------------------------------------------------
