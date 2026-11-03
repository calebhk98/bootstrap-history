"""The opening wage schedule priced at the present level, and the wage of an hour of a trade read from it."""
from typing import Optional
from sim.constants import declare


def person_year_hours(world):
    """The hours a person-year counts: the running economy's working year once it is open, else the scenario's."""
    hours = world.economy.agent_working_hours()
    return hours if hours is not None else world.trades.HOURS_PER_PERSON_YEAR


class WageScheduleReader:
    def __init__(self, world, settlement):
        self._world = world
        self._settlement = settlement
        self._wage_schedule_cache = None   # the opening's wage schedule, built on first use

    def opening_wage_schedule(self):
        """The civilisation's opening wage schedule, built once."""
        if self._wage_schedule_cache is None:
            self._wage_schedule_cache = self._world.trades.build_wage_schedule(self._world.scenario.civ)
        return self._wage_schedule_cache

    def wage_schedule(self):
        """The opening schedule priced at the present level: an hour of the unskilled trade is worth what the
        economy pays it, or before the economy has opened the opening's figure times the price level.
        Reading builds a priced copy and changes nothing."""
        opening = self.opening_wage_schedule()
        paid = self._world.economy.unskilled_wage()
        return opening.priced_at(paid if paid is not None
                                 else opening.money_per_labour_hour * self._world.finance.home_price_level())

    def money_per_labour_hour(self):
        """Money one hour of the unskilled numeraire trade is worth here."""
        return self.wage_schedule().money_per_labour_hour

    LABOUR_PAY_SHARE_OF_OUTPUT_GAIN = declare(
        "LABOUR_PAY_SHARE_OF_OUTPUT_GAIN", 0.0, kind="temporary_heuristic",
        unit="exponent on output_per_head (1 = pay rises as fast as output per hour)",
        source=None, confidence="D",
        why="How far pay per hour follows output per hour, for every employer alike (founder, "
            "firms, state, households). Zero: the economy's labour markets are the only wage "
            "mover. One is a labour market that pays an hour what it makes. Measured on Rome "
            "seeds 1-3: at one or one half the founder's early research and hiring grow dearer "
            "with the generic economy index and none of the three takes off in 100 years; at "
            "zero all three do (Complaint 354). Replace by the clearing of aggregate demand for "
            "hands against the working population, or by output per hour that comes from "
            "diffused technology (Complaint 101).")

    def wage_per_hour(self, trade) -> Optional[float]:
        """Money one hour of this trade is paid: the economy's wage under its one rule once the economy has opened (None
        when that rule gives the trade none), and before it opens the opening schedule's (training premium times the
        money value of an unskilled hour)."""
        if self._world.economy.agent_working_hours() is not None:
            return self._world.economy.agent_wage_at(trade, self._settlement.base_tile())
        return self.wage_schedule().wage_per_hour(trade)

    def base_annual_wage(self, trade) -> Optional[float]:
        """A year of the trade at `wage_per_hour`; None when that is."""
        wage = self.wage_per_hour(trade)
        return None if wage is None else wage * person_year_hours(self._world)
