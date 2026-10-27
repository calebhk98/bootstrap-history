"""The year steps every seat: world phases once, seat phases for each seat, one seat's end leaves the others playing."""

QUICK_TOPIC = True

import contextlib
import types

from unittest import mock

from .harness import check

from sim.hazards.merge import mildest_hazard
from sim.seats.api import SeatsSeat, run_is_over, seat_ended, seats_playing
from sim.engine.state import FounderState, HouseholdState, ProjectsState, SimulationState
from sim.engine.state_seat import FIRST_SEAT_ID, seat_from_template
from sim.engine import year_steps
from sim.engine.year_run import run_year

# ---- the hazard the world meets is the mildest any seat's works leave
plague = {"name": "plague", "staff_loss": 0.4, "output_factor": 0.7, "real_erosion": 0.2, "values": {"w_x": 0.1}}
spared_war = {"name": "plague", "staff_loss": 0.2, "output_factor": 0.9, "real_erosion": 0.1, "values": {"w_x": 0.1}}
merged = mildest_hazard([plague, spared_war])
check("the world takes the lowest staff loss and erosion and the highest output floor",
      (merged["staff_loss"], merged["real_erosion"], merged["output_factor"]) == (0.2, 0.1, 0.9), merged)
check("a seat averting a world effect averts it for the society",
      "output_factor" not in mildest_hazard([plague, {k: v for k, v in plague.items() if k != "output_factor"}]), None)
check("a seat the hazard does not reach leaves no world hazard", mildest_hazard([plague, None]) is None, None)
check("one seat's hazard is the world's", mildest_hazard([plague]) == plague, None)
check("merging does not change a seat's own hazard", plague["staff_loss"] == 0.4 and spared_war["staff_loss"] == 0.2, None)

# ---- a seat from data
template = {"starting_techs": ["a", "b"], "scholars": 2, "artisans": 3, "base_tile": "t1", "goal": "g", "country": "han"}
seat = seat_from_template(template, 500.0, {"auto_hire": False})
check("a template builds a seat with its own purse, knowledge, staff, place and goal",
      seat.household.capital == 500.0 and seat.projects.done == {"a", "b"} and seat.projects.granted == {"a", "b"}
      and seat.modules["workforce"].scholars == 2 and seat.modules["workforce"].artisans == 3 and seat.household.base_tile == "t1"
      and seat.goal == "g" and seat.country == "han", None)
other = seat_from_template(template, 500.0, {})
check("two seats from one template share no container",
      other.projects.done is not seat.projects.done and other.modules["workforce"].employees is not seat.modules["workforce"].employees
      and other.founder.policy is not seat.founder.policy, None)

# ---- the end rule: one seat's run ends, the others play on
state = SimulationState(household=HouseholdState(capital=1.0), projects=ProjectsState(), founder=FounderState())
state.seats["second"] = seat_from_template({}, 5.0, {})
for held in state.seats.values():
    held.modules["seats"] = SeatsSeat()
check("two seats are both playing at the start", seats_playing(state.seats) == [FIRST_SEAT_ID, "second"], None)
state.seats[FIRST_SEAT_ID].modules["seats"].dead_reason = "denounced: as a sorcerer"
check("a seat whose founder fell has ended", seat_ended(state.seats[FIRST_SEAT_ID]) and not seat_ended(state.seats["second"]), None)
check("the other seat keeps playing and the run goes on",
      seats_playing(state.seats) == ["second"] and not run_is_over(state.seats), seats_playing(state.seats))
state.seats["second"].modules["seats"].goal_year = 150
check("the run is over when every seat has ended or reached its goal", run_is_over(state.seats), None)
state.seats["second"].modules["seats"].goal_year = None
state.seats["second"].modules["seats"].dead_reason = "ran out of money"
check("the run is over when no seat is left", run_is_over(state.seats) and seats_playing(state.seats) == [], None)


# ---- the year's order, on a recording stand-in for the Sim
class Scenario:
    year = 100


class Alias:
    def __init__(self, ended):
        self.acting_seat = FIRST_SEAT_ID
        self.scenario = Scenario()
        self.ended = set(ended)


