"""What you built does not stay yours: diffusion across ventures and civilisations.

Split out of sim/engine/society.py, which had grown to 3,802 lines holding
one SocietyMixin with 61 methods. This piece is diffusion in both of the
senses the tree needs: how much of one venture's own edge has leaked to
imitators who watched the founder run it (diffusion_share, diffusion_index),
and how a DONE node spreads into the wider civilisation category by
category - food, medical and information at a curve of their own, and state-military as
what the government actor holds
(_diffusion_category, _diffusible_ids, _diffusion_pace,
civ_diffusion, _category_diffusion_index, food_diffusion_index,
medical_diffusion_index, information_diffusion_index,
state_military_diffusion,
medical_diffusion_relief, _state_military_diffusion_relief,
world_diffusion_report), plus what a diffused-or-foreign technology means for
the fog-of-war display and for cost (_is_foreign_institution,
_is_foreign_only, needs_first, civ_cost_factor). Domestic adoption -
literacy, trade absorption, the population's own capacity to take up what
already exists in this one household - is a separate subject; see
society_adoption.py. These are methods of Sim; they are a mixin only so
that they can live in a file of their own. Behaviour is unchanged and
verified byte-identical.
"""
from sim.constants import declare
from . import category_traits, seat_builds
from .institution_societies import belongs_to_other_society


