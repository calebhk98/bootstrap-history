"""What staff actually cost, every year, and what it costs to be one.

These are methods of Labour; they are a mixin only so that they can live in
a file of their own (see labour.py's own docstring for the split).

work_for_wages and wage_bill are the two directions of the same trade: a
founder selling their own hours at the going rate, and a household paying
its standing staff that same rate every year. Both ask the labour market (labour_market_api.py), which
starts from the labour-market schedule (wage_per_hour: subsistence floor,
training premium, tightness) and applies wage_cost_factors - the food,
housing and trade-tool multipliers (trade_data.tool_basket, HOUSING_PRESSURE_*,
WAGE_SHARE_*) that follow live market prices. Nothing here decides WHO can be hired or how many -
that is labour_population.py's market depth and labour_capacity.py's
household-room ceiling; this file only prices the trade once a person is
in it.
"""
from . import trade_data, wage_provider
from .wage_factors import tools_factor, weighted_factor
from .labour_market_api import LabourMarket
from .hours_sale_warning import sale_at_a_loss_note, starving_warning
from .labour_wage_ledger import WageLedgerMixin
from .staff_moves import (FOUNDER_DEAD, HOURS_NOT_POSITIVE, HOURS_SHORT, NO_SUCH_TRADE, TRADE_ABSENT,
                          wage_work_blocker)
from .staff_pay_rules import wage_bill_of, wage_for_hours_of
from sim.constants import declare


