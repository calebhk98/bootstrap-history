"""Complaint 640: a country seat holds a government, not a household. Each rule is called on built inputs: the join command
on a stand-in game, the addressing and refusal rules on built seats, the seat-run rules, the handover rules and the save."""

QUICK_TOPIC = True

import types

from .harness import check

from sim.engine.seat_move import move_seat_fields
from sim.seats.api import SeatsSeat, handover_refusal, run_is_over, seats_playing
from sim.engine.state import SimulationState, deserialize_state, serialize_state
from sim.engine.state_seat import COUNTRY_SEAT, FIRST_SEAT_ID, seat_from_template
from sim.refusal import cause_of
from sim.ui.proto import command_registry
import sim.ui.proto.dispatch  # noqa: F401  (registers every command)
from sim.ui.proto.seat_address import country_seat_refusal, run_as_seat

HOME = "rome_100ad"
GOVERNMENT = "gov_rome"
handlers = command_registry.handlers()


def household_seat():
    seat = seat_from_template({"starting_techs": ["fire"]}, 100.0, {})
    seat.modules["seats"] = SeatsSeat()
    return seat


def country_seat(holder=GOVERNMENT):
    seat = seat_from_template({"kind": COUNTRY_SEAT, "country": None}, 0.0, {})
    seat.modules["seats"] = SeatsSeat()
    seat.holder = holder
    return seat


class JoinGame:
    """What the join command reads: the seats, the countries with a government, and a join_seat that adds the seat."""

    def __init__(self):
        self.state = types.SimpleNamespace(seats={FIRST_SEAT_ID: household_seat()}, acting_seat=FIRST_SEAT_ID)
        self.civ = {"id": HOME}
        self.cfg = {"start_kit": "poor_scholar"}
        self.nodes = {"fire": {}}
        self.joined = []

    def view(self, name):
        assert name == "dead_reasons"
        return lambda: {}

    def society_techs_now(self):
        return {"fire"}

    def governed_countries(self):
        return [HOME, "han_china_100ad"]

    def join_seat(self, seat_id, template):
        seat = country_seat() if template.get("kind") == COUNTRY_SEAT else household_seat()
        self.state.seats[seat_id] = seat
        self.joined.append((seat_id, template))
        return seat


def join(game, **fields):
    return handlers["join"](game, {}, dict({"cmd": "join"}, **fields), None)


# ---- the join command
game = JoinGame()
reply = join(game, seat="merchant")
row = next(row for row in reply["seats"] if row["seat"] == "merchant")
check("a household seat's join reply has its own fields and no country-seat ones",
      reply["ok"] and reply["joined"] == "merchant" and not {"kind", "holder", "founder", "household"} & set(reply), sorted(reply))
check("a household seat's row has no kind or holder", "kind" not in row and "holder" not in row, row)

game = JoinGame()
reply = join(game, seat="senate", seat_kind="country")
row = next(row for row in reply["seats"] if row["seat"] == "senate")
check("a country seat joins, holding the government the engine gave it",
      reply["ok"] and reply["joined"] == "senate" and reply["kind"] == "country" and reply["holder"] == GOVERNMENT
      and reply["country"] == HOME, reply)
check("a country seat's reply has no founder and no household", reply["founder"] is None and reply["household"] is None
      and game.state.seats["senate"].founder is None and not game.state.seats["senate"].holds_household, reply)
check("a country seat's row names the kind and holder and shows no purse", row["kind"] == "country" and row["holder"] == GOVERNMENT
      and "capital" not in row, row)
check("the join asks the engine for a country template", game.joined == [("senate", {"kind": "country", "country": HOME})], game.joined)

game = JoinGame()
refused = join(game, seat="nowhere", seat_kind="country", country="atlantis")
check("a country with no government is refused with its choices and no seat is added",
      refused["ok"] is False and refused["cause"] == "unknown_country" and refused["choices"] == [HOME, "han_china_100ad"]
      and "nowhere" not in game.state.seats, refused)
refused = join(game, seat="odd", seat_kind="island")
check("an unknown seat kind is refused", refused["cause"] == "unknown_seat_kind" and "odd" not in game.state.seats, refused)
refused = join(game, seat="kitted", seat_kind="country", kit="poor_scholar")
check("a country seat takes no kit", refused["cause"] == "country_seat_has_no_kit" and "kitted" not in game.state.seats, refused)

# ---- which commands a country seat may run
seats = {FIRST_SEAT_ID: household_seat(), "senate": country_seat()}
stand_in = types.SimpleNamespace(state=types.SimpleNamespace(seats=seats))
refused = country_seat_refusal(stand_in, "senate", {"cmd": "state"})
check("a command that needs a household is refused for a country seat", refused["cause"] == "country_seat_has_no_household", refused)
check("a command a country seat may run is not refused", country_seat_refusal(stand_in, "senate", {"cmd": "levers"}) is None, None)
check("a household seat is never refused for lacking a household", country_seat_refusal(stand_in, FIRST_SEAT_ID, {"cmd": "state"}) is None, None)

# ---- the year runs for household seats; a country seat steps it through the first of them
class Runner:
    def __init__(self, playing):
        self.state = types.SimpleNamespace(seats=seats)
        self.acted = []
        self.playing = playing

    def playing_seats(self):
        return self.playing

    def act_as(self, seat_id):
        self.acted.append(seat_id)
        import contextlib
        return contextlib.nullcontext()


runner = Runner([FIRST_SEAT_ID])
reply = run_as_seat(runner, {"cmd": "step", "as": "senate"}, lambda command: {"ok": True, "command": command})
check("a step from a country seat runs as the first playing household seat", reply["ok"] and runner.acted == [FIRST_SEAT_ID]
      and reply["command"] == {"cmd": "step"}, (reply, runner.acted))
reply = run_as_seat(Runner([]), {"cmd": "step", "as": "senate"}, lambda command: {"ok": True})
check("with no household seat playing a step is refused with its cause", reply["ok"] is False and reply["cause"] == "no_household_seat", reply)

# ---- the seat-run rules
check("a country seat is not among the playing seats", seats_playing(seats) == [FIRST_SEAT_ID], seats_playing(seats))
check("a country seat alone does not end the run", run_is_over({"senate": country_seat()}) is False, None)
ended = household_seat()
ended.modules["seats"] = SeatsSeat(dead_reason="denounced")
check("a run is over when every household seat ended, whatever a country seat does",
      run_is_over({FIRST_SEAT_ID: ended, "senate": country_seat()}) is True, None)

# ---- handover
check("a country seat cannot be handed to a household seat",
      cause_of(handover_refusal(seats, "senate", FIRST_SEAT_ID, [])) == "replacement_wrong_kind", None)
seats_two = {"senate": country_seat(), "regent": country_seat(holder=None)}
check("a country seat can be handed to an empty country seat", handover_refusal(seats_two, "senate", "regent", []) is None, None)
moved = move_seat_fields(seats_two, "senate", "regent")
check("a country seat is handed over with its kind and holder", moved["from"] == "senate" and moved["to"] == "regent"
      and "senate" not in seats_two and seats_two["regent"].kind == "country" and seats_two["regent"].holder == GOVERNMENT, moved)

# ---- save and load
state = SimulationState(household=household_seat().household, projects=household_seat().projects, founder=household_seat().founder)
state.seats["regent"] = country_seat()
loaded = deserialize_state(serialize_state(state))
check("a save keeps the country seat, its kind and holder",
      loaded.seats["regent"].kind == "country" and loaded.seats["regent"].holder == GOVERNMENT
      and loaded.seats["regent"].founder is None, list(loaded.seats))
