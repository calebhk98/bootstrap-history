"""What you built does not stay yours: diffusion across ventures and civilisations.

Split out of sim/engine/society.py, which had grown to 3,802 lines holding
one SocietyMixin with 61 methods. This piece is diffusion in both of the
senses the tree needs: how much of one venture's own edge has leaked to
imitators who watched the founder run it (diffusion_share, diffusion_index),
and how a DONE node spreads into the wider civilisation category by
category - food, medical, information and state-military - at its own pace
(_diffusion_category, _diffusible_ids, _state_has_a_patron, _diffusion_pace,
civ_diffusion, _category_diffusion_index, food_diffusion_index,
medical_diffusion_index, information_diffusion_index,
state_military_diffusion, _advance_food_diffusion_population,
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
from constants import declare


class DiffusionMixin:

    # ---- WHAT YOU BUILT DOES NOT STAY YOURS ---------------------------------
    # "To make it even more interesting, you could make it so others try to
    # figure your stuff out, to sell it themselves... over a generation or
    # two." economy_index() (economy.py) already spends the idea that
    # diffused technology enriches the whole empire - it raises the WHOLE
    # economy the instant a tier-2+ node is DONE, with no delay and no
    # distinction between a technique you have never opened for business and
    # one you have been visibly selling from for a century. That is the
    # empire-wide half of the story, and it is not this file's to touch
    # (economy.py is another agent's). What is missing, and IS this file's
    # job, is the other half: a NUMBER, per venture, for how much of the one
    # thing YOU personally run has leaked to imitators - not a price, which
    # is the competing agent's own territory (see goods_market_factor,
    # economy.py, already doing exactly that job, by AGE, for four goods
    # categories) - a fraction of the original edge that is gone, that a
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
    CORPUS_DIFFUSION_PACE_DISPERSED = declare(
        "CORPUS_DIFFUSION_PACE_DISPERSED", 1.7, kind="temporary_heuristic",
        unit="dimensionless (diffusion pace multiplier)", source=None,
        confidence="D",
        why="How much faster knowledge diffuses to rivals once it is "
            "written AND dispersed - a rival can read it rather than "
            "reverse-engineer it from watching the workshop. Shared "
            "between diffusion_share (this founder's own venture) and "
            "_diffusion_pace (the whole society's adoption) so the two "
            "never disagree about what dispersal is worth. Tuned, not "
            "measured.")
    CORPUS_DIFFUSION_PACE_WRITTEN = declare(
        "CORPUS_DIFFUSION_PACE_WRITTEN", 1.3, kind="temporary_heuristic",
        unit="dimensionless (diffusion pace multiplier)", source=None,
        confidence="D",
        why="How much faster knowledge diffuses once merely written down "
            "(not yet dispersed) - smaller than "
            "CORPUS_DIFFUSION_PACE_DISPERSED because copies still sit in "
            "one place. Shared with _diffusion_pace; tuned, not measured.")
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
        share while economy_index() (or its successor) is credited with the
        matching gain to the wider economy - `diffused` there already grows
        with self.household.done regardless of this function, so the two are additive,
        not double-counting the same escape.
        """
        if node_id not in self.household.operating:
            return 0.0
        node = self.nodes.get(node_id)
        if not node or node.get("rev", 0) <= 0:
            return 0.0
        started = self.household.opened_year.get(node_id, self.household.done_year.get(node_id, self.year))
        age = max(0.0, self.year - started)
        pace = 1.0
        if self.running("corpus_dispersed"):
            pace = self.CORPUS_DIFFUSION_PACE_DISPERSED
        elif self.running("corpus_written"):
            pace = self.CORPUS_DIFFUSION_PACE_WRITTEN
        gen_lit = float(self.civ.get("literacy_general", 0.12))
        pace *= (self.LITERACY_DIFFUSION_PACE_BASE
                 + self.LITERACY_DIFFUSION_PACE_SPAN
                 * min(self.LITERACY_DIFFUSION_PACE_CAP_RATIO,
                       gen_lit / max(0.02, self.LITERACY_REFERENCE_GENERAL)))
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
        ops = sorted(node_id for node_id in self.household.operating
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
    # Four categories, read off the tree's own `traits` (the same field
    # alarm_of and state_interest already key off) rather than a second,
    # hand-maintained node list. The priority order matters only for the
    # handful of nodes carrying two of these traits at once
    # (ag2_veterinary_vaccination is both food and medical) - fixed, so the
    # same node is never counted against two different half-lives depending
    # on dict iteration order.
    DIFFUSION_TRAIT_PRIORITY = ("food", "medical", "military", "information")

    # Years for HALF of a just-completed technology in this category to
    # have spread through the society at large, absent any literacy or
    # state-capacity effect (see _diffusion_pace). Food and military are
    # faster than medical and information on purpose: a better crop or a
    # working gun is something a neighbour can see working and copy without
    # reading a word, where germ theory or a press depends on somebody
    # publishing and somebody else literate enough to read it. 25 years (a
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
    DIFFUSION_HALF_LIFE_MILITARY_YEARS = declare(
        "DIFFUSION_HALF_LIFE_MILITARY_YEARS", 20.0, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="Years for half of a newly-completed military technology to "
            "reach the state's own armies - fastest of the four "
            "categories, a working gun is something a neighbour can copy "
            "without reading a word. Tuned, not measured.")
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
    DIFFUSION_HALF_LIFE_YEARS = {
        "food": DIFFUSION_HALF_LIFE_FOOD_YEARS,
        "military": DIFFUSION_HALF_LIFE_MILITARY_YEARS,
        "medical": DIFFUSION_HALF_LIFE_MEDICAL_YEARS,
        "information": DIFFUSION_HALF_LIFE_INFORMATION_YEARS,
    }

    def _diffusion_category(self, node_record):
        traits = node_record.get("traits") or ()
        for trait in self.DIFFUSION_TRAIT_PRIORITY:
            if trait in traits:
                return trait
        return None

    def _diffusible_ids(self, cat):
        """Fixed, cached - same reasoning as _agri_mechanisation_ids above:
        only the tree's own traits decide membership, so this never needs
        recomputing once built, however large self.household.done grows."""
        cache = self.__dict__.get("_diffusible_ids_cache")
        if cache is None:
            cache = {category: [] for category in self.DIFFUSION_TRAIT_PRIORITY}
            for node_id, node in self.nodes.items():
                category = self._diffusion_category(node)
                if category:
                    cache[category].append(node_id)
            cache = {category: tuple(sorted(value)) for category, value in cache.items()}
            self._diffusible_ids_cache = cache
        return cache.get(cat, ())

    def _state_has_a_patron(self):
        """Only a patron gives the STATE anything - the same gate
        update_protection() already applies to military_leverage()'s own
        bonus there: a workshop with nobody to arm is a private matter, not
        the army's equipment."""
        return (self.running("patron_local") or self.running("patron_senatorial")
                or self.running("patron_imperial"))

    def _diffusion_pace(self, cat):
        """How much faster than DIFFUSION_HALF_LIFE_YEARS[cat]'s bare figure
        this category is actually moving, for THIS society, right now.

        Reuses diffusion_share's own two accelerants for medical and
        information (a corpus the knowledge is written into, and how
        literate the general population already is) rather than a second
        formula for "does this society read" - the user's own fourth
        point: printing and literacy change how fast anything textual
        spreads, and both categories that are genuinely about text
        (information itself, and medicine once it depends on germ theory
        rather than on watching a quarantine work) inherit that here.
        Military instead reads state_capacity, not literacy, because what
        limits an army re-equipping is organisation and money, not how many
        soldiers can read (mil_general_staff and mil_conscription_reserve
        are already scored for state_capacity in _TECH_EFFECTS.json on
        exactly that reasoning). Food reads neither: a better crop needs
        nobody to read anything and no army to re-equip, only a neighbour's
        field to watch.
        """
        pace = 1.0
        if cat in ("medical", "information"):
            if self.running("corpus_dispersed"):
                pace = self.CORPUS_DIFFUSION_PACE_DISPERSED
            elif self.running("corpus_written"):
                pace = self.CORPUS_DIFFUSION_PACE_WRITTEN
            gen_lit = float(self.civ.get("literacy_general", 0.12))
            pace *= (self.LITERACY_DIFFUSION_PACE_BASE
                     + self.LITERACY_DIFFUSION_PACE_SPAN
                     * min(self.LITERACY_DIFFUSION_PACE_CAP_RATIO,
                           gen_lit / max(0.02, self.LITERACY_REFERENCE_GENERAL)))
        elif cat == "military":
            pace *= self.MILITARY_DIFFUSION_PACE_BASE + self.MILITARY_DIFFUSION_PACE_STATE_CAPACITY_SPAN * self.state_capacity
        return pace

    MILITARY_DIFFUSION_PACE_BASE = declare(
        "MILITARY_DIFFUSION_PACE_BASE", 0.5, kind="temporary_heuristic",
        unit="dimensionless (pace multiplier floor)", source=None,
        confidence="D",
        why="Floor on military diffusion pace at zero state capacity - an "
            "army re-equips slowly, not instantly, even for the "
            "weakest-capacity state. Tuned, not measured.")
    MILITARY_DIFFUSION_PACE_STATE_CAPACITY_SPAN = declare(
        "MILITARY_DIFFUSION_PACE_STATE_CAPACITY_SPAN", 1.5, kind="temporary_heuristic",
        unit="dimensionless (pace multiplier span across state_capacity)",
        source=None, confidence="D",
        why="How much extra military diffusion pace a maximally capable "
            "state buys on top of MILITARY_DIFFUSION_PACE_BASE - what "
            "limits an army re-equipping is organisation and money, not "
            "literacy (see this method's own docstring). Tuned, not "
            "measured.")

    def civ_diffusion(self, node_id):
        """0..1: how much of the WHOLE SOCIETY, not this household, has
        adopted technology `node_id` - the number behind every consequence below.

        `done`, not `operating` (contrast diffusion_share): a field of New
        World crops or a boiled-water habit is something the country copies
        whether or not the founder still keeps a market stall in it. Zero
        for anything outside the four DIFFUSION_HALF_LIFE_YEARS categories -
        most of the tree is neither a crop, a cure, a weapon nor a text, and
        this mechanism has nothing to say about a lathe or a bookkeeping
        method. Military is additionally zero without a patron
        (_state_has_a_patron): the government cannot be using cannon the
        founder never showed to anyone with soldiers.
        """
        if node_id not in self.household.done:
            return 0.0
        node = self.nodes.get(node_id)
        if not node:
            return 0.0
        cat = self._diffusion_category(node)
        if cat is None:
            return 0.0
        if cat == "military" and not self._state_has_a_patron():
            return 0.0
        age = max(0.0, self.year - self.household.done_year.get(node_id, self.year))
        half_life = (self.DIFFUSION_HALF_LIFE_YEARS[cat]
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
        ids = [node_id for node_id in self._diffusible_ids(cat)
               if node_id in self.household.done and node_id not in self.household.granted]
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
        return self._category_diffusion_index("military")

    # ---- FOOD: THE COUNTRY EATS BETTER, AND GROWS --------------------------
    # apply_tech_effects' own `population` field already adds a one-off,
    # deliberately small amount (0.01-0.02, see _TECH_EFFECTS.json's own
    # note on why it stays small) the year a food technology completes,
    # spread over a flat 40-year ramp (POP_TECH_RAMP_YEARS) - a generation
    # for the CENSUS to catch up with a lower death rate on the founder's
    # OWN estate, not a claim that the whole country farms this way yet.
    # This is the other half the user asked for: as food_diffusion_index()
    # climbs - which, at a 25-year half life, is "within a few decades"
    # exactly as asked - the country's own baseline population rises again,
    # on top of that ramp, by up to FOOD_DIFFUSION_POP_BONUS_MAX. Capped
    # well above what a single node's instant delta could ever reach
    # (0.25 versus a handful of nodes at 0.02 each) ONLY because it is
    # earned slowly, over generations of the country actually adopting it,
    # never as an instant lump sum - see _TECH_EFFECTS.json's own
    # population field note for why the INSTANT deltas stay small instead
    # of scoring this the way Nunn and Qian (2011) actually would.
    FOOD_DIFFUSION_POP_BONUS_MAX = declare(
        "FOOD_DIFFUSION_POP_BONUS_MAX", 0.25, kind="temporary_heuristic",
        unit="dimensionless (fraction of baseline population)",
        source=None, confidence="D",
        why="Ceiling on how much the country's baseline population rises "
            "as food technologies fully diffuse - capped well above what "
            "a single node's instant _TECH_EFFECTS.json delta could reach "
            "(0.25 versus ~0.02 each) only because it is earned slowly, "
            "over generations, never as a lump sum (see comment above). "
            "Not fitted to Nunn and Qian (2011) or any other source "
            "numerically.")
    # How fast the realised bonus chases its own target once diffusion
    # moves it - fast relative to diffusion's own decades, so diffusion
    # itself, not this, is the slow part a player is actually watching.
    FOOD_DIFFUSION_POP_APPROACH_RATE = declare(
        "FOOD_DIFFUSION_POP_APPROACH_RATE", 0.15, kind="temporary_heuristic",
        unit="dimensionless (fraction of remaining gap closed per year)",
        source=None, confidence="D",
        why="How fast the realised population bonus chases its own "
            "diffusion-driven target - deliberately fast relative to "
            "diffusion's own multi-decade half-life, so diffusion, not "
            "this, is the slow part a player actually watches. Tuned, not "
            "measured.")

    def _advance_food_diffusion_population(self, year):
        target = self.FOOD_DIFFUSION_POP_BONUS_MAX * self.food_diffusion_index()
        applied = getattr(self, "_food_pop_bonus_applied", 0.0)
        gap = target - applied
        if gap <= 1e-6:
            return
        add = self.FOOD_DIFFUSION_POP_APPROACH_RATE * gap
        self._pop_scale_base += add
        applied += add
        self._food_pop_bonus_applied = applied
        # ONCE A GENERATION, same throttle as _advance_literacy's own - a
        # gain this small, reported every year of a centuries-long run, is
        # the same noise that throttle was written to stop.
        last = self._food_diffusion_said
        if applied > 0.005 and year - last >= 25:
            self._food_diffusion_said = year
            self.household.log.append((year, "what you grew is no longer only on your "
                             "own land: the crops and rotations you "
                             "introduced have spread far enough into the "
                             "country's own fields that the population is "
                             "running about %d%% above where it would "
                             "otherwise be" % round(applied * 100)))

    # ---- DISEASE: THE COUNTRY IS HARDER TO KILL WHOLESALE ------------------
    # _shocks' staff_loss branch (below) tells a household-level story
    # (`loss`, reduced by the founder's own sanitation and vaccination) and
    # an empire-wide one (`raw`, the hazard's historical, unmitigated rate -
    # deliberately untouched by the founder's PERSONAL hedges: your
    # quarantine protects your people, not everyone else's labour market).
    # Invent the cure or the vaccine for a pandemic and the Black Death
    # should become a minor period of some sickness rather than a
    # catastrophe, which needs the EMPIRE's own figure to fall as the
    # empire, not only the founder, absorbs germ theory, quarantine and
    # vaccination by the time the hazard's window opens.
    # medical_diffusion_relief is that number, read by _shocks directly
    # against `raw`, never against `loss` (which stays the founder's own,
    # private, has()-gated figure).
    MEDICAL_DIFFUSION_RELIEF_CAP = declare(
        "MEDICAL_DIFFUSION_RELIEF_CAP", 0.85, kind="temporary_heuristic",
        unit="dimensionless (fraction of empire-wide epidemic harm removed)",
        source=None, confidence="D",
        why="Ceiling on how much the country's own absorbed medicine can "
            "soften an empire-wide epidemic's raw historical rate, "
            "leaving a residual so no cure ever reduces a historical "
            "pandemic to literally nothing. Tuned, not measured against "
            "any actual disease-control record.")

    def medical_diffusion_relief(self):
        return min(self.MEDICAL_DIFFUSION_RELIEF_CAP, self.medical_diffusion_index())

    # ---- WAR: A STATE THAT IS ACTUALLY ARMED LOSES LESS, AND SACKS LESS ----
    # military_leverage() and _military_war_relief() (further below)
    # already answer "does the founder's OWN workshop protect the
    # founder" - has()-gated, private, and wired only into output_factor.
    # Give the ROMAN GOVERNMENT cannons and it is a different claim that it
    # is not being sacked by tribes: the STATE's own armies, not the
    # founder's private arsenal, and
    # sack_chance as well as output_factor. state_military_diffusion()
    # (above) is that number - patron-gated the same way update_protection
    # already gates military leverage's own patronage bonus, because a
    # foundry with nobody to arm is not the state's equipment yet, however
    # much of the tree it covers.
    STATE_MIL_RELIEF_CAP_OUTPUT = declare(
        "STATE_MIL_RELIEF_CAP_OUTPUT", 0.25, kind="temporary_heuristic",
        unit="dimensionless (fraction of output-shock harm removed at "
             "full diffusion)", source=None, confidence="D",
        why="Ceiling on how much the state's own armed forces (once the "
            "founder's military work has diffused to them) soften an "
            "output-crushing war - smaller than STATE_MIL_RELIEF_CAP_SACK "
            "because output shocks have other causes besides invasion. "
            "Tuned, not measured.")
    STATE_MIL_RELIEF_CAP_SACK = declare(
        "STATE_MIL_RELIEF_CAP_SACK", 0.35, kind="temporary_heuristic",
        unit="dimensionless (fraction of sack-chance harm removed at full "
             "diffusion)", source=None, confidence="D",
        why="Ceiling on how much the state's own armed forces soften "
            "sack_chance specifically - 'give the Roman government "
            "cannons and it is not being sacked by tribes' (see the "
            "section comment above). Tuned, not measured.")

    def _state_military_diffusion_relief(self, cap):
        diffused = self.state_military_diffusion()
        if diffused <= 0.0:
            return 1.0, None
        share = cap * diffused
        return (1.0 - share), ("the state's own armies now carry some of "
                               "what you worked out (%d%% of it has "
                               "reached them)" % round(diffused * 100))

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
            out["population_this_has_already_added"] = round(
                getattr(self, "_food_pop_bonus_applied", 0.0), 3)
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
        # CACHED FOREVER, not per-year, and ONLY for civs that actually pay
        # for the string search below. Rome's own answer is unconditionally
        # False without looking at k at all - that branch was already as
        # cheap as a Python method call can be, and touching a cache dict for
        # it would only add overhead. Everyone else's answer depends only on
        # this civilization's id (fixed at construction) and this node's own
        # key and name (fixed tree data) - nothing that changes over a run.
        # The 4a auto-grant loop in step() called this for every node in
        # `order` (2,831 of them) every single year, most of them already
        # done or never going to be granted this way at all, so a 500-year
        # Han run paid for the same string search on the same node hundreds
        # of times over. See `_done_changed` for the convention this
        # deliberately does NOT need: there is no invalidation here because
        # nothing it reads can change after the Sim is built.
        if self.civ.get("id") == "rome_100ad":
            return False
        cache = self.__dict__.setdefault("_foreign_institution_cache", {})
        value = cache.get(node_id)
        if value is None:
            hay = (node_id + " " + self.nodes[node_id].get("name", "")).lower()
            value = any(marker in hay for marker in self.FOREIGN_MARKERS)
            cache[node_id] = value
        return value

    def _is_foreign_only(self, node_id):
        """A legal or civic institution of a society that is not this one."""
        # CACHED FOREVER, for the same reason as _is_foreign_institution just
        # above, and with the same Rome fast path kept outside the cache.
        # start_reason() calls this on every not-yet-done node it is asked
        # about, every year, for as long as that node stays unbuilt.
        if self.civ.get("id") == "rome_100ad":
            return False
        cache = self.__dict__.setdefault("_foreign_only_cache", {})
        value = cache.get(node_id)
        if value is None:
            hay = (node_id + " " + self.nodes[node_id].get("name", "")).lower()
            value = any(marker in hay for marker in self.FOREIGN_INSTITUTIONS)
            cache[node_id] = value
        return value

    def needs_first(self, node_id):
        """(node, why) this society must have before it can begin `node_id` at all.

        cost_multipliers say a domain is DEARER here. Some things are not dear,
        they are impossible: a society with no draught animals, no iron and
        no wheel in practical use cannot start horse_collar at any price,
        however low a cost_multiplier might make it look.

        Data, like everything else about a civilisation, and always liftable -
        every entry names the node that opens it. See _SCHEMA.md.
        """
        spec = self.civ.get("needs_first") or {}
        for key, ent in spec.items():
            if key.startswith("_") or not isinstance(ent, dict):
                continue
            if node_id in (ent.get("ids") or ()):
                node = ent.get("node")
                if node and node not in self.household.done:
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
            if isinstance(remedy, dict) and remedy.get("node") in self.household.done:
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
