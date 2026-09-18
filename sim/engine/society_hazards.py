"""Hazards, their timelines, and the losses they cause.

Split out of sim/engine/society.py, which had grown to 3,809 lines holding
one SocietyMixin with 61 methods. This piece is everything about a dated
hazard once it is a live threat rather than a source of state pressure:
what built defences take off it (hazard_relief, _military_war_relief), how
long a hedge has left to be built (_calendar_floor_remaining, hazard_advice,
hedge_first_steps), when it lands (_yr_words, hazard_timeline), what a loss
does to the household (lose_capital, _resolve_hazard_condition, _shocks,
_random_events, _loss_words), and the one path out of a run
(_catastrophe). `_shocks` is 395 lines and is called every year from
Sim.step(); it is left undecomposed here, as instructed, for someone else
to take on separately. These are methods of Sim; they are a mixin only so
that they can live in a file of their own. Behaviour is unchanged and
verified byte-identical.
"""
from constants import declare
from .data import (closure, critical_path)
from .hazard_window import hazards_not_yet_past


class HazardsMixin:

    def hazard_relief(self, kind):
        """How much of one kind of harm the things you have built take off.

        Returns (multiplier, [what did it]). Diminishing: each counter removes a
        share of what is LEFT, so five partial answers are strong and none of
        them is a switch that turns history off.
        """
        mult, why = 1.0, []
        for node, share, label in self.HAZARD_COUNTERS.get(kind, ()):
            if node == "_own_gold":
                got = self.mine_capacity.get("gold", 0.0) > 0.0005
            elif node == "_own_silver":
                got = self.mine_capacity.get("silver", 0.0) > 0.01
            else:
                got = self.has(node)
            if got:
                mult *= (1.0 - share)
                why.append(label)
        if kind == "output_factor":
            war_relief, reason = self._military_war_relief()
            if reason:
                mult *= war_relief
                why.append(reason)
            # THE STATE'S OWN ARMIES, NOT ONLY THE FOUNDER'S WORKSHOP - see
            # "WAR: A STATE THAT IS ACTUALLY ARMED" above.
            state_relief, reason2 = self._state_military_diffusion_relief(
                self.STATE_MIL_RELIEF_CAP_OUTPUT)
            if reason2:
                mult *= state_relief
                why.append(reason2)
        elif kind == "sack_chance":
            # The founder's own walls and guns already sit in
            # HAZARD_COUNTERS["sack_chance"] above, has()-gated like every
            # other private hedge. This is the part that was missing: "give
            # the Roman government cannons and it is not being sacked by
            # tribes" is a claim about the STATE's army, which diffuses in
            # slowly and only once there is a patron to hand it to.
            state_relief, reason2 = self._state_military_diffusion_relief(
                self.STATE_MIL_RELIEF_CAP_SACK)
            if reason2:
                mult *= state_relief
                why.append(reason2)
        return mult, why

    MILITARY_WAR_RELIEF_CAP = declare(
        "MILITARY_WAR_RELIEF_CAP", 0.30, kind="temporary_heuristic",
        unit="dimensionless (fraction of war output-shock relieved at "
             "military_leverage=1.0)", source=None, confidence="D",
        why="Ceiling on how much a founder's own military work softens an "
            "output-crushing war - matched to endowment_land's own share "
            "in HAZARD_COUNTERS['output_factor'] rather than exceeding it, "
            "so land and an army are comparable hedges and neither dwarfs "
            "the other (see this method's own docstring). A relative "
            "calibration against another already-tuned figure, not a "
            "measured relief rate.")

    def _military_war_relief(self):
        """A state that can fight loses less of its economy when it has to.

        Every output_factor hazard in every civilization file - Rome's third
        century crisis and Gothic settlement, Han's rebellions and
        fragmentations, England's civil wars, the Mexica wars of
        independence and revolution - IS a war, a rebellion, or the
        administrative aftermath of one; none of them is a plague or a
        famine, which hit staff_loss and real_erosion instead (see the
        `years` these hazards share with `sack_chance` and `values` in the
        civilization files). So this is not gated per-hazard the way
        HAZARD_COUNTERS entries are: it is one diminishing term, on the same
        military_leverage() count update_protection() reads, applied
        wherever `output_factor` is. Deliberately NOT applied to staff_loss:
        a founder with cannon should not cure the Antonine plague, and most
        staff_loss hazards in the civilization files are exactly that -
        disease and famine - with no sack_chance or output_factor alongside
        them to say otherwise.

        Capped at 0.30, matching endowment_land's own share in
        HAZARD_COUNTERS["output_factor"] rather than exceeding it: land of
        your own and an army of your own are comparable hedges, and neither
        should dwarf the other.
        """
        lev = self.military_leverage()
        if lev <= 0.0:
            return 1.0, None
        share = self.MILITARY_WAR_RELIEF_CAP * lev
        return (1.0 - share), ("an army and treasury the state can call on "
                               "(military strength %d%%)" % round(lev * 100))

    def _calendar_floor_remaining(self, goal):
        """Minimum calendar years before `goal` is finished, even if every
        prerequisite still open were started TODAY - critical_path()'s own
        floor (see data.py), minus whatever of that chain is already done.

        THE NUMBER THE WARNING WAS MISSING. A Han playtester was told from
        turn one that the hedge against being sacked was "copies of your
        work kept somewhere else" and, having acted on that the moment it
        was said, still lost the corpus to the Yellow Turban rebellion -
        twice, some of it rebuilt and lost again. The advice was right and
        the words never changed; what was missing was that the strongest
        hedge in HAZARD_COUNTERS["sack_chance"] (academy_network, sharing
        0.40 of the risk, the biggest single number in that list) sits at
        the end of scientific_method -> corpus_written -> corpus_dispersed
        -> academy_network, a chain whose OWN yrs fields (data already
        carried, already shown per-node as `calendar_floor_years` by
        protocol.py, and already the basis of the `path` command's own
        "Longest serial chain" line) sum to a 30-year floor - not something
        five years' warning is enough for, and nothing before this said the
        chain had a length at all, only that it existed.

        Reuses critical_path(), the SAME function `path` already calls for
        exactly this question about a goal node - not a second notion of
        "how long something takes" invented for hazards - and only sums the
        portion of the winning chain not already in self.household.done, so a player
        partway through the chain sees what is actually left, not the whole
        chain's floor from scratch every time.
        """
        if goal not in self.nodes:
            return None
        _total, chain = critical_path(self.nodes, goal)
        remaining = sum(max(self.nodes[node_id]["yrs"], self.nodes[node_id]["ph"] / 2000.0)
                        for node_id in chain if node_id not in self.household.done)
        return round(remaining, 1)

    def hazard_advice(self, kind):
        """What KIND of thing would help, without naming what you cannot see.

        Under fog this must not turn into a list of node ids to go and build:
        that is the tech tree by the back door. It names the kind of answer, in
        the same words a person in the year 100 would use.
        """
        words = {"staff_loss": "clean water, quarantine, and eventually inoculation",
                 "sack_chance": "walls, firearms, powerful friends, and copies of "
                                "your work kept somewhere else",
                 "output_factor": "land and power of your own, not depending on trade "
                                  "a war can cut, and a state that can fight back",
                 "real_erosion": "metal you dug yourself, land, and a way to prove "
                                 "what a coin contains"}
        mult, why = self.hazard_relief(kind)
        out = {"you_currently_take": round(mult, 3), "because_of": why}
        if mult > 0.75:
            out["what_would_help"] = words.get(kind, "")
            # AND SOMETHING YOU CAN ACT ON. A playtester was told the answer to
            # the Spanish was "walls, firearms, powerful friends, and copies of
            # your work kept somewhere else", played 154 years, saw 269
            # startable things, and reported finding no hedge of any kind. The
            # hedges were there and shallow - a sand filter needs no
            # prerequisite at all, only one artisan you do not have yet - but
            # advice you cannot act on reads as advice about nothing.
            #
            # This does NOT name the hedge or open the tree. It names things you
            # could begin TODAY, which you can already see, and says only that
            # they lead that way. That is what a person who knows how the
            # technology works would know and what fog has no business hiding:
            # fog is about the society, not about your own education.
            step = self.hedge_first_steps(kind)
            if step:
                out["you_could_begin_now_toward_it"] = step
            # AND HOW LONG BEFORE ANY OF IT HELPS. Numbers only, never a node
            # id, so this tells nothing fog would hide: two playtesters (Han,
            # Rome) each acted on `what_would_help` the moment they read it and
            # were sacked anyway, because the strongest real hedge among these
            # words is not a purchase, it is a multi-decade diffusion chain -
            # see _calendar_floor_remaining's own comment. Given as a range
            # because these words bundle several genuinely different hedges
            # (a patron is bought in a few years; three dispersed academies are
            # not), and the range is the honest shape of the answer: some of
            # this is fast, and the slowest part is not.
            floors = sorted(
                floor_years for node, _share, _label in self.HAZARD_COUNTERS.get(kind, ())
                if not node.startswith("_") and node in self.nodes
                and not self.has(node)
                for floor_years in [self._calendar_floor_remaining(node)]
                if floor_years is not None)
            if floors:
                out["even_started_today_the_real_hedges_here_take_years"] = (
                    {"quickest": floors[0], "slowest": floors[-1]}
                    if floors[0] != floors[-1] else floors[0])
        return out

    def hedge_first_steps(self, kind, limit=4):
        """The hedges against `kind` that you can actually see, and what each
        one is waiting for.

        Deliberately NARROW: the counters themselves and their direct
        prerequisites, and only those fog would let you see anyway. An earlier
        version walked the whole ancestry and ranked by strategy order, which
        duly advised beginning a "respectable cover identity" as a hedge
        against smallpox - true, in that most of the tree is downstream of it,
        and useless to a reader. If nothing near is visible, the words on their
        own are the honest answer and this says nothing.
        """
        want = []
        leads_to = {}
        counters = set()
        for node, _share, label in self.HAZARD_COUNTERS.get(kind, ()):
            if node not in self.nodes or node in self.household.done:
                continue
            want.append((0, node))
            counters.add(node)
            leads_to.setdefault(node, label)
            for pre in self.nodes[node]["pre"]:
                if pre in self.nodes and pre not in self.household.done:
                    want.append((1, pre))
                    # SAY WHAT IT LEADS TO. A break tester was offered
                    # `horse_collar` as the thing to build against the Antonine
                    # plague, directly under prose saying the remedy is "clean
                    # water, quarantine, and eventually inoculation". It is a
                    # prerequisite of crop rotation, which is a real hedge
                    # against a famine year - but nothing said so, and an
                    # unexplained horse collar under a plague warning reads as
                    # the game being broken.
                    leads_to.setdefault(pre, "a step toward %s" % label)
        memo = {}
        seen, out = set(), []
        for distance, node_id in sorted(want):
            if node_id in seen:
                continue
            seen.add(node_id)
            if getattr(self, "fog", False) and not self.is_visible(node_id, _memo=memo):
                continue
            ok, why = self.start_reason(node_id)
            entry = {"id": node_id, "name": self.nodes[node_id]["name"],
                     "cost": round(self.project_cost(node_id), 1),
                     "because_it_gives_you": leads_to.get(node_id),
                     "can_begin_now": bool(ok),
                     "waiting_on": None if ok else why}
            # THE WHOLE ROAD, not just this one node's own calendar floor. A
            # step that "can begin now" and costs little reads as quick; for
            # a HAZARD_COUNTERS entry itself (not one of its prerequisites)
            # this is often the LAST of several such steps, each looking
            # equally beginnable, with a total the size of a human generation
            # behind it. See _calendar_floor_remaining.
            if node_id in counters:
                floor = self._calendar_floor_remaining(node_id)
                if floor is not None:
                    entry["years_even_if_you_start_today"] = floor
            out.append(entry)
            if len(out) >= limit:
                break
        # What you can start comes first: it is the part you can act on today.
        out.sort(key=lambda e: not e["can_begin_now"])
        return out

    # ---- A TIMELINE, NOT A WALL OF TEXT THAT NEVER CHANGES -----------------
    # `risk` already had dates, yearly odds, cumulative danger and what prior
    # choices buy against each - a winning player called that combination one
    # of the strongest systems in the game. What it did not have was ONE
    # compact, chronological answer to "what is coming, how soon, and am I
    # covered" - that reply is scattered across a single flat `hedged_by`
    # (one word for the whole civilisation, not per hazard) and a list of
    # hazard rows each carrying its own sack/staff-loss percentages several
    # keys deep. And `hedged_by` itself never changed its wording as a date
    # got closer: a Rome player watched it read "nothing yet" for a hundred
    # and fifty years, across a hazard that eventually arrived anyway, and
    # lost 22 technologies, 1.38 million denarii and 47 staff in the single
    # turn it landed - a third of their critical-path progress. The words had
    # been true every one of those years and had stopped being a WARNING long
    # before that, because a sentence that reads identically five years out
    # and a hundred and fifty years out carries no information about which of
    # those it is.
    #
    # THE FIX IS NOT A COUNTDOWN. A bare "N years left" still reads the same
    # at every distance greater than zero - what actually has to escalate is
    # the relationship between the calendar and the hedge itself. The real
    # hedges in HAZARD_COUNTERS have lead times of their own (see
    # _calendar_floor_remaining - up to thirty years for academy_network's
    # own dispersal chain) and a hazard that is fifty years off with a five-
    # year hedge is not urgent, while the SAME fifty years against a thirty-
    # year hedge is already something to be starting now, not later - it is
    # the gap between the two clocks that should set the tone, not either
    # clock alone.
    #
    # Three clean levels come out of comparing "years until it arrives" to
    # "years the live hedges still need". Two such lead times are kept, not
    # one, because they escalate at DIFFERENT moments: the QUICKEST counter
    # among HAZARD_COUNTERS (some relief, soonest) and the SLOWEST (the
    # strongest one among the same counters - the thirty-year
    # academy_network dispersal chain, for sack_chance). A player still has
    # time to begin the quick, partial answer well after it is already too
    # late for the one actually carrying the largest share of the relief, so
    # the bands below are four, nearest first (HORIZON_MULT gives the margin
    # on the furthest boundary - calm vs "begin now" - because a player who
    # starts exactly on the strong hedge's own floor has no slack left for
    # anything going wrong with it):
    #   - past the strong hedge's own floor by a comfortable margin: plenty
    #     of time, said once and then left alone.
    #   - inside that margin, strong hedge not yet begun: begin it now -
    #     there is still time, but not much of it.
    #   - past the strong hedge's own floor, but still within the quick
    #     hedge's: a partial answer can still finish; the real one cannot.
    #   - past even the quick hedge's own floor: too late to finish anything
    #     from a cold start; the event is coming regardless of what begins
    #     today.
    # A hazard already well hedged, or already in progress, or with no known
    # hedge at all, reports that plainly instead of forcing it into one of
    # these four bands.
    HAZARD_TIMELINE_BEGIN_NOW_MULT = 1.5
    # Which urgency tags keep their full sentence once a row is past the
    # nearest one - see the note where this is applied, in hazard_timeline
    # itself, for why position in the list is the wrong thing to key this on.
    HAZARD_TIMELINE_WARN_TAGS = frozenset(
        {"happening now", "too late to hedge", "stopgap only", "begin hedge now"})

    @staticmethod
    def _yr_words(n):
        n = round(n)
        return "%d year" % n if n == 1 else "%d years" % n

    def hazard_timeline(self, limit=4):
        """What is coming, how many years off, and whether what stands
        between now and then is enough - one line per hazard, nearest first.

        This is `risk`'s missing compact view: every number in it (years
        until, current relief, the fastest hedge's own lead time) is already
        computed elsewhere in this file (hazard_relief, hazard_advice,
        _calendar_floor_remaining) - this only arranges them chronologically
        and picks the words that should change as the gap between "when it
        lands" and "how long the hedge takes" closes. See the section
        comment above for why that gap, not the bare year count, is what
        actually has to escalate.
        """
        rows = []
        for hazard, year_start, year_end, in_progress in hazards_not_yet_past(
                self.civ, self.year):
            years_until = 0 if in_progress else (year_start - self.year)
            name = hazard.get("name", "hazard")
            kinds = [hazard_kind for hazard_kind in
                     ("staff_loss", "sack_chance", "output_factor", "real_erosion")
                     if hazard_kind in hazard]
            if not kinds:
                continue
            # THE LEAST-DEFENDED SIDE OF IT, not an average, and its OWN
            # hedge's own lead time - not the quickest lead time among ALL
            # the kinds this hazard happens to carry. A hazard that is both
            # a sacking risk (hedged, for real, only by a thirty-year
            # academy_network dispersal chain) and an output shock (hedged
            # by things as quick as two years) is exactly as urgent as the
            # sacking half if that is the half nothing has been built
            # against - taking the faster OTHER kind's lead time here would
            # have said "two years will cover you" about a risk a two-year
            # hedge does nothing for, which is the averaging mistake the
            # section comment above warns against, just one kind's own floor
            # away from where it would actually bite.
            # QUICKEST (some relief, started cold, soonest) and SLOWEST (the
            # strongest real hedge among the same counters - up to the
            # thirty-year academy_network chain for sack_chance) are both
            # kept, because they escalate at DIFFERENT times: a player still
            # has time for a partial answer after it is already too late for
            # the one that actually carries the largest share of the relief.
            worst_mult, quick_hedge, strong_hedge = 0.0, None, None
            for hazard_kind in kinds:
                mult, _why = self.hazard_relief(hazard_kind)
                if mult <= worst_mult:
                    continue
                worst_mult = mult
                quick_hedge = strong_hedge = None
                if mult > 0.75:
                    advice = self.hazard_advice(hazard_kind)
                    hedge_floor = advice.get("even_started_today_the_real_hedges_here_take_years")
                    if isinstance(hedge_floor, dict):
                        quick_hedge, strong_hedge = hedge_floor.get("quickest"), hedge_floor.get("slowest")
                    elif isinstance(hedge_floor, (int, float)):
                        quick_hedge = strong_hedge = hedge_floor
            hedged = worst_mult <= 0.75
            _yu = self._yr_words(years_until)
            if in_progress:
                urgency = "happening now"
                headline = ("%s: under way now%s"
                            % (name, "" if hedged else
                               ", and built defences do not cover most of it"))
            elif hedged:
                urgency = "hedged"
                headline = "%s: %s off, already well hedged" % (name, _yu)
            elif quick_hedge is None:
                urgency = "no hedge found"
                headline = ("%s: %s off, unhedged, no hedge visible yet"
                            % (name, _yu))
            elif years_until <= quick_hedge:
                urgency = "too late to hedge"
                headline = ("%s: only %s left; even the fastest hedge needs "
                            "about %s - it is coming regardless"
                            % (name, _yu, self._yr_words(quick_hedge)))
            elif strong_hedge and strong_hedge > quick_hedge and years_until <= strong_hedge:
                urgency = "stopgap only"
                headline = ("%s: %s off - a quick hedge (%s) could still "
                            "finish, the strong one (%s) could not"
                            % (name, _yu, self._yr_words(quick_hedge),
                               self._yr_words(strong_hedge)))
            elif years_until <= (strong_hedge or quick_hedge) * self.HAZARD_TIMELINE_BEGIN_NOW_MULT:
                urgency = "begin hedge now"
                headline = ("%s: %s off; the real hedge needs %s - time is "
                            "short" % (name, _yu,
                                      self._yr_words(strong_hedge or quick_hedge)))
            else:
                urgency = "on the horizon"
                headline = ("%s: %s off, unhedged, plenty of time to build "
                            "one (%s)" % (name, _yu,
                                          self._yr_words(strong_hedge or quick_hedge)))
            rows.append({"name": name, "years_until": years_until,
                         "in_progress": in_progress, "urgency": urgency,
                         "headline": headline})
        rows.sort(key=lambda r: (0 if r["in_progress"] else 1, r["years_until"]))
        rows = rows[:limit]
        # COMPACT EXCEPT WHERE IT IS ACTUALLY A WARNING, same reasoning
        # knowledge_risk's own known_hazards_ahead already applies to its
        # "note"/"what_you_can_do" fields, but keyed on URGENCY rather than
        # bare position in the list: a hazard that is calm stays calm
        # whether it is first or sixth on the list, and a hazard that is not
        # - "too late to hedge", "stopgap only", "begin hedge now",
        # "happening now" - is exactly the one case this whole method exists
        # to NOT bury in a compact name-and-number line. The single nearest
        # entry keeps its sentence regardless, so the reply always orients
        # on at least one real sentence even in a run where everything left
        # is calm.
        for i, row in enumerate(rows):
            if i == 0 or row["urgency"] in self.HAZARD_TIMELINE_WARN_TAGS:
                continue
            row.pop("headline", None)
            row.pop("in_progress", None)
        return rows

    def lose_capital(self, fraction):
        """Destroy a fraction of what you HAVE. Never a fraction of what you owe.

        Every capital loss in this file used to be written `self.household.capital *= x`,
        which is sign-blind: at minus a thousand denarii a sacking multiplied
        the DEBT by 0.4 and handed the player six hundred denarii. A sweep of
        the playtest notes caught it live twice - a Mexica sack took -251 to
        -100.5, an England thatch fire took -629.2 to -569.4 - which made the
        deepest hole in the game the safest place to stand, and made every
        catastrophe a reason to stay in arrears.

        A fire destroys goods. If you own nothing, the fire takes nothing; it
        does not pay off your creditors.
        """
        # ALWAYS floored, never optionally. This took a floor_at_zero=True
        # parameter that nothing read and no caller ever passed - the floor
        # below is unconditional - so the signature advertised a choice that
        # did not exist: floor_at_zero=False would have been accepted and
        # silently ignored, which is worse than not offering it.
        if self.household.capital <= 0:
            return 0.0
        lost = self.household.capital * max(0.0, min(1.0, fraction))
        self.household.capital -= lost
        return lost

    def _resolve_hazard_condition(self, h, yr, a):
        """History on rails, but the household is allowed to have changed
        the ground it runs on.

        A dated hazard's `years` window used to be the whole story: the
        Third-Century Crisis or the African grain fleet failing in 439 fired
        on schedule no matter what the player had built, which is the exact
        complaint a player who had spent three centuries industrialising
        made - technology changed how much a hazard hurt, never whether it
        happened. This is the fix, and it is deliberately narrow: only a
        hazard whose CIVILIZATION FILE gives it a `condition` is touched at
        all, so a hazard with none - which is most of them - fires exactly
        as before. See the civilization files themselves for which hazards
        got one and why: in every case the note names a MATERIAL cause (a
        supply line, a building material, a drainage engine) that a rich
        household's own building can plausibly remove, never a succession, a
        religious policy or an administrative reform - one household in 300
        AD did not choose the emperor, and none of those hazards carry a
        `condition` at all.

        `condition` names exactly one numeric field on the hazard
        (`field`), a list of tech ids the player must have ALL of
        (`requires_all`), and what happens when they do (`outcome`:
        "avert" drops the field for this hazard entirely, "alter" scales
        it via `alter_scale`, which is how much of the ORIGINAL shortfall
        - 1 minus the field, for output_factor; the field itself for the
        rest - survives). Returns `h` unchanged, or a SHALLOW COPY with
        that one field adjusted; every other field on the hazard (a sack
        risk, a values shift) is untouched, because a household that fed
        itself did not thereby also arm itself or convert the Church.

        Told, not silent, in all three cases - fires as written, fires
        altered, or is averted - the once, the year the hazard's window
        opens (`yr == a`), keyed on the hazard's own name so a multi-year
        window does not repeat itself every year it stays open.
        """
        cond = h.get("condition")
        if not cond:
            return h
        field = cond.get("field")
        need = cond.get("requires_all") or []
        met = all(self.has(tech_id) for tech_id in need)
        if yr == a:
            said = self._said_condition
            key = h.get("name", "hazard")
            if key not in said:
                said.add(key)
                msg = cond.get("met_message" if met else "unmet_message")
                if msg:
                    self.household.log.append((yr, msg))
        if not met or field not in h:
            return h
        adjusted = dict(h)
        outcome = cond.get("outcome")
        scale = cond.get("alter_scale", 1.0)
        if outcome == "avert":
            del adjusted[field]
        elif outcome == "alter":
            if field == "output_factor":
                adjusted[field] = 1.0 - (1.0 - h[field]) * scale
            else:
                adjusted[field] = h[field] * scale
        return adjusted

    STAFF_LOSS_HAZARD_ANNUAL_CHANCE = declare(
        "STAFF_LOSS_HAZARD_ANNUAL_CHANCE", 0.32, kind="temporary_heuristic",
        unit="dimensionless (yearly probability while the hazard's window "
             "is open)", source=None, confidence="D",
        why="Chance, in any given year of a staff_loss hazard's dated "
            "window, that it actually strikes this year rather than "
            "passing quietly - a multi-year plague window does not bite "
            "every single year of it. Tuned so the hazard is likely but "
            "not certain within its window; not fitted to any attested "
            "epidemic-year distribution.")
    PLAGUE_CASH_LOSS_SHARE = declare(
        "PLAGUE_CASH_LOSS_SHARE", 0.6, kind="temporary_heuristic",
        unit="dimensionless (fraction of the staff-loss fraction)",
        source=None, confidence="D",
        why="How much capital a staff-loss hazard also takes, as a "
            "multiple of the staff fraction lost - a plague empties the "
            "market as well as the workshop (see comment above). Tuned to "
            "make the cash loss proportionate to the staff loss, not "
            "measured against any attested plague-year revenue collapse.")
    # PLAGUE_RECOVERY_YEARS_REFERENCE / PLAGUE_RECOVERY_REFERENCE_SEVERITY
    # used to live here: a fixed 150-year recovery horizon, itself flagged
    # as a CLAUDE.md SS3.1/3.2 risk (a real attested demographic OUTCOME -
    # how long England specifically took to recover from one specific
    # plague - used directly as the model's recovery-speed parameter,
    # rather than a rate derived from fertility, mortality decline and the
    # land-labour ratio). WIRING MILESTONE 4 (docs/architecture/
    # WIRING_MILESTONE_4.md) removes both: recovery is now whatever
    # self.population's own vital rates produce on the surviving cohort
    # structure (core.py's _apply_population_mortality_shock/pop_scale/
    # wage_index), not a number this hazard hands out at the moment it
    # fires - the exact CLAUDE.md SS3.1 fix their own "why" asked for.
    SACK_CAPITAL_LOSS = declare(
        "SACK_CAPITAL_LOSS", 0.60, kind="temporary_heuristic",
        unit="dimensionless (fraction of capital)", source=None,
        confidence="D",
        why="Fraction of capital a sack takes - the largest single-event "
            "capital loss in this file, reflecting that a raid can carry "
            "off cash and portable goods wholesale. Tuned, not measured "
            "against any attested sacking's proceeds.")
    SACK_STAFF_RETENTION = declare(
        "SACK_STAFF_RETENTION", 0.55, kind="temporary_heuristic",
        unit="dimensionless (fraction of artisans/scholars/hired staff "
             "kept)", source=None, confidence="D",
        why="Fraction of artisans, scholars and every hired trade kept "
            "after a sack - applied uniformly across every trade so a "
            "sack is not gentler to hired staff than the plague family is "
            "(see comment above). Tuned, not measured.")
    REAL_EROSION_CASH_LOSS_SHARE = declare(
        "REAL_EROSION_CASH_LOSS_SHARE", 0.85, kind="temporary_heuristic",
        unit="dimensionless (fraction of the debasement rate)",
        source=None, confidence="D",
        why="How much of a currency debasement's rate also bites the "
            "cash actually held, on top of the money_real devaluation "
            "applied to everything - debasement destroys held coin faster "
            "than it destroys quoted labour/material costs (see this "
            "branch's own comment). Tuned, not measured against any "
            "attested debasement episode's real losses.")
    SACK_DIRECTORS_RETENTION = declare(
        "SACK_DIRECTORS_RETENTION", 0.65, kind="temporary_heuristic",
        unit="dimensionless (fraction of deputy directors kept)",
        source=None, confidence="D",
        why="Fraction of deputy directors kept after a sack - higher than "
            "SACK_STAFF_RETENTION on the reasoning that the institutions "
            "producing deputies are more resilient than ordinary staff on "
            "the ground. Tuned, not measured.")

    def _shocks(self, yr):
        """Dated catastrophes, read from the CIVILIZATION file.

        Rome gets the Antonine plague and the third century crisis. England 1300
        gets the Great Famine and the Black Death. The Mexica get the contact
        epidemics, which are the most severe hazard in the whole directory and
        are not a fair fight. None of it is hardcoded here any more.
        """
        rng = self.rng
        for hazard in self.civ.get("hazards", []):
            hazard_start, hazard_end = hazard.get("years", [0, 0])
            if not (hazard_start <= yr <= hazard_end):
                continue
            hazard = self._resolve_hazard_condition(hazard, yr, hazard_start)
            if "staff_loss" in hazard and rng.random() < self.STAFF_LOSS_HAZARD_ANNUAL_CHANCE:
                relief, why = self.hazard_relief("staff_loss")
                loss = hazard["staff_loss"] * relief
                _people_before = (self.household.scholars + self.household.artisans
                                  + sum(self.household.employees.values()))
                self.household.scholars *= (1 - loss); self.household.artisans *= (1 - loss)
                for trade in list(self.household.employees):
                    self.household.employees[trade] *= (1 - loss)
                self.household.directors_extra *= (1 - loss)
                # THE MONEY GOES TOO, and the log never said so. A weird-play
                # tester watched the Black Death take 12,676 denarii down to
                # 9,111 against a stated net of -195 a year, with the only
                # message reading "staff -45%", and reasonably concluded the
                # accounts were broken. A plague empties the market as well as
                # the workshop; that is real, and it has to be said.
                cash = self.lose_capital(loss * self.PLAGUE_CASH_LOSS_SHARE)
                # SAY WHAT ACTUALLY HAPPENED TO YOU. A weird-play tester with no
                # staff and no money read "staff -45%, and 0 pence gone" three
                # years running and reasonably concluded the event was firing
                # against nobody. It was: they had nothing to lose. An event
                # should report the harm it did, not the harm it would have
                # done to somebody else.
                # THE WHOLE SOCIETY LOST PEOPLE TOO, not only your household,
                # and your own hedges do not change that: the quarantine you
                # built protects your people, not everyone else's labour
                # market. A playtester found a plague that hit them and
                # nobody else, and asked why their wage bill never moved
                # afterward the way the real Black Death moved England's.
                # This uses the hazard's RAW rate, never `loss` above, which
                # is personal and already reduced by your own hedges; and
                # cutting self.population's actual cohorts (rather than
                # accumulating a scalar deficit) naturally compounds two
                # plagues in one lifetime onto whatever the first left
                # behind, because the second cut is a fraction of the
                # ALREADY-REDUCED population, not of some separately tracked
                # deficit - see _apply_population_mortality_shock (core.py),
                # which is what actually moves self.population; pop_scale
                # and wage_index (also core.py) read it back out on demand.
                #
                # THE COUNTRY'S OWN MEDICINE, NOT ONLY THE FOUNDER'S - the
                # one thing `raw` never used to answer to. med_relief is
                # medical_diffusion_relief() (above): how much of germ
                # theory, quarantine and vaccination has actually spread
                # through the society by the year this hazard's window
                # opens, as opposed to `relief` just above, which is the
                # founder's own private, has()-gated hedge. A founder who
                # invented the vaccine for a pandemic CENTURIES early and
                # let it diffuse is the user's own example - "the Black
                # Death becomes a minor period of some sickness" - answered
                # here, against the empire-wide figure, never against
                # `loss`.
                historical = hazard["staff_loss"]
                med_relief = self.medical_diffusion_relief()
                raw = historical * (1.0 - med_relief)
                self._apply_population_mortality_shock(raw)
                # The event has happened NOW.  Do not leave the population
                # and wage screens at their pre-plague values until the next
                # annual resolution; refresh (log-only now - see
                # _refresh_demographic_indexes's own docstring) immediately.
                self._refresh_demographic_indexes(yr)
                # SEVERITY HONESTY: the words have to match `loss`, the
                # number the mechanic just applied above, not `raw`, the
                # historical hazard's own unmitigated figure - a tester
                # whose sanitation and quarantine cut a 28% plague down to
                # 0.4% still read "staff -0%... (would have been -28%: ...)"
                # in the same breath, and came away certain they had just
                # lived through a 28% plague, because the sentence restated
                # 28% twice and the near-zero number once. `relief` (mult)
                # is the SAME diminishing fraction hazard_relief and
                # hazard_advice already compute, and hazard_timeline's own
                # "hedged" cutoff is this same 0.75 - reused, not a second
                # estimate of what your hedges did.
                _hit = []
                if _people_before > 0.05:
                    if why and relief <= 0.25:
                        _hit.append("staff -%d%%, held off almost entirely "
                                    "by what you built (%s)"
                                    % (loss * 100, "; ".join(why)))
                    elif why and relief <= 0.75:
                        _hit.append("staff -%d%% (softened by %s)"
                                    % (loss * 100, "; ".join(why)))
                    else:
                        _hit.append("staff -%d%%" % (loss * 100))
                if cash > 0.5:
                    _hit.append("%s gone with the trade that stopped"
                                % "{:,.0f}".format(cash))
                if not _hit:
                    _hit.append("you had nothing it could take")
                msg = "%s: %s" % (hazard.get("name", "hazard"), ", ".join(_hit))
                # THE WHOLE SOCIETY LOST PEOPLE TOO, not only your household,
                # and your own hedges do not change that: the quarantine you
                # built protects your people, not everyone else's labour
                # market (see the comment on `raw` above). Kept as a
                # SEPARATE sentence, explicitly "either way", so a household
                # that came through nearly untouched does not read this
                # empire-wide toll as its own.
                if raw > 0.01:
                    # NO FIXED RECOVERY HORIZON TO QUOTE ANY MORE - see
                    # core.py's _apply_population_mortality_shock/pop_scale:
                    # recovery is now whatever self.population's own vital
                    # rates produce on the surviving cohort structure, not a
                    # number this hazard hands out at the moment it fires.
                    msg += (". Empire-wide, population -%d%%%s - wages (and "
                            "everything paid in them) stay dear until the "
                            "population does, either way"
                            % (raw * 100,
                               (" (the country's own public health has "
                                "spread far enough to hold this below the "
                                "%d%% this would otherwise have been - "
                                "%d%% softer)"
                                % (round(historical * 100),
                                   round(med_relief * 100)))
                               if med_relief > 0.02 else ""))
                elif med_relief > 0.02 and historical > 0.01:
                    # THE COUNTRY CHANGED, SAY SO EVEN WHEN THE NUMBER
                    # ROUNDS TO NOTHING. A founder whose diffused medicine
                    # has cut a plague to under 1% empire-wide would
                    # otherwise see no "Empire-wide" clause at all and have
                    # no way to tell a mechanism that fired from one that
                    # never existed.
                    msg += (". Empire-wide: the country's own public health "
                            "- not only yours - has spread far enough that "
                            "this, historically a %d%% loss, barely "
                            "registers"
                            % round(historical * 100))
                self.household.log.append((yr, msg))
            if "sack_chance" in hazard:
                relief, why = self.hazard_relief("sack_chance")
                probability = hazard["sack_chance"] * relief
                if why and rng.random() < hazard["sack_chance"] - probability:
                    self.household.log.append((yr, "%s: an attack comes to nothing (%s)"
                                     % (hazard.get("name", "crisis"), "; ".join(why[:3]))))
                if rng.random() < probability:
                    # SAY WHAT IT TOOK FROM YOU. This printed "a site is
                    # sacked" and nothing else while removing 62% of a
                    # weird-play tester's money, restarting every project they
                    # had and cutting their people nearly in half - and they
                    # owned no sites at all. The plague family was taught to
                    # report the harm it actually did; this one was not, and a
                    # bare event line against an unexplained fall in capital is
                    # how a player stops trusting the ledger.
                    _cap0 = max(0.0, self.household.capital)
                    # EVERY TRADE YOU HIRED, NOT ONLY THE TWO GENERIC POOLS.
                    # A player watched the event announce "92.7 of your
                    # people gone" and then read `state`'s employees_total -
                    # the headcount screen actually shows - sitting exactly
                    # where it was. This branch reduced artisans, scholars
                    # and directors_extra and left self.household.employees (hired
                    # smiths, scribes, masons - for a developed household,
                    # most of its people) completely untouched, while the
                    # plague family right above DOES reduce employees (see
                    # its own `for t in self.household.employees` loop). A sack is not
                    # gentler to hired staff than a plague; the two hazards
                    # had simply drifted apart. _people0/_people_after now
                    # count the same population the announcement claims to
                    # describe and `state` actually renders.
                    _people0 = (self.household.artisans + self.household.scholars
                                + sum(self.household.employees.values()))
                    _act0 = len(self.household.active)
                    self.lose_capital(self.SACK_CAPITAL_LOSS)
                    self.household.artisans *= self.SACK_STAFF_RETENTION; self.household.scholars *= self.SACK_STAFF_RETENTION
                    for trade in list(self.household.employees):
                        self.household.employees[trade] *= self.SACK_STAFF_RETENTION
                    self.household.directors_extra *= self.SACK_DIRECTORS_RETENTION
                    for node_id in sorted(self.household.active):
                        self.household.active[node_id]["ph_left"] = self.nodes[node_id]["ph"]
                        self.household.active[node_id]["yrs"] = 0.0
                    _people_after = (self.household.artisans + self.household.scholars
                                     + sum(self.household.employees.values()))
                    _took = []
                    if _cap0 - max(0.0, self.household.capital) > 0.5:
                        _took.append("%s taken"
                                     % "{:,.0f}".format(_cap0 - max(0.0, self.household.capital)))
                    if _people0 - _people_after > 0.05:
                        _took.append("%.1f of your people gone"
                                     % (_people0 - _people_after))
                    if _act0:
                        _took.append("%d project%s back to the beginning"
                                     % (_act0, "" if _act0 == 1 else "s"))
                    self.household.log.append((yr, "%s: a site is sacked - %s"
                                     % (hazard.get("name", "crisis"),
                                        ", ".join(_took)
                                        or "you had nothing it could take")))
                    # Sim.corpus_hedge (core.py) is the one place this is
                    # decided, and `risk` calls the same method - see its
                    # own comment for why this used to quote `running()`
                    # and tell a player, in `risk`, that they had a hedge
                    # `running()` said had already lapsed.
                    corpus_loss_probability, frac, _hedge_before = self.corpus_hedge()
                    if rng.random() < corpus_loss_probability:
                        # sorted() matters: self.household.done is a SET and iterates in an
                        # order that depends on PYTHONHASHSEED, so feeding it
                        # unsorted to rng.sample made the same --seed give a
                        # different answer every invocation.
                        # Never the society's own inheritance: you can lose what
                        # YOU built, not what the civilization has always known.
                        # Nor corpus_dispersed: its whole definition is that
                        # copies exist in other people's hands, beyond this
                        # one site - a sack here cannot reach a copy sitting
                        # in a library three provinces away. corpus_written,
                        # one set of books in one place, stays losable; only
                        # dispersal is out of a single raid's reach. This is
                        # about a SACK specifically - mothballing or
                        # abandoning the corpus yourself is a different
                        # mechanism and still applies.
                        losable = sorted(node_id for node_id in self.household.done
                                         if node_id not in self.household.granted
                                         and node_id != "corpus_dispersed")
                        if losable:
                            drop = rng.sample(losable, max(1, int(len(losable) * frac)))
                            _lost = self.household.forgotten
                            for node_id in drop:
                                self.household.operating.discard(node_id)
                                self.household.done.discard(node_id)
                                self.household.mothballed.discard(node_id)
                                # KEPT, so `risk` can list what you have to
                                # build again. Otherwise the only record is a
                                # log line a century back.
                                _lost[node_id] = yr
                            self._done_changed()
                            # NAME THEM. A play tester discovered a loss decades
                            # later, when `start X` said "missing prerequisites:
                            # <thing you built two hundred years ago>", and then
                            # rebuilt the chain one refusal at a time. A bare
                            # count is not a report of what happened to you.
                            _named = sorted(drop)
                            _corpus = [tech_id for tech_id in ("corpus_written",
                                                   "corpus_dispersed")
                                       if tech_id in drop]
                            # AND WHAT IT DOES TO THE ROAD YOU ARE ACTUALLY ON.
                            # Naming the lost ids was the first fix; a Rome
                            # player with a real goal set still found out the
                            # road had gotten longer only by re-running `path`
                            # afterwards and comparing it by hand to what they
                            # remembered - a sack that silently undid a third
                            # of their critical-path progress in one turn.
                            # Said here, once, in the same breath as the loss
                            # itself, using the same goal-closure `never_
                            # abandon` already computes and caches.
                            _on_road = 0
                            _goal = getattr(self, "goal", None)
                            if _goal and _goal in self.nodes:
                                try:
                                    _gc = getattr(self, "_goal_closure", None)
                                    if _gc is None:
                                        _gc = self._goal_closure = closure(
                                            self.nodes, _goal)
                                    _on_road = sum(1 for tech_id in drop if tech_id in _gc)
                                except Exception:
                                    _on_road = 0
                            self.household.log.append((yr, "KNOWLEDGE LOST: %d technolog%s "
                                                 "forgotten - %s%s%s%s"
                                % (len(drop), "y" if len(drop) == 1 else "ies",
                                   ", ".join(_named[:8])
                                   + (" and %d more" % (len(_named) - 8)
                                      if len(_named) > 8 else ""),
                                   # BEFORE the loss, not after: `drop` has
                                   # already come out of `self.household.done` by this
                                   # point, so re-asking `self.household.done` here
                                   # could tell a player the corpus was
                                   # "never printed and dispersed" in the
                                   # same sentence that says the corpus
                                   # itself just went - both about the same
                                   # sacking. _hedge_before was read when
                                   # the sack started, before anything was
                                   # taken.
                                   "" if _hedge_before == "corpus_dispersed"
                                   else " (the corpus was never printed and "
                                        "dispersed)",
                                   ". THE CORPUS ITSELF WENT (%s): your hedge "
                                   "against this is gone and 'risk' will say so "
                                   "- build it again first" % ", ".join(_corpus)
                                   if _corpus else "",
                                   (". %d of these stood on the road to your "
                                    "goal: the route is longer than it was a "
                                    "moment ago - 'path' will show the rebuilt "
                                    "shape of it" % _on_road)
                                   if _on_road else "")))
            if "output_factor" in hazard:
                relief, why = self.hazard_relief("output_factor")
                # relief moves the floor back toward 1.0 rather than scaling the
                # damage: self-sufficiency means less of your income was ever
                # coming through the thing the war cut.
                floor = 1.0 - (1.0 - hazard["output_factor"]) * relief
                before = self.output_factor
                self.output_factor = min(self.output_factor, floor)
                # ONCE, AND THEN A REMINDER, not every year of a hundred-year
                # war. output_factor recovers a little each step, so this line
                # re-fired the moment the war pulled it back down - which is
                # every single year. A weird-play tester read the same sentence
                # about the Hundred Years War roughly eighty times and stopped
                # reading the log, which is the real cost: a message repeated
                # until it is noise has stopped being a message.
                said = getattr(self, "_said_output", {})
                key = hazard.get("name", "crisis")
                if before > self.output_factor and yr - said.get(key, -99) >= 20:
                    said[key] = yr
                    self._said_output = said
                    # SAY WHAT HELD. A founder who armed the state before the
                    # war arrived measured protection 0.019 to 0.019 against
                    # one who never touched the military branch, and every
                    # other hazard message in this file already names its
                    # hedges - staff_loss says "would have been"; sack_chance
                    # says "comes to nothing (%s)". This one said nothing,
                    # which is indistinguishable from doing nothing.
                    self.household.log.append((yr, "%s: trade and output fall to %d%% of "
                                         "normal%s"
                                     % (key, self.output_factor * 100,
                                        " (your own strength holds off worse: %s)"
                                        % "; ".join(why[:3]) if why else "")))
            if "real_erosion" in hazard:
                relief, why = self.hazard_relief("real_erosion")
                self.money_real *= (1 - hazard["real_erosion"])
                bite = hazard["real_erosion"] * self.REAL_EROSION_CASH_LOSS_SHARE * relief
                had = max(0.0, self.household.capital)
                self.lose_capital(bite)
                lost = had - max(0.0, self.household.capital)
                if not getattr(self, "_said_debasement", 0) or yr - self._said_debasement >= 15:
                    self._said_debasement = yr
                    # SAY WHAT IT DID TO YOU, and say what it did NOT do. A
                    # break tester read "the coin is worth 99% less", checked
                    # `why horse_collar` in 107, 207 and 307 AD, found the
                    # quote identical to the denarius, and filed it as the
                    # debasement doing nothing. It is doing something: every
                    # price in this game is what a thing really costs in
                    # labour and materials, which debasement does not change.
                    # What it destroys is the money you are HOLDING. Quoting
                    # the bite in coin makes that the visible half.
                    self.household.log.append((yr, "%s: the coin is worth %d%% less than it "
                                         "was%s. Quoted costs are what a thing "
                                         "really takes to make, so they do not "
                                         "move; what debases is the money in "
                                         "your chest, and this year it took %s%s"
                                     % (hazard.get("name", "debasement"),
                                        (1 - self.money_real) * 100,
                                        "; you feel less of it (%s)" % "; ".join(why)
                                        if why else "",
                                        "{:,.0f}".format(lost)
                                        if lost > 0.5 else "nothing, because you "
                                        "were holding none",
                                        " denarii" if lost > 0.5 else "")))
            if "values" in hazard:
                # A hazard can kill your people, burn a site, or make you
                # poorer, and that used to be the whole vocabulary. Norse
                # Christianisation is none of those: its real effect is on
                # what the society BELIEVES, which is exactly what
                # alarm_of() and update_protection() read out of self.w. This
                # is apply_tech_effects' mechanism (see there), aimed at a
                # hazard instead of a technology, with one difference: a
                # technology is a single event and logs once, but a hazard
                # like this runs for over a century, so the shift is spread
                # evenly across every year of `years` rather than dumped on
                # the first one. Applying 1/Nth of the total delta every
                # year, for N years, is what "gradual" means here; a single
                # jump on the first year would be exactly the fake
                # instantaneous conversion this mechanism exists to avoid.
                span = max(1, int(hazard_end) - int(hazard_start) + 1)
                changed = {}
                for field, total_delta in hazard["values"].items():
                    if field.startswith("_") or not isinstance(total_delta, (int, float)):
                        continue
                    if field not in self.w:
                        continue
                    before = self.w[field]
                    self.w[field] = max(self.VALUE_WEIGHT_FLOOR, min(self.VALUE_WEIGHT_CEILING, before + total_delta / span))
                    if abs(self.w[field] - before) > 1e-9:
                        changed[field] = self.w[field]
                # VISIBLE WHILE IT HAPPENS, not only in hindsight: a tester
                # should be able to watch the society turning against them
                # year by year, not discover it as a lump sum in the future.
                # A hundred-odd years of this hazard would be a hundred-odd
                # near-identical log lines if this fired every year, so it
                # is throttled to the first year, the last, and every tenth
                # in between -- the same spirit as the debasement throttle
                # just above, which exists for the same reason.
                if changed and (yr == hazard_start or yr == hazard_end or (yr - hazard_start) % 10 == 0):
                    self.household.log.append((yr, "%s: the society's values are shifting (%s)"
                                     % (hazard.get("name", "hazard"),
                                        ", ".join("%s now %.2f" % (field, value)
                                                  for field, value in sorted(changed.items())))))

    PATRON_DEATH_ANNUAL_CHANCE = declare(
        "PATRON_DEATH_ANNUAL_CHANCE", 0.05, kind="temporary_heuristic",
        unit="dimensionless (yearly probability, local patron only)",
        source=None, confidence="D",
        why="Yearly chance a local patron dies, prompting the need to "
            "court an heir - invented frequency, not fitted to any "
            "attested mortality rate for a Roman patronal relationship.")
    PATRON_DEATH_COOLDOWN_YEARS = declare(
        "PATRON_DEATH_COOLDOWN_YEARS", 25, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="Minimum gap between one patron's death and the next roll - a "
            "patron dies once and then you have courted his heir; the "
            "cooling-off keeps this from repeating within an implausibly "
            "short span. Round number, not measured.")
    PATRON_DEATH_SCANDAL = declare(
        "PATRON_DEATH_SCANDAL", 4, kind="temporary_heuristic",
        unit="scandal points", source=None, confidence="D",
        why="Scandal a patron's death and the scramble to court his heir "
            "generates. Tuned to be a real but minor bump; not measured.")
    PATRON_DEATH_PROTECTION_RETENTION = declare(
        "PATRON_DEATH_PROTECTION_RETENTION", 0.6, kind="temporary_heuristic",
        unit="dimensionless (fraction of protection kept)", source=None,
        confidence="D",
        why="Fraction of protection kept when a patron dies - losing most "
            "of your cover until a new patron relationship is established. "
            "Tuned, not measured.")
    PATRON_DEATH_COURTING_GIFT = declare(
        "PATRON_DEATH_COURTING_GIFT", 800.0, kind="temporary_heuristic",
        unit="denarii at price_index=1.0", source=None, confidence="D",
        why="Cost of courting a dead patron's heir afresh, at this "
            "society's own price level. Invented figure, not sourced to "
            "any attested gift-giving custom.")
    FIRE_ANNUAL_CHANCE = declare(
        "FIRE_ANNUAL_CHANCE", 0.03, kind="temporary_heuristic",
        unit="dimensionless (yearly probability)", source=None,
        confidence="D",
        why="Yearly chance of a fire in the household's own quarter - a "
            "tester playing Han China counted nine fires in Luoyang's "
            "insula district in a hundred years, which this rate is "
            "roughly consistent with, but the figure itself was chosen "
            "rather than fitted to an urban-fire record.")
    FIRE_CAPITAL_LOSS = declare(
        "FIRE_CAPITAL_LOSS", 0.18, kind="temporary_heuristic",
        unit="dimensionless (fraction of capital)", source=None,
        confidence="D",
        why="Fraction of capital a fire destroys. Tuned to be a real but "
            "recoverable setback; not measured against any attested urban "
            "fire's losses.")
    BANDITRY_ANNUAL_CHANCE = declare(
        "BANDITRY_ANNUAL_CHANCE", 0.02, kind="temporary_heuristic",
        unit="dimensionless (yearly probability)", source=None,
        confidence="D",
        why="Yearly chance banditry or a frontier war disrupts supply. "
            "Invented frequency, not fitted to any attested record.")
    BANDITRY_CAPITAL_LOSS = declare(
        "BANDITRY_CAPITAL_LOSS", 0.10, kind="temporary_heuristic",
        unit="dimensionless (fraction of capital)", source=None,
        confidence="D",
        why="Fraction of capital banditry or a frontier disruption costs - "
            "smaller than FIRE_CAPITAL_LOSS, a supply disruption rather "
            "than outright destruction. Tuned, not measured.")

    def _random_events(self, yr):
        rng = self.rng
        # A patron dies ONCE and then you have courted his heir. The old model
        # rolled 4% every year forever, so a long run logged the same line six
        # times, which is not how having a patron works.
        # ONE ATTRIBUTE, NOT TWO. The guard read `_last_patron_death` and the
        # body set `last_patron_death`, so the twenty-five year cooling-off
        # this comment describes never applied to anything: the roll came up
        # five per cent a year for ever, which is precisely the behaviour the
        # fix was written to stop. (The save list carried the unread name too.)
        if (rng.random() < self.PATRON_DEATH_ANNUAL_CHANCE and self.running("patron_local")
                and yr - getattr(self, "last_patron_death", -99) > self.PATRON_DEATH_COOLDOWN_YEARS):
            self.last_patron_death = yr
            self.household.scandal += self.PATRON_DEATH_SCANDAL
            was = self.household.protection
            self.household.protection *= self.PATRON_DEATH_PROTECTION_RETENTION
            gift = self.PATRON_DEATH_COURTING_GIFT * self.price_index
            courted = self.policy.get("auto_court_heir", not self.manual)
            if courted:
                self.household.capital -= gift
            # SAY WHAT IT COST. A play tester read "your patron dies; his heir
            # must be courted afresh", found nothing in `state` that had
            # changed by an amount they could point at, and asked whether the
            # line was decorative. It was not: it takes money, standing and
            # most of your cover, and it should say so, because the answer to
            # it - court somebody, spend on standing - is a decision.
            if courted:
                msg = ("your patron dies; auto_court_heir courts his heir "
                       "afresh for %s denarii. Protection falls from %d%% to "
                       "%d%% and scandal rises by %d"
                       % ("{:,.0f}".format(gift), was * 100,
                          self.household.protection * 100, self.PATRON_DEATH_SCANDAL))
            else:
                msg = ("your patron dies. No money was spent because "
                       "auto_court_heir is off; protection falls from %d%% "
                       "to %d%% and scandal rises by %d"
                       % (was * 100, self.household.protection * 100, self.PATRON_DEATH_SCANDAL))
            self.household.log.append((yr, msg))
        if rng.random() < self.FIRE_ANNUAL_CHANCE:
            had = max(0.0, self.household.capital)
            self.lose_capital(self.FIRE_CAPITAL_LOSS)
            # An insula is a Roman tenement block, and a tester playing Han China
            # counted nine fires in the insula district of Luoyang in a hundred
            # years. Every civilization file names its own quarter.
            self.household.log.append((yr, "fire in the %s: it destroyed %s"
                             % (self.civ.get("fire_quarter", "crowded quarter"),
                                self._loss_words(had))))
        if rng.random() < self.BANDITRY_ANNUAL_CHANCE:
            had = max(0.0, self.household.capital)
            self.lose_capital(self.BANDITRY_CAPITAL_LOSS)
            self.household.log.append((yr, "banditry or a frontier war disrupts supply: "
                                 "it cost you %s" % self._loss_words(had)))

    def _loss_words(self, had_before):
        """"1,240 denarii" or "nothing, you were holding none".

        Every one of these lines used to name the event and stop. A break
        tester's standing complaint across two rounds was that the game
        announces catastrophes and leaves you to diff your own `state` to find
        out whether anything happened.
        """
        lost = had_before - max(0.0, self.household.capital)
        if lost <= 0.5:
            return "nothing, because you were holding none"
        return "{:,.0f} denarii".format(lost)

    def _catastrophe(self, why):
        self.dead_reason = why
        self.household.log.append((self.year, "RUN ENDS: " + why))

    # -- driver -------------------------------------------------------------
