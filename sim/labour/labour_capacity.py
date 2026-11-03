"""How many trained, hired or supervised people this household may have: the institutional ceiling on trained
staff, the supervisory headroom beyond it, and the room left once the people already held are counted."""
from sim.constants import declare

from . import trade_data
from .staff_wage_reference import blended_annual_wage


class Capacity:
    def __init__(self, world, book, market, schedule, trades):
        self._world = world
        self.book = book
        self.market = market
        self.schedule = schedule
        self.trades = trades

    # WHO TRAINS PEOPLE, AND HOW MANY OF THEM.
    #
    # (node, scholars, artisans, directors, scales_with_units, must_be_running)
    #
    # The first nine are institutions the founder establishes: a school, a
    # licensed collegium, a patron, an endowment, a network of academies, and
    # the books that let people teach themselves. The rest are the late game's
    # own engine - each heavy industrial work trains the workforce that makes
    # the next one possible.
    #
    # scales_with_units: a second school trains a second school's worth of
    # scholars, so these are linear in institution_units (1.0 for a run that
    # never founds more than the original unit; the diminishing return lives
    # in what each further unit COSTS, see institution_unit_cost). The fixed
    # ones are singular by nature - there is one imperial patron.
    #
    # must_be_running: capacity that depends on a going concern disappears
    # when the concern does. bessemer_openhearth is the exception: a society
    # that has learned to make steel this way does not forget the men it
    # trained if one works closes.
    # Scholars/artisans/directors each institution trains outright, once
    # running - the raw figures behind STAFF_CAPACITY_SOURCES below, pulled
    # into named declarations so the table's own numbers carry provenance.
    # None of these is derived from anything physical (a real school's
    # actual graduation rate, a real patron's actual household); each is a
    # design-balance figure sized so the tree's own pacing (a school by
    # year N, an academy network by year M) feels achievable, which is
    # exactly the shape CLAUDE.md 3.4 calls a labelled heuristic rather
    # than a violation - nothing here stands in for a historical OUTCOME
    # (a wage, a price, an army size), only for an untouched mechanism
    # (how fast an institution actually trains people).

    # STAFF_CAPACITY_SOURCES: [(node, scholars, artisans, directors, scales_with_units, must_be_running)]
    # from each node's `staff_capacity`, as the mechanics module's `staff_capacity_sources` view gives them.

    STAFF_CAPITAL_INCOME_RATE = declare(
        "STAFF_CAPITAL_INCOME_RATE", 0.06, kind="temporary_heuristic",
        unit="fraction of capital per year", source=None, confidence="D",
        why="Idle capital is treated as though it earns this much a year "
            "toward what a household can afford to pay staff, standing in "
            "for a real return on capital (lending it out, investing it) "
            "this engine does not model at the household level. Not "
            "derived from DEBT_BASE_RATE or any other rate elsewhere in "
            "the engine; picked as a plausible order of magnitude.")

    STAFF_BUDGET_SHARE_OF_SPARE = declare(
        "STAFF_BUDGET_SHARE_OF_SPARE", 0.40, kind="temporary_heuristic",
        unit="fraction of true surplus", source=None, confidence="D",
        why="Of the surplus actually left after upkeep and living costs, "
            "the share a household is willing to commit to new staff in a "
            "single year rather than holding back - a caution constant, "
            "not a measured savings rate.")

    def staff_wage_reference(self):
        """Blended annual wage, in current money, of the trades that exist from
        the start: what hiring costs the market now, so an affordability
        budget turns into a headcount in the money it is paid in."""
        market = self.market
        wages = [wage for trade in sorted(self._world.trades.wages) if trade not in self._world.trades.trades_absent
                 for wage in [market.quote_annual(trade)] if wage is not None]
        blended = blended_annual_wage(wages)
        return blended if blended is not None else market.quote_annual(
            trade_data.fallback_trade_of(self._world, self.schedule.wage_schedule().training_years))

    STAFF_EXTRA_HEADROOM_WEIGHT = declare(
        "STAFF_EXTRA_HEADROOM_WEIGHT", 1.35, kind="temporary_heuristic",
        unit="dimensionless", source=None, confidence="D",
        why="How much more expensive supervision_room()'s extra headroom "
            "is treated as, relative to an institutional scholar or "
            "artisan, when the same affordability budget has to cover "
            "both. Tuned so the headroom hiring does not silently crowd "
            "out institutional staffing or the other way round; not "
            "measured against any real relative cost of the two.")

    STAFF_POP_SCALE_FLOOR = declare(
        "STAFF_POP_SCALE_FLOOR", 0.45, kind="temporary_heuristic",
        unit="fraction of the institutional ceiling", source=None,
        confidence="D",
        why="Even the smallest civilisation this game starts keeps this "
            "much of the institutional staffing ceiling, so a small "
            "society is diminished rather than unable to staff anything "
            "at all - the softening this function's own comment describes "
            "after 'a first pass made every small civilization fail "
            "outright'. Tuned to that observed failure, not measured.")

    STAFF_POP_SCALE_VARIABLE = declare(
        "STAFF_POP_SCALE_VARIABLE", 0.55, kind="temporary_heuristic",
        unit="fraction of the institutional ceiling, scaled by pop_scale",
        source=None, confidence="D",
        why="The remaining share of the institutional ceiling that DOES "
            "grow with population, paired with STAFF_POP_SCALE_FLOOR (the "
            "two are tuned to sum to 1.0).")

    STAFF_POP_SCALE_EXPONENT = declare(
        "STAFF_POP_SCALE_EXPONENT", 0.35, kind="temporary_heuristic",
        unit="dimensionless exponent on pop_scale", source=None,
        confidence="D",
        why="How sub-linearly the population-scaled share of staffing "
            "capacity grows with pop_scale - a civilisation of 4.5 million "
            "can eventually staff what one of 65 million can, just more "
            "slowly, rather than never. The sub-linear SHAPE is the real "
            "claim (bigger societies are not proportionately easier to "
            "staff from); the exact exponent is tuned, not fitted.")

    DIRECTOR_SCALE_HEADROOM = declare(
        "DIRECTOR_SCALE_HEADROOM", 1.3, kind="temporary_heuristic",
        unit="dimensionless", source=None, confidence="D",
        why="Directors are allowed to reach a slightly higher fraction of "
            "their institutional ceiling than scholars/artisans do at the "
            "same affordability `scale`, on the theory that a household "
            "stretched thin still prioritises the deputies who let it run "
            "concerns at a distance. Tuned headroom, not a measured "
            "priority order.")

    def staff_capacity(self):
        """How many trained people the institution can support.

        Ceilings, not rates. You cannot teach faster than you can feed, house and
        supervise, and you cannot supervise more than your directors can reach.
        Funding matters: an institute whose income has collapsed sheds people.
        """
        # There is no floor here any more. Rome does have excellent craftsmen for
        # hire and they are reachable through market_supply() and `hire`, which
        # is a thing you do rather than a staff of four you are handed on
        # arrival and never asked for.
        base_sc, base_ar = 0.0, 0.0
        # A SECOND SCHOOL TRAINS A SECOND SCHOOL'S WORTH OF SCHOLARS. Linear in
        # institution_units, which is 1.0 for a run that never founds more than
        # the original single unit - exactly the constants below, unchanged -
        # and the actual capacity a further unit buys otherwise. The COST of
        # each further unit is where the diminishing return lives (see
        # the production module's institution_unit_cost view); this is simply how big the
        # place you paid for actually is.
        # STAFF_CAPACITY_SOURCES is the whole list, in one place, because the
        # planner needs to read it too. A plan built from the tech tree alone
        # cannot see any of this: nothing in the goal's prerequisite closure
        # mentions a school, so a purely structural plan can walk into
        # quantum_solidstate_theory's demand for eight trained scholars
        # against a society that tops out at 5.9 of them and sit there
        # until the horizon runs out, unless the planner can read the same
        # table this function reads rather than an if-chain only this
        # function could see.
        scholars, artisans, directors = self._institutional_load(with_directors=True)
        # you cannot keep staff you cannot pay
        # a famous school attracts students and patrons it did not have to pay for
        # WAGES ARE A REAL CHARGE (see wage_bill), so this ceiling must be
        # more than "what you could pay for": it must leave room WITHOUT
        # eating the surplus needed to build anything, or hiring to the
        # edge of affordability could let payroll consume the entire
        # surplus, leaving nothing to spend on the work itself. A
        # programme whose payroll is its whole income is not a programme.
        #
        # SPARE MUST SUBTRACT living_cost() TOO, not just revenue() minus
        # upkeep() (the upkeep of BUILT WORKS alone): living_cost also
        # covers rent, appearances, tax and (via wage_bill) the staff
        # already carried. Subtracting living_cost here is what "what you
        # can pay for" has to mean if it is to mean anything: money already
        # going to rent and to people already employed is not there to
        # hire more people with.
        afford, pop = self._staffing_affordability()
        # EXTRA is supervision_room(), the headroom auto_hire adds on top of
        # this institutional ceiling (see step(), section 1). It must be
        # folded into the SAME denominator this ceiling is scaled against,
        # not added with no affordability check of its own: sc/ar are BOTH
        # ZERO before a workshop or a school is built, so an unconditional
        # extra would let the headroom hiring go through at full strength
        # regardless of income. Folding it in is what makes "grow the staff
        # toward what you can house and pay" true of the headroom hiring
        # and not just the institutional kind.
        extra = self.supervision_room()
        # NO FLOOR: a household with no surplus at all must be able to hire
        # nobody. A floor such as max(0.10, ...) would still hire a tenth
        # of the headroom regardless of affordability, undoing the whole
        # calculation above - "grow the staff toward what you can house and
        # pay" has to be able to mean nobody.
        scale = self._staff_scale_for(afford, scholars + artisans, extra)
        self._world.commands.set_staff_scale(scale)     # step() applies this to `extra` too
        return (base_sc + scholars * scale * pop, base_ar + artisans * scale * pop,
                directors * min(1.0, scale * self.DIRECTOR_SCALE_HEADROOM) * pop)

    def _institutional_load(self, with_directors=False):
        """Scholars and artisans (and directors) the running institutions train outright, before affordability."""
        scholars = artisans = directors = 0.0
        for key, _sc, _ar, _di, scaled, must_run in self._world.knowledge.STAFF_CAPACITY_SOURCES:
            if not (self._world.knowledge.running(key) if must_run else self._world.knowledge.has(key)):
                continue
            units = self._world.knowledge.institution_units(key) if scaled else 1.0
            scholars += _sc * units
            artisans += _ar * units
            directors += _di * units
        # LITERACY BOUNDS THE SCHOLAR CEILING. A school, an academy or an
        # imperial patron can only produce as many scholars as this society
        # has literate, propertied people to draw them from (literacy_factor
        # reads literacy_elite for "scholar"; see FINDINGS_ROUND2 section Q).
        # Below Rome's own literacy_elite (0.9, the number every one of the
        # figures above was already tuned against) this narrows the pool;
        # printing, schools and libraries raise literacy_elite
        # (apply_tech_effects in sim/diffusion/tech_effects.py) and widen it again as a run goes
        # on, which is the entire point of building them.
        scholars *= self.trades.literacy_factor(trade_data.scholar_trade())
        if with_directors:
            return scholars, artisans, directors
        return scholars, artisans

    def _staffing_affordability(self):
        """(people the spare income can pay, population scale on institutional ceilings)."""
        spare = max(0.0, (self._world.finance.revenue() - self._world.finance.upkeep() - self._world.finance.living_cost())
                    * self._world.finance.rep_factor()
                    + max(0.0, self._world.finance.balance) * self.STAFF_CAPITAL_INCOME_RATE)
        budget = spare * self.STAFF_BUDGET_SHARE_OF_SPARE
        reference = self.staff_wage_reference()
        afford = 0.0 if reference is None else budget / reference     # no wage to price a hire at: none can be paid for
        # A civilization of 1.5 million simply cannot field the trained people a
        # civilization of 65 million can, however rich you are. This is the single
        # biggest structural difference between playing Rome and playing Norway.
        # A 4.5 million person society CAN eventually staff a semiconductor
        # programme, it just has to grow into it: making that impossible
        # would be a modelling error, not a finding.
        pop = (self.STAFF_POP_SCALE_FLOOR
               + self.STAFF_POP_SCALE_VARIABLE * min(1.0, self._world.people.pop_scale ** self.STAFF_POP_SCALE_EXPONENT))
        return afford, pop

    def _staff_scale_for(self, afford, institutional_people, extra):
        """Fraction of an institutional ceiling the spare income can pay for (no floor: no surplus hires nobody)."""
        return min(1.0, afford / max(1.0, institutional_people + extra * self.STAFF_EXTRA_HEADROOM_WEIGHT))

    def room_added_by(self, places):
        """Household places a node worth `places` would add at the current income.

        The node joins the same institutional load staff_capacity scales by
        affordability, so it adds less than its flat figure when the spare
        income cannot pay for the people, and more as the surplus grows.
        """
        scholars, artisans = self._institutional_load()
        afford, pop = self._staffing_affordability()
        extra = self.supervision_room()
        before = artisans * self._staff_scale_for(afford, scholars + artisans, extra)
        after = (artisans + places) * self._staff_scale_for(afford, scholars + artisans + places, extra)
        return (after - before) * pop

    _SUPERVISION_ROOM_WHY = (
        "Household headroom (people a founder may oversee, distinct from "
        "the institutional staff_capacity ceiling) this source is worth, "
        "used identically by supervision_room() and by "
        "supervision_room_from()'s own breakdown of it - one declared name "
        "per source rather than the same literal written twice, so the "
        "breakdown cannot drift from the total it explains. Tuned game "
        "balance, not measured from anything: a real figure would come "
        "from how many workers a person of a given period could actually "
        "keep an eye on.")

    SUPERVISION_ROOM_SELF = declare(
        "SUPERVISION_ROOM_SELF", 6.0, kind="temporary_heuristic",
        unit="people", source=None, confidence="D",
        why=_SUPERVISION_ROOM_WHY)

    SUPERVISION_ROOM_PER_DIRECTOR_EXTRA = declare(
        "SUPERVISION_ROOM_PER_DIRECTOR_EXTRA", 14.0, kind="temporary_heuristic",
        unit="people per trained deputy", source=None, confidence="D",
        why=_SUPERVISION_ROOM_WHY)

    def supervision_room(self):
        """People you can direct and pay BEYOND what your institutions train.

        staff_capacity is a ceiling on what a school, a workshop and a
        patron produce and support. It must not also be treated as a
        ceiling on how many men you can hire off the street, which is
        limited by money and by the market instead: conflating the two
        would put a hard wall across a run needing more craftsmen than an
        institutional ceiling alone supplies, one no amount of wealth
        could ever cross. This is that honest headroom. You hire them,
        you pay them every year, and you can only supervise so many.
        """
        workforce = self._world.workforce
        room = (self.SUPERVISION_ROOM_SELF
                + self.SUPERVISION_ROOM_PER_DIRECTOR_EXTRA * workforce.directors_extra
                + max(0.0, workforce.worker_housing_places or 0.0))
        room = self._world.knowledge.effect_sum("supervision_room", room)
        # A SECOND TOWN, NOT A SECOND SCHOOLROOM. workshop_first, school_founded
        # and academy_network above are each a single PLACE a founder can stand
        # in; fin_chain_store is the tree's own word for the thing that is not
        # - "operates identical stores in multiple cities... requires
        # sophisticated management and accounting" - so it belongs in the same
        # unconditional headroom as the other three places, not only in the
        # income-gated institutional ceiling (STAFF_CAPACITY_SOURCES) a branch
        # network also feeds. Smaller than that ceiling's own 30-per-unit
        # figure, the same way school_founded's 10 here is smaller than its
        # own 12 there: most of what a branch is worth is still bounded by
        # whether the household can pay its clerks, not by whether a director
        # could in principle watch them.
        return room

    def supervision_room_from(self):
        """Where supervision_room's total actually comes from, as rows.

        ONE RULE, NOT TWO: this re-walks the same sources supervision_room
        itself does and its total is asserted equal to it, because a
        breakdown that can disagree with the figure it explains is worse than
        no breakdown. The reason it exists is that a starting grant was
        invisible: Rome begins with fin_societas and so oversees ten people
        in year one where every other civilisation oversees six, and nothing
        anywhere told a Roman player why, or told a Norse player what they
        were missing. A civilisation's starting technologies are the whole
        point of having five civilisations, and an advantage nobody can see
        is an advantage the player cannot reason about.
        """
        rows = [{"source": "yourself", "people": self.SUPERVISION_ROOM_SELF,
                 "what_it_is": "what one person can keep an eye on"}]
        workforce = self._world.workforce
        if workforce.directors_extra > 0.005:
            rows.append({"source": "your deputies", "people":
                         round(self.SUPERVISION_ROOM_PER_DIRECTOR_EXTRA * workforce.directors_extra, 2),
                         "what_it_is": "people you have trained to direct work"})
        housing = max(0.0, workforce.worker_housing_places or 0.0)
        if housing > 0.0:
            rows.append({"source": "worker housing", "people": housing,
                         "what_it_is": "places you have bought to house the people you employ"})
        for key, spec in self._world.knowledge.effect_terms("supervision_room"):
            if self._world.knowledge.effect_holds(key, spec):
                rows.append({"source": key,
                             "people": (round(self._world.knowledge.effect_value(key, spec), 2) if "per_unit" in spec
                                        else self._world.knowledge.effect_value(key, spec)),
                             "what_it_is": spec["words"]})
        return rows

    def household_room(self):
        """How many more people this household can feed, house and oversee.

        One number, used by `hire` and by `buy` alike: using different
        ones - or, worse, none at all for one of the two - would let a
        player be told one capacity through one verb and exceed it
        through the other.
        """
        return (self.staff_capacity()[1] + self.supervision_room()
                - self.book.headcount())
