"""The one labour market every employer asks.

An employer (the founder's household, a firm, the state, an interest group)
holds no wage arithmetic. It asks this market what an hour of a trade costs,
hires through the labour core (sim/markets/port_staff.py). The wage is the economy's
wage for the trade (labour_wages.py reads it; before the economy opens, the opening schedule with
the cost-of-living factors and the price and wage indices).
"""
from sim.constants import declare

from .wage_factors import annual_wage, housing_factor


class LabourMarket:
    """Quote one economy's labour: the wage is the economy's, the same for every employer."""

    TOWN_SPARE_HOUSING_SHARE = declare(
        "TOWN_SPARE_HOUSING_SHARE", 0.02, kind="temporary_heuristic",
        unit="fraction of the home town's people (dwellings open to hired hands)",
        source=None, confidence="D",
        why="How much housing a town has free for incoming hired labour, as a share of its own "
            "population; the housing term of a wage starts to bite when the people every employer "
            "has taken on fill this. Tuned so a town of tens of thousands absorbs its firms and a household's "
            "staff without a premium and a mass hiring by many employers does not; a real figure "
            "would come from a dwelling stock and its vacancy, which nothing here models.")

    def __init__(self, labour):
        self._labour = labour
        self._world = labour._world

    # ---- the wage ----

    def cost_factors(self, trade):
        """The food, housing and tool multipliers behind a trade's wage, for a screen to show."""
        return self._labour.wage_cost_factors(trade)

    def pay_scale(self):
        """What an hour pays against the opening schedule, at this economy's output per hour."""
        return self._world.real_output_per_head() ** self._labour.LABOUR_PAY_SHARE_OF_OUTPUT_GAIN

    def wage_index(self):
        """The scarcity-driven index every wage in this society is scaled by."""
        return self._world.wage_index

    def wage_index_change(self, index_before):
        """How far the wage index has moved from a reading taken earlier."""
        return self._world.wage_index - index_before

    def household_wage_ratio(self):
        """What an hour of the unskilled numeraire pays now against the opening, before the price level and
        the cost of living (the solver's prices carry those): the scarcity of hands against the working
        population, times the share of output gain pay passes on."""
        world = self._world
        return world.wage_index / world.wage_index_base * self.pay_scale()

    def town_housing_room(self):
        """People the home town can house beyond those already there: the spare share of its
        dwellings plus the worker housing built in it."""
        world = self._world
        return (self._labour.home_town_population_estimate() * self.TOWN_SPARE_HOUSING_SHARE
                + max(0.0, world.workforce.worker_housing_places or 0.0))

    def town_workers(self):
        """People every employer in the town has on its books: the founder's household and every
        firm and government."""
        return self._labour.headcount() + self._world.actor_staff_total()

    def town_housing_factor(self):
        """The housing multiplier on a wage. It reads how full the town's housing is from everyone
        employed in it, so it is the same for every employer hiring there."""
        return housing_factor(self.town_workers(), self.town_housing_room(),
                              self._labour.HOUSING_PRESSURE_START_OCCUPANCY, self._labour.HOUSING_PRESSURE_BAND,
                              self._labour.HOUSING_PRESSURE_MAX_MARKUP)

    def _annual(self, trade):
        """The economy's wage for the trade over a year; before the economy opens, the opening schedule's with the
        cost-of-living factors."""
        world = self._world
        wage = world.economy.agent_wage_per_hour(trade)
        if wage is not None:
            return wage * world.HOURS_PER_PERSON_YEAR
        base = self._labour.base_annual_wage(trade)
        factors = self._labour.wage_cost_factors(trade)
        return annual_wage(base, factors["weighted"], world.price_index, world.wage_index, 1.0, self.pay_scale())

    def quote_annual(self, trade, people=0.0, employer=None, pay_premium=0.0):
        """Money one person-year of a trade costs `employer` now: the economy's wage for the trade, the same for
        every employer and every number taken on (`people` and `employer` are accepted for callers that name them;
        a hire is a standing bid in the labour core, sim/markets/port_staff.py)."""
        return self._annual(trade) * (1.0 + pay_premium)

    def quote_annual_in(self, trade, country):
        """Money one person-year of a trade costs in another country's labour markets, from the wages those
        markets set (the agent economy's labour areas of that country); None while the country is not part of
        the economy or its markets have no wage. The home country is `quote_annual`."""
        answers = self._world.economy.agent_country(country)
        return None if answers is None else answers.pay_per_person_year(trade)

    def unscarce_annual(self, trade):
        """One person-year of a trade at its wage, before any pay premium (a screen's 'wage table' figure)."""
        return self._annual(trade)

    def quote(self, trade, hours=0.0, employer=None, pay_premium=0.0):
        """Money one hour of a trade costs `employer` now, once `hours` a year more are taken on;
        `pay_premium` is the fraction the employer pays over the market."""
        world = self._world
        people = hours / world.HOURS_PER_PERSON_YEAR
        return self.quote_annual(trade, people, employer, pay_premium) / world.HOURS_PER_PERSON_YEAR

    def commission_cost(self, trade, hours, premium):
        """What a one-off job of `hours` costs: the hour the market quotes, times a shop's `premium`."""
        return hours * premium * self.quote(trade)

    def in_current_money(self, schedule_amount):
        """An amount at the opening schedule's prices, in today's money."""
        world = self._world
        return schedule_amount * world.wage_index * world.price_index
