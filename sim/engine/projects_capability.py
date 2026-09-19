"""What a capability or institution IS: built, scaled, and still running.

Split out of sim/engine/projects.py (see that file's own docstring for why):
this is the accounting layer underneath everything else in this file - is_
venture() decides whether a node is a going concern at all, running() decides
whether a built one is actually open for business today rather than merely
known, and institution_units()/institution_unit_ceiling()/institution_unit_
cost() answer "how much of it", for the handful of institutions
(SCALABLE_INSTITUTIONS) that come in more than one size. capability_gaps()
is the player-facing report built on top of running(): which completed
institutions are silently not paying out because nobody opened them.

Every other file in this split calls running(), is_venture() or the
institution_unit_* functions constantly; nothing here calls back into them.
These are methods of Sim; they are a mixin only so that they can live in a
file of their own. Behaviour is unchanged and verified byte-identical.
"""
from constants import declare


class CapabilityMixin:
    def is_venture(self, node_id):
        """Is this something you could run as a going concern, as opposed to a
        piece of knowledge that simply changes what you can do?"""
        node = self.nodes.get(node_id)
        if node is None or node_id in self.household.granted:
            return False
        return node["rev"] > 0 or node["up"] > 0


    # ---- DONE VERSUS OPERATING, MADE LOUD --------------------------------
    # The corpus bug (see core.py's Sim.corpus_hedge) is one specific case
    # of a general shape: a screen promising a running()-gated payout while
    # reading has(). This table covers the general case - every OTHER
    # capability in CAPABILITY_INSTITUTIONS whose running()-gated effect a
    # player can actually lose without any screen ever saying so.
    #
    # Each value names what switches off, in the player's own words, not a
    # number - the numbers already live with the one function that computes
    # each effect (update_protection, standing_floor, credit_limit,
    # goods_reach_factor, staff_capacity, workshop_output - see the running()
    # call sites in each). This table only says WHICH of those just went
    # quiet, so nothing here can drift out of step with what those functions
    # actually pay: a number is never invented here, only named.
    #
    # plague_preparedness is the one CAPABILITY_INSTITUTIONS member
    # deliberately absent: its hazard relief (HAZARD_COUNTERS) is has()-gated
    # like corpus, so closing it costs nothing measurable today, and warning
    # about it anyway would be exactly the false alarm this exists to avoid.
    #
    # Closing a plague plan costs nothing BECAUSE the relief is
    # has()-gated, and whether has() is the right gate for quarantine
    # procedure and stockpiles, as opposed to for copies of a book already
    # in other people's hands, is an open question. See
    # Complaints/55-a-plague-plan-you-closed-still-saves-you.md. If that
    # complaint resolves towards has(), this entry should become an
    # explicit "nothing" rather than an absence.
    NOT_OPERATING_BENEFIT = {
        "academy_network": "Scholar and artisan training, standing, and its "
                           "reduction of eminence risk",
        "blast_furnace": "Artisan training capacity",
        "collegium_licensed": "Scholar capacity, protection and credit",
        "corpus_dispersed": "Standing, and the faster diffusion of "
                            "technology through the economy",
        "corpus_written": "Standing",
        "crucible_steel": "Artisan training capacity",
        "endowment_land": "Protection, credit and the lower interest rate",
        "exp_trade_route_extend": "The trade-route revenue bonus",
        "fin_argentarii": "The lower interest rate",
        "fin_university": "Protection",
        "freedman_staff": "Artisan capacity",
        "identity_cover": "Protection, credit and standing",
        "interchangeable_parts": "The price markup and staff-capacity bonus",
        "patron_imperial": "Protection, credit, state funding and status",
        "patron_local": "Protection and credit",
        "patron_senatorial": "Protection, credit and status",
        "power_grid": "The price markup and staff-capacity bonus",
        "railway": "The trade-reach revenue bonus and staff capacity",
        "sanitation_antisepsis": "Your extra life-expectancy",
        "school_founded": "Scholar and artisan training and the standing it earns",
        "steam_high_pressure": "Artisan training capacity",
        "telegraph_electric": "The trade-reach revenue bonus and staff capacity",
        "workshop_first": "Artisan capacity",
    }

    def capability_gaps(self):
        """Completed capability institutions that are NOT currently operating,
        each with the real running()-gated benefit it is not collecting right
        now. See NOT_OPERATING_BENEFIT above for why the list this walks is
        CAPABILITY_INSTITUTIONS minus plague_preparedness.

        fin_university is the one entry needing its own gate here rather than
        in the table: its sole running()-gated effect (update_protection,
        society.py) is an `or` with school_founded, so closing it costs
        nothing while school_founded is still open, and warning anyway would
        be a false alarm.
        """
        out = []
        for node_id in sorted(self.NOT_OPERATING_BENEFIT):
            if node_id not in self.nodes or not self.has(node_id) or self.running(node_id):
                continue
            if node_id == "fin_university" and self.running("school_founded"):
                continue
            benefit = self.NOT_OPERATING_BENEFIT[node_id]
            out.append({
                "id": node_id,
                "benefit_switched_off": benefit,
                "warning": ("Critical capability completed but not "
                           "operating: %s. %s is currently inactive."
                           % (node_id, benefit)),
                "fix": "open %s" % node_id,
            })
        return out


    def institution_units(self, node_id):
        """How much of this institution is actually running, as a number
        rather than a flag.

        0 if it is not open. 1.0 is a single, ordinary founding - exactly the
        size every rev/up/places/room figure elsewhere in the engine was
        always calibrated against, so a run that never expands one of these
        behaves EXACTLY as it did before this existed. Above 1.0 is genuine
        expansion; below 1.0 (see open_venture's `units` argument) is a
        starter founding smaller than the historically-calibrated size, which
        is the actual bridge running() needed: the reason the first workshop
        was never affordable was that there was no way to found a SMALL one.
        For anything not in SCALABLE_INSTITUTIONS this is just running() cast
        to a float, because there is nothing to found a second of.
        """
        if node_id not in self.SCALABLE_INSTITUTIONS:
            return 1.0 if self.running(node_id) else 0.0
        if node_id not in self.household.operating:
            return 0.0
        return max(0.0, getattr(self.household, "inst_units", {}).get(node_id, 1.0))

    LITERACY_GENERAL_FLOOR = declare(
        "LITERACY_GENERAL_FLOOR", 0.02, kind="temporary_heuristic",
        unit="fraction of population", source=None, confidence="D",
        why="The lowest literacy_general this ceiling will ever divide by, "
            "so a society with almost nobody literate still gets a real "
            "(tiny, not undefined or infinite) school-expansion ceiling "
            "rather than a division that blows up. Tuned floor, not a "
            "measured minimum literacy for any real society.")
    INSTITUTION_CEILING_POP_EXPONENT = declare(
        "INSTITUTION_CEILING_POP_EXPONENT", 0.5, kind="temporary_heuristic",
        unit="dimensionless exponent", source=None, confidence="D",
        why="Sub-linear (square-root) growth of how many units of an "
            "institution the population/literacy base can fill, matching "
            "this file's other diminishing-returns curves. Reused for "
            "both the population term and the literacy-ratio term on "
            "schools/academies. Tuned shape, not fitted.")
    SCHOOL_CEILING_BASE_UNITS = declare(
        "SCHOOL_CEILING_BASE_UNITS", 6.0, kind="temporary_heuristic",
        unit="units, at pop_scale=1.0 and reference literacy",
        source=None, confidence="D",
        why="How many units of a school or academy network a full-size, "
            "reference-literacy civilisation can fill. Tuned game "
            "balance, not measured against any real schooling capacity.")
    WORKSHOP_CEILING_BASE_UNITS = declare(
        "WORKSHOP_CEILING_BASE_UNITS", 4.0, kind="temporary_heuristic",
        unit="units, at pop_scale=1.0", source=None, confidence="D",
        why="As SCHOOL_CEILING_BASE_UNITS, for institutions bounded by "
            "population and craftsmen rather than literacy (workshops, "
            "collegia, a freedman staff).")

    def institution_unit_ceiling(self, node_id):
        """The most units of this institution the empire can actually fill.

        Bounded by population, and - the user's own instinct, and a real,
        historically sound one - by food: "a lot of rural people without good
        farming don't really want their kids to go to school, they want them
        working for food or money". This model has no literal tonnes-of-grain
        ledger, but it already has the right proxy for exactly that
        constraint: literacy_general, civ data's measure of how much of the
        population is NOT tied to subsistence farming and so could plausibly
        be literate at all (see labour.py's LITERACY_REFERENCE_GENERAL and its
        own comment on why Rome's is 0.12). A school's ceiling rising with
        literacy_general is not a coincidence dressed up as a rule: it is the
        same fact - a farming society can spare few hands for a classroom -
        counted from the other side, and it is also the virtuous circle the
        user was reaching for, because schools are one of the things that
        raise literacy_general in the first place (apply_tech_effects,
        society.py).

        One unit here is NOT one literal schoolhouse; at this model's scale
        # one unit is already the whole of Rome's original school_founded (34
        # places, institution_places, economy.py) and "5,000 schools" is the
        # player's mental picture of what investing several further units of
        # capacity buys, not a count this engine tracks building by building -
        # the same abstraction a "tonnes_per_year" mine already uses for
        # however many actual shafts that tonnage comes out of.
        """
        if node_id not in self.SCALABLE_INSTITUTIONS:
            return 1.0
        if node_id in ("school_founded", "academy_network"):
            lit = max(self.LITERACY_GENERAL_FLOOR,
                      float(self.civ.get("literacy_general", self.LITERACY_REFERENCE_GENERAL)))
            return max(1.0, self.SCHOOL_CEILING_BASE_UNITS * self.pop_scale ** self.INSTITUTION_CEILING_POP_EXPONENT
                       * (lit / self.LITERACY_REFERENCE_GENERAL) ** self.INSTITUTION_CEILING_POP_EXPONENT)
        # Workshops, collegia and a freedman staff draw on craftsmen rather
        # than the literate few, so population alone bounds them, not literacy.
        return max(1.0, self.WORKSHOP_CEILING_BASE_UNITS * self.pop_scale ** self.INSTITUTION_CEILING_POP_EXPONENT)

    # HOW MUCH DEARER EACH FURTHER UNIT IS, past the first. A second school
    # does not double the supply of people fit to teach in one: it draws on
    # the same small pool of the literate and the propertied the first one
    # already drew down, so founding it costs more than the first did, by a
    # growing margin, well before the population/literacy ceiling above ever
    # bites. 0.5 means the tenth unit's marginal founding cost is 5.5 times
    # the first's - steep enough that a founder pursues the ceiling by
    # raising literacy and population rather than by brute-force spending,
    # which is the whole reason the ceiling and the cost curve are two
    # separate mechanisms rather than one.
    INSTITUTION_EXPANSION_CONVEXITY = declare(
        "INSTITUTION_EXPANSION_CONVEXITY", 0.5, kind="temporary_heuristic",
        unit="dimensionless", source=None, confidence="D",
        why="How much dearer each further unit of a scalable institution "
            "is, past the first: 0.5 means the tenth unit's marginal "
            "founding cost is 5.5 times the first's. The convex SHAPE is a "
            "real claim (a second school draws on the same small literate "
            "pool the first one already drew down); the steepness itself "
            "is tuned to make a founder pursue the population/literacy "
            "ceiling rather than brute-force spending, not fitted to any "
            "real institution's actual expansion cost.")

    def institution_unit_cost(self, node_id, have_units, add_units):
        """Denarii to take this institution from `have_units` to
        `have_units + add_units`, where 1.0 unit costs exactly what founding
        it has always cost (venture_capex) - so a run that only ever founds
        the original single unit pays exactly what it always paid.
        """
        base = self.venture_capex(node_id)
        convexity = self.INSTITUTION_EXPANSION_CONVEXITY

        def cumulative_cost(units):
            return units + convexity * 0.5 * max(0.0, units - 1.0) ** 2
        return base * max(0.0, cumulative_cost(have_units + add_units) - cumulative_cost(have_units))

    # ---- BUILT, versus BUILT AND STILL RUNNING ----------------------------
    # `has` answers "do you know how / did you build it", and for a piece of
    # knowledge that is the whole story. For an establishment it is not. A
    # school with nobody paid to keep it open trains no scholars; a patron you
    # stopped cultivating does not lend his name; a workshop whose doors are
    # shut houses nobody. Gating every capability in this engine on `has`
    # alone would let a founder collect the twelve scholars a school
    # supports, the ten household places a workshop adds and the sixty
    # thousand of credit an imperial patron unlocks WITHOUT EVER OPENING ANY
    # OF THEM - and, since upkeep follows what you run, without paying a
    # denarius of their running cost either.
    #
    # This is the honest test, and it is `has` for everything that has no doors
    # to shut: a technique costs nothing to keep and cannot be closed.
    def running(self, node_id):
        """Built, and still being maintained - which is what a capability needs.

        True for anything you have done that is not a going concern (knowledge
        does not close), for this society's own crafts, and for a concern you
        actually have open.
        """
        if node_id not in self.household.done:
            return False
        if node_id in self.household.granted or not self.is_venture(node_id):
            return True
        # UNPARKED. This returned True unconditionally for a long time, with a
        # comment recording why: requiring the doors to be open sent Rome from
        # 38% of runs reaching the goal to none, because a workshop or a
        # school was a single boolean, one size, ever, so a founder who could
        # not afford the WHOLE of it could not afford any of it - "there is no
        # ladder to climb, only a single step that is either affordable or
        # not". Two earlier bridges (scaling an institution's upkeep by how
        # full it is, in economy.py; letting one be opened against what you
        # could raise rather than only what you were clearing, in
        # auto_open_ventures below) both survive and both helped Han without
        # ever recovering Rome, because neither one touched the actual defect:
        # there was no smaller size to start at.
        #
        # SCALABLE_INSTITUTIONS is that smaller size. institution_units(node_id) can
        # now sit below 1.0 - a starter founding, a fraction of the cost and
        # the yearly bleed of the historically-calibrated full size - and
        # auto_open_ventures founds exactly as much of one as the household's
        # surplus will carry rather than refusing the whole thing. Measured
        # the same way the parked comment was: eight runs a civilisation at
        # horizon 700, `captured_han_386.json` (the strategy that scores 100%
        # on both civilisations with this rule parked). See the measurement
        # recorded in this file's own test suite / the commit that unparked
        # this for the numbers; the short version is that Rome's median year
        # reached and median technologies built held, where requiring the
        # doors open with institutions still booleans had cost Rome the run
        # outright.
        return node_id in self.household.operating

