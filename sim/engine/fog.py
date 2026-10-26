"""What the player can see, and what their work is at risk of losing.

These are methods of Sim; they are a mixin only so that they can live in
a file of their own.
"""
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from sim.agents.api import Household
from .data import closure, JSONDict, Nodes
from . import event_causes
from sim.hazards.api import add_timing_to_steps, hazards_not_yet_past
from .staff_loss_waves import wave_exposure


class FogMixin:
    # FOG IS A RATCHET: revealed knowledge never shrinks. `revealed` is stored
    # on Household (sim/agents/household.py) as a ratcheting property;
    # assignments only grow what is already known.

    # Type annotations only (no runtime binding); provided by Sim and sibling
    # mixins (core.py, forward_projects.py, society_hazards.py,
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

    def _epidemic_risk(self) -> Dict[str, Any]:
        """What the disease model forecasts for the coming year (infections now, contact between tiles, and the
        chance each pathogen reaches the nation): the risk of epidemics read from the model, not from a dated list."""
        forecast = self.epidemic_forecast()
        return {key: value for key, value in forecast.items() if key != "expected_deaths_by_tile"}

    def knowledge_risk(self, advice: bool = True, chronology: bool = True) -> Dict[str, Any]:
        """How exposed your finished work is to being forgotten, and to what.

        The technical dependency graph `path` shows is not the whole
        dependency graph: a hazard's mitigation - an academy protecting
        against the Third Century Crisis, say - is a real dependency even
        when nothing in the tree makes it a technical prerequisite of
        anything. Leaving that risk as prose in a knowledge file, visible
        only to the mitigation and not to anything the player sees while
        deciding, is a tool that misleads by omission. So the numbers
        behind the dice are readable here while there is still time to act
        on them. `advice=False` leaves out each hazard's `what_you_can_do`
        and `chronology=False` the timeline (both costly) for callers that only read the other fields.
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
        forgotten = self.forgotten
        _gone = sorted((node_id for node_id, _year in (forgotten or {}).items()
                        if node_id not in projects.done),
                       key=lambda k: -(forgotten[k]))
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
                   "staff_loss_wave_chance_per_year": (self.STAFF_LOSS_HAZARD_ANNUAL_CHANCE if hazard.get("staff_loss")
                                                        is not None else None),
                   "note": hazard.get("note")}
            # WHAT YOU CAN DO ABOUT IT: every hazard here is fightable, and
            # this has to say so, or a hazard arriving on the year it was
            # forecast reads as weather rather than something the player
            # could have acted on.
            if advice:
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
                row.update(wave_exposure(self.STAFF_LOSS_HAZARD_ANNUAL_CHANCE,
                                         row["staff_loss_after_what_you_have_built"],
                                         year_start, year_end, scenario.year))
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
        timeline = self.hazard_timeline() if chronology else None
        can_be_sacked = any(entry.get("sacks_a_site") for entry in upcoming)
        if not can_be_sacked:
            return {
                "epidemic_forecast": self._epidemic_risk(),
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
            "epidemic_forecast": self._epidemic_risk(),
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
                "the_most_recent_went_in": forgotten[_gone[0]]} if _gone else {}),
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

    def on_road_to_goal(self, node_id: str) -> bool:
        """Whether the goal needs this node. A yes/no with no distance, so it
        names no route the player has not already been shown."""
        if not hasattr(self, "_goal_closure"):
            try:
                self._goal_closure = closure(self.nodes, self.state._goal)
            except Exception:
                self._goal_closure = set()
        return node_id in self._goal_closure

