"""What the player can see, and what their work is at risk of losing.

These are methods of Sim; they are a mixin only so that they can live in
a file of their own.
"""
import re
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .actors import Household
from .data import closure, JSONDict, Nodes
from .hazard_window import hazards_not_yet_past

# THE GAME TELLING YOU WHAT IS IMPORTANT IS THE GAME PLAYING ITSELF. A
# node's own note must not grade itself against the rest of the tree:
# school_founded's calling itself "the pivot of the entire game" and
# saying "every year of delay here costs more than any single
# technology", or corpus_dispersed's calling itself "THE highest
# expected-value node in the tree", are exactly the kind of sentence this
# strips. Under fog, which branch matters most is exactly the decision fog exists to
# leave to the player; a sentence that grades a node against the rest of the
# tree answers that question for them as plainly as a number would, fog or no
# fog, because it is the designer's own ranking, not something the founder in
# the story could know. It is cut everywhere a node's note is shown, not only
# under fog, because telling a player outright which of their own choices is
# correct is the same move whether or not the rest of the tree is hidden.
#
# NARROW ON PURPOSE, same lesson as FOREIGN_MARKERS and NEVER_ABANDON below.
# A sentence only qualifies if it BOTH names the game or the tree itself AND
# makes a ranking claim about it ("highest", "pivot", "largest single", ...),
# or matches one of the handful of exact phrases below that rank a node
# without naming "game"/"tree" in so many words ("costs more than any single
# technology", "must not cut"). A sentence that calls something "the most
# important instrument" a pilot has, or Cayley's discovery "his single most
# important insight", is a true statement about the real world and survives -
# it never mentions the game or the tree at all. Only a sentence that steps
# outside the fiction to grade the tree's own node against the rest of the
# tree is self-play, and only those are dropped. Deliberately NOT touched:
# "Nothing in the technical tree requires it. You may decline..." on
# school_founded's own note - stating that a thing is optional is the
# opposite of the fault this exists to fix, and "the whole game" on
# point_contact_transistor's note ("Getting here from 100 AD is the whole
# game") is left alone too, because the goal's own identity is already known
# under fog by design - see help's "what you are trying to do".
_SELF_PLAY_PHRASES = (
    "pivot of the entire game",
    "costs more than any single",
    "highest expected-value node in the tree",
    "highest expected-value defensive investment",
    "highest-leverage thing you can spend money on",
    "is simply the highest-leverage",
    "largest single call on your personal hours",
    "must not cut",
    # AND TELLING YOU WHAT TO DO FIRST, which is the same offence in the
    # imperative rather than the comparative and so slips past both the
    # phrase list and the meta-plus-ranking test above. Under fog, what to
    # build first IS the question being asked of the player. There are
    # only two such sentences in the whole tree, so they are named rather
    # than pattern matched, because a broad rule for imperatives would eat
    # the recipe instructions that are the point of the note field.
    "do this before writing any other recipe down",
    "build it first, use it to learn",
)
_SELF_PLAY_META = re.compile(
    r"\b(the game|this game|the entire game|the tree|this tree)\b", re.I)
_SELF_PLAY_RANK = re.compile(
    r"\bhighest\b|\blargest\b|\bpivot\b|\bmost important\b|\bsingle most\b", re.I)


def strip_self_play_advice(text: Optional[str]) -> Optional[str]:
    """Drop any sentence that ranks a node against the game or the tree,
    and hand back what is left. See the block comment above for why, and
    for exactly what does and does not qualify.
    """
    if not text:
        return text
    parts = re.split(r'(?<=[.!?]) ', text)

    def _is_self_play(sentence: str) -> bool:
        low = sentence.lower()
        if any(phrase in low for phrase in _SELF_PLAY_PHRASES):
            return True
        return bool(_SELF_PLAY_META.search(sentence) and _SELF_PLAY_RANK.search(sentence))

    return " ".join(sentence for sentence in parts if not _is_self_play(sentence)).strip()


