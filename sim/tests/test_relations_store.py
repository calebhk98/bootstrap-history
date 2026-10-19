"""Complaint 597: a relations store keyed by an ordered pair of countries (stance, treaty terms, a note, a dated
history other mechanisms append to); a seat writes only its own country's side; the record is the country's, so
it outlives the seat (stand-in game, no economy)."""

QUICK_TOPIC = True

import contextlib
import copy
import json

from .harness import check

from sim.engine.mod_stores import StoreBook
from sim.engine.state import FounderState, HouseholdState, ProjectsState, SimulationState
from sim.engine.state_seat import bind_seat, seat_from_template
from sim.ui.proto import command_registry
import sim.ui.proto.dispatch  # noqa: F401  (registers every command)
from sim.ui.proto.seat_address import run_as_seat
from sim.agents.api import relations


class Game:
    """The root state with the real alias rebinding, the stores and the country questions a handler asks."""

    def __init__(self):
        self.state = SimulationState(household=HouseholdState(capital=100.0), projects=ProjectsState(), founder=FounderState())
        self.state.seats["northern"] = seat_from_template({"country": "han"}, 50.0, 1e9, {})
        self.session_seat = None
        self.year = 100
        self.civ = {"id": "rome"}

    @property
    def stores(self):
        return StoreBook(self.state.stores)

    def partner_countries(self):
        return ["han", "parthia"]

    @contextlib.contextmanager
    def act_as(self, seat_id):
        previous = self.state.acting_seat
        bind_seat(self.state, seat_id)
        try:
            yield self
        finally:
            bind_seat(self.state, previous)


game = Game()
handlers = command_registry.handlers()


def send(cmd):
    return run_as_seat(game, cmd, lambda command: handlers[command["cmd"]](game, {}, command, None))


check("relations and set_relation are registered commands", all(name in command_registry.COMMANDS for name in ("relations", "set_relation")), None)

# ---- a pair with nothing recorded reads as the default, and reading writes nothing
blank = send({"cmd": "relations", "with": "han"})
check("an unrecorded pair is neutral with no history and no note",
      blank["ok"] and blank["country"] == "rome" and blank["with"] == "han" and blank["ours"]["stance"] == "neutral"
      and blank["ours"]["history"] == [] and blank["ours"]["note"] == "", blank)
check("reading writes nothing", game.state.stores.get("relations", {}) == {}, game.state.stores)

# ---- a seat sets its own country's side: stance, a treaty term, a note
reply = send({"cmd": "set_relation", "with": "han", "stance": "friendly"})
check("a seat sets its country's stance toward another country", reply["ok"] and reply["ours"]["stance"] == "friendly", reply)
reply = send({"cmd": "set_relation", "with": "han", "term": "grain_for_silk", "value": 3})
check("a treaty term is recorded under its name", reply["ok"] and reply["ours"]["treaty"] == {"grain_for_silk": 3}, reply)
reply = send({"cmd": "set_relation", "with": "han", "note": "their envoy lied about the silk weights"})
check("a note on another power is recorded", reply["ok"] and reply["ours"]["note"].startswith("their envoy"), reply)
check("the record is keyed by the ordered pair of countries", set(game.state.stores["relations"]) == {"rome|han"}, game.state.stores)

# ---- the other country's side stays its own
refused = send({"cmd": "set_relation", "with": "han", "side": "han", "stance": "hostile"})
check("a seat cannot set another country's side",
      refused["ok"] is False and refused["cause"] == "not_your_country" and "rome" in refused["choices"], refused)
refused = send({"cmd": "set_relation", "with": "rome", "stance": "hostile"})
check("a country has no relation with itself", refused["ok"] is False and refused["cause"] == "same_country", refused)
refused = send({"cmd": "set_relation", "with": "atlantis", "stance": "hostile"})
check("an unknown country is refused with the countries that exist",
      refused["ok"] is False and refused["cause"] == "unknown_country" and "han" in refused["choices"], refused)
refused = send({"cmd": "set_relation", "with": "han", "stance": "beloved"})
check("an unknown stance is refused with the stances",
      refused["ok"] is False and refused["cause"] == "unknown_stance" and "friendly" in refused["choices"], refused)
refused = send({"cmd": "set_relation", "with": "han"})
check("a call that sets nothing is refused", refused["ok"] is False and refused["cause"] == "nothing_to_set", refused)
check("refusals changed nothing", set(game.state.stores["relations"]) == {"rome|han"}
      and relations.read(game.stores, "rome", "han")["stance"] == "friendly", game.state.stores)

# ---- the other side's view: public fields show, the private note does not
theirs = send({"cmd": "relations", "with": "rome", "as": "northern"})
check("the northern seat reads its own side as the default", theirs["country"] == "han" and theirs["ours"]["stance"] == "neutral", theirs)
check("it sees the other side's stance and terms but not their note",
      theirs["theirs"]["stance"] == "friendly" and theirs["theirs"]["treaty"] == {"grain_for_silk": 3}
      and "note" not in theirs["theirs"], theirs)
send({"cmd": "set_relation", "with": "rome", "note": "keep the tea secret", "as": "northern"})
check("each country keeps its own side", relations.read(game.stores, "han", "rome")["note"] == "keep the tea secret"
      and relations.read(game.stores, "rome", "han")["note"].startswith("their envoy"), game.state.stores)

# ---- a mechanism appends dated events; both sides carry them
relations.record_event(game.stores, "rome", "han", game.year, "tribute_paid", amount=12.0)
listed = send({"cmd": "relations"})
rows = {row["with"]: row for row in listed["relations"]}
check("the list shows every country with a recorded relation", listed["ok"] and list(rows) == ["han"], listed)
check("an event states its year, kind and facts as values",
      rows["han"]["ours"]["history"] == [{"year": 100, "kind": "tribute_paid", "facts": {"amount": 12.0}}], rows)
check("both sides carry the event", relations.read(game.stores, "han", "rome")["history"][0]["kind"] == "tribute_paid", None)
for _ in range(relations.MAX_HISTORY + 5):
    relations.record_event(game.stores, "rome", "han", game.year, "tick")
check("history is bounded", len(relations.read(game.stores, "rome", "han")["history"]) == relations.MAX_HISTORY, None)

# ---- saved with the game: the stores dict is state, so a JSON round trip keeps it
revived = Game()
revived.state.stores = json.loads(json.dumps(game.state.stores))
check("a saved and loaded game reads the same record",
      relations.read(revived.stores, "rome", "han") == relations.read(game.stores, "rome", "han"), None)

# ---- the note outlives the seat: it is the country's
del game.state.seats["northern"]
check("a country's note survives the loss of its seat",
      relations.read(game.stores, "han", "rome")["note"] == "keep the tea secret", game.state.stores)
before = copy.deepcopy(game.state.stores)
send({"cmd": "relations", "with": "han"})
check("reading never writes", game.state.stores == before, None)
