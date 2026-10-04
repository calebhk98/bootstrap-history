"""The one labour market every employer asks.

An employer (the founder's household, a firm, the state, an interest group)
holds no wage arithmetic. It asks this market what an hour of a trade costs,
hires through it, and releases through it. The wage formula, the scarcity
premium and the record of recent hiring pressure live here and nowhere else;
tests/test_one_labour_market.py fails when wage arithmetic appears elsewhere.

The market reads the opening schedule (labour_wages.py: subsistence floor,
training premium, tightness), the cost-of-living factors, the economy's price
and wage indices, and the local supply a trade has (labour_population.py).
The pressure record is stored on the household state so a save carries it.
"""
import math

from sim.constants import declare

from . import trade_data
from .market.clearing import (FIRM_LABOUR_SUPPLY_ELASTICITY, MATCHING_EFFICIENCY_PER_YEAR,
                              MATCHING_SEARCHER_ELASTICITY)


class LabourMarket:
    """Quote, hire, release and read the pressure of one economy's labour."""

    LABOUR_PRESSURE_DECAY_RATE = declare(
        "LABOUR_PRESSURE_DECAY_RATE", 0.6, kind="temporary_heuristic",
        unit="fraction of remembered pressure surviving per year",
        source=None, confidence="D",
        why="How fast a burst of recent hiring or commissioning stops "
            "moving the price of a trade - the same rate this file's own "
            "comment says market_pressure decays at for slaves (0.55, "
            "'near enough'), reused for labour rather than fitted "
            "independently. Mostly gone in three years; a real figure "
            "would come from how fast a local labour market actually "
            "recovers from a demand shock, which nothing here measures.")
    LABOUR_PRESSURE_SHARE_CAP = declare(
        "LABOUR_PRESSURE_SHARE_CAP", 1.5, kind="temporary_heuristic",
        unit="dimensionless (pressure / market_supply)",
        source=None, confidence="D",
        why="Caps how much of the price-pressure curve a single burst of "
            "hiring can reach, so leaning on a trade harder and harder does "
            "not send its price to infinity. The curve shape (saturating, "
            "not linear) is a real claim about markets; where exactly it "
            "saturates is tuned.")
    LABOUR_PRICE_PRESSURE_COEFFICIENT = declare(
        "LABOUR_PRICE_PRESSURE_COEFFICIENT", 0.9, kind="temporary_heuristic",
        unit="dimensionless", source=None, confidence="D",
        why="How much a fully-leaned-on trade's price roughly doubles by: "
            "at share=1.0 this term alone adds 0.9 to the multiplier. "
            "material_price_factor uses the identical curve for the same "
            "reason; the coefficient itself is tuned to feel like a real but "
            "survivable premium, not fitted to an observed labour-market "
            "price response.")

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

    # ---- pressure: what recent hiring has done to a trade's local price ----

    def _records(self):
        return self._world.state.household.labour_pressure_records

    def standing_draw(self, trade):
        """Hours a year of this trade that standing staff already take out of its pool: trades drawn
        from the unskilled pool stay drawn while they serve, so they do not decay."""
        world = self._world
        if trade != trade_data.fallback_trade(self._labour.wage_schedule().training_years, world.trade_family):
            return 0.0
        drawn = [name for name in world.wages if trade_data.drawn_from_unskilled_pool(name)]
        return sum(world.actor_staff_fte(name) for name in drawn) * world.HOURS_PER_PERSON_YEAR

    def recent_pressure(self, trade):
        """Hours a year of this trade recently leaned on, decayed to this year."""
        record = self._records().get(trade)
        if not record:
            return 0.0
        hours, year = record
        age = max(0.0, self._world.state.scenario.year - year)
        return hours * (self.LABOUR_PRESSURE_DECAY_RATE ** age)

    def pressure(self, trade):
        """Recent pressure plus what the standing army takes from the unskilled pool."""
        return self.recent_pressure(trade) + self.standing_draw(trade)

    def pressured_trades(self):
        """Trades anyone has leaned on, in a stable order."""
        return sorted(self._records())

    def press(self, trade, hours):
        """Record demand for `hours` a year of a trade that is not a hire (teaching pulls a trade's
        people off their bench, a commission buys their time)."""
        self._records()[trade] = (self.recent_pressure(trade) + max(0.0, hours), self._world.state.scenario.year)

    def clear_pressure(self):
        self._records().clear()

    def _price_factor_from(self, pressure, supply):
        supply = max(1.0, supply)
        share = min(self.LABOUR_PRESSURE_SHARE_CAP, pressure / supply)
        return 1.0 + self.LABOUR_PRICE_PRESSURE_COEFFICIENT * share * share

    def price_factor(self, trade):
        """What hiring MORE of this trade costs beyond the wage table, from how hard it has recently
        been leaned on against the people the local market has of it."""
        return self._price_factor_from(self.pressure(trade), self._labour.market_supply(trade))

    def price_factor_after(self, trade, people):
        """The price factor the instant `people` more are on the books: the hire being weighed, not
        the market as it stands. Adds them to the household's headcount of the trade to read the
        supply they widen, then takes them off again."""
        people = max(0.0, people)
        if people <= 0:
            return self.price_factor(trade)
        household = self._world.state.household
        before = household.employees.get(trade, 0.0)
        household.employees[trade] = before + people
        try:
            supply_after = self._labour.market_supply(trade)
        finally:
            if before:
                household.employees[trade] = before
            else:
                household.employees.pop(trade, None)
        pressure_after = self.pressure(trade) + people * self._world.HOURS_PER_PERSON_YEAR
        return self._price_factor_from(pressure_after, supply_after)

    # ---- the wage ----

    def cost_factors(self, trade):
        """The food, housing and tool multipliers behind a trade's wage, for a screen to show."""
        return self._labour.wage_cost_factors(trade)

    def pay_scale(self):
        """What an hour pays against the opening schedule, at this economy's output per hour."""
        return self._world.real_output_per_head() ** self._labour.LABOUR_PAY_SHARE_OF_OUTPUT_GAIN

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
                + max(0.0, world.state.household.worker_housing_places or 0.0))

    def town_workers(self):
        """People every employer in the town has on its books: the founder's household and every
        firm and government."""
        return self._labour.headcount() + self._world.actor_staff_total()

    def town_housing_factor(self):
        """The housing multiplier on a wage. It reads how full the town's housing is from everyone
        employed in it, so it is the same for every employer hiring there."""
        occupancy = self.town_workers() / max(1.0, self.town_housing_room())
        pressure = (occupancy - self._labour.HOUSING_PRESSURE_START_OCCUPANCY) / self._labour.HOUSING_PRESSURE_BAND
        return 1.0 + self._labour.HOUSING_PRESSURE_MAX_MARKUP * max(0.0, min(1.0, pressure))

    def _annual(self, trade, scarcity):
        world = self._world
        wage = world.economy.agent_wage_per_hour(trade)
        if wage is not None:
            return wage * world.HOURS_PER_PERSON_YEAR * scarcity
        base = self._labour.base_annual_wage(trade)
        factors = self._labour.wage_cost_factors(trade)
        return (base * factors["weighted"] * world.price_index
                * world.wage_index * scarcity * self.pay_scale())

    def quote_annual(self, trade, people=0.0, employer=None, pay_premium=0.0):
        """Money one person-year of a trade costs `employer` now. `people` more taken on first move
        the local scarcity premium to what it will be once they are on the books (zero: as it
        stands). The rate does not depend on who asks; `employer` is accepted so a market that
        one day prices one buyer differently has the buyer to hand."""
        scarcity = self.price_factor_after(trade, people) if people else self.price_factor(trade)
        return self._annual(trade, scarcity) * (1.0 + pay_premium)

    def unscarce_annual(self, trade):
        """One person-year of a trade before the local scarcity premium (a screen's 'wage table' figure)."""
        return self._annual(trade, 1.0)

    def quote(self, trade, hours=0.0, employer=None, pay_premium=0.0):
        """Money one hour of a trade costs `employer` now, once `hours` a year more are taken on;
        `pay_premium` is the fraction the employer pays over the market."""
        world = self._world
        people = hours / world.HOURS_PER_PERSON_YEAR
        return self.quote_annual(trade, people, employer, pay_premium) / world.HOURS_PER_PERSON_YEAR

    def recruitable(self, trade, people, pay_premium=0.0):
        """How many of `people` an employer can expect to find this year in the local market: the
        matching form of the market core, with searchers the local hours not already taken."""
        people = max(0.0, people)
        if people <= 0.0:
            return 0.0
        searchers = max(0.0, self._labour.market_supply(trade) - self.pressure(trade))
        vacancies = people * self._world.HOURS_PER_PERSON_YEAR
        rate = (MATCHING_EFFICIENCY_PER_YEAR * (1.0 + pay_premium) ** FIRM_LABOUR_SUPPLY_ELASTICITY
                * (searchers / vacancies) ** MATCHING_SEARCHER_ELASTICITY)
        return min(people, people * (1.0 - math.exp(-rate)))

    def hire_cost(self, trade, people):
        """The finder's fee for taking on `people` of a trade: the first year's wage at the table
        rate times the premium as the market stands, which is what payroll charges once they are in."""
        return people * self.unscarce_annual(trade) * self.price_factor(trade)

    def commission_cost(self, trade, hours, premium):
        """What a one-off job of `hours` costs: the hour the market quotes, times a shop's `premium`."""
        return hours * premium * self.quote(trade)

    def in_current_money(self, schedule_amount):
        """An amount at the opening schedule's prices, in today's money."""
        world = self._world
        return schedule_amount * world.wage_index * world.price_index

    def hire(self, employer, trade, hours, pay_premium=0.0):
        """Take on `hours` a year of a trade. Returns the rate an hour cost (premium included), and
        records the pressure; a better payer draws from rivals rather than idle hands, so its
        premium scales the pressure down."""
        rate = self.quote(trade, 0.0, employer, pay_premium)
        if pay_premium > 0.0:
            hours = hours / (1.0 + pay_premium) ** FIRM_LABOUR_SUPPLY_ELASTICITY
        self.press(trade, hours)
        return rate

    def release(self, employer, trade, hours):
        """Give back `hours` a year of a trade: the pressure they put on its price eases."""
        record = self._records().get(trade)
        if not record:
            return
        remaining = max(0.0, self.recent_pressure(trade) - max(0.0, hours))
        self._records()[trade] = (remaining, self._world.state.scenario.year)