class FogMixin:
    # FOG IS A RATCHET, NOT A REWIND (see playtest/AUDIT_rounds_1_6.md, C1):
    # `load` restores the game but must not restore the player's memory
    # with it, or a save-build-look-load cycle lets a player see what
    # `available` reveals at no cost, refunding every denarius and year
    # that discovery cost, for free, as many times as they like. The
    # dishonest half is not that reload fails to un-teach a human who
    # already read a name - no save format can do that - it is reload
    # handing back the cost of having learned it.
    #
    # THE RATCHET LIVES ON `Household`, not here: `revealed` is this
    # household's own accumulated knowledge of the tree, which is exactly
    # the shape of state HOUSEHOLD_EXTRACTION.md moved onto its own
    # object, and a property is how the ratchet holds regardless of WHICH
    # code assigns to it - assigning a smaller set only ever grows what is
    # already known, never shrinks it. See sim/engine/actors/household.py
    # for the property itself. Every call site below reads and writes
    # `self.household.revealed` directly, for the same reason every other
    # moved field's engine-internal call sites do
    # (HOUSEHOLD_EXTRACTION.md section 2): this is the hot path, not the
    # outside surface.

    # -- ATTRIBUTES AND METHODS THIS MIXIN READS BUT DOES NOT DEFINE -------
    # Set/defined by Sim.__init__ and by sibling mixins (core.py,
    # projects_starting.py, society_hazards.py, projects_capability.py - not
    # owned by this task, see the top-level instructions' file list).
    # Declared here, type-only: a bare annotation binds nothing at runtime
    # (it only populates FogMixin.__annotations__), and a Callable-typed one
    # is exactly the same - neither creates a real attribute or method on
    # this class, so nothing here can shadow the real implementation another
    # mixin actually provides, the way a `def start_reason(self): ...` stub
    # placed directly in this class body would risk doing through Sim's own
    # MRO. See geography.py's identical pattern (and its own comment) for
    # the non-callable half of this.
    household: Household
    nodes: Nodes
    civ: JSONDict
    year: int
    goal: str
    _goal_closure: Set[str]
    start_reason: Callable[..., Tuple[bool, Optional[str]]]
    corpus_hedge: Callable[[], Tuple[float, float, Optional[str]]]
    hazard_advice: Callable[[str], Dict[str, Any]]
    hazard_relief: Callable[[str], Tuple[float, List[str]]]
    hazard_timeline: Callable[..., List[Dict[str, Any]]]
    capability_gaps: Callable[[], List[Dict[str, Any]]]

    def reveal_from(self, node_id: str) -> None:
        """Completing something teaches you what it leads towards, vaguely."""
        if not getattr(self, "fog", False):
            return
        self.household.revealed = set(getattr(self.household, "revealed", set()))
        self.household.revealed.add(node_id)
        for other, node in self.nodes.items():
            if node_id in node.get("pre", []):
                self.household.revealed.add(other)
            for group in node.get("req_any", []):
                if node_id in (group.get("options") or {}):
                    self.household.revealed.add(other)

    def is_visible(self, node_id: str, _memo: Optional[Dict[str, bool]] = None) -> bool:
        """Can the player see this node at all?

        _memo: an optional dict shared across one recursive descent. is_visible
        calls start_reason, and start_reason calls is_visible on every missing
        prerequisite of a node with missing prerequisites - which, on a node
        deep in the tree, is every one of ITS missing prerequisites too. Without
        sharing one memo down that whole call tree, checking visibility of a
        single deep node re-derived the visibility of common ancestors once per
        path to them, which is exponential in the depth of the tree. A profiler
        on `can_start('dynamo')` on norse_900ad under fog counted 12,465 nested
        calls to start_reason from three top-level ones, at 0.45s each; a plain
        `available` call, which checks all ~2,800 nodes this way, did not return
        in 60 seconds. The memo makes one recursive descent O(nodes touched)
        instead of O(paths to them); a fresh dict per outward-facing call (the
        default) keeps it exact - nothing here is cached ACROSS commands, so a
        node built or revealed between one call and the next is seen correctly
        next time.
        """
        if not getattr(self, "fog", False):
            return True
        if node_id in self.household.done or node_id in self.household.active:
            return True
        if node_id in getattr(self.household, "revealed", set()):
            return True
        memo = {} if _memo is None else _memo
        if node_id in memo:
            return memo[node_id]
        memo[node_id] = False        # provisional: the tree is a DAG so this should
                                # never actually be read back, but a cycle must
                                # not recurse forever if one ever sneaks in.
        # anything you could start right now is visible by definition: you can
        # see the work in front of you even if you cannot see past it
        #
        # _why=False: this discards start_reason's message too - is_visible
        # only ever wants the boolean - and it is what turns the recursive
        # descent (this function calls start_reason, which calls
        # missing_prereq_message, which calls is_visible on every missing
        # prerequisite, which calls back into start_reason...) from building
        # a player-facing sentence at every single level into building one
        # only at the outermost call that actually asked for it.
        result = self.start_reason(node_id, _memo=memo, _why=False)[0]
        memo[node_id] = result
        return result

    def missing_prereq_message(self, missing: List[str],
                               _memo: Optional[Dict[str, bool]] = None) -> Optional[str]:
        """Format a list of not-yet-done prerequisite ids as one player-facing
        message, filtered through the same visibility test `start_reason`
        (and so `why`) applies. A second caller computing its own missing
        list and printing the ids raw is exactly how `bounty` leaked
        industrial zinc's power_grid, the getter's induction-coupling
        prerequisite and the vacuum tube's hidden cathode: the filter lived
        in start_reason alone, and nothing stopped a second command from
        skipping it. There must be exactly one way to turn "missing" into
        words.
        """
        if not missing:
            return None
        known = [prereq_id for prereq_id in missing if self.is_visible(prereq_id, _memo=_memo)]
        hidden = len(missing) - len(known)
        if not getattr(self, "fog", False) or not hidden:
            msg = "missing prerequisites: " + ", ".join(missing)
            return msg + self._free_prereq_hint(missing)
        bits = []
        if known:
            bits.append("missing prerequisites: " + ", ".join(known))
        bits.append("%d other thing%s you have not heard of yet"
                    % (hidden, "" if hidden == 1 else "s"))
        msg = "; and ".join(bits) if known else \
            ("this needs %s, and you do not yet know what %s"
             % (bits[-1], "they are" if hidden > 1 else "it is"))
        # ONLY EVER THE VISIBLE ONES. `known` is already the fog filter this
        # whole method exists to apply, so the hint is built from it and a
        # hidden prerequisite is never named by the hint either.
        return msg + self._free_prereq_hint(known)

    # WHAT IT COSTS TO SAY YES. Eight nodes in this tree - cap_measure_temp,
    # cap_measure_elec, cap_measure_mass_mg, cap_measure_time_s,
    # cap_power_water, cap_power_steam, cap_power_electric, cap_power_grid -
    # cost nothing, take no hours, take no years and cannot fail. They are the
    # engine's way of saying "you built a thermometer, so now you can measure
    # temperature", and a player still has to start each one by hand.
    #
    # A refusal that names one of these as a missing prerequisite must not
    # say only "missing prerequisites: cap_measure_temp" - a bare name
    # gives no indication that the thing behind it is free and one command
    # away, and reads as pure administrative friction if it does not say
    # so.
    #
    # NOT AUTO-GRANTED, deliberately. Each of these carries 20 a year of
    # upkeep if it is ever OPENED, so completing them on the player's behalf
    # would be spending their money on a decision they were never asked about.
    # They do not need opening to satisfy a prerequisite - start_reason tests
    # `p not in self.household.done`, not operating - so the honest fix is to say what
    # the refusal was already about: this one is free, start it.
    FREE_PREREQ_NAMED_AT_MOST = 3

    def _free_prereq_hint(self, missing: List[str]) -> str:
        """", and X costs nothing..." for whichever missing prerequisites are
        free, instant and startable right now - or "" when none are."""
        ready: List[str] = []
        for node_id in missing:
            node = self.nodes.get(node_id)
            if not node:
                continue
            if ((node.get("_total_cost") or 0) > 1 or (node.get("ph") or 0) > 0
                    or (node.get("yrs") or 0) > 0 or (node.get("risk") or 0) > 0):
                continue
            # ONLY IF THEY CAN ACT ON IT NOW. Naming a free node that is
            # itself blocked is not help, it is a second refusal wearing the
            # first one's clothes.
            if all(prereq_id in self.household.done for prereq_id in node["pre"]):
                ready.append(node_id)
        if not ready:
            return ""
        ready = ready[:self.FREE_PREREQ_NAMED_AT_MOST]
        if len(ready) == 1:
            return (". %s costs nothing, takes no time and cannot fail: "
                    "start %s" % (ready[0], ready[0]))
        return (". %s cost nothing, take no time and cannot fail: start "
                "them now (%s)"
                % (", ".join(ready), ", ".join("start " + node_id for node_id in ready)))

    def fog_scrub(self, text: Optional[str]) -> Optional[str]:
        """Strip node ids the player has not discovered out of a message."""
        if not text or not getattr(self, "fog", False):
            return text
        scrubbed = text
        for node_id in self.nodes:
            if node_id in scrubbed and not self.is_visible(node_id):
                scrubbed = scrubbed.replace(node_id, "something you have not heard of")
        return scrubbed

    def fog_summary(self, node_id: str) -> str:
        """One sentence. Deliberately not the whole note, and never the unlocks."""
        # Stripped before the first sentence is taken, not after: school_
        # founded's note OPENS with "The pivot of the entire game." - the
        # exact sentence fog_summary would otherwise hand back as the whole
        # answer, under fog, for the one command whose entire job is to stay
        # vague. See strip_self_play_advice above.
        note = strip_self_play_advice((self.nodes[node_id].get("note") or "").strip())
        if not note:
            return self.nodes[node_id]["name"]
        for sep in (". ", "? ", "! "):
            if sep in note:
                note = note.split(sep)[0].strip() + "."
                break
        # Hard cap. A "one sentence" summary that runs to 160 characters, times
        # thirty entries in a list, is most of the reply.
        return note if len(note) <= 110 else note[:107].rstrip(" ,;") + "..."

    def knowledge_risk(self) -> Dict[str, Any]:
        """How exposed your finished work is to being forgotten, and to what.

        The technical dependency graph `path` shows is not the whole
        dependency graph: a hazard's mitigation - an academy protecting
        against the Third Century Crisis, say - is a real dependency even
        when nothing in the tree makes it a technical prerequisite of
        anything. Leaving that risk as prose in a knowledge file, visible
        only to the mitigation and not to anything the player sees while
        deciding, is a tool that misleads by omission. So the numbers
        behind the dice are readable here while there is still time to act
        on them.
        """
        # `has`, NOT running(): every other capability in this engine was
        # moved onto running() - a school with nobody paid to keep it open
        # trains nobody - and this one deliberately stays where it is.
        # Books that exist are books that exist, whether or not the
        # institution that produced them is still open. See
        # Sim.corpus_hedge (core.py): the sack itself calls the same
        # method, so this screen cannot quote a hedge the sack does not
        # honour.
        chance, frac, hedge = self.corpus_hedge()
        at_risk = len(self.household.done - self.household.granted)
        # WHAT YOU HAVE ALREADY LOST, and have to build again: without this,
        # the only record of a sacking is a log line a century back, and
        # the only way to discover a loss is one cryptic refusal at a time
        # - "missing prerequisites: <thing you built two hundred years
        # ago>".
        _gone = sorted((node_id for node_id, _year in (getattr(self.household, "forgotten", None) or {}).items()
                        if node_id not in self.household.done),
                       key=lambda k: -(self.household.forgotten[k]))
        upcoming = []
        for hazard, year_start, year_end, in_progress in hazards_not_yet_past(
                self.civ, self.year):
            row = {"name": hazard.get("name", "hazard"),
                   "years": [year_start, year_end],
                   "in_progress": in_progress,
                   "sacks_a_site": bool(hazard.get("sack_chance")),
                   "sack_chance_per_year": hazard.get("sack_chance"),
                   "staff_loss": hazard.get("staff_loss"),
                   "staff_loss_wave_chance_per_year": (0.32 if hazard.get("staff_loss")
                                                        is not None else None),
                   "note": hazard.get("note")}
            # WHAT YOU CAN DO ABOUT IT: every hazard here is fightable, and
            # this has to say so, or a hazard arriving on the year it was
            # forecast reads as weather rather than something the player
            # could have acted on.
            row["what_you_can_do"] = {}
            for kind in ("staff_loss", "sack_chance", "output_factor", "real_erosion"):
                if kind in hazard or (kind == "sack_chance" and hazard.get("sack_chance")):
                    row["what_you_can_do"][kind] = self.hazard_advice(kind)
            if "sack_chance" in hazard:
                row["sack_chance_after_what_you_have_built"] = round(
                    hazard["sack_chance"] * self.hazard_relief("sack_chance")[0], 4)
            if "staff_loss" in hazard:
                row["staff_loss_after_what_you_have_built"] = round(
                    hazard["staff_loss"] * self.hazard_relief("staff_loss")[0], 4)
                remaining = max(year_start, self.year)
                waves = max(1, year_end - remaining + 1)
                per_wave = row["staff_loss_after_what_you_have_built"]
                row["remaining_annual_wave_checks"] = waves
                row["chance_of_at_least_one_staff_loss_wave"] = round(
                    1.0 - (1.0 - 0.32) ** waves, 4)
                row["expected_cumulative_staff_loss"] = round(
                    1.0 - (1.0 - 0.32 * per_wave) ** waves, 4)
            upcoming.append(row)
        # WHAT IS ACTUALLY NEAR, in full, and the rest by name. Every dated
        # hazard now carries a real historical note and England has fifteen of
        # them; sending all of it made one `risk` reply seventeen thousand
        # bytes, which is the wall this whole interface was broken up to stop
        # producing. A player deciding what to do this decade does not need
        # four hundred words on enclosure in 1700.
        _soon = [row for row in upcoming
                 if row.get("in_progress") or (row["years"][0] - self.year) <= 120]
        _later = [row for row in upcoming if row not in _soon]
        # Full hazard records are large (advice plus historical prose). Keep
        # only the four nearest actionable records and reduce every later one
        # to the two fields needed to find it in the chronology.
        _full = _soon[:4]
        _compact = _soon[4:] + _later
        upcoming = _full + [{"name": row["name"], "years": row["years"],
                             "sacks_a_site": row.get("sacks_a_site", False)}
                            for row in _compact]
        # A civilisation with no sack-capable hazards (Norse, among others)
        # must not advertise a loss risk or recommend a hedge for one: risk
        # you cannot face is not risk.
        # A COMPACT CHRONOLOGICAL VIEW, sorted nearest-first, that says the
        # same thing `known_hazards_ahead` says in scattered, per-kind detail
        # but ESCALATES as a date closes in rather than repeating itself -
        # see hazard_timeline's own comment (society.py) for why "hedged_by:
        # nothing yet" sitting unchanged on this screen for a hundred and
        # fifty years was the actual defect, not merely the lack of a list.
        timeline = self.hazard_timeline()
        can_be_sacked = any(entry.get("sacks_a_site") for entry in upcoming)
        if not can_be_sacked:
            return {
                "technologies_at_risk": at_risk,
                "loss_chance_if_a_site_is_sacked": round(chance, 2),
                "fraction_lost_when_it_happens": round(frac, 2),
                "expected_technologies_lost_per_sacking": 0.0,
                "hedged_by": hedge,
                "better_hedge_available": None,
                "note": "no remaining hazard for this civilization sacks a site, "
                        "so nothing here is currently at risk of being forgotten",
                "critical_capabilities_not_operating": self.capability_gaps() or None,
                "known_hazards_ahead": upcoming,
                "timeline": timeline,
            }
        return {
            "technologies_at_risk": at_risk,
            "loss_chance_if_a_site_is_sacked": round(chance, 2),
            "fraction_lost_when_it_happens": round(frac, 2),
            # PER SACKING means the sacking has already happened, so `chance`
            # - which is the probability that a sacking costs you anything
            # at all - must not be applied a second time here, or the
            # expected loss undercounts.
            "expected_technologies_lost_per_sacking": round(at_risk * frac, 1),
            "and_the_chance_a_sacking_costs_you_anything": round(chance, 2),
            # done versus operating, on the ONE screen whose whole job is
            # telling you what protects you. `hedged_by` below only answers
            # the sack hedge (has(), by design - see corpus_hedge); this
            # answers everything else this run has completed but let lapse.
            "critical_capabilities_not_operating": self.capability_gaps() or None,
            **({"you_have_already_lost": len(_gone),
                "and_have_to_build_again": _gone[:10],
                "the_most_recent_went_in": self.household.forgotten[_gone[0]]} if _gone else {}),
            # Under fog, do not name a node the player has not discovered:
            # the hedge named here has to pass the same visibility test
            # `why` uses, or the two commands would contradict each other
            # about whether the player has heard of it.
            "hedged_by": hedge if (not getattr(self, "fog", False)
                                   or self.is_visible(hedge or "")) else "nothing yet",
            "better_hedge_available": (
                None if hedge == "corpus_dispersed" else
                ("corpus_dispersed" if not getattr(self, "fog", False)
                 else "there is said to be a way to guard against this; "
                      "you have not found it yet")),
            "known_hazards_ahead": upcoming,
            "timeline": timeline,
        }

    # Institutions that belong to one named society. Granting them to everyone
    # was the bug; refusing to let anyone else BUILD them would be a worse one,
    # because a founder can perfectly well introduce an aqueduct to Tenochtitlan.
    # This only blocks the free gift.
    # Standing, knowledge and persona are not plant: they carry upkeep
    # because they cost you to maintain, but they must never be let go to
    # save money the way a mill or a mine can. Shedding `identity_cover` -
    # a persona AND a real prerequisite of the goal - for money can
    # permanently softlock a run, because knowledge cannot be repossessed.
    # Everything else can lapse.
    #
    # NARROW ON PURPOSE: this list protects only true knowledge and
    # persona categories, not institutions like patron_local,
    # collegium_licensed, freedman_staff or workshop_first - those must
    # stay sheddable, or a ruined run could never stop bleeding and
    # recover. A patronage can lapse and a workshop can close; what you
    # cannot lose is who you are and what you know.
    #
    # Creditors forcing the founder to forget Newton's laws
    # (sc2_physics_newtons_laws, cat "physics", up 40) is already covered
    # above; abstract science and medicine outside pure mathematics can go
    # the same way: cell theory, DNA, the phase diagram of iron, none of
    # them a building, all of them carrying real upkeep (40 to 400 denarii,
    # from "keeping up scholarly correspondence" rather than rent) and so
    # all of them ELIGIBLE under the up-exceeds-revenue test that gates
    # both shed_loss_makers and enforce_credit_limit's seizure. "theory" and
    # "knowledge" are what the tree itself calls these categories, which is
    # the same evidence "physics" and "mathematics" were added on: you cannot
    # be made to un-know a thing to balance a ledger, whatever it is filed
    # under. NARROW ON PURPOSE, same lesson as FOREIGN_MARKERS below: most
    # knowledge (tex_drop_spindle, "basic textile technique", among it) costs
    # nothing to keep and was never at risk, needing no protection here at
    # all - see the note on that in never_abandon's caller. This list is only
    # for the knowledge that DOES carry upkeep and would otherwise be shed for
    # it.
    NEVER_ABANDON = {"mathematics", "physics", "method", "notation",
                     "algebra", "geometry", "probability", "analysis",
                     "theory", "knowledge"}

    def never_abandon(self, node_id: str) -> bool:
        """Protected: knowledge, and anything the goal actually needs.

        Keying the softlock guard on the GOAL CLOSURE rather than on a list of
        category names is what makes both halves work. You can let a patron go
        and rebuild him later; you cannot have the game quietly delete a step
        you need and then refuse to fund rebuilding it.
        """
        if self.nodes[node_id]["cat"] in self.NEVER_ABANDON:
            return True
        if not hasattr(self, "_goal_closure"):
            try:
                self._goal_closure = closure(self.nodes, self.goal)
            except Exception:
                self._goal_closure = set()
        return node_id in self._goal_closure

    FOREIGN_MARKERS = ("_roman", "_rome", "annona", "insula", "societas",
                       "collegium", "argentarii", "latifundi",
                       # The cursus publicus is the Roman imperial dispatch
                       # relay and the Pharos is one specific Ptolemaic
                       # building at Alexandria. Neither is a generic capability
                       # any society might have, so without a marker of their
                       # own both would be handed free to Han and to the
                       # Norse alike.
                       "cursus", "pharos")

    # A Roman masonry arch is a way of laying stone and anyone can learn it. The
    # annona is the Roman state's grain dole and Roman citizenship is a status
    # only Rome can confer, and neither is a thing you can BUILD in Luoyang.
    # This must stay NARROW: blocking anything with "collegium" in the
    # name, for example, would cut the licensed association out of the
    # tree, and with it school_founded, endowment_land, academy_network and
    # both patronage tiers - the entire institutional ladder - even though
    # every society has partnerships, money-lenders and licensed
    # associations under its own names. What no other society has is Roman
    # citizenship specifically, because only Rome can confer it;
    # `citizenship` itself models a status the courts will hear, which
    # every society has one of under its own name, so even that must not
    # be blocked. The right list here is empty. What remains civ-specific
    # is which institutions you are GRANTED for free, which FOREIGN_MARKERS
    # still handles: the Han are not handed the annona.
    FOREIGN_INSTITUTIONS = ()
