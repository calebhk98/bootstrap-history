"""The simulation itself: what one year does, and the loop over years."""
import copy, os, sys

from sim.constants import declare
from sim.demography.api import OpenPopulation
from sim.workforce.api import WatchStaff
from sim.living_stock.api import GrantOpeningHerds, GrantOpeningStock
from sim.engine.state import SimulationState, ActiveProjectState
from sim.engine.state_seat import bind_seat
from .data import (DEFAULTS, kit_capital, load_civ, load_geography, load_resources,
                   nodes_in_civ_money, TECH_EFFECTS, TRADE_REGISTRY)

from sim.world import demography
from sim.world import agriculture
from sim.world import farming_technique
from sim.world import land
from sim.geography.api import regions, tiles_held


from sim.land.api import rules as land_rules
from sim.knowledge.api import LearnTechnique, declared_starting_techs
from .forward_markets import ForwardMarketsMixin
from .forward_foreign_trade import ForwardForeignTradeMixin
from .forward_demography import ForwardDemographyMixin
from .forward_agriculture import ForwardAgricultureMixin
from .forward_living_stock import ForwardLivingStockMixin
from .forward_reporting import ReportingForwardsMixin
from .forward_coin import ForwardCoinMixin
from .forward_campaigns import ForwardCampaignsMixin
from .forward_diffusion import DiffusionForwardsMixin
from .forward_prices import ForwardPricesMixin
from .forward_mechanics import ForwardMechanicsMixin
from .forward_knowledge import ForwardKnowledgeMixin
from .forward_disease import DiseaseForwardsMixin
from .forward_land import ForwardLandMixin
from .forward_workforce import ForwardWorkforceMixin
from .projects import ProjectsMixin
from .core_seats import SeatMixin
from .year_run import run_year
from sim.seats.api import SetFounderLife
from .forward_seats import ForwardSeatsMixin
from .forward_hazards import HazardsForwardsMixin
from .forward_polity import PolityForwardsMixin
from .seat_defaults import default_policy
from .forward_actors import ActorsForwardsMixin
from .forward_finance import ForwardFinanceMixin
from .forward_production import ForwardProductionMixin
from .forward_freight import ForwardFreightMixin
from .forward_resources import ForwardResourcesMixin
from .forward_materials import ForwardMaterialsMixin
from .mod_stores import ModStoresMixin
from .core_properties import ForwardingPropertiesMixin
from .core_step_phases import StepContext, StepPhasesMixin
from .data import trade_family
from .invariants import check_simulation_invariants
from sim.agents.api import Household
from .agents_port_household import HouseholdPort
from sim.materials.api import RestoreReadings


