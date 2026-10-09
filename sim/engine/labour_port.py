"""The engine's side of the labour wall: what the labour package reads from the simulation, and where
the simulation keeps its `Labour`."""
from sim.agents.api import edges
from sim.labour.api import Labour
from . import data, purchase_rule, solve_prices_core, wage_schedule


class LabourWorld:
    """What one simulation's labour reads from it: the state, the civilisation, the mechanics and
    prices around it, and the engine's trade tables. One explicit member per thing labour uses."""

    # the named edges labour's postings name as their counterparty
    EDGE_WORKERS = edges.EDGE_WORKERS
    EDGE_SLAVE_TRADERS = edges.EDGE_SLAVE_TRADERS
    EDGE_EMPLOYERS = edges.EDGE_EMPLOYERS

    def __init__(self, sim):
        self._sim = sim
        self._trade_registry = None

    def pay_edge(self, edge_name, amount, purpose):
        """The founder's household pays a named edge."""
        self._sim.pay_edge(edge_name, amount, purpose)

    def receive_from_edge(self, edge_name, amount, purpose):
        """A named edge pays the founder's household."""
        self._sim.receive_from_edge(edge_name, amount, purpose)

    @property
    def wages(self):
        return data.WAGES

    @property
    def trades_absent(self):
        return data.TRADES_ABSENT

    @property
    def trade_notes(self):
        return data.TRADE_NOTES

    def techniques_available_to(self, production, reached_nodes):
        return solve_prices_core.techniques_available_to(production, reached_nodes)

    @property
    def trade_registry(self):
        """Each trade's fields as plain mappings: the named ones and everything else its file states."""
        if self._trade_registry is None:
            self._trade_registry = {trade_id: {"family": trade.family, "training_years": trade.training_years,
                                               **trade.extra}
                                    for trade_id, trade in data.TRADE_REGISTRY.items()}
        return self._trade_registry

    def trade_family(self, trade):
        return data.trade_family(trade)

    def closure(self, nodes, goal):
        return data.closure(nodes, goal)

    def can_pay(self, cost):
        return purchase_rule.can_pay(self._sim, cost)

    def refusal_text(self, what, cost):
        return purchase_rule.refusal_text(self._sim, what, cost)

    def build_wage_schedule(self, civ, tightness_factors=None):
        return wage_schedule.build_schedule(data.TRADE_REGISTRY, civ, tightness_factors=tightness_factors)

    @property
    def HOURS_PER_PERSON_YEAR(self):
        return self._sim.HOURS_PER_PERSON_YEAR

    @property
    def LABOUR_PRODUCTIVITY_SOURCES(self):
        return self._sim.LABOUR_PRODUCTIVITY_SOURCES

    @property
    def ROOM_SOURCES(self):
        return self._sim.ROOM_SOURCES

    @property
    def STAFF_ATTRITION_RATE(self):
        return self._sim.STAFF_ATTRITION_RATE

    @property
    def STAFF_CAPACITY_SOURCES(self):
        return self._sim.STAFF_CAPACITY_SOURCES

    @property
    def STAFF_SOURCES(self):
        return self._sim.STAFF_SOURCES

    def active_hours_still_wanted(self):
        return self._sim.active_hours_still_wanted()

    def actor_staff_fte(self, trade):
        return self._sim.actor_staff_fte(trade)

    def actors_staff_nationwide(self, trade):
        return self._sim.actor_staff_nationwide(trade)

    def actor_staff_total(self):
        return self._sim.actor_staff_total()

    def adult_equivalent_population(self, population):
        return self._sim._adult_equivalent_population(population)

    def build_worker_housing(self, places):
        return self._sim.build_worker_housing(places)

    @property
    def cfg(self):
        return self._sim.cfg

    @property
    def civ(self):
        return self._sim.civ

    @property
    def economy(self):
        return self._sim.economy

    def effect_factor(self, channel, start=1.0, exponent=None):
        return self._sim.effect_factor(channel, start, exponent)

    def effect_holds(self, node_id, spec):
        return self._sim.effect_holds(node_id, spec)

    def effect_sum(self, channel, start=0.0):
        return self._sim.effect_sum(channel, start)

    def effect_terms(self, channel):
        return self._sim._effect_terms(channel)

    def effect_value(self, node_id, spec):
        return self._sim.effect_value(node_id, spec)

    def essential_price_ratio(self):
        return self._sim.essential_price_ratio()

    def exclusion_reason(self, node_id):
        return self._sim.exclusion_reason(node_id)

    @property
    def farm_arable_ceiling(self):
        return self._sim._farm_arable_ceiling

    @property
    def farm_ladder(self):
        return self._sim._farm_ladder

    @property
    def farm_land(self):
        return self._sim.farm_land

    @farm_land.setter
    def farm_land(self, value):
        self._sim.farm_land = value

    @property
    def farm_stock_kg(self):
        return self._sim.farm_stock_kg

    @property
    def farm_technique_this_year(self):
        return self._sim._farm_technique_this_year

    @farm_technique_this_year.setter
    def farm_technique_this_year(self, value):
        self._sim._farm_technique_this_year = value

    @property
    def goal(self):
        return self._sim.goal

    @property
    def goal_closure(self):
        return self._sim._goal_closure

    @goal_closure.setter
    def goal_closure(self, value):
        self._sim._goal_closure = value

    def has(self, node_id):
        return self._sim.has(node_id)

    def held_and_running(self, include_starting=True):
        return self._sim.held_and_running(include_starting)

    def home_price_level(self):
        return self._sim.home_price_level()

    @property
    def household(self):
        return self._sim.household

    def housing_price_per_place(self):
        return self._sim.housing_price_per_place()

    def institution_units(self, node_id):
        return self._sim.institution_units(node_id)

    def is_venture(self, node_id):
        return self._sim.is_venture(node_id)

    def is_visible(self, node_id, _memo=None):
        return self._sim.is_visible(node_id, _memo)

    def living_cost(self, _rev=None, _upkeep=None):
        return self._sim.living_cost(_rev, _upkeep)

    def market_price_ratio(self, material):
        return self._sim.market_price_ratio(material)

    def material_price_factor(self, emp_key):
        return self._sim.material_price_factor(emp_key)

    def mechanic(self, node_id, name):
        return self._sim.mechanic(node_id, name)

    @property
    def nodes(self):
        return self._sim.nodes

    def nodes_with_mechanic(self, name):
        return self._sim.nodes_with_mechanic(name)

    @property
    def order(self):
        return self._sim.order

    @property
    def pop_scale(self):
        return self._sim.pop_scale

    @property
    def population(self):
        return self._sim.population

    @property
    def price_index(self):
        return self._sim.price_index

    def real_output_per_head(self):
        return self._sim.real_output_per_head()

    def reopen_units(self, node_id):
        return self._sim.reopen_units(node_id)

    def rep_factor(self):
        return self._sim.rep_factor()

    def revenue(self):
        return self._sim.revenue()

    def revenue_capacity(self):
        return self._sim.revenue_capacity()

    @property
    def rng(self):
        return self._sim.rng

    def running(self, node_id):
        return self._sim.running(node_id)

    def shared_answer(self, key, inputs, compute):
        return self._sim._shared_answer(key, inputs, compute)

    def spending_power(self, kind='buy'):
        return self._sim.spending_power(kind)

    def staff_closure_age(self, node_id):
        return self._sim.staff_closure_age(node_id)

    def staff_hire_advice(self, kind, count=None):
        return self._sim.staff_hire_advice(kind, count)

    def staffing_draw_of(self, node_id, foreman_units=None):
        return self._sim._staffing_draw_of(node_id, foreman_units)

    def staffing_held_totals(self):
        return self._sim.staffing_held_totals()

    def staffing_shortfalls(self, totals, strict=False):
        return self._sim._staffing_shortfalls(totals, strict)

    def start_reason(self, node_id, ignore_trade=False, _memo=None, _why=True):
        return self._sim.start_reason(node_id, ignore_trade, _memo, _why)

    @property
    def state(self):
        return self._sim.state

    def trade_school_price_per_seat(self):
        return self._sim.trade_school_price_per_seat()

    def upkeep(self):
        return self._sim.upkeep()

    def venture_foreman(self, node_id):
        return self._sim.venture_foreman(node_id)

    def venture_foremen_used(self, excluding=None):
        return self._sim.venture_foremen_used(excluding)

    def venture_staff_free(self):
        return self._sim.venture_staff_free()

    @property
    def wage_index(self):
        return self._sim.wage_index

    @property
    def wage_index_base(self):
        return self._sim._wage_index_base


class LabourPortMixin:
    """Gives `Sim` its labour as `sim.labour`. Not saved: it holds only caches and is rebuilt on demand."""

    @property
    def labour(self):
        labour = self.__dict__.get("_labour")
        if labour is None:
            labour = self.__dict__["_labour"] = Labour(LabourWorld(self))
        return labour
