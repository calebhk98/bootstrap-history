"""How a population takes up what the founder has built.

Split out of sim/engine/society.py, which had grown to 3,802 lines holding
one SocietyMixin with 61 methods. This piece is the domestic side of
adoption: applying a DONE node's one-off effects on the wider civilisation
(apply_tech_effects), how far literacy can spread and
how fast it does (literacy_ceiling_general, literacy_ceiling_elite,
_schooling_flow, _advance_literacy), how long a new trade takes a labour
market to absorb (_trade_absorption_years, _advance_trade_absorption,
_grow_endemic_trade), and the per-year driver that calls all of the above
(advance_society). Cross-civilisation diffusion of what has already been
adopted here is a separate subject; see society_diffusion.py. These are
methods of Sim; they are a mixin only so that they can live in a file of
their own. Behaviour is unchanged and verified byte-identical.
"""

from sim.constants import declare
from .data import (TECH_EFFECTS, TRADES_ABSENT)


class AdoptionMixin:

    # The FIRST answer to "I have no staff" has to be the obvious one: hire
    # somebody. Without it, growing staff has no path short of an
    # institution costing thousands, leaving a player stuck with one scholar
    # for centuries, guessing among institution nodes in the hope one of
    # them helps.
    def staff_hire_advice(self, kind, count=None):
        """The hire command for `kind`, sized to `count` people when the
        shortfall is known, else a typical order."""
        if kind == "scholars":
            return ("{\"cmd\":\"hire\",\"trade\":\"scholar\",\"n\":%d} "
                    "hires literate men by the year; see {\"cmd\":\"labour\"}"
                    % (count or 2))
        return ("{\"cmd\":\"hire\",\"trade\":\"smith\",\"n\":%d} or any "
                "trade in {\"cmd\":\"labour\"}; or "
                "{\"cmd\":\"commission\",\"trade\":\"smith\",\"hours\":400} "
                "to buy one job instead of employing anybody" % (count or 3))

    @property
    def STAFF_SOURCES(self):
        """{"scholars"|"artisans": [(node or HIRE/BUY, advice)]}: HIRE first, the nodes
        declaring `staff_advice` in their order, then BUY."""
        hire = {kind: ("HIRE", self.staff_hire_advice(kind)) for kind in ("scholars", "artisans")}
        buy = ("BUY", "{\"cmd\":\"buy\",\"what\":\"slaves\",\"n\":N} then "
                      "manumit, though they are untrained for three years")
        sources = {kind: [entry] for kind, entry in hire.items()}
        for node_id, spec in self._effect_terms("staff_advice"):
            sources[spec["kind"]].append((node_id, spec["advice"]))
        sources["artisans"].append(buy)
        return sources
    # fin_company_town and fin_chain_store are NOT added to the "artisans"
    # list above. _staff_advice (labour.py) calls is_visible() on every node
    # named here with no memo of its own, and missing_prereq_message - which
    # is_visible can call - itself names an artisans/scholars shortfall by
    # calling straight back into _staff_advice. workshop_first and
    # freedman_staff sit one or two shallow, always-affordable prerequisites
    # from nothing and never trip this; fin_chain_store's own chain
    # (fin_department_store -> fin_market) is deep enough in the tree that a
    # node on it can itself be blocked on artisans, which re-enters this same
    # list, finds fin_chain_store again, and recurses without end - measured
    # as an actual RecursionError, not a theoretical risk. The room advice
    # these two nodes actually need lives in ROOM_SOURCES (labour.py)
    # instead, which has no such call back into itself.

    VALUE_WEIGHT_FLOOR = declare(
        "VALUE_WEIGHT_FLOOR", -1.0, kind="temporary_heuristic",
        unit="dimensionless (bound on any self.value_weights entry)",
        source=None, confidence="D",
        why="Lower bound any societal value weight (self.value_weights) can "
            "be pushed "
            "to by a tech effect or a values-shifting hazard - symmetric "
            "with a weight's own natural -1..1 scale. Not derived from "
            "any model of how far a society's values can actually move.")
    VALUE_WEIGHT_CEILING = declare(
        "VALUE_WEIGHT_CEILING", 1.5, kind="temporary_heuristic",
        unit="dimensionless (bound on any self.value_weights entry)",
        source=None, confidence="D",
        why="Upper bound any societal value weight can be pushed to - "
            "asymmetric with VALUE_WEIGHT_FLOOR, allowing a weight to be "
            "reinforced somewhat past its natural 1.0 ceiling by repeated "
            "tech effects. Tuned, not derived.")

    def apply_tech_effects(self, node_id):
        """Building something changes what this society is like.

        This is what applies _TECH_EFFECTS.json, and it is called from
        _complete(). Printing raises literacy; the scientific method reduces the
        fear of the inexplicable. The whole argument for teaching and printing
        early is that they change people, and this is where that happens.

        It was once true that the effects table was written, committed with a
        description of what it would do, and never referenced by any code. That
        was fixed, and this comment then described the fix in the past tense
        badly enough that an agent reading the file reported the dead mechanic
        as a live finding. A comment that states a bug without stating plainly
        that it is fixed will be read as current, because that is the only
        sensible way to read it.
        """
        eff = TECH_EFFECTS.get(node_id)
        if not eff:
            return
        changed = []
        for field, delta in eff.items():
            if field.startswith("_") or not isinstance(delta, (int, float)):
                continue
            if field in self.value_weights:
                before = self.value_weights[field]
                self.value_weights[field] = max(
                    self.VALUE_WEIGHT_FLOOR,
                    min(self.VALUE_WEIGHT_CEILING, before + delta))
                changed.append("%s %.2f -> %.2f" % (
                    field, before, self.value_weights[field]))
            elif field in ("literacy_general", "literacy_elite", "state_capacity"):
                before = float(self.civ.get(field, 0.0))
                ceiling = {"literacy_elite": self.literacy_ceiling_elite,
                           "literacy_general": self.literacy_ceiling_general}.get(field, lambda: 1.0)()
                # A start above the ceiling is kept; tech cannot push past it.
                self.civ[field] = max(0.0, min(max(ceiling, before), before + delta))
                if field == "state_capacity":
                    self.state_capacity = self.civ[field]
                changed.append("%s %.1f%% -> %.1f%% (%+.1f points, one step)" % (
                    field, before * 100, self.civ[field] * 100,
                    (self.civ[field] - before) * 100))
            elif field == "population":
                # Only the disease technologies carry this weight; the
                # disease burden reads it live from the tree.
                burden = self._disease_burden()
                total_weight = sum(self._tech_effects[tech_id].get("population", 0.0)
                                   for tech_id in self.DISEASE_BURDEN_TECH_IDS)
                burden_before = (min(1.0, burden + delta / total_weight)
                                 if total_weight > 0 and self.has(node_id)
                                 and node_id in self.DISEASE_BURDEN_TECH_IDS else burden)
                changed.append("population (disease burden %.2f -> %.2f of the "
                               "pre-industrial level, which slows deaths and "
                               "raises survival from the next year)"
                               % (burden_before, burden))
        if changed:
            self.state.household.log.append((self.state.scenario.year,
                "%s changes the society, the whole of it at once rather than one "
                "site: %s" % (self.nodes[node_id]["name"], "; ".join(sorted(changed)))))

    # ---- EDUCATING A WHOLE SOCIETY, NOT JUST A HOUSEHOLD -------------------
    # A school teaches a little more every year it stays open. What limits
    # literacy is the cost of a child's time: farm households need their
    # children in the fields, so the reachable share falls with the farm
    # share of the society's working hours, which the labour market sets.
    UNABLE_TO_READ_SHARE = declare(
        "UNABLE_TO_READ_SHARE", 0.01, kind="temporary_heuristic",
        unit="dimensionless (share of any class, 0..1)", source=None,
        confidence="D",
        why="Share of people who cannot learn to read at all (severe "
            "cognitive or sensory impairment), so no ceiling reaches 1.0. "
            "A small round figure, not taken from a survey.")
    FARM_CHILDREN_KEPT_FROM_SCHOOL = declare(
        "FARM_CHILDREN_KEPT_FROM_SCHOOL", 0.8, kind="temporary_heuristic",
        unit="dimensionless (share of farm households' children, 0..1)",
        source=None, confidence="D",
        why="Share of a farming household's children whose labour the farm "
            "needs, so they cannot be spared for a classroom. Multiplied by "
            "the farm share of hours; a round figure, not measured.")

    def literacy_ceiling_general(self):
        """The most of the general population schooling could make literate
        now: everyone but the unable, less the farm children kept at work."""
        kept_home = self.FARM_CHILDREN_KEPT_FROM_SCHOOL * self.labour.farm_share_of_hours()
        return (1.0 - self.UNABLE_TO_READ_SHARE) * (1.0 - kept_home)

    GENERATION_YEARS = declare(
        "GENERATION_YEARS", 25, kind="temporary_heuristic", unit="years",
        source=None, confidence="C",
        why="Length of a human generation; spaces literacy census messages "
            "and decides when schooling has run for a generation.")

    def literacy_ceiling_elite(self):
        """The propertied and lettered class is not tied to the fields, so
        only those who cannot learn to read are left out."""
        return 1.0 - self.UNABLE_TO_READ_SHARE

    def _schooling_flow(self):
        """0 if no school is open here at all; otherwise a small positive
        number that grows, with diminishing returns, in how much school and
        academy capacity is actually running.

        Square-rooted in institution_units for the same reason every other
        institution-driven pool in this engine is (see staff_capacity and
        hired_cap, labour.py, and institution_unit_ceiling, projects.py): a
        second school teaches nearly as many more people as the first one
        did; a ninth does not teach nine times as many. This is 0.0, and
        every function below that reads it does nothing, for the run that
        never builds a school at all - which is deliberate: literacy in this
        model is something a society is TAUGHT into, not something that
        drifts upward for free while nobody is teaching anybody.
        """
        for node_id, spec in self._effect_terms("schooling_flow"):
            if spec.get("required") and not self.running(node_id):
                return 0.0
        return self.effect_sum("schooling_flow")


    # HOW FAST LITERACY CLOSES THE GAP TO ITS CEILING, per unit of
    # _schooling_flow, per year. At flow 1.0 (a single ordinary school and
    # nothing more) the general-literacy gap closes with a time constant of
    # about 1/(0.006*1) ~= 167 years, so a run has to want this for the long
    # haul, across several generations. At flow ~7 (several schools and
    # academies both expanded) the time constant falls to about 24 years, so
    # heavy, deliberate investment can visibly transform a society within one
    # or two long lifetimes: 90%+ literacy is reachable, but it costs
    # generations of sustained schooling and mechanisation, not five turns of
    # building schools.
    LITERACY_GROWTH_RATE_GENERAL = declare(
        "LITERACY_GROWTH_RATE_GENERAL", 0.006, kind="temporary_heuristic",
        unit="dimensionless per unit of schooling flow, per year",
        source=None, confidence="D",
        why="How fast general literacy closes the gap to its ceiling per "
            "unit of _schooling_flow - see comment above: at flow 1.0 "
            "this is a ~167-year time constant, requiring sustained "
            "investment across generations; at flow ~7 it falls to about "
            "24 years. Tuned to hit those two illustrative time constants, "
            "not fitted to any measured literacy-growth curve.")
    # Faster than the general rate: the propertied class an academy draws on
    # is a far smaller pool to reach than "the whole countryside", so the
    # same institutional effort closes its gap faster. Chosen so Rome's own
    # 0.90 starting elite literacy, already close to its 0.97 ceiling, moves
    # only slightly over a run even under heavy investment - this lever is
    # for the civilisations that start far below it, Norse and Mexica among
    # them, not a way to squeeze Rome's last few points out faster.
    LITERACY_GROWTH_RATE_ELITE = declare(
        "LITERACY_GROWTH_RATE_ELITE", 0.010, kind="temporary_heuristic",
        unit="dimensionless per unit of schooling flow, per year",
        source=None, confidence="D",
        why="How fast elite literacy closes its gap - faster than the "
            "general rate because the propertied class an academy draws "
            "on is a far smaller pool to reach (see comment above). "
            "Chosen so Rome's own high starting elite literacy moves only "
            "slightly over a run; not fitted to a measured curve.")

    PRINTING_DIFFUSION_SCHOOLING_BOOST = declare(
        "PRINTING_DIFFUSION_SCHOOLING_BOOST", 0.5, kind="temporary_heuristic",
        unit="dimensionless (multiplies information_diffusion_index)",
        source=None, confidence="D",
        why="How much faster schooling closes literacy's gap once "
            "printing has diffused past the founder's own workshop - "
            "texts actually exist to teach from. Tuned to be a real, "
            "visible boost without letting a country of diffused printing "
            "teach anyone by itself (still requires flow>0); not measured.")

    def effective_schooling_flow(self):
        """Schooling flow once diffused printing is counted: texts to teach
        from make the same schooling effort teach faster, but only where
        some school is open (a flow of zero stays zero)."""
        flow = self._schooling_flow()
        if flow <= 0.0:
            return 0.0
        return flow * (1.0 + self.PRINTING_DIFFUSION_SCHOOLING_BOOST
                       * self.information_diffusion_index())

    def literacy_next_year(self):
        """{civ field: value} for each literacy figure the next year of
        schooling would move, without applying it."""
        flow = self.effective_schooling_flow()
        moved = {}
        if flow <= 0.0:
            return moved
        for field, ceiling, rate in (
                ("literacy_general", self.literacy_ceiling_general(),
                 self.LITERACY_GROWTH_RATE_GENERAL),
                ("literacy_elite", self.literacy_ceiling_elite(),
                 self.LITERACY_GROWTH_RATE_ELITE)):
            current = float(self.civ.get(field, 0.0))
            if current < ceiling - 1e-6:
                after = min(ceiling, current + rate * flow * (ceiling - current))
                if after - current > 1e-6:
                    moved[field] = after
        return moved

    def _advance_literacy(self, year):
        """Once a year: let running schools and academies close part of the
        gap between this society's literacy and what it could now reach.

        Logistic-shaped on purpose (the increment shrinks as the gap does,
        the same shape prominence_hazard's `settles_at` and staff_capacity's
        `scale` already use for "approaches a limit, never overshoots it"):
        a society does not leap to its ceiling, and it does not overshoot it
        and have to fall back either.
        """
        changed = self.literacy_next_year()
        self.civ.update(changed)
        if not changed:
            return
        # Census message at most once a generation, so small yearly gains stay quiet.
        last = self._literacy_said
        if year - last >= self.GENERATION_YEARS:
            self._literacy_said = year
            bits = []
            if "literacy_general" in changed:
                bits.append("general reading is now %d%% of the population"
                            % round(changed["literacy_general"] * 100))
            if "literacy_elite" in changed:
                bits.append("the lettered and propertied class is now %d%% "
                            "literate" % round(changed["literacy_elite"] * 100))
            school_phrase = "schooling shows in the census"
            school_started = self.done_year.get(self.school_node())
            if school_started is not None and year - school_started >= self.GENERATION_YEARS:
                school_phrase = "a generation of schooling shows in the census"
            self.state.household.log.append((year, "%s: %s" % (school_phrase, "; ".join(bits))))

    # ---- A TRADE THE FOUNDER INTRODUCED BECOMES A TRADE THE SOCIETY HAS ----
    # "If I invent electricity, you can't say that after 100 years I still
    # can't find anyone who can make or research generators." TRADES_ABSENT
    # (data.py) names five trades - chemist, electrician, engineer,
    # machinist, optician - that do not exist here until the founder
    # personally teaches the first one (train(), labour.py); trade_available()
    # then reads them as permanently available because self.household.trades_created
    # never shrinks. What does not follow from that alone is the society
    # producing MORE of them on its own: literate_capacity() bounds how many
    # the founder can hire or teach, and nothing besides the founder's own
    # director-hours and money moves a trade's headcount toward that bound
    # without this mechanism. Once a taught trade has been established long
    # enough, WITH schools actually running, the society naturalises it: it
    # starts producing its own people in that trade, on its own, the same
    # way it always produced its own smiths, bounded by the exact same
    # literate_capacity() wall a founder training them by hand is bounded
    # by.
    #
    # No schooling running at all means this never fires, by design: the
    # user's framing is "an EDUCATED society eventually produces its own
    # electricians", not "any society, given centuries, does" - a founder who
    # never builds a school keeps a trade as their own personal secret for
    # as long as the run lasts, which is the honest answer to "after 100
    # years I'm still the only one" when nothing was ever done to change it.
    TRADE_ABSORPTION_BASE_YEARS = declare(
        "TRADE_ABSORPTION_BASE_YEARS", 110.0, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="Years before a founder-taught trade becomes endemic to the "
            "society, absent any schooling flow - see the section comment "
            "above for the framing ('an EDUCATED society eventually "
            "produces its own electricians'). Round figure chosen to put "
            "the total span at about a century; not fitted to any "
            "attested trade-naturalisation record.")
    # Never faster than one working lifetime, however much is invested: a
    # trade the founder taught last year cannot be "something this society
    # has always had" by definition, whatever the schooling budget is.
    TRADE_ABSORPTION_MIN_YEARS = declare(
        "TRADE_ABSORPTION_MIN_YEARS", 35.0, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="Floor on how fast schooling can make a trade endemic, however "
            "much is invested - roughly one working lifetime, so a trade "
            "taught last year cannot already be 'something this society "
            "has always had'. Round figure, not measured.")

    def _trade_absorption_years(self, flow):
        return max(self.TRADE_ABSORPTION_MIN_YEARS,
                   self.TRADE_ABSORPTION_BASE_YEARS / (1.0 + flow) ** 0.5)

    # Once endemic, the fraction of the remaining gap to literate_capacity()
    # closed each year. A time constant of 1/0.05 == 20 years on top of the
    # 35-110 years it already took to BECOME endemic - so the total span from
    # "the founder teaches the first one" to "the society is producing them
    # near its own natural ceiling" is on the order of a century, generations
    # either way you slice it, which is the pace the brief asked this whole
    # mechanism to run at.
    TRADE_DIFFUSION_APPROACH_RATE = declare(
        "TRADE_DIFFUSION_APPROACH_RATE", 0.05, kind="temporary_heuristic",
        unit="fraction of the gap per year", source=None, confidence="D",
        why="Yearly approach rate of an endemic trade's workforce toward "
            "its literate_capacity() ceiling: 5% a year means a half-life "
            "of about 14 years, so from a standing start of one workshop "
            "the whole span is century-scale. Tuned to that target pace, "
            "not measured.")

    def _advance_trade_absorption(self, year):
        household = self.state.household
        for trade in sorted(TRADES_ABSENT):
            if trade not in household.trades_created:
                continue          # never taught here; nothing to naturalise
            intro = household.trade_introduced_year.get(trade)
            if intro is None:
                # First year this function has ever seen the trade in
                # trades_created. Recorded now rather than back-dated,
                # because train() (labour.py) does not itself timestamp the
                # set it adds to, and "the year this file first noticed" is
                # at worst one step later than the true year, which cannot
                # matter against a minimum absorption time measured in
                # decades.
                household.trade_introduced_year[trade] = year
                continue
            if trade in household.trades_endemic:
                self._grow_endemic_trade(trade)
                continue
            flow = self._schooling_flow()
            if flow <= 0.0:
                continue
            if year - intro >= self._trade_absorption_years(flow):
                household.trades_endemic.add(trade)
                # IN-WORLD, NOT A CHANGE-LOG. This narrates a census fact -
                # the trade is no longer one household's secret - the same
                # way every other log line in this file narrates an event
                # the founder would actually observe, never a note about the
                # code that produced it.
                household.log.append((year, "%s is no longer only your trade: "
                                 "enough schooling has passed through enough "
                                 "hands that this society simply has its own "
                                 "%ss now, the way it always had smiths"
                                 % (trade, trade)))

    def _grow_endemic_trade(self, trade):
        """Let a naturalised trade's own headcount drift toward the same
        ceiling literate_capacity() already enforces on a founder hiring or
        teaching it by hand - so this never hands out a person the rest of
        the engine would have refused the player.

        Continuous, not whole-person rounded: `state`'s own
        "staff_are_fractional_because" text already explains to the player
        that headcount here is a full-time-equivalent that phases in
        smoothly rather than a literal integer count of named people (see
        protocol.py), so this is consistent with a number the player already
        sees fluctuate this way from hiring, training and attrition alike.
        """
        ceiling = self.labour.literate_capacity(trade)
        if not (ceiling < float("inf")):
            return
        household = self.state.household
        have = household.employees.get(trade, 0.0)
        room = ceiling - have
        if room <= 1e-6:
            return
        household.employees[trade] = have + room * self.TRADE_DIFFUSION_APPROACH_RATE
        self.labour.resync_pools()

    def advance_society(self, year):
        """Once a year: everything in this file that moves on the society's
        own slow clock rather than on a project's. Called from step() right
        after _demographic_recovery().
        """
        self._advance_literacy(year)
        self._advance_trade_absorption(year)
