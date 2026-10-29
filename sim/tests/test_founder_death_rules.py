"""The founder's death: the yearly mortality step (the seats module's `founder_mortality`) logs it with the age and whether the
deputies carry the work, counts the programme's dissolution in the years after, and the step stops on the line; the state reads the
age from what the step saved, else from the log (`_founder_death_info`). The module is built with plain values for the views it reads.
The ending after a dispersed corpus and the forgetting are in test_founder_ending_rules."""

QUICK_TOPIC = True

import random
from types import SimpleNamespace

from .harness import check

from sim.refusal import LogLine
from sim.reporting.api import RecordEvent
from sim.seats.api import SeatsSeat
from sim.seats.module import Seats
from sim.ui.proto import event_kinds
from sim.ui.proto.state_waiting import _founder_death_info
from sim.tests import module_harness

UNTIL_END = 12
BEFORE_FORGETTING = 3


from sim.tests.ui_stand_in import Game as StandInGame

class Game:
    """The seats module over the views the mortality step reads, with its sent commands to read back."""

    def __init__(self, alive=True, life_left=5, stalled=0, deputies=False, year=100, extended=False, losable=()):
        self.projects = SimpleNamespace(operating=set())
        self.slot = SeatsSeat(founder_alive=alive, life_left=life_left, stalled=stalled)
        patronage = {"founder_age": 61, "deputies": 0.0, "deputy_hours": 0.0, "deputies_carry_the_work": deputies}
        self.module = module_harness.build(Seats, seat=self.slot, views={
            "dissolution_terms": {"life_extension_years": 2, "years_before_forgetting": BEFORE_FORGETTING,
                                  "forget_fraction_divisor": 4, "years_until_end": UNTIL_END},
            "running_mechanics": lambda name: ["the_mechanic"] if extended else [], "patronage": patronage,
            "losable_node_ids": lambda keep_dispersed: list(losable),
            "game_random": random.Random(1), "techniques_held": set(), "techniques_granted": set(),
            "corpus_dispersed": lambda node_id: False})
        self.state = SimpleNamespace(founder=self.slot, projects=self.projects)


def after_step(game):
    game.module.founder_mortality()
    return game


def logged(game):
    return [command for command in module_harness.sent(game.module) if isinstance(command, RecordEvent)]


game = after_step(Game(life_left=1))
lines = logged(game)
check("a founder whose last year is spent dies", game.slot.founder_alive is False)
check("the death is a founder_dies line with the age and whether deputies carry the work",
      [line.kind for line in lines] == ["founder_dies"] and lines[0].facts == {"aged": 61, "deputies_carry_the_work": False}, lines)
living = after_step(Game(life_left=5))
check("a founder with years left lives on and logs nothing",
      living.slot.founder_alive and living.slot.life_left == 4 and not logged(living))
extended = after_step(Game(life_left=1, extended=True))
check("a mechanic that extends the founder's life adds its years and so spares the last year",
      extended.slot.founder_alive and extended.slot.life_left == 2)
check("a death with deputies carrying the work does not start the dissolution",
      after_step(Game(life_left=1, deputies=True)).slot.stalled == 0)
check("a death with no deputies starts the dissolution count at one", after_step(Game(life_left=1)).slot.stalled == 1)

for stalled_before, expected_shown in ((1, False), (2, True), (5, True), (8, True), (10, True), (3, False), (6, False)):
    dissolving = after_step(Game(alive=False, stalled=stalled_before))
    shown = [line for line in logged(dissolving) if line.kind == "programme_dissolving"]
    check("the dissolution is announced when %d years have passed: %s" % (stalled_before + 1, expected_shown),
          bool(shown) == expected_shown and (not shown or shown[0].facts == {
              "years_since_death": stalled_before + 1, "run_ends_after_years": UNTIL_END}), (stalled_before, shown))
ended = after_step(Game(alive=False, stalled=UNTIL_END - 1))
check("the programme is ended when the dissolution has run its years",
      ended.slot.dead_reason is not None and [line.kind for line in logged(ended)].count("run_ends") == 1)
check("before then it is not ended", after_step(Game(alive=False, stalled=UNTIL_END - 2)).slot.dead_reason is None)
check("a living founder resets the count", after_step(Game(life_left=5, stalled=4)).slot.stalled == 0)

check("a founder_dies line stops a multi-year step", event_kinds.stops_a_step(LogLine("founder_dies", "dead", aged=61)) is True)
check("a dissolution notice does not stop a step", event_kinds.stops_a_step(LogLine("programme_dissolving", "fading")) is False)


def reader(alive, saved_age=None, saved_year=None, log=()):
    return StandInGame(founder_alive=alive, _founder_death_aged=saved_age, _founder_death_year=saved_year, log=list(log))


check("a living founder has no death to report", _founder_death_info(reader(True)) is None)
check("the age and year the step saved are read first",
      _founder_death_info(reader(False, 58, 130, [(131, LogLine("founder_dies", "dead", aged=99))])) == {"year": 130, "aged_about": 58})
scanned = reader(False, log=[(120, LogLine("hazard_hit", "plague")), (131, LogLine("founder_dies", "dead", aged=77))])
check("with nothing saved the log's founder_dies line gives the age and year",
      _founder_death_info(scanned) == {"year": 131, "aged_about": 77})
check("a dead founder with no line and nothing saved has no age to report", _founder_death_info(reader(False)) is None)
