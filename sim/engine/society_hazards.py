"""Hazards, their timelines, and the losses they cause.

Everything about a dated hazard once it is a live threat rather than a
source of state pressure: what built defences take off it (hazard_relief,
_military_war_relief), how long a hedge has left to be built
(_calendar_floor_remaining, hazard_advice, hedge_first_steps), when it
lands (_yr_words, hazard_timeline), what a loss does to the household
(lose_capital, _resolve_hazard_condition, _shocks, _random_events,
_loss_words), and the one path out of a run (_catastrophe).

`_shocks` is a thin dispatcher over one method per hazard kind
(_shock_staff_loss, _shock_sack_chance, _shock_output_factor,
_shock_real_erosion, _shock_values). Each of those methods' self.rng draws
must stay in the exact order they would run in if `_shocks` tested every
hazard kind in one body, in sequence - see each one's own docstring -
because save/load and the fingerprint tests only reproduce a run
byte-for-byte if draw order is preserved. These are methods of Sim; they
are a mixin only so that they can live in a file of their own.
"""
from sim.constants import declare
from .data import (closure, critical_path)
from .hazard_window import hazards_not_yet_past


class HazardsMixin:

    KNOWLEDGE_RESIDUE_AFTER_CLOSURE = declare(
        "KNOWLEDGE_RESIDUE_AFTER_CLOSURE", 0.3, kind="temporary_heuristic",
        unit="dimensionless (fraction of a counter's relief kept)",
        source=None, confidence="D",
        why="Share of a hazard counter's relief that survives closing the "
            "institution that delivered it: people who learned the "
            "procedure and a public that saw it work remain, stockpiles "
            "and trained staff do not. Not derived from a decay model.")

    def _counter_strength(self, node):
        """Fraction of a counter's relief in force: 0 if never built, full
        while it is knowledge or a running concern, a residue once a
        concern has been closed."""
        if not self.has(node):
            return 0.0
        if self.running(node):
            return 1.0
        return self.KNOWLEDGE_RESIDUE_AFTER_CLOSURE

    def apply_staff_survival(self, survival_share):
        """Each person on the books survives a shock with probability
        `survival_share`, rolled one by one so headcounts stay whole."""
        household = self.state.household
        household.scholars = self._surviving_people(household.scholars, survival_share)
        household.artisans = self._surviving_people(household.artisans, survival_share)
        for trade in sorted(household.employees):
            survivors = self._surviving_people(household.employees[trade], survival_share)
            if survivors > 0:
                household.employees[trade] = survivors
            else:
                household.employees.pop(trade)

    def _surviving_people(self, headcount, survival_share):
        people = int(round(headcount))
        return float(sum(1 for _ in range(people) if self.rng.random() >= 1.0 - survival_share))

    def hazard_relief(self, kind, beyond_national=False):
        """How much of one kind of harm the things you have built take off.

        Returns (multiplier, [what did it]). Diminishing: each counter removes a
        share of what is LEFT, so five partial answers are strong and none of
        them is a switch that turns history off. With `beyond_national`, a
        technique counts only for the part of the country that has not adopted
        it yet, since national adoption already lowered the exposure.
        """
        mult, why = 1.0, []
        for node, share, label in self.HAZARD_COUNTERS.get(kind, ()):
            adopted_nationally = 0.0
            if node == "_own_gold":
                strength = 1.0 if self.mine_capacity.get("gold", 0.0) > 0.0005 else 0.0
            elif node == "_own_silver":
                strength = 1.0 if self.mine_capacity.get("silver", 0.0) > 0.01 else 0.0
            else:
                strength = self._counter_strength(node)
                if beyond_national and strength > 0.0:
                    adopted_nationally = self.civ_diffusion(node)
            closed = 0.0 < strength < 1.0
            strength *= 1.0 - adopted_nationally
            if strength > 0.0:
                mult *= (1.0 - share * strength)
                if closed:
                    label = "%s (lapsed: %s is closed)" % (label, self.nodes[node]["name"])
                if adopted_nationally > 0.0:
                    label = "%s (partly adopted nationally)" % label
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

        THE NUMBER THE WARNING WAS MISSING: knowing that a hedge exists is
        not the same as knowing how long it takes to reach. The strongest
        hedge in HAZARD_COUNTERS["sack_chance"] (academy_network, sharing
        0.40 of the risk, the biggest single number in that list) sits at
        the end of scientific_method -> corpus_written -> corpus_dispersed
        -> academy_network, a chain whose OWN yrs fields (data already
        carried, already shown per-node as `calendar_floor_years` by
        protocol.py, and already the basis of the `path` command's own
        "Longest serial chain" line) sum to a 30-year floor - not something
        a warning with only a few years' lead time is enough for, so the
        warning has to say the chain has a length, not only that it
        exists.

        Reuses critical_path(), the SAME function `path` already calls for
        exactly this question about a goal node - not a second notion of
        "how long something takes" invented for hazards - and only sums the
        portion of the winning chain not already in self.state.projects.done, so a player
        partway through the chain sees what is actually left, not the whole
        chain's floor from scratch every time.
        """
        if goal not in self.nodes:
            return None
        _total, chain = critical_path(self.nodes, goal)
        done = self.state.projects.done
        remaining = sum(max(self.nodes[node_id]["yrs"], self.nodes[node_id]["ph"] / 2000.0)
                        for node_id in chain if node_id not in done)
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
            # AND SOMETHING YOU CAN ACT ON: a category-level answer like
            # "walls, firearms, powerful friends, and copies of your work
            # kept somewhere else" is easy to read as advice about nothing
            # when it sits among hundreds of startable things and none of
            # them is named as the hedge - even when a hedge is shallow
            # and immediate, like a sand filter needing no prerequisite at
            # all, only one artisan not yet on hand.
            #
            # This does NOT name the hedge or open the tree. It names things you
            # could begin TODAY, which you can already see, and says only that
            # they lead that way. That is what a person who knows how the
            # technology works would know and what fog has no business hiding:
            # fog is about the society, not about your own education.
            step = self.hedge_first_steps(kind)
            if step:
                out["you_could_begin_now_toward_it"] = step
            # AND HOW LONG BEFORE ANY OF IT HELPS: numbers only, never a node
            # id, so this tells nothing fog would hide. The strongest real
            # hedge among these words is not always a purchase - sometimes
            # it is a multi-decade diffusion chain (see
            # _calendar_floor_remaining's own comment), so acting on
            # `what_would_help` the moment it is read is not necessarily
            # enough. Given as a range because these words bundle several
            # genuinely different hedges (a patron is bought in a few
            # years; three dispersed academies are not), and the range is
            # the honest shape of the answer: some of this is fast, and
            # the slowest part is not.
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
        done = self.state.projects.done
        for node, _share, label in self.HAZARD_COUNTERS.get(kind, ()):
            if node not in self.nodes or node in done:
                continue
            want.append((0, node))
            counters.add(node)
            leads_to.setdefault(node, label)
            for pre in self.nodes[node]["pre"]:
                if pre in self.nodes and pre not in done:
                    want.append((1, pre))
                    # SAY WHAT IT LEADS TO: a first-step node can look
                    # entirely unrelated to the hazard it hedges against
                    # (a prerequisite of the actual counter, not the
                    # counter itself), so offering it with no explanation
                    # reads as the game being broken unless this says what
                    # it leads to.
                    leads_to.setdefault(pre, "a step toward %s" % label)
        memo = {}
        seen, out = set(), []
        for distance, node_id in sorted(want):
            if node_id in seen:
                continue
            seen.add(node_id)
            if self.fog and not self.is_visible(node_id, _memo=memo):
                continue
            can_start, why = self.start_reason(node_id)
            entry = {"id": node_id, "name": self.nodes[node_id]["name"],
                     "cost": round(self.project_cost(node_id), 1),
                     "because_it_gives_you": leads_to.get(node_id),
                     "can_begin_now": bool(can_start),
                     "waiting_on": None if can_start else why}
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
        out.sort(key=lambda entry: not entry["can_begin_now"])
        return out

    # Timeline compares "years until hazard" to "lead time of each hedge"
    # (quickest and slowest separately: they escalate at different times).
    # The gap between clocks sets urgency, not either clock alone.
    # States: plenty of time; begin now; quick only; too late; hedged/no hedge.
    HAZARD_TIMELINE_BEGIN_NOW_MULT = 1.5
    # Urgency tags that keep full sentence regardless of position in list.
    HAZARD_TIMELINE_WARN_TAGS = frozenset(
        {"happening now", "too late to hedge", "stopgap only", "begin hedge now"})

    @staticmethod
    def _yr_words(years):
        years = round(years)
        return "%d year" % years if years == 1 else "%d years" % years

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
            # Use worst-defended kind and its own lead times (quickest and slowest).
            # Don't average across kinds: a hazard that is both a sack and output
            # shock is as urgent as its slowest hedge, not the average.
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
        rows.sort(key=lambda row: (0 if row["in_progress"] else 1, row["years_until"]))
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

        Multiplying `self.state.household.capital` by a fraction directly is
        sign-blind: at minus a thousand denarii, multiplying by 0.4 would
        turn a debt into six hundred denarii handed to the player, making
        the deepest hole in the game the safest place to stand and every
        catastrophe a reason to stay in arrears.

        A fire destroys goods. If you own nothing, the fire takes nothing; it
        does not pay off your creditors.
        """
        # ALWAYS floored, never optionally: a parameter to make flooring
        # skippable would advertise a choice that should not exist here -
        # this function must always destroy at most what is actually held.
        household = self.state.household
        if household.capital <= 0:
            return 0.0
        lost = household.capital * max(0.0, min(1.0, fraction))
        household.capital -= lost
        return lost

    def _resolve_hazard_condition(self, hazard, year, hazard_start):
        """History on rails, but the household is allowed to have changed
        the ground it runs on.

        Technology can change how much a dated hazard hurts, never whether
        it happens on schedule - the Third-Century Crisis or the African
        grain fleet failing in 439 fires when its `years` window says so
        regardless of what the player has built. This mechanism is
        deliberately narrow: only a hazard whose CIVILIZATION FILE gives it
        a `condition` is touched at all, so a hazard with none - which is
        most of them - fires exactly on schedule. See the civilization
        files themselves for which hazards carry one and why: in every case
        the note names a MATERIAL cause (a
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
        rest - survives). Returns `hazard` unchanged, or a SHALLOW COPY with
        that one field adjusted; every other field on the hazard (a sack
        risk, a values shift) is untouched, because a household that fed
        itself did not thereby also arm itself or convert the Church.

        Told, not silent, in all three cases - fires as written, fires
        altered, or is averted - the once, the year the hazard's window
        opens (`year == hazard_start`), keyed on the hazard's own name so a multi-year
        window does not repeat itself every year it stays open.
        """
        cond = hazard.get("condition")
        if not cond:
            return hazard
        field = cond.get("field")
        need = cond.get("requires_all") or []
        met = all(self.has(tech_id) for tech_id in need)
        if year == hazard_start:
            said = self._said_condition
            key = hazard.get("name", "hazard")
            if key not in said:
                said.add(key)
                msg = cond.get("met_message" if met else "unmet_message")
                if msg:
                    self.state.household.log.append((year, msg))
        if not met or field not in hazard:
            return hazard
        adjusted = dict(hazard)
        outcome = cond.get("outcome")
        scale = cond.get("alter_scale", 1.0)
        if outcome == "avert":
            del adjusted[field]
        elif outcome == "alter":
            if field == "output_factor":
                adjusted[field] = 1.0 - (1.0 - hazard[field]) * scale
            else:
                adjusted[field] = hazard[field] * scale
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
    # Recovery: self.population vital rates, not a fixed parameter here.
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

    # -- driver -------------------------------------------------------------

    def _shocks(self, year):
        """Dated catastrophes, read from the CIVILIZATION file.

        Rome gets the Antonine plague and the third century crisis. England 1300
        gets the Great Famine and the Black Death. The Mexica get the contact
        epidemics, which are the most severe hazard in the whole directory and
        are not a fair fight. None of it is hardcoded here any more.

        One method per hazard kind (staff_loss, sack_chance, output_factor,
        real_erosion, values), called here in this same order for every hazard
        whose window is open this year. This order is load-bearing: it fixes
        the number and sequence of self.rng draws this method (and
        everything it calls) makes, and save/load and the fingerprint tests
        depend on that sequence reproducing byte-for-byte.
        """
        for hazard in self.civ.get("hazards", []):
            hazard_start, hazard_end = hazard.get("years", [0, 0])
            if not (hazard_start <= year <= hazard_end):
                continue
            hazard = self._resolve_hazard_condition(hazard, year, hazard_start)
            self._shock_staff_loss(hazard, year)
            self._shock_sack_chance(hazard, year)
            self._shock_output_factor(hazard, year)
            self._shock_real_erosion(hazard, year)
            self._shock_values(hazard, year, hazard_start, hazard_end)

    def _shock_staff_loss(self, hazard, year):
        """The staff_loss branch of _shocks: disease and famine years.

        The self.rng draws here must stay in the exact order _shocks calls
        this in relative to the other hazard-kind methods - see _shocks's
        own docstring.
        """
        rng = self.rng
        if "staff_loss" in hazard and rng.random() < self.STAFF_LOSS_HAZARD_ANNUAL_CHANCE:
            historical = hazard["staff_loss"]
            # National prevalence after the country's own medicine; the
            # household is exposed to this, not to the historical rate.
            med_relief = self.medical_diffusion_relief()
            raw = historical * (1.0 - med_relief)
            # Household mitigations cut its risk only where the nation has not adopted them.
            relief, why = self.hazard_relief("staff_loss", beyond_national=True)
            loss = raw * relief
            household = self.state.household
            _people_before = (household.scholars + household.artisans
                              + sum(household.employees.values()))
            _staff_before = self.staff_snapshot()
            self.apply_staff_survival(1 - loss)
            household.directors_extra *= (1 - loss)
            self.log_staff_reduction(hazard.get("name", "a plague"), _staff_before)
            # Cash goes with the trade that stopped.
            cash = self.lose_capital(loss * self.PLAGUE_CASH_LOSS_SHARE)
            self._apply_population_mortality_shock(raw)
            # Refresh population and wage screens now, not at year end.
            self._refresh_demographic_indexes(year)
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
            # Separate sentence so a spared household does not read the national toll as its own.
            if raw > 0.01:
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
                msg += (". Empire-wide: the country's own public health "
                        "- not only yours - has spread far enough that "
                        "this, historically a %d%% loss, barely "
                        "registers"
                        % round(historical * 100))
            self.state.household.log.append((year, msg))

    def _shock_sack_chance(self, hazard, year):
        """The sack_chance branch of _shocks: a site sacked.

        The self.rng draws here must stay in the exact order _shocks calls
        this in relative to the other hazard-kind methods - see _shocks's
        own docstring. The actual sacking (_sack_site) and the knowledge it
        can take (_sack_corpus_loss) are their own methods for the same
        reason: each rng draw has an exact place in that sequence.
        """
        rng = self.rng
        if "sack_chance" in hazard:
            relief, why = self.hazard_relief("sack_chance")
            probability = hazard["sack_chance"] * relief
            if why and rng.random() < hazard["sack_chance"] - probability:
                self.state.household.log.append((year, "%s: an attack comes to nothing (%s)"
                                 % (hazard.get("name", "crisis"), "; ".join(why[:3]))))
            if rng.random() < probability:
                self._sack_site(hazard, year)

    def _sack_site(self, hazard, year):
        """What a sack itself takes: capital, staff, projects reset - then,
        maybe, the corpus.

        The self.rng draw at the bottom has an exact place in the sequence
        _shocks makes its draws in - see _shocks's own docstring.
        """
        rng = self.rng
        household = self.state.household
        projects = self.state.projects
        _cap0 = max(0.0, household.capital)
        # Count all staff (artisans, scholars, hired employees, directors)
        # so the message matches what state actually renders.
        _people0 = (household.artisans + household.scholars
                    + sum(household.employees.values()))
        _act0 = len(projects.active)
        self.lose_capital(self.SACK_CAPITAL_LOSS)
        _staff_before = self.staff_snapshot()
        self.apply_staff_survival(self.SACK_STAFF_RETENTION)
        self.log_staff_reduction("the sack of a site", _staff_before)
        household.directors_extra *= self.SACK_DIRECTORS_RETENTION
        for node_id in sorted(projects.active):
            projects.active[node_id]["ph_left"] = self.nodes[node_id]["ph"]
            projects.active[node_id]["yrs"] = 0.0
        _people_after = (household.artisans + household.scholars
                         + sum(household.employees.values()))
        _took = []
        if _cap0 - max(0.0, household.capital) > 0.5:
            _took.append("%s taken"
                         % "{:,.0f}".format(_cap0 - max(0.0, household.capital)))
        if _people0 - _people_after > 0.05:
            _took.append("%.1f of your people gone"
                         % (_people0 - _people_after))
        if _act0:
            _took.append("%d project%s back to the beginning"
                         % (_act0, "" if _act0 == 1 else "s"))
        household.log.append((year, "%s: a site is sacked - %s"
                         % (hazard.get("name", "crisis"),
                            ", ".join(_took)
                            or "you had nothing it could take")))
        # corpus_hedge (core.py) computes both the roll and the defense state.
        corpus_loss_probability, frac, _hedge_before = self.corpus_hedge()
        if rng.random() < corpus_loss_probability:
            self._sack_corpus_loss(year, frac, _hedge_before)

    def _sack_corpus_loss(self, year, frac, _hedge_before):
        """The corpus lost to a sack: which technologies, and what it does to
        the goal road.

        Called from _sack_site, right after the corpus_loss_probability
        roll: the self.rng.sample() draw below must stay exactly there in
        the draw sequence, or save/load and the fingerprint tests stop
        reproducing a run byte-for-byte.
        """
        rng = self.rng
        # sorted() for determinism: .done is a set with hash-order iteration.
        # Exclude: society inheritance (granted), dispersed copies (beyond reach).
        # Losable: corpus_written only (local site); corpus_dispersed survives.
        projects = self.state.projects
        losable = sorted(node_id for node_id in projects.done
                         if node_id not in projects.granted
                         and not self.corpus_is_dispersed(node_id))
        if losable:
            drop = rng.sample(losable, max(1, int(len(losable) * frac)))
            _lost = projects.forgotten
            for node_id in drop:
                projects.operating.discard(node_id)
                projects.done.discard(node_id)
                projects.mothballed.discard(node_id)
                _lost[node_id] = year  # Track for rebuilding.
            self._done_changed()
            self._log_corpus_loss(year, drop, _hedge_before)

    def _log_corpus_loss(self, year, drop, _hedge_before):
        """Name what a sack's corpus loss took, and what it does to the goal
        road.

        Makes no self.rng draws: `drop` is already decided by the time this
        runs.
        """
        # Name what was lost, not just the count.
        _named = sorted(drop)
        _corpus = [tech_id for tech_id in self.nodes_with_mechanic("corpus")
                   if tech_id in drop]
        # Report impact on goal road: how many lost nodes were on the path.
        _on_road = 0
        _goal = self.goal
        if _goal and _goal in self.nodes:
            try:
                _gc = getattr(self, "_goal_closure", None)
                if _gc is None:
                    _gc = self._goal_closure = closure(
                        self.nodes, _goal)
                _on_road = sum(1 for tech_id in drop if tech_id in _gc)
            except Exception:
                _on_road = 0
        self.state.household.log.append((year, "KNOWLEDGE LOST: %d technolog%s "
                             "forgotten - %s%s%s%s"
            % (len(drop), "y" if len(drop) == 1 else "ies",
               ", ".join(_named[:8])
               + (" and %d more" % (len(_named) - 8)
                  if len(_named) > 8 else ""),
               "" if _hedge_before == self.best_corpus_node()
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

    def _shock_output_factor(self, hazard, year):
        """The output_factor branch of _shocks: wars and the administrative
        aftermath of one.

        Makes no self.rng draws.
        """
        if "output_factor" in hazard:
            relief, why = self.hazard_relief("output_factor")
            # relief moves the floor back toward 1.0 rather than scaling the
            # damage: self-sufficiency means less of your income was ever
            # coming through the thing the war cut.
            floor = 1.0 - (1.0 - hazard["output_factor"]) * relief
            economy = self.state.economy
            scenario = self.state.scenario
            before = economy.output_factor
            economy.output_factor = min(economy.output_factor, floor)
            # Log only on first hit or after 20 years: avoid noise on recovery.
            said = scenario._said_output or {}
            key = hazard.get("name", "crisis")
            if before > economy.output_factor and year - said.get(key, -99) >= 20:
                said[key] = year
                scenario._said_output = said
                self.state.household.log.append((year, "%s: trade and output fall to %d%% of "
                                     "normal%s"
                                 % (key, economy.output_factor * 100,
                                    " (your own strength holds off worse: %s)"
                                    % "; ".join(why[:3]) if why else "")))

    def _shock_real_erosion(self, hazard, year):
        """The real_erosion branch of _shocks: currency debasement.

        Makes no self.rng draws.
        """
        if "real_erosion" in hazard:
            relief, why = self.hazard_relief("real_erosion")
            economy = self.state.economy
            scenario = self.state.scenario
            household = self.state.household
            economy.money_real *= (1 - hazard["real_erosion"])
            bite = hazard["real_erosion"] * self.REAL_EROSION_CASH_LOSS_SHARE * relief
            had = max(0.0, household.capital)
            self.lose_capital(bite)
            lost = had - max(0.0, household.capital)
            if not scenario._said_debasement or year - scenario._said_debasement >= 15:
                scenario._said_debasement = year
                # Report the money lost held, not quoted costs (which reflect reality).
                household.log.append((year, "%s: the coin is worth %d%% less than it "
                                     "was%s. Quoted costs are what a thing "
                                     "really takes to make, so they do not "
                                     "move; what debases is the money in "
                                     "your chest, and this year it took %s%s"
                                 % (hazard.get("name", "debasement"),
                                    (1 - economy.money_real) * 100,
                                    "; you feel less of it (%s)" % "; ".join(why)
                                    if why else "",
                                    "{:,.0f}".format(lost)
                                    if lost > 0.5 else "nothing, because you "
                                    "were holding none",
                                    " denarii" if lost > 0.5 else "")))

    def _shock_values(self, hazard, year, hazard_start, hazard_end):
        """The values branch of _shocks: gradual shifts in what the society
        believes, spread evenly across the hazard's own window.

        Makes no self.rng draws.
        """
        if "values" in hazard:
            # Like apply_tech_effects but spread across years: 1/N of total delta yearly.
            # Single-event tech logs once; multi-year hazard should shift gradually.
            span = max(1, int(hazard_end) - int(hazard_start) + 1)
            changed = {}
            for field, total_delta in hazard["values"].items():
                if field.startswith("_") or not isinstance(total_delta, (int, float)):
                    continue
                if field not in self.value_weights:
                    continue
                before = self.value_weights[field]
                self.value_weights[field] = max(
                    self.VALUE_WEIGHT_FLOOR,
                    min(self.VALUE_WEIGHT_CEILING, before + total_delta / span))
                if abs(self.value_weights[field] - before) > 1e-9:
                    changed[field] = self.value_weights[field]
            # Log at start, end, and every 10 years: visible change without noise.
            if changed and (year == hazard_start or year == hazard_end or (year - hazard_start) % 10 == 0):
                self.state.household.log.append((year, "%s: the society's values are shifting (%s)"
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
        book_money=True, unit="denarii at price_index=1.0", source=None, confidence="D",
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

    def _random_events(self, year):
        rng = self.rng
        # Patron death rolls once per cooldown, not every year.
        founder = self.state.founder
        household = self.state.household
        last_patron_death = founder.last_patron_death
        if (rng.random() < self.PATRON_DEATH_ANNUAL_CHANCE and self.running_with_mechanic("patron_mortal")
                and (last_patron_death is None or year - last_patron_death > self.PATRON_DEATH_COOLDOWN_YEARS)):
            founder.last_patron_death = year
            household.scandal += self.PATRON_DEATH_SCANDAL
            was = household.protection
            household.protection *= self.PATRON_DEATH_PROTECTION_RETENTION
            gift = self.PATRON_DEATH_COURTING_GIFT * self.price_index
            courted = self.policy.get("auto_court_heir", not self.manual)
            if courted:
                household.capital -= gift
            if courted:
                msg = ("your patron dies; auto_court_heir courts his heir "
                       "afresh for %s denarii. Protection falls from %d%% to "
                       "%d%% and scandal rises by %d"
                       % ("{:,.0f}".format(gift), was * 100,
                          household.protection * 100, self.PATRON_DEATH_SCANDAL))
            else:
                msg = ("your patron dies. No money was spent because "
                       "auto_court_heir is off; protection falls from %d%% "
                       "to %d%% and scandal rises by %d"
                       % (was * 100, household.protection * 100, self.PATRON_DEATH_SCANDAL))
            household.log.append((year, msg))
        if rng.random() < self.FIRE_ANNUAL_CHANCE:
            had = max(0.0, household.capital)
            self.lose_capital(self.FIRE_CAPITAL_LOSS)
            household.log.append((year, "fire in the %s: it destroyed %s"
                             % (self.civ.get("fire_quarter", "crowded quarter"),
                                self._loss_words(had))))
        if rng.random() < self.BANDITRY_ANNUAL_CHANCE:
            had = max(0.0, household.capital)
            self.lose_capital(self.BANDITRY_CAPITAL_LOSS)
            household.log.append((year, "banditry or a frontier war disrupts supply: "
                                 "it cost you %s" % self._loss_words(had)))

    def _loss_words(self, had_before):
        """"1,240 denarii" or "nothing, you were holding none".

        Every catastrophe line must say what it actually cost, not only
        name the event: a player should not have to diff their own `state`
        to find out whether anything happened.
        """
        lost = had_before - max(0.0, self.state.household.capital)
        if lost <= 0.5:
            return "nothing, because you were holding none"
        return "{:,.0f} denarii".format(lost)

    def _catastrophe(self, why):
        self.state.founder.dead_reason = why
        self.state.household.log.append((self.state.scenario.year, "RUN ENDS: " + why))