class FakeSim:
    """Records each phase call with the seat acting when it ran; shocks may end seats."""

    debug = False
    events = True

    def __init__(self, seat_ids, ends_in_shocks=()):
        self.state = Alias(())
        self.seat_ids = list(seat_ids)
        self.ends_in_shocks = set(ends_in_shocks)
        self.calls = []

    def playing_seats(self):
        return [seat_id for seat_id in self.seat_ids if seat_id not in self.state.ended]

    def ended_seats(self):
        return sorted(self.state.ended)

    @contextlib.contextmanager
    def act_as(self, seat_id):
        previous = self.state.acting_seat
        self.state.acting_seat = seat_id
        try:
            yield self
        finally:
            self.state.acting_seat = previous

    def _record(self, name, *arguments):
        self.calls.append((name, self.state.acting_seat))

    @property
    def assembly(self):
        """The assembly's phase lookup: a module's phase `name` records as `step_<name>`; the year's dated shocks may end seats."""
        def phase(name):
            def run(*arguments):
                self._record("step_" + name)
                if name == "dated_shocks":
                    self.state.ended |= self.ends_in_shocks
            return run
        return types.SimpleNamespace(phase_handler=phase, applied=types.SimpleNamespace(phases=[]))

    def __getattr__(self, name):
        return lambda *arguments: self._record(name, *arguments)


_ROOT_STEPS = {"begin_world_year": "begin_world_year", "money_seat": "_step_money_seat", "money_world": "_step_money_world",
               "seat_work": "_run_seat_work"}


def run_recorded(sim):
    """run_year with the root's own steps (year_steps) recording as calls of the stand-in, under the names the checks use."""
    patches = [mock.patch.object(year_steps, function, lambda target, recorded=recorded: target._record(recorded))
               for function, recorded in _ROOT_STEPS.items()]
    for patch in patches:
        patch.start()
    try:
        run_year(sim)
    finally:
        for patch in patches:
            patch.stop()


def names(sim, phase):
    return [seat for call, seat in sim.calls if call == phase]


two = FakeSim([FIRST_SEAT_ID, "second"])
run_recorded(two)
check("each seat phase runs once for each seat, in joining order",
      names(two, "_step_money_seat") == [FIRST_SEAT_ID, "second"] and names(two, "_run_seat_work") == [FIRST_SEAT_ID, "second"]
      and names(two, "step_credit_limit") == [FIRST_SEAT_ID, "second"], two.calls)
check("each world phase runs once", all(len(names(two, phase)) == 1 for phase in
      ("_step_money_world", "step_dated_shocks", "step_market", "step_wild_stock", "begin_world_year")), two.calls)
check("the market closes after every seat's work and before the credit check",
      [call for call, _ in two.calls].index("step_market") > max(i for i, (call, _) in enumerate(two.calls) if call == "_run_seat_work")
      and [call for call, _ in two.calls].index("step_market") < [call for call, _ in two.calls].index("step_credit_limit"), None)
check("the year advances once", two.state.scenario.year == 101, two.state.scenario.year)

ended = FakeSim([FIRST_SEAT_ID, "second"], ends_in_shocks=[FIRST_SEAT_ID])
run_recorded(ended)
check("a seat ended by the year's shocks takes no further part in it, the other carries on",
      names(ended, "_step_money_seat") == [FIRST_SEAT_ID, "second"] and names(ended, "_run_seat_work") == ["second"]
      and names(ended, "step_living_stock") == ["second"] and names(ended, "step_credit_limit") == ["second"], ended.calls)
check("world phases after the shocks run as a seat still playing", names(ended, "step_market") == ["second"], ended.calls)
check("the year still advances", ended.state.scenario.year == 101, None)

alone = FakeSim([FIRST_SEAT_ID, "second"], ends_in_shocks=[FIRST_SEAT_ID, "second"])
run_recorded(alone)
check("when every seat ends in the shocks the year stops there, as a one-seat game does",
      names(alone, "_run_seat_work") == [] and names(alone, "step_market") == [] and alone.state.scenario.year == 100, alone.calls)

dead_before = FakeSim([FIRST_SEAT_ID, "second"])
dead_before.state.ended.add(FIRST_SEAT_ID)
run_recorded(dead_before)
check("a seat that ended earlier is not stepped again",
      names(dead_before, "_step_money_seat") == ["second"] and names(dead_before, "step_apprenticeships") == ["second"], dead_before.calls)

single = FakeSim([FIRST_SEAT_ID])
run_recorded(single)
check("one seat runs the phases in the order a one-seat year always had",
      [call for call, _ in single.calls if call in (
          "step_apprenticeships", "step_staff", "_step_money_seat", "_step_money_world", "step_win_conditions",
          "step_dated_shocks", "_run_seat_work", "step_market", "step_living_stock", "step_defence_stores", "step_random_events",
          "step_credit_limit")] == [
          "step_apprenticeships", "step_staff", "_step_money_seat", "_step_money_world", "step_win_conditions",
          "step_dated_shocks", "_run_seat_work", "step_market", "step_living_stock", "step_defence_stores", "step_random_events",
          "step_credit_limit"], single.calls)