class Sim(
        ModStoresMixin,
        ForwardMechanicsMixin,
        ForwardKnowledgeMixin,
        ForwardMarketsMixin,
        ForwardForeignTradeMixin,
        ForwardProductionMixin,
        ForwardPricesMixin,
        ForwardLandMixin,
        DiseaseForwardsMixin,
        ForwardWorkforceMixin,
        ProjectsMixin,
        SeatMixin,
        ForwardSeatsMixin,
        HazardsForwardsMixin,
        PolityForwardsMixin,
        ActorsForwardsMixin,
        DiffusionForwardsMixin,
        ForwardFinanceMixin,
        ForwardFreightMixin,
        ForwardingPropertiesMixin,
        StepPhasesMixin,
        ForwardLivingStockMixin,
        ReportingForwardsMixin,
        ForwardCoinMixin,
        ForwardAgricultureMixin,
        ForwardResourcesMixin,
        ForwardMaterialsMixin,
        ForwardDemographyMixin,
        ForwardCampaignsMixin,
):
    FOUNDER_MIN_REMAINING_LIFE_YEARS = declare(
        "FOUNDER_MIN_REMAINING_LIFE_YEARS", 5, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="Floor on the founder's gaussian-drawn remaining lifespan, so "
            "an unlucky draw does not end a run in its first years before "
            "anything is possible. Round guard value, not a mortality "
            "estimate.")
    # DISEASE_BURDEN_TECH_IDS (nodes declaring the `disease_burden` mechanic) is
    # provided by the mechanics module (sim/mechanics); food techs in _TECH_EFFECTS.json do not declare it.

    def __init__(self, nodes, order, rng, events=True, cfg=None, verbose=False,
                 bounty_set=None, civ=None, manual=False, debug=None, defer_economy=False):
        self.nodes = nodes
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
            SimulationState, HouseholdState, ProjectsState,
            EconomyState, FounderState,
            ScenarioState
        )
        from . import game_assembly
        from .bridge_land import MODS_DIR
        self.assembly = game_assembly.build(MODS_DIR, self.debug)
        self.state = SimulationState(
            household=HouseholdState(capital=0.0),
            projects=ProjectsState(),
            economy=EconomyState(),
            founder=FounderState(),
            scenario=ScenarioState(),
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
        self.open_value_weights()
        # A civilization brings its own date, its own price level and its own
        # capacity to fund things. Norse Scandinavia does not start in 100 AD.
        self.cfg["start_year"] = int(self.civ.get("year", self.cfg["start_year"]))
        self.price_index = float(self.civ.get("price_index", 1.0))
        self._wage_index_base = float(self.civ.get("wage_index", 1.0))
        # the nation's people: the age structure its civilisation's size settles into (the demography module owns them)
        self.send(OpenPopulation())
        # Initial condition: cleared area is what feeds the starting
        # population given the yield of the best ground the held tiles
        # offer; later clearing works down the same best-first ladder.
        held_tiles = tiles_held(self.civ, self.world_map)
        land_rules.require_territory(self.civ, held_tiles)
        territory = land.territory_cropland(self.farm_sites())
        self._farm_ladder = territory.ladder
        self._farm_arable_ceiling = territory.cropped_hectares
        self.labour.set_farm_area(self._agriculture.farmland_for_population(
            self._adult_equivalent_population(self.population), ladder=self._farm_ladder).hectares)
        self._opening_farmed_hectares = self.farm_land.hectares
        # the weather cells and their correlation are fixed for the life of a run: built now, from the territory as it opens
        self.view("farm_weather_cells")()
        # the granary starts empty (an initial condition) and carries over between years (demography's farm year)
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
            state=self.state,
            port=HouseholdPort())
        self._seat_facades = {self.state.acting_seat: self.household}
        self.send(WatchStaff(self.state.acting_seat))
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
        # founder remaining lifespan, elite male already aged 35
        self.send(SetFounderLife(1e9 if self.cfg["immortal"]
                                 else max(self.FOUNDER_MIN_REMAINING_LIFE_YEARS,
                                          rng.gauss(self.cfg["founder_life_mean"], self.cfg["founder_life_sd"]))))
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
        from . import game_assembly
        game_assembly.attach(self)   # the modules read the state as loaded from here on
        cleared = self.view("farm_holdings")()["cleared_hectares"]
        if cleared is not None:
            self.labour.set_farm_area(cleared)
            self.refresh_farm_territory()

        # Sync civ live state and metadata
        if self.state._rng is not None:
            rng_version, _keys, rng_gaussian = self.state._rng
            self.rng.setstate((rng_version, tuple(int(x) for x in _keys), rng_gaussian))

        # Reset transient caches
        self._reset_economic_caches()
        game_assembly.attach(self)
        # the demand the last throttle saw is read before the next one, so it is carried
        self.send(RestoreReadings())

    def _wrap_seat_containers(self):
        """Wrap the bound seat's mutation-aware containers and start its version counters."""
        from sim.invalidating import _InvalidatingDict, _InvalidatingSet
        from sim.engine.state import ActiveProjectState
        self.state.projects.business.watch = self._operating_changed
        self.state.projects.active = _InvalidatingDict(
            {k: ActiveProjectState.from_dict(v if isinstance(v, dict) else v.to_canon_dict(), _on_change=self._active_changed)
             for k, v in (self.state.projects.active or {}).items()},
            on_change=self._active_changed
        )
        self.send(WatchStaff(self.state.acting_seat))
        self.household.start_version_counters(self.state)

    # ---- OUTSIDE-SURFACE PROPERTIES FOR THE EXTRACTED HOUSEHOLD ----------
    # Moved to sim/engine/core_properties.py's ForwardingPropertiesMixin:
    # 107 one-line @property forwards onto self.household/self.population
    # (capital, done, operating, log, and so on), plus the comment block
    # explaining why each is a property and never __getattr__. Sim still
    # inherits ForwardingPropertiesMixin below, so every name in that file
    # keeps resolving on a live Sim instance exactly as it did here.


    # -- helpers ------------------------------------------------------------

    # ---- GEOGRAPHY: reach and material cost, FOR THE CIVILIZATION IN PLAY --
    # Reach must be computed from the ACTUAL civilization's own home
    # ground, never hard-coded from one fixed point such as Italy: a
    # single Italy-measured `reach` per region gets every civilization
    # except the one based there backwards - for example Han China would treat Chinese silk as three
    # reach-steps away and Malaya, which Chinese and Malay traders already
    # sail to routinely, as an exotic frontier, while Italy, a place that
    # civilization has never seen, would be reach 0. Everything below
    # computes reach from the ACTUAL civilization's own home ground.

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
