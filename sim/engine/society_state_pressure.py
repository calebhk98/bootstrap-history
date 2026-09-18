"""How society and the state notice, fear, and lean on a growing household.

Split out of sim/engine/society.py, which had grown to 3,809 lines holding
one SocietyMixin with 61 methods. This piece is the throughline from a
single technology being alarming (alarm_of, state_interest) through what
defends the founder against that alarm (update_protection,
withdraw_from_public_life) to the two separate dangers that outgrow any
defence - personal prominence (eminence_report, prominence_hazard) and the
state's own fiscal interest once a household is large enough to be worth
assessing (household_scale, state_notice, requisition_report,
office_report, military_demand_eligible, confiscation_risk,
state_pressure_report, _state_pressure) - plus the one physical crossing to
sim/world/military_logistics.py (military_leverage,
military_equipment_burden_kg_per_soldier_per_year) that both the protection
and the pressure mechanics spend as a multiplier. These are methods of Sim;
they are a mixin only so that they can live in a file of their own.
Behaviour is unchanged and verified byte-identical.
"""
import math

from constants import declare

from world import military_logistics


STATE_INTEREST_RELIGIOUS_ADJACENT_WEIGHT = declare(
    "STATE_INTEREST_RELIGIOUS_ADJACENT_WEIGHT", -0.9, kind="temporary_heuristic",
    unit="dimensionless (multiplies w_religious_rigidity)", source=None,
    confidence="D",
    why="How much a religiously rigid society's OWN interest in a technology "
        "is suppressed by that technology being religious_adjacent - "
        "negative because rigidity chills state interest in it rather than "
        "raising it, near but not equal to a full -1.0 offset. No source "
        "ties this specific fraction to any state's actual interest in "
        "religious matters; a real figure needs a model of how a state's "
        "own priorities are formed, not a hand-picked weight per trait.")

ALARM_WEIGHT_INEXPLICABLE = declare(
    "ALARM_WEIGHT_INEXPLICABLE", 10.0, kind="temporary_heuristic",
    unit="alarm points (multiplies w_magic_fear)", source=None,
    confidence="D",
    why="How alarming an effect a society has no category for is, before "
        "any defence - the largest of the per-trait weights here because "
        "alarm_of's own docstring says this is the thing that matters, not "
        "speed or money. No source measures a society's fright at an "
        "unexplained effect in these units; a real mechanism would derive "
        "alarm from what a specific society's own epistemic categories can "
        "and cannot explain, not from a fixed per-trait table.")
ALARM_WEIGHT_SPECTACLE = declare(
    "ALARM_WEIGHT_SPECTACLE", 4.0, kind="temporary_heuristic",
    unit="alarm points (multiplies w_magic_fear)", source=None,
    confidence="D",
    why="A visible spectacle alarms a magic-fearing society less than "
        "something truly inexplicable does - it is still explained by "
        "showmanship - so this sits at a fixed fraction of "
        "ALARM_WEIGHT_INEXPLICABLE. Tuned to feel proportionate, not "
        "derived from any source.")
ALARM_WEIGHT_RELIGIOUS_ADJACENT = declare(
    "ALARM_WEIGHT_RELIGIOUS_ADJACENT", 9.0, kind="temporary_heuristic",
    unit="alarm points (multiplies w_religious_rigidity)", source=None,
    confidence="D",
    why="How alarming a religious authority finds a religiously-adjacent "
        "effect, in the same invented units as every other weight in this "
        "table. No source; a real figure needs a model of a specific "
        "religious institution's own doctrine and its actual reaction to a "
        "specific claim, not one number for the whole category.")
ALARM_WEIGHT_STATUS_THREATENING = declare(
    "ALARM_WEIGHT_STATUS_THREATENING", 5.0, kind="temporary_heuristic",
    unit="alarm points", source=None, confidence="D",
    why="How alarming a technology that threatens the standing of an "
        "existing elite is, flat regardless of the society's own weights - "
        "unlike the other terms here, this one carries no `weights[...]` "
        "multiplier at all, which is itself an unexamined choice. Tuned "
        "game balance, not a measured social reaction.")
ALARM_WEIGHT_WEAPON_DEMOCRATISING = declare(
    "ALARM_WEIGHT_WEAPON_DEMOCRATISING", 6.0, kind="temporary_heuristic",
    unit="alarm points", source=None, confidence="D",
    why="How alarming a weapon that lets ordinary people fight on equal "
        "terms with an elite is, also flat regardless of the society's own "
        "weights - see military_leverage()'s own docstring for the other "
        "half of what this trait does. Invented game balance.")
ALARM_WEIGHT_LABOUR_SAVING = declare(
    "ALARM_WEIGHT_LABOUR_SAVING", 4.0, kind="temporary_heuristic",
    unit="alarm points (multiplies max(0, -w_labour_saving))", source=None,
    confidence="D",
    why="How alarming a labour-saving technology is to a society that "
        "specifically fears labour displacement (negative w_labour_saving) "
        "- zero for a society that does not. Tuned to sit alongside the "
        "other per-trait weights above, not measured.")
ALARM_FAMILIARITY_FLOOR = declare(
    "ALARM_FAMILIARITY_FLOOR", 0.12, kind="temporary_heuristic",
    unit="dimensionless (floor on 1 - familiarity)", source=None,
    confidence="D",
    why="However habituated a society becomes to the founder, alarm never "
        "falls below this floor - a full stranger is not read the same as "
        "a lifelong native however long the founder has been visible. "
        "Chosen so familiarity remains a strong, not total, defence; not "
        "derived from any measured habituation curve.")
ALARM_PROTECTION_FLOOR = declare(
    "ALARM_PROTECTION_FLOOR", 0.15, kind="temporary_heuristic",
    unit="dimensionless (floor on 1 - protection)", source=None,
    confidence="D",
    why="However protected the founder is by patrons, office and money, "
        "alarm never falls below this floor - protection can blunt "
        "suspicion, never erase it outright. Chosen for the same reason as "
        "ALARM_FAMILIARITY_FLOOR; not measured.")
ALARM_IDENTITY_COVER_MULTIPLIER = declare(
    "ALARM_IDENTITY_COVER_MULTIPLIER", 0.75, kind="temporary_heuristic",
    unit="dimensionless multiplier", source=None, confidence="D",
    why="A respectable cover identity reads an inexplicable effect as "
        "learning rather than sorcery - see the comment just above this "
        "constant's use - cutting alarm by a quarter. Tuned so having a "
        "cover identity is a real, visible help without eliminating alarm "
        "outright; not measured against any historical case.")


