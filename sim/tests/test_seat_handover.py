"""A seat can be handed to a replacement: the known nodes, holdings, goal, country and notes pass to it and the old
seat leaves the year. The pure move is called on built seat records; the protocol command is read by its fields."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import relations
from sim.engine.seat_move import move_seat_fields
from sim.engine.state_seat import seat_from_template
from sim.refusal import cause_of
from sim.seats.api import SeatsSeat, handover_refusal
import sim.ui.proto.dispatch  # noqa: F401  (registers every command)
from sim.ui.proto import command_registry
from sim.ui.proto.notes_store import add_note, all_notes, hand_over_notes
from sim.ui.proto.seat_address import run_as_seat

from sim.resources.state import ResourcesSeat

from .seat_handover_fixture import Game


def give(seat, techs, country, goal):
    seat.projects.done |= set(techs)
    seat.projects.granted |= set(techs)
    seat.modules["resources"] = ResourcesSeat(mines=[{"material": "iron_ore"}])
    seat.modules.setdefault("seats", SeatsSeat())
    seat.modules["seats"].patents["loom"] = {"owner": "x"}
    seat.modules["seats"].shares_held["guild"] = 3.0
    seat.country, seat.goal = country, goal


# ---- the pure move on built seat records
seats = {"leaver": seat_from_template({"scholars": 2.0}, 40.0, {}), "heir": seat_from_template({}, 7.0, {})}
give(seats["leaver"], ["fire", "wheel"], "han", "steam_engine")
before = seats["leaver"]
heir_founder = seats["heir"].founder
check("an unknown seat is refused with its cause and the choices", cause_of(handover_refusal(seats, "leaver", "ghost", [])) == "unknown_seat"
      and handover_refusal(seats, "leaver", "ghost", []).choices == ["leaver", "heir"], None)
check("a seat handed to itself is refused", cause_of(handover_refusal(seats, "heir", "heir", [])) == "same_seat", None)
check("a good handover has no refusal", handover_refusal(seats, "leaver", "heir", []) is None, None)
moved = move_seat_fields(seats, "leaver", "heir")
heir = seats["heir"]
check("the replacement knows the same nodes", heir.projects.done == {"fire", "wheel"} and heir.projects.granted == {"fire", "wheel"}, heir.projects)
check("the replacement holds the same workings, patents and shares",
      heir.holdings is before.holdings and heir.modules["resources"].mines == [{"material": "iron_ore"}]
      and "loom" in heir.modules["seats"].patents and heir.modules["seats"].shares_held == {"guild": 3.0}, heir.holdings)
check("the household, goal and country pass on", heir.household is before.household and heir.modules["workforce"].scholars == 2.0
      and heir.goal == "steam_engine" and heir.country == "han", None)
check("the replacement keeps its own founder", heir.founder is heir_founder, None)
check("the old seat is gone from the year", list(seats) == ["heir"] and moved["from"] == "leaver" and moved["known_nodes"] == 2, moved)

# ---- notes and country records survive
game = Game(["leaver", "heir"])
leaver = game.state.seats["leaver"]
give(leaver, ["fire"], "han", None)
add_note(game, "build the bloomery first")
game._switch_seat("heir")
add_note(game, "the heir's own note")
game._switch_seat("leaver")
relations.set_side(game.stores, "han", "rome", note="never trust their envoys", stance="wary")
check("a seat reads only its own notes", [row["text"] for row in all_notes(game)] == ["build the bloomery first"], None)
check("the notes pass to the replacement", hand_over_notes(game, "leaver", "heir") == 1, None)
game._switch_seat("heir")
check("the replacement reads both its own and the inherited notes",
      [row["text"] for row in all_notes(game)] == ["build the bloomery first", "the heir's own note"], all_notes(game))
game._switch_seat("leaver")
check("the leaver no longer has the notes", all_notes(game) == [], None)
# not text: a stored relation note round-trips between seats
check("the country's relation note stays with the country the replacement now plays for",
      relations.read(game.stores, "han", "rome")["note"] == "never trust their envoys", None)

# ---- the protocol command
handlers = command_registry.handlers()


def send(game_, cmd):
    return run_as_seat(game_, cmd, lambda command: handlers[command["cmd"]](game_, {}, command, None))


game = Game(["leaver", "heir", "third"])
give(game.state.seats["leaver"], ["fire", "wheel"], "han", "steam_engine")
send(game, {"cmd": "note", "text": "keep the forge fed"})
check("handover is a registered command", "handover" in command_registry.COMMANDS, None)
refused = send(game, {"cmd": "handover", "to": "ghost"})
check("an unknown replacement is refused with a cause and changes nothing",
      refused["ok"] is False and refused["cause"] == "unknown_seat" and "heir" in refused["choices"] and len(game.state.seats) == 3, refused)
refused = send(game, {"cmd": "handover", "to": "leaver"})
check("a seat handed to itself is refused", refused["ok"] is False and refused["cause"] == "same_seat", refused)
refused = send(game, {"cmd": "handover", "to": "heir", "from": "third"})
check("a seat the caller does not own is refused", refused["ok"] is False and refused["cause"] == "not_your_seat"
      and "third" in game.state.seats, refused)
refused = send(game, {"cmd": "handover"})
check("no replacement named is refused", refused["ok"] is False and refused["cause"] == "no_replacement", refused)
game.state.seats["heir"].modules["resources"] = ResourcesSeat(mines=[{"material": "iron_ore"}])
refused = send(game, {"cmd": "handover", "to": "heir"})
check("a replacement with workings of its own is refused with what it holds and nothing changes",
      refused["ok"] is False and refused["cause"] == "replacement_not_empty" and refused["holds"] == ["holdings"]
      and "leaver" in game.state.seats, refused)
game.state.seats["heir"].modules["resources"].mines.clear()
game.session_seat = "leaver"
reply = send(game, {"cmd": "handover", "to": "heir"})
check("a handover answers with what moved", reply["ok"] is True and reply["from"] == "leaver" and reply["to"] == "heir"
      and reply["known_nodes"] == 2 and reply["notes"] == 1 and reply["country"] == "han", reply)
check("the seats left are the replacement and the other", [row["seat"] for row in reply["seats"]] == ["heir", "third"], reply)
check("the replacement holds the knowledge and the old seat is gone",
      game.state.seats["heir"].projects.done == {"fire", "wheel"} and "leaver" not in game.state.seats, None)
check("the session now plays the replacement and the acting seat is a live seat",
      game.session_seat == "heir" and game.state.acting_seat in game.state.seats, game.state.acting_seat)
