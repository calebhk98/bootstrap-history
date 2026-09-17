"""What a society believes, fears, and does to you for being large.

Split out of simulator.py, which had grown to 5,600 lines. These are
methods of Sim; they are a mixin only so that they can live in a file of
their own. Behaviour is unchanged and verified byte-identical.
"""
import collections, json, math, os, random
from collections import defaultdict

from constants import declare
from .data import *          # the shared tables and loaders
from .data import (TECH_EFFECTS, TRADES_ABSENT, closure, critical_path)


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


class SocietyMixin:
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
            out["military_supply"] = ("%s may demand your output; refusing a "
                                      "state that can still fight is not free"
                                      % state_pressure_cfg.get("military_name", "the arsenal"))
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
    # is deliberately NOT wired into revenue() here: that function belongs to
    # the agent making the goods market competitive at the same time this was
    # written, and two agents independently pricing the same venture is
    # exactly the tangle the brief asked this to avoid. See diffusion_share's
    # own docstring for exactly how a price formula should read it.
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

    def diffusion_share(self, k):
        """0..VENTURE_DIFFUSION_CAP: how much of what running venture `k`
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
        if k not in self.household.operating:
            return 0.0
        node = self.nodes.get(k)
        if not node or node.get("rev", 0) <= 0:
            return 0.0
        started = self.household.opened_year.get(k, self.household.done_year.get(k, self.year))
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
    # A player's complaint, stated plainly after the first round of work on
    # this only fixed what a dated hazard does TO THE FOUNDER (see
    # _resolve_hazard_condition above): "sail to the Americas and bring back
    # New World crops, add crop rotation, and within a few decades ALL of
    # Rome has significantly more food and a larger population. Give the
    # Roman government cannons and it is not being sacked by tribes. Invent
    # the cure or the vaccine for a pandemic and the Black Death becomes a
    # minor period of some sickness rather than a catastrophe." None of
    # that is household risk, which `condition` already answers; it is what
    # the founder's workshop does to the COUNTRY, which was inert before
    # this section existed.
    #
    # civ_diffusion(k) is the missing number, reusing diffusion_share's own
    # shape just above (age since completion, sped up by a written/
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
    # publishing and somebody else literate enough to read it - the user's
    # own fourth point, given a mechanism instead of a name. 25 years (a
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

    def _diffusion_category(self, n):
        traits = n.get("traits") or ()
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

    def civ_diffusion(self, k):
        """0..1: how much of the WHOLE SOCIETY, not this household, has
        adopted technology `k` - the number behind every consequence below.

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
        if k not in self.household.done:
            return 0.0
        node = self.nodes.get(k)
        if not node:
            return 0.0
        cat = self._diffusion_category(node)
        if cat is None:
            return 0.0
        if cat == "military" and not self._state_has_a_patron():
            return 0.0
        age = max(0.0, self.year - self.household.done_year.get(k, self.year))
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

    def _advance_food_diffusion_population(self, yr):
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
        if applied > 0.005 and yr - last >= 25:
            self._food_diffusion_said = yr
            self.household.log.append((yr, "what you grew is no longer only on your "
                             "own land: the crops and rotations you "
                             "introduced have spread far enough into the "
                             "country's own fields that the population is "
                             "running about %d%% above where it would "
                             "otherwise be" % round(applied * 100)))

    # ---- DISEASE: THE COUNTRY IS HARDER TO KILL WHOLESALE ------------------
    # _shocks' staff_loss branch (below) already tells a household-level
    # story (`loss`, reduced by the founder's own sanitation and
    # vaccination) and an empire-wide one (`raw`, the hazard's historical,
    # unmitigated rate - deliberately untouched by the founder's PERSONAL
    # hedges: your quarantine protects your people, not everyone else's
    # labour market). What it could not yet do is the user's own example -
    # "invent the cure or the vaccine for a pandemic and the Black Death
    # becomes a minor period of some sickness rather than a catastrophe" -
    # because nothing let the EMPIRE's own figure fall just because the
    # empire, not only the founder, had absorbed germ theory, quarantine
    # and vaccination by the time the hazard's window opened.
    # medical_diffusion_relief is that missing number, read by _shocks
    # directly against `raw`, never against `loss` (which stays the
    # founder's own, private, has()-gated figure it always was).
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
    # military_leverage() and _military_war_relief() (further below,
    # pre-existing) already answer "does the founder's OWN workshop protect
    # the founder" - has()-gated, private, and wired only into
    # output_factor. The user's cannon example is a different claim: "give
    # the ROMAN GOVERNMENT cannons and it is not being sacked by tribes" -
    # the STATE's own armies, not the founder's private arsenal, and
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

    def _is_foreign_institution(self, k):
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
        value = cache.get(k)
        if value is None:
            hay = (k + " " + self.nodes[k].get("name", "")).lower()
            value = any(marker in hay for marker in self.FOREIGN_MARKERS)
            cache[k] = value
        return value

    def _is_foreign_only(self, k):
        """A legal or civic institution of a society that is not this one."""
        # CACHED FOREVER, for the same reason as _is_foreign_institution just
        # above, and with the same Rome fast path kept outside the cache.
        # start_reason() calls this on every not-yet-done node it is asked
        # about, every year, for as long as that node stays unbuilt.
        if self.civ.get("id") == "rome_100ad":
            return False
        cache = self.__dict__.setdefault("_foreign_only_cache", {})
        value = cache.get(k)
        if value is None:
            hay = (k + " " + self.nodes[k].get("name", "")).lower()
            value = any(marker in hay for marker in self.FOREIGN_INSTITUTIONS)
            cache[k] = value
        return value

    def needs_first(self, k):
        """(node, why) this society must have before it can begin `k` at all.

        cost_multipliers say a domain is DEARER here. Some things are not dear,
        they are impossible: a break tester started horse_collar in the Valley
        of Mexico in 1500, on the same screen as a menu describing a society
        with "no draught animals, no iron, no wheel in practical use", and
        `why` there still described it as a collar for a draught horse.

        Data, like everything else about a civilisation, and always liftable -
        every entry names the node that opens it. See _SCHEMA.md.
        """
        spec = self.civ.get("needs_first") or {}
        for key, ent in spec.items():
            if key.startswith("_") or not isinstance(ent, dict):
                continue
            if k in (ent.get("ids") or ()):
                node = ent.get("node")
                if node and node not in self.household.done:
                    return node, (ent.get("because") or
                                  "this society has no %s" % key)
        return None, None

    def civ_cost_factor(self, k):
        """What this society is unusually good or bad at building.

        Until now every civilization built every node at the same real cost and
        differed only in population, prices, values and reach. That misses the
        most important thing about them. The Mexica are not a small Rome: there
        is no domesticable draught animal anywhere in Mesoamerica, so every load
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
        # it. This was written into every civilization file and then never wired
        # into the code at all: a playtester built collegium_licensed, watched
        # the public-works multiplier sit unchanged at 1.53, and went and read
        # the source to find that `handicap_remedies` is referenced nowhere.
        # They were right. The feature existed only as data and as a claim in a
        # commit message.
        rem = self.civ.get("handicap_remedies") or {}
        node = self.nodes[k]

        def mult(key):
            multiplier = float(mults[key])
            remedy = rem.get(key)
            if isinstance(remedy, dict) and remedy.get("node") in self.household.done:
                multiplier = float(remedy.get("residual", 1.0))
            return multiplier

        # THE CATEGORY IS THE CRAFT; THE TRAITS ARE WHAT IT IS FOR, and treating
        # them as equals inverted the whole system. Every matching key used to be
        # multiplied together, so a longship - category `ships`, which the Norse
        # file scores 0.60, the best in Europe - also carried its `infrastructure`
        # trait at 1.80 and `commerce` at 1.10, and came out at 1.19. Measured
        # across the tree before this fix: all 20 ship nodes, 48 of 50 marine
        # nodes and all 19 navigation nodes cost the Norse MORE than they cost
        # Rome. The one thing that civilisation is famous for was its worst
        # domain, and the file said the opposite.
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
        for hazard in (self.civ.get("hazards") or []):
            yrs = hazard.get("years") or []
            if not yrs:
                continue
            year_start = yrs[0]
            year_end = yrs[1] if len(yrs) > 1 else yrs[0]
            if self.year > year_end:
                continue                      # already survived, or missed
            in_progress = year_start <= self.year <= year_end
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
    PLAGUE_RECOVERY_YEARS_REFERENCE = declare(
        "PLAGUE_RECOVERY_YEARS_REFERENCE", 150.0, kind="hardcoded_historical_outcome",
        unit="years", source="Broadberry et al., British Economic Growth, "
             "2015: England's population took roughly 150 years to regain "
             "its pre-Black-Death level.",
        confidence="B",
        why="Reference recovery time for a hazard of "
            "PLAGUE_RECOVERY_REFERENCE_SEVERITY's own severity - other "
            "hazards' recovery horizons scale off this reference in "
            "proportion to how much of the population they actually took "
            "(see core.py's _demographic_recovery). FLAGGED AS A CLAUDE.md "
            "SS3.1/3.2 RISK, the same shape as economy.py's DEBT_BASE_RATE: "
            "it is a real, attested demographic OUTCOME (how long England "
            "specifically took to recover from one specific plague) used "
            "directly as the model's recovery-speed parameter, rather than "
            "a rate derived from fertility, mortality decline and the "
            "land-labour ratio the way CLAUDE.md SS3.1 asks a recovery "
            "dynamic to be derived. It looks sourced, which is what makes "
            "it dangerous in the same way DEBT_BASE_RATE was: the citation "
            "is genuine, and the number is still the answer, not an input "
            "to a demographic model that does not exist yet.")
    PLAGUE_RECOVERY_REFERENCE_SEVERITY = declare(
        "PLAGUE_RECOVERY_REFERENCE_SEVERITY", 0.45, kind="hardcoded_historical_outcome",
        unit="dimensionless (staff_loss fraction)", source=
        "england_1300.json's own Black Death entry (staff_loss 0.45).",
        confidence="B",
        why="The staff_loss severity PLAGUE_RECOVERY_YEARS_REFERENCE's "
            "150 years is calibrated to specifically - so the Antonine "
            "plague (0.28) gets a shorter, gentler recovery than the "
            "Black Death, not the same 150 years regardless of size. Read "
            "directly off england_1300.json rather than duplicated by "
            "hand, but kept as its own declared number because this file "
            "cannot import that civilisation file's data at class-body "
            "time.")
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
        prep = self.running("plague_preparedness")
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
                # is personal and already reduced by your own hedges; and it
                # compounds onto any deficit still open from an earlier,
                # unfinished recovery rather than overwriting it, because two
                # plagues in one lifetime are worse than either alone.
                # _demographic_recovery() in core.py is what reads this back
                # out into pop_scale and wage_index, and lets it decay.
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
                self.pop_deficit = 1.0 - (1.0 - self.pop_deficit) * (1.0 - raw)
                self._pop_recovery_years = max(
                    self._pop_recovery_years,
                    self.PLAGUE_RECOVERY_YEARS_REFERENCE
                    * (raw / self.PLAGUE_RECOVERY_REFERENCE_SEVERITY))
                # The event has happened NOW.  Do not leave the population
                # and wage screens at their pre-plague values until the next
                # annual resolution; refresh without advancing recovery.
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
                    msg += (". Empire-wide, population -%d%%%s - wages (and "
                            "everything paid in them) stay dear for roughly "
                            "the next %d years either way"
                            % (raw * 100,
                               (" (the country's own public health has "
                                "spread far enough to hold this below the "
                                "%d%% this would otherwise have been - "
                                "%d%% softer)"
                                % (round(historical * 100),
                                   round(med_relief * 100)))
                               if med_relief > 0.02 else "",
                               round(self._pop_recovery_years)))
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
