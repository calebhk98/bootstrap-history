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

    # STAFF_CAPACITY_SOURCES: [(node, scholars, artisans, directors, scales_with_units, must_be_running)] from each
    # node's `staff_capacity`, as the mechanics module's `staff_capacity_sources` view gives them: the scholars,
    # artisans and directors each institution trains outright. scales_with_units makes capacity linear in
    # institution_units; must_be_running drops it when the going concern stops. The figures are design-balance
    # numbers, not derived from a real school's graduation rate.

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
        wages = [market.quote_annual(trade) for trade in sorted(self._world.trades.wages)
                 if trade not in self._world.trades.trades_absent]
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
            "capacity grows with pop_scale - a small civilisation "
            "can eventually staff what a large one can, just more "
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
        """(scholars, artisans, directors) the institution can support; see `staff_ceiling`."""
        return self.staff_ceiling()[:3]

    def staff_ceiling(self):
        """(scholars, artisans, directors, scale): how many trained people the institution can support, and the share
        of its institutional ceiling the income can pay (the scale the supervision headroom takes too).

        Ceilings, not rates. You cannot teach faster than you can feed, house and
        supervise, and you cannot supervise more than your directors can reach.
        Funding matters: an institute whose income has collapsed sheds people.
        """
        # No floor: skilled people to hire come through market_supply() and `hire`, not as a staff handed over.
        # The institutional load is read from STAFF_CAPACITY_SOURCES (linear in institution_units where a source
        # scales), the one list the planner reads too.
        base_sc, base_ar = 0.0, 0.0
        scholars, artisans, directors = self._institutional_load(with_directors=True)
        # The ceiling leaves room without eating the surplus needed to build anything: spare income is net of
        # living_cost (rent, appearances, tax, the wage bill of the staff already carried) as well as upkeep.
        afford, pop = self._staffing_affordability()
        # `extra` is supervision_room(), the headroom auto_hire adds beyond the institutional ceiling; it is folded
        # into the same affordability denominator so the headroom hiring is also limited by income.
        extra = self.supervision_room()
        # no floor on the scale: a household with no surplus hires nobody
        scale = self._staff_scale_for(afford, scholars + artisans, extra)
        return (base_sc + scholars * scale * pop, base_ar + artisans * scale * pop,
                directors * min(1.0, scale * self.DIRECTOR_SCALE_HEADROOM) * pop, scale)

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
        # literacy bounds the scholar ceiling: only as many scholars as the society has literate, propertied people
        # to draw them from; printing, schools and libraries raise it again (apply_tech_effects).
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
        afford = budget / self.staff_wage_reference()
        # a small society cannot field the trained people a large one can, however rich; it can grow into them
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
        return room

    def supervision_room_from(self):
        """Where supervision_room's total actually comes from, as rows.

        ONE RULE, NOT TWO: this re-walks the same sources supervision_room
        itself does and its total is asserted equal to it, because a
        breakdown that can disagree with the figure it explains is worse than
        no breakdown. The reason it exists is that a starting grant was
        invisible: a civilisation that begins with a technology granting room
        oversees more people in year one than the others, and nothing
        anywhere told its player why, or told another player what they
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

        One number, used by `hire`, `train`, `buy` and the staff controls alike: it is net of the people already
        posted in the labour core and not yet arrived, and of the people being taught a trade, so no verb spends the same
        room twice.
        """
        return (self.staff_capacity()[1] + self.supervision_room()
                - self.book.headcount() - self.book.staff_posted() - self.book.in_training_total())
