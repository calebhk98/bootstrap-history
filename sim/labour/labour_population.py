"""The local labour market: who is out there, how much of them this
household can reach.

Split out of labour.py (see that file's own docstring for why). These are
methods of Labour; they are a mixin only so that they can live in a file of
their own. 
What leaning on a trade does to its price lives in labour_market_api.py.
trade_available and found_trade_school decide whether a trade can be had here
AT ALL; market_supply, reachable_trade_population and national_trade_population
give the depth of that market, this household's reach into it, and the whole
country's rough total. A trade's people are the working people of one
provincial town (TOWN_POPULATION_REFERENCE sizes it) times the trade's share of
non-farm labour, read from society's hours or the recipe graph's need, so a
trade a mod adds is sized without code. SCHOLAR_ENGAGEMENT_FRACTION,
SCRIBE_ENGAGEMENT_FRACTION and MERCHANT_DENSITY size the trades literacy
bounds; NO_DEMAND_TRADE_SHARE and UNSKILLED_POOL_TOWN_SHARE cover the rest.
population_report and home_town_population_estimate are what the 'population'
command shows, built from the numbers above.
effective_scholars and scholar_hands_available answer "how many scholars
can this household actually put to work this year", the population-side
half of the same question hours_you_can_call_on (labour_training.py)
answers for craft hours.
"""
from sim.constants import declare, REGISTRY

from . import legacy_trade_defaults, trade_data
from .workforce_spinup import FARM_TRADE


