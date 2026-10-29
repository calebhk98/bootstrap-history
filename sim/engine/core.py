"""The simulation itself: what one year does, and the loop over years."""
import copy, os, sys

from sim.constants import declare
from sim.demography.api import OpenPopulation, rules as demography_rules
from sim.workforce.api import WatchStaff
from sim.living_stock.api import GrantOpeningHerds, GrantOpeningStock
from sim.engine.state import SimulationState
from sim.assembly.api import notify_seat_bound
from .data import (DEFAULTS, kit_capital, load_civ,
                   nodes_in_civ_money)

from sim.world import demography
from sim.world import agriculture
from sim.agriculture.api import RecordOpeningFarm, SetFarmTerritory
from sim.finance.api import NoteLenderPosting
from .farm_territory_refresh import refresh_farm_territory
from sim.world import land


from sim.land.api import rules as land_rules
from sim.knowledge.api import LearnTechnique, StartDoneYearRecord, declared_starting_techs
from . import change_hooks, node_rederive, seat_registry, year_steps
from .year_run import run_year
from sim.knowledge.api import ReplaceTree
from sim.seats.api import JoinCastSeats, SetFounderLife, SetGoal, SetPolicy
from sim.refusal import Refusal
from .seat_defaults import default_policy
from .root_facts import horizon_end_year, scenario_fact, view_fact
from .year_steps import StepContext
from .data import trade_family
from .invariants import check_simulation_invariants
from sim.ledger.api import OpenCashBook, RestorePurse
from sim.materials.api import RestoreReadings
from sim.polity.api import SetValueWeights
from sim.projects.api import RestoreProjectOrder, WatchActive
from sim.ventures.api import WatchBusiness
from sim.scenario.api import (OpenScenario, RecordOpeningLiteracy, ScenarioSources, SetEndYear, SetFog,
                              SetYear)
from . import units


