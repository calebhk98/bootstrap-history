"""A country seat (slow: builds a game, because the holder is a government actor the cast seeds): join reads back the
seat's holder, it has no founder or household, a year runs with it, a household seat's reply is unchanged, and a
country seat is handed over by the same path."""
import os
import tempfile

from .harness import *  # noqa: F401,F403
from sim.engine.saveload import load_state, save_state
from sim.ui.proto import command_registry
from sim.ui.proto import dispatch  # noqa: F401  (registers every command)
from sim.ui.proto.seat_address import run_as_seat

game = sim(civ="rome_100ad", capital=1000.0, events=True)
game.end_year = game.cfg["start_year"] + game.cfg["horizon_years"]
handlers = command_registry.handlers()


def send(cmd):
    return run_as_seat(game, cmd, lambda command: handlers[command["cmd"]](game, game.nodes, command, None))


household_reply = send({"cmd": "join", "seat": "merchant"})
check("a household seat's join reply has its own fields and no country-seat ones",
      household_reply["ok"] and household_reply["joined"] == "merchant"
      and not {"kind", "holder", "founder", "household"} & set(household_reply), sorted(household_reply))
merchant_row = next(row for row in household_reply["seats"] if row["seat"] == "merchant")
check("a household seat's row has no kind or holder", "kind" not in merchant_row and "holder" not in merchant_row, merchant_row)

reply = send({"cmd": "join", "seat": "senate", "seat_kind": "country"})
home = game.civ["id"]
check("a country seat joins", reply["ok"] and reply["joined"] == "senate" and reply["kind"] == "country", reply)
check("its holder is the country's government", reply["holder"] == game.actors.government_of(home).actor_id
      and reply["country"] == home, reply)
check("it has no founder and no household", reply["founder"] is None and reply["household"] is None
      and game.state.seats["senate"].founder is None and not game.state.seats["senate"].holds_household, reply)
row = next(row for row in reply["seats"] if row["seat"] == "senate")
check("its row names the kind and holder", row["kind"] == "country" and row["holder"] == reply["holder"] and "capital" not in row, row)
check("it is not among the household seats the year runs, and the game is not over with it",
      "senate" not in game.playing_seats() and "senate" not in game.ended_seats() and not game.run_over(), game.playing_seats())

refused = send({"cmd": "join", "seat": "nowhere", "seat_kind": "country", "country": "atlantis"})
check("a country with no government is refused with its choices", refused["ok"] is False and refused["cause"] == "unknown_country"
      and home in refused["choices"] and "nowhere" not in game.state.seats, refused)
refused = send({"cmd": "join", "seat": "odd", "seat_kind": "island"})
check("an unknown seat kind is refused", refused["cause"] == "unknown_seat_kind" and "odd" not in game.state.seats, refused)
refused = send({"cmd": "join", "seat": "kitted", "seat_kind": "country", "kit": "poor_scholar"})
check("a country seat takes no kit", refused["cause"] == "country_seat_has_no_kit" and "kitted" not in game.state.seats, refused)
refused = send({"cmd": "state", "as": "senate"})
check("a command that needs a household is refused for a country seat", refused["cause"] == "country_seat_has_no_household", refused)

year_before = game.year
reply = send({"cmd": "step", "as": "senate"})
check("a year runs with a country seat in the game, stepped from it", reply["ok"] and game.year == year_before + 1, game.year)
game.step()
check("a second year runs", game.year == year_before + 2, game.year)

# handover goes through the same path: the replacement is an empty country seat
send({"cmd": "join", "seat": "regent", "seat_kind": "country"})
check("a country seat cannot be handed to a household seat",
      send({"cmd": "handover", "to": "merchant", "as": "senate"})["cause"] == "replacement_wrong_kind", None)
reply = send({"cmd": "handover", "to": "regent", "as": "senate"})
check("a country seat is handed over", reply["ok"] and reply["from"] == "senate" and reply["to"] == "regent"
      and "senate" not in game.state.seats and game.state.seats["regent"].kind == "country", reply)
check("the replacement holds the same government", game.state.seats["regent"].holder == game.actors.government_of(home).actor_id, None)
game.step()
check("the year runs after the handover", game.year == year_before + 3, game.year)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "save.json")
    save_state(game, path)
    load_state(game, path)
check("a save keeps the country seat, its kind and holder",
      game.state.seats["regent"].kind == "country" and game.state.seats["regent"].holder is not None
      and game.state.seats["regent"].founder is None, list(game.state.seats))
