"""What the engine does on its own, every year, about staffing and money.

Split out of sim/engine/projects.py (see that file's own docstring for why):
where projects_ventures.py holds the two verbs a player types (`open`,
`close`), this file holds the automatic rule that applies the same logic
every year afterward - close_unstaffed_ventures() shuts what nobody is left
to supervise, reopen_restaffed_ventures() brings back what can be supervised
again, staffing_closure_warnings() tells a player what is about to shut
before it does, and auto_open_ventures() opens (or expands) what plainly
pays for itself within what the household can actually afford. mothball_work
and restore_work are the same shut-down/reopen pair for a completed work
that was never a staffing casualty at all, just switched off deliberately
and switched back on.

These are methods of Sim; they are a mixin only so that they can live in a
file of their own. Behaviour is unchanged and verified byte-identical.
"""
from constants import declare


class StaffingMixin:

    STAFFING_CLOSURE_SLACK = declare(
        "STAFFING_CLOSURE_SLACK", 0.5, kind="temporary_heuristic",
        unit="people (scholars or craftsmen)", source=None, confidence="D",
        why="Hysteresis band on the staffing-closure rule: a concern only "
            "closes when the shortfall is a real half-a-pair-of-hands or "
            "more, not any exact crossing of the line - attrition wobbles "
            "the balance every year, and an exact comparison closed and "
            "reopened the same concern almost every turn for centuries "
            "(see this function's own comment). Shared with "
            "staffing_closure_warnings, which measures room against the "
            "same band so a warning and the actual closure rule can never "
            "disagree about where the line is. Tuned to stop the flapping, "
            "not measured.")

    def close_unstaffed_ventures(self, yr):
        """Shut what nobody is left to watch, dearest to supervise first.

        Not a policy and not an automation you can switch off: it is the same
        rule `open` already applies, applied on the years after the first. A
        shop whose keeper you dismissed is a shop that stops trading, and the
        alternative - which is what the game did - is a fortune of concerns
        running themselves for ever on an empty payroll.
        """
        # HYSTERESIS. Attrition is 3.5% a year and auto_hire tracks the
        # ceiling, so the supervision balance wobbles across the line
        # constantly - and an exact comparison meant a concern closed and was
        # reopened almost every single turn for four centuries. A play tester
        # called it "endless re-opening busywork" and they were right: nobody
        # shuts a shop because they are a fortieth of a man short this spring.
        # Close only when the shortfall is a real pair of hands.
        SLACK = self.STAFFING_CLOSURE_SLACK
        closed = []
        while self.household.operating:
            sch_used, art_used = self.venture_staff_used()
            foremen_used = self.venture_foremen_used()
            own = self.FOUNDER_IS_WORTH if self.founder_alive else 0.0
            foremen_ok = all(
                used <= self.household.employees.get(trade, 0.0) + 0.01
                for trade, used in foremen_used.items())
            if (sch_used <= self.effective_scholars() + SLACK
                    and art_used <= self.household.artisans + own + SLACK
                    and foremen_ok):
                break
            # THE LEAST WORTH KEEPING, not the largest. This picked whichever
            # concern needed the most hands, which is very nearly the same as
            # picking the most PROFITABLE one - a break tester watched it close
            # a 600-a-year hopper wagon twice and keep a concern earning
            # nothing with identical staffing. Shut the one that returns least
            # for the people it ties up.
            # sorted(): min() over a set returns whichever equal-keyed element
            # came first in iteration order, which is not fixed.
            # ONLY WHAT ACTUALLY HOLDS HANDS. The key divides by
            # max(0.01, hands), so a concern that ties up NOBODY scored minus
            # a hundred and seventy thousand and was chosen first every time -
            # and closing it freed not one pair of hands, so the loop came
            # round and closed the next, and the next, until nothing was open
            # at all. That is how a founder who opened a school, an academy
            # and an imperial patron on the same turn had all three shut by
            # the staffing rule on the next one. You cannot answer a shortage
            # of craftsmen by closing something no craftsman was watching.
            _holders = [node_id for node_id in sorted(self.household.operating)
                        if self.venture_hands(node_id)[1] > 0.005
                        or self.venture_hands(node_id)[0] > 0.005
                        or self.venture_foreman(node_id)[1] > 0.005]
            if not _holders:
                break
            worst = min(_holders,
                        key=lambda k: ((self.nodes[k]["rev"] - self.nodes[k]["up"])
                                       / max(0.01, self.venture_hands(k)[1]
                                             + self.venture_foreman(k)[1]),
                                       -self.venture_hands(k)[1]))
            self.household.operating.discard(worst)
            self.household.mothballed.add(worst)
            _sfs = getattr(self.household, "shut_for_staff", {})
            _sfs[worst] = yr
            self.household.shut_for_staff = _sfs
            closed.append(worst)
        if closed:
            self.household.log.append((yr, "nobody left to keep an eye on %d concern%s, so "
                                 "%s closed. You still know how; reopen with "
                                 "'open' once you have the people. The premises "
                                 "and the stock stand for a few years yet, so "
                                 "reopening soon costs a tenth of what opening did"
                             % (len(closed), "" if len(closed) == 1 else "s",
                                ", ".join(sorted(closed)[:4])
                                + (" and others" if len(closed) > 4 else ""))))
        return closed

    def reopen_restaffed_ventures(self, yr):
        """Bring back what the staffing rule shut, the moment you have the
        people to watch it again - not a policy, the other half of one.

        close_unstaffed_ventures is deliberately not a policy a player can
        switch off (see its own docstring): it is the world taking back a
        concern nobody is left to watch. Three playtesters found that the
        world never gave it back, even after they hired or taught their way
        past the shortfall - reopening was `auto_open`, a SEPARATE policy
        that defaults off for a player, and the whole of "most of the mid
        and late game was a repetitive hire-then-reopen treadmill rather
        than fresh decisions" is a player retyping `open` on the same
        handful of ids every few years, for no decision at all: they had
        already decided to run this concern once, and losing a craftsman to
        attrition is not a moment that asks them to decide it again.

        So this runs unconditionally, like the rule it undoes, and it is
        careful to undo only THAT rule: shut_for_staff is set nowhere except
        close_unstaffed_ventures, so a concern a player shut on purpose with
        `mothball` never reappears on its own - that is still their call.
        """
        _shut = getattr(self.household, "shut_for_staff", {})
        cands = [node_id for node_id in sorted(_shut)
                 if node_id in self.household.mothballed and node_id in self.household.done and node_id in self.nodes]
        if not cands:
            return []
        # BEST-EARNING FIRST, same idea as auto_open_ventures: when only some
        # of what closed can be restaffed with what you have free this year,
        # what comes back first should be what is worth the most, not
        # whichever id sorts first.
        cands.sort(key=lambda k: -((self.nodes[k]["rev"] - self.nodes[k]["up"])
                                   / max(0.01, sum(self.venture_hands(k)))))
        reopened = []
        for node_id in cands:
            need_sch, need_art = self.venture_hands(node_id)
            sch_free, art_free = self.venture_staff_free()
            if need_sch > sch_free + 0.01 or need_art > art_free + 0.01:
                continue
            ok, _msg = self.open_venture(node_id)
            if ok:
                reopened.append(node_id)
        if reopened:
            self.household.log.append((yr, "you have the people again: %s reopen%s on "
                                 "their own, now that somebody is free to "
                                 "watch %s"
                             % (", ".join(sorted(reopened)[:4])
                                + (" and others" if len(reopened) > 4 else ""),
                                "" if len(reopened) == 1 else "s",
                                "it" if len(reopened) == 1 else "them")))
        return reopened

    # ---- A WARNING BEFORE THE DOOR SHUTS, NOT AN AUTOMATION THAT OPENS IT --
    # close_unstaffed_ventures closes a concern the moment attrition pushes
    # the household's own staff below what keeping it open needs, and
    # reopen_restaffed_ventures now (see its own docstring) brings it back
    # the moment the shortfall is made good - between them the engine already
    # does the closing and the reopening on its own. Players were clear they
    # want neither automated further: what they asked for is to SEE a closure
    # coming while there is still a year or two to react - hire, teach,
    # stop something else on purpose - in their own words, "power grid
    # supervision is within 5 craftsmen of closure." This is that sentence,
    # not a third policy: it changes nothing about who gets hired, taught or
    # shut, only what the player is told before the staffing rule decides it
    # for them.
    #
    # THE SAME SLACK BAND close_unstaffed_ventures ITSELF USES, not a fresh
    # threshold invented for this: SLACK=0.5 there is the hysteresis that
    # stops a concern flapping open and shut across an exact tie, so "room
    # before closure" has to be measured against that same cushion or this
    # would warn about a closure that was never actually imminent (or stay
    # silent until after the real threshold had already passed).
    STAFFING_WARNING_BAND = declare(
        "STAFFING_WARNING_BAND", 5.0, kind="temporary_heuristic",
        unit="people (scholars or craftsmen) of headroom", source=None,
        confidence="D",
        why="How much slack has to remain before a running concern is "
            "worth warning about at all - a player asked, in their own "
            "words, to see 'power grid supervision is within 5 craftsmen "
            "of closure' before it happens. Tuned to give a year or two "
            "of real warning, not measured against any real staffing "
            "turnover rate.")

    # THE CLIFF ITSELF, not just the approach to it. Two players independently
    # reported the same shape of surprise: a single artisan dying took a
    # concern from comfortably staffed to closed the same year, with recurring
    # income swinging from strongly positive to nothing. STAFFING_WARNING_BAND
    # already puts every concern like that inside the warning list (5 people
    # of headroom catches 1), but the headline it got was the same generic
    # "within N craftsmen of closure" whether N was 4.8 or 0.3 - it never said
    # that N here is small enough that ONE ordinary attrition event, not a
    # policy failure or a run of bad luck, is what closes it, and it never
    # said what that closure would actually cost or how to buy the room back.
    # This band is where that sharper sentence kicks in: room this thin is not
    # early warning any more, it is the edge itself.
    STAFFING_NO_SLACK_BAND = declare(
        "STAFFING_NO_SLACK_BAND", 1.0, kind="temporary_heuristic",
        unit="people (scholars or craftsmen) of headroom", source=None,
        confidence="D",
        why="Below this much headroom, the warning sharpens from 'N spare' "
            "to 'losing just one more closes it outright' - room this thin "
            "means one ordinary attrition event, not a policy failure or "
            "bad luck, is what actually closes the concern. Tuned to mark "
            "the point where the arithmetic really does mean one person, "
            "not measured.")

    def staffing_closure_warnings(self, limit=3):
        """Which running concern the staffing rule would shut NEXT if
        attrition keeps biting, and how many people of slack still stand
        between here and that - see the section comment above for why this
        exists instead of a third automation.

        Silent while the household is comfortably staffed (the common case):
        only reports when the SAME margin close_unstaffed_ventures itself
        would act on has shrunk to STAFFING_WARNING_BAND or less, in
        whichever of scholars or craftsmen actually binds for that concern -
        a concern that only ever drew on scholars is not put on notice by a
        shortage of craftsmen, and the other way round.
        """
        if not self.household.operating:
            return []
        sch_used, art_used = self.venture_staff_used()
        own = self.FOUNDER_IS_WORTH if self.founder_alive else 0.0
        SLACK = self.STAFFING_CLOSURE_SLACK   # close_unstaffed_ventures' own hysteresis band
        sch_room = self.effective_scholars() + SLACK - sch_used
        art_room = self.household.artisans + own + SLACK - art_used
        if sch_room > self.STAFFING_WARNING_BAND and art_room > self.STAFFING_WARNING_BAND:
            return []
        _holders = [node_id for node_id in sorted(self.household.operating)
                    if self.venture_hands(node_id)[1] > 0.005
                    or self.venture_hands(node_id)[0] > 0.005]
        if not _holders:
            return []
        # SAME ORDER close_unstaffed_ventures would close in - dearest to
        # keep, for what it ties up, first - so the concerns named here are
        # exactly the ones actually at risk, not merely the largest.
        ranked = sorted(_holders,
                        key=lambda k: ((self.nodes[k]["rev"] - self.nodes[k]["up"])
                                       / max(0.01, self.venture_hands(k)[1]),
                                       -self.venture_hands(k)[1]))
        out = []
        for node_id in ranked:
            sch_need, art_need = self.venture_hands(node_id)
            candidates = []
            if sch_need > 0.005:
                candidates.append(("scholars", sch_room))
            if art_need > 0.005:
                candidates.append(("craftsmen", art_room))
            if not candidates:
                continue
            # WHICHEVER OF ITS OWN TRADES IS SCARCEST, not whichever this
            # concern happens to need most: a concern that ties up both a
            # scholar and three craftsmen is at risk the moment EITHER pool
            # runs out, so the tighter of the two is what actually decides
            # when it closes.
            word, room = min(candidates, key=lambda c: c[1])
            if room > self.STAFFING_WARNING_BAND:
                continue
            name = self.nodes[node_id]["name"]
            # WHAT IT COSTS TO LOSE, in the same recurring den/yr the player
            # already judges every concern by (rev - up, the same figure
            # `ventures` and the ranking above use) - not just that it would
            # close, but whether closing it is worth reacting to.
            net = max(0.0, self.nodes[node_id]["rev"] - self.nodes[node_id]["up"])
            cost = "{:,.0f}".format(net)
            # THE COMMAND THAT FIXES IT, named, not left for the player to
            # infer from "craftsmen"/"scholars" alone - hire is always
            # sayable (STAFF_SOURCES' own reasoning: the labour market is in
            # front of you whether or not any institution is), so this is the
            # one remedy safe to name inline rather than routing through the
            # fuller, sometimes-circular advice _staff_advice gives.
            _kind = "scholars" if word == "scholars" else "artisans"
            fix = next(why for node, why in self.STAFF_SOURCES[_kind]
                       if node == "HIRE")
            one_loss_closes = room <= self.STAFFING_NO_SLACK_BAND + 1e-9
            if room <= 0.05:
                headline = ("%s has no %s free this year and is next in "
                            "line to close - that would cost %s den/yr in "
                            "recurring income. %s"
                            % (name, word, cost, fix))
            elif one_loss_closes:
                # THE MISSING CASE: no slack at all. Room here is under one
                # whole person, so losing even ONE %s of this trade - one
                # death, one who leaves - closes this outright the same
                # year, not "eventually" and not "if things get worse".
                headline = ("%s has no spare %s: losing just one more "
                            "closes it outright, costing %s den/yr in "
                            "recurring income. %s"
                            % (name, word, cost, fix))
            else:
                # THE DIRECTION OF SAFETY, UNMISTAKABLE. "is within N
                # craftsmen of closure" read, on first sight, like a
                # countdown - an England player hired more staff, watched
                # this number climb 1.3 to 2.3, and took the rise for the
                # situation getting WORSE before working out that bigger
                # here means safer. "has N spare craftsmen before it
                # closes" cannot be misread the same way: spare is
                # obviously a good thing to have more of, and it is the
                # same word the no-slack branch just above already uses
                # ("has no spare %s: losing just one more closes it
                # outright") - the two headlines now share one vocabulary
                # for the same fact instead of two that could be read as
                # opposites of each other.
                headline = ("%s has %s spare %s before it closes"
                            % (name, ("%.1f" % room).rstrip("0").rstrip("."),
                               word))
            out.append({"id": node_id, "name": name, "within": round(max(0.0, room), 1),
                       "of": word, "headline": headline,
                       "recurring_income_at_risk": round(net, 1),
                       "one_loss_closes_it": one_loss_closes,
                       "fix": fix})
            if len(out) >= limit:
                break
        return out

    AUTO_OPEN_DEEP_ARREARS_CREDIT_SHARE = declare(
        "AUTO_OPEN_DEEP_ARREARS_CREDIT_SHARE", 0.5, kind="temporary_heuristic",
        unit="fraction of credit_limit", source=None, confidence="D",
        why="Beyond this share of the credit line owed, a household is "
            "'deep in arrears' for purposes of gating NEW institutional "
            "bleed (not ordinary net-positive concerns, which answer for "
            "themselves on payback period). Tuned to stop the optimizer "
            "borrowing to the hilt (the 'ABANDONED 1 works...two hundred "
            "and six times' history this function's own comment "
            "describes) without recreating the earlier catch-22 where a "
            "household already in the red could never open the shop that "
            "would dig it out.")
    AUTO_OPEN_INSTITUTION_ARREARS_SHARE = declare(
        "AUTO_OPEN_INSTITUTION_ARREARS_SHARE", 0.75, kind="temporary_heuristic",
        unit="fraction of credit_limit", source=None, confidence="D",
        why="A second, slightly looser arrears threshold specifically for "
            "whether an institution may open against what it could RAISE "
            "rather than only what it is currently clearing. Tuned "
            "alongside AUTO_OPEN_DEEP_ARREARS_CREDIT_SHARE as one of 'two "
            "guards' against the same borrow-to-the-hilt failure mode; not "
            "measured.")
    AUTO_OPEN_SURPLUS_SHARE_FOR_BLEED = declare(
        "AUTO_OPEN_SURPLUS_SHARE_FOR_BLEED", 0.5, kind="temporary_heuristic",
        unit="fraction of this year's real surplus", source=None,
        confidence="D",
        why="How much of this year's actual surplus (not credit) may be "
            "committed to a new institution's standing bleed. Tuned "
            "caution, not measured.")
    AUTO_OPEN_CREDIT_LINE_BLEED_SHARE = declare(
        "AUTO_OPEN_CREDIT_LINE_BLEED_SHARE", 0.10, kind="temporary_heuristic",
        unit="fraction of credit_limit", source=None, confidence="D",
        why="The borrowing allowance ON TOP OF real surplus that lets a "
            "household cross the 'no institution ever affordable because "
            "there is no institution yet' deadlock (workshop_first "
            "bleeding 900/yr against a surplus that was negative BECAUSE "
            "there was no workshop - see this function's own long "
            "comment). Deliberately small and deliberately excluded from "
            "the later expansion-ladder loop, which spends real cash flow "
            "only. Tuned bootstrap allowance, not measured.")
    AUTO_EXPAND_MIN_ROOM_UNITS = declare(
        "AUTO_EXPAND_MIN_ROOM_UNITS", 0.05, kind="temporary_heuristic",
        unit="units", source=None, confidence="D",
        why="Below this much room left under an institution's unit "
            "ceiling, expanding it further is not worth the bookkeeping - "
            "an epsilon-scale floor on a real decision (whether to spend "
            "an expansion step), not a display threshold. Tuned, not "
            "measured.")
    AUTO_EXPAND_MIN_OCCUPANCY = declare(
        "AUTO_EXPAND_MIN_OCCUPANCY", 0.85, kind="temporary_heuristic",
        unit="fraction of institution_places", source=None, confidence="D",
        why="An institution is not expanded automatically until it is "
            "already this full - a household with room to spare is not "
            "short of more of it, whatever it could technically still "
            "borrow. Tuned occupancy trigger, not measured.")
    AUTO_EXPAND_SURPLUS_SHARE = declare(
        "AUTO_EXPAND_SURPLUS_SHARE", 0.25, kind="temporary_heuristic",
        unit="fraction of this year's real surplus", source=None,
        confidence="D",
        why="At most a quarter of this year's real surplus may fund "
            "discretionary institutional GROWTH (as opposed to the "
            "bootstrap allowance that opens the first unit at all) - "
            "growth is optional, so it is capped tighter than survival "
            "spending. Tuned, not measured.")
    AUTO_EXPAND_MIN_STEP_UNITS = declare(
        "AUTO_EXPAND_MIN_STEP_UNITS", 0.1, kind="temporary_heuristic",
        unit="units", source=None, confidence="D",
        why="The smallest expansion step worth actually taking in a "
            "single year - below this the bookkeeping is not worth it. "
            "Tuned, not measured.")

    AUTO_OPEN_PAYBACK_LIMIT_YEARS = declare(
        "AUTO_OPEN_PAYBACK_LIMIT_YEARS", 3.0, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="While deep in arrears, only a concern whose own capex clears "
            "inside this many years of its net revenue is offered at all - "
            "a concern that pays for its own door within a season or two "
            "is not the ABANDONED-206 failure mode (large capex against "
            "small net, borrowed to the hilt) this gate exists to stop. "
            "Tuned payback ceiling, not measured against any real lending "
            "standard.")

    def auto_open_ventures(self):
        """Open what plainly pays for itself, best margin first, within the
        staff and the money available. Default ON for the optimizer and OFF
        for a player, like every other automation in this game."""
        opened = []
        cands = self._auto_open_ordinary_candidates()
        # AUTO-OPENING ASKS "open", NOT "buy": a door on a concern that is
        # already built and already earning pays for its own fee, while a
        # wage buys nothing back. Each of the three helpers below computes
        # its own budget (_surplus, _bleed_room, _line) or calls
        # open_venture(), which runs the real spending_power("open") gate on
        # its own account - see _auto_open_check_deep_arrears' own comment.
        # sim/tests/test_affordability_and_credit.py's own guard on this is
        # behavioural: it wraps spending_power on a real Sim, forces the
        # answer to zero and requires each site's refusal to actually
        # follow from it.
        _deep_arrears = self._auto_open_check_deep_arrears()
        caps = self._auto_open_institution_candidates(_deep_arrears)
        _surplus, _bleed_room = self._auto_open_institution_budget()
        newly_opened, _surplus, _bleed_room = self._auto_open_institutions(
            caps, _surplus, _bleed_room)
        opened.extend(newly_opened)
        newly_opened, _surplus = self._auto_expand_institutions(_surplus, _deep_arrears)
        opened.extend(newly_opened)
        newly_opened, blocked = self._auto_open_ordinary_ventures(cands, _deep_arrears)
        opened.extend(newly_opened)
        self._auto_open_log_blocked(blocked, opened)
        return opened

    def _auto_open_ordinary_candidates(self):
        """Ordinary, completed, net-positive concerns not yet running,
        best margin for the money they tie up first - see the section
        comment below for what "for the money" means and why."""
        # BEST MARGIN FOR THE MONEY IT TIES UP, not best margin outright. When
        # what you can raise is the binding constraint - which is exactly when
        # this matters - a 400-a-year shop that opens for 60 is worth more than
        # a 3,200-a-year works you cannot afford at all.
        # sorted() is stable, so ties keep the order of the input - and the
        # input was a generator over a set. sorted(self.household.done) first.
        cands = sorted((node_id for node_id in sorted(self.household.done)
                        if self.is_venture(node_id) and node_id not in self.household.operating
                        and self.nodes[node_id]["rev"] > self.nodes[node_id]["up"]),
                       key=lambda k: -((self.nodes[k]["rev"] - self.nodes[k]["up"])
                                       / max(1.0, self.venture_capex(k))))
        return cands

    def _auto_open_check_deep_arrears(self):
        """Whether the household is deep enough in arrears that a NEW
        institution's standing bleed is gated - see the long comment
        below for why this is measured against arrears at all, and why
        an ordinary concern (cands) is answered on its own payback
        instead, further down in _auto_open_ordinary_ventures."""
        # DEEP IN ARREARS IS NOT "IN ARREARS": a household in the red must
        # still be able to open the shop that would dig it out, so the gate
        # cannot be `capital <= 0`. But with no gate at all, opening a new
        # institution - a standing bleed against money not yet coming in -
        # becomes unconstrained borrowing. Half the credit line is the
        # line: below it you can still open your way out, above it you are
        # digging (see the caps/scalable-growth guards right below,
        # unchanged by what follows).
        #
        # A completed, ordinary, net-positive concern (`cands`, below) is a
        # different thing, and gating it on household-wide arrears is the
        # wrong test: an ordinary concern's own payback period, not the
        # size of the hole the household is in, is what should decide it.
        # Blanket-refusing anything while the household owes more than half
        # its credit line would leave an already-built, already-earning
        # concern with cheap capex and a fast payback sitting shut - sunk
        # capex earning nothing is worse for the household AND its
        # creditors than letting it open. So: gate the INSTITUTIONS below on
        # the household's arrears, but let an ordinary concern answer for
        # itself - its own payback period, not the size of the hole it
        # would be dug from - in the `cands` loop near the end of this
        # function, which already refuses (via `open_venture`) anything
        # whose capex it cannot actually raise or whose supervision it
        # cannot actually staff.
        # "open", NOT "buy", AND THE DIFFERENCE IS LOAD-BEARING: opening an
        # already-built, already-earning concern must IGNORE how deep the
        # household already is, and ask only what could be raised for a
        # door fee on something that pays for itself in weeks. "buy" must
        # count the debt carried, because that is the honest answer for a
        # wage or a commission that buys nothing back - opening an
        # already-earning concern is the one case where debt must not
        # count, since refusing it only leaves its capex sunk and earning
        # nothing for as long as the arrears last.
        #
        # spending_power() must not be reused here even though it looks
        # like the same arithmetic written twice: it answers a different
        # question (whether the household can spend at all, not whether
        # THIS concern's own payback justifies opening it while in
        # arrears).
        _deep_arrears = (self.household.capital < 0
                         and -self.household.capital > self.credit_limit() * self.AUTO_OPEN_DEEP_ARREARS_CREDIT_SHARE)
        return _deep_arrears

    def _auto_open_institution_candidates(self, _deep_arrears):
        """Capability institutions not yet running, that a founder could
        open at a loss the household can carry - see the comment below
        for why these are worth opening below their own break-even."""
        # AND THE ONES WHOSE WORTH IS NOT AT THE DOOR. A school takes 2,500 a
        # year and hands back 800, so the margin test above shuts it out for
        # ever - and a school is where twelve of your scholars come from.
        # Everything a capability is gated on has to be able to open on the
        # strength of the capability, at a loss, provided the loss is one the
        # household can actually carry. Cheapest to keep first, so a poor
        # founder gets the workshop and the local patron before the academy.
        # STILL NOTHING WHILE DEEP IN ARREARS: an institution is a standing
        # bleed against revenue the household does not have, exactly the
        # unconstrained-borrowing case the comment above warns about.
        caps = [] if _deep_arrears else sorted(
                      (node_id for node_id in sorted(self.household.done)
                       if node_id in self.CAPABILITY_INSTITUTIONS
                       and node_id not in self.household.operating and self.is_venture(node_id)
                       and self.nodes[node_id]["rev"] <= self.nodes[node_id]["up"]),
                      key=lambda k: (self.nodes[k]["up"] - self.nodes[k]["rev"],
                                     self.venture_capex(k), k))
        return caps

    def _auto_open_institution_budget(self):
        """How much real surplus, and how much standing bleed against it,
        a new institution may be opened or grown with this year - see the
        comment below for why an institution may borrow against what it
        could raise and not only against what is already clearing."""
        # WHAT IS LEFT AFTER EVERYTHING YOU ARE ALREADY COMMITTED TO. Opening
        # an institution you cannot feed is how a household ends up abandoning
        # the works it already had.
        # AN INSTITUTION IS AN INVESTMENT, AND A LENDER KNOWS IT: requiring a
        # CURRENT surplus creates a catch-22, where an institution that would
        # itself supply the household's places, staff and workshop capacity
        # can never open, because surplus stays negative precisely for lack
        # of the institution.
        #
        # `start` has always been allowed to borrow, and a half-dug foundation
        # is worse collateral than a working shop. So an institution may be
        # opened against what you could RAISE and not only out of what you are
        # clearing - with two guards, since opening one this way is otherwise
        # unconstrained borrowing: nothing opens while you are deep in
        # arrears, and the standing bleed you take on may not outgrow a
        # tenth of your line.
        _surplus = (self.revenue() - self.upkeep() - self.living_cost())
        _line = self.credit_limit()
        _deep = self.household.capital < 0 and -self.household.capital > _line * self.AUTO_OPEN_INSTITUTION_ARREARS_SHARE
        _bleed_room = (max(0.0, _surplus) * self.AUTO_OPEN_SURPLUS_SHARE_FOR_BLEED
                       + (0.0 if _deep else _line * self.AUTO_OPEN_CREDIT_LINE_BLEED_SHARE))
        return _surplus, _bleed_room

    def _auto_open_institutions(self, caps, _surplus, _bleed_room):
        """Open institution candidates that fit inside this year's bleed
        room, at full size if it fits or as a smaller starter founding
        if it does not - see the inline comment for the starter-founding
        case."""
        opened = []
        for node_id in caps:
            _bleed = self.institution_upkeep(node_id) - self.nodes[node_id]["rev"]
            if _bleed <= _bleed_room:
                ok, _message = self.open_venture(node_id)
                if ok:
                    opened.append(node_id)
                    _surplus -= _bleed
                    _bleed_room -= _bleed
                continue
            # TOO DEAR AT FULL SIZE - FOUND IT SMALLER. This is the actual
            # bridge running() needed and mines already had: workshop_first
            # bled 900 a year against a surplus that was negative BECAUSE
            # there was no workshop, so the full-size gate above refused it
            # for four and a half centuries straight. A place you can only
            # afford a fifth of is still a place; institution_units below
            # 1.0 is what open_venture calls a starter founding.
            if node_id not in self.SCALABLE_INSTITUTIONS or _bleed <= 0:
                continue
            starter = max(0.0, min(1.0, _bleed_room / _bleed))
            if starter < self.STARTER_FOUNDING_MIN_UNITS:
                continue
            ok, _message = self.open_venture(node_id, units=starter)
            if ok:
                opened.append(node_id)
                _spent = _bleed * starter
                _surplus -= _spent
                _bleed_room -= _spent
        return opened, _surplus, _bleed_room

    def _auto_expand_institutions(self, _surplus, _deep_arrears):
        # CLIMB THE LADDER ONCE IT IS OPEN - BUT ONLY ON REAL MONEY AND REAL
        # DEMAND, NOT ON THE STARTER FOUNDING'S CREDIT ALLOWANCE: `_bleed_room`
        # includes a TENTH OF THE CREDIT LINE, the borrowing allowance the
        # starter founding above genuinely needs to break the initial
        # deadlock. Reusing it here to grow an already-open institution would
        # look affordable most years without ever checking whether the
        # household could actually CARRY the resulting upkeep against its
        # actual revenue. Every further unit is discretionary growth, not
        # survival, and discretionary growth has no business spending a
        # bootstrap allowance meant for the one step that has none.
        # So: real cash flow only (no credit line here), and only when the
        # place is actually full enough to want more room - a household with
        # 14 people is not short of a 12-place workshop, whatever it can
        # technically still borrow.
        opened = []
        if _surplus > 0.01 and not _deep_arrears:
            for node_id in sorted(self.SCALABLE_INSTITUTIONS):
                if node_id not in self.household.operating or _surplus <= 0.01:
                    continue
                have = self.institution_units(node_id)
                ceiling = self.institution_unit_ceiling(node_id)
                room = ceiling - have
                if room < self.AUTO_EXPAND_MIN_ROOM_UNITS:
                    continue
                places_now = self.institution_places(node_id) * have
                if self.headcount() < places_now * self.AUTO_EXPAND_MIN_OCCUPANCY:
                    continue        # not full enough yet to be worth more
                per_unit = self.nodes[node_id]["up"] - self.nodes[node_id]["rev"]
                # AT MOST A QUARTER OF THIS YEAR'S REAL SURPLUS, and at most
                # one further unit a year - growth, not a second bootstrap.
                afford_room = _surplus * self.AUTO_EXPAND_SURPLUS_SHARE
                step = min(1.0, room) if per_unit <= 0 else \
                    max(0.0, min(1.0, room, afford_room / per_unit))
                if step < self.AUTO_EXPAND_MIN_STEP_UNITS:
                    continue
                ok, _message = self.open_venture(node_id, units=step)
                if ok:
                    opened.append(node_id)
                    _spent = max(0.0, per_unit) * step
                    _surplus -= _spent
        return opened, _surplus

    def _auto_open_ordinary_ventures(self, cands, _deep_arrears):
        # A CONCERN THAT PAYS FOR ITS OWN DOOR WITHIN A SEASON OR TWO IS A
        # DIFFERENT CASE FROM UNCONSTRAINED BORROWING: that failure mode is
        # ventures whose capex is large against their annual net - borrow to
        # the hilt, and the debt outruns what they pay back before they even
        # finish ramping up. A venture whose capex clears inside
        # PAYBACK_LIMIT_YEARS is the opposite case: refusing it while deep in
        # arrears leaves its capex sunk for nothing, which helps neither the
        # household nor whoever it owes. `open_venture` still refuses, on its
        # own numbers, anything whose capex cannot actually be raised or
        # whose supervision cannot actually be staffed - this only widens
        # what is even offered to it while the household is deep in arrears.
        opened = []
        PAYBACK_LIMIT_YEARS = self.AUTO_OPEN_PAYBACK_LIMIT_YEARS
        blocked = None
        for node_id in cands:
            # NO SECOND, STRICTER GATE. This broke out the moment capital went
            # negative, so a household in arrears could never open anything -
            # and opening a concern is the only way to stop being in arrears.
            # An England run went into the red in its first year, logged
            # "tex_horizontal_loom would earn 400 a year against 30 of upkeep
            # and is still shut: you have no money to open it with" for a
            # century, and settled its debts twenty-eight times over seven
            # hundred years. open_venture already refuses what you cannot
            # raise, and a lender will advance against a shop with stock in it
            # as readily as against half-built work.
            if _deep_arrears:
                node = self.nodes[node_id]
                _payback = self.venture_capex(node_id) / max(0.01, node["rev"] - node["up"])
                if _payback > PAYBACK_LIMIT_YEARS:
                    if blocked is None:
                        blocked = (node_id, ("it would take %.1f years to pay for its "
                                       "own doors, and nothing slower than %.0f "
                                       "opens while you are this deep in arrears; "
                                       "clear enough debt to cross half your "
                                       "credit line, or wait for it to look "
                                       "quicker against what you can raise"
                                       % (_payback, PAYBACK_LIMIT_YEARS)))
                    continue
            ok, why = self.open_venture(node_id)
            if ok:
                opened.append(node_id)
            elif blocked is None:
                blocked = (node_id, why)
        return opened, blocked

    def _auto_open_log_blocked(self, blocked, opened):
        """Say why the best candidate stayed shut, if nothing at all
        opened this year - see the comment below for why silence here
        is indistinguishable from a broken policy."""
        # SAY WHY THE BEST ONE STAYED SHUT: throwing away every refusal
        # open_venture hands back would let a concern earning far more than
        # its upkeep sit closed indefinitely with the policy switched on. A
        # policy that silently declines is indistinguishable from a policy
        # that is broken.
        if blocked and not opened:
            node_id, why = blocked
            said = getattr(self.household, "_said_autoopen", {})
            if self.year - said.get(node_id, -99) >= 10:
                said[node_id] = self.year
                self.household._said_autoopen = said
                self.household.log.append((self.year,
                                 "%s would earn %s a year against %s of upkeep and "
                                 "is still shut: %s"
                                 % (node_id, "{:,.0f}".format(self.nodes[node_id]["rev"]),
                                    "{:,.0f}".format(self.nodes[node_id]["up"]),
                                    why or "something is in the way")))

    def mothball_work(self, k):
        """Shut a completed work down to stop paying its upkeep.

        The lever for a finished, running institution that is a drag on
        upkeep, distinct from `stop` (which only cancels work still in
        progress) - without it, the only way to change what a household is
        paying for is to start MORE things. It is not free: you lose what
        the work gave you, and restoring it costs a fraction of building
        it.
        """
        if k not in self.nodes:
            return False, "no such node"
        if k not in self.household.done:
            return False, "you have not built that"
        if k in self.household.granted:
            return False, ("that is something the society has, not something you "
                           "maintain; there is no upkeep of yours to stop")
        # MONEY IS NOT THE ONLY THING THIS TOOL CAN FREE: refusing whenever
        # upkeep is zero, on the theory that nothing would be saved, is true
        # of the money and false of the staff - a concern with no money
        # upkeep at all can still tie up a fraction of a scholar or
        # craftsman in venture_hands (a going concern's "your people already
        # spoken for" table), which is exactly the fraction a player can be
        # short of even when there is "nothing to save" in money terms. Ask
        # what THIS tool actually releases (money upkeep, and, if it is
        # running, supervision time) rather than asking about money alone.
        sch_held, art_held = self.venture_hands(k) if k in self.household.operating else (0.0, 0.0)
        if self.nodes[k]["up"] <= 0 and sch_held <= 0.005 and art_held <= 0.005:
            return False, ("that has no money upkeep of yours to stop paying, and "
                           "nobody of yours is tied up supervising it either; "
                           "there is nothing to save")
        # A DELIBERATE SHUTDOWN IS NOT AN ABANDONMENT: never_abandon exists
        # to stop the ENGINE quietly deleting a step a player needs and then
        # refusing to fund rebuilding it. A player choosing to close
        # something down is the opposite - they chose it, and restore
        # brings it back. Blocking this here would leave upkeep that is
        # bankrupting a player as the one thing they are not allowed to
        # stop paying for, turning a bad year into an unrecoverable
        # softlock. Knowledge still cannot be unlearned; a building can
        # always be shut.
        if self.never_abandon(k) and self.nodes[k]["cat"] in self.NEVER_ABANDON:
            return False, ("that is knowledge, or it is who you are here. "
                           "You cannot un-know a thing to save its upkeep")
        # SHUTTING A SHOP DOWN IS NOT FORGETTING HOW IT WORKED: this touches
        # only `operating` (what you run), never `done` (what you know).
        # Conflating them would cost a closed loss-maker its place in the
        # tree, forcing "you will have to restore or rebuild it before you
        # can go on" for a concern that was only ever switched off, not
        # forgotten.
        was_running = k in self.household.operating
        self.household.operating.discard(k)
        self.household.mothballed.add(k)
        if not was_running:
            return True, ("%s was not running, so there was nothing to stop "
                          "paying for. You still know how to do it." % k)
        # SAY WHAT WAS ACTUALLY FREED, not only the money: a concern held
        # together by staff time alone (up<=0, sch_held/art_held>0, the
        # exact case above) is reachable by this method, so the confirmation
        # has to say so, or freeing 0.75 craftsmen would read as a no-op
        # that happened to succeed.
        _freed = []
        if self.nodes[k]["up"] > 0 or self.nodes[k]["rev"] > 0:
            _freed.append("you stop paying %s a year for it and stop earning "
                          "the %s a year it brought in"
                          % ("{:,.0f}".format(self.nodes[k]["up"]),
                             "{:,.0f}".format(self.nodes[k]["rev"])))
        if sch_held > 0.005 or art_held > 0.005:
            _freed.append("it frees %.2f scholars and %.2f craftsmen who were "
                          "tied up supervising it" % (sch_held, art_held))
        return True, ("%s shut down: %s. You still know how to do it, and "
                      "'restore %s' opens it again"
                      % (k, "; ".join(_freed), k))

    RESTORE_COST_MIN_UPKEEP_YEARS = declare(
        "RESTORE_COST_MIN_UPKEEP_YEARS", 2.0, kind="temporary_heuristic",
        unit="years of upkeep", source=None, confidence="D",
        why="A floor under restore's cost from the node's own upkeep, not "
            "only a share of build cost - thirty per cent of a cheap-to-"
            "build node is nothing, and this closed the hole where a "
            "cheap node could be mothballed and restored every tick for "
            "free (see this function's own comment). Twice what mines' "
            "own mothball-reversal already implies is not free either; "
            "tuned, not measured.")

    def restore_work(self, k):
        """Bring a mothballed work back, and open its doors again.

        It costs about twice what `open` costs on its own, because it does two
        things: it puts the plant back up - which rotted while it stood idle -
        and it starts the concern trading. `open` alone assumes the plant is
        still there.
        """
        if k not in getattr(self.household, "mothballed", set()):
            return False, "you have not shut that down"
        if k not in self.household.done:
            return False, ('you no longer know how to do that, so there is '
                           'nothing to reopen: build it again with '
                           '{"cmd":"start","id":"%s"}' % k)
        node = self.nodes[k]
        # A FLOOR FROM THE UPKEEP, not only a share of the build cost: thirty
        # per cent of nothing is nothing, so a node that costs nothing to
        # build while costing 20 a year to keep could otherwise be shut down
        # and brought back around the annual tick for free, making its
        # upkeep optional. The engine already gets this right for mines -
        # `quote mine` says in as many words that mothballing is not free to
        # reverse, because the shaft floods and the crew disperses. Two
        # years of the upkeep avoided is what it costs to find the people
        # and the plant again.
        fee = max(self.project_cost(k) * self.RESTORE_COST_SHARE_OF_BUILD,
                  node["up"] * self.RESTORE_COST_MIN_UPKEEP_YEARS)
        # THE SAME GRACE `open` GIVES: a concern the staffing rule shut is a
        # shop whose keeper was lost, not a work that was abandoned.
        # open_venture charges a tenth to reopen one within a few years and
        # says so in the closing message; `restore` - the verb a player
        # actually reaches for - must honour that same discount, or a
        # player pays double what the closing message promised.
        _shut = getattr(self.household, "shut_for_staff", {})
        _in_grace = k in _shut and self.year - _shut[k] <= self.STAFF_CLOSURE_GRACE
        # SAY WHICH CASE THIS IS, not just a number: the closing message
        # promises "reopening soon costs a tenth of what opening did", so a
        # player who comes back to `restore` after the grace window has
        # lapsed and is billed the full price needs a line connecting that
        # to the promise and saying the window is gone - a number with no
        # account of itself reads as broken whether it is wrong or merely
        # unexplained.
        _grace_note = None
        if k in _shut:
            if _in_grace:
                fee *= self.STAFF_CLOSURE_DISCOUNT
                _grace_note = ("the staffing window is still open (shut %d "
                               "years ago, of %d allowed), so this is the "
                               "discounted tenth, not the full price"
                               % (self.year - _shut[k], self.STAFF_CLOSURE_GRACE))
            else:
                _grace_note = ("the staffing discount only lasts %d years "
                               "after a closure, and it has been %d - too "
                               "long for the tenth, so this is the full "
                               "price, the same as rebuilding the plant "
                               "from nothing"
                               % (self.STAFF_CLOSURE_GRACE, self.year - _shut[k]))
        if fee > self.spending_power("buy"):
            return False, ("bringing it back costs %s denarii%s, and between "
                           "%s in cash and what anyone will advance against a "
                           "purchase you can raise %s"
                           % ("{:,.0f}".format(fee),
                              ("; " + _grace_note) if _grace_note else "",
                              "{:,.0f}".format(self.household.capital),
                              "{:,.0f}".format(self.spending_power("buy"))))
        if any(prereq_id not in self.household.done for prereq_id in node["pre"]):
            return False, ("you no longer have what it stands on: "
                           + ", ".join(prereq_id for prereq_id in node["pre"] if prereq_id not in self.household.done))
        self.household.capital -= fee
        self.household.done.add(k)
        self._done_changed()
        self.household.mothballed.discard(k)
        # Back in service means back in OPERATION: restore is what a player
        # types to reopen something they shut, so it must put it back on the
        # books rather than leaving it known-but-closed.
        if self.is_venture(k):
            self.household.operating.add(k)
        return True, ("%s back in service for %s denarii%s"
                      % (k, "{:,.0f}".format(fee),
                         (" (%s)" % _grace_note) if _grace_note else ""))

