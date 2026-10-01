"""Complaint 294: an actor can mark a planned project and savings target; `stuck` respects it."""
from .harness import *  # noqa: F401,F403

from sim.engine.proto.typed import parse_typed
from sim.engine.proto.render_typed import _RENDERERS


def ask(test_sim, **command):
    return S._agent_dispatch(test_sim, NODES, command)


saver = sim(capital=2_000.0)
cheapest = min((node_id for node_id in NODES if node_id not in saver.done and saver.start_reason(node_id)[0]),
               key=saver.project_cost)
before = ask(saver, cmd="stuck")
check("without a target stuck recommends starting the cheapest thing",
      cheapest in str(before["what_is_holding_you_up"]), before["what_is_holding_you_up"])

check("'saving <id> <amount>' parses", parse_typed("saving %s 9000" % cheapest)[0]
      == {"cmd": "saving", "id": cheapest, "target": 9000.0}, parse_typed("saving %s 9000" % cheapest))
check("'saving off' parses", parse_typed("saving off")[0] == {"cmd": "saving", "off": True}, parse_typed("saving off"))

saver.recurring_net = lambda: 500.0
target = saver.capital + 1_800.0
reply = ask(saver, cmd="saving", id=cheapest, target=target)
check("setting a target is accepted", reply.get("ok") is True, reply)
plan = reply["saving"]
check("the plan names the project, target, cash and net income",
      plan["id"] == cheapest and plan["target"] == target and plan["cash"] == saver.capital
      and plan["net_income_per_year"] == 500.0, plan)
check("the year affordable is today's year plus whole years of income needed",
      plan["year_affordable"] == saver.year + 4, plan)

after = ask(saver, cmd="stuck")
text = str(after["what_is_holding_you_up"])
check("stuck no longer recommends starting the cheapest thing while saving",
      "would begin the cheapest" not in text, text)
saving_rows = [row for row in after["what_is_holding_you_up"] if row.get("kind") == "saving"]
check("stuck shows a saving row with the affordable year",
      saving_rows and str(plan["year_affordable"]) in saving_rows[0]["why"] and cheapest in saving_rows[0]["what"],
      saving_rows)
check("the printed stuck screen shows it", "SAVING" in _RENDERERS["stuck"](after), _RENDERERS["stuck"](after)[:300])

default = ask(saver, cmd="saving", id=cheapest)
check("no amount means the project's own cost", default["saving"]["target"] == round(saver.project_cost(cheapest), 1), default)

saver.recurring_net = lambda: -10.0
losing = ask(saver, cmd="saving", id=cheapest, target=saver.capital + 5_000.0)
check("with no surplus there is no affordable year", losing["saving"]["year_affordable"] is None, losing)

reached = ask(saver, cmd="saving", id=cheapest, target=saver.capital - 1.0)
check("a target already in hand is affordable this year", reached["saving"]["year_affordable"] == saver.year, reached)

bad = ask(saver, cmd="saving", id="no_such_node")
check("an unknown project is refused", bad.get("ok") is False, bad)
check("a negative amount is refused", ask(saver, cmd="saving", id=cheapest, target=-5).get("ok") is False)

cleared = ask(saver, cmd="saving", off=True)
check("off clears the target", cleared["ok"] and cleared["saving"] is None, cleared)
check("stuck recommends the cheapest again once cleared",
      cheapest in str(ask(saver, cmd="stuck")["what_is_holding_you_up"]))

saver.recurring_net = lambda: 500.0
ask(saver, cmd="saving", id=cheapest, target=saver.capital + 1_800.0)
standing = ask(saver, cmd="saving")
check("bare saving shows the standing plan", standing["saving"]["id"] == cheapest, standing)