class DiffusionMixin:

    # ---- WHAT YOU BUILT DOES NOT STAY YOURS ---------------------------------
    # "To make it even more interesting, you could make it so others try to
    # figure your stuff out, to sell it themselves... over a generation or
    # two." The empire-wide half of the story is real output (real_output.py):
    # a technique cheapens the goods its entries make. What is missing, and IS this file's
    # job, is the other half: a NUMBER, per venture, for how much of the one
    # thing YOU personally run has leaked to imitators - not a price, which
    # is the competing agent's own territory (the agent economy's prices) - a fraction of the original edge that is gone, that a
    # price formula can spend however it spends a competitive market. This
    # is deliberately NOT wired into revenue() here: pricing belongs to
    # economy.py's own goods-market code, and two places independently
    # pricing the same venture is exactly the tangle a single price formula
    # is meant to avoid. See diffusion_share's own docstring for exactly how
    # a price formula should read it.
    #
    # Years for HALF of a visibly-run venture's original edge to have leaked
    # to competitors who watched you run it, absent any effect of publishing
    # or literacy. Pitched at the low end of "a generation or two" (a
    # generation is conventionally 25-30 years) because the ventures this
    # applies to are ones you are OPERATING for revenue in public, which is
    # the most visible thing a person in this model can be doing - the
    # opposite case, a technique you worked out and never opened for
    # business, is exactly what `k not in self.household.operating` below returns zero
    # for, because nobody has anything to watch.
    VENTURE_DIFFUSION_HALF_LIFE_YEARS = declare(
        "VENTURE_DIFFUSION_HALF_LIFE_YEARS", 40.0, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="Years for half of a visibly-run venture's original edge to "
            "leak to competitors, absent any publishing or literacy "
            "effect - pitched at the low end of 'a generation or two' "
            "(see comment above). Chosen to sit in that plausible range, "
            "not fitted to any measured rate of competitive imitation.")
    # HOWEVER LONG YOU HAVE BEEN VISIBLE, some of a first-mover's edge never
    # leaves: your own customers, your own reputation for the thing, your own
    # head start on the next improvement. Capped, the same way protection,
    # familiarity and every other saturating share in this file are capped,
    # so this can never be read as "and eventually it reaches 1.0", a claim
    # this model has no basis for making.
    VENTURE_DIFFUSION_CAP = declare(
        "VENTURE_DIFFUSION_CAP", 0.65, kind="temporary_heuristic",
        unit="dimensionless (share, 0..1)", source=None, confidence="D",
        why="However long a venture has been visibly run, some of a "
            "first-mover's edge never leaves - customers, reputation, a "
            "head start on the next improvement (see comment above). "
            "Capped so this is never read as eventually reaching 1.0; not "
            "measured.")
    LITERACY_DIFFUSION_PACE_BASE = declare(
        "LITERACY_DIFFUSION_PACE_BASE", 0.7, kind="temporary_heuristic",
        unit="dimensionless (pace multiplier floor)", source=None,
        confidence="D",
        why="Floor on the literacy-driven diffusion-pace multiplier, at "
            "the reference literacy level - a society at or below "
            "reference literacy still diffuses at 70% pace, never zero. "
            "Shared with _diffusion_pace; tuned, not measured.")
    LITERACY_DIFFUSION_PACE_SPAN = declare(
        "LITERACY_DIFFUSION_PACE_SPAN", 0.3, kind="temporary_heuristic",
        unit="dimensionless (pace multiplier span above the floor)",
        source=None, confidence="D",
        why="How much extra diffusion pace a more literate society buys "
            "on top of LITERACY_DIFFUSION_PACE_BASE, up to "
            "LITERACY_DIFFUSION_PACE_CAP_RATIO times the reference "
            "literacy. Shared with _diffusion_pace; tuned, not measured.")
    LITERACY_DIFFUSION_PACE_CAP_RATIO = declare(
        "LITERACY_DIFFUSION_PACE_CAP_RATIO", 2.0, kind="temporary_heuristic",
        unit="dimensionless (multiple of reference literacy)", source=None,
        confidence="D",
        why="Ceiling on how much a society's literacy, relative to the "
            "reference level, can boost diffusion pace - twice the "
            "reference literacy is treated as maximally literate for this "
            "purpose. Shared with _diffusion_pace; tuned, not measured.")
    DIFFUSION_PACE_FLOOR = declare(
        "DIFFUSION_PACE_FLOOR", 0.4, kind="temporary_heuristic",
        unit="dimensionless (minimum diffusion pace)", source=None,
        confidence="D",
        why="Floor on the overall diffusion pace divisor, so a society "
            "with no accelerants at all still diffuses at some minimum "
            "rate rather than the half-life going to infinity. Shared "
            "between diffusion_share and _diffusion_pace; tuned, not "
            "measured.")

    def diffusion_share(self, node_id):
        """0..VENTURE_DIFFUSION_CAP: how much of what running venture `node_id`
        earns has already leaked to competitors who watched you run it and
        went into the same business themselves.

        Zero for anything not currently operating (running()/is_venture,
        projects.py) - a technique sitting in `done` with the doors shut is
        not a thing anybody has watched you run - and zero for anything with
        no revenue, since there is no market in it to compete for. Two
        things move it FASTER than the bare passage of time: a corpus that is
        written down and dispersed is knowledge a rival can read rather than
        having to reverse-engineer from watching your workshop (reusing
        corpus_written/corpus_dispersed - the model's own existing idea of
        how published knowledge spreads, rather than inventing a second one
        - see the brief's own pointer to it); and a more literate society has
        more people able to read it and go into business against you, the
        same literacy_general this file already reads everywhere else a
        society's own capacity is the question.

        FOR THE MARKET AGENT: a revenue formula that wants to spend this
        number honestly should reduce what THIS venture earns by up to this
        share while the wider economy is credited with the matching gain through
        the goods' prices (real_output.py), which follow projects.done regardless
        of this function, so the two are additive, not double-counting the same escape.
        """
        projects = self.state.projects
        scenario = self.state.scenario
        if node_id not in projects.operating:
            return 0.0
        node = self.nodes.get(node_id)
        if not node or node.get("rev", 0) <= 0:
            return 0.0
        done_year_map = projects.done_year or {}
        started = projects.opened_year.get(node_id, done_year_map.get(node_id, scenario.year))
        age = max(0.0, scenario.year - started)
        pace = self.corpus_diffusion_pace()
        gen_lit = float(self.civ.get("literacy_general", 0.12))
        pace *= (self.LITERACY_DIFFUSION_PACE_BASE
                 + self.LITERACY_DIFFUSION_PACE_SPAN
                 * min(self.LITERACY_DIFFUSION_PACE_CAP_RATIO,
                       gen_lit / max(0.02, self.labour.LITERACY_REFERENCE_GENERAL)))
        half_life = self.VENTURE_DIFFUSION_HALF_LIFE_YEARS / max(self.DIFFUSION_PACE_FLOOR, pace)
        share = 1.0 - 0.5 ** (age / half_life)
        return min(self.VENTURE_DIFFUSION_CAP, max(0.0, share))

    def diffusion_index(self):
        """One number for the whole household: the revenue-weighted average
        of diffusion_share() across everything currently operated for a
        living. 0.0 if nothing is operating, or everything operating is
        brand new. Revenue-weighted rather than a plain average because a
        household running one huge ironworks and one brand-new stall should
        read as "mostly caught up with", not as "half caught up with" -
        exactly the same reasoning revenue() itself already weights by each
        node's own `rev` figure.
        """
        projects = self.state.projects
        ops = sorted(node_id for node_id in projects.operating
                     if self.nodes.get(node_id, {}).get("rev", 0) > 0)
        if not ops:
            return 0.0
        tot_w = tot = 0.0
        for node_id in ops:
            weight = self.nodes[node_id]["rev"]
            tot_w += weight
            tot += weight * self.diffusion_share(node_id)
        return tot / tot_w if tot_w > 0 else 0.0

    # ---- THE COUNTRY CHANGES TOO, NOT ONLY YOUR OWN EXPOSURE TO IT ---------
    # `condition` (see _resolve_hazard_condition above) answers what a dated
    # hazard does TO THE FOUNDER's own household risk. It says nothing about
    # what the founder's workshop does to the COUNTRY: sail to the Americas
    # and bring back New World crops, add crop rotation, and within a few
    # decades ALL of Rome has significantly more food and a larger
    # population; give the Roman government cannons and it is not being
    # sacked by tribes; invent the cure or the vaccine for a pandemic and
    # the Black Death becomes a minor period of some sickness rather than a
    # catastrophe. civ_diffusion(node_id) is that missing number.
    #
    # It reuses diffusion_share's own shape just above (age since
    # completion, sped up by a written/
    # dispersed corpus and by how literate the society already is) rather
    # than inventing a second idea of what diffusion is - but gated on
    # DONE, not on operating: crop_rotation happens to carry rev>0 in this
    # tree and germ_theory does not, and a country does not need the
    # founder's own stall open for business to go on planting the crop or
    # boiling the water once it has seen it done. Bounded at 1.0, not
    # VENTURE_DIFFUSION_CAP's 0.65 - a crop or a vaccine can become
    # something literally everyone has, in a way a founder's personal
    # market share against live competitors never fully does.
    #
    # The diffusing categories are the tree's own `traits` (the same field
    # alarm_of and state_interest already key off), listed in priority order
    # in data/world/category_traits.json (`diffusion_traits`). The order
    # matters only for nodes carrying two of these traits at once
    # (ag2_veterinary_vaccination is both food and medical) - fixed, so the
    # same node is never counted against two different half-lives.

    # Years for HALF of a just-completed technology in this category to
    # have spread through the society at large, absent any literacy or
    # state-capacity effect (see _diffusion_pace). Food is faster than
    # medical and information on purpose: a better crop is something a
    # neighbour can see working and copy without reading a word, where
    # germ theory or a press depends on somebody publishing and somebody
    # else literate enough to read it. 25 years (a
    # generation) is pitched at the low end of "a few decades", matching
    # Nunn and Qian's (2011) own description of the potato's spread across
    # Europe as a matter of generations rather than years.
    DIFFUSION_HALF_LIFE_FOOD_YEARS = declare(
        "DIFFUSION_HALF_LIFE_FOOD_YEARS", 25.0, kind="temporary_heuristic",
        unit="years", source="Nunn and Qian (2011) describe the potato's "
             "spread across Europe as a matter of generations rather than "
             "years.",
        confidence="C",
        why="Years for half of a newly-completed food technology to "
            "spread through the wider society, absent any literacy or "
            "state-capacity effect - a better crop is something a "
            "neighbour can see working and copy without reading a word. "
            "Pitched at the low end of 'a few decades' to match the cited "
            "source's description, not fitted to it numerically.")
    DIFFUSION_HALF_LIFE_MEDICAL_YEARS = declare(
        "DIFFUSION_HALF_LIFE_MEDICAL_YEARS", 35.0, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="Years for half of a newly-completed medical technology to "
            "spread - slower than food or military because germ theory or "
            "a vaccine depends on publishing and on somebody literate "
            "enough to read it. Tuned, not measured.")
    DIFFUSION_HALF_LIFE_INFORMATION_YEARS = declare(
        "DIFFUSION_HALF_LIFE_INFORMATION_YEARS", 30.0, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="Years for half of a newly-completed information technology "
            "(printing and the like) to spread through society. Tuned, "
            "not measured.")
    def _diffusion_half_life_years(self, cat):
        """Bare half-life of a diffusion trait: a number in its data entry, or
        the declared constant it names."""
        entry = category_traits.diffusion_traits()[cat]
        if "half_life_years" in entry:
            return float(entry["half_life_years"])
        return getattr(self, entry["half_life_constant"])

    def _diffusion_category(self, node_record):
        traits = node_record.get("traits") or ()
        for trait in category_traits.diffusion_trait_names():
            if trait in traits:
                return trait
        return None

    def _diffusible_ids(self, cat):
        """Fixed, cached - same reasoning as _agri_mechanisation_ids above:
        only the tree's own traits decide membership, so this never needs
        recomputing once built, however large self.household.done grows."""
        cache = self.__dict__.get("_diffusible_ids_cache")
        if cache is None:
            cache = {category: [] for category in category_traits.diffusion_trait_names()}
            for node_id, node in self.nodes.items():
                category = self._diffusion_category(node)
                if category:
                    cache[category].append(node_id)
            cache = {category: tuple(sorted(value)) for category, value in cache.items()}
            self._diffusible_ids_cache = cache
        return cache.get(cat, ())

    def _diffusion_pace(self, cat):
        """How much faster than the category's bare half-life
        this category is actually moving, for THIS society, right now.

        Reuses diffusion_share's own two accelerants for medical and
        information (a corpus the knowledge is written into, and how
        literate the general population already is) rather than a second
        formula for "does this society read" - the user's own fourth
        point: printing and literacy change how fast anything textual
        spreads, and both categories that are genuinely about text
        (information itself, and medicine once it depends on germ theory
        rather than on watching a quarantine work) inherit that here.
        Military is not here: it is what the government holds. Food reads
        neither: a better crop needs nobody to read anything and no army to re-equip, only a neighbour's
        field to watch.
        """
        pace = 1.0
        if category_traits.diffusion_traits()[cat].get("text_paced"):
            pace = self.corpus_diffusion_pace()
            gen_lit = float(self.civ.get("literacy_general", 0.12))
            pace *= (self.LITERACY_DIFFUSION_PACE_BASE
                     + self.LITERACY_DIFFUSION_PACE_SPAN
                     * min(self.LITERACY_DIFFUSION_PACE_CAP_RATIO,
                           gen_lit / max(0.02, self.labour.LITERACY_REFERENCE_GENERAL)))
        return pace

    def civ_diffusion(self, node_id):
        """0..1: how much of the WHOLE SOCIETY, not this household, has
        adopted technology `node_id` - the number behind every consequence below.

        `done`, not `operating` (contrast diffusion_share): a field of New
        World crops or a boiled-water habit is something the country copies
        whether or not the founder still keeps a market stall in it. Zero
        for anything outside the four diffusion categories -
        most of the tree is neither a crop, a cure, a weapon nor a text, and
        this mechanism has nothing to say about a lathe or a bookkeeping
        method. Military is not a curve: it is 1 when the government
        actor holds the node (copied from the founder, or licensed) and 0
        when it does not.
        """
        scenario = self.state.scenario
        if not seat_builds.holders_of(self.state.seats, node_id):
            return 0.0
        node = self.nodes.get(node_id)
        if not node:
            return 0.0
        cat = self._diffusion_category(node)
        if cat is None:
            return 0.0
        if category_traits.diffusion_traits()[cat].get("government_held"):
            return 1.0 if node_id in self.state_treasury().knowledge else 0.0
        # the society copies from whichever seat finished it first
        age = max(0.0, scenario.year - seat_builds.earliest_done_year(self.state.seats, node_id, scenario.year))
        half_life = (self._diffusion_half_life_years(cat)
                     / max(0.4, self._diffusion_pace(cat)))
        return max(0.0, min(1.0, 1.0 - 0.5 ** (age / half_life)))

    def _category_diffusion_index(self, cat):
        """Plain average across every founder-built DONE node in `cat` -
        not revenue-weighted like diffusion_index(): a food category with
        one fully-spread crop and one just-introduced one is honestly "half
        spread", not "mostly spread because the old one earns more" (most
        of these nodes earn no revenue at all). sorted() for the same
        determinism reason every other float sum over a set in this file
        uses it.
        """
        # Opening-state knowledge is already part of this society; it is not
        # a founder innovation waiting to diffuse from the household.  Counting
        # newly explicit inherited grants here both diluted later projects and
        # treated those grants as if the founder had introduced them.
        ids = sorted(seat_builds.built_by_any(self.state.seats, self._diffusible_ids(cat)))
        if not ids:
            return 0.0
        return sum(self.civ_diffusion(node_id) for node_id in sorted(ids)) / len(ids)

    def food_diffusion_index(self):
        return self._category_diffusion_index("food")

    def medical_diffusion_index(self):
        return self._category_diffusion_index("medical")

    def information_diffusion_index(self):
        return self._category_diffusion_index("information")

    def state_military_diffusion(self):
        """Share of the founder's military work the government actor holds."""
        held = self.state_treasury().knowledge
        ids = sorted(seat_builds.built_by_any(self.state.seats, self._diffusible_ids("military")))
        return sum(1 for node_id in ids if node_id in held) / len(ids) if ids else 0.0

    # ---- DISEASE: THE COUNTRY IS HARDER TO KILL WHOLESALE ------------------
    # National prevalence of an epidemic falls as the country absorbs the
    # medicine; the household is exposed to that prevalence (see
    # _shock_staff_loss). Relief is coverage (the diffusion index) times how
    # far people follow the guidance; there is no fixed ceiling.
    MEDICAL_COMPLIANCE_BASE = declare(
        "MEDICAL_COMPLIANCE_BASE", 0.5, kind="temporary_heuristic",
        unit="dimensionless (share following public-health guidance at "
             "zero state capacity)", source=None, confidence="D",
        why="Share of people who follow quarantine and hygiene guidance "
            "with no administration behind it; state capacity supplies "
            "the rest. Not derived from a behavioural model.")

    def medical_compliance(self):
        return (self.MEDICAL_COMPLIANCE_BASE
                + (1.0 - self.MEDICAL_COMPLIANCE_BASE) * self.state_capacity)

    def medical_diffusion_relief(self):
        return min(1.0, self.medical_diffusion_index() * self.medical_compliance())

    # ---- WAR: A STATE THAT IS ACTUALLY ARMED LOSES LESS, AND SACKS LESS ----
    # military_leverage() and _military_war_relief() (further below)
    # already answer "does the founder's OWN workshop protect the
    # founder" - has()-gated, private, and wired only into output_factor.
    # Give a government cannons and it is a different claim that it is not
    # being sacked by tribes: the STATE's own armies, not the founder's
    # private arsenal, and sack_chance as well as output_factor.
    # Each of the founder's military inventions the government holds (it copied it from its own
    # budget or was licensed it) removes its own share of the harm, one after another on what is
    # left, as hazard_relief combines every defence. The share of the founder's tree the state holds
    # (state_military_diffusion) is reported but is not the basis: inventing more weapons never
    # lowers the relief.
    STATE_MIL_RELIEF_PER_WEAPON_OUTPUT = declare(
        "STATE_MIL_RELIEF_PER_WEAPON_OUTPUT", 0.04, kind="temporary_heuristic",
        unit="dimensionless (share of the remaining output-shock harm one held "
             "weapon removes)", source=None, confidence="D",
        why="What the state's armies gain from one more of the founder's weapons "
            "against an output-crushing war; smaller than the sack figure because "
            "output shocks have other causes besides invasion. Tuned, not measured.")
    STATE_MIL_RELIEF_PER_WEAPON_SACK = declare(
        "STATE_MIL_RELIEF_PER_WEAPON_SACK", 0.06, kind="temporary_heuristic",
        unit="dimensionless (share of the remaining sack-chance harm one held "
             "weapon removes)", source=None, confidence="D",
        why="What the state's armies gain from one more of the founder's weapons "
            "against being sacked by tribes. Tuned, not measured.")

    def state_military_weapons_held(self):
        """How many of the founder's military inventions the government holds."""
        held = self.state_treasury().knowledge
        return sum(1 for node_id in seat_builds.built_by_any(self.state.seats, self._diffusible_ids("military"))
                   if node_id in held)

    def _state_military_diffusion_relief(self, per_weapon):
        weapons = self.state_military_weapons_held()
        if weapons <= 0:
            return 1.0, None
        return ((1.0 - per_weapon) ** weapons,
                "the state's own armies now carry %d of the weapons you worked out" % weapons)

    def world_diffusion_report(self):
        """None while nothing the founder has built is spreading into the
        wider society; otherwise a compact, inspectable snapshot of how far
        it has spread and what that is doing to the country - the user's
        own fourth requirement, that this never happen silently in a state
        variable. Gated to None when dormant so an early game's `state`
        reply pays nothing for a mechanism that has not fired yet (see
        `worth_knowing_early`'s own gate, just above, for the same pattern).
        """
        food, med, mil, info = (self.food_diffusion_index(),
                                 self.medical_diffusion_index(),
                                 self.state_military_diffusion(),
                                 self.information_diffusion_index())
        if food < 0.01 and med < 0.01 and mil < 0.01 and info < 0.01:
            return None
        out = {}
        if food >= 0.01:
            out["food_and_farming_the_country_has_adopted"] = round(food, 3)
        if med >= 0.01:
            out["public_health_the_country_has_adopted"] = round(med, 3)
            out["how_much_softer_the_next_epidemic_will_be"] = round(
                self.medical_diffusion_relief(), 3)
        if mil >= 0.01:
            out["military_technology_now_in_the_states_hands"] = round(mil, 3)
        if info >= 0.01:
            out["printing_and_literacy_the_country_has_adopted"] = round(info, 3)
        return out

    # FOG OF WAR. Without it the player sees the entire tree from the first
    # minute, including exactly what a transistor needs, which is both a spoiler
    # and a lie about what knowing something feels like. With fog on you see
    # what you have built in full, what you could start next as a one line
    # summary, and nothing at all about where any of it leads.

    def _is_foreign_institution(self, node_id):
        # CACHED FOREVER, not per-year: the answer depends only on this
        # civilization's society (fixed at construction) and this node's own
        # key and name (fixed tree data) - nothing that changes over a run.
        # The 4a auto-grant loop in step() called this for every node in
        # `order` (2,831 of them) every single year, most of them already
        # done or never going to be granted this way at all, so a 500-year
        # Han run paid for the same string search on the same node hundreds
        # of times over. See `_done_changed` for the convention this
        # deliberately does NOT need: there is no invalidation here because
        # nothing it reads can change after the Sim is built.
        cache = self.__dict__.setdefault("_foreign_institution_cache", {})
        value = cache.get(node_id)
        if value is None:
            hay = (node_id + " " + self.nodes[node_id].get("name", "")).lower()
            value = belongs_to_other_society(hay, self.civ, "markers")
            cache[node_id] = value
        return value

    def _is_foreign_only(self, node_id):
        """A legal or civic institution of a society that is not this one."""
        # CACHED FOREVER, for the same reason as _is_foreign_institution just
        # above.
        # start_reason() calls this on every not-yet-done node it is asked
        # about, every year, for as long as that node stays unbuilt.
        cache = self.__dict__.setdefault("_foreign_only_cache", {})
        value = cache.get(node_id)
        if value is None:
            hay = (node_id + " " + self.nodes[node_id].get("name", "")).lower()
            value = belongs_to_other_society(hay, self.civ, "exclusive_markers")
            cache[node_id] = value
        return value

    def needs_first(self, node_id, about_stock=None):
        """(node, why) this society must have before it can begin `node_id` at all.

        cost_multipliers say a domain is DEARER here. Some things are not dear,
        they are impossible: a society with no draught animals, no iron and
        no wheel in practical use cannot start horse_collar at any price,
        however low a cost_multiplier might make it look.

        Data, like everything else about a civilisation, and always liftable -
        every entry names the node that opens it. See _SCHEMA.md.

        `about_stock` narrows to the gates that rest on held living stock (True) or on
        knowledge alone (False); left out, either.
        """
        spec = self.civ.get("needs_first") or {}
        for key, ent in spec.items():
            if key.startswith("_") or not isinstance(ent, dict):
                continue
            if about_stock is not None and bool(ent.get("material")) != about_stock:
                continue
            if node_id in (ent.get("ids") or ()):
                node = ent.get("node")
                stock = {ent["material"]: ent.get("units", 0.0)} if ent.get("material") else None
                if stock and self.stock_holds_met(stock):
                    continue
                if node and node not in self.state.projects.done:
                    return node, (ent.get("because") or
                                  "this society has no %s" % key)
        return None, None

    def civ_cost_factor(self, node_id):
        """What this society is unusually good or bad at building.

        Every civilization differs in population, prices, values and reach,
        but that alone misses the most important thing about some of them.
        The Mexica are not a small Rome: there is no domesticable draught
        animal anywhere in Mesoamerica, so every load
        moves on a human back, and that is a permanent fact about the continent
        rather than something the founder can teach away. The Norse build the
        best ships in Europe and cannot organise a public works programme. Han
        China already has cast iron, paper and the blast furnace.

        A factor above 1 means this society finds that domain harder than Rome
        does; below 1, easier. It is deliberately a small table in the civ file
        rather than logic in here, so a new civilization is data.
        """
        mults = self.civ.get("cost_multipliers") or {}
        if not mults:
            return 1.0
        # A remedy lifts a handicap once you have built the thing that answers
        # it, read from `handicap_remedies` in the civ file.
        rem = self.civ.get("handicap_remedies") or {}
        node = self.nodes[node_id]

        def mult(key):
            multiplier = float(mults[key])
            remedy = rem.get(key)
            if isinstance(remedy, dict) and remedy.get("node") in self.state.projects.done:
                multiplier = float(remedy.get("residual", 1.0))
            return multiplier

        # THE CATEGORY IS THE CRAFT; THE TRAITS ARE WHAT IT IS FOR, and treating
        # them as equals inverts the whole system: multiplying every matching
        # key together lets secondary traits (infrastructure, commerce) swamp
        # the craft category a civilisation is actually built around - a
        # longship, category `ships`, the Norse's best domain, must not come
        # out costing them MORE than it costs Rome just because its
        # infrastructure and commerce traits are also present.
        #
        # What a thing takes to build is its craft. What it is used for should
        # colour that, not overwhelm it, so traits apply at a damped exponent
        # when the craft is known and at full weight when it is not.
        cat = node.get("cat")
        traits = [trait for trait in (node.get("traits") or ()) if trait in mults]
        if cat in mults:
            factor = mult(cat)
            for trait in traits:
                factor *= mult(trait) ** 0.25
            return factor
        factor = 1.0
        for trait in traits:
            factor *= mult(trait)
        return factor
