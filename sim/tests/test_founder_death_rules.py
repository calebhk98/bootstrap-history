"""The founder's death: the yearly mortality step (`StepPhasesMixin._step_founder_mortality`) logs it with the age and whether the
deputies carry the work, counts the programme's dissolution in the years after, and the step stops on the line; the state reads the
age from what the step saved, else from the log (`_founder_death_info`). The mixin runs on a stand-in game carrying only what it
reads. The ending after a dispersed corpus and the forgetting are in test_founder_death_and_victory_ending."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.engine.core_step_phases import StepPhasesMixin
from sim.refusal import LogLine, cause_of, facts_of
from sim.ui.proto import event_kinds
from sim.ui.proto.state_waiting import _founder_death_info

UNTIL_END = 12
BEFORE_FORGETTING = 3


class Game(StepPhasesMixin):
    """The parts of a Sim that the mortality step reads and writes."""
    DISSOLUTION_YEARS_UNTIL_END = UNTIL_END
    DISSOLUTION_YEARS_BEFORE_FORGETTING = BEFORE_FORGETTING
    DISSOLUTION_FORGET_FRACTION_DIVISOR = 4
    SANITATION_LIFE_EXTENSION_YEARS = 2

    def __init__(self, alive=True, life_left=5, stalled=0, deputies=False, year=100):
        self.state = SimpleNamespace(
            founder=SimpleNamespace(founder_alive=alive, life_left=life_left),
            projects=SimpleNamespace(stalled=stalled, operating=set(), done=set()),
            household=SimpleNamespace(log=[]), scenario=SimpleNamespace(year=year))
        self.deputies = deputies
        self.catastrophes = []
        self.extended = False

    def running_with_mechanic(self, name):
        return self.extended

    def founder_age(self):
        return 61

    def deputies_carry_the_work(self):
        return self.deputies

    def _deputy_consequence(self):
        return "consequence"

    def _deputy_hours_sentence(self):
        return "hours sentence"

    def losable_node_ids(self):
        return []

    def _catastrophe(self, reason):
        self.catastrophes.append(reason)

    def _what_survived_the_dissolution(self):
        return "survived"


def after_step(game):
    game._step_founder_mortality()
    return game


def logged(game):
    return [line for _year, line in game.state.household.log]


game = after_step(Game(life_left=1))
lines = logged(game)
check("a founder whose last year is spent dies", game.state.founder.founder_alive is False)
check("the death is a founder_dies line with the age and whether deputies carry the work",
      [cause_of(line) for line in lines] == ["founder_dies"] and facts_of(lines[0]) == {"aged": 61, "deputies_carry_the_work": False}, lines)
living = after_step(Game(life_left=5))
check("a founder with years left lives on and logs nothing",
      living.state.founder.founder_alive and living.state.founder.life_left == 4 and not logged(living))
extended = Game(life_left=1)
extended.extended = True
after_step(extended)
check("a mechanic that extends the founder's life adds its years and so spares the last year",
      extended.state.founder.founder_alive and extended.state.founder.life_left == 2)
check("a death with deputies carrying the work does not start the dissolution",
      after_step(Game(life_left=1, deputies=True)).state.projects.stalled == 0)
check("a death with no deputies starts the dissolution count at one", after_step(Game(life_left=1)).state.projects.stalled == 1)

for stalled_before, expected_shown in ((1, False), (2, True), (5, True), (8, True), (10, True), (3, False), (6, False)):
    dissolving = after_step(Game(alive=False, stalled=stalled_before))
    shown = [line for line in logged(dissolving) if cause_of(line) == "programme_dissolving"]
    check("the dissolution is announced when %d years have passed: %s" % (stalled_before + 1, expected_shown),
          bool(shown) == expected_shown and (not shown or facts_of(shown[0]) == {
              "years_since_death": stalled_before + 1, "run_ends_after_years": UNTIL_END}), (stalled_before, shown))
check("the programme is ended when the dissolution has run its years",
      len(after_step(Game(alive=False, stalled=UNTIL_END - 1)).catastrophes) == 1)
check("before then it is not ended", len(after_step(Game(alive=False, stalled=UNTIL_END - 2)).catastrophes) == 0)
check("a living founder resets the count", after_step(Game(life_left=5, stalled=4)).state.projects.stalled == 0)

check("a founder_dies line stops a multi-year step", event_kinds.stops_a_step(LogLine("founder_dies", "dead", aged=61)) is True)
check("a dissolution notice does not stop a step", event_kinds.stops_a_step(LogLine("programme_dissolving", "fading")) is False)


def reader(alive, saved_age=None, saved_year=None, log=()):
    return SimpleNamespace(founder_alive=alive, _founder_death_aged=saved_age, _founder_death_year=saved_year, log=list(log))


check("a living founder has no death to report", _founder_death_info(reader(True)) is None)
check("the age and year the step saved are read first",
      _founder_death_info(reader(False, 58, 130, [(131, LogLine("founder_dies", "dead", aged=99))])) == {"year": 130, "aged_about": 58})
scanned = reader(False, log=[(120, LogLine("hazard_hit", "plague")), (131, LogLine("founder_dies", "dead", aged=77))])
check("with nothing saved the log's founder_dies line gives the age and year",
      _founder_death_info(scanned) == {"year": 131, "aged_about": 77})
check("a dead founder with no line and nothing saved has no age to report", _founder_death_info(reader(False)) is None)