class Sim:
    # DISEASE_BURDEN_TECH_IDS (nodes declaring the `disease_burden` mechanic) is
    # provided by the mechanics module (sim/mechanics); food techs in _TECH_EFFECTS.json do not declare it.

    def __init__(self, nodes, order, rng, events=True, cfg=None, verbose=False,
                 bounty_set=None, civ=None, manual=False, debug=None, defer_economy=False):
        self._agriculture = agriculture
        self._demography = demography
        self.step_context = StepContext(
            trade_family=trade_family,
            invariant_checker=check_simulation_invariants)
        self.debug = __debug__ if debug is None else bool(debug)
        self.verbose = verbose
        from . import game_assembly
        from .bridge_land import MODS_DIR
        self.mods_dir = MODS_DIR   # this game's mods: its assembly, its policy switches and its seats' defaults read this
        self.assembly = game_assembly.build(self.mods_dir, self.debug)
        self._scenario = self.assembly.modules["scenario"]
        # the setup the game is played in: the civilisation, the configuration, the modes (the scenario module owns them)
        self.send(OpenScenario(
            civilisation=copy.deepcopy(civ or load_civ()), configuration=dict(DEFAULTS, **(cfg or {})), manual=bool(manual),
            events=events, bounty_set=set(bounty_set or ()),
            sources=ScenarioSources(load_civilisation=load_civ, kit_capital=kit_capital,
                                    display_units=lambda: (units.registry(), units.chosen_units(), lambda: units.unit_context(self))),
            dice=rng))
        self.nodes = nodes_in_civ_money(nodes, self.civ)
        node_rederive.remember_derived_gates(self, self.civ["starting_techs"])
        # Authoritative live SimulationState hierarchy
        from sim.engine.state import (
            SimulationState, HouseholdState,
            EconomyState, FounderState
        )
        self.state = SimulationState(
            household=HouseholdState(),
            economy=EconomyState(),
            founder=FounderState(),
            _civ=self.civ.get("id"),
        )
        game_assembly.attach(self)   # the modules answer from here on: the opening below already sends commands
        self.send(RestoreProjectOrder(tuple(order)))   # the order the household's hours serve projects, opened from the tree's
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
        # set after the build by whoever front-ends the game (and `seed` again by a load); None while a game has none
        self.seed = None
        self.session_seat = None
        self._stack_cautions = {}   # per seat: whether it was told of the stack caution
        self._founder_death_cache = None   # the founder's death read off the log by the UI, once it is found
        # MANUAL MODE: the optimizer in step() 4b never starts anything on its
        # own. The only projects that ever become active are ones something
        # called start_project() on, i.e. a human or an agent choosing them.
        # See the comment on step() 4b and on start_project() for why this
        # exists: without it, "choosing" a node in `play` was cosmetic.
        self.send(SetValueWeights(tuple(self.civ["values"].items())))
        # A civilization brings its own date, its own price level and its own
        # capacity to fund things. Norse Scandinavia does not start in 100 AD.
        self.price_index = float(self.civ.get("price_index", 1.0))
        # the nation's people: the age structure its civilisation's size settles into (the demography module owns them)
        self.send(OpenPopulation())
        # Initial condition: cleared area is what feeds the starting
        # population given the yield of the best ground the held tiles
        # offer; later clearing works down the same best-first ladder.
        held_tiles = self.view("tiles_listed_by")(self.civ)
        land_rules.require_territory(self.civ, held_tiles)
        territory = land.territory_cropland(self.view("farm_sites")())
        self.send(SetFarmTerritory(territory.ladder, territory.cropped_hectares))
        self.labour.set_farm_area(self._agriculture.farmland_for_population(
            demography_rules.adult_equivalents(self.view("population")()), ladder=self.view("farm_ladder")()).hectares)
        self.send(RecordOpeningFarm())
        # the weather cells and their correlation are fixed for the life of a run: built now, from the territory as it opens
        self.view("farm_weather_cells")()
        # the granary starts empty (an initial condition) and carries over between years (demography's farm year)
        self.send(SetYear(self.cfg["start_year"]))
        config = self.cfg
        # The opening purse is at this society's prices: the kits are stated in labourer-years, and revenue and living costs convert
        # through `price_index`, so a purse left flat would buy a third more months of bread in Luoyang than in Scandinavia.
        start_money = config["start_capital"]
        if start_money is None:
            start_money = kit_capital(config["start_kit"], self.civ)
        opening_cash = float(start_money) * self.price_index
        self.send(RestorePurse(opening_cash))   # the seat's opening purse, and the cash its book measures from
        self.send(OpenCashBook(opening_cash))
        self.send(WatchStaff(self.state.acting_seat))
        self.send(WatchActive(self.state.acting_seat))
        self.send(WatchBusiness(self.state.acting_seat))
        # EVERY AUTOMATIC BEHAVIOUR, IN ONE PLACE, SWITCHABLE.
        #
        # Everything automatic must be controllable: a player can enable or
        # disable it, or do it manually instead, and every automatic action
        # logs a line saying it happened. Defaults differ between the
        # optimizer and a human: the optimizer has to run unattended, so it
        # manages its own household; a player is handed nothing they did not
        # ask for.
        #
        for name, value in default_policy(manual, self.mods_dir).items():
            self.send(SetPolicy(name, value))
        # World-level "last time I said X" trackers; household ones live on HouseholdState.
        # THE FOLLOWING EIGHT FIELDS ARE BIOGRAPHICAL TO ONE MORTAL PERSON, not
        # to a household in general, and stay on `Sim` for exactly that reason
        # - see household.py's module docstring for the full argument. Moving
        # them would mean deciding, right now, with no second example to
        # design against, what death, personal hours or a patron mean for a
        # firm or a government; that is a real design question and this
        # extraction does not answer it by default.
        # founder remaining lifespan, elite male already aged 35
        life = self.view("founder_life_terms")()
        self.send(SetFounderLife(1e9 if life["immortal"]
                                 else max(life["minimum"], rng.gauss(life["mean"], life["spread"]))))
        # --- RAW MATERIAL QUANTITIES -------------------------------------
        # How much of each material physically exists: a material's
        # existence somewhere does not mean an unlimited quantity of it is
        # available.
        # --- GEOGRAPHY: where things are, FOR THE CIVILIZATION IN PLAY (computed once; see sim/geography/)
        self.view("legacy_geography")().open(self.view("geography_data")())
        # Whatever this civilization already has is free and already done, and it
        # is GRANTED, not earned: it must never count in done_earned as though
        # the founder had built it, and it must never be "forgotten" in a
        # sacking - Han China does not forget how to cast iron because your
        # workshop burned down.
        #
        # Sends LearnTechnique(granted=True) for each; stays on Sim because it
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
        self.send(RecordOpeningLiteracy(self.view("literacy")("literacy_general", None), self.view("literacy")("literacy_elite", None)))
        self._reconnect_state_hooks()
        # opened now, not by the first question a screen or a cost asks: while it opens the engine's
        # own figures answer, and nothing computed from them may stay cached afterwards
        # a game about to load a save leaves it: the save holds the seats and the economy's record
        self._economy_deferred = bool(defer_economy)
        if not defer_economy:
            self.view("legacy_economy")().open_agent()
            self.send(GrantOpeningHerds())
            self._done_changed()
            joined = self.send(JoinCastSeats())
            if isinstance(joined, Refusal):
                raise ValueError(str(joined))

    def _reconnect_state_hooks(self):
        """Reconnect transient cache state, version counters, and invalidating wrappers after save/load."""
        self.state.actors.purses.observer = lambda account, signed, label: self.send(NoteLenderPosting(account, signed, label))
        for seat_id in self.state.seats:
            self._wrap_seat_containers(seat_id)
        from . import game_assembly
        game_assembly.attach(self)   # the modules read the state as loaded from here on
        cleared = self.view("farm_holdings")()["cleared_hectares"]
        if cleared is not None:
            self.labour.set_farm_area(cleared)
            refresh_farm_territory(self)

        # Sync civ live state and metadata
        if self.state._rng is not None:
            rng_version, _keys, rng_gaussian = self.state._rng
            self.rng.setstate((rng_version, tuple(int(x) for x in _keys), rng_gaussian))

        # Reset transient caches
        game_assembly.attach(self)
        notify_seat_bound(self.assembly)
        # the demand the last throttle saw is read before the next one, so it is carried
        self.send(RestoreReadings())

    def _wrap_seat_containers(self, seat_id=None):
        """Wrap a seat's mutation-aware containers (the acting seat's unless one is named) and start its version counters."""
        seat_id = self.state.acting_seat if seat_id is None else seat_id
        self.send(WatchBusiness(seat_id))
        self.send(WatchActive(seat_id))
        self.send(WatchStaff(seat_id))

    # ---- the facts the root states itself (sim/engine/root_facts.py) ----
    # the scenario module's: the clock, the modes and the setup the game was built from
    year = scenario_fact("world.year", SetYear)
    fog = scenario_fact("world.fog", lambda value: SetFog(bool(value)))
    fuzzy_estimates = scenario_fact("world.fuzzy_estimates")
    cfg = scenario_fact("configuration")
    civ = scenario_fact("civilisation")
    start_civ = scenario_fact("start_civilisation")
    manual = scenario_fact("manual")
    events = scenario_fact("events")
    bounty_set = scenario_fact("bounty_set")
    end_year = property(horizon_end_year, lambda self, value: self.send(SetEndYear(value)))
    # the tree, the stores, the purse and the founder's goal and policy
    nodes = view_fact("tree_nodes", set_command=ReplaceTree)
    stores = view_fact("store_book")
    capital = view_fact("acting_balance", set_command=RestorePurse)
    goal = view_fact("goal", "node", SetGoal)
    goal_year = view_fact("goal", "year")
    policy = view_fact("founder", "policy")
    # the techniques and the projects of the acting seat
    active = view_fact("active_projects")
    done = view_fact("techniques_held")
    done_year = view_fact("done_year")
    revealed = view_fact("techniques_revealed")
    operating = view_fact("operating")
    mothballed = view_fact("mothballed")
    bountied = view_fact("bountied")
    granted = view_fact("techniques_granted")
    forgotten = view_fact("techniques_forgotten")
    failed_attempts = view_fact("failed_attempts")
    paid_towards = view_fact("paid_towards")


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

    def view(self, name):
        """The published view `name` (call it, or index a keyed one); engine and UI code not in a module reads this way."""
        return self.assembly.views[name]

    def send(self, command):
        """Apply `command` through the module that owns it now; engine code not yet in a module sends this way."""
        return self.assembly.handlers[type(command)](command)

    def _done_changed(self):
        change_hooks.done_changed(self)

    def _operating_changed(self):
        change_hooks.operating_changed(self)

    @property
    def labour(self):
        """The workforce module's labour implementation (tests and mods still call its members)."""
        return self.assembly.modules["workforce"].labour

    def step(self):
        """Advance every seat one year (the order and what runs once or per seat: year_run.py)."""
        run_year(self)

    # ---- the seat registry (sim/engine/seat_registry.py) ----

    def add_seat(self, seat_id, seat):
        seat_registry.add_seat(self, seat_id, seat)

    def act_as(self, seat_id):
        """Run the body as `seat_id`, then restore the seat that was acting."""
        return seat_registry.act_as(self, seat_id)

    @property
    def rng(self):
        """The game's random source: the scenario module's (`game_random`)."""
        return self._scenario.dice

    def run(self, goal, horizon=None):
        self.goal = goal
        self.send(StartDoneYearRecord())
        horizon = horizon or self.cfg["horizon_years"]
        end = self.cfg["start_year"] + horizon
        while self.year < end and not self.view("run_over")():
            self.step()
        return self


# ----------------------------------------------------------------------------
# Strategies
# ----------------------------------------------------------------------------