class StatePressureMixin:
    def state_interest(self, n):
        weights = self.w
        state_weights = dict(self.STATE_WEIGHTS)
        state_weights.update({"military": weights["w_military"], "labour_saving": weights["w_labour_saving"],
                  "information": weights["w_information"], "commerce": weights["w_commerce"],
                  "religious_adjacent": STATE_INTEREST_RELIGIOUS_ADJACENT_WEIGHT * weights["w_religious_rigidity"]})
        return sum(state_weights.get(trait, 0.0) for trait in n.get("traits", []))

    def alarm_of(self, n):
        """How alarming this technology is TO THIS CIVILIZATION, before defences.

        Note what is NOT in here: speed, and money. Building fast does not make
        you a sorcerer. Producing an effect a society has no category for does.
        """
        weights = self.w
        alarm = 0.0
        for trait in n.get("traits", []):
            if   trait == "inexplicable":        alarm += ALARM_WEIGHT_INEXPLICABLE * weights["w_magic_fear"]
            elif trait == "spectacle":           alarm += ALARM_WEIGHT_SPECTACLE  * weights["w_magic_fear"]
            elif trait == "religious_adjacent":  alarm += ALARM_WEIGHT_RELIGIOUS_ADJACENT  * weights["w_religious_rigidity"]
            elif trait == "status_threatening":  alarm += ALARM_WEIGHT_STATUS_THREATENING
            elif trait == "weapon_democratising":alarm += ALARM_WEIGHT_WEAPON_DEMOCRATISING
            elif trait == "labour_saving":       alarm += ALARM_WEIGHT_LABOUR_SAVING  * max(0.0, -weights["w_labour_saving"])
        alarm *= (1.0 + max(0.0, -weights["w_novelty"]))
        alarm *= max(ALARM_FAMILIARITY_FLOOR, 1.0 - self.household.familiarity)      # people habituate, fast
        alarm *= max(ALARM_PROTECTION_FLOOR, 1.0 - self.household.protection)       # patrons, office, money
        # A recognised scholar doing something strange is a scholar; a stranger
        # doing the same thing is a sorcerer. This is the persona working, and
        # it is what the node has always said it does.
        if self.running("identity_cover"):
            alarm *= ALARM_IDENTITY_COVER_MULTIPLIER
        return alarm

    def military_leverage(self):
        """How much of the military branch this founder can put in a patron's
        hands: the count that "if I woke up in Rome and made cannon" is
        actually asking about.

        Measured against a founder with none of the 111+ military, weapon and
        fortification nodes, the ONLY effect any of them had anywhere in the
        engine was `weapon_democratising` raising suspicion (see alarm_of) -
        arming a state you already live in was a pure liability. This is the
        other half: a founder who hands a patron the flintlock or the bastion
        fort is worth more to him, which is what update_protection() and
        hazard_relief("output_factor") below both spend it on.

        Sqrt-scaled and capped at 1.0, the same shape standing_floor() uses
        for earned work: the FIRST working gun matters enormously to a patron
        shopping for an edge over his rivals, the fortieth barely adds
        anything he does not already have. Counts founder-built DONE nodes,
        not merely operating nodes or the society's inherited grants. A
        fortification design or powder formula remains useful after its
        workshop closes, but Rome's existing army is not the founder's work.
        Reaches 1.0 at 25 nodes, a little over a fifth of the tree's military
        branch, so this cannot be maxed by a token gesture, and cannot be
        maxed by "build everything military" either - both would make the
        branch a strategy unto itself, which the other ~2,700 nodes on the
        way to a transistor should not have to compete with.
        """
        military_node_count = sum(1 for node_id in self.household.done - self.household.granted
                if "military" in self.nodes[node_id].get("traits", ()))
        if military_node_count <= 0:
            return 0.0
        return min(1.0, math.sqrt(military_node_count / self.MILITARY_LEVERAGE_SATURATES_AT))

    MILITARY_LEVERAGE_SATURATES_AT = declare(
        "MILITARY_LEVERAGE_SATURATES_AT", 25.0, kind="temporary_heuristic",
        unit="founder-built military-branch nodes", source=None,
        confidence="D",
        why="How many founder-built military nodes reach full military "
            "leverage (1.0) - a little over a fifth of the tree's 111+ "
            "military branch, chosen (see this method's own docstring) so "
            "leverage cannot be maxed by a token gesture nor by treating "
            "the whole military branch as a strategy unto itself. Not "
            "measured against any historical count of decisive weapons.")

    def military_equipment_burden_kg_per_soldier_per_year(self):
        """WHAT AN ARMY COSTS TO FIELD AND KEEP FED - THE ONE CROSSING TO
        sim/world/military_logistics.py THIS ENGINE WIRES IN, chosen out of
        that module's own ranked candidates (see its module docstring and
        this task's own brief) and everything else rejected. Reasons below.

        WHAT THIS RETURNS: the continuing annual physical claim - kilograms
        of worked iron and ammunition, NOT money - one equipped soldier
        represents at this founder's current military_leverage(), a
        straight-line interpolation between two points military_logistics.py
        computes from its own declared constants alone:

          leverage 0.0: a soldier equipped with cold steel only -
                        military_logistics.annual_iron_and_ammunition_burden_
                        kg_per_soldier() with no firearm - iron upkeep alone.
          leverage 1.0: a soldier equipped to MODERN_SERVICE_RIFLE standard,
                        firing MILITARY_EQUIPMENT_ERA_CAMPAIGN_TEMPO_
                        ENGAGEMENTS_PER_YEAR engagements a year (declared
                        below) - iron upkeep plus that many engagements'
                        worth of cartridges.

        This is THE stakeholder's own example run through the numbers: hand
        Rome a modern rifle and the physical claim equipping one soldier
        places on the state - not a battle outcome, not territory, just what
        the state has to keep supplying - is roughly an order of magnitude
        higher than equipping him with a sword, because a cartridge weapon
        burns mass in ammunition every engagement that a sword's occasional
        replacement does not. That is a genuine finding of military_
        logistics.py's own declared figures, not asserted here.

        WHY LEVERAGE, LINEARLY. military_leverage() is this engine's ONLY
        existing measure of how far up the military branch a founder has
        climbed, already used the same way (as a plain multiplier) by
        update_protection() and hazard_relief("output_factor"). Nothing in
        the tech-tree schema currently tags a node "this is specifically a
        firearm" versus "this is military generally" (see this task's own
        report for the measurement), so there is no cleaner signal to read
        military_equipment_era_burden's two endpoints against. Interpolating
        LINEARLY, rather than at some discrete leverage threshold, is this
        function's own labelled choice, not a reading of anything: a real
        replacement would key off which specific nodes are done (bow and
        armour traits at the low end, cartridge-firearm traits at the high
        end) rather than treating the whole branch as one dial.
        TRANSITIONAL HEURISTIC (CLAUDE.md SS3.4) for exactly that reason.

        WHAT THIS DOES NOT DO, AND WHY THOSE WERE REJECTED. The task ranked
        three candidates: this cost-to-field-and-feed figure; how far a
        force can project from home; whether a campaign is even feasible.
        The other two both need state this engine does not have and this
        crossing does not invent, per CLAUDE.md SS3.1's own instruction to
        say so plainly rather than manufacture a fake army to multiply:

          - PROJECTION RANGE (pack_animal_max_one_way_range_km()) needs a
            supply base and a distance from it - real coordinates and a
            campaign location - which live in sim/engine/geography.py
            (region_reach() and friends), a file this crossing is not
            permitted to touch and which has no notion of a military
            campaign either. The range figure itself does not vary with
            anything this engine tracks (it is a fixed property of one pack
            animal's mass and appetite, not of the founder's technology),
            so reporting it here would be a static fact bolted on, not a
            crossing that responds to play.
          - CAMPAIGN FEASIBILITY (sustainable_foraging_army_size()) needs a
            surplus-per-square-kilometre figure that is sim/world/
            agriculture.py's domain, a file this crossing is also not
            permitted to touch (and importing it would recreate exactly the
            cross-module coupling both modules' own docstrings refuse, for
            the same concurrent-editing reason). This engine also has no
            standing army size or location to test feasibility FOR: every
            civilisation's population (self.civ["population"]) is in the
            millions, so any population-derived force size this crossing
            could invent would clear a feasibility floor trivially and
            report nothing that ever varies - the "manufactured number with
            nothing to attach to" this task's brief explicitly warns against.

        WHY NOT MONEY. This function returns kilograms, and stays in
        kilograms all the way to where it is used (state_pressure_report()
        below) rather than being converted to a share of revenue. Turning a
        mass into currency needs a price, and grain/iron/ammunition prices
        are sim/engine/economy.py's domain - a file this crossing is not
        permitted to touch. Inventing a conversion rate here would be
        exactly the kind of unjustified constant CLAUDE.md SS3.1 rules out,
        dressed up as physics. The existing MILITARY_DEMAND_BASE_SHARE/
        MILITARY_DEMAND_LEVERAGE_SHARE monetary mechanic below is therefore
        left untouched by this crossing - see state_pressure_report()'s own
        comment at the point this function's result is used.
        """
        melee_kg = military_logistics.annual_iron_and_ammunition_burden_kg_per_soldier()
        rifle_kg = military_logistics.annual_iron_and_ammunition_burden_kg_per_soldier(
            firearm=military_logistics.MODERN_SERVICE_RIFLE,
            engagements_per_year=self.MILITARY_EQUIPMENT_ERA_CAMPAIGN_TEMPO_ENGAGEMENTS_PER_YEAR)
        leverage = self.military_leverage()
        return melee_kg + leverage * (rifle_kg - melee_kg)

    MILITARY_EQUIPMENT_ERA_CAMPAIGN_TEMPO_ENGAGEMENTS_PER_YEAR = declare(
        "MILITARY_EQUIPMENT_ERA_CAMPAIGN_TEMPO_ENGAGEMENTS_PER_YEAR", 6.0,
        kind="temporary_heuristic",
        unit="engagements/year", source=None, confidence="D",
        why="sim/world/military_logistics.py deliberately has no campaign-"
            "tempo model of its own (see its module docstring's WHERE THIS "
            "MODEL IS WRONG (d) and daily_supply_requirement_kg()'s "
            "engagements_per_day parameter) and takes one as a plain "
            "argument for exactly that reason; this is society.py's own "
            "placeholder for 'a modest campaigning season', standing in "
            "for the campaign-calendar mechanism (marches, sieges, battles "
            "at different intensities) that would derive a real figure. "
            "Six is an order-of-magnitude guess at 'a few real engagements "
            "a year, not one a week and not one a decade', with no source "
            "behind it - moving it changes military_equipment_burden_kg_"
            "per_soldier_per_year()'s reported number at full leverage but "
            "not its direction or its melee-tier floor.")

    PATRON_PROTECTION_LOCAL = declare(
        "PATRON_PROTECTION_LOCAL", 0.18, kind="temporary_heuristic",
        unit="dimensionless protection points (multiplies patronage_weight)",
        source=None, confidence="D",
        why="How much protection a local patron's name buys against "
            "accusation, scaled by this society's own patronage_weight. No "
            "attested source ties a specific protection value to a "
            "specific patron tier; a real figure needs a model of how "
            "much a patron of this rank could actually shield a client in "
            "court or before a magistrate.")
    PATRON_PROTECTION_SENATORIAL = declare(
        "PATRON_PROTECTION_SENATORIAL", 0.26, kind="temporary_heuristic",
        unit="dimensionless protection points (multiplies patronage_weight)",
        source=None, confidence="D",
        why="As PATRON_PROTECTION_LOCAL, senatorial tier - larger, tuned to "
            "feel proportionate to the step up in patron standing, not "
            "measured.")
    PATRON_PROTECTION_IMPERIAL = declare(
        "PATRON_PROTECTION_IMPERIAL", 0.32, kind="temporary_heuristic",
        unit="dimensionless protection points (multiplies patronage_weight)",
        source=None, confidence="D",
        why="As PATRON_PROTECTION_SENATORIAL, imperial tier - the largest "
            "of the three, tuned rather than measured.")

    MILITARY_USEFULNESS_PROTECTION = declare(
        "MILITARY_USEFULNESS_PROTECTION", 0.09, kind="temporary_heuristic",
        unit="dimensionless protection points (multiplies patronage_weight "
             "* military_leverage)", source=None, confidence="D",
        why="Extra protection a patron gives a founder who can supply "
            "cannon or bastions, on top of the flat patron protection - "
            "gated on having a patron at all, since a founder with no "
            "buyer for it is not protected by knowing how to cast one. "
            "Tuned to be a real but secondary bonus alongside the patron "
            "tiers, not measured against any attested case.")
    IDENTITY_COVER_PROTECTION = declare(
        "IDENTITY_COVER_PROTECTION", 0.12, kind="temporary_heuristic",
        unit="dimensionless protection points", source=None,
        confidence="D",
        why="What a respectable cover identity - books, a house, clothes, "
            "a secretary, a reputation for piety - is worth against "
            "accusation. See this method's own comment on what "
            "identity_cover actually buys; the figure itself is invented "
            "game balance.")
    CITIZENSHIP_PROTECTION = declare(
        "CITIZENSHIP_PROTECTION", 0.10, kind="temporary_heuristic",
        unit="dimensionless protection points", source=None,
        confidence="D",
        why="What formal citizenship (legal standing, the right to appeal "
            "a verdict) is worth against accusation. Plausible in kind - "
            "citizenship is a real legal shield - and invented in size.")
    COLLEGIUM_LICENSED_PROTECTION = declare(
        "COLLEGIUM_LICENSED_PROTECTION", 0.10, kind="temporary_heuristic",
        unit="dimensionless protection points", source=None,
        confidence="D",
        why="What a licensed collegium (a legally recognised guild body) "
            "is worth against accusation. Not sourced to any attested "
            "collegium privilege.")
    ENDOWMENT_LAND_PROTECTION = declare(
        "ENDOWMENT_LAND_PROTECTION", 0.08, kind="temporary_heuristic",
        unit="dimensionless protection points", source=None,
        confidence="D",
        why="What conspicuous benefaction - an endowment of land - is "
            "worth against accusation: a visible act of civic generosity "
            "that buys goodwill. Invented size.")
    LEARNED_INSTITUTION_PROTECTION = declare(
        "LEARNED_INSTITUTION_PROTECTION", 0.06, kind="temporary_heuristic",
        unit="dimensionless protection points", source=None,
        confidence="D",
        why="What founding a university or a school is worth against "
            "accusation - smallest of the built protections here, on the "
            "reasoning that a teacher is respectable but less politically "
            "connected than a patron or a magistracy. Tuned, not measured.")
    PRESSED_OFFICE_PROTECTION = declare(
        "PRESSED_OFFICE_PROTECTION", 0.10, kind="temporary_heuristic",
        unit="dimensionless protection points", source=None,
        confidence="D",
        why="The protection a pressed civic office buys, once the state "
            "has noticed the household - a burden and a shield at once, "
            "see office_report()'s own docstring. Sized similarly to the "
            "built protections above rather than measured against any "
            "attested decurionate privilege.")
    REPUTATION_PROTECTION_CAP = declare(
        "REPUTATION_PROTECTION_CAP", 0.30, kind="temporary_heuristic",
        unit="dimensionless (maximum protection from reputation alone)",
        source=None, confidence="D",
        why="Ceiling on how much sheer personal reputation, independent of "
            "any patron or office, can protect a founder - so reputation "
            "alone cannot out-protect every built defence combined. "
            "Chosen to match the shape of the other protection caps in "
            "this method, not measured.")
    REPUTATION_PROTECTION_SCALE = declare(
        "REPUTATION_PROTECTION_SCALE", 260.0, kind="temporary_heuristic",
        unit="reputation points per unit of protection", source=None,
        confidence="D",
        why="How fast reputation converts into protection, against "
            "REPUTATION_PROTECTION_CAP above. Reputation's own scale is "
            "itself invented (see STANDING_* in economy.py), so this "
            "denominator is a heuristic layered on a heuristic.")
    BRIBERY_PROTECTION_CAP = declare(
        "BRIBERY_PROTECTION_CAP", 0.30, kind="temporary_heuristic",
        unit="dimensionless (maximum protection from bribery alone)",
        source=None, confidence="D",
        why="Ceiling on how much protection bribery, advocacy and piety "
            "can buy on their own, matching REPUTATION_PROTECTION_CAP so "
            "neither spendable defence dominates the other. Tuned, not "
            "measured against any attested bribe schedule.")
    BRIBERY_PROTECTION_INCOME_SHARE = declare(
        "BRIBERY_PROTECTION_INCOME_SHARE", 0.6, kind="temporary_heuristic",
        unit="dimensionless (fraction of revenue treated as a full bribery "
             "budget)", source=None, confidence="D",
        why="What share of a year's revenue spent on bribes counts as a "
            "maximal bribery effort, the denominator bribes_ytd is judged "
            "against. No source ties a specific spending share to a "
            "specific bribe's actual effect on an accusation; a real "
            "figure needs a model of what a bribe could actually buy from "
            "a given magistrate.")
    PROTECTION_CEILING = declare(
        "PROTECTION_CEILING", 0.92, kind="temporary_heuristic",
        unit="dimensionless (maximum total protection)", source=None,
        confidence="D",
        why="However many defences a household stacks, protection never "
            "reaches 1.0 - nothing makes a founder completely immune to "
            "accusation. Chosen to leave alarm_of's own protection floor "
            "(ALARM_PROTECTION_FLOOR) meaningful even at maximum "
            "protection; not measured.")

    def update_protection(self):
        """Standing, office and MONEY all protect. The old model had money only
        endangering you, which is backwards: wealth buys advocates, priesthoods,
        magistracies and, in a society with a bribability of 0.55, verdicts."""
        protection = 0.0
        weights = self.w
        if self.running("patron_local"):        protection += self.PATRON_PROTECTION_LOCAL * weights["patronage_weight"]
        if self.running("patron_senatorial"):   protection += self.PATRON_PROTECTION_SENATORIAL * weights["patronage_weight"]
        if self.running("patron_imperial"):     protection += self.PATRON_PROTECTION_IMPERIAL * weights["patronage_weight"]
        # AN ARMOURER IS PROTECTED DIFFERENTLY FROM A PHILOSOPHER, AND ONLY
        # WHEN SOMEBODY WANTS WHAT HE MAKES. Sejanus's people were safe until
        # they no longer had anything Tiberius needed, and the same logic
        # runs the other way: a patron who can call on your powder mill or
        # your bastion design has a reason to keep you out of court that
        # identity_cover and citizenship do not supply on their own. Gated on
        # having a patron at all - knowing how to cast a cannon with nobody
        # to sell it to is not leverage, it is just a dangerous thing to be
        # caught doing, which is exactly what alarm_of's weapon_democratising
        # term already charges you for and this does NOT cancel.
        if (self.running("patron_local") or self.running("patron_senatorial")
                or self.running("patron_imperial")):
            protection += self.MILITARY_USEFULNESS_PROTECTION * weights["patronage_weight"] * self.military_leverage()
        # IT SAYS "REDUCES ALL FUTURE SUSPICION" AND IT DID NOTHING OF THE KIND.
        # identity_cover's entire implementation was +1.0 to the reputation
        # floor and +400 to the credit limit, and the suspicion it promised to
        # reduce was a field that no longer exists. Its real value was that it
        # gated a quarter of the tree - which is why every tester concluded
        # they had to have it and assumed it was about illegal activity. It is
        # a persona: books, a house, clothes, a secretary and a reputation for
        # piety. What that buys is that an inexplicable effect coming out of
        # YOUR workshop is read as learning rather than as sorcery.
        if self.running("identity_cover"):      protection += self.IDENTITY_COVER_PROTECTION
        if self.has("citizenship"):         protection += self.CITIZENSHIP_PROTECTION
        if self.running("collegium_licensed"):  protection += self.COLLEGIUM_LICENSED_PROTECTION
        if self.running("endowment_land"):      protection += self.ENDOWMENT_LAND_PROTECTION   # conspicuous benefaction
        if self.running("fin_university") or self.running("school_founded"): protection += self.LEARNED_INSTITUTION_PROTECTION
        # BOTH A BURDEN AND A SHIELD. Once this household is large enough for
        # the state to press a civic office on it (state_notice() past
        # STATE_NOTICE_THRESHOLD - see office_report(), _state_pressure()),
        # that office costs money every year AND is itself standing: the
        # historical pattern this answers is that the very rich were pressed
        # into exactly this kind of service, not offered it. Unlike the
        # patron_* terms above, this needs nothing built - it is not a choice
        # - which is the whole point: "the version you do not get to decline
        # cheaply".
        if self.state_notice() > self.STATE_NOTICE_THRESHOLD:
            protection += self.PRESSED_OFFICE_PROTECTION
        protection += min(self.REPUTATION_PROTECTION_CAP,
                           self.household.reputation / self.REPUTATION_PROTECTION_SCALE)
        # BRIBERY, ADVOCACY AND PIETY: an explicit, spendable defence.
        income = max(1.0, self.revenue())
        protection += min(self.BRIBERY_PROTECTION_CAP,
                           (self.household.bribes_ytd / (income * self.BRIBERY_PROTECTION_INCOME_SHARE))
                           * weights["bribability"])
        self.household.protection = min(self.PROTECTION_CEILING, protection)

    WITHDRAW_EVERY = declare(
        "WITHDRAW_EVERY", 12, kind="temporary_heuristic", unit="years",
        source=None, confidence="D",
        why="How long after withdrawing from public life the founder must "
            "wait before doing it again - being seen to retire twice in a "
            "short span is not retirement, it is a performance. A real "
            "figure needs a model of how quickly a specific society forgets "
            "a public retirement; this is a round number chosen to feel "
            "like a real cooling-off period, not derived from one.")
    WITHDRAW_MIN_EMINENCE_FRACTION = declare(
        "WITHDRAW_MIN_EMINENCE_FRACTION", 0.5, kind="temporary_heuristic",
        unit="dimensionless (fraction of eminence_danger)", source=None,
        confidence="D",
        why="Below this share of the danger line, nobody has noticed the "
            "founder enough for withdrawing to buy anything - so the "
            "action is refused rather than silently wasting standing. "
            "Chosen to match the other half-danger-line thresholds this "
            "file uses (e.g. YOU ARE BECOMING CONSPICUOUS in core.py), not "
            "derived from a model of what makes someone worth withdrawing "
            "from.")
    WITHDRAW_REPUTATION_RETENTION = declare(
        "WITHDRAW_REPUTATION_RETENTION", 0.5, kind="temporary_heuristic",
        unit="dimensionless (fraction of the gap above the standing floor "
             "kept)", source=None, confidence="D",
        why="Withdrawing moves reputation only halfway to the standing "
            "floor, not all the way to it - the work already done still "
            "stands for something. Chosen so withdrawal is a real, costly "
            "decision without being total self-erasure; not derived from "
            "any account of how quickly a real retirement was actually "
            "forgotten.")
    WITHDRAW_EMINENCE_RETENTION = declare(
        "WITHDRAW_EMINENCE_RETENTION", 0.5, kind="temporary_heuristic",
        unit="dimensionless (fraction of eminence kept)", source=None,
        confidence="D",
        why="Withdrawing halves eminence outright, mirroring "
            "WITHDRAW_REPUTATION_RETENTION's own halving of the standing "
            "gap - the one lever this file gives against prominence "
            "should visibly work. Tuned to make the decision worthwhile, "
            "not measured.")

    def withdraw_from_public_life(self):
        """Deliberately become a smaller man. The one lever against prominence.

        Both play testers of round eight died to eminence and both said the
        same thing about it: `help eminence` says "nothing lowers it directly,
        which is the point", the two counters named are ten-year builds behind
        long chains, and the steady state the game prints is above the danger
        line - so playing well is a death sentence and no command reads as
        "get smaller". That is a mechanic with no decision in it.

        This is the decision. It is what the men this hazard is modelled on
        actually did, and what the game's own confiscation event already
        describes ("you withdraw from public life for a while"): stop
        appearing, stop publishing under your own name, let somebody else take
        the credit. The price is reputation, which in this model is not
        cosmetic - it sets your credit limit, your protection, what wages you
        must pay, how fast the market supplies you and the calendar floor on
        every project. You cannot get small and stay grand.

        What you BUILT you keep: the floor under reputation is exactly the work
        that stands, so this takes away the novelty and leaves the corpus.
        """
        if not self.founder_alive:
            return False, "there is nobody left to withdraw"
        last = getattr(self.household, "last_withdrawal", -999)
        if self.year - last < self.WITHDRAW_EVERY:
            return False, ("you stepped back in %d; doing it again so soon is "
                           "not retirement, it is a performance, and nobody "
                           "would believe it. You could again in %d"
                           % (last, last + self.WITHDRAW_EVERY))
        floor = self.standing_floor()
        # DO NOT LET THEM PAY FOR NOTHING. Same rule as `bribe`: work out
        # whether it would buy anything before taking anything. At an eminence
        # nobody has noticed, retiring is not modesty, it is throwing away the
        # standing that gets your work funded and staffed.
        danger = self.cfg["eminence_danger"]
        if self.household.eminence < danger * self.WITHDRAW_MIN_EMINENCE_FRACTION:
            return False, ("nobody is watching you closely enough for this to "
                           "buy anything: prominence is %.1f against a danger "
                           "line of %.0f. Withdrawing now would only cost you "
                           "the standing that gets your work funded. Nothing "
                           "was changed." % (self.household.eminence, danger))
        if self.household.reputation <= floor + 0.5:
            return False, ("you are already as obscure as a man who has built "
                           "what you have built can be. What is left of your "
                           "standing is the work itself, and that does not go "
                           "away. Nothing was changed.")
        self.household.last_withdrawal = self.year
        rep_before, em_before = self.household.reputation, self.household.eminence
        # Halfway to the floor, not to zero: the work stands.
        self.household.reputation = floor + (self.household.reputation - floor) * self.WITHDRAW_REPUTATION_RETENTION
        self.household.eminence *= self.WITHDRAW_EMINENCE_RETENTION
        self.update_protection()
        msg = ("you withdraw from public life: reputation %.1f -> %.1f, "
               "eminence %.1f -> %.1f. What you built still stands, and that "
               "is the floor under your standing (%.1f). It costs you credit, "
               "protection and cheap labour until it grows back."
               % (rep_before, self.household.reputation, em_before, self.household.eminence, floor))
        self.household.log.append((self.year, msg))
        return True, msg

    EMINENCE_HAZARD_SCALE = declare(
        "EMINENCE_HAZARD_SCALE", 90.0, kind="temporary_heuristic",
        unit="eminence points per unit of yearly ruin probability",
        source=None, confidence="D",
        why="How much eminence above the danger line it takes to add a "
            "full 100% to this year's chance of a prominence event - the "
            "same denominator core.py's step() uses when it actually rolls "
            "the dice, kept as one shared constant so the number quoted "
            "here can never disagree with the one that fires. Tuned so "
            "the risk climbs noticeably but not instantly past the line, "
            "not measured against any real rate of political destruction.")
    EMINENCE_OUTCOME_CONFISCATION_SHARE = declare(
        "EMINENCE_OUTCOME_CONFISCATION_SHARE", 0.45, kind="temporary_heuristic",
        unit="dimensionless (share of prominence events)", source=None,
        confidence="D",
        why="Of the events prominence causes, the share that are property "
            "confiscation and forced retirement - shared with core.py's "
            "step(), which rolls against this same split. Invented "
            "proportions, not measured against any attested rate of each "
            "outcome for a fallen Roman grandee.")
    EMINENCE_OUTCOME_PATRON_LOST_SHARE = declare(
        "EMINENCE_OUTCOME_PATRON_LOST_SHARE", 0.35, kind="temporary_heuristic",
        unit="dimensionless (share of prominence events)", source=None,
        confidence="D",
        why="Of the events prominence causes, the share that are a patron "
            "destroyed in someone else's quarrel - shared with core.py's "
            "step(). Invented, not measured.")
    EMINENCE_OUTCOME_RUN_ENDS_SHARE = declare(
        "EMINENCE_OUTCOME_RUN_ENDS_SHARE", 0.20, kind="temporary_heuristic",
        unit="dimensionless (share of prominence events)", source=None,
        confidence="D",
        why="Of the events prominence causes, the share that end the run "
            "outright - the remainder after EMINENCE_OUTCOME_CONFISCATION_"
            "SHARE and EMINENCE_OUTCOME_PATRON_LOST_SHARE, shared with "
            "core.py's step(). Invented, not measured.")

    def eminence_report(self):
        """Where you stand against the one danger no patron can protect you from."""
        cfg = self.cfg
        danger = cfg["eminence_danger"]
        yearly = self.prominence_hazard()
        # eminence decays self.EMINENCE_DECAY_RATE a year (see core.py's
        # step()) and gains `yearly`, so this is where it settles if
        # nothing changes.
        settles = yearly / (1.0 - self.EMINENCE_DECAY_RATE)
        probability = max(0.0, (self.household.eminence - danger) / self.EMINENCE_HAZARD_SCALE)
        helps = []
        if not self.running("academy_network"):
            helps.append("a wide, dispersed institution is harder to destroy than "
                         "one great man")
        if self.running("patron_imperial"):
            helps.append("you are as close to the throne as it is possible to "
                         "stand, which is the most exposed place there is")
        if self.household.capital > self.EMINENCE_WEALTH_VISIBLE_THRESHOLD:
            helps.append("visible wealth is half of what makes you a target")
        # THE LEVER, NAMED. Two play testers read this screen, found no command
        # in it that meant "get smaller", and died. It is `withdraw`.
        _last = getattr(self.household, "last_withdrawal", None)
        if _last is not None and self.year - _last < self.WITHDRAW_EVERY:
            _lever_note = ("you stepped back in %d; again no sooner than %d"
                  % (_last, _last + self.WITHDRAW_EVERY))
        else:
            _lever_note = ("'withdraw' halves this now and gives up half the reputation "
                  "you hold above what your work alone is worth (%.1f). That is "
                  "a real price - reputation is your credit, your protection, "
                  "your wages and the pace of your projects - and it is the only "
                  "thing that lowers prominence the year you do it."
                  % self.standing_floor())
        return {"now": round(self.household.eminence, 2),
                "dangerous_above": danger,
                "settles_at_if_nothing_changes": round(settles, 1),
                "chance_of_ruin_this_year": round(probability, 4),
                # WHICH OUTCOME. A play tester survived two confiscations and
                # was then ended by a third roll, with "7% chance of ruin this
                # year" shown before all three, and had no way to know the rolls
                # differed. They do: 45% a confiscation, 35% a patron lost, 20%
                # the end. Reading "chance of ruin" as "chance of death" was the
                # game's fault, not theirs.
                "if_it_lands_it_is": {
                    "property confiscated and a forced retirement": self.EMINENCE_OUTCOME_CONFISCATION_SHARE,
                    "your patron destroyed in someone else's quarrel": self.EMINENCE_OUTCOME_PATRON_LOST_SHARE,
                    "the end of the run": self.EMINENCE_OUTCOME_RUN_ENDS_SHARE},
                "chance_the_run_ENDS_this_year": round(probability * self.EMINENCE_OUTCOME_RUN_ENDS_SHARE, 4),
                "the_one_lever": _lever_note,
                "what_would_change_it": helps,
                "note": "This is prominence, not scandal. It cannot be bribed "
                        "away, and every defence that makes you safer from "
                        "accusation makes you larger and so raises this."}

    EMINENCE_HAZARD_BASE_SCALE = declare(
        "EMINENCE_HAZARD_BASE_SCALE", 2.2, kind="temporary_heuristic",
        unit="dimensionless", source=None, confidence="D",
        why="Overall scale on the yearly prominence hazard - see this "
            "method's own docstring for why the mechanic exists at all "
            "(everything else saturates and left 200 successful runs out "
            "of 200 with nothing able to touch the founder). Tuned by "
            "measuring settled values against the danger line for two "
            "dice-free trials (see the 'A SIXTH OFF' comment below); not "
            "derived from any model of how quickly a real autocracy turns "
            "on a client.")
    EMINENCE_DANGER_WEIGHT_DEFAULT = declare(
        "EMINENCE_DANGER_WEIGHT_DEFAULT", 0.5, kind="temporary_heuristic",
        unit="dimensionless", source=None, confidence="D",
        why="Fallback value for a civilisation file that does not set its "
            "own w_eminence_danger weight - a mid-scale default rather "
            "than zero, so a civilisation that forgot to set this is not "
            "silently immune to the mechanic. Not itself measured.")
    EMINENCE_HAZARD_REPUTATION_SHARE = declare(
        "EMINENCE_HAZARD_REPUTATION_SHARE", 0.70, kind="temporary_heuristic",
        unit="dimensionless (weight in the hazard mix)", source=None,
        confidence="D",
        why="How much of the prominence hazard comes from reputation "
            "(squared, so it is dominated by the already-famous) versus "
            "visible wealth - reputation weighted heavier because being "
            "personally renowned is closer to what actually destroyed "
            "Sejanus, Seneca and Thrasea Paetus (see this method's own "
            "docstring) than mere money was. Tuned split, not fitted to "
            "any of those cases individually.")
    EMINENCE_HAZARD_WEALTH_SHARE = declare(
        "EMINENCE_HAZARD_WEALTH_SHARE", 0.30, kind="temporary_heuristic",
        unit="dimensionless (weight in the hazard mix)", source=None,
        confidence="D",
        why="The complement of EMINENCE_HAZARD_REPUTATION_SHARE: how much "
            "of the prominence hazard comes from visible wealth alone.")
    EMINENCE_REPUTATION_SCALE = declare(
        "EMINENCE_REPUTATION_SCALE", 100.0, kind="temporary_heuristic",
        unit="reputation points", source=None, confidence="D",
        why="Reference reputation this hazard treats as '1.0 famous' - "
            "reputation's own scale is itself invented (see STANDING_* in "
            "economy.py), so this normalisation is a heuristic layered on "
            "a heuristic.")
    EMINENCE_WEALTH_VISIBLE_THRESHOLD = declare(
        "EMINENCE_WEALTH_VISIBLE_THRESHOLD", 250000.0, kind="temporary_heuristic",
        unit="denarii", source=None, confidence="D",
        why="Capital treated as '1.0 visibly rich' for the prominence "
            "hazard, and reused verbatim by eminence_report's own "
            "what_would_change_it note and by household_scale's "
            "HOUSEHOLD_WEALTH_SATURATES_AT comment as the smaller, "
            "personal-wealth line beneath that mechanic's much larger "
            "fiscal one. A round number marking enough personal wealth to "
            "be a courtier's envy, not measured against any specific "
            "attested Roman fortune.")
    EMINENCE_IMPERIAL_PATRON_MULTIPLIER = declare(
        "EMINENCE_IMPERIAL_PATRON_MULTIPLIER", 1.5, kind="temporary_heuristic",
        unit="dimensionless multiplier", source=None, confidence="D",
        why="Standing nearest the throne is the most exposed place there "
            "is - see this method's own docstring - so an imperial patron "
            "raises the hazard by half again. Tuned to be a real, visible "
            "cost to the strongest patronage tier, not measured.")
    EMINENCE_ACADEMY_NETWORK_MULTIPLIER = declare(
        "EMINENCE_ACADEMY_NETWORK_MULTIPLIER", 0.65, kind="temporary_heuristic",
        unit="dimensionless multiplier", source=None, confidence="D",
        why="A wide, dispersed institution is harder to destroy than one "
            "great man, cutting the hazard by over a third. Tuned to make "
            "academy_network a real hedge without eliminating the hazard "
            "outright; not measured.")
    EMINENCE_FAMILIARITY_RELIEF = declare(
        "EMINENCE_FAMILIARITY_RELIEF", 0.15, kind="temporary_heuristic",
        unit="dimensionless (fraction of hazard familiarity removes)",
        source=None, confidence="D",
        why="How much familiarity - the model's own measure of how "
            "unsurprising the founder has become - softens the prominence "
            "hazard. 'A SIXTH OFF, NOT A THIRD' below records that this "
            "was first tried at a third and measured, across three "
            "thousand run-years, to make the mechanic literally "
            "unreachable (every reported chance of ruin summed to 0.00); "
            "a sixth was chosen so a decades-long fixture of the city "
            "settles just under the danger line and one who has also "
            "reached the throne settles well over it - calibrated against "
            "that measurement, not derived from a model of habituation.")

    def prominence_hazard(self):
        """Eminence is its own hazard, and protection does NOT reduce it.

        The model had a defect that only showed once the tree got big: every
        defence saturates. Protection caps at 0.92, familiarity decays alarm to
        a tenth, reputation sits at 97 out of 100 by the second century, and the
        result was 200 successful runs out of 200. Nothing could touch you.

        What was missing is that in an autocracy prominence is not only a shield,
        it is a target, and the people who protect you are the people who destroy
        you when you outgrow them. Sejanus was the most protected man in Rome
        until the morning he was not. Seneca was the emperor's own tutor. Thrasea
        Paetus was merely admired. None of them was brought down by a mob or by a
        magic charge; they were brought down by being too eminent in a system
        with one man at the top.

        So this rises with reputation and with visible wealth, it is multiplied
        by having got close to the throne, and no amount of patronage reduces it.
        It feeds scandal rather than killing you outright, because the usual
        outcome is a bad year, a confiscation or a lost patron, not a death.
        """
        weights = self.w
        rep = max(0.0, self.household.reputation) / self.EMINENCE_REPUTATION_SCALE
        wealth = min(1.0, max(0.0, self.household.capital) / self.EMINENCE_WEALTH_VISIBLE_THRESHOLD)
        hazard = (self.EMINENCE_HAZARD_BASE_SCALE
                  * weights.get("w_eminence_danger", self.EMINENCE_DANGER_WEIGHT_DEFAULT)
                  * (self.EMINENCE_HAZARD_REPUTATION_SHARE * rep * rep
                     + self.EMINENCE_HAZARD_WEALTH_SHARE * wealth))
        if self.running("patron_imperial"):
            hazard *= self.EMINENCE_IMPERIAL_PATRON_MULTIPLIER          # nearest the throne, most exposed to its turnover
        # A wide, dispersed institution is harder to destroy than one great man.
        if self.running("academy_network"):
            hazard *= self.EMINENCE_ACADEMY_NETWORK_MULTIPLIER
        # AND A CITY GETS USED TO YOU. familiarity is the model's own measure of
        # how unsurprising you have become - it already decays the alarm your
        # work causes - and it was the one defence prominence ignored. Two play
        # testers read "EMINENCE is dangerous above 26 (settles near 39.2)" and
        # correctly described it as the game announcing that a successful run is
        # scheduled to die. A man who has been the great man of the city for
        # ninety years is a fixture, not a novelty; he is still exposed, and he
        # is not what he was in his first decade.
        #
        # A SIXTH OFF, NOT A THIRD. The first attempt at this took a third, and
        # a break tester then measured three thousand run-years in which the
        # sum of every reported chance of ruin was exactly 0.00 - a mechanic
        # that cannot reach you is not a hazard, it is scenery, and the
        # correction had gone as far past the line as the original sat the
        # other side of it. At a sixth, a man who has been the city's fixture
        # for ninety years settles just under the danger line and a man who has
        # also got himself next to the throne settles well over it, which is
        # the shape the whole mechanic is about.
        hazard *= (1.0 - self.EMINENCE_FAMILIARITY_RELIEF * self.household.familiarity)
        return hazard

    # ---- THE STATE NOTICES YOU ----------------------------------------------
    # A player who had already won the game - 691 employees, 1.1 billion
    # denarii, working firearms, a power grid, a railway - filed the sharper
    # half of a complaint about history being on rails: technology changed how
    # much a dated hazard hurt, never whether the state itself reacted to what
    # had been built under it. The state never once requisitioned the
    # household's output, demanded military supply, pressed an office on it,
    # or threatened confiscation. Pre-industrial state predation on a large
    # private fortune is one of the most reliable facts of the period this
    # game is set in - the annona and the munera, the Han salt and iron
    # monopolies, English purveyance, Mexica tribute are not colour, they are
    # how these states paid for themselves - and scandal (the only existing
    # political counterweight) saturates and is bribed away long before a
    # household reaches this scale (see 6b in core.py's step()).
    #
    # THIS DOES NOT INVENT A SECOND POLITICAL SCALE. Every input below is a
    # number the engine already tracks for another purpose - eminence,
    # capital, headcount (labour.py), military_leverage() above, this civil-
    # isation's own state_capacity - combined freshly for THIS question, the
    # same way military_leverage() and prominence_hazard() each already
    # recombine self.household.done/self.household.reputation/self.household.capital for their own
    # different questions. Nothing here is stored as a new persistent stat
    # that decays or grows on its own clock the way reputation/scandal/
    # eminence/protection do; state_notice() is recomputed from those every
    # time it is read, so there is nothing new to save, load, or drift.
    #
    # state_capacity (0..1 per civilisation, _SCHEMA.md's own "can the state
    # fund and compel a large project?") is the FIRST factor, not an
    # afterthought: Rome (0.85) and Han (0.9) start near their own ceiling, so
    # for them this whole mechanic is gated almost entirely by household scale
    # below, exactly as history would predict for two empires that already
    # had annona fleets and salt monopolies running before this household's
    # founder was born. Norse (0.15) caps the PRODUCT so low that none of the
    # thresholds below can be crossed at all while the state stays that weak -
    # "the thing is an assembly, not a state" (norse_900ad.json's own
    # institutions note) - which is the honest answer for a society with no
    # tax office, not a gap in the mechanic. A Norse run that spends centuries
    # building the institutions this civilisation's own opening text predicts
    # ("kings, bishops, written law, taxes and towns") raises state_capacity
    # by the same tech effects (mil_conscription_reserve, fin_central_bank,
    # telegraph and railway among them - see _TECH_EFFECTS.json) that do it
    # for everyone else, and can eventually cross these same lines; that is
    # the mechanic correctly answering "what if the player builds the state
    # up", not a special case written in for it.
    HOUSEHOLD_HEADCOUNT_SATURATES_AT = declare(
        "HOUSEHOLD_HEADCOUNT_SATURATES_AT", 500.0, kind="temporary_heuristic",
        unit="employees+slaves+freedmen", source=None, confidence="D",
        why="Headcount at which household_scale()'s headcount term "
            "saturates at 1.0 - a round number chosen so the state's "
            "notice keeps climbing over most of a run's plausible staff "
            "size rather than maxing out early; not fitted to any "
            "specific historical household's size.")
    # Ten times prominence_hazard's own 250,000-denarii "visibly rich" line,
    # deliberately: that number marks enough personal wealth for a courtier to
    # envy, which is a different and smaller bar than enough FISCAL scale for
    # a treasury to think assessing your output is worth an official's time.
    # A household a few times richer than a senator is eminence's problem,
    # already modelled; a household whose output could supply an army or a
    # grain fleet is this one's, and that is a ten-million-denarii household,
    # not a quarter-million one - see the measured trajectories in this
    # section's own commit for where Rome and Han actually cross it.
    HOUSEHOLD_WEALTH_SATURATES_AT = declare(
        "HOUSEHOLD_WEALTH_SATURATES_AT", 10000000.0, kind="temporary_heuristic",
        unit="denarii", source=None,
        confidence="D",
        why="Capital at which household_scale()'s wealth term saturates - "
            "ten times prominence_hazard's own 250,000-denarii 'visibly "
            "rich' line (EMINENCE_WEALTH_VISIBLE_THRESHOLD), deliberately: "
            "personal envy and fiscal scale worth an official's time are "
            "different, larger bars. See the comment above for the "
            "reasoning; the figure itself is chosen to fit the measured "
            "trajectories of two dice-free trials, not derived from a "
            "fiscal model.")

    def household_scale(self):
        """0..1: how large and visible this household is to a state deciding
        whether it is worth the bother of leaning on - not a new stat, a
        fresh combination of three the engine already has. Headcount
        (labour.py's own employees+slaves+freedmen) and visible wealth are
        weighted heaviest, because a state assessing a household for
        requisition or tribute is counting workshops and granaries, not
        court gossip; eminence (already the engine's own measure of personal
        prominence) contributes a smaller share, because a household can be
        economically enormous and personally obscure - the exact shape of
        the player complaint this answers, reached at 4,213 employees and
        1.77 billion denarii while eminence itself never once crossed its
        own danger line (see the Rome dice-free trial this mechanic was
        measured against). Every term sqrt-saturates or caps at 1.0, the same
        diminishing shape military_leverage() and agrarian_slack() already
        use: the five-hundredth employee does not make you five hundred
        times more noticeable than the first.
        """
        head = self.headcount()
        head_s = min(1.0, math.sqrt(max(0.0, head)
                                    / self.HOUSEHOLD_HEADCOUNT_SATURATES_AT))
        wealth_s = min(1.0, max(0.0, self.household.capital)
                       / self.HOUSEHOLD_WEALTH_SATURATES_AT)
        danger = self.cfg["eminence_danger"]
        emin_s = min(1.0, max(0.0, self.household.eminence) / danger)
        return (self.HOUSEHOLD_SCALE_HEADCOUNT_WEIGHT * head_s
                + self.HOUSEHOLD_SCALE_WEALTH_WEIGHT * wealth_s
                + self.HOUSEHOLD_SCALE_EMINENCE_WEIGHT * emin_s)

    HOUSEHOLD_SCALE_HEADCOUNT_WEIGHT = declare(
        "HOUSEHOLD_SCALE_HEADCOUNT_WEIGHT", 0.45, kind="temporary_heuristic",
        unit="dimensionless (weight in household_scale mix)", source=None,
        confidence="D",
        why="How much household_scale() weights headcount - heaviest, "
            "because a state assessing a household for requisition counts "
            "workshops and granaries, not court gossip (see this method's "
            "own docstring). Tuned split, not fitted to any specific "
            "fiscal assessment.")
    HOUSEHOLD_SCALE_WEALTH_WEIGHT = declare(
        "HOUSEHOLD_SCALE_WEALTH_WEIGHT", 0.35, kind="temporary_heuristic",
        unit="dimensionless (weight in household_scale mix)", source=None,
        confidence="D",
        why="How much household_scale() weights visible wealth - second "
            "heaviest, for the same reasoning as "
            "HOUSEHOLD_SCALE_HEADCOUNT_WEIGHT. Tuned, not measured.")
    HOUSEHOLD_SCALE_EMINENCE_WEIGHT = declare(
        "HOUSEHOLD_SCALE_EMINENCE_WEIGHT", 0.20, kind="temporary_heuristic",
        unit="dimensionless (weight in household_scale mix)", source=None,
        confidence="D",
        why="How much household_scale() weights eminence (personal "
            "prominence) - smallest, because a household can be "
            "economically enormous and personally obscure, the exact gap "
            "this mechanic exists to close (see this method's own "
            "docstring). Tuned, not measured.")

    def state_notice(self):
        """0..1: state_capacity times household_scale() - the single gate
        every pressure below checks before it does anything. Below its
        thresholds nobody in government has a reason to know this household
        exists; above them, the state's own capacity to organise and compel
        (state_capacity) decides how hard that interest bites, exactly the
        reading Diocletian's own hazard note (rome_100ad.json) gives that
        field: his reforms make the state heavier, not the household richer,
        and the patronage shift that hazard already carries is the other
        half of the same fact this mechanic spends on requisition instead.
        """
        return self.state_capacity * self.household_scale()

    # Below this, the state has bigger things to do than assess one
    # household: the measured Han dice-free trial (strategies/planned_han.json,
    # deterministic_sim) crosses it around year 400-420, a hundred and thirty-
    # odd years before that trial's own goal year of 551, not in some epilogue
    # after the tree is already finished - see this section's commit message
    # for the full trajectory. Requisition and office share this one line:
    # both are the state treating an enterprise as large enough to count,
    # just in two different registers (goods taken vs. a burden of service).
    STATE_NOTICE_THRESHOLD = declare(
        "STATE_NOTICE_THRESHOLD", 0.35, kind="temporary_heuristic",
        unit="dimensionless (state_notice, 0..1)", source=None,
        confidence="D",
        why="Below this, the state has bigger things to do than assess "
            "one household. Fitted so a Han dice-free trial crosses it "
            "around year 400-420, well before that trial's own year-551 "
            "goal, not in an epilogue after the tree is finished - a "
            "calibration choice against measured trajectories, not a "
            "derivation from a fiscal-capacity model.")
    STATE_NOTICE_THRESHOLD_MILITARY = declare(
        "STATE_NOTICE_THRESHOLD_MILITARY", 0.20, kind="temporary_heuristic",
        unit="dimensionless (state_notice, 0..1)", source=None,
        confidence="D",
        why="Arms draw attention at a lower bar than general economic "
            "weight - 'a household that can make firearms in 400 AD Rome "
            "will be asked for them' does not wait for the household to "
            "also be rich - so this sits below STATE_NOTICE_THRESHOLD, "
            "paired with MIL_LEVERAGE_FLOOR_FOR_DEMAND rather than acting "
            "on notice alone. Tuned, not measured.")
    MIL_LEVERAGE_FLOOR_FOR_DEMAND = declare(
        "MIL_LEVERAGE_FLOOR_FOR_DEMAND", 0.20, kind="temporary_heuristic",
        unit="dimensionless (military_leverage, 0..1)", source=None,
        confidence="D",
        why="Roughly one military-branch node done (military_leverage() "
            "reaches 0.20 at n=1 of 25 - see that method's own docstring): "
            "the FIRST working gun, not a standing army, is already "
            "enough for a state that can fight to want an accounting of "
            "it. Chosen to line up with military_leverage()'s own curve, "
            "not measured independently.")
    MILITARY_DEMAND_COOLDOWN_YEARS = declare(
        "MILITARY_DEMAND_COOLDOWN_YEARS", 20.0, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="Minimum gap between one military-supply demand and the next "
            "on the same household - long enough that it reads as an "
            "occasional levy rather than an annual tax. Round number, not "
            "derived from any attested requisition schedule.")
    MILITARY_DEMAND_ANNUAL_CHANCE = declare(
        "MILITARY_DEMAND_ANNUAL_CHANCE", 0.10, kind="temporary_heuristic",
        unit="dimensionless (yearly probability once eligible)",
        source=None, confidence="D",
        why="Once a household is militarily useful and visible enough "
            "(military_demand_eligible), the yearly chance the state "
            "actually asks. Invented frequency, not fitted to any "
            "attested requisition rate.")
    # The tail risk, and deliberately a much higher line than the one above:
    # confiscation is not the ordinary cost of being noticed, it is what
    # happens at the very top of the same scale, to a household the state
    # has decided is too large to go on merely taxing. Measured against both
    # dice-free trials, this is crossed only in the final quarter-to-sixth of
    # the run (Han: ~80 years before goal; Rome: inside the explosive final
    # staffing surge that actually finishes the tree, not after it) - see
    # this section's commit message. Never lowered to make this bite earlier:
    # a tail risk that fires in the middle of an ordinary run is not a tail
    # risk, it is a second flat tax wearing a dice roll.
    STATE_NOTICE_THRESHOLD_CONFISCATION = declare(
        "STATE_NOTICE_THRESHOLD_CONFISCATION", 0.75, kind="temporary_heuristic",
        unit="dimensionless (state_notice, 0..1)", source=None,
        confidence="D",
        why="Where the tail confiscation risk begins - see the comment "
            "above: calibrated so it is crossed only late (the final "
            "quarter to sixth of a run) in both measured dice-free "
            "trials, deliberately never lowered to make it bite earlier. "
            "A calibration choice against those trajectories, not a "
            "derivation from a state-capacity model.")
    CONFISCATION_MAX_RATE = declare(
        "CONFISCATION_MAX_RATE", 0.28, kind="temporary_heuristic",
        unit="dimensionless (yearly probability at full notice)",
        source=None, confidence="D",
        why="Yearly confiscation probability once state_notice reaches "
            "1.0 (scaled down below that by _notice_over). Invented "
            "ceiling, not fitted to any attested confiscation rate for a "
            "fortune too large to go on taxing.")
    CONFISCATION_CAPITAL_LOSS = declare(
        "CONFISCATION_CAPITAL_LOSS", 0.25, kind="temporary_heuristic",
        unit="dimensionless (fraction of capital seized)", source=None,
        confidence="D",
        why="Fraction of capital an outright confiscation takes. Tuned to "
            "be a real, painful loss without being a whole-fortune wipe; "
            "not sourced to any attested confiscation.")

    def _notice_over(self, threshold):
        """0..1: how far past `threshold` state_notice() stands, as a share
        of the remaining distance to full notice - the same shape
        hazard_relief's own diminishing counters and prominence_hazard's
        `settles_at` use for "starts at nothing right at the line and closes
        in on its ceiling", not a cliff the year the line is crossed.
        """
        notice = self.state_notice()
        if notice <= threshold:
            return 0.0
        return min(1.0, (notice - threshold) / (1.0 - threshold))

    def requisition_report(self):
        """(share of this year's revenue, [why it is smaller than listed])
        the state takes as goods at its own price rather than the market's -
        Rome's annona and munera, Han's salt and iron monopolies, English
        purveyance, Norse dues at the thing, Mexica tribute (see each civil-
        isation file's own `state_pressure.requisition_note`). Bargainable:
        protection is exactly the patronage and standing a household already
        spends on everything else in this file, and it works here too,
        because a well-connected man negotiates his assessment down; it does
        not buy exemption, because the state's claim on your surplus does not
        go away, only its price.
        """
        if self.state_notice() <= self.STATE_NOTICE_THRESHOLD:
            return 0.0, []
        state_pressure_cfg = self.civ.get("state_pressure") or {}
        base = float(state_pressure_cfg.get("requisition_base_share",
                                             self.REQUISITION_BASE_SHARE_DEFAULT))
        share = base * self._notice_over(self.STATE_NOTICE_THRESHOLD)
        why = []
        if self.household.protection > 0:
            share *= (1.0 - self.REQUISITION_PROTECTION_DISCOUNT * self.household.protection)
            why.append("bargained down by standing and patronage (protection "
                       "%d%%)" % round(self.household.protection * 100))
        return max(0.0, share), why

    REQUISITION_BASE_SHARE_DEFAULT = declare(
        "REQUISITION_BASE_SHARE_DEFAULT", 0.15, kind="temporary_heuristic",
        unit="dimensionless (share of revenue at full notice)",
        source=None, confidence="D",
        why="Fallback requisition share for a civilisation file that does "
            "not set its own requisition_base_share - most civ files do "
            "set one (Rome's annona and munera, Han's monopolies, and so "
            "on), so this only matters for a file that omits it. Invented "
            "figure, not fitted to any attested requisition rate.")
    REQUISITION_PROTECTION_DISCOUNT = declare(
        "REQUISITION_PROTECTION_DISCOUNT", 0.55, kind="temporary_heuristic",
        unit="dimensionless (fraction discounted at protection=1.0)",
        source=None, confidence="D",
        why="How much a fully-protected household bargains its "
            "requisition assessment down - a well-connected man negotiates "
            "his assessment down but does not buy exemption outright (see "
            "this method's own docstring). Tuned so protection is a real, "
            "substantial discount without erasing the state's claim; not "
            "measured.")

    def office_report(self):
        """(share of this year's revenue, office's name in this civilisation)
        a pressed civic office costs every year it runs - Rome's decurionate,
        a Han commandery post, the English shrievalty, standing watch for a
        Norse leidang muster, a Mexica cuauhpilli commission. UNLIKE
        requisition, protection does not discount this: the whole point of
        this pressure, as against the patron nodes a household chooses to
        build, is that it is not bought off cheaply. What it gives back
        instead is protection itself - see update_protection()'s own use of
        this same gate - the historical pattern that the very rich were
        pressed into service that cost them money and also shielded them.
        """
        if self.state_notice() <= self.STATE_NOTICE_THRESHOLD:
            return 0.0, None
        state_pressure_cfg = self.civ.get("state_pressure") or {}
        base = float(state_pressure_cfg.get("office_base_share",
                                             self.OFFICE_BASE_SHARE_DEFAULT))
        share = base * self._notice_over(self.STATE_NOTICE_THRESHOLD)
        return max(0.0, share), state_pressure_cfg.get("office_name", "a civic office")

    OFFICE_BASE_SHARE_DEFAULT = declare(
        "OFFICE_BASE_SHARE_DEFAULT", 0.05, kind="temporary_heuristic",
        unit="dimensionless (share of revenue at full notice)",
        source=None, confidence="D",
        why="Fallback pressed-office cost for a civilisation file that "
            "does not set its own office_base_share. Invented figure, "
            "smaller than REQUISITION_BASE_SHARE_DEFAULT because an office "
            "also buys back protection (see this method's own docstring); "
            "not fitted to any attested decurionate or shrievalty cost.")

    def military_demand_eligible(self):
        """Is this household both militarily useful and visible enough that
        a state which can fight would bother asking it for supply?

        military_leverage() alone is not enough - it is earned the moment a
        node is done, on paper, and a state does not write to a household it
        has never heard of - so this also requires state_notice() past its
        own (lower) military line. Reusing military_leverage() rather than a
        hand-picked list of gunpowder-branch ids is deliberate: that count
        already is this engine's one answer to "how much of the military
        tree has this founder actually got", read by update_protection() and
        hazard_relief("output_factor") for two other questions already: a
        third reader does not get to define "militarily significant" its own
        way.
        """
        return (self.military_leverage() >= self.MIL_LEVERAGE_FLOOR_FOR_DEMAND
                and self.state_notice() > self.STATE_NOTICE_THRESHOLD_MILITARY)

    def confiscation_risk(self):
        """(yearly probability, [what is holding it off]) of the tail risk at
        the top of the state-notice scale - distinct from the eminence-driven
        confiscation core.py's step() already rolls (that one is the court's
        jealousy of a great man, unbribable by design, see prominence_hazard's
        own docstring); this one is the treasury deciding a fortune it can no
        longer tax is a fortune worth simply taking, and it answers to the
        four things that actually mitigated that historically: a patron high
        enough to matter and general standing (protection, which already
        blends both), dispersal of the household's own holdings (academy_
        network or endowment_land - "too dispersed to seize at a stroke", the
        same reading sack_chance's HAZARD_COUNTERS already give academy_
        network), and being useful to the state (military_leverage() again -
        a state does not strip clean the one workshop that arms it).
        """
        over = self._notice_over(self.STATE_NOTICE_THRESHOLD_CONFISCATION)
        if over <= 0.0:
            return 0.0, []
        probability = self.CONFISCATION_MAX_RATE * over
        mitig, why = 1.0, []
        if self.household.protection > 0:
            mitig *= (1.0 - self.CONFISCATION_PROTECTION_DISCOUNT * self.household.protection)
            why.append("a patron and standing high enough to matter")
        dispersal = 0.0
        if self.has("academy_network"):
            dispersal = max(dispersal, self.CONFISCATION_DISPERSAL_ACADEMY_NETWORK)
        elif self.has("endowment_land"):
            dispersal = max(dispersal, self.CONFISCATION_DISPERSAL_ENDOWMENT_LAND)
        if dispersal > 0:
            mitig *= (1.0 - dispersal)
            why.append("holdings too dispersed to be seized at a stroke")
        lev = self.military_leverage()
        if lev > 0:
            mitig *= (1.0 - self.CONFISCATION_MILITARY_USEFULNESS_DISCOUNT * lev)
            why.append("too useful to the state to strip clean")
        return probability * mitig, why

    CONFISCATION_PROTECTION_DISCOUNT = declare(
        "CONFISCATION_PROTECTION_DISCOUNT", 0.5, kind="temporary_heuristic",
        unit="dimensionless (fraction discounted at protection=1.0)",
        source=None, confidence="D",
        why="How much a fully-protected household's confiscation risk is "
            "cut by a patron and general standing. Tuned to be a real, "
            "partial mitigation rather than a full defence - this is the "
            "treasury's own claim, not a courtroom accusation protection "
            "otherwise defends against - not measured.")
    CONFISCATION_DISPERSAL_ACADEMY_NETWORK = declare(
        "CONFISCATION_DISPERSAL_ACADEMY_NETWORK", 0.35, kind="temporary_heuristic",
        unit="dimensionless (fraction of confiscation risk removed)",
        source=None, confidence="D",
        why="How much a dispersed academy network mitigates confiscation "
            "risk - 'too dispersed to seize at a stroke', the same reading "
            "HAZARD_COUNTERS already gives academy_network against "
            "sack_chance. Tuned to be the stronger of the two dispersal "
            "hedges; not measured.")
    CONFISCATION_DISPERSAL_ENDOWMENT_LAND = declare(
        "CONFISCATION_DISPERSAL_ENDOWMENT_LAND", 0.20, kind="temporary_heuristic",
        unit="dimensionless (fraction of confiscation risk removed)",
        source=None, confidence="D",
        why="How much an endowment of land mitigates confiscation risk - "
            "weaker than CONFISCATION_DISPERSAL_ACADEMY_NETWORK because "
            "land is still one seizable holding rather than a network "
            "spread across multiple places. Tuned, not measured.")
    CONFISCATION_MILITARY_USEFULNESS_DISCOUNT = declare(
        "CONFISCATION_MILITARY_USEFULNESS_DISCOUNT", 0.4, kind="temporary_heuristic",
        unit="dimensionless (fraction discounted at military_leverage=1.0)",
        source=None, confidence="D",
        why="How much being militarily useful to the state mitigates "
            "confiscation risk - a state does not strip clean the one "
            "workshop that arms it (see this method's own docstring). "
            "Tuned, not measured.")

    def state_pressure_report(self):
        """What `risk`/`state` shows BEFORE any of this bites - the same
        obligation eminence_report() already meets for prominence, answering
        the brief's own fairness standard: a confiscation with no warning is
        the same unfairness as the silent staffing cliff an earlier round
        fixed. Deliberately terse - `state full` has a hard readability
        budget this engine already enforces (see test_regressions.py's own
        "state full stays readable") - so a dormant household (the common
        case for most of a run under the measured trajectories) gets a bare
        null and nothing else, and only what is actually live gets a field
        of its own.
        """
        notice = self.state_notice()
        req_share, _req_why = self.requisition_report()
        off_share, off_name = self.office_report()
        conf_p, conf_why = self.confiscation_risk()
        state_pressure_cfg = self.civ.get("state_pressure") or {}
        # NULL, NOT A SENTENCE, WHEN DORMANT. `state full` has a measured
        # 9,000-byte readability budget (test_regressions.py's own "state
        # full stays readable") that the densest civilisation files already
        # sit close to; most of a run has nothing live to report here (see
        # this mechanic's own commit message for how late these thresholds
        # are actually crossed), so the common case costs almost nothing
        # rather than one more always-present sentence.
        if req_share <= 0.0005 and off_share <= 0.0005 and conf_p <= 0.0 \
                and not self.military_demand_eligible():
            return None
        out = {"now": round(notice, 3), "noticed_above": self.STATE_NOTICE_THRESHOLD,
               "confiscation_risk_above": self.STATE_NOTICE_THRESHOLD_CONFISCATION}
        if req_share > 0.0005:
            out["requisition"] = ("%s takes about %d%% of this year's revenue"
                                  % (state_pressure_cfg.get("requisition_name", "the state"),
                                     round(req_share * 100)))
        if off_share > 0.0005 and off_name:
            out["office"] = ("%s costs about %d%% of revenue a year, and "
                             "buys protection in return" % (off_name, round(off_share * 100)))
        if self.military_demand_eligible():
            # THE ONE CROSSING TO sim/world/military_logistics.py. See
            # military_equipment_burden_kg_per_soldier_per_year()'s own
            # docstring for what this number is, why leverage alone drives
            # it, and why supply RANGE and campaign FEASIBILITY - the other
            # two candidates that module supports - are not wired in here.
            # Kilograms only, never converted to money: see that docstring's
            # WHY NOT MONEY. This changes only the TEXT of an already-
            # existing, already-gated notice, not the MILITARY_DEMAND_*
            # share/probability arithmetic below, which is unchanged.
            burden_kg = self.military_equipment_burden_kg_per_soldier_per_year()
            out["military_supply"] = ("%s may demand your output; refusing a "
                                      "state that can still fight is not free "
                                      "(equipping one soldier your way costs "
                                      "it about %.1f kg of iron and "
                                      "ammunition a year)"
                                      % (state_pressure_cfg.get("military_name", "the arsenal"),
                                         burden_kg))
        if conf_p > 0:
            out["confiscation_chance_this_year"] = round(conf_p, 4)
            out["confiscation_reduced_by"] = conf_why
        out["what_helps"] = ("a patron or standing; holdings not all in one "
                             "place; being useful to a state that fights")
        return out

    MILITARY_DEMAND_BASE_SHARE = declare(
        "MILITARY_DEMAND_BASE_SHARE", 0.10, kind="temporary_heuristic",
        unit="dimensionless (share of revenue)", source=None,
        confidence="D",
        why="Base share of revenue a military supply demand takes, before "
            "scaling with how militarily useful the household is. Invented "
            "figure, not fitted to any attested requisition-in-kind rate.")
    MILITARY_DEMAND_LEVERAGE_SHARE = declare(
        "MILITARY_DEMAND_LEVERAGE_SHARE", 0.10, kind="temporary_heuristic",
        unit="dimensionless (share of revenue at military_leverage=1.0)",
        source=None, confidence="D",
        why="Extra share of revenue a military demand takes for a household "
            "at full military leverage - a state asks more of a workshop "
            "that can supply more. Tuned, not measured.")
    MILITARY_DEMAND_PROTECTION_DISCOUNT = declare(
        "MILITARY_DEMAND_PROTECTION_DISCOUNT", 0.4, kind="temporary_heuristic",
        unit="dimensionless (fraction discounted at protection=1.0)",
        source=None, confidence="D",
        why="How much a fully-protected household's military demand is "
            "discounted - a patron's standing softens even a demand that "
            "is not otherwise bargainable. Tuned, not measured.")
    CONFISCATION_REPUTATION_LOSS = declare(
        "CONFISCATION_REPUTATION_LOSS", 6, kind="temporary_heuristic",
        unit="reputation points", source=None, confidence="D",
        why="Reputation lost when the treasury confiscates a fortune - "
            "being stripped of wealth by the state is itself a public "
            "humiliation. Tuned to be a real, noticeable hit alongside "
            "STANDING_* figures elsewhere in this engine; not measured.")

    def _state_pressure(self, yr):
        """Once a year: the state notices what this household has become,
        and acts on it. See the section comment above `household_scale` for
        the full argument; this is only the yearly application of the four
        reports above.
        """
        notice = self.state_notice()
        rev = max(0.0, self.revenue())
        state_pressure_cfg = self.civ.get("state_pressure") or {}

        req_share, req_why = self.requisition_report()
        off_share, off_name = self.office_report()
        took = (req_share + off_share) * rev
        if took > 0.5:
            self.household.capital -= took
            last = self.household._said_requisition
            if yr - last >= 15:
                self.household._said_requisition = yr
                bits = ["%s takes %s this year" % (
                    state_pressure_cfg.get("requisition_name", "the state"),
                    "{:,.0f}".format(req_share * rev))]
                if req_why:
                    bits.append("; ".join(req_why))
                if off_share > 0.0005 and off_name:
                    bits.append("%s costs %s more, and is not something you "
                                "get to decline cheaply"
                                % (off_name, "{:,.0f}".format(off_share * rev)))
                self.household.log.append((yr, "THE STATE HAS NOTICED YOU: " + "; ".join(bits)))
        elif notice > self.STATE_NOTICE_THRESHOLD * 0.7:
            # APPROACHING, NOT YET BITING. The same fairness standard as
            # eminence's own "YOU ARE BECOMING CONSPICUOUS" warning in
            # core.py's step(): a player should see this coming before the
            # first denarius is actually taken, not discover it in the
            # ledger after the fact.
            band = int(notice / max(0.01, self.STATE_NOTICE_THRESHOLD * 0.1))
            if band > self.household._said_notice_approach:
                self.household._said_notice_approach = band
                self.household.log.append((yr, "this household is becoming large enough "
                                     "for the state to take an interest: "
                                     "notice %.2f against a line of %.2f. A "
                                     "patron or standing, and holdings that "
                                     "are not all in one place, are what "
                                     "blunt it when it arrives"
                                     % (notice, self.STATE_NOTICE_THRESHOLD)))

        if self.events and self.military_demand_eligible():
            last = self.household.last_military_demand
            if (yr - last >= self.MILITARY_DEMAND_COOLDOWN_YEARS
                    and self.rng.random() < self.MILITARY_DEMAND_ANNUAL_CHANCE):
                self.household.last_military_demand = yr
                lev = self.military_leverage()
                take = (rev * (self.MILITARY_DEMAND_BASE_SHARE
                               + self.MILITARY_DEMAND_LEVERAGE_SHARE * lev)
                        * (1.0 - self.MILITARY_DEMAND_PROTECTION_DISCOUNT * self.household.protection))
                take = max(0.0, take)
                self.household.capital -= take
                name = state_pressure_cfg.get("military_name", "the arsenal")
                self.household.log.append((yr, "%s asks for your output: %s handed over "
                                     "in powder, iron or finished pieces. "
                                     "Refusing a state that can still fight "
                                     "is not free, and this was the cheaper "
                                     "choice"
                                 % (name, "{:,.0f}".format(take))))

        probability, conf_why = self.confiscation_risk()
        if probability > 0.0:
            band = int(probability / 0.05)
            last_band = self.household._said_confiscation_band
            if band > last_band:
                self.household._said_confiscation_band = band
                self.household.log.append((yr, "THE TREASURY IS LOOKING AT YOUR FORTUNE: "
                                     "a %d%% chance this year of outright "
                                     "confiscation, against a scale that "
                                     "only keeps climbing while this "
                                     "household grows. %s"
                                 % (round(probability * 100),
                                    ("Held off by: " + "; ".join(conf_why))
                                    if conf_why else
                                    "Nothing you have built is holding it "
                                    "off yet")))
            if self.events and self.rng.random() < probability:
                had = max(0.0, self.household.capital)
                self.lose_capital(self.CONFISCATION_CAPITAL_LOSS)
                lost = had - max(0.0, self.household.capital)
                self.household.reputation = max(0.0, self.household.reputation - self.CONFISCATION_REPUTATION_LOSS)
                name = state_pressure_cfg.get("confiscation_name", "confiscation")
                self.household.log.append((yr, "%s: the state takes what it judges a "
                                     "fortune too large to go on merely "
                                     "taxing - %s gone"
                                 % (name, "{:,.0f}".format(lost)
                                    if lost > 0.5 else "nothing, because you "
                                    "were holding none")))
        else:
            self.household._said_confiscation_band = -1
