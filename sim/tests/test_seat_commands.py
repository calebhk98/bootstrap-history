"""A command is for the seat it names: `as` picks the household, no `as` is the session's seat (the first by
default), an unknown seat is a refusal, and the seats and join commands answer from the game's seats (stand-ins,
no game)."""

QUICK_TOPIC = True

import contextlib

from .harness import check

from sim.engine.state import FounderState, HouseholdState, ProjectsState, SimulationState
from sim.engine.state_seat import FIRST_SEAT_ID, bind_seat, seat_from_template
from sim.ui.proto import command_registry
import sim.ui.proto.dispatch  # noqa: F401  (registers every command)
from sim.ui.proto.dispatch_seats import seat_rows
from sim.ui.proto.seat_address import addressed_seat, run_as_seat, without_seat

# ---- who a command is for
ids = [FIRST_SEAT_ID, "second"]
check("no `as` is the first seat", addressed_seat(ids, {"cmd": "state"}) == (FIRST_SEAT_ID, None), None)
check("no `as` is the session's seat when it has one", addressed_seat(ids, {"cmd": "state"}, "second") == ("second", None), None)
check("`as` beats the session's seat", addressed_seat(ids, {"cmd": "state", "as": FIRST_SEAT_ID}, "second") == (FIRST_SEAT_ID, None), None)
seat, refusal = addressed_seat(ids, {"cmd": "state", "as": "nobody"})
check("an unknown seat is a refusal that lists the seats and changes nothing",
      seat is None and refusal["ok"] is False and "second" in refusal["error"] and "Nothing was changed" in refusal["error"], refusal)
seat, refusal = addressed_seat(ids, {"cmd": "state", "as": 3})
check("a seat id that is not a string is a refusal", seat is None and refusal["ok"] is False, refusal)
check("the addressing key is not an argument of the handler", without_seat({"cmd": "step", "as": "second", "years": 2}) == {"cmd": "step", "years": 2}, None)


# ---- the same command, different households
class Game:
    """The root state with the real alias rebinding, which is all a handler reads."""

    def __init__(self):
        self.state = SimulationState(household=HouseholdState(capital=100.0), projects=ProjectsState(), founder=FounderState())
        self.state.seats["second"] = seat_from_template({}, 50.0, 1e9, {})
        self.session_seat = None
        self.year = 100
        self.civ = {"id": "home"}

    @contextlib.contextmanager
    def act_as(self, seat_id):
        previous = self.state.acting_seat
        bind_seat(self.state, seat_id)
        try:
            yield self
        finally:
            bind_seat(self.state, previous)

    @property
    def capital(self):
        return self.state.household.capital

    def recurring_net(self):
        return 0.0

    def ended_seats(self):
        return [seat_id for seat_id, held in self.state.seats.items() if held.founder.dead_reason]


game = Game()
nodes = {"plan_a": {}}
handlers = command_registry.handlers()


def send(cmd):
    return run_as_seat(game, cmd, lambda command: handlers[command["cmd"]](game, nodes, command, None))


first = game.state.seats[FIRST_SEAT_ID]
second = game.state.seats["second"]
send({"cmd": "saving", "id": "plan_a", "target": 11.0})
check("without `as` the first seat's household changes", first.household.saving_for == "plan_a" and second.household.saving_for is None, None)
send({"cmd": "saving", "id": "plan_a", "target": 22.0, "as": "second"})
check("with `as` the named seat's household changes and the first is as it was",
      second.household.saving_target == 22.0 and first.household.saving_target == 11.0, None)
check("the acting seat is restored after a command for another seat", game.state.acting_seat == FIRST_SEAT_ID and game.state.household is first.household, None)
refused = send({"cmd": "saving", "id": "plan_a", "target": 99.0, "as": "ghost"})
check("a command for an unknown seat changes no household",
      refused["ok"] is False and first.household.saving_target == 11.0 and second.household.saving_target == 22.0, refused)
game.session_seat = "second"
send({"cmd": "saving", "off": True})
check("a session seat takes the commands that name no seat", second.household.saving_for is None and first.household.saving_for == "plan_a", None)

# ---- the seats command
rows = seat_rows(game)
check("the seats list names each seat and shows the addressed seat's purse only",
      [row["seat"] for row in rows] == [FIRST_SEAT_ID, "second"] and "capital" in rows[0] and "capital" not in rows[1], rows)
second.founder.dead_reason = "denounced: as a sorcerer"
check("a seat whose run ended says why", seat_rows(game)[1]["ended"] == "denounced: as a sorcerer" and seat_rows(game)[0]["ended"] is None, None)
reply = handlers["seats"](game, nodes, {"cmd": "seats"}, None)
check("the seats command answers ok with the seats and the year", reply["ok"] and len(reply["seats"]) == 2 and reply["year"] == 100, reply)
check("seats and join are registered commands with help", all(name in command_registry.COMMANDS for name in ("seats", "join")), None)
refused_join = handlers["join"](game, nodes, {"cmd": "join", "seat": "second"}, None)
check("joining under a taken name is refused and changes nothing", refused_join["ok"] is False and len(game.state.seats) == 2, refused_join)
refused_kit = handlers["join"](game, nodes, {"cmd": "join", "seat": "third", "kit": "no_such_kit"}, None)
check("joining with an unknown kit is refused", refused_kit["ok"] is False and "third" not in game.state.seats, refused_kit)
check("joining with no name is refused", handlers["join"](game, nodes, {"cmd": "join"}, None)["ok"] is False, None)
