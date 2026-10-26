"""The founder's life: growing old, dying, and the programme dissolving when no deputies carry the work on (the rules are
founder_rules.py). A run ends for a seat alone; the others keep playing."""
from typing import Any, Dict, Optional

from sim.knowledge.api import ForgetTechnique
from sim.reporting.api import RecordEvent

from . import founder_rules
from .commands import EndRun, SetFounderLife


class Founder:

    def founder(self) -> Dict[str, Any]:
        """The acting seat's founder: {alive, life_left, dead_reason (None while the seat plays), policy (the standing
        policy object, still kept on the seat's founder record; None for a country seat)}."""
        held = self.needs.legacy_seats()[self.clock.acting_seat].founder
        return {"alive": self.seat.founder_alive, "life_left": self.seat.life_left, "dead_reason": self.seat.dead_reason,
                "policy": None if held is None else held.policy}

    def dead_reasons(self) -> Dict[str, str]:
        """Why each ended seat's run ended, by seat id, in joining order."""
        return {seat_id: self.seat_of(seat_id).dead_reason for seat_id in self.ended_seats()}

    def set_founder_life(self, command: SetFounderLife) -> None:
        self.seat.founder_alive = True
        self.seat.life_left = command.years

    def end_run(self, command: EndRun) -> None:
        self.seat.dead_reason = command.reason
        if command.announce and command.reason:
            self.needs.send(RecordEvent.of("run_ends", founder_rules.run_ends_line(command.reason)))

    def founder_mortality(self, seat_id: Optional[str] = None) -> None:
        """Once a year for the acting seat: the founder grows a year older and may die, and a programme left with no
        director dissolves, forgetting what it built, until the run ends."""
        terms = self.needs.dissolution_terms()
        seat = self.seat
        if seat.founder_alive:
            seat.life_left = founder_rules.years_left(
                seat.life_left, bool(self.needs.running_mechanics("founder_life_extension")), terms["life_extension_years"])
            if founder_rules.has_died(seat.life_left):
                seat.founder_alive = False
                patronage = self.needs.patronage()
                self.needs.send(RecordEvent.of(
                    "founder_dies", founder_rules.death_line(patronage["founder_age"], self._consequence(patronage)),
                    aged=patronage["founder_age"], deputies_carry_the_work=bool(patronage["deputies_carry_the_work"])))
        patronage = self.needs.patronage()
        projects = self.needs.legacy_projects()
        if founder_rules.dissolves(seat.founder_alive, patronage["deputies_carry_the_work"]):
            projects.stalled += 1
            if founder_rules.forgets_this_year(projects.stalled, terms["years_before_forgetting"]):
                losable = self.needs.losable_node_ids(True)
                # sorted() in the view matters: the held set iterates in an order that depends on PYTHONHASHSEED, and
                # a sample of it would give the same seed a different answer on every invocation
                if losable:
                    for node_id in self.needs.legacy_dice().sample(losable, founder_rules.forgotten_count(
                            len(losable), terms["forget_fraction_divisor"])):
                        projects.operating.discard(node_id)
                        self.needs.send(ForgetTechnique((node_id,)))
            if founder_rules.warns(projects.stalled):
                self.needs.send(RecordEvent.of(
                    "programme_dissolving", founder_rules.dissolving_line(projects.stalled, self._hours_sentence(patronage)),
                    years_since_death=projects.stalled, run_ends_after_years=terms["years_until_end"]))
            if founder_rules.run_ends(projects.stalled, terms["years_until_end"]):
                self.end_run(EndRun(founder_rules.dissolution_end(self._survivors())))
        else:
            projects.stalled = 0

    def _hours_sentence(self, patronage: Dict[str, Any]) -> str:
        return founder_rules.deputy_hours_sentence(patronage["deputies"], patronage["deputy_hours"])

    def _consequence(self, patronage: Dict[str, Any]) -> str:
        return founder_rules.deputy_consequence(bool(patronage["deputies_carry_the_work"]), patronage["deputies"],
                                                patronage["deputy_hours"])

    def _survivors(self) -> str:
        held = self.needs.techniques_held()
        any_dispersed = any(self.needs.corpus_dispersed(node_id) for node_id in held)
        return founder_rules.what_survived(any_dispersed, len(held - self.needs.techniques_granted()))
