"""The one labour market every employer asks.

An employer (the founder's household, a firm, the state, an interest group)
holds no wage arithmetic. It asks this market what an hour of a trade costs,
hires through the labour core (sim/markets/port_staff.py). The wage is the economy's
wage for the trade (labour_wages.py reads it; before the economy opens, the opening schedule with
the cost-of-living factors and the price and wage indices, which only the opening needs).
"""
from sim.constants import declare

from . import trade_data, wage_provider
from .wage_factors import annual_wage, housing_factor, tools_factor, weighted_factor


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

    def __init__(self, world, schedule, settlement, book):
        self._world = world
        self.schedule = schedule
        self.settlement = settlement
        self.book = book

    # ---- the wage ----

    HOUSING_PRESSURE_START_OCCUPANCY = declare(
        "HOUSING_PRESSURE_START_OCCUPANCY", 0.75, kind="temporary_heuristic",
        unit="fraction of supervision_room occupied", source=None,
        confidence="D",
        why="Housing pressure on wages begins only once this share of the "
            "household's real places are occupied - a household with room "
            "to spare pays no housing premium at all. Tuned threshold, not "
            "measured from any real housing-market crowding curve.")
    HOUSING_PRESSURE_BAND = declare(
        "HOUSING_PRESSURE_BAND", 0.25, kind="temporary_heuristic",
        unit="fraction of supervision_room", source=None, confidence="D",
        why="How much further occupancy has to rise, past "
            "HOUSING_PRESSURE_START_OCCUPANCY, before the housing premium "
            "reaches its full HOUSING_PRESSURE_MAX_MARKUP - i.e. it is "
            "fully saturated at 1.0 (completely full). Tuned, not "
            "measured.")
    HOUSING_PRESSURE_MAX_MARKUP = declare(
        "HOUSING_PRESSURE_MAX_MARKUP", 0.4, kind="temporary_heuristic",
        unit="fraction added to the housing cost factor", source=None,
        confidence="D",
        why="The most a fully-crowded household's housing cost factor can "
            "rise by. Tuned game balance, not a measured rent response to "
            "crowding.")
    WAGE_SHARE_FOOD = declare(
        "WAGE_SHARE_FOOD", 0.45, kind="temporary_heuristic",
        unit="fraction of the wage-cost weighting", source=None,
        confidence="D",
        why="Subsistence food's assumed share of what a wage has to cover, "
            "used to blend the endogenous food/housing/tool price factors "
            "with the flat skill/difficulty premium into one multiplier on "
            "the historical wage table. The four shares (this, WAGE_SHARE_"
            "HOUSING, WAGE_SHARE_TOOLS, WAGE_SHARE_SKILL_DIFFICULTY) are "
            "tuned to sum to 1.0 and to leave the weighted factor at "
            "almost exactly 1.0 under neutral starting prices (see this "
            "function's own docstring); a real breakdown would need actual "
            "household-budget shares for a pre-modern worker, which this "
            "project does not have.")
    WAGE_SHARE_HOUSING = declare(
        "WAGE_SHARE_HOUSING", 0.20, kind="temporary_heuristic",
        unit="fraction of the wage-cost weighting", source=None,
        confidence="D", why="See WAGE_SHARE_FOOD.")
    WAGE_SHARE_TOOLS = declare(
        "WAGE_SHARE_TOOLS", 0.10, kind="temporary_heuristic",
        unit="fraction of the wage-cost weighting", source=None,
        confidence="D", why="See WAGE_SHARE_FOOD.")
    WAGE_SHARE_SKILL_AND_DIFFICULTY = declare(
        "WAGE_SHARE_SKILL_AND_DIFFICULTY", 0.25, kind="temporary_heuristic",
        unit="fraction of the wage-cost weighting", source=None,
        confidence="D",
        why="The fixed share of a wage that is skill, training, hazard and "
            "bargaining position - the part the historical wage table "
            "itself carries and that this endogenous model does not try "
            "to re-derive. See WAGE_SHARE_FOOD for the rest of the split.")

    def cost_factors(self, trade):
        """Endogenous food, housing and trade-tool multipliers for a wage.

        The labour-market schedule is the neutral benchmark; these factors
        scale it by how far live food, housing and tool prices have moved: the staple's and the tools'
        market ratio (price over the incumbents' cost) at the last year's close, the tools' also by the demand pressure.
        At neutral prices the weighted factor is 1.0 to within about a part
        in a million.

        It is not EXACTLY 1.0, and the difference is the model working. The
        tools term reads real market factors, and a society does not start
        with an empty market: Rome's 223 inherited technologies already burn
        charcoal, so charcoal opens the game carrying 5.0 t/yr of demand and
        prices a hair above neutral. The smith's wage carries that hair. This
        docstring claimed "exactly" for a long time, and the one check that
        would have caught it happened to sit behind a stray sys.exit in
        another test module and had never run.
        """
        food = self._world.last_market_price_ratio(wage_provider.staple_material(self._world.civ))
        housing = self.town_housing_factor()
        basket = trade_data.tool_basket(trade_data.registry_of(self._world), trade)
        tools = tools_factor(basket, self._world.material_price_factor, self._world.last_market_price_ratio)
        return {"food": food, "housing": housing, "tools": tools,
                "skill_and_difficulty": 1.0,
                "weighted": weighted_factor(self.WAGE_SHARE_FOOD, self.WAGE_SHARE_HOUSING, self.WAGE_SHARE_TOOLS,
                                            self.WAGE_SHARE_SKILL_AND_DIFFICULTY, food, housing, tools)}

    def pay_scale(self):
        """What an hour pays against the opening schedule, at this economy's output per hour."""
        return self._world.real_output_per_head() ** self.schedule.LABOUR_PAY_SHARE_OF_OUTPUT_GAIN

    def town_housing_room(self):
        """People the home town can house beyond those already there: the spare share of its
        dwellings plus the worker housing built in it."""
        world = self._world
        return (self.settlement.home_town_population_estimate() * self.TOWN_SPARE_HOUSING_SHARE
                + max(0.0, world.workforce.worker_housing_places or 0.0))

    def town_workers(self):
        """People every employer in the town has on its books: the founder's household and every
        firm and government."""
        return self.book.headcount() + self._world.actor_staff_total()

    def town_housing_factor(self):
        """The housing multiplier on a wage. It reads how full the town's housing is from everyone
        employed in it, so it is the same for every employer hiring there."""
        return housing_factor(self.town_workers(), self.town_housing_room(),
                              self.HOUSING_PRESSURE_START_OCCUPANCY, self.HOUSING_PRESSURE_BAND,
                              self.HOUSING_PRESSURE_MAX_MARKUP)

    def _annual(self, trade):
        """The economy's wage for the trade over a year. Only before the economy opens, the opening schedule's with the
        cost-of-living factors, the price index and the wage index."""
        world = self._world
        wage = world.economy.agent_wage_per_hour(trade)
        if wage is not None:
            return wage * world.HOURS_PER_PERSON_YEAR
        base = self.schedule.base_annual_wage(trade)
        factors = self.cost_factors(trade)
        return annual_wage(base, factors["weighted"], world.price_index, world.wage_index, 1.0, self.pay_scale())

    def quote_annual(self, trade):
        """Money one person-year of a trade costs now: the economy's wage for the trade, the same for every employer and
        every number taken on (a hire is a standing bid in the labour core, sim/markets/port_staff.py)."""
        return self._annual(trade)

    def quote_annual_in(self, trade, country):
        """Money one person-year of a trade costs in another country's labour markets, from the wages those
        markets set (the agent economy's labour areas of that country); None while the country is not part of
        the economy or its markets have no wage. The home country is `quote_annual`."""
        answers = self._world.economy.agent_country(country)
        return None if answers is None else answers.pay_per_person_year(trade)

    def unscarce_annual(self, trade):
        """One person-year of a trade at its wage, before any pay premium (a screen's 'wage table' figure)."""
        return self._annual(trade)

    def quote(self, trade):
        """Money one hour of a trade costs now: the one wage of the trade."""
        return self._annual(trade) / self._world.HOURS_PER_PERSON_YEAR

    def commission_cost(self, trade, hours):
        """What a one-off job of `hours` costs: the hour the market quotes."""
        return hours * self.quote(trade)
