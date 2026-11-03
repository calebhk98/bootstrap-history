"""What staff cost every year and what it costs to be one: the founder's own hours sold at the market wage, the
books on them, and the standing job.

work_for_wages and wage_bill are the two directions of the same trade: a founder offering their own hours at
the going rate, and a household paying its standing staff that same rate every year. Both are settled by the
year's clearing (sim/markets/port_staff.py) at the one wage of the trade, which the labour market quotes."""
from sim.reporting.api import RecordEvent
from sim.refusal import Refusal
from .labour_wage_schedule import person_year_hours
from .founder_hours import hours_free
from .labour_refusals import economy_lacks, economy_lacks_refusal
from .hours_sale_warning import sale_at_a_loss_note, starving_warning
from .staff_moves import (FOUNDER_DEAD, HOURS_NOT_POSITIVE, HOURS_SHORT, NO_SUCH_TRADE, TRADE_ABSENT,
                          wage_work_blocker)
from .staff_pay_rules import wage_bill_of, wage_for_hours_of


class Wages:
    def __init__(self, world, book, hours, market, trades):
        self._world = world
        self.book = book
        self.hours = hours
        self.market = market
        self.trades = trades

    def wage_for_hours(self, trade, hours):
        """What `hours` of the founder's own work pay now at the trade's market wage, the one wage every employer pays. The
        figure work_for_wages expects and every quote of that pay (the stall banner, the year's wage-work rule) reads."""
        return wage_for_hours_of(self.market.quote_annual(trade), person_year_hours(self._world), hours)

    def best_wage_trade(self):
        """The trade open to the founder that pays most an hour, or None when none is open."""
        trades = [trade for trade in self._world.trades.wages if self.trades.trade_available(trade)]
        return max(trades, key=lambda trade: self.wage_for_hours(trade, 1.0), default=None)

    def work_for_wages(self, trade, hours, commit=True):
        """Do a job. For money. Like everybody else.

        It is a fair gap otherwise: you could hire a smith, a glassblower
        or a farmer all day long and had no way to BE one. A founder with
        no capital and a useful pair of hands should be able to earn
        a wage, and at the start it is one of the few things he can do.

        The hours are offered in the labour core with the households' own (sim/markets/port_staff.py) and paid
        what the year's clearing hires of them, at the one market wage of the trade, the same the game charges you when
        you hire someone, so there is no arbitrage in either direction. The pay returned is the quote, not money in
        hand. The cost is your own hours, which are the one resource nothing else can buy: hours offered here are
        hours the standing job (`standing_job_pay`, below) does not sell and your own projects cannot have.

        With `commit` False it is a quote: the pay and the note as the sale would leave them, with no offer, log line
        or book kept (the hours count against the year only while the note is worked out).
        """
        blocker = wage_work_blocker(
            self._world.standing.founder_alive, trade in self._world.trades.wages,
            lambda: self.trades.trade_available(trade), hours,
            lambda: self.hours.director_pool() - self.hours.director_hours_committed())
        # The trade gate is trade_available(), the test `hire` uses: work needs a customer, so a trade nobody here practises is refused.
        if blocker == FOUNDER_DEAD:
            return 0.0, Refusal("founder_dead", "there is nobody left to do the work: these are YOUR "
                                "hours, and the founder is dead. What you built goes "
                                "on; you do not.")
        if blocker == NO_SUCH_TRADE:
            here = sorted(candidate_trade for candidate_trade in self._world.trades.wages if self.trades.trade_available(candidate_trade))
            return 0.0, Refusal("no_such_trade", "no such trade. you could work as: " + ", ".join(here), choices=here)
        if blocker == TRADE_ABSENT:
            return 0.0, Refusal("trade_absent", "nobody here will pay you to be a %s: the trade does "
                                "not exist in this society, so there is no employer "
                                "for it. Teach it first with train, or work at "
                                "something they do recognise." % trade)
        if economy_lacks(self._world, trade):
            return 0.0, economy_lacks_refusal(trade)
        hours = float(hours)
        if blocker == HOURS_NOT_POSITIVE:
            return 0.0, Refusal("hours_not_positive", "hours must be greater than zero")
        # Hours already committed to teaching count against the pool as well as hours sold for wages.
        if blocker == HOURS_SHORT:
            left = self.hours.director_pool() - self.hours.director_hours_committed()
            return 0.0, Refusal("hours_short", "you have %.0f of your own hours left this year, not %.0f"
                                % (max(0.0, left), hours), hours_left=max(0.0, left))
        # Your own hour is worth the labour-market quote for the trade, the rate it costs to employ someone in it.
        workforce = self._world.workforce
        pay = self.wage_for_hours(trade, hours)
        revenue_before = self._world.finance.revenue()
        offered = workforce.hours_offered_for_wages
        offered_before = offered.get(trade)
        offered[trade] = (offered_before or 0.0) + hours
        try:
            message = self._sale_note(pay, revenue_before, commit, trade, hours)
        finally:
            if not commit:     # a quote is the sale tried and put back
                if offered_before is None:
                    offered.pop(trade, None)
                else:
                    offered[trade] = offered_before
        return pay, message

    def _sale_note(self, pay, revenue_before, commit, trade, hours):
        """The warning about the sale just made (or quoted): hours that starve a project, or a trade that pays less than the standing job."""
        # a sale that would starve an active project of the hours it still wants is warned about, never refused (selling hours can pay a debt)
        _wanted = self._world.actors.active_hours_still_wanted()
        _starve = None
        if _wanted:
            _starve = starving_warning(_wanted, max(0.0, self.hours.director_pool() - self.hours.director_hours_committed()))
        if commit:
            self.log_wage_work(trade, hours, pay)
        # hours sold here are hours the standing job does not sell; the note says when that loses money
        message = sale_at_a_loss_note(pay, revenue_before - self._world.finance.revenue(),
                                      lambda amount: self._world.game.money_text(amount, grouped=True))
        if message:
            return message + (" Also: " + _starve if _starve else "")
        return _starve

    def wage_bill(self):
        """What your standing staff costs you every year, by trade.

        A machinist is not paid a labourer's wage and cannot be had at one. This
        is the other half of differentiating the trades: the expensive trades are
        expensive to keep, so a large staff of the people you actually need is a
        real commitment rather than a number that drifts upward on its own.

        The rate is the economy's wage for the trade, the same for every employer. The labour core pays it in
        the year's clearing (sim/markets/port_staff.py); this figure is what the staff the core hired will cost.
        """
        return wage_bill_of(self.book.employed_by_trade(), self.market.quote_annual)

    def wage_work_this_year(self):
        """Hours offered on request so far this year (the pay comes with the year's clearing)."""
        workforce = self._world.workforce
        if workforce.wage_hours_this_year <= 0:
            return {}
        return {"hours": round(workforce.wage_hours_this_year, 1)}

    def close_wage_year(self):
        """Keep the year's wage-work books as last year's; the offers stay until the clearing pays and spends them (`clearing_settled`)."""
        workforce = self._world.workforce
        summary = self.wage_work_this_year()
        if summary:
            summary["year"] = self._world.game.year
            summary["wage_income"] = 0.0
        workforce.wage_work_last_year = summary or None

    def log_wage_work(self, trade, hours, pay):
        """One log line saying what the offer should earn at the market wage."""
        self._world.send(RecordEvent.of("wage_work_sold", "wage work: offered %s hours as a %s, about %s at this year's clearing"
                    % (self._world.game.plain_number(hours), trade, self._world.game.money_text(pay, grouped=True, short=True)), trade=trade, hours=hours, pay=pay))

    def work_for_wages_dry_run(self, trade, hours):
        """(pay, message) for work_for_wages as a quote: nothing is posted, logged or kept."""
        return self.work_for_wages(trade, hours, commit=False)

    def hours_for_sale(self, counting_offers=True):
        """Hours of the year the household has not spoken for (teaching, moving, supervising its own
        businesses, hours already sold on request); none once the founder is dead. TEMPORARY HEURISTIC:
        hours put into the household's own projects are not taken out (they are worked alongside the job)
        until a project's hours are the hours of a seat. With `counting_offers` False the hours offered for wages this year are
        not taken out: the standing job in an ordinary year."""
        if not self._world.standing.founder_alive:
            return 0.0
        return hours_free(self.hours.director_pool(), self.hours.director_hours_committed(counting_offers))

    def standing_job_pay(self, trade, counting_offers=True):
        """A year of the unspoken-for hours sold in `trade` at its market wage; nothing without a trade."""
        if trade is None:
            return 0.0
        return self.wage_for_hours(trade, self.hours_for_sale(counting_offers))

    def wage_signature(self):
        """What moves a trade's market wage, for callers that cache a figure derived from `standing_job_pay`: the year and
        every trade's quoted wage now (the wage changes at the year's clearing and before the economy opens, not only with the year)."""
        return (self._world.game.year, tuple(self.market.quote_annual(trade) for trade in sorted(self._world.trades.wages)))
