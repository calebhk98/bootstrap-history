"""What the labour package reads of the game, grouped by the module that owns the view: one reader class per group, each a plain
class holding the module's `needs`. `WorkforceWorld` (world.py) holds one of each."""
from sim.demography.api import rules as demography_rules
from sim.prices.api import solve_prices_core

from .commands import BuildHousing
from .provided import last_answer, overhead_hours


class ScenarioReads:
    """The scenario and the tree: configuration, civilisation, nodes, the goal and what it needs, what has been built."""

    def __init__(self, needs):
        self._needs = needs

    @property
    def cfg(self):
        return self._needs.game_config()

    @property
    def civ(self):
        return self._needs.civilisation()

    @property
    def nodes(self):
        return self._needs.tree_nodes()

    @property
    def order(self):
        return self._needs.project_order()

    @property
    def goal(self):
        return self._needs.goal()["node"]

    @property
    def goal_closure(self):
        """What the goal needs, once worked out (None before)."""
        return self._needs.goal_closure()

    def closure(self, nodes, goal):
        return self._needs.tree_closure(goal)

    def built_ways(self):
        """The roads, track, canals, bridges and ports built, {edge key: {way: true}} (the record itself)."""
        return self._needs.built_ways()

    @property
    def farm_land(self):
        return self._needs.farm_land()


class KnowledgeReads:
    """What the acting seat knows and what the knowledge module says of it: techniques, effects, mechanics, the sources of staff and room."""

    def __init__(self, needs):
        self._needs = needs

    def has(self, node_id):
        return node_id in self._needs.techniques_held()

    def held_and_running(self, include_starting=True):
        return self._needs.held_techniques(include_starting)

    def is_visible(self, node_id, _memo=None):
        return self._needs.visibility(node_id, _memo)

    def is_venture(self, node_id):
        return self._needs.is_venture[node_id]

    def running(self, node_id):
        return self._needs.running[node_id]

    def institution_units(self, node_id):
        return self._needs.institution_units[node_id]

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

    def teaching_knowledge(self):
        """(nodes held by each active actor, what the society already knows, what has been demonstrated)."""
        return self._needs.teaching_knowledge()


class FinanceReads:
    """Money, prices and what the acting seat can pay."""

    def __init__(self, needs):
        self._needs = needs

    @property
    def balance(self):
        """The acting seat's purse, now."""
        return self._needs.acting_balance()

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

    def housing_price_per_place(self):
        return self._needs.housing_price_per_place()

    def trade_school_price_per_seat(self):
        return self._needs.trade_school_price_per_seat()

    def build_worker_housing(self, places):
        return self._needs.send(BuildHousing(places))


class PeopleReads:
    """The nation's people and places, from the demography module and the town providers."""

    def __init__(self, needs):
        self._needs = needs

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

    def provided_town_population(self, tile, nominal_people):
        """People the town providers say live at `tile`, or None when none has an opinion (the last answer wins)."""
        return last_answer(self._needs.town_population(tile, nominal_people))

    def has_town_premiums(self):
        return self._needs.town_mortality_premium.has_providers

    def provided_mortality_premium(self, tile, town_people):
        """The premium the premium providers give for the town at `tile` (never negative), or None."""
        return last_answer(self._needs.town_mortality_premium(tile, town_people))


class TradeReads:
    """The trade tables and the wage schedule."""

    def __init__(self, needs, parts):
        self._needs = needs
        self._parts = parts
        self._trade_registry = None

    @property
    def wages(self):
        return self._parts.fact_views.starting_wages()

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

    def build_wage_schedule(self, civ):
        return self._parts.fact_views.wage_schedule_for(civ)

    def techniques_available_to(self, production, reached_nodes):
        return solve_prices_core.techniques_available_to(production, reached_nodes)

    @property
    def wage_index(self):
        return self._parts.fact_views.opening_wage_index()

    @property
    def HOURS_PER_PERSON_YEAR(self):
        return self._parts.views.hours_per_person_year()


class ActorReads:
    """The other actors' staff and the hours still wanted of the acting seat's people."""

    def __init__(self, needs):
        self._needs = needs

    def actor_staff_fte(self, trade):
        return self._needs.actor_staff[trade]

    def actors_staff_nationwide(self, trade):
        return self._needs.actor_staff_nationwide[trade]

    def actor_staff_total(self):
        return self._needs.actor_staff_total()

    def director_overhead_hours(self):
        """Hours of the directed-hours pool the game's overhead providers charge (none unless a mod provided some)."""
        return overhead_hours(self._needs.director_overhead())

    def active_hours_still_wanted(self):
        return self._needs.active_hours_still_wanted()

    def shared_answer(self, key, inputs, compute, standalone=False):
        return self._needs.shared_answer(key, inputs, compute, standalone)

    def stopped_yearly_value(self, node_ids):
        rows = self._needs.concern_market()
        return sum(rows.get(node_id, 0.0) for node_id in node_ids)

    def keep_staffed_hires(self):
        return self._needs.keep_staffed_hires()

    def concerns_to_close_for_staffing(self):
        return self._needs.concerns_to_close_for_staffing()

    def venture_foreman(self, node_id):
        return self._needs.venture_foreman[node_id]

    def venture_foremen_used(self, excluding=None):
        return self._needs.venture_foremen_used(excluding)

    def venture_staff_free(self):
        return self._needs.venture_staff_free()
