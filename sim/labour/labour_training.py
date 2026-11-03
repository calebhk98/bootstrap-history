"""Teaching trades into existence: trade schools, the years and hours a trade takes to teach, and `train`."""
import math

from sim.refusal import Refusal
from . import trade_data, trade_first_hands, trade_formation
from .labour_refusals import cash_in_hand_refusal, literate_wall_refusal
from .request_rules import teaching_fee, teaching_hours_refusal, train_request_refusal
from .staff_moves import crosses_literacy_wall
from sim.ledger.api import PayEdge


class Training:
    def __init__(self, world, advice, book, capacity, hours, market, supply, trades):
        self._world = world
        self.advice = advice
        self.book = book
        self.capacity = capacity
        self.hours = hours
        self.market = market
        self.supply = supply
        self.trades = trades

    def found_trade_school(self, trade, seats):
        """Create durable local training capacity for one named trade."""
        if trade not in self._world.trades.wages or not self.trades.trade_available(trade):
            return False, ("the trade must exist before a school can reproduce "
                           "it; teach or discover %s first" % trade)
        seats = float(seats)
        cost = seats * self._world.finance.trade_school_price_per_seat()
        workforce = self._world.workforce
        if seats <= 0 or cost > self._world.finance.balance:
            return False, "cannot afford that trade school"
        self._world.send(PayEdge(self._world.EDGE_WORKERS, cost, "trade schools"))
        schools = workforce.trade_schools
        if schools is None:
            schools = workforce.trade_schools = {}
        schools[trade] = schools.get(trade, 0.0) + seats
        workforce.trades_created.add(trade)
        return True, None

    def training_years_from(self, trade, source):
        """Years to turn a person of `source` into `trade`: the trade's full apprenticeship scaled by the share
        of its tasks the source does not do (trade_formation)."""
        shares = trade_formation.shipped_task_shares()
        uncovered = trade_formation.uncovered_share(shares.get(trade, {}), shares.get(source, {}))
        return trade_formation.training_years(self._full_years(trade), uncovered)

    def uncovered_from(self, trade, source):
        """The share of `trade`'s tasks that people of `source` do not already do."""
        shares = trade_formation.shipped_task_shares()
        return trade_formation.uncovered_share(shares.get(trade, {}), shares.get(source, {}))

    def training_hours_per_person(self, trade, source=None):
        """The teacher's own hours to teach one person `trade` from `source` (default: the nearest practised trade)."""
        source = source or self.source_trade_for(trade)
        if not source:
            return 0.0
        return trade_formation.teacher_hours_per_person(self.training_years_from(trade, source),
                                                        self._world.trades.HOURS_PER_PERSON_YEAR)

    def _full_years(self, trade):
        return float(trade_data.registry_of(self._world).get(trade, {}).get("training_years", 0.0) or 0.0)

    def source_trade_for(self, trade):
        """The trade stated as the teacher in the registry, else the practised trade whose tasks cover the most of
        this one's (ties by id). None when no trade is practised."""
        stated = trade_data.registry_of(self._world).get(trade, {}).get("taught_from")
        if stated:
            return stated
        created = self._world.workforce.trades_created
        present = [other for other in self._world.trades.wages
                   if other != trade and (other not in self._world.trades.trades_absent or other in created)]
        ranked = trade_formation.nearest_sources(trade, trade_formation.shipped_task_shares(), present)
        return ranked[0][1] if ranked else None

    def train_check(self, trade, count, frm=None):
        """Everything `train` and `quote train` agree on before money or hours
        move. Returns (plan, refusal); the plan holds the whole-person count,
        the source trade, the founder hours and the keep paid now."""
        trade = str(trade or "").strip().lower()
        # PEOPLE ARE WHOLE. See the identical check in hire() for why: a
        # taught trade is still a roster of actual people, not a quantity of
        # training-hours, and "0.03 engineers" was exactly as false whichever
        # verb put it there.
        frm, refusal = train_request_refusal(
            trade in self._world.trades.wages, trade, count, lambda: frm or self.source_trade_for(trade),
            lambda source: source in self._world.trades.trades_absent and source not in self._world.workforce.trades_created)
        if refusal:
            return None, refusal
        count = float(round(count))
        # LITERACY BOUNDS TEACHING TOO, and this is where it bites hardest:
        # engineer, chemist, machinist and optician can ONLY be had this way
        # (trade_available refuses to hire them at all), so without this check
        # a founder with enough director-hours and money could teach an
        # unlimited technical staff into a society two per cent of whose
        # people can read. Money and hours are necessary; they were never
        # supposed to be sufficient. See FINDINGS_ROUND2 section Q.
        if trade in self.trades.LITERATE_TRADES:
            cap = self.supply.literate_capacity(trade)
            have = self.book.trade_headcount_pending(trade)
            if crosses_literacy_wall(have, count, cap):
                return None, literate_wall_refusal(trade, cap, have)
        years = self.training_years_from(trade, frm)
        teaching_hours = trade_formation.teacher_hours_per_person(years, self._world.trades.HOURS_PER_PERSON_YEAR) * count
        teacher = self.outside_teacher(trade)
        # another actor holding the knowledge teaches and is paid for their hours; otherwise it is your own
        hours = 0.0 if teacher else teaching_hours
        pool = self.hours.director_pool() - self.hours.director_hours_committed()
        refusal = teaching_hours_refusal(hours, pool, count, trade)
        if refusal:
            return None, refusal
        # THE SAME ROOM `hire` AND `buy` SHARE: household_room exists so all
        # three verbs agree on the same ceiling. `train` must check it too,
        # or a household could teach its way past its actual capacity to
        # feed, house and oversee people, ending up unable to hire the
        # artisans it needs to supervise anything it just taught. People
        # you teach have to be fed, housed and overseen like anybody else.
        room = self.capacity.household_room()
        if count > room:
            whole = int(max(0.0, room))
            advice = self.advice.room_advice()
            return None, Refusal("household_room", "you can feed, house and oversee %.2f more people, "
                                 "and teaching %g would make %g. %s %s"
                                 % (math.floor(max(0.0, room) * 100) / 100.0, count, count,
                                    "Teach %d instead." % whole if whole >= 1
                                    else "There is no room for even one.",
                                    advice), room=max(0.0, room), remedies=advice.facts["remedies"])
        # Teaching pulls the SOURCE trade's people off their own bench for the
        # duration, which is exactly what market_pressure prices for buying
        # slaves and labour market price_factor now prices for hiring: the more of
        # `frm` you have already pulled recently, the dearer feeding the next
        # batch while they learn.
        uncovered = self.uncovered_from(trade, frm)
        # the early slice is paid as staff from its own date, so the source's wages are kept up front only for the rest
        kept_years = trade_first_hands.prepaid_keep_years(years, self._full_years(trade), uncovered)
        fee = teaching_fee(count, self.market.quote_annual(frm), kept_years, teacher, teaching_hours,
                           self._world.trades.HOURS_PER_PERSON_YEAR)      # the source's wages while they learn
        if fee > self._world.finance.spending_power("buy"):
            return None, cash_in_hand_refusal(self._world, 
                "keeping %g %s%s fed while they learn"
                % (count, trade, "" if count == 1 else "s"), fee)
        return {"count": count, "from": frm, "hours": hours, "fee": fee, "years": years, "teacher": teacher,
                      "uncovered": uncovered}, None

    def outside_teacher(self, trade):
        """The first actor other than you that holds the knowledge to teach `trade` (trade_formation.teachers_of),
        or None when you teach it yourself from what you know."""
        by_actor, baseline, demonstrated = self._world.knowledge.teaching_knowledge()
        teachers = trade_formation.teachers_of(trade, trade_formation.shipped_gating_nodes(), by_actor, baseline,
                                               demonstrated)
        named = [teacher for teacher in teachers if teacher in by_actor]
        return named[0] if named else None

    def trainee_wage_bill(self, trade, count):
        """Yearly wage the people taught will add once they join the staff."""
        return count * self.market.quote_annual(trade)

    def train(self, trade, count, frm=None):
        """Teach a trade that does not exist here into existence.

        This is the answer to "there are no machinists in 100 AD". There are
        smiths, and a smith who spends two years with you becomes the first
        machinist in the world. It costs your own hours, which is the scarcest
        thing you have, and it is per-trade: the machinists you made are no use
        at all when you need a chemist.
        """
        trade = str(trade or "").strip().lower()
        plan, refusal = self.train_check(trade, count, frm)
        if refusal:
            return False, refusal
        count, frm, hours, fee, years = plan["count"], plan["from"], plan["hours"], plan["fee"], plan["years"]
        workforce = self._world.workforce
        current_year = self._world.year
        self._world.send(PayEdge(self._world.EDGE_WORKERS, fee, "training fees"))
        workforce.teaching_hours_this_year = (workforce.teaching_hours_this_year or 0.0) + hours
        workforce.trades_created.add(trade)
        rows = trade_first_hands.cohort_rows(
            current_year, trade, float(count), years, self._full_years(trade), plan["uncovered"])
        workforce.training.extend(rows)
        # SAY WHAT IT TOOK: teaching can quietly eat most of a year's
        # founder-hours, with nothing left afterward to supervise what it
        # just cost elsewhere to run - the reply has to report the actual
        # hours and money spent, not just a brief note about when training
        # finishes. Teaching is the most expensive thing you can do with a
        # year.
        _left = max(0.0, self.hours.director_pool() - self.hours.director_hours_committed())
        # WHAT HAS HAPPENED, AND WHAT IS STILL NEEDED - not just the first
        # half: "ready in year N" has to say plainly that they cannot do a
        # day of the work before that year (ready is the year they MATURE,
        # not the year they start), and that core.py adds them to
        # self.household.employees itself the moment they do, automatically
        # - no 'hire' needed to put THESE apprentices to work. Either half
        # missing leaves the other easy to misread.
        return True, ("%g %s%s finish training during %d's annual resolution "
                      "and join your staff automatically immediately afterward "
                      "- no 'hire' needed for them. "
                      "Part of the cohort, the share of the tasks %ss already do, joins sooner (see the education "
                      "screen); before that they cannot do a day of the work. It took "
                      "%s of your own hours (%s left this year) and %s "
                      "to keep them while they learn"
                      % (count, trade, "s" if count != 1 else "", trade_first_hands.year_joined(rows[-1][1]), frm,
                         self._world.plain_number(hours), self._world.plain_number(_left),
                         self._world.money_text(fee, grouped=True)))
