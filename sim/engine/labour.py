"""People: hiring them, teaching them, buying them, paying them.

Split out of simulator.py, which had grown to 5,600 lines. These are
methods of Sim; they are a mixin only so that they can live in a file of
their own. Behaviour is unchanged and verified byte-identical.
"""
import collections, json, math, os, random
from collections import defaultdict

from .data import *          # the shared tables and loaders
from .data import (ANNUAL_WAGE, TRADES_ABSENT, TRADE_NOTES, WAGES, closure, trade_family)


class LabourMixin:
    def _stochastic_round(self, x):
        """Round a continuous headcount target to a whole number of people
        without biasing where it is actually heading.

        PEOPLE ARE WHOLE; THE PATH TOWARD THEM DOES NOT HAVE TO BE. The
        automatic staff-growth in core.py's step() is a smoothing formula -
        this year's target minus what you have, times a rate - and that math
        is exactly what every balance comment near it was tuned against. Had
        it simply rounded the smoothed figure down every year, growth toward
        a ceiling of, say, 6 people from 0 would have sat at 5 forever
        (0.18 of the gap each year, floor()'d, converges just under the next
        whole number and never crosses it): hiring would have quietly gone
        dead a person short of every ceiling in the game. Rounding UP every
        year over-hires just as systematically the other way.
        A fractional remainder is instead spent as THIS YEAR's chance of the
        next whole person: 6.4 people is six for certain and a 40% chance of
        a seventh, drawn from self.rng so it is reproducible. Averaged over
        many years the realised headcount tracks the old fractional
        trajectory exactly, and no single year is ever asked to employ part
        of a person.
        """
        x = max(0.0, x)
        whole = math.floor(x)
        if self.rng.random() < x - whole:
            whole += 1
        return float(whole)

    def director_pool(self):
        h = 0.0
        if self.founder_alive:
            own = self.cfg["founder_hours_per_year"]
            # In bondage most of your hours are owed to somebody else. Not all
            # of them: nobody worked every waking hour, and the evenings are
            # where the work gets done. This is the cost, and it is temporary.
            if self.bondage_years_left > 0:
                own *= 0.25
            h += own
        h += self.directors_extra * self.cfg["director_hours_per_year"]
        return h

    # ---- literacy bounds who you can hire ----------------------------------
    # FINDINGS_ROUND2 section Q: every civ file carries literacy_general and
    # literacy_elite, apply_tech_effects (society.py) raises them when paper,
    # printing, schools and libraries are built, and until now nothing else in
    # the engine ever read either number. A scribe cost the same to hire in a
    # society where two people in a hundred could read as in one where nine
    # could.
    #
    # `scholar` is drawn from the lettered, propertied class - literacy_elite
    # in the civ file, "fraction of the propertied class that can read". The
    # rest - `scribe`, and the trades taught into being from ordinary
    # craftsmen (`engineer`, `chemist`, `machinist`, `optician`) - draw on the
    # wider literacy_general pool of anyone who can read at all. `merchant` is
    # left out on purpose: an agent working on commission is not, in this
    # period, chiefly a reader.
    # electrician was simply left out, and a play tester found the hole: their
    # machinists stopped dead at the literacy ceiling while `train electrician
    # 20` succeeded and handed them twenty-seven. It is a taught trade that
    # reads drawings, exactly like the other four.
    LITERATE_TRADES = frozenset({"scholar", "scribe", "engineer", "chemist",
                                 "machinist", "optician", "electrician"})
    # The literacy this file's trade shares and staff ceilings were already
    # tuned against, before literacy was read anywhere: Rome's own numbers
    # (rome_100ad.json), because every other constant in this economy - price
    # index, cost multipliers - is already calibrated relative to Rome. Below
    # its own reference literacy stays 1.0 and NOTHING changes for Rome; a
    # civilization with less of either number gets a genuinely smaller pool,
    # in proportion, and a civilization with more (Han's elite literacy, 0.95
    # against Rome's 0.9) is not penalised for having read more than Rome did.
    LITERACY_REFERENCE_GENERAL = 0.12   # rome_100ad.json literacy_general
    LITERACY_REFERENCE_ELITE = 0.90     # rome_100ad.json literacy_elite

    def literacy_factor(self, trade):
        """0..1: how much of this trade's usual pool this society's literacy
        can actually fill. 1.0 for anything that is not a literate trade."""
        if trade not in self.LITERATE_TRADES:
            return 1.0
        if trade == "scholar":
            lit, ref = self.civ.get("literacy_elite", 0.0), self.LITERACY_REFERENCE_ELITE
        else:
            lit, ref = self.civ.get("literacy_general", 0.0), self.LITERACY_REFERENCE_GENERAL
        # NOT CLAMPED AT ONE. Rome starts AT the reference, so this returned
        # exactly 1.0 for Rome for ever: printing, movable type, a school and
        # three academies raised literacy_general from 0.12 to 0.27 and moved
        # the specialist ceiling not at all. A play tester watched theirs sit
        # at "5.9 in total, ever, at any price" through all of it and called
        # the whole mechanism dead. It is the one thing the argument for
        # printing rests on: a society that reads more can staff more.
        #
        # Bounded at four, because a lettered pool cannot outgrow the town
        # without the town growing, and because the tech effects that feed it
        # are deliberately small.
        return max(0.0, min(4.0, float(lit) / ref))

    def literate_capacity(self, trade):
        """The most people this society's literacy will EVER let you have in
        this trade, hired and taught combined - a headcount ceiling, not an
        hours one.

        `hire`'s own affordability and supervision checks say nothing about
        whether anyone who can read is available at any price; this is the
        actual wall. Read as people rather than hours, it is the same
        abstracted labour-market scale market_supply() already uses for the
        share a scholar-family trade gets (25,000 hours at full population
        scale, of which a lettered trade gets 35% before literacy narrows it
        further) - not a second population model that has to be kept in step
        with the first, but that one.

        FOR `scholar` ONLY, THIS IS NOT THE WHOLE WALL. A player who typed
        `hire scholar 12` was refused at 5.9, "ever, at any price" - and
        auto_hire, forty years later with the same civilisation, held 146.4
        scholars, because step() smoothed self.scholars toward
        staff_capacity()'s institutional ceiling directly and never once
        called hire() or read this function. Fixing the bypass (see step(),
        core.py) without fixing the number it now has to respect would have
        made the game worse, not better: the goal itself, and two nodes on
        the only road to it, want 25 trained scholars, and the market-share
        formula above tops out at 6.36 even after every literacy technology
        in the tree - printing, paper, a school, three academies - because
        Rome's literacy_elite starts at 0.900 and the field is capped at
        1.0. An eight per cent gain is what "a society that reads more can
        staff more" is worth if reading is the only lever, and it is not:
        the actual reason a household of one can eventually field two dozen
        literate men is that a school, an academy or an imperial patron
        hands them over ALREADY TRAINED, on the institution's own payroll -
        which is exactly what staff_capacity()'s `sc` already computes, and
        already used to justify auto_hire's own math before this function
        capped hire() and train() at a sixth of it. So the wall a person at
        a keyboard is held to is the same market-share pool as before PLUS
        the same institutional pool auto_hire was already trusted to grow
        toward: a city of a million cannot produce twenty-five idle
        scholars for one household to hire off the street, but it can
        certainly produce them once that household has built the school
        that trains them and the network that pays for a second and a
        third. Early game, with no such institution running, this adds
        nothing and the ceiling is exactly what it always was.
        """
        if trade not in self.LITERATE_TRADES:
            return float("inf")
        base = self.cfg["hired_hours_cap_base"] * (0.25 + 0.75 * min(1.0, self.pop_scale))
        people = base * 0.35 / self.HOURS_PER_PERSON_YEAR
        # A FLOOR OF TWO, because the unfloored number said something false.
        # Norse elite literacy is a sixth of Rome's, which took this ceiling to
        # 0.2 people: not "scarce" but "there is no such person in Scandinavia,
        # at any price, ever". That is wrong about the period. Viking-age
        # Scandinavia had runic literacy, rune-carvers who cut inscriptions for
        # hire, merchants who kept reckonings, and from the tenth century
        # priests who read Latin. What it did not have was a POOL - a body of
        # lettered men large enough to staff an institution.
        #
        # So literacy bounds the SCALE of what you can build and not whether a
        # single literate person can be found.
        #
        # ADDED, not a maximum. My first attempt floored this with max(), which
        # fixed the falsehood and broke the mechanism: the floor was larger than
        # anything Norse literacy could reach, so teaching the society to read
        # changed the ceiling not at all, for the one civilisation the mechanism
        # exists to matter for. A floor that swallows the signal is worse than
        # no floor. The rune-carver and the priest are always findable; the POOL
        # on top of them is what literacy buys, and it is what teaching moves.
        cap = 1.5 + people * self.literacy_factor(trade)
        if trade == "scholar":
            # THE SAME POOL auto_hire ALREADY TRUSTED. staff_capacity()'s `sc`
            # is schools, academies, patrons and the industrial cascade that
            # trains scholars outright and carries their keep on the
            # institution's own upkeep (see _grant_staff) - it is not a second,
            # looser estimate of the same thing, it is the number step() was
            # already smoothing self.scholars toward before this function's
            # cap ever got in the way. Zero with no such institution running,
            # which is why a fresh household still sees exactly the
            # market-share figure above and no more.
            cap += self.staff_capacity()[0]
        return cap

    def _literate_wall_refusal(self, trade, cap, have):
        """The refusal hire() and train() give when literate_capacity() bites.

        SAY HOW MANY YOU CAN HAVE, NOT ONLY THAT YOU CANNOT HAVE SIX. A play
        tester asked for six machinists against a ceiling of 5.9, holding
        NONE, and read "will not supply more than 5.9 in total, ever, at any
        price" as being capped out. They stopped asking, and a run sat
        frozen for two hundred years with seventeen million denarii in the
        bank; changing the one number to four started it moving again in
        four. Say the number they should type.

        AND DO NOT BLAME LITERACY FOR A WALL IT DID NOT BUILD. The old text
        read "this society's literacy will not supply more than X" for
        every trade alike, which is a real description of the Norse scribe
        case and a false one of the Rome scholar case: Rome's literacy_elite
        starts at 0.900 against a field capped at 1.0, so literacy itself
        can never move this ceiling by more than about eight per cent,
        while the actual quantity doing the work is hired_hours_cap_base -
        this household's own reach into the labour market - and, for
        scholar, the institutional pool literate_capacity() now folds in
        (see its docstring). Both matter; only one is literacy, and saying
        only "literacy" when the market-reach term is doing most of the
        work is exactly the kind of statement a play tester built a run
        around and lost two centuries to.
        """
        _room = max(0.0, cap - have)
        _whole = int(_room + 1e-9)
        lever = (
            "Building the institutions that train scholars outright - a "
            "school, an academy, an imperial patron - is what actually "
            "moves this number; printing, paper and libraries raise "
            "literacy itself, which by itself is the smaller of the two."
            if trade == "scholar" else
            "Printing, paper, schools and academies widen the pool - they "
            "raise how many people here can read, and this ceiling rises "
            "with it.")
        return ("this household's reach into the labour market for %ss "
                "will not stretch past %.1f in total, hired and taught "
                "together - not \"this society's literacy\" alone, which "
                "only narrows an already-limited reach further - and you "
                "have %.1f already (hired and still being taught). %s %s"
                % (trade, cap, have,
                   ("%d more is the most you can take right now." % _whole)
                   if _whole >= 1 else "There is no room for even one more.",
                   lever))

    def _trade_headcount_pending(self, trade):
        """People already on the books in this trade, plus people already
        being taught into it who are not ready yet - what a fresh hire or a
        fresh training run would be added ON TOP OF."""
        pending = sum(row[3] for row in self.training
                      if len(row) > 2 and row[2] == trade)
        return self.employees.get(trade, 0.0) + pending

    # ---- the market responds to demand, and to supply ----------------------
    # FINDINGS_ROUND2 section R: market_pressure already does this for slaves
    # - buying in bulk bids the price up, it remembers between purchases, and
    # it decays - and nothing else in the economy had an equivalent. This is
    # the labour half: the same saturating idea, extended honestly rather than
    # copied, and self-contained (decayed on READ rather than decremented once
    # a year in step(), which lives in core.py, so nothing outside this file
    # has to know this exists). 0.6x a year, the same rate market_pressure
    # decays at (0.55, near enough) - mostly gone in three years.
    def labour_pressure(self, trade):
        rec = getattr(self, "_labour_pressure", None)
        rec = rec.get(trade) if rec else None
        if not rec:
            return 0.0
        hours, yr = rec
        age = max(0.0, self.year - yr)
        return hours * (0.6 ** age)

    def _add_labour_pressure(self, trade, hours):
        d = getattr(self, "_labour_pressure", None)
        if d is None:
            d = self._labour_pressure = {}
        d[trade] = (self.labour_pressure(trade) + max(0.0, hours), self.year)

    def _labour_price_factor_from(self, pressure, supply):
        """The one curve behind labour_price_factor - split out so a forecast
        can share it exactly rather than recomputing it (see
        labour_price_factor_after_hiring)."""
        supply = max(1.0, supply)
        share = min(1.5, pressure / supply)
        return 1.0 + 0.9 * share * share

    def labour_price_factor(self, trade):
        """What hiring, commissioning or keeping MORE of this trade costs
        beyond the wage table, from how hard you have recently leaned on its
        local supply.

        `market_supply(trade)` is the ceiling: everyone this trade could put
        to work here, including everyone you already employ. Recent pressure
        taken as a share of that ceiling is negligible at a fifth of it and
        roughly doubles the price at the whole of it - the same curve
        `material_price_factor` uses for the same reason. Because the ceiling
        itself grows when you teach the trade a bigger workforce, or when an
        institution or literacy widens it, the SAME recent pressure buys a
        smaller premium once the supply behind it is bigger: teaching fifty
        machinists is what makes hiring the fifty-first one cheap again, not
        merely possible.
        """
        return self._labour_price_factor_from(self.labour_pressure(trade),
                                               self.market_supply(trade))

    def labour_price_factor_after_hiring(self, trade, n=1.0):
        """What labour_price_factor(trade) becomes the INSTANT you hire n
        more - not the market as it stands, the hire you are contemplating.

        This is the number `hire` itself effectively charges from the moment
        the new people are on the books (see wage_bill, which applies the
        CURRENT labour_price_factor to every head of a trade, not only the
        newest one): a Norse player was quoted "a year of one: 525" for a
        scholar, hired one, and the standing wage bill came to 847.92 - 61%
        more - because that one hire pushed labour_price_factor for scholars
        from 1.0 to 1.615 against a near-empty local supply. The quote and
        the bill were never inconsistent; the quote just priced the market
        as it stood, one command before the player's own action moved it.

        Genuinely simulates the hire rather than re-deriving market_supply's
        formula a second time (which differs for a taught-only trade): adds
        n to employees[trade], reads the real market_supply(trade) back, and
        undoes the change. labour_pressure needs no such trick - it is a
        running total, not a function of current headcount - so n more
        hours are simply added to it, exactly as _add_labour_pressure would.
        """
        n = max(0.0, n)
        if n <= 0:
            return self.labour_price_factor(trade)
        add_hours = n * self.HOURS_PER_PERSON_YEAR
        before = self.employees.get(trade, 0.0)
        self.employees[trade] = before + n
        try:
            supply_after = self.market_supply(trade)
        finally:
            if before:
                self.employees[trade] = before
            else:
                self.employees.pop(trade, None)
        pressure_after = self.labour_pressure(trade) + add_hours
        return self._labour_price_factor_from(pressure_after, supply_after)

    # What each of these adds to the CEILING on people, taken from
    # staff_capacity below so the advice and the arithmetic cannot drift apart.
    ROOM_SOURCES = (
        ("workshop_first", 6), ("freedman_staff", 10), ("school_founded", 12),
        ("patron_senatorial", 6), ("endowment_land", 8), ("patron_imperial", 50),
        ("academy_network", 50), ("interchangeable_parts", 40),
        ("crucible_steel", 12), ("blast_furnace", 15),
        ("telegraph_electric", 25), ("steam_high_pressure", 45),
        # met_open_hearth_furnace, NOT "bessemer_openhearth" - same stale id
        # STAFF_CAPACITY_SOURCES carried below until it was corrected there;
        # this second table was not updated in the same pass, so `k in
        # self.nodes` silently dropped it from every piece of advice this
        # function gives and the sixty-five places an open-hearth furnace is
        # actually worth (see staff_capacity(), which DOES use the right id)
        # were never once offered as a reason to build or reopen one.
        ("met_open_hearth_furnace", 65), ("railway", 95), ("power_grid", 130),
    )
    # fin_trial_balance, fin_company_town and fin_chain_store - the
    # organisation entries added alongside STAFF_CAPACITY_SOURCES above - are
    # deliberately NOT in ROOM_SOURCES, even though every one of them raises
    # the same ceiling every other entry here does. _room_advice's own
    # "nearest first" sort (below) ranks by CLOSURE SIZE, a proxy that holds
    # for the furnace-and-patronage tree above because a shallow node there
    # is also a cheap one. It does not hold for the finance branch: the whole
    # point of fin_chain_store's own note ("requires sophisticated management
    # and accounting") is that it is a late, expensive, 30,000-denarii
    # institution sitting only two prerequisites deep (fin_market ->
    # fin_department_store), so ranking it by closure size alone told a
    # founder with four hundred denarii in year 100 that the NEAREST way to
    # more room was a chain of department stores - a measured, not a
    # theoretical, failure of this heuristic once a second branch of the
    # tree with a different shape is let into it. The institutions
    # themselves are real (STAFF_CAPACITY_SOURCES, supervision_room); this
    # one piece of advice text is not worth teaching the sort to weigh cost
    # as well as depth for three nodes, so they are simply left unnamed here
    # - a player who builds them (for their own revenue, or for the
    # household room staff_capacity() already credits them with) still gets
    # the room; this function just never tells them to go build one.

    def _room_advice(self):
        """What raises the CEILING on people, which is not what buys people.

        The household-room refusal handed back _staff_advice, which names
        hiring, commissioning and buying - every one of which needs room you do
        not have. A play tester ran into a ceiling of 166.9 against a node
        wanting 200 craftsmen and wrote that none of the three remedies the
        game's own message suggests works. They were right: the room comes from
        institutions and heavy industry, and nothing pointed at those.
        """
        # A CLOSED ROOM SOURCE IS NOT A MISSING ONE. staff_capacity() already
        # drops a source's places the moment its venture is not running (see
        # STAFF_CAPACITY_SOURCES's must_be_running), and the advice below used
        # to filter only on `k not in self.done` - so a school built, then
        # shut for want of a supervisor, vanished from this text entirely: not
        # counted (correctly), and never named as the cheapest way back,
        # either. A player who hit the ceiling it had been holding up was
        # told to build endowment_land or court an imperial patron instead of
        # simply reopening what they already owned.
        reopen = [(k, add) for k, add in self.ROOM_SOURCES
                  if k in self.done and k in self.nodes and k not in self.operating
                  and self.is_venture(k)]
        reopen.sort(key=lambda kv: -kv[1])
        want = [(k, add) for k, add in self.ROOM_SOURCES
                if k not in self.done and k in self.nodes
                and self.is_visible(k)]
        # NEAREST FIRST, and nearest means how much of the tree stands between
        # you and it. Sorted on size alone this offered power_grid (+130) to a
        # founder with six places - the last node in the game, true and
        # useless - while workshop_first, one prerequisite away, went unnamed.
        def _distance(k):
            return len(closure(self.nodes, k) - self.done)
        want.sort(key=lambda kv: (_distance(kv[0]), -kv[1]))
        _reopen_bit = (
            ("you already have %s, shut: reopening %s is cheaper than "
             "building anything else. "
             % (" and ".join("%s (+%d)" % (k, a) for k, a in reopen[:2]),
                "it" if len(reopen) == 1 else "them"))
            if reopen else "")
        if not want:
            if reopen:
                return ("Room is not bought, it is built - or in this case, "
                        "reopened: %s'open %s'."
                        % (_reopen_bit, reopen[0][0]))
            return ("Room comes from institutions and heavy industry, and you "
                    "have every one of them this society offers; what is left "
                    "grows on its own as they run.")
        _now = [(k, a) for k, a in want if self.start_reason(k)[0]]
        return ("Room is not bought, it is built: %s%s. Each is somewhere for "
                "people to work and somebody to oversee them.%s"
                % (_reopen_bit,
                   "; ".join("%s (+%d places)" % (k, a) for k, a in want[:3]),
                   "" if _now else " None is startable today; they are listed "
                                   "nearest first, so the first is what to work "
                                   "towards."))

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
    STAFF_CAPACITY_SOURCES = (
        ("workshop_first",         0.0,   6.0, 0.0, True,  True),
        ("freedman_staff",         0.0,  10.0, 0.0, True,  True),
        ("school_founded",        12.0,  12.0, 2.0, True,  True),
        ("collegium_licensed",     3.0,   0.0, 0.0, True,  True),
        ("patron_senatorial",      4.0,   6.0, 0.0, False, True),
        ("patron_imperial",       14.0,  50.0, 2.0, False, True),
        ("endowment_land",         6.0,   8.0, 1.0, False, True),
        ("academy_network",       40.0,  50.0, 6.0, True,  True),
        ("corpus_dispersed",       8.0,   0.0, 1.0, False, True),
        ("interchangeable_parts",  4.0,  40.0, 0.0, False, True),
        ("crucible_steel",         0.0,  12.0, 0.0, False, True),
        ("blast_furnace",          0.0,  15.0, 0.0, False, True),
        ("telegraph_electric",     6.0,  25.0, 0.0, False, True),
        ("steam_high_pressure",    0.0,  45.0, 0.0, False, True),
        # met_open_hearth_furnace, NOT "bessemer_openhearth", which is the id
        # this line carried for as long as it existed and which is not in the
        # tree: self.has() of a node that does not exist is False for ever, so
        # the sixty-five artisans the late game's biggest single training step
        # was supposed to hand over were never handed over once.
        ("met_open_hearth_furnace", 6.0,  65.0, 0.0, False, False),
        ("railway",                8.0,  95.0, 0.0, False, True),
        ("power_grid",            45.0, 130.0, 6.0, False, True),
        # ORGANISATION, NOT INDUSTRY: the same question - "how many more
        # people can this household feed, house and oversee" - answered by
        # the tech tree's own finance/organisation branch
        # (data/branches/40_finance_institutions.json) instead of by a
        # furnace. A player asked to play as Walmart or Amazon, and every
        # wall they actually hit (see literate_capacity, household_room,
        # buy_slaves) is this one: supervision and housing, never market
        # depth. Rome and Han's own dice-free trials already reach several
        # thousand employees on the INDUSTRIAL entries above alone (see this
        # commit's own measurement); what they have never been given credit
        # for needing is the organisational technology history actually used
        # to run a household that big - books honest enough that a manager
        # far from you cannot simply lie about what he did with your money,
        # tied housing, and a network of branches in other towns. These
        # nodes already sit in the tree, already cost founder-hours and
        # denarii to build, and until now did nothing but sit there.
        #
        # fin_societas ("Partnership... Legally recognised, but partners
        # remain personally liable") is deliberately NOT here despite being
        # the most obvious "share the watching" node in the branch: Rome's
        # own civilisation file grants it for free in year one
        # (starting_techs, rome_100ad.json), so any effect hung on it would
        # not be a choice a founder makes, it would be a silent day-one
        # buff to every single Rome run, dice-free included - exactly the
        # "materially faster" failure this project's own brief warns
        # against, and it was CAUGHT this way: a regression test expecting
        # a fresh sim's director pool at exactly 2,000 hours read 2,216
        # after one step with a one-line version of this entry that gave
        # fin_societas a director. No other node touched here is a starting
        # grant for any of the five civilisations (checked by hand against
        # every civ file's own starting_techs).
        #
        # fin_trial_balance, the top of fin_double_entry -> fin_ledger ->
        # fin_trial_balance: "the foundation of trust between owner and
        # manager across distance. Without it, the manager can simply lie."
        # That sentence is the entire argument for why a Roman household
        # could field a deputy who runs a concern the founder never visits -
        # this is the accounting, not a bigger market, so it buys clerks
        # (ar) and deputies (di), never scholars or the ceiling on craftsmen
        # a furnace trains.
        # fin_societas ("Partnership between two or more parties to share
        # profits and losses. Legally recognised, but partners remain
        # personally liable") IS here, and the reasoning that kept it out was
        # wrong. It was left unwired because Rome grants it in starting_techs
        # and so any effect would be "a silent day-one buff to every Rome run,
        # not a player choice". But a starting grant is not a bug to be
        # routed around, it is the whole mechanism by which these five
        # civilisations differ from one another: Rome is the only one of the
        # five whose own file hands it over, and Rome beginning with a legally
        # recognised partnership form while a Norse or Mexica founder must
        # build one is exactly the asymmetry the starting_techs list exists to
        # express. The real fault in a silent buff is the silence, not the
        # buff, so this is attributed wherever capacity is attributed.
        #
        # fin_societas is NOT in this table, though it was tried here first.
        # A director in this table is a trained deputy who can run something
        # the founder never visits, and fin_trial_balance below is the node
        # whose own note argues for exactly that ("the foundation of trust
        # between owner and manager across distance. Without it, the manager
        # can simply lie"). A partner is a different thing: somebody beside
        # you sharing the watching, not somebody you can trust at a distance,
        # and the tree already distinguishes the two. So the partnership's
        # effect lives in supervision_room() instead, where it reads as "one
        # more capable person to oversee with" rather than as a deputy the
        # accounting has not yet been invented to supervise.
        ("fin_trial_balance",      0.0,   4.0, 2.0, False, False),
        # fin_company_town ("Employer provides housing, food, and goods to
        # workers... Highly profitable but politically dangerous"): the
        # housing half of "feed, house and oversee" bought outright, at the
        # going concern's own cost (it runs at a loss on the books, like a
        # school, which is why it belongs in CAPABILITY_INSTITUTIONS rather
        # than being shed as an ordinary mistake - see economy.py).
        ("fin_company_town",       0.0,  20.0, 0.0, False, True),
        # fin_chain_store ("operates identical stores in multiple cities,
        # buying centrally and selling retail in each location... requires
        # sophisticated management and accounting"): REACH, named in the
        # tree's own words. One household drawing on one town is the whole
        # of the household-room wall this section answers; a second unit of
        # this is a second city's worth of the same organisation, which is
        # exactly what SCALABLE_INSTITUTIONS/institution_units already means
        # for a second school "built across town" - here it is a second town,
        # not a second schoolroom. Its branch managers are the `di` term:
        # layers of supervision a founder's own two thousand hours a year
        # could never provide alone.
        ("fin_chain_store",        0.0,  30.0, 4.0, True,  True),
    )

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
        sc = ar = di = 0.0
        # A SECOND SCHOOL TRAINS A SECOND SCHOOL'S WORTH OF SCHOLARS. Linear in
        # institution_units, which is 1.0 for a run that never founds more than
        # the original single unit - exactly the constants below, unchanged -
        # and the actual capacity a further unit buys otherwise. The COST of
        # each further unit is where the diminishing return lives (see
        # ProjectsMixin.institution_unit_cost); this is simply how big the
        # place you paid for actually is.
        # STAFF_CAPACITY_SOURCES is the whole list, in one place, because the
        # planner needs to read it too. A plan built from the tech tree alone
        # cannot see any of this: nothing in the goal's prerequisite closure
        # mentions a school, so a purely structural plan walked into
        # quantum_solidstate_theory's demand for eight trained scholars with a
        # society that tops out at 5.9 of them and sat there until the horizon
        # ran out. The list had to stop being an if-chain only this function
        # could read before the planner could be taught to build the school.
        for key, _sc, _ar, _di, scaled, must_run in self.STAFF_CAPACITY_SOURCES:
            if not (self.running(key) if must_run else self.has(key)):
                continue
            u = self.institution_units(key) if scaled else 1.0
            sc += _sc * u
            ar += _ar * u
            di += _di * u
        # LITERACY BOUNDS THE SCHOLAR CEILING. A school, an academy or an
        # imperial patron can only produce as many scholars as this society
        # has literate, propertied people to draw them from (literacy_factor
        # reads literacy_elite for "scholar"; see FINDINGS_ROUND2 section Q).
        # Below Rome's own literacy_elite (0.9, the number every one of the
        # figures above was already tuned against) this narrows the pool;
        # printing, schools and libraries raise literacy_elite
        # (apply_tech_effects, society.py) and widen it again as a run goes
        # on, which is the entire point of building them.
        sc *= self.literacy_factor("scholar")
        # you cannot keep staff you cannot pay
        # a famous school attracts students and patrons it did not have to pay for
        # WAGES ARE A REAL CHARGE NOW (see wage_bill), so this ceiling is no
        # longer "what you could pay for": it is what you can pay for WITHOUT
        # eating the surplus you need in order to build anything. The first
        # version of the explicit wage bill hired to the old affordability
        # ceiling and the household then consumed the entire surplus: revenue
        # 32,000, upkeep 17,000, wages 12,000, and exactly nothing left to spend
        # on the work, for two centuries. A programme whose payroll is its whole
        # income is not a programme.
        #
        # SPARE USED TO BE revenue() MINUS UPKEEP() ALONE, which is the upkeep of
        # BUILT WORKS and says nothing about living_cost - rent, appearances, tax
        # and (via wage_bill) the staff you ALREADY carry. On turn one, with 400
        # denarii, 232/yr of income and a 230/yr household, that left "spare"
        # reading a healthy 267 while the true surplus was 3.5. auto_hire spent
        # against the healthy number, not the true one. Subtracting living_cost
        # here is what "what you can pay for" has to mean if it is to mean
        # anything: money already going to rent and to people you already
        # employ is not there to hire more people with.
        spare = max(0.0, (self.revenue() - self.upkeep() - self.living_cost())
                    * self.rep_factor() + max(0.0, self.capital) * 0.06)
        budget = spare * 0.40
        afford = budget / (420.0 * self.price_index * self.wage_index)
        # EXTRA is supervision_room(), the headroom auto_hire adds on top of
        # this institutional ceiling (see step(), section 1). It used to be
        # added with no affordability check of its own at all - this ceiling's
        # `scale` only ever throttled sc/ar, which are BOTH ZERO before you
        # have built a workshop or a school, so the extra six-person headroom
        # went through at full strength regardless of income. A tester's turn
        # one hired 1.32 artisans and 0.38 scholars on 400 denarii and a net
        # income of 3.5/yr, taking living cost to 699.9 and capital to -688.
        # Folding extra into the SAME denominator this ceiling is scaled
        # against is what makes "grow the staff toward what you can house and
        # pay" true of the headroom hiring and not just the institutional kind.
        extra = self.supervision_room()
        # NO FLOOR. This read max(0.10, ...), so a household with no surplus at
        # all still hired a tenth of its headroom - about 0.6 craftsmen, some
        # 250 a year in wages, against a net income of 3.5. A break tester
        # turned auto_hire on, did nothing else whatever, and was in debt
        # bondage ten steps later. The whole careful affordability calculation
        # above was undone by the floor beneath it: "grow the staff toward what
        # you can house and pay" has to be able to mean nobody.
        scale = min(1.0, afford / max(1.0, sc + ar + extra * 1.35))
        self._staff_scale = scale     # step() applies this to `extra` too
        # A civilization of 1.5 million simply cannot field the trained people a
        # civilization of 65 million can, however rich you are. This is the single
        # biggest structural difference between playing Rome and playing Norway.
        # Softened after a first pass made every small civilization fail outright.
        # A 4.5 million person society CAN eventually staff a semiconductor
        # programme, it just has to grow into it. Making that impossible was a
        # modelling error, not a finding.
        pop = 0.45 + 0.55 * min(1.0, self.pop_scale ** 0.35)
        return (base_sc + sc * scale * pop, base_ar + ar * scale * pop,
                di * min(1.0, scale * 1.3) * pop)

    def supervision_room(self):
        """People you can direct and pay BEYOND what your institutions train.

        staff_capacity is a ceiling on what a school, a workshop and a patron
        produce and support. It is not a ceiling on how many men you can hire
        off the street, which is limited by money and by the market. Conflating
        the two put a hard wall across the Norse run: it needed thirty craftsmen
        for interchangeable parts against an institutional ceiling of 27.6, and
        a society of a million and a half could never cross the gap however rich
        it got. The old model cleared it by handing every founder four artisans
        on arrival, which is the thing a tester objected to and which I removed;
        this is the honest version of the same headroom. You hire them, you pay
        them every year, and you can only supervise so many.
        """
        room = 6.0 + 14.0 * self.directors_extra
        if self.running("workshop_first"):
            room += 6.0 * self.institution_units("workshop_first")
        if self.running("school_founded"):
            room += 10.0 * self.institution_units("school_founded")
        if self.running("academy_network"):
            room += 30.0 * self.institution_units("academy_network")
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
        if self.running("fin_chain_store"):
            room += 20.0 * self.institution_units("fin_chain_store")
        # A PARTNER IS NOT ON YOUR PAYROLL, which is why a partnership belongs
        # in this headroom and not only in the institutional ceiling above.
        # (Headroom, not a free staff: hiring INTO it is still scaled by what
        # the household can afford - see _staff_scale in hired_room - so this
        # raises how many people a founder may oversee, never how many they
        # can pay for.) fin_societas is the tree's own "share profits and
        # losses... partners remain personally liable": a partner brings their
        # own capital and their own attention, so the household can oversee
        # more people without first being able to afford to pay for the
        # oversight. Gating it on what the founder can pay would model a hired
        # manager, which is a different node.
        #
        # has(), not running(): fin_societas has neither revenue nor upkeep
        # (see ProjectsMixin's CAPABILITY_INSTITUTIONS comment), so it can
        # never be "opened" and a running() test would make it dead for ever.
        #
        # 4.0 against the founder's own 6.0 above: a partner is a capable
        # person sharing the burden, not a second founder. Rome begins with
        # this and no other civilisation does (starting_techs, rome_100ad.json),
        # so a Roman household oversees 10 people in year one where a Norse
        # one oversees 6 and must build the partnership to catch up. That
        # asymmetry is the point of the starting_techs list, not a side effect
        # of it to be routed around.
        if self.has("fin_societas"):
            room += 4.0
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
        rows = [{"source": "yourself", "people": 6.0,
                 "what_it_is": "what one person can keep an eye on"}]
        if self.directors_extra > 0.005:
            rows.append({"source": "your deputies", "people":
                         round(14.0 * self.directors_extra, 2),
                         "what_it_is": "people you have trained to direct work"})
        for key, per, words in (
                ("workshop_first", 6.0, "a place of your own to work in"),
                ("school_founded", 10.0, "a school, and the people it keeps"),
                ("academy_network", 30.0, "an academy network"),
                ("fin_chain_store", 20.0, "branches in other towns")):
            if self.running(key):
                rows.append({"source": key,
                             "people": round(per * self.institution_units(key), 2),
                             "what_it_is": words})
        if self.has("fin_societas"):
            rows.append({"source": "fin_societas", "people": 4.0,
                         "what_it_is": "a partner who shares the watching, and "
                                       "whose own capital and attention are not "
                                       "on your payroll"})
        return rows

    def hired_cap(self):
        # a civilization of 1.5 million cannot staff what one of 65 million can
        cap = self.cfg["hired_hours_cap_base"] * (0.25 + 0.75 * min(1.0, self.pop_scale))
        # 1.0 + (mult - 1.0) * sqrt(units): exactly the old `cap *= mult` at
        # units 1.0 (a run that never expands sees the identical multiplier),
        # and SQRT rather than linear beyond that - because these multipliers
        # already compound with one another (a school, an academy and a
        # freedman staff open together and their factors multiply), and a
        # break tester's Rome run climbed school_founded to 8.85 units and
        # academy_network to 8.75 on the back of literacy growth alone, which
        # at a linear rate would have multiplied hired_cap by roughly 9 x 13
        # from these two terms alone. Diminishing returns belong on what a
        # place trains, same as they already do on what it costs to found
        # (institution_unit_cost) - a second school teaches nearly as many
        # more people as the first did; a ninth does not teach nine times as
        # many as one did.
        if self.running("school_founded"):
            cap *= 1.0 + 1.0 * self.institution_units("school_founded") ** 0.5
        if self.running("freedman_staff"):
            cap *= 1.0 + 0.5 * self.institution_units("freedman_staff") ** 0.5
        if self.running("patron_imperial"):   cap *= 3.0
        if self.running("academy_network"):
            cap *= 1.0 + 1.5 * self.institution_units("academy_network") ** 0.5
        if self.running("interchangeable_parts"): cap *= 1.5
        return cap

    # ---- how a SOCIETY reacts to a TECHNOLOGY -------------------------------
    STATE_WEIGHTS = {"infrastructure":0.5, "food":0.7, "medical":0.5,
                     "luxury":0.1, "spectacle":0.1, "inexplicable":0.0,
                     "status_threatening":-0.6, "weapon_democratising":-0.5}

    def _staff_advice(self, kind):
        """Name the remedy, not just the shortfall - and only remedies you could
        actually have heard of.

        This advice told a tester to "build workshop_first" for ten years while
        `why workshop_first` replied "you have never heard of that", from the
        same program in the same second. They called it the single most confusing
        thing in the game and they were right. Hiring is always sayable, because
        the labour market is in front of you; a named institution is not, until
        it is.
        """
        bits = []
        for node, why in self.STAFF_SOURCES.get(kind, []):
            if node in ("BUY", "HIRE"):
                bits.append(why)
            # CLOSED IS NOT MISSING. market_supply() only applies a source's
            # multiplier via running(node), so a school built and then shut
            # for want of a supervisor stops widening the hiring pool exactly
            # as if it had never been built - and this advice, filtering on
            # `node not in self.done`, fell silent about it rather than
            # naming the actual remedy. Reopening costs a supervisor, not a
            # second institution; say that first.
            elif node in self.done and node not in self.operating and self.is_venture(node):
                bits.append("reopen %s ('open %s') - you already built this; "
                            "it is only shut" % (node, node))
            elif node not in self.done and self.is_visible(node):
                # NOT A CIRCLE. `why workshop_first` says it is blocked for want
                # of artisans, and the advice on how to get artisans said "build
                # workshop_first (you need somewhere for them to work)" - a play
                # tester quoted the two lines against each other. If the remedy
                # is itself waiting on the very thing it is meant to supply,
                # naming it is worse than saying nothing: say what it is waiting
                # on instead, so the reader knows which end to start at.
                # Asked DIRECTLY of the node's own requirement, never through
                # start_reason - which calls this function, so the obvious
                # version of this test recurses until the stack gives out.
                _n = self.nodes[node]
                _short = (_n["art"] > self.artisans + 1e-9 if kind == "artisans"
                          else _n["sch"] > self.effective_scholars() + 1e-9)
                if _short:
                    bits.append("build %s eventually (%s) - but it is itself "
                                "waiting on %s, so hire or commission first"
                                % (node, why, kind))
                else:
                    bits.append("build %s (%s)" % (node, why))
        if not bits:
            return "wait: your existing institutions add %s each year." % kind
        return "To get more %s: %s." % (kind, "; ".join(bits[:3]))

    def work_for_wages(self, trade, hours):
        """Do a job. For money. Like everybody else.

        The reviewer asked for this and it is a fair gap: you could hire a smith,
        a glassblower or a farmer all day long and had no way to BE one. A
        founder with no capital and a useful pair of hands should be able to earn
        a wage, and at the start it is one of the few things he can do.

        It is paid at the ordinary rate for that trade, which is the same table
        the game charges you when you hire someone, so there is no arbitrage in
        either direction. The cost is your own hours, which are the one resource
        nothing else can buy, so this is always a trade of time for money and
        usually a bad one once you have anything better to do. That is the
        honest shape of wage labour.
        """
        if not self.founder_alive:
            return 0.0, ("there is nobody left to do the work: these are YOUR "
                         "hours, and the founder is dead. What you built goes "
                         "on; you do not.")
        w = WAGES.get(trade)
        if w is None:
            here = sorted(t for t in WAGES if self.trade_available(t))
            return 0.0, ("no such trade. you could work as: " + ", ".join(here))
        # A TRADE NOBODY HERE PRACTISES IS A TRADE NOBODY HERE WILL PAY YOU FOR.
        # A break tester earned wages as a chemist, an electrician and an
        # engineer in 1500 Tenochtitlan, in the same session where `hire` had
        # just refused all three ("there are no chemists to hire in this society
        # at any price") and `labour` listed them under do_not_exist_here. The
        # gate existed; this one command simply never applied it, and its own
        # "no such trade" whitelist named the full civilisation-agnostic roster,
        # which is what told the tester those jobs were available in the first
        # place.
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
        # EVERY HOUR ALREADY SPOKEN FOR, not just the ones sold for wages.
        # director_hours_committed() has counted teaching as well as wage work
        # since the "free second year inside every year" bug, and this line
        # never used it: `train machinist 2` plus `train chemist 2` reported
        # 200 hours left and `work smith 2000` was then accepted, for 3,800
        # hours spent in a 2,000-hour year. A break tester found it in a
        # session where the same counter refused them correctly in the other
        # direction, which is what made it obvious it was one-way.
        left = self.director_pool() - self.director_hours_committed()
        if hours > left:
            return 0.0, ("you have %.0f of your own hours left this year, not %.0f"
                         % (max(0.0, left), hours))
        # Your own labour is worth the trade rate: the SAME rate the game charges
        # you to employ somebody in that trade, which is the point. It used to be
        # billed from the hourly column while hiring was billed from the annual
        # one, and those two columns disagree by about half, so a founder could
        # work as a scholar for 1,416 a year and hire one for 625. The docstring
        # claimed "there is no arbitrage in either direction" while the arithmetic
        # ran a 2.3x spread.
        rate = ANNUAL_WAGE.get(trade, 375.0) / self.HOURS_PER_PERSON_YEAR
        pay = (hours * rate * self.price_index * self.wage_index
               * (1.0 + min(0.5, self.reputation / 200.0)))
        before_practice = self.revenue()
        self.capital += pay
        self.wage_hours_this_year = getattr(self, "wage_hours_this_year", 0.0) + hours
        self.wages_earned = getattr(self, "wages_earned", 0.0) + pay
        # SAY WHEN IT IS A BAD TRADE. Selling your hours costs you the practice
        # those same hours were running (see practice_attention), and for a
        # physician it is usually a loss: a tester measured a full year of
        # labour at 66 denarii against a 227 cost of living, and it switched
        # off 259 a year of practice. That is realistic - a trained man does
        # not dig ditches for preference - but the game charged it silently and
        # the player had to work it out from the ledger.
        # DO NOT BLOCK IT - WARN ABOUT IT. Selling hours is a legitimate way to
        # dig out of debt, and this command already lets a player sell every
        # one of them; the missing part, found the same way by both a Norse
        # and a Han playtester, was that nothing said so. One watched a
        # project sit at "waiting on: your hours" for turn after turn with no
        # explanation while they kept working all 2,000 hours a year; the
        # other worked out the fix - work (2000 - hours the project still
        # wants) - only by noticing the stuck percentage and reasoning
        # backward, and asked for exactly this: "have work either warn you if
        # you are about to starve your own active project of its last hours,
        # or show remaining-hours-needed somewhere more prominent." Computed
        # from project_hour_pace/active_hours_still_wanted (projects.py), the
        # same formula step() itself uses to hand out the pool, so this can
        # never warn about a shortfall step() would not also produce.
        _starve = None
        _wanted = self.active_hours_still_wanted()
        if _wanted:
            _after = max(0.0, self.director_pool() - self.director_hours_committed())
            _short = {kk: vv for kk, vv in _wanted.items() if vv > _after + 0.5}
            if _short:
                _named = sorted(_short.items(), key=lambda kv: -kv[1])[:2]
                _more = len(_short) - len(_named)
                _bits = ["%s (wants about %.0f more of your hours this year)"
                        % (kk, vv) for kk, vv in _named]
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
        lost = before_practice - self.revenue()
        if lost > pay:
            # THE THREE NUMBERS HAVE TO SUBTRACT. Rounding each separately gave
            # "you earned 128 ... was worth 234 ... so this cost you 105", and
            # a break tester did the subtraction. Round first, then subtract.
            _p, _l = round(pay), round(lost)
            _msg = ("you earned %s, and the practice those hours were "
                    "running was worth %s a year - so this cost you %s. "
                    "Wage work is for when you have no practice to lose."
                    % ("{:,.0f}".format(_p), "{:,.0f}".format(_l),
                       "{:,.0f}".format(_l - _p)))
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

        Recently having leaned hard on a trade's local supply (labour_price_factor)
        shows up here too, not only in the fee `hire` charged to bring someone
        on: a town that just watched you take on half its smiths pays every
        smith more for a few years, yours included, until the pressure decays
        or the supply of smiths genuinely grows.
        """
        total = 0.0
        for t, n in self.employees.items():
            total += n * ANNUAL_WAGE.get(t, 375.0) * self.wage_index * self.labour_price_factor(t)
        return total * self.price_index

    def effective_scholars(self):
        """You are your own natural philosopher; everyone else is hired."""
        return self.scholars + (1.0 if self.founder_alive else 0.0)

    def trade_available(self, t):
        """Can this trade be had here at all, at any price?

        Rome has masons and plumbers in abundance and no machinists whatever.
        An absent trade is not expensive, it is absent, and the only way to have
        one is to teach somebody the trade yourself.
        """
        if t not in TRADES_ABSENT:
            return True
        return t in self.trades_created

    def _trade_market_class(self, t):
        """Which reachable-labour-pool class a trade falls in - read ONCE,
        here, so market_supply's own hiring ceiling and
        national_trade_population's country-wide estimate (used by the
        'population' command) cannot say two different things about the
        same trade. See TRADE_DENSITY for what each class is worth, and
        why, and TOWN_POPULATION_REFERENCE for the town size it is a
        fraction OF.

        Unchanged in substance from the keyword/list check this replaced;
        only pulled out to one place instead of being reasoned about twice.
        """
        note = TRADE_NOTES.get(t, "").lower()
        if "abundance" in note or "abundant" in note or "numerous" in note:
            return "abundant"
        if "scarcest" in note:
            return "scarce"
        if trade_family(t) == "scholar":
            return "scholar"
        if t in ("labourer", "artisan", "carpenter", "mason", "potter", "smith",
                 "sailor", "miner", "furnaceman"):
            return "common"
        return "uncommon"          # glassblowers, engravers, opticians' forebears

    # A PLAYER HIRED FIVE BLACKSMITHS AND WATCHED THE STANDING WAGE JUMP.
    # Measured on the pre-fix build: market_supply("smith") was 22,500 hours -
    # 11.25 people - because hired_hours_cap_base (data.py) is 25,000 hours
    # "at full population scale", by its own comment, "what a provincial
    # town's labour market can actually supply", and smith's old share of it
    # was 0.9. Nothing in the game ever said "town"; rome_100ad.json says
    # population 65,000,000 and urban_fraction 0.12 - about 7,800,000 town
    # dwellers - so a player reasonably read "11.25 smiths" as a claim about
    # the Roman Empire's entire smithing capacity, and it is an absurd claim
    # at that scale.
    #
    # THE PLAYER IS RIGHT ABOUT THE SYMPTOM AND WRONG ABOUT ONE MECHANISM.
    # Hiring five smiths where thousands exist should barely move the price;
    # the old pool made it move a lot, because the pool was sized for a
    # hamlet. Buying ten slaves is a DIFFERENT wall - household_room, this
    # household's own capacity to feed, house and supervise people, checked
    # in hire() below and nothing to do with market_supply - and is correctly
    # left alone: a household of one cannot run ten slaves without somewhere
    # to put them, in any economy, however deep its labour market runs.
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
    TOWN_POPULATION_REFERENCE = 50000.0

    # What SHARE of that town plies each class of trade - feeding BOTH
    # market_supply's ceiling for 'abundant' and 'common' (the classes the
    # break report was actually about) and national_trade_population's
    # country-wide estimate for every class. 'scarce', 'uncommon' and
    # 'scholar' keep their PRE-EXISTING, separately-tuned hiring ceilings
    # below (0.08 x base, 0.25 x base, and the literacy-bound 0.35 x base
    # literate_capacity's own docstring explains at length) - this fix
    # targets the trades that were wrongly sharp, not the ones that are
    # correctly so, and changing a density entry for those three classes
    # moves only what 'population' reports the COUNTRY holds, never this
    # household's hiring cap or the regression coverage tuned against it
    # (FINDINGS_ROUND2 section R's millwright checks, literate_capacity's
    # own scholar-ceiling checks).
    #
    #   common:    anchored directly on the Ostia figure above.
    #   abundant:  the trades the wage table's OWN notes call abundant or
    #              numerous (mason, plumber, sailor) - set higher again,
    #              matching the stronger language, still no more than an
    #              order of magnitude's worth of judgement on top of a real
    #              attestation.
    #   uncommon, scarce: NO COMPARABLE FIGURE FOUND for engraver,
    #              glassblower, master (uncommon) or for millwright, which
    #              its own note already calls "the scarcest useful trade
    #              you can hire" (scarce). These two are honest
    #              order-of-magnitude placeholders for the population
    #              report only, smaller than an attested trade and smaller
    #              again for the one the game already singles out as
    #              rarest - not research, and said so here rather than
    #              dressed up as data.
    TRADE_DENSITY = {
        "abundant": 0.014,
        "common": 0.007,
        "uncommon": 0.001,
        "scarce": 0.00015,
    }
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
    SCHOLAR_ENGAGEMENT_FRACTION = 0.002   # of literacy_elite x population
    SCRIBE_ENGAGEMENT_FRACTION = 0.05     # of literacy_general x population
    MERCHANT_DENSITY = 0.004              # of urban population, like a craft

    def market_supply(self, t):
        """Hours a year of this trade the local labour market can actually supply.

        THIS IS ONE TOWN'S MARKET, NOT THE COUNTRY'S - the household this
        game puts you in charge of draws on one town's labour, the way a
        real Roman, Han or Norse founder would have. See
        TOWN_POPULATION_REFERENCE's own comment for why that is a
        defensible modelling choice and TRADE_DENSITY for how big 'one
        town's worth' of each trade actually is; national_trade_population
        answers the country-wide question this number is not trying to.
        """
        if not self.trade_available(t):
            return 0.0
        base = self.cfg["hired_hours_cap_base"] * (0.25 + 0.75 * min(1.0, self.pop_scale))
        if t in TRADES_ABSENT:
            # Only the people you taught, plus the ones they have taught since.
            return self.employees.get(t, 0.0) * self.HOURS_PER_PERSON_YEAR * 1.5
        cls = self._trade_market_class(t)
        if cls in ("abundant", "common"):
            # A REAL TOWN'S WORTH, not base's village-sized share of it (see
            # this function's own docstring and the comment above
            # TOWN_POPULATION_REFERENCE for the full account and its
            # citation).
            town = self.TOWN_POPULATION_REFERENCE * (0.25 + 0.75 * min(1.0, self.pop_scale))
            cap = town * self.TRADE_DENSITY[cls] * self.HOURS_PER_PERSON_YEAR
        elif cls == "scholar":
            cap = base * 0.35          # literate men are a small fraction of anywhere
        elif cls == "scarce":
            cap = base * 0.08
        else:
            cap = base * 0.25          # uncommon: glassblowers, engravers, masters
        if self.running("school_founded"):
            cap *= 1.0 + 1.0 * self.institution_units("school_founded") ** 0.5
        if self.running("patron_imperial"):       cap *= 3.0
        if self.running("academy_network"):
            cap *= 1.0 + 1.5 * self.institution_units("academy_network") ** 0.5
        if self.running("interchangeable_parts"): cap *= 1.5
        # A trade that needs reading cannot be bought past how many people
        # here can read (FINDINGS_ROUND2 section Q). scholar and scribe are
        # the only literate trades that reach this branch - the taught ones
        # (engineer, chemist, machinist, optician) are all in TRADES_ABSENT
        # and returned above, bounded instead by literate_capacity() in
        # train().
        if t in self.LITERATE_TRADES:
            cap *= self.literacy_factor(t)
        return cap + self.employees.get(t, 0.0) * self.HOURS_PER_PERSON_YEAR

    def reachable_trade_population(self, t):
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
        if t in ("scholar", "scribe"):
            return self.literate_capacity(t)
        return self.market_supply(t) / self.HOURS_PER_PERSON_YEAR

    def national_trade_population(self, t):
        """A rough ESTIMATE of how many people ply this trade across the
        WHOLE COUNTRY - not this household's reach (reachable_trade_
        population, above) and not a second population model: the same
        TRADE_DENSITY this file's own market_supply reads, applied to the
        country's urban population instead of to one town, because a
        craft trade is overwhelmingly a town trade (see civ['urban_
        fraction'], which core.py already reads for pop_scale). 0.0 for a
        trade that does not exist in this society at all - trade_
        available() already says so.

        Every number this returns is explicitly an estimate and the
        'population' command says so on the screen; nobody has published a
        trade-by-trade occupational census of Rome, Han China or Viking-age
        Scandinavia, and TRADE_DENSITY's own comment already says, for two
        of its four classes, that no comparable figure was found at all.
        """
        if not self.trade_available(t):
            return 0.0
        pop = float(self.civ.get("population", 0.0))
        urban = pop * float(self.civ.get("urban_fraction", 0.0))
        if t == "scholar":
            return pop * float(self.civ.get("literacy_elite", 0.0)) * self.SCHOLAR_ENGAGEMENT_FRACTION
        if t == "scribe":
            return pop * float(self.civ.get("literacy_general", 0.0)) * self.SCRIBE_ENGAGEMENT_FRACTION
        if t == "merchant":
            return urban * self.MERCHANT_DENSITY
        if t in TRADES_ABSENT:
            # engineer, chemist, machinist, optician, electrician: taught
            # into existence by you alone (trade_available already checked
            # this is now true), so "the country's" population of the trade
            # IS what you have taught - there is no wider pool to estimate.
            return self.employees.get(t, 0.0)
        return urban * self.TRADE_DENSITY.get(self._trade_market_class(t), 0.0)

    def home_town_population_estimate(self):
        """How big the single town TOWN_POPULATION_REFERENCE represents
        actually is for THIS civilisation, at its current pop_scale - the
        number the 'population' command shows next to the country's own,
        so a player can see "one household, one town" for themselves
        instead of inferring it from a refusal. An estimate, said as one:
        this engine has no named city for the founder to stand in, only
        the abstraction hired_hours_cap_base and this constant already
        are (see TOWN_POPULATION_REFERENCE's own comment).
        """
        return self.TOWN_POPULATION_REFERENCE * (0.25 + 0.75 * min(1.0, self.pop_scale))

    def population_report(self):
        """Everything the 'population' command (protocol.py) shows, worked
        out here rather than in the command layer: the country's own
        numbers (population, urban_fraction - already loaded for
        pop_scale, see core.py), the size of the one town this household
        actually reaches, and - per trade - the three-way comparison that
        is the whole point of this command: how many exist in the
        country, how many are within reach, how many you employ, and what
        share of the reachable pool that is.

        A PLAYER ASKED FOR THIS DIRECTLY, and it dissolves most of the
        "the labour market is the size of a village" complaint by itself:
        "market can supply 22,500 hours" (the old number) says nothing
        about whether that is most of the trade or a rounding error
        against it. This says both, next to each other, once.
        """
        pop = float(self.civ.get("population", 0.0))
        urban_frac = float(self.civ.get("urban_fraction", 0.0))
        trades = []
        for t in sorted(WAGES):
            national = self.national_trade_population(t)
            reach = self.reachable_trade_population(t) if self.trade_available(t) else 0.0
            have = self.employees.get(t, 0.0)
            trades.append({
                "trade": t,
                "exists_here": self.trade_available(t),
                "estimated_in_the_country": round(national, 1),
                "within_your_reach": round(reach, 2),
                "you_employ": round(have, 2),
                "share_of_the_reachable_pool_you_employ":
                    round(have / reach, 4) if reach > 1e-9 else None,
            })
        return {
            "civilisation": self.civ.get("name", self.civ.get("id", "")),
            "population": round(pop),
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
                "see labour.py's TRADE_DENSITY for what is cited and what is a "
                "placeholder. Buying people (a slave, a freedman) is bounded "
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

    # ---- a technology can make the SAME worker do more, without replacing
    # them ------------------------------------------------------------------
    # THE SECOND QUESTION: before this, nothing in the engine let a
    # technology raise output per worker while leaving the workforce itself
    # untouched. Everything market_supply() and labour_pressure() model is
    # about how many HOURS a trade can supply and what hiring more of them
    # costs; nothing ever asked an hour, once bought, to be worth more than
    # any other hour of the same trade. A flying shuttle does not hire a
    # second weaver or replace the first one - the tree's own note on
    # tex_flying_shuttle says so ("one weaver now handles wide looms...
    # triples weaving speed"). That is a real technology this engine had no
    # way to represent.
    #
    # WIRED TO NODES THAT ARE ALREADY IN THE TREE, each cited from its own
    # note, not invented for this. Deliberately conservative and deliberately
    # narrow: only nodes whose own note describes making an existing trade's
    # hour do more work, not nodes that reduce how many people are needed
    # (that is automation, and the tree already has a separate, correctly
    # different mechanism for it - see tex_power_loom in commodities.py,
    # which raises national cloth OUTPUT, not weaver PRODUCTIVITY, and is
    # deliberately left out of this table). The bonus for each node is a
    # fraction of what its own note claims, because these numbers compound
    # with one another and with everything else in the economy, and a
    # technology tree with forty of these stacked at face value would make
    # the whole game about which order you build them in rather than what
    # they cost.
    #
    # (node, trade, bonus). Sourced, node by node:
    #   tex_treadle_loom    "speeds weaving noticeably" - the weakest claim in
    #                       the chain (the note itself says the weaver still
    #                       works the shuttle by hand), so the smallest bonus.
    #   tex_flying_shuttle  "triples weaving speed" - but weaving is a slice
    #                       of what the `artisan` trade covers in this model
    #                       (there is no dedicated weaver trade), so the
    #                       tripling is scaled down hard rather than applied
    #                       to the whole trade.
    #   tex_spinning_wheel  "roughly tripling output per spinner" - same
    #                       dilution reasoning as the shuttle.
    #   met_trip_hammer     "much faster than hand hammering... foundation of
    #                       heavy forge work" - smith.
    #   met_water_ore_stamp "crush ore... far faster than hand crushing" -
    #                       miner, who does the crushing this replaces.
    #   met_three_high_mill "doubles throughput" of a rolling mill - smith.
    #   met_converter_furnace "speed and low labour cost per ton is the
    #                       payoff" - furnaceman.
    #   bellows_water_blown "the single highest-leverage mechanical change
    #                       available... continuous high-volume blast" - the
    #                       user's own example of a non-automating speed-up;
    #                       furnaceman.
    #   mfg_rake_clearance  "saves 30 percent power and doubles tool life" -
    #                       machinist.
    #   mfg_hss_development "cuts three times faster than Mushet steel" - the
    #                       most direct per-hour claim of the set; machinist.
    #   prc_capstan_turret_lathe "unskilled operator can repeat production" -
    #                       still an operator, still a machinist, just a much
    #                       faster one per hour; machinist.
    LABOUR_PRODUCTIVITY_SOURCES = (
        ("tex_treadle_loom", "artisan", 0.03),
        ("tex_flying_shuttle", "artisan", 0.06),
        ("tex_spinning_wheel", "artisan", 0.05),
        ("met_trip_hammer", "smith", 0.08),
        ("met_water_ore_stamp", "miner", 0.08),
        ("met_three_high_mill", "smith", 0.10),
        ("met_converter_furnace", "furnaceman", 0.08),
        ("bellows_water_blown", "furnaceman", 0.10),
        ("mfg_rake_clearance", "machinist", 0.06),
        ("mfg_hss_development", "machinist", 0.15),
        ("prc_capstan_turret_lathe", "machinist", 0.10),
    )
    # NEVER MORE THAN HALF AGAIN, however many of the above a run has built.
    # Every other saturating multiplier in this file (labour_price_factor,
    # literacy_factor) is capped for the same reason: an uncapped sum of
    # small, individually-defensible bonuses is still an uncapped sum, and
    # this compounds with hired_cap, market_supply's own institutional
    # multipliers, and the project pacing built on top of both.
    LABOUR_PRODUCTIVITY_CAP = 1.5

    def labour_productivity(self, trade):
        """How much MORE a real hour of this trade is worth this year, from
        technology that makes the worker faster rather than replacing them.

        1.0 with nothing built (an hour is an hour, exactly the old
        behaviour). Multiplies the HOURS a project can draw, in
        hours_you_can_call_on - not market_supply, and not the wage bill: the
        workforce is not bigger and is not paid differently, it simply gets
        more done. See LABOUR_PRODUCTIVITY_SOURCES for what is wired in and
        why each figure is what it is.
        """
        bonus = 0.0
        for node, tr, add in self.LABOUR_PRODUCTIVITY_SOURCES:
            if tr == trade and node in self.done:
                bonus += add
        return min(self.LABOUR_PRODUCTIVITY_CAP, 1.0 + bonus)

    def hours_you_can_call_on(self, t):
        """Hours of this trade a project can actually draw on this year.

        COMMISSIONED HOURS ARE PART OF THE CEILING, NOT ON TOP OF IT. Three
        places told a break tester the town could field 8,750 scribe-hours a
        year; commissioning the full 8,750 on top of the standing pool then let
        a 10,000-hour project finish, making the real ceiling 17,500 and every
        one of those three statements false. A commission buys a job from
        somebody else's shop - it is the same scribes. What it really buys is
        certainty: hours reserved for your work rather than competed for.
        """
        # TWO CHANNELS, AND BOTH HAVE TO BE SAID. Hiring draws on the people
        # who live here, and that pool is what market_supply bounds. A
        # commission is a job placed with somebody else's shop, and a shop
        # subcontracts: it is a second channel, dearer per hour, bounded in
        # turn by what the local trade can spare (see commission()).
        #
        # A break tester found this stated as one ceiling of 8,750 in three
        # places while the real one was 17,500, and then - when the two were
        # collapsed into one - found that commissioning bought byte-identical
        # progress and was pointless. Neither is right. Two channels, each
        # bounded, each named wherever the number is printed.
        #
        # PRODUCTIVITY MULTIPLIES THE RESULT, NOT market_supply ITSELF. This
        # is what turns "the same crew gets more done" into "the market can
        # supply more people" if it were applied upstream instead - the wall
        # a project's labour draw actually runs into is how much WORK gets
        # out of the hours it can call on, which is this number, not how
        # many people the town could in principle hire (market_supply, still
        # unchanged, still governs hiring capacity and labour_price_factor).
        return ((self.market_supply(t) + self.contract_hours.get(t, 0.0))
                * self.labour_productivity(t))

    def hours_reserved(self, t):
        """Hours of this trade you have already bought from an outside shop."""
        return self.contract_hours.get(t, 0.0)

    def market_supply_split(self, t):
        """(the town's hours, your own people's hours). Same total, said honestly.

        market_supply is hours of this trade AVAILABLE TO YOU, which includes
        your own staff - so `labour trade smith` reported "market can supply
        22,500 hours", then 24,500 after hiring one smith, and a break tester
        reasonably filed it as taking smiths out of the market making more
        smith-hours available. The arithmetic was right and the label was
        wrong: the town's share had not moved at all.
        """
        mine = self.employees.get(t, 0.0) * self.HOURS_PER_PERSON_YEAR
        total = self.market_supply(t)
        if t in TRADES_ABSENT:
            # There is no market in these at all; every hour is somebody you
            # taught, or somebody they taught.
            return 0.0, total
        return max(0.0, total - mine), mine

    def _cash_in_hand_refusal(self, what, fee):
        """Refuse a wage, an apprentice's keep, or a job's fee for want of
        cash - and say WHY it is refused outright rather than borrowed, which
        `start` would be allowed to do for the identical shortfall.

        This is deliberate, not an oversight: spending_power's own docstring
        (economy.py) explains it - a lender advances against work already
        under way, which is what starting a project can point to. A payroll,
        an apprentice's keep, or a one-off commission fee is money that is
        simply spent the moment it changes hands, with nothing left to
        repossess, so none of the three may draw more than half the credit
        line, where a project may draw the whole of it. An England player hit
        this mid-crisis and called it arbitrary because the refusal never
        said so - it only ever showed capital, never the reason or the room
        that WAS there. One message for hire, train and commission, so the
        three cannot drift apart from each other or from this reasoning.
        """
        room = self.spending_power("buy")
        return ("%s costs %s denarii, due now - not on credit past half your "
                "line. You have %s in hand and could raise about %s more of "
                "your credit line for this (not all of it: a lender funds "
                "work already under way, which is what starting a project "
                "can point to; a wage, an apprentice's keep or a commission "
                "fee is money simply spent, and nothing stands behind that "
                "the way a half-built project does). You are %s short."
                % (what, "{:,.0f}".format(fee), "{:,.0f}".format(self.capital),
                   "{:,.0f}".format(max(0.0, room)),
                   "{:,.0f}".format(max(0.0, fee - room))))

    def hire(self, trade, n):
        """Take someone onto the staff permanently. They are paid every year."""
        trade = str(trade or "").strip().lower()
        if trade not in WAGES:
            return False, ("no such trade: %s. Trades: %s"
                           % (trade, ", ".join(sorted(WAGES))))
        if isinstance(n, str) or isinstance(n, bool):
            # `buy` and `start` both type-check and `hire` did not, so "5"
            # walked straight in where 5 was meant.
            return False, "n must be a number, not %r" % (n,)
        if n <= 0:
            return False, "n must be greater than zero. Nothing was changed."
        # PEOPLE ARE WHOLE. A household can want a third of another artisan's
        # worth of work, and it can buy that in hours (`commission`); it
        # cannot put a third of a person on the payroll, and the engine used
        # to let it, silently, which is how a play tester ended up reading
        # "0.03 engineers" on their own staff roster - a household drawing
        # wages for somebody who could not supervise anything because there
        # was no such person. See core.py step() for the matching fix to
        # attrition, which used to manufacture the same fractions going the
        # other way.
        if abs(n - round(n)) > 1e-6:
            return False, ("you hire whole people, not %g of one. Hire %d or %d."
                           % (n, math.floor(n), math.ceil(n)))
        n = float(round(n))
        if not self.trade_available(trade):
            return False, ("there are no %ss to hire in this society at any price: %s "
                           'Teach one: {"cmd":"train","trade":"%s","n":1}'
                           % (trade, TRADE_NOTES.get(trade, ""), trade))
        # LITERACY IS A WALL, NOT A COST. Money buys the finder's fee below;
        # it cannot buy people who do not exist. See FINDINGS_ROUND2 section
        # Q and literate_capacity()'s docstring.
        if trade in self.LITERATE_TRADES:
            cap = self.literate_capacity(trade)
            have = self._trade_headcount_pending(trade)
            if have + n > cap + 1e-6:
                return False, self._literate_wall_refusal(trade, cap, have)
        # A finder's fee and the first year in advance, which is what a household
        # actually pays to take a skilled man off someone else's bench. Buying
        # deep into a trade's LOCAL supply bids its price up, the same
        # principle market_pressure already applies to slaves (see
        # labour_price_factor for why it is not a one-way ratchet: teaching
        # or hiring your way to a bigger supply of the trade brings the price
        # back down).
        _lpf_now = self.labour_price_factor(trade)
        fee = (n * ANNUAL_WAGE.get(trade, 375.0) * self.wage_index * self.price_index
              * _lpf_now)
        if fee > self.spending_power("buy"):
            _msg = self._cash_in_hand_refusal(
                "hiring %g %s%s" % (n, trade, "" if n == 1 else "s"), fee)
            # SAY WHOSE MARKET THIS IS, where the player actually feels it.
            # A premium this big is the market saying "you have leaned hard
            # on the %ss THIS HOUSEHOLD CAN REACH" - one town's worth, not a
            # claim about the whole country - and a refusal that does not
            # say so reads as a statement about the Roman Empire's entire
            # smithing capacity, which is the exact confusion 'population'
            # exists to head off.
            if _lpf_now > 1.05:
                _msg += (" Part of that is the standing wage itself: leaning "
                         "on the %ss within this household's reach - one "
                         "town's labour market, not the whole country - has "
                         "pushed the going rate up %d%%; the population "
                         "command shows how big that reach actually is."
                         % (trade, round((_lpf_now - 1.0) * 100)))
            return False, _msg
        room = self.household_room()
        if n > room:
            # TRUNCATED, NOT ROUNDED, and it says what a whole number of people
            # would be. A weird-play tester was refused `hire artisan 7` and
            # told "you can supervise, house and teach 7.0 more people, not 7",
            # which is a refusal that reads as a contradiction: the room was
            # 6.96 and the %.1f rounded it up. A figure a player is meant to act
            # on must never be rounded in the direction that overstates it.
            room = max(0.0, room)
            whole = int(room)
            return False, ("you can supervise, house and teach %.2f more people, "
                           "not %g%s. %s"
                           % (math.floor(room * 100) / 100.0, n,
                              " - %d is the most whole people you can take" % whole
                              if whole else " - you have no room for even one",
                              self._room_advice()))
        self.capital -= fee
        # CARRIED FORWARD, so the next step does not bill the same year twice.
        # See step() 2, where it is netted off living_cost.
        self.wages_prepaid = getattr(self, "wages_prepaid", 0.0) + fee
        self.employees[trade] = self.employees.get(trade, 0.0) + float(n)
        self._add_labour_pressure(trade, float(n) * self.HOURS_PER_PERSON_YEAR)
        self._resync_pools()
        # SAY HOW MANY, AND HOW MANY YOU NOW HAVE. This returned None, so the
        # only thing a player saw was "hired: scholar" - no number. A play
        # tester asked for eight, and did not discover for twenty years that
        # they had one, by which time half the tree was refusing them for want
        # of two trained scholars. A verb that takes a quantity has to report
        # the quantity.
        return True, ("%g %s%s taken on for %s denarii (a finder's fee and the "
                      "first year in advance). You now have %.1f, and %.2f "
                      "household place(s) left"
                      % (n, trade, "" if n == 1 else "s",
                         "{:,.0f}".format(fee), self.employees[trade],
                         max(0.0, self.household_room())))

    def fire(self, trade, n):
        """Let staff go. Their wages stop; so does what they were doing.

        AND IT CANCELS AN APPRENTICESHIP. `auto_train` nearly ended a play
        tester's run: it started engineers, chemists AND machinists at 781 a
        year each against 1,005 of revenue, and turning the policy off did not
        stop what was already in flight - four more people they never asked for
        arrived over the next two years and the wage bill reached 2,491. There
        was no command anywhere that could stop them. Dismissing a trade you
        are still teaching is the obvious reading of `fire`, and it is the
        missing lever: what you paid to feed them while they learned is spent,
        the way any abandoned work is, and they do not arrive.
        """
        trade = str(trade or "").strip().lower()
        have = self.employees.get(trade, 0.0)
        pending = sum(r[3] for r in self.training
                      if len(r) > 3 and r[2] == trade)
        if have <= 0 and pending <= 0:
            return False, "you employ no %ss, and none are being taught" % trade
        n = float(n)
        # THE SAME WHOLENESS hire() AND train() NOW ENFORCE. Letting a
        # fraction of a person go is the mirror image of hiring one, and
        # would reopen the exact hole this file's other two verbs were just
        # closed for: a roster that can drift back to "0.03 engineers"
        # through `fire` even though nothing can hire or teach its way there
        # any more. Rounded rather than refused, because "let go 2.5" has an
        # obvious meaning (two, or the two-point-something you actually
        # have) and refusing outright would only make a player retype it.
        if have > 0 and abs(n - round(n)) > 1e-6 and n < have:
            n = float(math.ceil(n))
        note = None
        if have > 0:
            gone = min(n, have)
            self.employees[trade] = have - gone
            if self.employees[trade] <= 1e-9:
                self.employees.pop(trade)
            n -= gone
            note = "let %g %s%s go" % (gone, trade, "s" if gone != 1 else "")
        if n > 0 and pending > 0:
            stopped, still = 0.0, []
            for r in self.training:
                if len(r) > 3 and r[2] == trade and n > 0:
                    take = min(n, r[3])
                    r[3] -= take
                    n -= take
                    stopped += take
                if len(r) <= 3 or r[3] > 1e-9:
                    still.append(r)
            self.training = still
            if stopped > 0:
                note = ((note + "; " if note else "")
                        + "stopped teaching %g more (what you paid to keep them "
                          "while they learned is gone)" % stopped)
        self._resync_pools()
        return True, note

    def train(self, trade, n, frm=None):
        """Teach a trade that does not exist here into existence.

        This is the answer to "there are no machinists in 100 AD". There are
        smiths, and a smith who spends two years with you becomes the first
        machinist in the world. It costs your own hours, which is the scarcest
        thing you have, and it is per-trade: the machinists you made are no use
        at all when you need a chemist.
        """
        trade = str(trade or "").strip().lower()
        if trade not in WAGES:
            return False, "no such trade: %s" % trade
        if n <= 0:
            return False, "n must be greater than zero. Nothing was changed."
        # PEOPLE ARE WHOLE. See the identical check in hire() for why: a
        # taught trade is still a roster of actual people, not a quantity of
        # training-hours, and "0.03 engineers" was exactly as false whichever
        # verb put it there.
        if abs(n - round(n)) > 1e-6:
            return False, ("you teach whole people, not %g of one. Teach %d or %d."
                           % (n, math.floor(n), math.ceil(n)))
        n = float(round(n))
        frm = (frm or ("smith" if trade in ("machinist", "engineer")
                       else "glassblower" if trade == "optician"
                       else "scribe" if trade == "chemist"
                       else "smith")).strip().lower()
        if frm in TRADES_ABSENT and frm not in self.trades_created:
            return False, "you cannot teach from %ss; there are none" % frm
        # LITERACY BOUNDS TEACHING TOO, and this is where it bites hardest:
        # engineer, chemist, machinist and optician can ONLY be had this way
        # (trade_available refuses to hire them at all), so without this check
        # a founder with enough director-hours and money could teach an
        # unlimited technical staff into a society two per cent of whose
        # people can read. Money and hours are necessary; they were never
        # supposed to be sufficient. See FINDINGS_ROUND2 section Q.
        if trade in self.LITERATE_TRADES:
            cap = self.literate_capacity(trade)
            have = self._trade_headcount_pending(trade)
            if have + n > cap + 1e-6:
                return False, self._literate_wall_refusal(trade, cap, have)
        hours = 450.0 * n            # your hours, teaching, per person
        pool = self.director_pool() - self.director_hours_committed()
        if hours > pool:
            return False, ("teaching %g %ss takes %.0f of your own hours and you have "
                           "%.0f uncommitted this year" % (n, trade, hours, max(0.0, pool)))
        # THE SAME ROOM `hire` AND `buy` SHARE. household_room exists because
        # two verbs used different numbers and a tester was told to their face
        # they could take six more people and then took seven with the other
        # one. `train` was the third verb and checked nothing at all, so the
        # optimizer taught its way to a headcount of 26.9 against room for 6 -
        # minus eighteen places - and then could not hire the artisans it
        # needed to supervise anything. People you teach have to be fed, housed
        # and overseen like anybody else.
        room = self.household_room()
        if n > room:
            whole = int(max(0.0, room))
            return False, ("you can feed, house and oversee %.2f more people, "
                           "and teaching %g would make %g. %s %s"
                           % (math.floor(max(0.0, room) * 100) / 100.0, n, n,
                              "Teach %d instead." % whole if whole >= 1
                              else "There is no room for even one.",
                              self._room_advice()))
        # Teaching pulls the SOURCE trade's people off their own bench for the
        # duration, which is exactly what market_pressure prices for buying
        # slaves and labour_price_factor now prices for hiring: the more of
        # `frm` you have already pulled recently, the dearer feeding the next
        # batch while they learn.
        fee = (n * ANNUAL_WAGE.get(frm, 375.0) * 1.2 * self.wage_index * self.price_index
              * self.labour_price_factor(frm))
        if fee > self.spending_power("buy"):
            return False, self._cash_in_hand_refusal(
                "keeping %g %s%s fed while they learn"
                % (n, trade, "" if n == 1 else "s"), fee)
        self.capital -= fee
        self.teaching_hours_this_year = getattr(self, "teaching_hours_this_year", 0.0) + hours
        self.trades_created.add(trade)
        self.training.append([0.0, self.year + 2.0, trade, float(n)])
        self._add_labour_pressure(frm, float(n) * self.HOURS_PER_PERSON_YEAR)
        # SAY WHAT IT TOOK. A play tester's `train machinist 4` quietly ate
        # 1,800 of their 2,000 founder-hours and, with nothing left to
        # supervise with, closed a dozen concerns as a side effect - and the
        # reply was six words about two years' time. Teaching is the most
        # expensive thing you can do with a year and it never said so.
        _left = max(0.0, self.director_pool() - self.director_hours_committed())
        # WHAT HAS HAPPENED, AND WHAT IS STILL NEEDED - not just the first
        # half. A Rome player trained 2 machinists, read "will be ready in
        # 141", and expected them simply to be at work by then; `labour
        # machinist` still read "you employ: 0" at year 141 because they had
        # not yet finished (ready is the year they MATURE, not the year they
        # start). What this never said, in either direction: they cannot do
        # a day of the work before that year, and core.py adds them to
        # self.employees itself the moment they do, automatically - no
        # 'hire' needed to put THESE apprentices to work.
        return True, ("%g %s%s will be ready in %d, and join your staff "
                      "automatically that year - no 'hire' needed for them. "
                      "Until then they cannot do a day of the work. It took "
                      "%s of your own hours (%s left this year) and %s "
                      "denarii to keep them while they learn"
                      % (n, trade, "s" if n != 1 else "", self.year + 2,
                         "{:,.0f}".format(hours), "{:,.0f}".format(_left),
                         "{:,.0f}".format(fee)))

    def auto_commission_for_blocked(self, look=40):
        """Buy the hands for the nearest thing that is blocked ONLY on hands.

        Deliberately narrow. It looks at the front of the priority order, at
        things the goal actually needs, and only acts where craftsmen are the
        single remaining obstacle - not where money, prerequisites, the
        calendar or scholars are. Buying a year of a carpenter to raise a
        workshop is a sensible thing to do; buying labour speculatively is not,
        and this must never become a way to spend a run's savings on nothing.
        """
        # ON CREDIT IF NEED BE. This required money in hand, which is exactly
        # what a household in the hole does not have - and buying a season of
        # somebody's hands is a one-off, not a standing wage, so it is the
        # right instrument for a poor household and the wrong one to forbid
        # them. A Rome run ended at year 800 with 270 technologies, no
        # craftsmen at all and no way to get any: it could not hire (no
        # surplus), could not commission (no cash), so attrition took the last
        # of its staff and it never opened another concern. commission() does
        # its own affordability check against cash AND credit, which is the
        # check that should govern here too.
        if self.spending_power("buy") <= 0:
            return None
        need = getattr(self, "_goal_closure", None)
        if need is None:
            try:
                need = self._goal_closure = closure(self.nodes, self.goal)
            except Exception:
                need = self._goal_closure = set()
        seen = 0
        for k in self.order:
            if seen >= look:
                break
            if k in self.done or k in self.active or k not in need:
                continue
            n = self.nodes[k]
            if any(p not in self.done for p in n["pre"]):
                continue
            seen += 1
            short = n["art"] - self.craft_hands_available()
            if short <= 0 or n["sch"] > self.effective_scholars():
                continue
            hours = short * self.HOURS_PER_PERSON_YEAR
            # The cheapest craft trade this society actually has that can
            # spare the time: a workshop needs hands, not a particular guild.
            best = None
            for t in sorted(WAGES):
                if trade_family(t) != "craft" or not self.trade_available(t):
                    continue
                spare = self.market_supply(t) - self.contract_hours.get(t, 0.0)
                if spare < hours:
                    continue
                if best is None or WAGES[t] < WAGES[best]:
                    best = t
            if best is None:
                continue
            ok, _why = self.commission(best, hours)
            if ok:
                return (k, best, hours)
        return None

    def craft_hands_available(self):
        """Craftsmen you can actually put on a job this year: the ones on your
        own staff, plus the ones whose time you have already bought.

        Hours under contract are people for as long as the contract runs. A
        year of a carpenter's time IS a carpenter, for the purposes of whether
        you can attempt a thing that needs one, and buying a job rather than a
        person is the whole point of `commission`."""
        contracted = sum(h for t, h in getattr(self, "contract_hours", {}).items()
                         if trade_family(t) == "craft")
        # AND YOURSELF. effective_scholars() has always counted the founder as
        # one of the scholars - "you are your own natural philosopher" - and
        # nothing counted them as a pair of hands, though the premise of the
        # whole game is a person who knows how every one of these things is
        # made. The asymmetry had a cost: workshop_first wants two craftsmen,
        # and a Norse run that could field one could never build the place
        # craftsmen work, so it ended six hundred years later with 136
        # technologies and no staff at all.
        own = 1.0 if self.founder_alive else 0.0
        return self.artisans + own + contracted / self.HOURS_PER_PERSON_YEAR

    def commission(self, trade, hours):
        """Pay for a job, not for a person.

        A tester's objection, and a fair one: "maybe you don't want employees,
        you just want some copper wire, and you don't need a full time smith".
        This buys a specific piece of work from somebody else's shop at a
        premium over their wage, with no standing obligation either way.
        """
        trade = str(trade or "").strip().lower()
        if trade not in WAGES:
            return False, "no such trade: %s" % trade
        if hours <= 0:
            return False, "hours must be greater than zero. Nothing was changed."
        if not self.trade_available(trade):
            return False, ("no %s will take the work; the trade does not exist here: %s"
                           % (trade, TRADE_NOTES.get(trade, "")))
        spare = self.market_supply(trade) - self.contract_hours.get(trade, 0.0)
        if hours > spare:
            return False, ("the %ss here can spare %.0f more hours this year, not %.0f"
                           % (trade, max(0.0, spare), hours))
        # A shop charges more for a one-off than it pays its own man for a
        # year, and more again if you are buying deep into what the local
        # market can spare this year (see labour_price_factor).
        fee = (hours * WAGES[trade] * 1.6 * self.wage_index * self.price_index
              * self.labour_price_factor(trade))
        if fee > self.spending_power("buy"):
            return False, self._cash_in_hand_refusal(
                "%.0f hours of a %s" % (hours, trade), fee)
        self.capital -= fee
        self.contract_hours[trade] = self.contract_hours.get(trade, 0.0) + hours
        self.commissioned[trade] = self.commissioned.get(trade, 0.0) + hours
        self._add_labour_pressure(trade, hours)
        return True, ("%.0f hours of a %s bought for %.0f denarii" % (hours, trade, fee))

    def headcount(self):
        return sum(self.employees.values()) + self.slaves + self.freedmen

    def director_hours_committed(self):
        """Hours of your own year already spoken for before any project sees them.

        WAGE HOURS BELONG HERE, and their absence was the worst thing two naive
        testers found. `work` kept its own separate tally, so a founder could
        report "your_hours_left_this_year: 0.0" after a full 2,400 hours of paid
        labour and then complete eight projects worth 2,044 founder-hours in the
        same year. One of them called it "a free second year inside every year"
        and correctly identified it as the dominant strategy in the game. There
        is one year, and one pair of hands.
        """
        return (getattr(self, "teaching_hours_this_year", 0.0)
                + getattr(self, "wage_hours_this_year", 0.0))

    def _grant_staff(self, scholars=0.0, artisans=0.0):
        """An institution hands you people outright, on completion - the
        school's own professors, the freedmen a patron staffs your workshop
        with. They are not on the payroll you can fire (their keep is already
        inside the institution's own upkeep), so they do not belong in
        `self.employees`; they have to survive `_resync_pools()` some other
        way, which is what this records.

        Before this existed, `_complete()` added straight to self.scholars /
        self.artisans, and the very next call to `_resync_pools()` - which
        runs unconditionally every single step() - overwrote both from
        `self.employees` alone and threw the grant away entirely. A player
        who founded the school, in the one mode (`--manual`, which the
        interactive protocol always uses) where nothing else keeps employees
        and the aggregate in step, read the node's own description promising
        "+4 scholars" and then watched a refusal a year later say "needs 2
        trained scholars, you have 1.0" - the pivot node, built and paid for,
        doing nothing at all.
        """
        g = getattr(self, "granted_staff", None)
        if g is None:
            g = self.granted_staff = {"scholars": 0.0, "artisans": 0.0}
        g["scholars"] = g.get("scholars", 0.0) + scholars
        g["artisans"] = g.get("artisans", 0.0) + artisans
        self.scholars += scholars
        self.artisans += artisans

    def _resync_pools(self):
        """Recompute the two aggregate pools the tech tree asks for from the
        actual people on the books. `art` and `sch` in the tree mean "trained
        people who understand your methods", so they are the sum of the trades,
        not a number that floats free of them.

        ONLY `scholar` COUNTS AS A TRAINED SCHOLAR. TRADE_FAMILY groups
        scholar, chemist, engineer, scribe and merchant together as
        "scholar" - and that grouping is real and stays exactly as it is for
        market_supply(), where it means "draws on the same small, literate-
        or-propertied slice of the population", which is equally true of all
        five. It is not the same claim as "is a trained natural philosopher",
        and an earlier version of this function used the one grouping for
        both: hiring three scribes raised effective_scholars() from 0 to
        4.0, so a node gated on "2 trained scholars" would start on the
        strength of scribes who had never been asked to do a philosopher's
        work, while STAFF_SOURCES - the advice this same household is given
        on how to get scholars - names only `hire scholar` and never scribe,
        chemist, engineer or merchant, which is strong evidence the five-way
        grouping was sized for the labour MARKET and reused for the staff
        ROSTER by mistake. train()'s own docstring already makes the
        non-interchangeability of the taught trades explicit ("the
        machinists you made are no use at all when you need a chemist");
        nothing about a chemist makes them a scholar either.

        PLUS WHAT AN INSTITUTION GRANTED OUTRIGHT. See _grant_staff: those
        people are real and already paid for out of the institution's own
        upkeep, and this is the one place that ever told self.scholars and
        self.artisans what they are, so it is the one place that has to add
        the grant back rather than let it be overwritten out of existence.
        """
        craft = sum(n for t, n in self.employees.items() if trade_family(t) == "craft")
        schol = self.employees.get("scholar", 0.0)
        granted = getattr(self, "granted_staff", None) or {}
        # PEOPLE STILL LEARNING ARE NOT YET CRAFTSMEN. Two things were wrong
        # here at once and they cancelled into a disappearance. Everyone bought
        # counted at full worth from the day of purchase, so the training lag
        # that buy_slaves' own docstring promises did nothing; and when a
        # training row finally matured, step() added its capacity to
        # self.artisans - which THIS function then recomputed from scratch and
        # threw away at the next call. A play tester bought and freed people,
        # saw them enter training as a trade named literally `None`, and
        # watched their craftsmen fall from 35 to 3.8 when the training
        # finished. Excluding those still learning makes the lag real and makes
        # the maturation stick, because by then they are simply part of the
        # count below.
        # buy_slaves stores 0.55 of a worker per person bought, so that is the
        # divisor that recovers the headcount still learning.
        learning = sum(row[0] for row in getattr(self, "training", ())
                       if len(row) <= 2) / 0.55
        owned = max(0.0, self.freedmen + self.slaves - learning)
        # Split what is left in the same proportion as what is held.
        held = self.freedmen + self.slaves
        if held > 0:
            free_share = self.freedmen / held
        else:
            free_share = 0.0
        self.artisans = (craft + owned * free_share * 1.0
                         + owned * (1.0 - free_share) * 0.7
                         + granted.get("artisans", 0.0))
        self.scholars = schol + granted.get("scholars", 0.0)

    TRAINING_YEARS = 3.0      # nobody is a useful artisan the week you buy them

    def slave_quote(self, n_people):
        """What buying this many people actually costs, here, today.

        A town's slave market has a depth; buying beyond it bids the price up.
        Flat pricing let a playtester take 3,333 people in one instant at list
        price, which no market of any period would absorb.
        """
        if n_people <= 0:
            return 0.0
        # The surcharge has to remember. My first version priced each CALL by
        # its own size and kept no memory, so a playtester bought 1,000 people
        # in a hundred calls of ten and paid 297 a head instead of 3,868, a
        # thirteenfold discount, with no cap. A market that resets between two
        # purchases made in the same instant is not a market.
        #
        # market_pressure accumulates with every purchase and decays each year
        # as sellers restock, so buying in slices is now priced as one large
        # purchase unless you actually wait between them.
        depth = max(8.0, 40.0 * self.pop_scale ** 0.5)
        # Integrate the rising price ACROSS the purchase instead of applying one
        # surcharge to the whole block. Applying the end-price to every head
        # overcharged a single large call relative to the same number bought in
        # slices, which is why slicing still saved about a fifth. Now the nth
        # head costs what the nth head costs however you group them.
        already = getattr(self, "market_pressure", 0.0)
        n = float(n_people)
        e = 1.85                       # 1 + 0.85
        integral = (((already + n) ** e) - (already ** e)) / (e * (depth ** 0.85))
        return 300.0 * (n + integral) * self.price_index

    def household_room(self):
        """How many more people this household can feed, house and oversee.

        One number, used by `hire` and by `buy` alike. They used different ones
        - which is to say `buy` used none - and a weird-play tester was told to
        their face they could take six more people and then took seven with the
        other verb.
        """
        return (self.staff_capacity()[1] + self.supervision_room()
                - self.headcount())

    def buy_slaves(self, n_people):
        """The option the model refuses to hide, and refuses to make costless.

        Roman labour is cheap because much of it is coerced, and any honest model
        of a Roman enterprise has to let you do this. It is available, it works,
        it is counted separately, and manumission is modelled as strictly better
        on the numbers as well as on every other ground: a freedman is paid, is
        literate, stays, and transmits what he knows.

        A playtester found three separate holes here and they compounded.

        First, buy_slaves added 0.55 artisans per person and manumit then added
        ANOTHER 0.55 for the SAME PERSON, so one human being yielded 1.1 workers.
        Manumission does not clone anybody. It makes the same person work
        properly, which is a rise from 0.55 to 1.0, so it adds 0.45.

        Second, the price was flat at 300 denarii however many you bought, so
        3,333 people could be had in a single instant at list price. No market
        of any period absorbs that. The price now rises with the size of the
        purchase against the local market's depth.

        Third, it was INSTANT. Buy and free ten people and you had eleven
        trained artisans in the same tick, for money alone, with no founder
        hours and no calendar time. That strictly dominated freedman_staff, the
        node that models the same thing honestly at 900 founder hours and two
        years, so the narrated route was always the worse deal. People now
        arrive untrained and become useful over a training lag.
        """
        if n_people <= 0:
            return 0
        # THE SAME ROOM `hire` ENFORCES. A weird-play tester was told to their
        # face that they could supervise, house and teach six more people, and
        # then took seven with a different verb - "buy slaves bypasses the cap
        # that hire enforces". The constraint is about your household's
        # capacity to feed, house and oversee people, and a person you own
        # needs all three exactly as much as a person you pay. More so.
        room = self.household_room()
        if n_people > room:
            self._last_buy_refusal = (
                "you can supervise, house and teach %.2f more people, not %g - "
                "and a person you own needs feeding and housing exactly as much "
                "as one you pay. %s"
                % (max(0.0, room), n_people, self._staff_advice("artisans")))
            return 0
        # A town's slave market has a depth. Buying beyond it bids the price up.
        price = self.slave_quote(n_people)
        if price > self.capital:
            return 0
        self.capital -= price
        self.slaves += n_people
        self.market_pressure = getattr(self, "market_pressure", 0.0) + n_people
        # Untrained on arrival. They become productive through self.training.
        self.training.append([n_people * 0.55, self.year + self.TRAINING_YEARS])
        return n_people

    def manumit(self, n_people):
        n_people = min(n_people, self.slaves)
        if not n_people:
            return 0
        self.slaves -= n_people
        self.freedmen += n_people
        self.manumitted_total += n_people
        # The SAME person, working properly: 0.55 to 1.0, not another whole
        # worker. This was the double count.
        #
        # But only for people who are actually TRAINED. A playtester noticed
        # that freeing someone bought this morning still handed over the 0.45
        # uplift immediately while their 0.55 sat in the training queue, so
        # buy-and-free bought 82 per cent of a trained artisan with no calendar
        # time at all, which is most of the way back to the exploit the training
        # lag was added to close. Freeing an untrained person upgrades what they
        # will be worth WHEN they mature; it does not skip the maturing.
        # The training queue also carries taught-trade rows now (which have a
        # trade name in them and no artisan capacity), so read column 0 by index
        # rather than unpacking a row whose width is no longer fixed.
        in_training = sum(row[0] for row in self.training)
        untrained = min(n_people, int(in_training / 0.55 + 0.5))
        trained_freed = max(0, n_people - untrained)
        self.artisans += trained_freed * 0.45
        if untrained:
            share = untrained / max(1.0, in_training / 0.55)
            for row in self.training:
                row[0] *= 1.0 + 0.45 / 0.55 * min(1.0, share)
        # Manumission was publicly admired, and admiration saturates. The first
        # freedmen you make are a statement; the four hundredth is a payroll.
        # Uncapped, this was a reputation pump that beat taking a patron.
        gain = 0.4 * n_people / (1.0 + self.manumitted_total / 25.0)
        self.reputation += min(gain, 6.0)
        return n_people
