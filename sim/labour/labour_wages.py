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
from .labour_market_api import LabourMarket
from .labour_wage_ledger import WageLedgerMixin
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
        rate = self.labour_market.quote_annual(trade) / self._world.HOURS_PER_PERSON_YEAR
        reputation = self._world.state.household.reputation
        return hours * rate * (1.0 + min(self.WAGE_REPUTATION_BONUS_CAP, reputation / self.WAGE_REPUTATION_SCALE))

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
        nothing else can buy, so this is always a trade of time for money and
        usually a bad one once you have anything better to do. That is the
        honest shape of wage labour.
        """
        if not self._world.state.founder.founder_alive:
            return 0.0, ("there is nobody left to do the work: these are YOUR "
                         "hours, and the founder is dead. What you built goes "
                         "on; you do not.")
        if trade not in self._world.wages:
            here = sorted(candidate_trade for candidate_trade in self._world.wages if self.trade_available(candidate_trade))
            return 0.0, ("no such trade. you could work as: " + ", ".join(here))
        # A TRADE NOBODY HERE PRACTISES IS A TRADE NOBODY HERE WILL PAY YOU
        # FOR: this has to gate on trade_available(), the same test `hire`
        # uses, or a founder could earn wages in a trade the society does
        # not yet have any employer for.
        #
        # The founder really does know chemistry - that is the premise. What he
        # does not have is a customer. Wage labour is somebody else deciding
        # your work is worth money, and there is nobody here to decide that
        # until you have taught the trade, at which point trade_available()
        # turns true and this opens by itself.
        if not self.trade_available(trade):
            return 0.0, ("nobody here will pay you to be a %s: the trade does "
                         "not exist in this society, so there is no employer "
                         "for it. Teach it first with train, or work at "
                         "something they do recognise." % trade)
        hours = float(hours)
        if hours <= 0:
            return 0.0, "hours must be greater than zero"
        # EVERY HOUR ALREADY SPOKEN FOR, not just the ones sold for wages:
        # this must check against director_hours_committed(), which counts
        # teaching as well as wage work, or the two together can spend more
        # hours than exist in the year.
        left = self.director_pool() - self.director_hours_committed()
        if hours > left:
            return 0.0, ("you have %.0f of your own hours left this year, not %.0f"
                         % (max(0.0, left), hours))
        # Your own labour is worth the trade rate: the SAME rate the game
        # charges you to employ somebody in that trade, which is the point.
        # It has to be derived from the labour market quote, not a separate hourly
        # column, or the two disagree and the docstring's "no arbitrage in
        # either direction" claim becomes false.
        household = self._world.state.household
        pay = self.wage_for_hours(trade, hours)
        before_practice = self._world.revenue()
        self._world.receive_from_edge(self._world.EDGE_EMPLOYERS, pay, "wages for your own work")
        household.wage_hours_this_year = household.wage_hours_this_year + hours
        household.wages_earned = (household.wages_earned or 0.0) + pay
        household.wage_income_this_year = household.wage_income_this_year + pay
        # SAY WHEN IT IS A BAD TRADE: selling your hours costs you the
        # practice those same hours were running (see practice_attention),
        # and for a trained person it is usually a net loss. That is
        # realistic - a trained man does not dig ditches for preference -
        # but it has to be said explicitly, not charged silently and left
        # for the player to work out from the ledger.
        # DO NOT BLOCK IT - WARN ABOUT IT: selling hours is a legitimate
        # way to dig out of debt, so this must never refuse the sale, only
        # warn when it would starve an active project of the hours it
        # still wants this year. Computed from project_hour_pace/
        # active_hours_still_wanted (projects.py), the same formula step()
        # itself uses to hand out the pool, so this can never warn about a
        # shortfall step() would not also produce.
        _starve = None
        _wanted = self._world.active_hours_still_wanted()
        if _wanted:
            _after = max(0.0, self.director_pool() - self.director_hours_committed())
            _short = {trade_id: hours_wanted for trade_id, hours_wanted in _wanted.items() if hours_wanted > _after + 0.5}
            if _short:
                _named = sorted(_short.items(), key=lambda kv: -kv[1])[:2]
                _more = len(_short) - len(_named)
                _bits = ["%s (wants about %.0f more of your hours this year)"
                        % (trade_id, hours_wanted) for trade_id, hours_wanted in _named]
                _starve = (
                    "this leaves only %.0f of your own hours for the rest of "
                    "the year, and %s: %s%s. Nothing is lost - what it does "
                    "not get this year it gets next - but if that is not what "
                    "you meant, work fewer hours. Selling them anyway is a "
                    "fair move if it is cash you need right now."
                    % (_after,
                       "it still wants more than that" if len(_short) == 1
                       else "these still want more than that",
                       "; ".join(_bits),
                       (", and %d more" % _more) if _more else ""))
        lost = before_practice - self._world.revenue()
        self.log_wage_work(trade, hours, pay, lost)
        if lost > pay:
            # THE THREE NUMBERS HAVE TO SUBTRACT: rounding each separately
            # can give "you earned 128 ... was worth 234 ... so this cost
            # you 105" - numbers that do not actually subtract when a
            # reader checks by hand. Round first, then subtract.
            _paid, _lost = round(pay), round(lost)
            _msg = ("you earned %s, and the practice those hours were "
                    "running was worth %s a year - so this cost you %s. "
                    "Wage work is for when you have no practice to lose."
                    % (self._world.money_text(_paid, grouped=True), self._world.money_text(_lost, grouped=True),
                       self._world.money_text(_lost - _paid, grouped=True)))
            if _starve:
                _msg += " Also: " + _starve
            return pay, _msg
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
        total = 0.0
        for trade, count in self._world.state.household.employees.items():
            total += count * self.labour_market.quote_annual(trade)
        return total

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
        tools = (sum(self._world.material_price_factor(material) * self._world.last_market_price_ratio(material)
                     for material in basket) / len(basket)
                 if basket else 1.0)
        return {"food": food, "housing": housing, "tools": tools,
                "skill_and_difficulty": 1.0,
                "weighted": self.WAGE_SHARE_FOOD * food + self.WAGE_SHARE_HOUSING * housing
                            + self.WAGE_SHARE_TOOLS * tools + self.WAGE_SHARE_SKILL_AND_DIFFICULTY}

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
