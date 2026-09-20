"""Buying and teaching trades into existence: hiring, firing, teaching,
commissioning, and what a technology does to an hour once bought.

These are methods of Sim; they are a mixin only so that they can live in
a file of their own (see labour.py's own docstring for the split).

hire, fire, train and commission are the four verbs a player actually
types; _cash_in_hand_refusal is the one refusal message all three money-
up-front verbs share, so they cannot drift apart from each other or from
the reasoning behind them. auto_commission_for_blocked and craft_hands_
available are the automated and manual halves of the same question -
buying hands for a project that is blocked only on hands. hours_you_can_
call_on, hours_reserved and market_supply_split turn labour_population.py's
market depth into what a project can actually draw this year, and labour_
productivity (LABOUR_PRODUCTIVITY_SOURCES) is the technology side of that
same hour: what a flying shuttle or a trip hammer makes the SAME worker
worth, without hiring anyone new.
"""
import math

from .data import (TRADES_ABSENT, TRADE_NOTES, WAGES, closure, trade_family)
from sim.constants import declare


class TrainingMixin:
    """Hiring, firing, teaching and commissioning trades, and what a
    technology does to an hour once bought - see this module's own
    docstring for why these verbs and labour_productivity sit together.
    """


    # ---- a technology can make the SAME worker do more, without replacing
    # them ------------------------------------------------------------------
    # THE SECOND QUESTION: everything market_supply() and labour_pressure()
    # model is about how many HOURS a trade can supply and what hiring more
    # of them costs; neither asks an hour, once bought, to be worth more
    # than any other hour of the same trade. A flying shuttle does not hire
    # a second weaver or replace the first one - the tree's own note on
    # tex_flying_shuttle says so ("one weaver now handles wide looms...
    # triples weaving speed"). This is what represents that: a real
    # technology effect the hiring/hours mechanism alone cannot capture.
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
    #                       available... continuous high-volume blast" - a
    #                       non-automating speed-up; furnaceman.
    #   mfg_rake_clearance  "saves 30 percent power and doubles tool life" -
    #                       machinist.
    #   mfg_hss_development "cuts three times faster than Mushet steel" - the
    #                       most direct per-hour claim of the set; machinist.
    #   prc_capstan_turret_lathe "unskilled operator can repeat production" -
    #                       still an operator, still a machinist, just a much
    #                       faster one per hour; machinist.
    _LABOUR_PRODUCTIVITY_WHY = (
        "A fraction of the productivity gain this node's own tree note "
        "claims, diluted because these figures compound with one another "
        "and because the affected trade (e.g. 'artisan') is broader than "
        "the specific task the note describes (e.g. weaving) - see this "
        "table's own long comment above for exactly which note each row "
        "cites and how much it was scaled down. The dilution factor is "
        "tuned judgement, not itself sourced.")
    LABOUR_PRODUCTIVITY_TEX_TREADLE_LOOM = declare(
        "LABOUR_PRODUCTIVITY_TEX_TREADLE_LOOM", 0.03, kind="temporary_heuristic",
        unit="fractional bonus to an artisan-hour's output",
        source="tex_treadle_loom's own tree note: 'speeds weaving "
               "noticeably' (the weakest claim in this table's chain).",
        confidence="D", why=_LABOUR_PRODUCTIVITY_WHY)
    LABOUR_PRODUCTIVITY_TEX_FLYING_SHUTTLE = declare(
        "LABOUR_PRODUCTIVITY_TEX_FLYING_SHUTTLE", 0.06, kind="temporary_heuristic",
        unit="fractional bonus to an artisan-hour's output",
        source="tex_flying_shuttle's own tree note: 'triples weaving "
               "speed'.",
        confidence="D", why=_LABOUR_PRODUCTIVITY_WHY)
    LABOUR_PRODUCTIVITY_TEX_SPINNING_WHEEL = declare(
        "LABOUR_PRODUCTIVITY_TEX_SPINNING_WHEEL", 0.05, kind="temporary_heuristic",
        unit="fractional bonus to an artisan-hour's output",
        source="tex_spinning_wheel's own tree note: 'roughly tripling "
               "output per spinner'.",
        confidence="D", why=_LABOUR_PRODUCTIVITY_WHY)
    LABOUR_PRODUCTIVITY_MET_TRIP_HAMMER = declare(
        "LABOUR_PRODUCTIVITY_MET_TRIP_HAMMER", 0.08, kind="temporary_heuristic",
        unit="fractional bonus to a smith-hour's output",
        source="met_trip_hammer's own tree note: 'much faster than hand "
               "hammering... foundation of heavy forge work'.",
        confidence="D", why=_LABOUR_PRODUCTIVITY_WHY)
    LABOUR_PRODUCTIVITY_MET_WATER_ORE_STAMP = declare(
        "LABOUR_PRODUCTIVITY_MET_WATER_ORE_STAMP", 0.08, kind="temporary_heuristic",
        unit="fractional bonus to a miner-hour's output",
        source="met_water_ore_stamp's own tree note: 'crush ore... far "
               "faster than hand crushing'.",
        confidence="D", why=_LABOUR_PRODUCTIVITY_WHY)
    LABOUR_PRODUCTIVITY_MET_THREE_HIGH_MILL = declare(
        "LABOUR_PRODUCTIVITY_MET_THREE_HIGH_MILL", 0.10, kind="temporary_heuristic",
        unit="fractional bonus to a smith-hour's output",
        source="met_three_high_mill's own tree note: 'doubles throughput' "
               "of a rolling mill.",
        confidence="D", why=_LABOUR_PRODUCTIVITY_WHY)
    LABOUR_PRODUCTIVITY_MET_CONVERTER_FURNACE = declare(
        "LABOUR_PRODUCTIVITY_MET_CONVERTER_FURNACE", 0.08, kind="temporary_heuristic",
        unit="fractional bonus to a furnaceman-hour's output",
        source="met_converter_furnace's own tree note: 'speed and low "
               "labour cost per ton is the payoff'.",
        confidence="D", why=_LABOUR_PRODUCTIVITY_WHY)
    LABOUR_PRODUCTIVITY_BELLOWS_WATER_BLOWN = declare(
        "LABOUR_PRODUCTIVITY_BELLOWS_WATER_BLOWN", 0.10, kind="temporary_heuristic",
        unit="fractional bonus to a furnaceman-hour's output",
        source="bellows_water_blown's own tree note: 'the single "
               "highest-leverage mechanical change available... "
               "continuous high-volume blast'.",
        confidence="D", why=_LABOUR_PRODUCTIVITY_WHY)
    LABOUR_PRODUCTIVITY_MFG_RAKE_CLEARANCE = declare(
        "LABOUR_PRODUCTIVITY_MFG_RAKE_CLEARANCE", 0.06, kind="temporary_heuristic",
        unit="fractional bonus to a machinist-hour's output",
        source="mfg_rake_clearance's own tree note: 'saves 30 percent "
               "power and doubles tool life'.",
        confidence="D", why=_LABOUR_PRODUCTIVITY_WHY)
    LABOUR_PRODUCTIVITY_MFG_HSS_DEVELOPMENT = declare(
        "LABOUR_PRODUCTIVITY_MFG_HSS_DEVELOPMENT", 0.15, kind="temporary_heuristic",
        unit="fractional bonus to a machinist-hour's output",
        source="mfg_hss_development's own tree note: 'cuts three times "
               "faster than Mushet steel' - the most direct per-hour claim "
               "in this table.",
        confidence="D", why=_LABOUR_PRODUCTIVITY_WHY)
    LABOUR_PRODUCTIVITY_PRC_CAPSTAN_TURRET_LATHE = declare(
        "LABOUR_PRODUCTIVITY_PRC_CAPSTAN_TURRET_LATHE", 0.10, kind="temporary_heuristic",
        unit="fractional bonus to a machinist-hour's output",
        source="prc_capstan_turret_lathe's own tree note: 'unskilled "
               "operator can repeat production'.",
        confidence="D", why=_LABOUR_PRODUCTIVITY_WHY)
    LABOUR_PRODUCTIVITY_SOURCES = (
        ("tex_treadle_loom", "artisan", LABOUR_PRODUCTIVITY_TEX_TREADLE_LOOM),
        ("tex_flying_shuttle", "artisan", LABOUR_PRODUCTIVITY_TEX_FLYING_SHUTTLE),
        ("tex_spinning_wheel", "artisan", LABOUR_PRODUCTIVITY_TEX_SPINNING_WHEEL),
        ("met_trip_hammer", "smith", LABOUR_PRODUCTIVITY_MET_TRIP_HAMMER),
        ("met_water_ore_stamp", "miner", LABOUR_PRODUCTIVITY_MET_WATER_ORE_STAMP),
        ("met_three_high_mill", "smith", LABOUR_PRODUCTIVITY_MET_THREE_HIGH_MILL),
        ("met_converter_furnace", "furnaceman", LABOUR_PRODUCTIVITY_MET_CONVERTER_FURNACE),
        ("bellows_water_blown", "furnaceman", LABOUR_PRODUCTIVITY_BELLOWS_WATER_BLOWN),
        ("mfg_rake_clearance", "machinist", LABOUR_PRODUCTIVITY_MFG_RAKE_CLEARANCE),
        ("mfg_hss_development", "machinist", LABOUR_PRODUCTIVITY_MFG_HSS_DEVELOPMENT),
        ("prc_capstan_turret_lathe", "machinist", LABOUR_PRODUCTIVITY_PRC_CAPSTAN_TURRET_LATHE),
    )
    # NEVER MORE THAN HALF AGAIN, however many of the above a run has built.
    # Every other saturating multiplier in this file (labour_price_factor,
    # literacy_factor) is capped for the same reason: an uncapped sum of
    # small, individually-defensible bonuses is still an uncapped sum, and
    # this compounds with hired_cap, market_supply's own institutional
    # multipliers, and the project pacing built on top of both.
    LABOUR_PRODUCTIVITY_CAP = declare(
        "LABOUR_PRODUCTIVITY_CAP", 1.5, kind="temporary_heuristic",
        unit="dimensionless multiplier", source=None, confidence="D",
        why="However many productivity-raising technologies a run has "
            "built, no trade's hour may be worth more than half again its "
            "base value. Every other saturating multiplier in this file "
            "(labour_price_factor, literacy_factor) is capped for the "
            "same reason: an uncapped sum of small, individually-"
            "defensible bonuses is still an uncapped sum, and this "
            "compounds with hired_cap and market_supply's own "
            "institutional multipliers. The cap value itself is tuned, "
            "not derived from any real productivity ceiling.")

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
        projects = self.state.projects
        for node, row_trade, add in self.LABOUR_PRODUCTIVITY_SOURCES:
            if row_trade == trade and node in projects.done:
                bonus += add
        return min(self.LABOUR_PRODUCTIVITY_CAP, 1.0 + bonus)

    def hours_you_can_call_on(self, trade):
        """Hours of this trade a project can actually draw on this year.

        COMMISSIONED HOURS ARE PART OF THE CEILING, NOT ON TOP OF IT: a
        commission buys a job from somebody else's shop, but it is the same
        scribes drawing on the same local pool market_supply already
        bounds, not a second pool stacked on top of it. What it really buys
        is certainty: hours reserved for your work rather than competed
        for.
        """
        # TWO CHANNELS, AND BOTH HAVE TO BE SAID. Hiring draws on the people
        # who live here, and that pool is what market_supply bounds. A
        # commission is a job placed with somebody else's shop, and a shop
        # subcontracts: it is a second channel, dearer per hour, bounded in
        # turn by what the local trade can spare (see commission()).
        # Collapsing the two into one indistinguishable pool would make
        # commissioning pointless, since it would just be spending money to
        # buy the same hours market_supply already counts. Two channels,
        # each bounded, each named wherever the number is printed.
        #
        # PRODUCTIVITY MULTIPLIES THE RESULT, NOT market_supply ITSELF. This
        # is what turns "the same crew gets more done" into "the market can
        # supply more people" if it were applied upstream instead - the wall
        # a project's labour draw actually runs into is how much WORK gets
        # out of the hours it can call on, which is this number, not how
        # many people the town could in principle hire (market_supply, still
        # unchanged, still governs hiring capacity and labour_price_factor).
        return ((self.market_supply(trade) + self.state.household.contract_hours.get(trade, 0.0))
                * self.labour_productivity(trade))

    def hours_reserved(self, trade):
        """Hours of this trade you have already bought from an outside shop."""
        return self.state.household.contract_hours.get(trade, 0.0)

    def market_supply_split(self, trade):
        """(the town's hours, your own people's hours). Same total, said honestly.

        market_supply is hours of this trade AVAILABLE TO YOU, which
        includes your own staff - so printing it raw after hiring a smith
        would show the total rising (say, 22,500 to 24,500) and read as
        hiring having pulled smiths OUT of the market and made more
        smith-hours available elsewhere. The arithmetic is right and the
        reading is wrong: the town's own share has not moved at all, only
        yours has grown, so the two have to be reported apart.
        """
        mine = self.state.household.employees.get(trade, 0.0) * self.HOURS_PER_PERSON_YEAR
        total = self.market_supply(trade)
        if trade in TRADES_ABSENT:
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
        line, where a project may draw the whole of it. The refusal has to
        say so explicitly, not only show capital, or it reads as arbitrary
        rather than as the reasoning it actually is. One message for hire,
        train and commission, so the three cannot drift apart from each
        other or from this reasoning.
        """
        room = self.spending_power("buy")
        return ("%s costs %s denarii, due now - not on credit past half your "
                "line. You have %s in hand and could raise about %s more of "
                "your credit line for this (not all of it: a lender funds "
                "work already under way, which is what starting a project "
                "can point to; a wage, an apprentice's keep or a commission "
                "fee is money simply spent, and nothing stands behind that "
                "the way a half-built project does). You are %s short."
                % (what, "{:,.0f}".format(fee), "{:,.0f}".format(self.state.household.capital),
                   "{:,.0f}".format(max(0.0, room)),
                   "{:,.0f}".format(max(0.0, fee - room))))

    def hire(self, trade, count):
        """Take someone onto the staff permanently. They are paid every year."""
        trade = str(trade or "").strip().lower()
        if trade not in WAGES:
            return False, ("no such trade: %s. Trades: %s"
                           % (trade, ", ".join(sorted(WAGES))))
        if isinstance(count, str) or isinstance(count, bool):
            # `buy` and `start` both type-check and `hire` did not, so "5"
            # walked straight in where 5 was meant.
            return False, "n must be a number, not %r" % (count,)
        if count <= 0:
            return False, "n must be greater than zero. Nothing was changed."
        # PEOPLE ARE WHOLE: a household can want a third of another artisan's
        # worth of work, and it can buy that in hours (`commission`); it
        # cannot put a third of a person on the payroll, or a roster could
        # read "0.03 engineers" - wages drawn for somebody who could not
        # supervise anything because there is no such person. See core.py
        # step() for the matching constraint on attrition, going the other
        # way.
        if abs(count - round(count)) > 1e-6:
            return False, ("you hire whole people, not %g of one. Hire %d or %d."
                           % (count, math.floor(count), math.ceil(count)))
        count = float(round(count))
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
            if have + count > cap + 1e-6:
                return False, self._literate_wall_refusal(trade, cap, have)
        # A finder's fee and the first year in advance, which is what a household
        # actually pays to take a skilled man off someone else's bench. Buying
        # deep into a trade's LOCAL supply bids its price up, the same
        # principle market_pressure already applies to slaves (see
        # labour_price_factor for why it is not a one-way ratchet: teaching
        # or hiring your way to a bigger supply of the trade brings the price
        # back down).
        _lpf_now = self.labour_price_factor(trade)
        fee = (count * self.annual_wage(trade, include_local_scarcity=False)
               * _lpf_now)
        if fee > self.spending_power("buy"):
            _msg = self._cash_in_hand_refusal(
                "hiring %g %s%s" % (count, trade, "" if count == 1 else "s"), fee)
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
        if count > room:
            # TRUNCATED, NOT ROUNDED, and it says what a whole number of people
            # would be: rounding room UP in the message can print "you can
            # supervise, house and teach 7.0 more people, not 7" while
            # refusing exactly that request - a refusal that contradicts
            # itself. A figure a player is meant to act on must never be
            # rounded in the direction that overstates it.
            room = max(0.0, room)
            whole = int(room)
            return False, ("you can supervise, house and teach %.2f more people, "
                           "not %g%s. %s"
                           % (math.floor(room * 100) / 100.0, count,
                              " - %d is the most whole people you can take" % whole
                              if whole else " - you have no room for even one",
                              self._room_advice()))
        household = self.state.household
        household.capital -= fee
        # CARRIED FORWARD, so the next step does not bill the same year twice.
        # See step() 2, where it is netted off living_cost.
        household.wages_prepaid = (household.wages_prepaid or 0.0) + fee
        household.employees[trade] = household.employees.get(trade, 0.0) + float(count)
        self._add_labour_pressure(trade, float(count) * self.HOURS_PER_PERSON_YEAR)
        self._resync_pools()
        # SAY HOW MANY, AND HOW MANY YOU NOW HAVE: a reply that only names
        # the trade, with no number, gives a player no way to notice a
        # request for eight landing as one. A verb that takes a quantity
        # has to report the quantity.
        return True, ("%g %s%s taken on for %s denarii (a finder's fee and the "
                      "first year in advance). You now have %.1f, and %.2f "
                      "household place(s) left"
                      % (count, trade, "" if count == 1 else "s",
                         "{:,.0f}".format(fee), household.employees[trade],
                         max(0.0, self.household_room())))

    def fire(self, trade, count):
        """Let staff go. Their wages stop; so does what they were doing.

        AND IT CANCELS AN APPRENTICESHIP: turning `auto_train` off does not
        stop training already in flight, so there has to be some command
        that can. Dismissing a trade you are still teaching is the obvious
        reading of `fire`, and it is the missing lever: what you paid to
        feed them while they learned is spent, the way any abandoned work
        is, and they do not arrive.
        """
        trade = str(trade or "").strip().lower()
        household = self.state.household
        have = household.employees.get(trade, 0.0)
        pending = sum(record[3] for record in household.training
                      if len(record) > 3 and record[2] == trade)
        if have <= 0 and pending <= 0:
            return False, "you employ no %ss, and none are being taught" % trade
        count = float(count)
        # THE SAME WHOLENESS hire() AND train() ENFORCE: letting a fraction of
        # a person go is the mirror image of hiring one, and would reopen
        # the same hole - a roster that can drift to "0.03 engineers" -
        # through `fire` alone even though nothing can hire or teach its
        # way there. Rounded rather than refused, because "let go 2.5" has
        # an obvious meaning (two, or the two-point-something you actually
        # have) and refusing outright would only make a player retype it.
        if have > 0 and abs(count - round(count)) > 1e-6 and count < have:
            count = float(math.ceil(count))
        note = None
        if have > 0:
            gone = min(count, have)
            household.employees[trade] = have - gone
            if household.employees[trade] <= 1e-9:
                household.employees.pop(trade)
            count -= gone
            note = "let %g %s%s go" % (gone, trade, "s" if gone != 1 else "")
        if count > 0 and pending > 0:
            stopped, still = 0.0, []
            for record in household.training:
                if len(record) > 3 and record[2] == trade and count > 0:
                    take = min(count, record[3])
                    record[3] -= take
                    count -= take
                    stopped += take
                if len(record) <= 3 or record[3] > 1e-9:
                    still.append(record)
            household.training = still
            if stopped > 0:
                note = ((note + "; " if note else "")
                        + "stopped teaching %g more (what you paid to keep them "
                          "while they learned is gone)" % stopped)
        self._resync_pools()
        return True, note

    TEACHING_HOURS_PER_PERSON = declare(
        "TEACHING_HOURS_PER_PERSON", 450.0, kind="temporary_heuristic",
        unit="founder-hours per person taught", source=None,
        confidence="D",
        why="How many of the founder's own hours it takes to teach one "
            "person a new trade. Tuned so teaching is a real, felt cost "
            "against the roughly 2,000-hour year (see this method's own "
            "docstring on a play tester who trained 4 machinists and lost "
            "1,800 of 2,000 founder-hours), not measured against any real "
            "pre-modern apprenticeship's actual instructional load.")
    TEACHING_MATURATION_YEARS = declare(
        "TEACHING_MATURATION_YEARS", 2.0, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="How long after being taught a person takes to mature into a "
            "working member of the new trade - shorter than TRAINING_YEARS "
            "(3.0, for a bought and untrained person) because teaching "
            "starts from an already-skilled craftsman rather than an "
            "unskilled purchase. Tuned, not measured.")
    TEACHING_FEE_MULTIPLIER = declare(
        "TEACHING_FEE_MULTIPLIER", 1.2, kind="temporary_heuristic",
        unit="dimensionless multiplier on the source trade's annual wage",
        source=None, confidence="D",
        why="What it costs, per person taught, to keep the SOURCE "
            "trade's people fed while they are pulled off their own "
            "bench to learn something new - a premium over their "
            "ordinary annual wage, the same idea labour_price_factor "
            "prices for hiring and market_pressure prices for buying "
            "slaves. Tuned premium, not a measured opportunity cost.")

    def train(self, trade, count, frm=None):
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
        if count <= 0:
            return False, "n must be greater than zero. Nothing was changed."
        # PEOPLE ARE WHOLE. See the identical check in hire() for why: a
        # taught trade is still a roster of actual people, not a quantity of
        # training-hours, and "0.03 engineers" was exactly as false whichever
        # verb put it there.
        if abs(count - round(count)) > 1e-6:
            return False, ("you teach whole people, not %g of one. Teach %d or %d."
                           % (count, math.floor(count), math.ceil(count)))
        count = float(round(count))
        frm = (frm or ("smith" if trade in ("machinist", "engineer")
                       else "glassblower" if trade == "optician"
                       else "scribe" if trade == "chemist"
                       else "smith")).strip().lower()
        if frm in TRADES_ABSENT and frm not in self.state.household.trades_created:
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
            if have + count > cap + 1e-6:
                return False, self._literate_wall_refusal(trade, cap, have)
        hours = self.TEACHING_HOURS_PER_PERSON * count            # your hours, teaching, per person
        pool = self.director_pool() - self.director_hours_committed()
        if hours > pool:
            return False, ("teaching %g %ss takes %.0f of your own hours and you have "
                           "%.0f uncommitted this year" % (count, trade, hours, max(0.0, pool)))
        # THE SAME ROOM `hire` AND `buy` SHARE: household_room exists so all
        # three verbs agree on the same ceiling. `train` must check it too,
        # or a household could teach its way past its actual capacity to
        # feed, house and oversee people, ending up unable to hire the
        # artisans it needs to supervise anything it just taught. People
        # you teach have to be fed, housed and overseen like anybody else.
        room = self.household_room()
        if count > room:
            whole = int(max(0.0, room))
            return False, ("you can feed, house and oversee %.2f more people, "
                           "and teaching %g would make %g. %s %s"
                           % (math.floor(max(0.0, room) * 100) / 100.0, count, count,
                              "Teach %d instead." % whole if whole >= 1
                              else "There is no room for even one.",
                              self._room_advice()))
        # Teaching pulls the SOURCE trade's people off their own bench for the
        # duration, which is exactly what market_pressure prices for buying
        # slaves and labour_price_factor now prices for hiring: the more of
        # `frm` you have already pulled recently, the dearer feeding the next
        # batch while they learn.
        fee = count * self.annual_wage(frm) * self.TEACHING_FEE_MULTIPLIER
        if fee > self.spending_power("buy"):
            return False, self._cash_in_hand_refusal(
                "keeping %g %s%s fed while they learn"
                % (count, trade, "" if count == 1 else "s"), fee)
        household = self.state.household
        current_year = self.state.scenario.year
        household.capital -= fee
        household.teaching_hours_this_year = (household.teaching_hours_this_year or 0.0) + hours
        household.trades_created.add(trade)
        household.training.append([0.0, current_year + self.TEACHING_MATURATION_YEARS, trade, float(count)])
        self._add_labour_pressure(frm, float(count) * self.HOURS_PER_PERSON_YEAR)
        # SAY WHAT IT TOOK: teaching can quietly eat most of a year's
        # founder-hours, with nothing left afterward to supervise what it
        # just cost elsewhere to run - the reply has to report the actual
        # hours and money spent, not just a brief note about when training
        # finishes. Teaching is the most expensive thing you can do with a
        # year.
        _left = max(0.0, self.director_pool() - self.director_hours_committed())
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
                      "Until then they cannot do a day of the work. It took "
                      "%s of your own hours (%s left this year) and %s "
                      "denarii to keep them while they learn"
                      % (count, trade, "s" if count != 1 else "", current_year + self.TEACHING_MATURATION_YEARS,
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
        projects = self.state.projects
        household = self.state.household
        for node_id in self.order:
            if seen >= look:
                break
            if node_id in projects.done or node_id in projects.active or node_id not in need:
                continue
            node = self.nodes[node_id]
            if any(prereq_id not in projects.done for prereq_id in node["pre"]):
                continue
            seen += 1
            short = node["art"] - self.craft_hands_available()
            if short <= 0 or node["sch"] > self.effective_scholars():
                continue
            hours = short * self.HOURS_PER_PERSON_YEAR
            # The cheapest craft trade this society actually has that can
            # spare the time: a workshop needs hands, not a particular guild.
            best = None
            for trade in sorted(WAGES):
                if trade_family(trade) != "craft" or not self.trade_available(trade):
                    continue
                spare = self.market_supply(trade) - household.contract_hours.get(trade, 0.0)
                if spare < hours:
                    continue
                if best is None or WAGES[trade] < WAGES[best]:
                    best = trade
            if best is None:
                continue
            did_commission, _why = self.commission(best, hours)
            if did_commission:
                return (node_id, best, hours)
        return None

    def craft_hands_available(self):
        """Craftsmen you can actually put on a job this year: the ones on your
        own staff, plus the ones whose time you have already bought.

        Hours under contract are people for as long as the contract runs. A
        year of a carpenter's time IS a carpenter, for the purposes of whether
        you can attempt a thing that needs one, and buying a job rather than a
        person is the whole point of `commission`."""
        household = self.state.household
        contracted = sum(hours for trade, hours in getattr(household, "contract_hours", {}).items()
                         if trade_family(trade) == "craft")
        # AND YOURSELF. effective_scholars() has always counted the founder as
        # one of the scholars - "you are your own natural philosopher" - and
        # nothing counted them as a pair of hands, though the premise of the
        # whole game is a person who knows how every one of these things is
        # made. The asymmetry had a cost: workshop_first wants two craftsmen,
        # and a Norse run that could field one could never build the place
        # craftsmen work, so it ended six hundred years later with 136
        # technologies and no staff at all.
        own = 1.0 if self.state.founder.founder_alive else 0.0
        return household.artisans + own + contracted / self.HOURS_PER_PERSON_YEAR

    COMMISSION_PREMIUM_MULTIPLIER = declare(
        "COMMISSION_PREMIUM_MULTIPLIER", 1.6, kind="temporary_heuristic",
        unit="dimensionless multiplier on the trade's ordinary wage rate",
        source=None, confidence="D",
        why="What a shop charges for a one-off job over what it pays its "
            "own man for a year, before local scarcity (labour_price_"
            "factor) adds anything further. Tuned so commissioning is a "
            "real premium over hiring rather than a free substitute for "
            "it, not measured from any real subcontracting markup. NOTE "
            "for Complaints/34 ('buying scholar hours fails for want of "
            "scholars'): this function's own gates - trade_available(), "
            "market_supply(trade) for the spare-hours ceiling, and this "
            "fee against spending_power('buy') - do not test "
            "self.household.employees for `trade` at all, and "
            "market_supply('scholar') (see that function) is independent "
            "of whether any scholars are currently on staff. Nothing in "
            "this file's commission()/market_supply() path refuses a "
            "scholar commission for want of existing scholar employees; "
            "if the complaint reproduces, the refusal is not coming from "
            "here.")

    def commission(self, trade, hours):
        """Pay for a job, not for a person.

        Sometimes what is needed is some copper wire, not a full-time
        smith on the payroll. This buys a specific piece of work from
        somebody else's shop at a premium over their wage, with no
        standing obligation either way.
        """
        trade = str(trade or "").strip().lower()
        if trade not in WAGES:
            return False, "no such trade: %s" % trade
        if hours <= 0:
            return False, "hours must be greater than zero. Nothing was changed."
        if not self.trade_available(trade):
            return False, ("no %s will take the work; the trade does not exist here: %s"
                           % (trade, TRADE_NOTES.get(trade, "")))
        household = self.state.household
        spare = self.market_supply(trade) - household.contract_hours.get(trade, 0.0)
        if hours > spare:
            return False, ("the %ss here can spare %.0f more hours this year, not %.0f"
                           % (trade, max(0.0, spare), hours))
        # A shop charges more for a one-off than it pays its own man for a
        # year, and more again if you are buying deep into what the local
        # market can spare this year (see labour_price_factor).
        fee = (hours * WAGES[trade] * self.COMMISSION_PREMIUM_MULTIPLIER
              * self.wage_index * self.price_index
              * self.labour_price_factor(trade))
        if fee > self.spending_power("buy"):
            return False, self._cash_in_hand_refusal(
                "%.0f hours of a %s" % (hours, trade), fee)
        household.capital -= fee
        household.contract_hours[trade] = household.contract_hours.get(trade, 0.0) + hours
        household.commissioned[trade] = household.commissioned.get(trade, 0.0) + hours
        self._add_labour_pressure(trade, hours)
        return True, ("%.0f hours of a %s bought for %.0f denarii" % (hours, trade, fee))