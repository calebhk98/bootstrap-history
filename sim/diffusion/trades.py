"""A trade the founder introduced becomes a trade the society has.

Once a taught trade has been established long enough, with schools actually running, the society naturalises it: it
produces its own people in that trade, bounded by the same literate capacity that bounds a founder training them by
hand. With no schooling this never fires: a founder who builds no school keeps the trade as a personal secret.

Needs: trade_spread, staff, literacy_capacity, schooling flow (its own)."""
from sim.reporting.api import RecordEvent
from sim.workforce.api import NoteTradeSpread, SetEmployed

from . import constants
from .trade_absorption import BECOME_ENDEMIC, GROW, RECORD_INTRODUCTION, absorption_step, absorption_years, headcount_toward_ceiling


class TradeAbsorption:

    def trade_absorption_years(self, flow: float) -> float:
        return absorption_years(flow, constants.TRADE_ABSORPTION_MIN_YEARS, constants.TRADE_ABSORPTION_BASE_YEARS)

    def advance_trade_absorption(self, year: int) -> None:
        spread = self.needs.trade_spread()
        for trade in spread["absent"]:
            if trade not in spread["created"]:
                continue          # never taught here; nothing to naturalise
            introduced = spread["introduced_year"].get(trade)
            flow = self.schooling_flow()
            step = absorption_step(introduced, trade in spread["endemic"], flow, year, self.trade_absorption_years)
            if step == RECORD_INTRODUCTION:
                # first year the trade is seen as taught; recorded now, not back-dated
                self.needs.send(NoteTradeSpread(trade, introduced_year=year))
            elif step == GROW:
                self.grow_endemic_trade(trade)
            elif step == BECOME_ENDEMIC:
                self.needs.send(NoteTradeSpread(trade, endemic=True))
                # in-world, not a change-log: a census fact the founder would observe
                self.needs.send(RecordEvent.of("trade_no_longer_only_yours", "%s is no longer only your trade: "
                                               "enough schooling has passed through enough "
                                               "hands that this society simply has its own "
                                               "%ss now, the way it always had smiths" % (trade, trade)))

    def grow_endemic_trade(self, trade: str) -> None:
        """Let a naturalised trade's own headcount drift toward the ceiling a founder hiring or teaching it by hand
        meets. Continuous, not whole-person rounded: staff here are full-time equivalents."""
        have = self.needs.staff()["employees"].get(trade, 0.0)
        grown = headcount_toward_ceiling(have, self.needs.literacy_capacity[trade], constants.TRADE_DIFFUSION_APPROACH_RATE)
        if grown == have:
            return
        self.needs.send(SetEmployed(trade, grown))