class PopulationMixin:
    """The labour market this household draws on: its depth and the
    population estimates behind it -
    see this module's own docstring for why these subjects sit together.
    """


    def effective_scholars(self):
        """You are your own natural philosopher; everyone else is hired."""
        return self._world.state.household.scholars + (1.0 if self._world.state.founder.founder_alive else 0.0)

    def scholar_hands_available(self):
        """Scholars you can actually put on a project this year: the ones on
        your own staff, yourself, plus the ones whose time you have already
        bought under contract.

        THE SAME FIX craft_hands_available() GOT, ARRIVING LATE. That
        function's own comment records the bug: a gate that read the payroll
        alone, so work you had already paid an outside shop to do could not
        satisfy the requirement - and the refusal's advice was to go and
        commission it. `commission` could not unblock the gate that
        recommended commission.

        It was fixed for craft trades and never extended to scholars, so the
        identical defect survived for them and was reported as
        Complaints/34: buying labourer hours works, buying SCHOLAR hours
        does nothing. Reproduced against the live protocol - a 2,000-hour
        scholar commission succeeded, took the money, and left the refusal
        byte-identical.

        A year of a scholar's time IS a scholar, for the purpose of whether
        you may attempt a thing that needs one. Buying the work rather than
        the person is the whole point of `commission`, and it is what
        somebody in this position actually did.
        """
        contracted = sum(hours for trade, hours
                         in getattr(self._world.household, "contract_hours", {}).items()
                         if self._world.trade_family(trade) == self._world.trade_family(trade_data.scholar_trade()))
        return (self.effective_scholars()
                + contracted / self._world.HOURS_PER_PERSON_YEAR)

    def trade_available(self, trade):
        """Can this trade be had here at all, at any price?

        Rome has masons and plumbers in abundance and no machinists whatever.
        An absent trade is not expensive, it is absent, and the only way to have
        one is to teach somebody the trade yourself.
        """
        if trade not in self._world.trades_absent:
            return True
        household = self._world.state.household
        return (trade in household.trades_created
                or (household.trade_schools or {}).get(trade, 0.0) > 0)

    def found_trade_school(self, trade, seats):
        """Create durable local training capacity for one named trade."""
        if trade not in self._world.wages or not self.trade_available(trade):
            return False, ("the trade must exist before a school can reproduce "
                           "it; teach or discover %s first" % trade)
        seats = float(seats)
        cost = seats * self._world.trade_school_price_per_seat()
        household = self._world.state.household
        if seats <= 0 or cost > household.capital:
            return False, "cannot afford that trade school"
        household.debit(cost, "trade schools")
        schools = getattr(household, "trade_schools", None)
        if schools is None:
            schools = household.trade_schools = {}
        schools[trade] = schools.get(trade, 0.0) + seats
        household.trades_created.add(trade)
        return True, None

    def _is_lettered(self, trade):
        """Whether the trade's pool is bounded by who can read and write, not by what
        the town's households need made."""
        scholar_family = self._world.trade_family(trade_data.scholar_trade())
        return (bool(trade_data.literate_trades(trade_data.registry_of(self._world), (trade,)))
                or trade in legacy_trade_defaults.LETTERED_BUT_NOT_LITERATE
                or self._world.trade_family(trade) == scholar_family)

    def _share_of_town_work(self, trade):
        """The trade's share of non-farm labour: society's current hours when it has
        them, else the need the recipe graph puts on it; 0.0 with neither."""
        hours = self._world.state.economy.society_labour_hours
        rest = sum(value for name, value in hours.items() if name != FARM_TRADE)
        if rest > 0.0 and hours.get(trade, 0.0) > 0.0 and trade != FARM_TRADE:
            return hours[trade] / rest
        return self._non_farm_need_shares().get(trade, 0.0)

    def _is_demand_derived(self, trade):
        return (not self._is_lettered(trade) and not self._is_unskilled_pool(trade)
                and self._share_of_town_work(trade) > self.NO_DEMAND_TRADE_SHARE)

    def _is_unskilled_pool(self, trade):
        """Work drawn from the unskilled pool: the farm trade, those under arms, and every trade the
        registry puts in the farm trade's family (hands anyone can become in a season or two)."""
        return (trade == FARM_TRADE or trade_data.drawn_from_unskilled_pool(trade)
                or self._world.trade_family(trade) == self._world.trade_family(FARM_TRADE))

    def _working_fraction(self):
        population = self._world.population
        return population.working_age / population.total if population.total > 0 else 0.0

    def _town_people_of_trade(self, trade):
        """People of an ordinary trade in the towns this household reaches by
        travel: their working people times the trade's share of work, never
        below the declared floor share."""
        working = self.reach_population_estimate() * self._working_fraction()
        if self._is_unskilled_pool(trade):
            return working * self.UNSKILLED_POOL_TOWN_SHARE
        return working * max(self._share_of_town_work(trade), self.NO_DEMAND_TRADE_SHARE)

    def _trade_density_source(self, trade):
        """Name of the declared constant this trade's population estimate rests on,
        None when it is derived from need or unavailable. Used by population_report
        and _density_is_placeholder to look up metadata.
        """
        if not self.trade_available(trade) or trade in self._world.trades_absent:
            return None
        if trade == trade_data.scholar_trade():
            return "SCHOLAR_ENGAGEMENT_FRACTION"
        if trade_data.literate_trades(trade_data.registry_of(self._world), (trade,)):
            return "SCRIBE_ENGAGEMENT_FRACTION"
        if trade in legacy_trade_defaults.LETTERED_BUT_NOT_LITERATE:
            return "MERCHANT_DENSITY"
        if self._is_unskilled_pool(trade):
            return "UNSKILLED_POOL_TOWN_SHARE"
        if self._is_demand_derived(trade):
            return None
        return "NO_DEMAND_TRADE_SHARE"

    def _density_is_placeholder(self, trade):
        """Whether a trade's population estimate is a placeholder
        (temporary_heuristic) or a cited estimate (engineering_estimate).
        Looks up the constant name in REGISTRY rather than hard-coding which
        trades are placeholders, so the answer stays consistent with the
        declaration itself.
        """
        source_name = self._trade_density_source(trade)
        if source_name is None:
            return False
        if source_name not in REGISTRY:
            return False
        return REGISTRY[source_name].get("kind") == "temporary_heuristic"

    # HIRING A HANDFUL OF SMITHS MUST NOT MOVE THE STANDING WAGE. A market
    # supply pool sized for a single provincial town, not the whole country,
    # would make hiring five smiths where thousands actually exist move the
    # price a lot, because the pool itself is the size of a hamlet -
    # something the game needs to say out loud rather than leave a player to
    # infer (see the 'population' command, and the framing note in `hire`,
    # `labour` and each civ's opening briefing). Buying ten slaves is a
    # DIFFERENT wall - household_room, this household's own capacity to
    # feed, house and supervise people, checked in hire() below and nothing
    # to do with market_supply - and is correctly left alone: a household of
    # one cannot run ten slaves without somewhere to put them, in any
    # economy, however deep its labour market runs.
    #
    # TOWN_POPULATION_REFERENCE is the size of the single market this
    # household's reach actually represents, at full population scale (Rome
    # itself, pop_scale == 1.0) - not the whole country, which is exactly the
    # thing this game needs to say out loud rather than leave a player to
    # infer (see the 'population' command, and the framing note in `hire`,
    # `labour` and each civ's opening briefing). ANCHORED, not invented: the
    # album of the fabri tignuarii of Ostia (CIL XIV 4569, dated 198 AD)
    # records about 350 quinquennial members of one building-trade guild in a
    # town usually put at the order of 50,000 people (Meiggs, "Roman Ostia",
    # 2nd ed. 1973, ch. on the plebs and the collegia) - call it 0.7% of the
    # town registered in ONE common craft. A floor, not a ceiling: guild
    # rolls undercount apprentices, slaves, women in the associated trades
    # and anyone who never joined.
    #
    # It shrinks with pop_scale exactly the way hired_hours_cap_base already
    # does ("a civilization of 1.5 million cannot field what one of 65
    # million can" - hired_cap()'s own comment) - a smaller civilisation's
    # own provincial towns are smaller too, which is a separate and
    # defensible claim from how big ONE of them is.
    TOWN_POPULATION_REFERENCE = declare(
        "TOWN_POPULATION_REFERENCE", 50000.0, kind="engineering_estimate",
        unit="people, at pop_scale=1.0",
        source="Meiggs, 'Roman Ostia', 2nd ed. 1973 (the album of the "
               "fabri tignuarii of Ostia, CIL XIV 4569, dated 198 AD, "
               "records about 350 quinquennial members of one "
               "building-trade guild in a town usually put at the order "
               "of 50,000 people).",
        confidence="C",
        why="The size of the ONE provincial town this household's labour "
            "market represents, at full population scale - not the whole "
            "country. Anchored on a real attestation (guild membership as "
            "a share of a town of known rough size), used as a floor "
            "rather than a precise census figure since guild rolls "
            "undercount apprentices, slaves and women in the trade. This "
            "sizes a MARKET, not a historical outcome the simulation is "
            "meant to reproduce - see this constant's own long comment "
            "above for the full derivation.")

    # A trade's people in the town = the town's working people x its share of
    # non-farm labour (society's hours, else the recipe graph's need). The two
    # shares below cover trades that share cannot size.
    NO_DEMAND_TRADE_SHARE = declare(
        "NO_DEMAND_TRADE_SHARE", 0.00005, kind="temporary_heuristic",
        unit="fraction of the town's working people", source=None,
        confidence="D",
        why="Floor share for a trade no available recipe puts need on (a "
            "specialist whose work is not in the household-demand graph yet): "
            "a few people always practise it. An order-of-magnitude "
            "placeholder until every trade's work is in the recipe graph.")
    UNSKILLED_POOL_TOWN_SHARE = declare(
        "UNSKILLED_POOL_TOWN_SHARE", 0.05, kind="temporary_heuristic",
        unit="fraction of the town's working people", source=None,
        confidence="D",
        why="Town people for hire from the unskilled pool (farm labour and "
            "the trades drawn from it, such as an army): the farm trade's "
            "hours are decided by the farm logic, not the non-farm need "
            "split, so the town's share of them is an authored guess.")
    # scholar and scribe are bound by literacy, not by town population (see
    # literacy_factor, literate_capacity) - their NATIONAL estimate uses the
    # same idea applied to the literate pool instead of the town: what
    # fraction of the people who can read at all make their living reading
    # and writing for others, rather than simply being a literate landowner,
    # priest or advocate. Neither fraction is a count anyone published; both
    # are deliberately small because the trades themselves are (Rome's own
    # literate_capacity("scholar") tops out at 5.9 reachable before any
    # institution trains more). merchant is excluded from LITERATE_TRADES on
    # purpose (see that set's own comment - "an agent working on commission is
    # not, in this period, chiefly a reader") so it gets a plain urban density
    # instead, also with no specific count found.
    SCHOLAR_ENGAGEMENT_FRACTION = declare(
        "SCHOLAR_ENGAGEMENT_FRACTION", 0.002, kind="temporary_heuristic",
        unit="fraction of (literacy_elite x population)", source=None,
        confidence="D",
        why="What fraction of the literate, propertied population makes "
            "its living as a scholar for hire, rather than simply being a "
            "literate landowner, priest or advocate. No published count "
            "exists for this; deliberately small, consistent with "
            "literate_capacity('scholar') topping out at 5.9 reachable "
            "for Rome before any institution trains more.")
    SCRIBE_ENGAGEMENT_FRACTION = declare(
        "SCRIBE_ENGAGEMENT_FRACTION", 0.05, kind="temporary_heuristic",
        unit="fraction of (literacy_general x population)", source=None,
        confidence="D",
        why="As SCHOLAR_ENGAGEMENT_FRACTION, for scribes drawn from the "
            "wider general-literacy pool rather than the propertied elite.")
    MERCHANT_DENSITY = declare(
        "MERCHANT_DENSITY", 0.004, kind="temporary_heuristic",
        unit="fraction of urban population", source=None, confidence="D",
        why="Merchant density, treated like an ordinary craft density "
            "(a share of work) rather than a literacy-bound one, because "
            "merchant is deliberately excluded from LITERATE_TRADES (an "
            "agent working on commission is not, in this period, chiefly "
            "a reader). No specific count found; an order-of-magnitude "
            "placeholder.")

    TAUGHT_TRADE_SUPPLY_MULTIPLIER = declare(
        "TAUGHT_TRADE_SUPPLY_MULTIPLIER", 1.5, kind="temporary_heuristic",
        unit="dimensionless multiplier on your own employees' hours",
        source=None, confidence="D",
        why="For a trade this society had no word for until you taught it "
            "(TRADES_ABSENT), the market this household reaches is only "
            "the people you trained plus the ones they have since trained "
            "themselves - approximated as half again your own headcount's "
            "hours, standing in for that second generation, rather than "
            "modelling who-taught-whom explicitly.")
    def _hiring_cap_before_actors(self, trade):
        """Hours a year of a trade the town's people offer, before firms' and governments' staff
        are taken out of it."""
        base = (self._world.cfg["hired_hours_cap_base"] * self.local_market_share()
                * (self.POP_SCALE_FLOOR_SHARE
                   + self.POP_SCALE_VARIABLE_SHARE * min(1.0, self._world.pop_scale)))
        if self._is_lettered(trade):
            cap = base * self.SCHOLAR_MARKET_SHARE   # literate men are a small fraction of anywhere
        else:
            cap = self._town_people_of_trade(trade) * self._world.HOURS_PER_PERSON_YEAR
        cap = self._world.effect_factor("market_hiring_factor", cap, self.HIRING_MULTIPLIER_EXPONENT)
        # A trade that needs reading cannot be bought past how many people
        # here can read; taught literate trades are absent and bounded by
        # literate_capacity() in train() instead.
        if trade in self.LITERATE_TRADES:
            cap *= self.literacy_factor(trade)
        return cap

    def market_supply(self, trade):
        """Hours a year of this trade the local labour market can actually supply.

        THIS IS ONE TOWN'S MARKET, NOT THE COUNTRY'S - the household this
        game puts you in charge of draws on one town's labour, the way a
        real Roman, Han or Norse founder would have. See
        TOWN_POPULATION_REFERENCE's own comment for why that is a
        defensible modelling choice and _town_people_of_trade for how big 'one
        town's worth' of each trade actually is; national_trade_population
        answers the country-wide question this number is not trying to.
        """
        if not self.trade_available(trade):
            return 0.0
        household = self._world.state.household
        school_hours = ((household.trade_schools or {}).get(trade, 0.0)
                        * self._world.HOURS_PER_PERSON_YEAR)
        if trade in self._world.trades_absent:
            return self._taught_trade_people(trade) * self._world.HOURS_PER_PERSON_YEAR
        cap = self._world.shared_answer(
            ("hiring_cap", trade), (self._world.civ.get("literacy_elite"), self._world.civ.get("literacy_general")),
            lambda: self._hiring_cap_before_actors(trade))
        # firms and governments hire from the same pool, so what they employ is not on offer
        cap = max(0.0, cap - self._world.actor_staff_fte(trade) * self._world.HOURS_PER_PERSON_YEAR)
        hours = cap + household.employees.get(trade, 0.0) * self._world.HOURS_PER_PERSON_YEAR + school_hours
        return min(hours, self.people_who_exist(trade) * self._world.HOURS_PER_PERSON_YEAR)

    def reachable_trade_population(self, trade):
        """What this household's own labour market actually holds of this
        trade, your own employees included - the 'population' command's
        "within your reach" column; see national_trade_population for the
        other half of the same question.

        scholar and scribe read literate_capacity() INSTEAD OF market_
        supply(): that is the real wall hire() and train() enforce for
        them (see _literate_wall_refusal - "this household's reach into
        the labour market for %ss will not stretch past %.1f"), floored
        at 1.5 so a literate person always exists somewhere, which market_
        supply's own formula is not floored to. Showing the smaller,
        unfloored market_supply figure here would make Norse scribes read
        as "0.2 within your reach" when the game will in fact let a
        player hire one - exactly the kind of false "nobody's there"
        reading literate_capacity's own floor exists to prevent.
        """
        if trade_data.literate_trades(trade_data.registry_of(self._world), (trade,)):
            return self.literate_capacity(trade)
        return self.market_supply(trade) / self._world.HOURS_PER_PERSON_YEAR

    def _taught_trade_people(self, trade):
        """People in a trade only you teach: your staff, their own students
        (approximated as a multiple of your headcount) and school places."""
        household = self._world.state.household
        return (household.employees.get(trade, 0.0) * self.TAUGHT_TRADE_SUPPLY_MULTIPLIER
                + (household.trade_schools or {}).get(trade, 0.0))

    def people_who_exist(self, trade):
        """People in this trade who exist in the country, counting your own
        staff even if a collapse has left the estimate below them."""
        return max(self.national_trade_population(trade),
                   self._world.state.household.employees.get(trade, 0.0))

    def available_trades(self):
        """Every trade this society has that the labour market can supply."""
        return [trade for trade in sorted(self._world.wages) if self.trade_available(trade)]

    def project_staffing_shortfall(self, node):
        """A sentence when the country lacks the people this project needs at
        once, else None. Demand is the trained heads the node asks for, and at
        least one person in every trade it draws hours from; supply is the
        people who exist in those trades."""
        trades = sorted(trade for trade, hours in (node["lab"] or {}).items()
                        if hours > 0 and trade not in self._world.trades_absent
                        and self.trade_available(trade))
        working_age = self._world.population.working_age
        craft_supply = sum(self.people_who_exist(trade) for trade in trades)
        scholar_supply = self.people_who_exist(trade_data.scholar_trade())
        empty = [trade for trade in trades if self.people_who_exist(trade) < 1.0]
        craft_need = float(node["art"])
        scholar_need = float(node["sch"])
        short = []
        if empty:
            short.append("no %s left to do the %s" % (
                "one" if len(empty) == 1 else "people",
                ", ".join(empty) + " work"))
        if craft_need > (craft_supply if trades else working_age):
            short.append("%d craftsmen against about %.1f" % (
                craft_need, craft_supply if trades else working_age))
        if scholar_need > scholar_supply:
            short.append("%d scholars against about %.1f" % (scholar_need, scholar_supply))
        if craft_need + scholar_need > working_age:
            short.append("%d workers against %.0f of working age" % (
                craft_need + scholar_need, working_age))
        if not short:
            return None
        return ("there are not enough people in this country to staff it: %s. "
                "Only about %.0f people of working age exist, and a project "
                "needing more workers than exist cannot be staffed at any price."
                % ("; ".join(short), working_age))

    def national_trade_population(self, trade):
        """A rough ESTIMATE of how many people ply this trade across the whole
        country - not this household's reach: the same share of work
        _town_people_of_trade reads, applied to the country's urban working
        people instead of one town's. 0.0 for a trade this society does not
        have (trade_available says so). Nobody has published an occupational
        census of the ancient world, so every figure is an estimate and the
        'population' command says so.
        """
        if not self.trade_available(trade):
            return 0.0
        # The age-cohort model's running headcount is the actual population.
        pop = self._world.population.total
        urban = pop * float(self._world.civ.get("urban_fraction", 0.0))
        working = self._world.population.working_age
        if trade_data.drawn_from_unskilled_pool(trade):
            return working   # any of the working age may be called up
        if trade == trade_data.scholar_trade():
            return pop * float(self._world.civ.get("literacy_elite", 0.0)) * self.SCHOLAR_ENGAGEMENT_FRACTION
        if trade_data.literate_trades(trade_data.registry_of(self._world), (trade,)):
            return pop * float(self._world.civ.get("literacy_general", 0.0)) * self.SCRIBE_ENGAGEMENT_FRACTION
        if trade in legacy_trade_defaults.LETTERED_BUT_NOT_LITERATE:
            return urban * self.MERCHANT_DENSITY
        if trade in self._world.trades_absent:
            return self._taught_trade_people(trade)
        if trade == FARM_TRADE:
            return working * (1.0 - float(self._world.civ.get("urban_fraction", 0.0)))
        if self._is_unskilled_pool(trade):
            return urban * self._working_fraction() * self.UNSKILLED_POOL_TOWN_SHARE
        return (urban * self._working_fraction()
                * max(self._share_of_town_work(trade), self.NO_DEMAND_TRADE_SHARE))

    def population_report(self):
        """Everything the 'population' command (protocol.py) shows, worked
        out here rather than in the command layer: the country's own
        numbers (population, urban_fraction - already loaded for
        pop_scale, see core.py), the size of the one town this household
        actually reaches, and - per trade - the three-way comparison that
        is the whole point of this command: how many exist in the
        country, how many are within reach, how many you employ, and what
        share of the reachable pool that is.

        This has to say both at once: a bare "market can supply 22,500
        hours" says nothing about whether that is most of the trade or a
        rounding error against it, and leaves "the labour market is the
        size of a village" unanswered.
        """
        # self.population.total (the age-cohort model) is the direct
        # answer for `pop`, not a reconstruction-by-ratio (see
        # national_trade_population's own comment, just above).
        # `reference_pop`/`scale_from_baseline` are kept as the screen's
        # own "before simulated changes" comparison, not as inputs to
        # `pop`.
        reference_pop = float(self._world.civ.get("population", 0.0))
        pop = self._world.population.total
        scale_from_baseline = (pop / reference_pop) if reference_pop else 1.0
        urban_frac = float(self._world.civ.get("urban_fraction", 0.0))
        trades = []
        for trade in sorted(self._world.wages):
            national = self.national_trade_population(trade)
            reach = self.reachable_trade_population(trade) if self.trade_available(trade) else 0.0
            have = self._world.state.household.employees.get(trade, 0.0)
            trades.append({
                "trade": trade,
                "exists_here": self.trade_available(trade),
                "estimated_in_the_country": round(national, 1),
                "within_your_reach": round(reach, 2),
                "you_employ": round(have, 2),
                "share_of_the_reachable_pool_you_employ":
                    round(have / reach, 4) if reach > 1e-9 else None,
                "is_placeholder": self._density_is_placeholder(trade),
            })
        return {
            "civilisation": self._world.civ.get("short_name", self._world.civ.get("name", self._world.civ.get("id", ""))),
            "population": round(pop),
            "reference_population_before_simulated_changes": round(reference_pop),
            "population_change_from_reference": round(scale_from_baseline - 1.0, 4),
            "urban_fraction": round(urban_frac, 3),
            "urban_population_estimate": round(pop * urban_frac),
            "the_town_you_actually_operate_in": {
                "estimated_population": round(self.home_town_population_estimate()),
                "note": ("an ESTIMATE, not a place this game names: you are one "
                        "household drawing on one town's labour market, not the "
                        "whole of the country above - see what_this_means, below."),
            },
            "trades": trades,
            "what_this_means": (
                "Every hiring limit and every wage move in this game is sized "
                "to ONE household's reach into ONE town's labour market, not "
                "to the %s people counted above. A trade's 'within your "
                "reach' figure is what that market can actually supply you; "
                "'estimated in the country' is the whole civilisation's rough "
                "total, for scale. Both are explicit ESTIMATES, not a census - "
                "some trade counts are based on historical records, others are "
                "rough placeholders. Buying people (a slave, a freedman) is bounded "
                "separately, by this household's own room to feed, house and "
                "supervise them ('labour' shows that ceiling) - NOT by how "
                "deep any market runs. One thing the two columns will look "
                "like they disagree about, and do not: for a SPECIALISED "
                "trade - an engraver, a glassblower, a millwright - the "
                "reachable figure is far tighter than the country total "
                "divided by the number of towns would suggest, because a "
                "specialist does not practise in every town and the ones who "
                "do are not all for hire. The common crafts are the ones "
                "sized straight off a town's own population."
                % "{:,.0f}".format(pop)),
        }