"""What the player can see, and what their work is at risk of losing.

These are methods of Sim; they are a mixin only so that they can live in
a file of their own.
"""
import re
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from sim.agents.api import Household
from . import category_traits
from .data import closure, JSONDict, Nodes
from . import event_causes
from .hazard_window import hazards_not_yet_past
from .hazard_hedge_timing import add_timing_to_steps

# Removes sentences where a node grades itself against the rest of the tree.
# Matches exact phrases like "pivot", "highest-value", "costs more than any
# single technology", or meta-ranking patterns (mentioning "game"/"tree" + ranking
# words). [temporary_heuristic]
_SELF_PLAY_PHRASES = (
    "pivot of the entire game",
    "costs more than any single",
    "highest expected-value node in the tree",
    "highest expected-value defensive investment",
    "highest-leverage thing you can spend money on",
    "is simply the highest-leverage",
    "largest single call on your personal hours",
    "must not cut",
    # Imperative phrases that say what to build first (same offence as ranking)
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
    # FOG IS A RATCHET: revealed knowledge never shrinks. `revealed` is stored
    # on Household (sim/agents/household.py) as a ratcheting property;
    # assignments only grow what is already known.

    # Type annotations only (no runtime binding); provided by Sim and sibling
    # mixins (core.py, projects_starting.py, society_hazards.py,
    # projects_capability.py). See geography.py for the same pattern.
    household: Household
    state: Any
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
        if not self.state._fog:
            return
        projects = self.state.projects
        projects.revealed.add(node_id)
        for other, node in self.nodes.items():
            if node_id in node.get("pre", []):
                projects.revealed.add(other)
            for group in node.get("req_any", []):
                if node_id in (group.get("options") or {}):
                    projects.revealed.add(other)

    def is_visible(self, node_id: str, _memo: Optional[Dict[str, bool]] = None) -> bool:
        """Can the player see this node at all?

        _memo: an optional dict shared across one recursive descent. is_visible
        calls start_reason, and start_reason calls is_visible on every missing
        prerequisite of a node with missing prerequisites - which, on a node
        deep in the tree, is every one of ITS missing prerequisites too. Without
        sharing one memo down that whole call tree, checking visibility of a
        single deep node re-derived the visibility of common ancestors once per
        path to them, which is exponential in the depth of the tree. A profiler
        on `can_start('dynamo')` on a late civilisation under fog counted 12,465 nested
        calls to start_reason from three top-level ones, at 0.45s each; a plain
        `available` call, which checks all ~2,800 nodes this way, did not return
        in 60 seconds. The memo makes one recursive descent O(nodes touched)
        instead of O(paths to them); a fresh dict per outward-facing call (the
        default) keeps it exact - nothing here is cached ACROSS commands, so a
        node built or revealed between one call and the next is seen correctly
        next time.
        """
        if not self.state._fog:
            return True
        projects = self.state.projects
        if node_id in projects.done or node_id in projects.active:
            return True
        if node_id in getattr(projects, "revealed", set()):
            return True
        memo = {} if _memo is None else _memo
        if node_id in memo:
            return memo[node_id]
        memo[node_id] = False  # provisional guard against cycles in DAG
        # Anything startable now is visible; _why=False avoids building messages
        # at every recursive level, only at the outermost call.
        result = self.start_reason(node_id, _memo=memo, _why=False)[0]
        memo[node_id] = result
        return result

    def prerequisite_label(self, prereq_id: str) -> str:
        """The id with the node's name beside it, so the id is identifiable."""
        name = self.nodes.get(prereq_id, {}).get("name")
        return "%s (%s)" % (prereq_id, name) if name and name != prereq_id else prereq_id

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
        if not self.state._fog or not hidden:
            msg = "missing prerequisites: " + ", ".join(self.prerequisite_label(prereq_id) for prereq_id in missing)
            return msg + self._free_prereq_hint(missing)
        bits = []
        if known:
            bits.append("missing prerequisites: " + ", ".join(self.prerequisite_label(prereq_id) for prereq_id in known))
        hidden_kinds = self._hidden_prerequisite_kinds([prereq_id for prereq_id in missing if prereq_id not in known])
        bits.append("%d other thing%s you have not heard of yet%s"
                    % (hidden, "" if hidden == 1 else "s",
                       " (%s)" % ", ".join(hidden_kinds) if hidden_kinds else ""))
        msg = "; and ".join(bits) if known else \
            ("this needs %s, and you do not yet know what %s"
             % (bits[-1], "they are" if hidden > 1 else "it is"))
        # ONLY EVER THE VISIBLE ONES. `known` is already the fog filter this
        # whole method exists to apply, so the hint is built from it and a
        # hidden prerequisite is never named by the hint either.
        return msg + self._free_prereq_hint(known)

    # Plain words for a node's kind, so a hidden blocker keeps its identity but shows what sort of thing it is.
    FOG_KIND_HINTS = {
        "ENGINEERING": "a technique or device", "SCIENCE": "an idea or body of theory",
        "INSTITUTION": "an institution or social arrangement", "RESOURCE": "a material or its source",
        "INFRASTRUCTURE": "a built facility", "CAPABILITY": "a measurement or power capability",
    }
    # A hidden prerequisite shows its kind only when this share of its own prerequisites is already done.
    FOG_HINT_NEARNESS = 0.5

    def _hidden_prerequisite_kinds(self, hidden_ids: List[str]) -> List[str]:
        """Kind phrases for hidden prerequisites the player has built enough nearby knowledge to place."""
        done = self.state.projects.done
        kinds: List[str] = []
        for node_id in hidden_ids:
            node = self.nodes.get(node_id) or {}
            prereqs = node.get("pre") or []
            near = (sum(1 for prereq_id in prereqs if prereq_id in done) / len(prereqs) >= self.FOG_HINT_NEARNESS
                    if prereqs else True)
            phrase = self.FOG_KIND_HINTS.get(node.get("kind"))
            if near and phrase and phrase not in kinds:
                kinds.append(phrase)
        return kinds

    # Capability nodes (cap_measure_*, cap_power_*) cost nothing, take no time.
    # A refusal naming one must say it is free and startable now, not just the name.
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
            if all(prereq_id in self.state.projects.done for prereq_id in node["pre"]):
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
        if not text or not self.state._fog:
            return text
        scrubbed = text
        # Sort by length descending to replace longer ids first, avoiding
        # corruption when one id is a prefix of another.
        sorted_ids = sorted(self.nodes, key=lambda node_id: -len(node_id))
        for node_id in sorted_ids:
            if not self.is_visible(node_id):
                # Whole ids only; ':' joins a namespaced id, so it is not a boundary either
                pattern = r'(?<![\w:])' + re.escape(node_id) + r'(?![\w:])'
                scrubbed = re.sub(pattern, "something you have not heard of", scrubbed)
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
        # Uses has() not running(): books exist even if institution closed.
        chance, frac, hedge = self.corpus_hedge()
        projects = self.state.projects
        scenario = self.state.scenario
        at_risk = len(set(self.losable_node_ids(keep_dispersed=False)))
        # WHAT YOU HAVE ALREADY LOST, and have to build again: without this,
        # the only record of a sacking is a log line a century back, and
        # the only way to discover a loss is one cryptic refusal at a time
        # - "missing prerequisites: <thing you built two hundred years
        # ago>".
        _gone = sorted((node_id for node_id, _year in (getattr(projects, "forgotten", None) or {}).items()
                        if node_id not in projects.done),
                       key=lambda k: -(projects.forgotten[k]))
        upcoming = []
        for hazard, year_start, year_end, in_progress in hazards_not_yet_past(
                self.civ, scenario.year):
            # the chances shown are the ones the event's stated causes leave, as things stand today
            effective, causes = event_causes.effective_hazard(self, hazard)
            hazard = effective if effective is not None else event_causes.weakened(hazard, 0.0)
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
                    row["what_you_can_do"][kind] = self.hazard_advice(kind, hazard)
            add_timing_to_steps(row["what_you_can_do"], scenario.year, year_start, in_progress)
            if causes["checked"]:
                row["causes_hold_now"] = not causes["failed"]
                row["causes"] = [{key: cause[key] for key in ("quantity", "node", "op", "threshold", "value", "holds", "why")}
                                 for cause in causes["conditions"]]
                if effective is None:
                    row["skipped_while_causes_fail"] = True
            if "sack_chance" in hazard:
                row["sack_chance_after_what_you_have_built"] = round(
                    self.hazard_figure("sack_chance", hazard), 4)
            if "output_factor" in hazard:
                row["output_factor"] = hazard["output_factor"]
                row["output_factor_after_what_you_have_built"] = round(
                    self.hazard_figure("output_factor", hazard), 4)
            if "staff_loss" in hazard:
                exposure = self.staff_loss_exposure(hazard["staff_loss"])
                row["staff_loss_before_what_you_have_built"] = round(exposure["before_defences"], 4)
                row["staff_loss_after_what_you_have_built"] = round(exposure["loss"], 4)
                if exposure["national_relief"] > 0.02:
                    row["national_public_health"] = {
                        "share_removed": round(exposure["national_relief"], 4),
                        "from": self.national_public_health_sources()}
                remaining = max(year_start, scenario.year)
                waves = max(1, year_end - remaining + 1)
                per_wave = row["staff_loss_after_what_you_have_built"]
                row["remaining_annual_wave_checks"] = waves
                row["chance_of_at_least_one_staff_loss_wave"] = round(
                    1.0 - (1.0 - 0.32) ** waves, 4)
                row["expected_cumulative_staff_loss"] = round(
                    1.0 - (1.0 - 0.32 * per_wave) ** waves, 4)
            upcoming.append(row)
        # Show full records for next 4 actionable hazards, rest by name only (avoid bloat).
        _soon = [row for row in upcoming
                 if row.get("in_progress") or (row["years"][0] - scenario.year) <= 120]
        _later = [row for row in upcoming if row not in _soon]
        # Full hazard records are large (advice plus historical prose). Keep
        # only the four nearest actionable records and reduce every later one
        # to the two fields needed to find it in the chronology.
        _full = _soon[:4]
        _compact = _soon[4:] + _later
        upcoming = _full + [{"name": row["name"], "years": row["years"],
                             "sacks_a_site": row.get("sacks_a_site", False)}
                            for row in _compact]
        # Civs with no sack hazards: no loss risk to report. Get chronological timeline.
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
                "the_most_recent_went_in": projects.forgotten[_gone[0]]} if _gone else {}),
            # Under fog, do not name a node the player has not discovered:
            # the hedge named here has to pass the same visibility test
            # `why` uses, or the two commands would contradict each other
            # about whether the player has heard of it.
            "hedged_by": hedge if (not self.state._fog
                                   or self.is_visible(hedge or "")) else "nothing yet",
            "better_hedge_available": (
                None if hedge == self.best_corpus_node() else
                (self.best_corpus_node() if not self.state._fog
                 else "there is said to be a way to guard against this; "
                      "you have not found it yet")),
            "known_hazards_ahead": upcoming,
            "timeline": timeline,
        }

    # Categories flagged never_abandoned (data/world/category_traits.json)
    # protect knowledge that carries upkeep and cannot be lost without
    # softlocking the run. Institutions (patron_local, collegium_licensed,
    # etc.) are not flagged: they can and must lapse.

    def never_abandon(self, node_id: str) -> bool:
        """Protected: knowledge, and anything the goal actually needs.

        Keying the softlock guard on the GOAL CLOSURE rather than on a list of
        category names is what makes both halves work. You can let a patron go
        and rebuild him later; you cannot have the game quietly delete a step
        you need and then refuse to fund rebuilding it.
        """
        if category_traits.has_trait(self.nodes[node_id]["cat"], "never_abandoned"):
            return True
        if self.relied_on_running(node_id):
            return False
        return self.on_road_to_goal(node_id)

    def on_road_to_goal(self, node_id: str) -> bool:
        """Whether the goal needs this node. A yes/no with no distance, so it
        names no route the player has not already been shown."""
        if not hasattr(self, "_goal_closure"):
            try:
                self._goal_closure = closure(self.nodes, self.state._goal)
            except Exception:
                self._goal_closure = set()
        return node_id in self._goal_closure

