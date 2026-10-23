"""SCENARIO (Complaint 640): Complaint 595 through the protocol (slow: builds a game): a country seat's lever command changes the seat's own
government, the reply states the change in fields, and a household seat or another country is refused with a cause."""
from .harness import *  # noqa: F401,F403
from sim.engine.agents_port import SimWorld
from sim.ui.proto import command_registry
from sim.ui.proto import dispatch  # noqa: F401  (registers every command)
from sim.ui.proto.seat_address import run_as_seat

game = unopened_sim(civ="rome_100ad", capital=1000.0, events=True)
handlers = command_registry.handlers()


def send(cmd):
    return run_as_seat(game, cmd, lambda command: handlers[command["cmd"]](game, game.nodes, command, None))


home = str(game.civ["id"])
send({"cmd": "join", "seat": "merchant"})
send({"cmd": "join", "seat": "senate", "seat_kind": "country"})
record = game.actors.government_of(home).record
declared = game.civ["state_revenue"][0]

reply = send({"cmd": "lever", "lever": "revenue", "name": declared["form"], "value": 0.5, "as": "senate"})
check("a rate lever replies with the change in fields",
      reply["ok"] and (reply["lever"], reply["name"], reply["before"], reply["after"], reply["country"])
      == ("revenue", declared["form"], None, 0.5, home), reply)
check("it changed the government's record and the revenue forms the budget reads",
      record.levers["revenue"][declared["form"]]["rate"] == 0.5
      and next(form for form in SimWorld(game).revenue_forms() if form["form"] == declared["form"])["rate"] == 0.5, record.levers)
check("the reply lists the levers now set", reply["levers"]["revenue"][declared["form"]]["rate"] == 0.5, reply["levers"])

reply = send({"cmd": "lever", "lever": "army", "value": 123, "as": "senate"})
check("the army lever is set on the government", reply["ok"] and record.levers["army"] == 123.0, reply)
check("the levers command lists it", send({"cmd": "levers", "as": "senate"})["levers"]["army"] == 123.0, None)
check("a typed lever line is read", send({"cmd": "lever", "text": "reserve 4", "as": "senate"})["after"] == 4.0, None)

refused = send({"cmd": "lever", "lever": "army", "value": 5, "as": "merchant"})
check("a household seat is refused", refused["ok"] is False and refused["cause"] == "household_seat_has_no_government", refused)
refused = send({"cmd": "lever", "lever": "army", "value": 5, "country": "han_china_100ad", "as": "senate"})
check("another country's lever is refused with the one allowed", refused["cause"] == "not_your_country" and refused["choices"] == [home], refused)
refused = send({"cmd": "lever", "lever": "tithe", "value": 5, "as": "senate"})
check("an unknown lever is refused with the choices", refused["cause"] == "unknown_lever" and "army" in refused["choices"], refused)
refused = send({"cmd": "lever", "lever": "revenue", "name": declared["form"], "value": 7, "as": "senate"})
check("a value out of range is refused with its limits", refused["cause"] == "value_out_of_range" and refused["high"] == 1.0, refused)
check("refusals changed nothing", record.levers["army"] == 123.0 and record.levers["revenue"][declared["form"]]["rate"] == 0.5, record.levers)

