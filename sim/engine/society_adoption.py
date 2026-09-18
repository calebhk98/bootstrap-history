"""How a population takes up what the founder has built.

Split out of sim/engine/society.py, which had grown to 3,809 lines holding
one SocietyMixin with 61 methods. This piece is the domestic side of
adoption: applying a DONE node's one-off effects on the wider civilisation
(apply_tech_effects), the agrarian slack that mechanisation frees up
(_is_agri_mechanisation, agrarian_slack), how far literacy can spread and
how fast it does (literacy_ceiling_general, literacy_ceiling_elite,
_schooling_flow, _advance_literacy), how long a new trade takes a labour
market to absorb (_trade_absorption_years, _advance_trade_absorption,
_grow_endemic_trade), and the per-year driver that calls all of the above
(advance_society). Cross-civilisation diffusion of what has already been
adopted here is a separate subject; see society_diffusion.py. These are
methods of Sim; they are a mixin only so that they can live in a file of
their own. Behaviour is unchanged and verified byte-identical.
"""
import math

from constants import declare
from .data import (TECH_EFFECTS, TRADES_ABSENT)


class AdoptionMixin:

    # The FIRST answer to "I have no staff" is now the obvious one, which the
    # model did not have until this round: hire somebody. A tester spent five
    # hundred years with one scholar, built five separate institution nodes
    # hoping one of them would help, and wrote "if there's a way to grow
    # scholars, I never found it" - because there was not one, short of an
    # institution costing thousands.
    STAFF_SOURCES = {
        "scholars": [("HIRE", "{\"cmd\":\"hire\",\"trade\":\"scholar\",\"n\":2} "
                              "hires literate men by the year; see {\"cmd\":\"labour\"}"),
                     ("school_founded", "the school produces scholars in quantity, and "
                                        "grants more every year it runs"),
                     ("academy_network", "three academies produce more than one school"),
                     ("collegium_licensed", "required before the school is legal")],
        "artisans": [("HIRE", "{\"cmd\":\"hire\",\"trade\":\"smith\",\"n\":3} or any "
                              "trade in {\"cmd\":\"labour\"}; or "
                              "{\"cmd\":\"commission\",\"trade\":\"smith\",\"hours\":400} "
                              "to buy one job instead of employing anybody"),
                     ("freedman_staff", "buy, teach and free a technical staff"),
                     ("workshop_first", "you need somewhere for them to work"),
                     ("BUY", "{\"cmd\":\"buy\",\"what\":\"slaves\",\"n\":N} then "
                             "manumit, though they are untrained for three years")],
    }
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

    # A lower death rate shows up in the census a generation later, not the
    # year the node completes, so a "population" tech effect is spread over
    # this many years rather than dumped on the first one. Forty years is
    # two adult generations, which is about how long it takes a mortality
    # improvement to finish working its way through age structure into a
    # visibly larger population, and it is short enough that a civilization
    # which never stops building these nodes still cannot make the ramp
    # itself the fast part of the cascade.
    POP_TECH_RAMP_YEARS = declare(
        "POP_TECH_RAMP_YEARS", 40, kind="temporary_heuristic", unit="years",
        source=None, confidence="C",
        why="How many years a population-raising technology's total effect "
            "is spread over before showing in the headcount - two adult "
            "generations, roughly how long a mortality improvement takes "
            "to work through age structure into a visibly larger "
            "population (see comment above). A plausible order of "
            "magnitude, not a fitted demographic transition time.")

    VALUE_WEIGHT_FLOOR = declare(
        "VALUE_WEIGHT_FLOOR", -1.0, kind="temporary_heuristic",
        unit="dimensionless (bound on any self.w value weight)",
        source=None, confidence="D",
        why="Lower bound any societal value weight (self.w) can be pushed "
            "to by a tech effect or a values-shifting hazard - symmetric "
            "with a weight's own natural -1..1 scale. Not derived from "
            "any model of how far a society's values can actually move.")
    VALUE_WEIGHT_CEILING = declare(
        "VALUE_WEIGHT_CEILING", 1.5, kind="temporary_heuristic",
        unit="dimensionless (bound on any self.w value weight)",
        source=None, confidence="D",
        why="Upper bound any societal value weight can be pushed to - "
            "asymmetric with VALUE_WEIGHT_FLOOR, allowing a weight to be "
            "reinforced somewhat past its natural 1.0 ceiling by repeated "
            "tech effects. Tuned, not derived.")

    def apply_tech_effects(self, k):
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
        eff = TECH_EFFECTS.get(k)
        if not eff:
            return
        changed = []
        for field, delta in eff.items():
            if field.startswith("_") or not isinstance(delta, (int, float)):
                continue
            if field in self.w:
                before = self.w[field]
                self.w[field] = max(self.VALUE_WEIGHT_FLOOR, min(self.VALUE_WEIGHT_CEILING, before + delta))
                changed.append(field)
            elif field in ("literacy_general", "literacy_elite", "state_capacity"):
                before = float(self.civ.get(field, 0.0))
                self.civ[field] = max(0.0, min(1.0, before + delta))
                if field == "state_capacity":
                    self.state_capacity = self.civ[field]
                changed.append(field)
            elif field == "population":
                # SANITATION, ANTISEPSIS, BETTER FOOD AND THE LIKE RAISE THE
                # POPULATION, AND THAT FEEDS BACK: more people is a bigger
                # labour market and a bigger ceiling on trade (see pop_scale
                # in economy.py, labour.py and geography.py). Unlike every
                # other field above, this does NOT land in one year - a
                # lower death rate shows up in the headcount a generation
                # later, not the day a latrine opens - so it is queued here
                # and spread over RAMP_YEARS by _demographic_recovery() in
                # core.py, the same file that drives the mortality side of
                # this same cascade. `delta` is this technology's total,
                # eventual addition to this civilization's baseline
                # population, as a fraction of it.
                #
                # EXCEPT FOR THE EIGHT DISEASE/SANITATION TECHNOLOGIES
                # (Sim.DISEASE_BURDEN_TECH_IDS, core.py), which WIRING ONE
                # (Complaints/48-technology-cannot-stop-people-dying-young.
                # md) gives a REAL, LIVE effect instead: core.py's own
                # `_disease_burden` sums these same `population` weights
                # straight off `self.has(...)` every year, which is a
                # standing fact about a technology this civilisation holds
                # ("it now boils its water"), not a one-off pulse that
                # ramps in and then is done. Queuing them into
                # `_pop_tech_pending` AS WELL would have the same tree-
                # author weight doing two jobs at once, one of which
                # (`_pop_tech_pending` draining into `_pop_scale_base`,
                # which WIRING_MILESTONE_4.md SS1.3 already established is
                # read by nothing) was already known-inert - so it is
                # deliberately NOT queued for these eight; the five
                # remaining FOOD-effect technologies that also carry a
                # `population` field (crop_rotation, fud_three_field_
                # rotation, fud_seed_drill, mat_newworld_crops, ag2_canning)
                # are unaffected and still queue exactly as before.
                if k not in self.DISEASE_BURDEN_TECH_IDS:
                    self._pop_tech_pending.append(
                        (delta / self.POP_TECH_RAMP_YEARS, self.POP_TECH_RAMP_YEARS))
                changed.append(field)
        if changed:
            self.household.log.append((self.year, "%s changes the society: %s"
                             % (self.nodes[k]["name"], ", ".join(sorted(changed)))))

    # ---- EDUCATING A WHOLE SOCIETY, NOT JUST A HOUSEHOLD -------------------
    # "Can we make the whole country's literacy rates improve? What if we
    # make 5,000 schools and tractors and food production... can I create a
    # 90%+ literate population?" Before this, literacy_general/literacy_elite
    # moved only through the fixed, one-off deltas in _TECH_EFFECTS.json,
    # applied once, the year a technology like printing_press or
    # school_founded first completes (see apply_tech_effects above). Founding
    # a hundred schools did nothing that founding one did not: nothing else
    # in the engine ever read institution_units("school_founded") against
    # literacy. This section is the missing half - a school or an academy
    # that is actually OPEN teaches the society a little more every year it
    # stays open, not only on the day its doors first unlocked - bounded by
    # the user's own, historically correct caveat: a farming family that
    # cannot spare a child from the harvest will not send that child to a
    # classroom however many classrooms you build, so the CEILING literacy
    # can approach is itself a function of how much of the countryside's
    # labour has been freed by mechanised agriculture, and only the RATE of
    # approach to that ceiling is a function of how much schooling is
    # running.
    AGRI_MECHANISATION_CATS = frozenset(
        {"agriculture", "field_machinery", "crops", "soil"})

    def _is_agri_mechanisation(self, k):
        """Is `k` one of the technologies that lets a farm feed the same
        number of mouths with fewer hands - the thing that frees a child
        for a classroom instead of the harvest?

        Reads the tree's own `cat` and `traits`, the same fixed, structural
        tree data civ_cost_factor already keys off, rather than a second,
        hand-maintained list that could drift out of step with which nodes
        the tree actually has. THE TREE ALREADY NAMES THIS: `labour_saving`
        is a trait, and the first version of this function matched on `food`
        alone, which is also carried by tea, coffee and sugar imports, jam
        and cheese making and a dozen other nodes that make farming more
        PROFITABLE without freeing a single pair of hands from it - 136
        nodes matched, most of them tier 0-1, so a household could reach
        full mechanisation before touching anything resembling a reaper.
        Requiring `labour_saving` as well narrows this to the 40 nodes that
        are actually about doing the same farm work with fewer people: the
        chaff cutter and the harrow at the cheap end, the reaper, the
        threshing machine and tile drainage in the middle, the steam
        tractor and the combine harvester at the top. tl_tractor is
        checked by id on its own because the tree files it under the
        generic `vehicle_types` category with every other wheeled thing
        rather than with the rest of agriculture, and a tractor is exactly
        what the user asked for by name.
        """
        node = self.nodes.get(k)
        if not node:
            return False
        if k == "tl_tractor":
            return True
        if "labour_saving" not in (node.get("traits") or ()):
            return False
        return node.get("cat") in self.AGRI_MECHANISATION_CATS or "food" in node["traits"]

    # Reaches full effect at 18 of the 40 matching nodes done (see
    # _is_agri_mechanisation): a little under half, "substantially
    # mechanised farming", not "literally every one of them".
    AGRI_MECHANISATION_SATURATES_AT = declare(
        "AGRI_MECHANISATION_SATURATES_AT", 18.0, kind="temporary_heuristic",
        unit="matching done nodes (of 40)", source=None, confidence="D",
        why="Count of mechanisation-trait nodes done at which "
            "agrarian_slack() saturates at 1.0 - a little under half of "
            "the 40 matching nodes, chosen to mean 'substantially "
            "mechanised farming' rather than 'literally every one'. Not "
            "fitted to any measured mechanisation threshold.")

    def agrarian_slack(self):
        """0..1: how much of the countryside's labour mechanised farming has
        freed, which is the hard limit on how many children a family can
        spare for a school instead of the fields.

        This is the user's own instinct, already half-stated in
        institution_unit_ceiling's own comment (projects.py) before this
        function existed: "a lot of rural people without good farming don't
        really want their kids to go to school, they want them working for
        food or money." Nothing in this engine keeps a literal tonne of
        grain, so this counts what the tree actually offers instead - the
        reaper, the threshing machine, the seed drill, the tractor, better
        rotations and fertiliser - the same shape military_leverage() already
        uses for "how much of one branch of the tree have you actually
        built": a plain count of matching DONE nodes (order cannot change a
        sum of ones, so this needs no sorted() the way a weighted sum would,
        see military_leverage's own unsorted count for the same reasoning),
        square-rooted so the fifth mechanised technique matters far more than
        the fifteenth, and capped at 1.0 so this can never be a lever on its
        own - only a MULTIPLIER on what schooling is allowed to do, below.

        CALLED EVERY YEAR SCHOOLING IS RUNNING, not once at completion like
        apply_tech_effects - _advance_literacy reads the CEILING every year,
        which reads this. Scanning self.household.done (up to 2,833 entries, and only
        ever growing over the course of a long run) for a 40-node match every
        single year of a 700-year run is the wrong direction: only 40 ids can
        ever match at all (see _is_agri_mechanisation), fixed the moment the
        tree loads, so this walks THAT list once, cached forever the same way
        _is_foreign_institution caches (below) - nothing that changes after
        construction - and does one `in self.household.done` set lookup per id, however
        large self.household.done has grown.
        """
        ids = self.__dict__.get("_agri_mechanisation_ids")
        if ids is None:
            ids = self._agri_mechanisation_ids = tuple(
                sorted(node_id for node_id in self.nodes if self._is_agri_mechanisation(node_id)))
        mechanised_count = sum(1 for node_id in ids if node_id in self.household.done)
        if mechanised_count <= 0:
            return 0.0
        return min(1.0, math.sqrt(mechanised_count / self.AGRI_MECHANISATION_SATURATES_AT))

    # What a pre-industrial society can reach on schooling and urban/clerical
    # literacy alone, with farming still entirely by hand: a merchant class,
    # a priesthood, a bureaucracy and their households, well above Rome's
    # bare 12% general literacy and well short of a modern figure. Kept
    # deliberately conservative rather than citing a campaign like Sweden's
    # that reached near-universal reading through the church rather than
    # freed farm labour, because this model has no lever for that route and
    # a number this file cannot actually justify with a mechanism is not one
    # it should claim.
    LITERACY_ROOM_WITHOUT_MECHANISATION = declare(
        "LITERACY_ROOM_WITHOUT_MECHANISATION", 0.35, kind="temporary_heuristic",
        unit="dimensionless (literate share, 0..1)", source=None,
        confidence="D",
        why="Literacy ceiling reachable on schooling and urban/clerical "
            "literacy alone, farming untouched by hand - a merchant class, "
            "priesthood and bureaucracy, above Rome's own bare 12% general "
            "literacy and well short of a modern figure. Kept deliberately "
            "conservative rather than citing an outlier campaign this "
            "model has no lever for (see comment above); not derived from "
            "a model of pre-industrial literacy.")
    LITERACY_MECHANISATION_ROOM = declare(
        "LITERACY_MECHANISATION_ROOM", 0.55, kind="temporary_heuristic",
        unit="dimensionless (literate share, 0..1, at full mechanisation)",
        source=None, confidence="D",
        why="Extra literacy ceiling full agricultural mechanisation opens "
            "up, taking the ceiling to exactly 0.90 together with "
            "LITERACY_ROOM_WITHOUT_MECHANISATION - the answer to 'can I "
            "create a 90%+ literate population', costing exactly what the "
            "user's own caveat says it costs. Chosen to land on that "
            "round target, not derived from a labour-supply model.")
    LITERACY_CEILING_GENERAL_MAX = declare(
        "LITERACY_CEILING_GENERAL_MAX", 0.90, kind="temporary_heuristic",
        unit="dimensionless (literate share, 0..1)", source=None,
        confidence="D",
        why="Hard ceiling on general literacy however much mechanisation "
            "and schooling a society has - a hard 10% of any "
            "pre-transistor-era population (the very young, the infirm, "
            "the itinerant) is not a schooling question at all. Round "
            "figure, not derived from a demographic breakdown.")

    def literacy_ceiling_general(self):
        """The most of the general population schooling could ever make
        literate here, RIGHT NOW - not a fixed number, because
        agrarian_slack() moves it as the countryside mechanises.

        This is the answer to "can I create a 90%+ literate population": at
        the limit, full mechanisation (agrarian_slack() == 1.0) puts the
        ceiling at 0.35 + 0.55 == 0.90, and it costs exactly what the user's
        own caveat says it costs - schools AND the agricultural machinery
        that frees the children who would otherwise be working the harvest.
        Never above 0.90: a hard 10% of any pre-transistor-era population -
        the very young, the infirm, the itinerant - is not a schooling
        question at all.
        """
        room = self.LITERACY_ROOM_WITHOUT_MECHANISATION
        return min(self.LITERACY_CEILING_GENERAL_MAX,
                   room + self.LITERACY_MECHANISATION_ROOM * self.agrarian_slack())

    # The propertied and lettered class literacy_elite measures was never
    # the class tied to the fields, so its ceiling does not read
    # agrarian_slack() at all: an academy can teach every noble and priest's
    # child a society has whether or not a single field has been mechanised.
    # Left short of 1.0 for the same reason literacy_ceiling_general is: some
    # fraction of any class is never going to be readers.
    LITERACY_CEILING_ELITE = declare(
        "LITERACY_CEILING_ELITE", 0.97, kind="temporary_heuristic",
        unit="dimensionless (literate share, 0..1)", source=None,
        confidence="D",
        why="Ceiling on literacy among the propertied and lettered class, "
            "left short of 1.0 for the same reason "
            "LITERACY_CEILING_GENERAL_MAX is: some fraction of any class "
            "is never going to be readers. Round figure, not derived from "
            "any measured elite-literacy ceiling.")

    def literacy_ceiling_elite(self):
        return self.LITERACY_CEILING_ELITE

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
        if not self.running("school_founded"):
            return 0.0
        flow = self.institution_units("school_founded") ** 0.5
        if self.running("academy_network"):
            flow += self.ACADEMY_SCHOOLING_FLOW_MULTIPLIER * self.institution_units("academy_network") ** 0.5
        return flow

    ACADEMY_SCHOOLING_FLOW_MULTIPLIER = declare(
        "ACADEMY_SCHOOLING_FLOW_MULTIPLIER", 1.5, kind="temporary_heuristic",
        unit="dimensionless", source=None, confidence="D",
        why="How much more schooling flow an academy network unit "
            "contributes than a school unit does - a bigger, later "
            "institution teaching more per unit. Tuned to feel "
            "proportionate, not measured against any attested academy "
            "output.")

    # HOW FAST LITERACY CLOSES THE GAP TO ITS CEILING, per unit of
    # _schooling_flow, per year. At flow 1.0 (a single ordinary school and
    # nothing more) the general-literacy gap closes with a time constant of
    # about 1/(0.006*1) ~= 167 years - a run has to want this for the long
    # haul, across several generations, exactly the caution the brief asked
    # for. At flow ~7 (several schools and academies both expanded - the
    # "8.85 units" scale labour.py's own comments record a break tester
    # actually reaching) the time constant falls to about 24 years, so heavy,
    # deliberate investment can visibly transform a society within one or two
    # long lifetimes, which is the other half of what the user asked for:
    # yes, 90%+ is reachable, and it costs generations of sustained schooling
    # and mechanisation, not five turns of building schools.
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

    def _advance_literacy(self, yr):
        """Once a year: let running schools and academies close part of the
        gap between this society's literacy and what it could now reach.

        Logistic-shaped on purpose (the increment shrinks as the gap does,
        the same shape prominence_hazard's `settles_at` and staff_capacity's
        `scale` already use for "approaches a limit, never overshoots it"):
        a society does not leap to its ceiling, and it does not overshoot it
        and have to fall back either.
        """
        flow = self._schooling_flow()
        if flow <= 0.0:
            return
        # PRINTING SPREADING TO THE COUNTRY MAKES SCHOOLING ITSELF FASTER.
        # The user's fourth point given a mechanical home: once movable
        # type or the press has diffused past the one printer's workshop
        # that built it, the same schooling effort teaches faster, because
        # texts actually exist for it to teach FROM. Still requires flow>0
        # above - a country full of diffused printing with no school open
        # still teaches nobody, by the same "taught, not a free drift"
        # rule every other figure in this section already follows.
        flow *= (1.0 + self.PRINTING_DIFFUSION_SCHOOLING_BOOST * self.information_diffusion_index())
        changed = {}
        gen = float(self.civ.get("literacy_general", 0.0))
        gen_ceil = self.literacy_ceiling_general()
        if gen < gen_ceil - 1e-6:
            gen_new = min(gen_ceil, gen + self.LITERACY_GROWTH_RATE_GENERAL
                          * flow * (gen_ceil - gen))
            if gen_new - gen > 1e-6:
                self.civ["literacy_general"] = gen_new
                changed["literacy_general"] = gen_new
        eli = float(self.civ.get("literacy_elite", 0.0))
        eli_ceil = self.literacy_ceiling_elite()
        if eli < eli_ceil - 1e-6:
            eli_new = min(eli_ceil, eli + self.LITERACY_GROWTH_RATE_ELITE
                          * flow * (eli_ceil - eli))
            if eli_new - eli > 1e-6:
                self.civ["literacy_elite"] = eli_new
                changed["literacy_elite"] = eli_new
        if not changed:
            return
        # ONCE A GENERATION, NOT ONCE A YEAR. A gain of a few thousandths a
        # year is real and worth recording, and logging it every single year
        # for a five-hundred-year run would be the same fault the debasement
        # and output_factor hazards were already fixed for elsewhere in this
        # file: a message repeated until it is noise has stopped being a
        # message. Thrown on a fixed 25-year clock (a generation) rather than
        # on a rounded-value change, so it fires on the same schedule whether
        # a run is barely investing or investing heavily.
        last = self._literacy_said
        if yr - last >= 25:
            self._literacy_said = yr
            bits = []
            if "literacy_general" in changed:
                bits.append("general reading is now %d%% of the population"
                            % round(changed["literacy_general"] * 100))
            if "literacy_elite" in changed:
                bits.append("the lettered and propertied class is now %d%% "
                            "literate" % round(changed["literacy_elite"] * 100))
            self.household.log.append((yr, "a generation of schooling shows in the "
                             "census: %s" % "; ".join(bits)))

    # ---- A TRADE THE FOUNDER INTRODUCED BECOMES A TRADE THE SOCIETY HAS ----
    # "If I invent electricity, you can't say that after 100 years I still
    # can't find anyone who can make or research generators." TRADES_ABSENT
    # (data.py) names five trades - chemist, electrician, engineer,
    # machinist, optician - that do not exist here until the founder
    # personally teaches the first one (train(), labour.py); trade_available()
    # then reads them as permanently available because self.household.trades_created
    # never shrinks. What never followed from that is the society producing
    # MORE of them on its own: literate_capacity() bounds how many the
    # founder can hire or teach, and until now nothing but the founder's own
    # director-hours and money ever moved a trade's headcount toward that
    # bound. This is the missing mechanism - once a taught trade has been
    # established long enough, WITH schools actually running, the society
    # naturalises it: it starts producing its own people in that trade, on
    # its own, the same way it always produced its own smiths, bounded by
    # the exact same literate_capacity() wall a founder training them by hand
    # would have been bounded by.
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
        unit="dimensionless (fraction of remaining gap closed per year)",
        source=None, confidence="D",
        why="Once endemic, how fast a trade's headcount approaches "
            "literate_capacity()'s own ceiling - a 20-year time constant "
            "on top of the years it already took to become endemic, so "
            "the whole span is century-scale. Tuned to that target pace, "
            "not measured.")

    def _advance_trade_absorption(self, yr):
        for trade in sorted(TRADES_ABSENT):
            if trade not in self.household.trades_created:
                continue          # never taught here; nothing to naturalise
            intro = self.household.trade_introduced_year.get(trade)
            if intro is None:
                # First year this function has ever seen the trade in
                # trades_created. Recorded now rather than back-dated,
                # because train() (labour.py) does not itself timestamp the
                # set it adds to, and "the year this file first noticed" is
                # at worst one step later than the true year, which cannot
                # matter against a minimum absorption time measured in
                # decades.
                self.household.trade_introduced_year[trade] = yr
                continue
            if trade in self.household.trades_endemic:
                self._grow_endemic_trade(trade)
                continue
            flow = self._schooling_flow()
            if flow <= 0.0:
                continue
            if yr - intro >= self._trade_absorption_years(flow):
                self.household.trades_endemic.add(trade)
                # IN-WORLD, NOT A CHANGE-LOG. This narrates a census fact -
                # the trade is no longer one household's secret - the same
                # way every other log line in this file narrates an event
                # the founder would actually observe, never a note about the
                # code that produced it.
                self.household.log.append((yr, "%s is no longer only your trade: "
                                 "enough schooling has passed through enough "
                                 "hands that this society simply has its own "
                                 "%ss now, the way it always had smiths"
                                 % (trade, trade)))

    def _grow_endemic_trade(self, t):
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
        ceiling = self.literate_capacity(t)
        if not (ceiling < float("inf")):
            return
        have = self.household.employees.get(t, 0.0)
        room = ceiling - have
        if room <= 1e-6:
            return
        self.household.employees[t] = have + room * self.TRADE_DIFFUSION_APPROACH_RATE
        self._resync_pools()

    def advance_society(self, yr):
        """Once a year: everything in this file that moves on the society's
        own slow clock rather than on a project's. Called from step() right
        alongside _demographic_recovery(), which is the same kind of thing -
        a population figure that ramps in over generations - for population
        instead of literacy and trades.
        """
        self._advance_literacy(yr)
        self._advance_trade_absorption(yr)
        # THE COUNTRY, NOT ONLY THE FOUNDER'S OWN CENSUS ENTRY. See
        # "THE COUNTRY CHANGES TOO" above for why this is additional to,
        # never a replacement for, apply_tech_effects' own population queue.
        self._advance_food_diffusion_population(yr)
