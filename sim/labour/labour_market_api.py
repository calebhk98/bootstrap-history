"""The one labour market every employer asks.

An employer (the founder's household, a firm, the state, an interest group)
holds no wage arithmetic. It asks this market what an hour of a trade costs,
hires through it, and releases through it. The wage is the economy's
wage for the trade (labour_wages.py reads it; before the economy opens, the opening schedule with
the cost-of-living factors and the price and wage indices). The record of recent hiring pressure
lives here: it is read by the groups' wage rule only, and stored on the household state so a save carries it.
"""
from sim.constants import declare

from . import trade_data
from .wage_factors import annual_wage, housing_factor
from .market.clearing import FIRM_LABOUR_SUPPLY_ELASTICITY


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
        return self._world.workforce.labour_pressure_records

    def standing_draw(self, trade):
        """Hours a year of this trade that standing staff already take out of its pool: trades drawn
        from the unskilled pool stay drawn while they serve, so they do not decay."""
        world = self._world
        if trade != trade_data.fallback_trade_of(world, self._labour.wage_schedule().training_years):
            return 0.0
        drawn = [name for name in world.wages if trade_data.drawn_from_unskilled_pool(name)]
        return sum(world.actor_staff_fte(name) for name in drawn) * world.HOURS_PER_PERSON_YEAR

    def recent_pressure(self, trade):
        """Hours a year of this trade recently leaned on, decayed to this year."""
        record = self._records().get(trade)
        if not record:
            return 0.0
        hours, year = record
        age = max(0.0, self._world.year - year)
        return hours * (self.LABOUR_PRESSURE_DECAY_RATE ** age)

    def pressure(self, trade):
        """Recent pressure plus what the standing army takes from the unskilled pool."""
        return self.recent_pressure(trade) + self.standing_draw(trade)

    def pressure_signature(self):
        """A cheap fingerprint of the pressure on every trade, for callers that cache a figure which
        depends on the market's wages."""
        return tuple(sorted(self._records().items()))

    def pressured_trades(self):
        """Trades anyone has leaned on, in a stable order."""
        return sorted(self._records())

    def press(self, trade, hours):
        """Record demand for `hours` a year of a trade that is not a hire (teaching pulls a trade's
        people off their bench, a commission buys their time)."""
        self._records()[trade] = (self.recent_pressure(trade) + max(0.0, hours), self._world.year)

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
        self._records()[trade] = (remaining, self._world.year)
