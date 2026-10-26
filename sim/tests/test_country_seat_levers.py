"""Complaint 595 through the protocol: the lever and levers commands find the acting seat's own government, hand the request to
`government_levers.set_lever` with that government's record and the country's context, and shape the reply. Called on a stand-in
game with `set_lever` replaced by a recorder; what each lever does to the record is held by test_government_levers."""

QUICK_TOPIC = True

import types
from unittest import mock

from .harness import check

from sim.agents.records import ActorRecord
from sim.engine.state_seat import COUNTRY_SEAT, FIRST_SEAT_ID, seat_from_template
from sim.refusal import Refusal
from sim.ui.proto import command_registry
import sim.ui.proto.dispatch  # noqa: F401  (registers every command)

HOME = "rome_100ad"
FORM = {"form": "land_tax", "basis": "harvest", "rate": 0.1}
handlers = command_registry.handlers()


class LeverGame:
    """What the lever commands read: the acting seat, the country's government and its people, the goods and techniques."""

    def __init__(self, acting_kind=COUNTRY_SEAT, governed=True):
        seat = seat_from_template({"kind": acting_kind, "country": None}, 10.0, {})
        self.state = types.SimpleNamespace(seats={"senate": seat}, acting_seat="senate")
        self.civ = {"id": HOME}
        self.population = types.SimpleNamespace(total=1234.0)
        self.nodes = {"fire": {}}
        self.record = ActorRecord(kind="government", revenue_forms=[dict(FORM)])
        self.asked = []
        government = types.SimpleNamespace(record=self.record)
        self.actors = types.SimpleNamespace(government_of=lambda country: self.asked.append(country) or (government if governed else None))


def send(game, **fields):
    with mock.patch("sim.ui.proto.dispatch_levers.material_prices", lambda sim: {"wheat_kg": 2.0}):
        return handlers[fields.pop("cmd", "lever")](game, {}, fields, None)


class Recorder:
    """A set_lever that records its arguments and answers a change (or the refusal it is given)."""

    def __init__(self, answer):
        self.answer, self.calls = answer, []

    def __call__(self, record, request, context):
        self.calls.append((record, request, context))
        record.levers["army"] = 123.0
        return self.answer


change = {"lever": "army", "name": None, "before": None, "after": 123.0}
game = LeverGame()
recorder = Recorder(change)
with mock.patch("sim.agents.government_levers.set_lever", recorder):
    reply = send(game, lever="army", value=123)
record, request, context = recorder.calls[0]
check("a country seat's lever is set on its own government's record", record is game.record and request["value"] == 123, request)
check("the context carries the declared forms, the goods, the people and the techniques",
      context.declared_forms == [FORM] and context.materials == {"wheat_kg"} and context.population == 1234.0
      and context.techniques == {"fire"}, context)
check("the reply states the change in fields, the country and the levers now set",
      reply["ok"] and (reply["lever"], reply["before"], reply["after"], reply["country"]) == ("army", None, 123.0, HOME)
      and reply["levers"]["army"] == 123.0, reply)
check("the home country's government is asked for by None", game.asked == [None], game.asked)

game = LeverGame()
recorder = Recorder(change)
with mock.patch("sim.agents.government_levers.set_lever", recorder):
    reply = send(game, text="reserve 4")
check("a typed lever line is read into lever and value", (recorder.calls[0][1]["lever"], recorder.calls[0][1]["value"]) == ("reserve", 4.0),
      recorder.calls)
recorder = Recorder(change)
with mock.patch("sim.agents.government_levers.set_lever", recorder):
    send(game, text="revenue land_tax 0.5")
check("a typed line for a named lever reads the name before the value",
      (recorder.calls[0][1]["lever"], recorder.calls[0][1]["name"], recorder.calls[0][1]["value"]) == ("revenue", "land_tax", 0.5), recorder.calls)

recorder = Recorder(Refusal("value_out_of_range", "too high", choices=[0, 1], high=1.0))
with mock.patch("sim.agents.government_levers.set_lever", recorder):
    refused = send(game, lever="revenue", name="land_tax", value=7)
check("a refusal from the rule is passed on with its cause, choices and facts",
      refused["ok"] is False and refused["cause"] == "value_out_of_range" and refused["choices"] == [0, 1] and refused["high"] == 1.0, refused)

# ---- who may set a lever
game = LeverGame(acting_kind="household")
recorder = Recorder(change)
with mock.patch("sim.agents.government_levers.set_lever", recorder):
    refused = send(game, lever="army", value=5)
check("a household seat is refused and the rule is not called",
      refused["cause"] == "household_seat_has_no_government" and recorder.calls == [], refused)
game = LeverGame()
recorder = Recorder(change)
with mock.patch("sim.agents.government_levers.set_lever", recorder):
    refused = send(game, lever="army", value=5, country="han_china_100ad")
check("another country's lever is refused with the one allowed",
      refused["cause"] == "not_your_country" and refused["choices"] == [HOME] and recorder.calls == [], refused)
game = LeverGame(governed=False)
check("a country with no government is refused with its cause", send(game, lever="army", value=5)["cause"] == "no_government", None)

# ---- the levers command
game = LeverGame()
game.record.levers["army"] = 123.0
reply = send(game, cmd="levers")
check("the levers command lists what the government has set and the kinds that can be set",
      reply["ok"] and reply["levers"]["army"] == 123.0 and "army" in reply["kinds"] and reply["country"] == HOME, reply)
check("the levers command refuses a household seat",
      send(LeverGame(acting_kind="household"), cmd="levers")["cause"] == "household_seat_has_no_government", None)
