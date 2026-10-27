"""What the labour package reads of the game: one member per view the workforce module declares, answered through its needs.

`Labour` (sim/labour/) asks this object where it used to ask the engine. The members that return raw state
(`state`, `household`, `rng`, `nodes`, `order`) are `legacy_*` views, debts that go when that state moves. The three
engine-held facts labour writes (the farm's land, the year's farming technique, the goal's closure) are written through
`legacy_game` until their owners move."""
from sim.agents.api import edges
from sim.demography.api import rules as demography_rules
from sim.ledger.api import PayEdge, ReceiveFromEdge
from sim.prices.api import solve_prices_core
from .commands import BuildHousing


class WorkforceWorld:

    # the named edges labour's postings name as their counterparty
    EDGE_WORKERS = edges.EDGE_WORKERS
    EDGE_SLAVE_TRADERS = edges.EDGE_SLAVE_TRADERS
    EDGE_EMPLOYERS = edges.EDGE_EMPLOYERS

    def __init__(self, needs, owner):
        self._needs = needs
        self._owner = owner          # the workforce module: its own views are asked of it directly
        self._trade_registry = None
        self._economy = AgentEconomyReads(needs)

    def send(self, command):
        """Apply a command through the module that owns it."""
        return self._needs.send(command)

    # ---- the acting seat and the log ----

    def reputation(self):
        return self._needs.standing()["reputation"]

    @property
    def founder_alive(self):
        return self._needs.founder()["alive"]

    def logged_events(self):
        """How many lines the acting seat's log holds now."""
        return len(self._needs.event_log())

    @property
    def workforce(self):
        """The acting seat's people and hours: the module's own seat state, written only by labour and the module."""
        return self._owner.seat

    @property
    def year(self):
        return self._needs.year()

    @property
    def policy(self):
        """The acting seat's standing policy switches (read here, never written)."""
        return self._needs.founder()["policy"]

    @property
    def society(self):
        """The society's labour hours and wage tightness: the module's own world state."""
        return self._owner.world

    @property
    def household(self):
        return self._needs.legacy_household_actor()

    @property
    def state(self):
        return self._needs.legacy_state()

    @property
    def rng(self):
        return self._needs.legacy_dice()

    def simulation(self):
        """The game itself, for the town providers a mod registers to read (labour/town_providers.py)."""
        return self._needs.legacy_game()

    # ---- the scenario ----

    @property
    def cfg(self):
        return self._needs.game_config()

    @property
    def civ(self):
        return self._needs.civilisation()

    @property
    def nodes(self):
        return self._needs.legacy_tree()

    @property
    def order(self):
        return self._needs.legacy_order()

    @property
    def goal(self):
        return self._needs.legacy_state()._goal

    @property
    def goal_closure(self):
        return getattr(self._needs.legacy_game(), "_goal_closure", None)

    @goal_closure.setter
    def goal_closure(self, value):
        self._needs.legacy_game()._goal_closure = value

    def closure(self, nodes, goal):
        return self._needs.tree_closure(goal)

    def has(self, node_id):
        return node_id in self._needs.techniques_held()

    def held_and_running(self, include_starting=True):
        return self._needs.held_techniques(include_starting)

    def built_ways(self):
        """The roads, track, canals, bridges and ports built, {edge key: {way: true}} (the record itself)."""
        return self._needs.built_ways()

    def is_visible(self, node_id, _memo=None):
        return self._needs.visibility(node_id, _memo)

    def is_venture(self, node_id):
        return self._needs.is_venture[node_id]

    def running(self, node_id):
        return self._needs.running[node_id]

    def institution_units(self, node_id):
        return self._needs.institution_units[node_id]

    def reopen_units(self, node_id):
        return self._needs.reopen_units[node_id]

    def exclusion_reason(self, node_id):
        return self._needs.exclusion_reason[node_id]

    def start_reason(self, node_id, ignore_trade=False, _memo=None, _why=True):
        return self._needs.start_check(node_id, ignore_trade, _memo, _why)

    def mechanic(self, node_id, name):
        return self._needs.mechanic[name].get(node_id)

    def nodes_with_mechanic(self, name):
        return tuple(self._needs.mechanic[name])

    def effect_factor(self, channel, start=1.0, exponent=None):
        return self._needs.effect_factor(channel, start, exponent)

    def effect_holds(self, node_id, spec):
        return self._needs.effect_holds(node_id, spec)

    def effect_sum(self, channel, start=0.0):
        return self._needs.effect_sum(channel, start)

    def effect_terms(self, channel):
        return self._needs.effect_terms(channel)

    def effect_value(self, node_id, spec):
        return self._needs.effect_value(node_id, spec)

    @property
    def LABOUR_PRODUCTIVITY_SOURCES(self):
        return self._needs.labour_productivity_sources()

    @property
    def ROOM_SOURCES(self):
        return self._needs.room_sources()

    @property
    def STAFF_CAPACITY_SOURCES(self):
        return self._needs.staff_capacity_sources()

    @property
    def STAFF_SOURCES(self):
        return self._needs.staff_sources()

    def staff_hire_advice(self, kind, count=None):
        return self._needs.staff_hire_advice(kind, count)

    def literacy(self, field):
        return self._needs.literacy(field, self._needs.acting_country())

    def research_productivity(self):
        return self._needs.research_productivity(self._needs.acting_country())

    # ---- text ----

    def money_text(self, amount, grouped=False, short=False):
        """A sum in the civilisation's coin as the player's chosen unit writes it."""
        return self._needs.money_text(amount, grouped, short)

    def plain_number(self, value, digits=0):
        """A count, a number of people or of hours."""
        return self._needs.plain_number(value, digits)

    # ---- people, places and the nation ----

    @property
    def population(self):
        return self._needs.population()

    @property
    def pop_scale(self):
        return self._needs.pop_scale()

    def people_by_tile(self):
        """{tile: people} from the regions the demography module tracks, or None before they cover the tiles held."""
        return self._needs.people_by_tile()

    def urban_fraction(self):
        return self._needs.urban_fraction()

    def adult_equivalent_population(self, population):
        return demography_rules.adult_equivalents(population)

    def home_tiles_held(self):
        return self._needs.home_tiles_held()

    def home_tiles_held_version(self):
        """Changes whenever the tiles the home country owns might."""
        return self._needs.home_tiles_held_version()

    # ---- prices, money and the market ----

    @property
    def price_index(self):
        return self._needs.price_index()

    def home_price_level(self):
        return self._needs.home_price_level()

    def last_market_price_ratio(self, material):
        return self._needs.last_market_price_ratio[material]

    def material_price_factor(self, emp_key):
        return self._needs.material_price_factor[emp_key]

    def real_output_per_head(self):
        return self._needs.real_output_per_head()

    def rep_factor(self):
        return self._needs.rep_factor()

    def revenue(self):
        return self._needs.revenue_estimate()

    def upkeep(self):
        return self._needs.upkeep()

    def living_cost(self, _rev=None, _upkeep=None):
        return self._needs.living_cost(_rev, _upkeep)

    def spending_power(self, kind='buy'):
        return self._needs.spending_power(kind)

    def can_pay(self, cost):
        return self._needs.can_pay(cost)

    def refusal_text(self, what, cost):
        return self._needs.purchase_refusal(what, cost)

    def pay_edge(self, edge_name, amount, purpose):
        """The acting seat's household pays a named edge."""
        self._needs.send(PayEdge(edge_name, amount, purpose))

    def receive_from_edge(self, edge_name, amount, purpose):
        """A named edge pays the acting seat's household."""
        self._needs.send(ReceiveFromEdge(edge_name, amount, purpose))

    def harvest_share_taken(self, material):
        """Share of the harvest of a material the home state's forms take from growers; none without a government."""
        return self._needs.harvest_share_taken[material]

    def housing_price_per_place(self):
        return self._needs.housing_price_per_place()

    def trade_school_price_per_seat(self):
        return self._needs.trade_school_price_per_seat()

    def build_worker_housing(self, places):
        return self._needs.send(BuildHousing(places))

    # ---- the agent economy ----

    @property
    def economy(self):
        """What the agent economy answers, as the views the module declares give it."""
        return self._economy

    def economy_unskilled_wage(self):
        """Money one hour of the unskilled trade is paid in the agent economy; None until the game's money is priced at it."""
        return self._needs.agent_unskilled_wage()

    # ---- the trade tables and the wage schedule ----

    @property
    def wages(self):
        return self._needs.starting_wages()

    @property
    def trades_absent(self):
        return self._needs.trades_absent()

    @property
    def trade_notes(self):
        return self._needs.trade_notes()

    @property
    def trade_registry(self):
        """Each trade's fields as plain mappings: the named ones and everything else its file states."""
        if self._trade_registry is None:
            self._trade_registry = {trade_id: {"family": trade.family, "training_years": trade.training_years, **trade.extra}
                                    for trade_id, trade in self._needs.trade_records().items()}
        return self._trade_registry

    def trade_family(self, trade):
        return self._needs.trade_family[trade]

    def build_wage_schedule(self, civ, tightness_factors=None):
        return self._needs.wage_schedule_for(civ, tightness_factors)

    def techniques_available_to(self, production, reached_nodes):
        return solve_prices_core.techniques_available_to(production, reached_nodes)

    @property
    def wage_index(self):
        return self._owner.wage_index()

    @property
    def wage_index_base(self):
        return self._owner.wage_index_terms()["base"]

    @property
    def HOURS_PER_PERSON_YEAR(self):
        return self._owner.hours_per_person_year()

    # ---- the farm ----

    def farm_holdings(self):
        """The acting seat's farm: hectares, granary, what the last farm year left and the hours the farm needs."""
        return self._needs.farm_holdings()

    @property
    def farm_land(self):
        return self._needs.farm_land()

    @farm_land.setter
    def farm_land(self, value):
        self._needs.legacy_game().farm_land = value

    @property
    def farm_arable_ceiling(self):
        return self._needs.farm_arable_ceiling()

    @property
    def farm_ladder(self):
        return self._needs.farm_ladder()

    @property
    def farm_technique_this_year(self):
        return self._needs.farm_technique_this_year()

    @farm_technique_this_year.setter
    def farm_technique_this_year(self, value):
        self._needs.legacy_game()._farm_technique_this_year = value

    # ---- the actors and the hours still wanted ----

    def actor_staff_fte(self, trade):
        return self._needs.actor_staff[trade]

    def actors_staff_nationwide(self, trade):
        return self._needs.actor_staff_nationwide[trade]

    def actor_staff_total(self):
        return self._needs.actor_staff_total()

    def teaching_knowledge(self):
        """(nodes held by each active actor, what the society already knows, what has been demonstrated)."""
        return self._needs.teaching_knowledge()

    def director_overhead_hours(self):
        return self._needs.director_overhead_hours()

    def active_hours_still_wanted(self):
        return self._needs.active_hours_still_wanted()

    def shared_answer(self, key, inputs, compute, standalone=False):
        return self._needs.shared_answer(key, inputs, compute, standalone)

    def stopped_yearly_value(self, node_ids):
        return self._needs.concern_rows_stopped(node_ids)

    def staff_closure_age(self, node_id):
        return self._needs.staff_closure_age[node_id]

    def staffing_draw_of(self, node_id, foreman_units=None):
        return self._needs.staffing_draw(node_id, foreman_units)

    def staffing_held_totals(self):
        return self._needs.staffing_held_totals()

    def staffing_shortfalls(self, totals, strict=False):
        return self._needs.staffing_shortfalls(totals, strict)

    def concerns_to_close_for_staffing(self):
        return self._needs.concerns_to_close_for_staffing()

    def venture_foreman(self, node_id):
        return self._needs.venture_foreman[node_id]

    def venture_foremen_used(self, excluding=None):
        return self._needs.venture_foremen_used(excluding)

    def venture_staff_free(self):
        return self._needs.venture_staff_free()


class AgentEconomyReads:
    """The agent economy's answers labour asks for, each a view of the module's needs."""

    def __init__(self, needs):
        self._needs = needs

    def agent_people_by_trade(self):
        return self._needs.agent_people_by_trade()

    def agent_people_by_tile_and_trade(self):
        return self._needs.agent_people_by_tile_and_trade()

    def agent_wage_per_hour(self, trade):
        return self._needs.agent_wage[trade]

    def agent_country(self, country):
        return self._needs.agent_country[country]

    def agent_prices(self):
        return self._needs.agent_prices()