class WagesMixin(WageLedgerMixin):
    """What a trade costs to keep on staff, and what selling your own hours
    at that same rate earns - see this module's own docstring for why wage
    pricing is kept apart from who can be hired at all.
    """


    WAGE_REPUTATION_BONUS_CAP = declare(
        "WAGE_REPUTATION_BONUS_CAP", 0.5, kind="temporary_heuristic",
        unit="fraction of the trade rate", source=None, confidence="D",
        why="A well-known founder can earn up to half again the ordinary "
            "trade rate for their own hours of wage labour, capped so "
            "reputation cannot make wage labour arbitrarily lucrative. "
            "Tuned game balance, not a measured wage premium for fame.")
    WAGE_REPUTATION_SCALE = declare(
        "WAGE_REPUTATION_SCALE", 200.0, kind="temporary_heuristic",
        unit="reputation points per 100% of the bonus", source=None,
        confidence="D",
        why="How much reputation it takes to reach WAGE_REPUTATION_BONUS_"
            "CAP's own ceiling. Tuned to REPUTATION_EASE_SCALE's own order "
            "of magnitude (economy.py), not derived from anything.")

    @property
    def labour_market(self):
        """The one labour market every employer asks (labour_market_api.py)."""
        market = self.__dict__.get("_labour_market")
        if market is None:
            market = self.__dict__["_labour_market"] = LabourMarket(self)
        return market

    def wage_for_hours(self, trade, hours):
        """What `hours` of the founder's own work in `trade` pay now. The one answer work_for_wages
        pays and every quote of that pay (the stall banner, the year's wage-work rule) reads."""
        return wage_for_hours_of(self.labour_market.quote_annual(trade), self._world.HOURS_PER_PERSON_YEAR, hours,
                                 self._world.state.household.reputation, self.WAGE_REPUTATION_BONUS_CAP, self.WAGE_REPUTATION_SCALE)

    def best_wage_trade(self):
        """The trade open to the founder that pays most an hour, or None when none is open."""
        trades = [trade for trade in self._world.wages if self.trade_available(trade)]
        return max(trades, key=lambda trade: self.wage_for_hours(trade, 1.0), default=None)

    def work_for_wages(self, trade, hours):
        """Do a job. For money. Like everybody else.

        It is a fair gap otherwise: you could hire a smith, a glassblower
        or a farmer all day long and had no way to BE one. A founder with
        no capital and a useful pair of hands should be able to earn
        a wage, and at the start it is one of the few things he can do.

        It is paid at the ordinary rate for that trade, which is the same table
        the game charges you when you hire someone, so there is no arbitrage in
        either direction. The cost is your own hours, which are the one resource
        nothing else can buy: hours sold here are hours the standing job
        (labour_job.py) does not sell and your own projects cannot have.
        """
        blocker = wage_work_blocker(
            self._world.founder_alive, trade in self._world.wages,
            lambda: self.trade_available(trade), hours,
            lambda: self.director_pool() - self.director_hours_committed())
        # A TRADE NOBODY HERE PRACTISES IS A TRADE NOBODY HERE WILL PAY YOU FOR: the gate is trade_available(), the
        # same test `hire` uses. The founder really does know chemistry; what he lacks is a customer, until the
        # trade has been taught and trade_available() turns true.
        if blocker == FOUNDER_DEAD:
            return 0.0, ("there is nobody left to do the work: these are YOUR "
                         "hours, and the founder is dead. What you built goes "
                         "on; you do not.")
        if blocker == NO_SUCH_TRADE:
            here = sorted(candidate_trade for candidate_trade in self._world.wages if self.trade_available(candidate_trade))
            return 0.0, ("no such trade. you could work as: " + ", ".join(here))
        if blocker == TRADE_ABSENT:
            return 0.0, ("nobody here will pay you to be a %s: the trade does "
                         "not exist in this society, so there is no employer "
                         "for it. Teach it first with train, or work at "
                         "something they do recognise." % trade)
        hours = float(hours)
        if blocker == HOURS_NOT_POSITIVE:
            return 0.0, "hours must be greater than zero"
        # EVERY HOUR ALREADY SPOKEN FOR, not just the ones sold for wages: teaching counts as well as wage work.
        if blocker == HOURS_SHORT:
            left = self.director_pool() - self.director_hours_committed()
            return 0.0, ("you have %.0f of your own hours left this year, not %.0f"
                         % (max(0.0, left), hours))
        # Your own labour is worth the trade rate: the SAME rate the game
        # charges you to employ somebody in that trade, which is the point.
        # It has to be derived from the labour market quote, not a separate hourly
        # column, or the two disagree and the docstring's "no arbitrage in
        # either direction" claim becomes false.
        household = self._world.state.household
        pay = self.wage_for_hours(trade, hours)
        revenue_before = self._world.revenue()
        self._world.receive_from_edge(self._world.EDGE_EMPLOYERS, pay, "wages for your own work")
        household.wage_hours_this_year = household.wage_hours_this_year + hours
        household.wages_earned = (household.wages_earned or 0.0) + pay
        household.wage_income_this_year = household.wage_income_this_year + pay
        # DO NOT BLOCK IT - WARN ABOUT IT: selling hours is a legitimate
        # way to dig out of debt, so this must never refuse the sale, only
        # warn when it would starve an active project of the hours it
        # still wants this year. Computed from project_hour_pace/
        # active_hours_still_wanted (projects.py), the same formula step()
        # itself uses to hand out the pool, so this can never warn about a
        # shortfall step() would not also produce.
        _wanted = self._world.active_hours_still_wanted()
        _starve = None
        if _wanted:
            _starve = starving_warning(_wanted, max(0.0, self.director_pool() - self.director_hours_committed()))
        self.log_wage_work(trade, hours, pay)
        # SAY WHEN IT IS A BAD TRADE: hours sold here are hours the standing job does not sell, and when
        # that job pays more than this trade the sale loses money. The sale still happens.
        message = sale_at_a_loss_note(pay, revenue_before - self._world.revenue(),
                                      lambda amount: self._world.money_text(amount, grouped=True))
        if message:
            return pay, message + (" Also: " + _starve if _starve else "")
        return pay, _starve

    def wage_bill(self):
        """What your standing staff costs you every year, by trade.

        A machinist is not paid a labourer's wage and cannot be had at one. This
        is the other half of differentiating the trades: the expensive trades are
        expensive to keep, so a large staff of the people you actually need is a
        real commitment rather than a number that drifts upward on its own.

        Recently having leaned hard on a trade's local supply (labour market price_factor)
        shows up here too, not only in the fee `hire` charged to bring someone
        on: a town that just watched you take on half its smiths pays every
        smith more for a few years, yours included, until the pressure decays
        or the supply of smiths genuinely grows.
        """
        return wage_bill_of(self.employed_by_trade(), self.staff_pay)

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

    def wage_cost_factors(self, trade):
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
        housing = self.labour_market.town_housing_factor()
        basket = trade_data.tool_basket(trade_data.registry_of(self._world), trade)
        tools = tools_factor(basket, self._world.material_price_factor, self._world.last_market_price_ratio)
        return {"food": food, "housing": housing, "tools": tools,
                "skill_and_difficulty": 1.0,
                "weighted": weighted_factor(self.WAGE_SHARE_FOOD, self.WAGE_SHARE_HOUSING, self.WAGE_SHARE_TOOLS,
                                            self.WAGE_SHARE_SKILL_AND_DIFFICULTY, food, housing, tools)}

    def _opening_wage_schedule(self):
        """The wage schedule at the opening's price level; its tightness factors live in the economy
        state, so a save carries them."""
        factors = self._world.state.economy.wage_tightness_factors
        cached = getattr(self, "_wage_schedule_cache", None)
        if cached is None or cached.tightness_factors is not factors:
            cached = self._wage_schedule_cache = self._world.build_wage_schedule(
                self._world.civ, tightness_factors=factors)
            cached.opening_money_per_labour_hour = cached.money_per_labour_hour
        return cached

    def wage_schedule(self):
        """This household's labour-market wage schedule, in money at the present price level. An hour of
        the unskilled trade is worth what the economy pays it; before the economy has opened it is worth
        the opening's figure."""
        schedule = self._opening_wage_schedule()
        paid = self._world.economy_unskilled_wage()
        schedule.money_per_labour_hour = (paid if paid is not None
                                          else schedule.opening_money_per_labour_hour * self._world.home_price_level())
        return schedule

    def money_per_labour_hour(self):
        """Money one hour of the unskilled numeraire trade is worth here."""
        return self.wage_schedule().money_per_labour_hour

    LABOUR_PAY_SHARE_OF_OUTPUT_GAIN = declare(
        "LABOUR_PAY_SHARE_OF_OUTPUT_GAIN", 0.0, kind="temporary_heuristic",
        unit="exponent on output_per_head (1 = pay rises as fast as output per hour)",
        source=None, confidence="D",
        why="How far pay per hour follows output per hour, for every employer alike (founder, "
            "firms, state, households). Zero: the schedule's own clearing (tightness, which moves "
            "trades against each other but has no aggregate demand for hands) is the only wage "
            "mover. One is a labour market that pays an hour what it makes. Measured on Rome "
            "seeds 1-3: at one or one half the founder's early research and hiring grow dearer "
            "with the generic economy index and none of the three takes off in 100 years; at "
            "zero all three do (Complaint 354). Replace by the clearing of aggregate demand for "
            "hands against the working population, or by output per hour that comes from "
            "diffused technology (Complaint 101).")

    def wage_per_hour(self, trade):
        """The opening schedule's money for one hour of this trade, before price level, cost
        factors and scarcity. Employers do not read it; they ask the labour market."""
        return self.wage_schedule().wage_per_hour(trade)

    def base_annual_wage(self, trade):
        return self.wage_schedule().annual_wage(trade)

    def wage_document(self):
        """The wage vector in the shape the price solver reads."""
        return self.wage_schedule().document()

    def update_wages(self):
        """One year of wage adjustment toward the trades that are short."""
        hours = self._world.state.economy.society_labour_hours
        if not hours:
            return
        self.wage_schedule().step(self._hours_needed_for_wages(), hours)
