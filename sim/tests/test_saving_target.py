"""Complaint 294: an actor can mark a planned project and savings target. The plan, the year it becomes affordable,
the command's refusals and the typed forms, each on a stand-in game (cash, income, year and a household record, no
game). `stuck` respecting the target is test_saving_target_scenario."""
from types import SimpleNamespace

from .harness import check, NODES

from sim.ui.proto.dispatch_saving import _cmd_saving
from sim.ui.proto.render_typed import _RENDERERS
from sim.ui.proto.saving_plan import saving_plan, saving_reason
from sim.ui.proto.typed import parse_typed

QUICK_TOPIC = True

PROJECT = sorted(NODES)[0]


def _saver(cash=2_000.0, income=500.0, year=100, project_cost=900.0):
    return SimpleNamespace(
        state=SimpleNamespace(household=SimpleNamespace(saving_for=None, saving_target=0.0)),
        capital=cash, year=year, recurring_net=lambda: income, project_cost=lambda node_id: project_cost,
        civ={"id": "stub"})


def _ask(saver, **command):
    return _cmd_saving(saver, NODES, dict(cmd="saving", **command), False)


check("'saving <id> <amount>' parses", parse_typed("saving %s 9000" % PROJECT)[0]
      == {"cmd": "saving", "id": PROJECT, "target": 9000.0}, parse_typed("saving %s 9000" % PROJECT))
check("'saving off' parses", parse_typed("saving off")[0] == {"cmd": "saving", "off": True}, parse_typed("saving off"))

check("with no target set there is no plan", saving_plan(_saver()) is None and saving_reason(_saver()) is None)

saver = _saver()
target = saver.capital + 1_800.0
reply = _ask(saver, id=PROJECT, target=target)
check("setting a target is accepted", reply.get("ok") is True, reply)
plan = reply["saving"]
check("the plan names the project, target, cash and net income",
      plan["id"] == PROJECT and abs(plan["target"] - target) < 0.1 and abs(plan["cash"] - saver.capital) < 0.1
      and plan["net_income_per_year"] == 500.0, plan)
check("the year affordable is today's year plus whole years of income needed (1800 at 500 a year is four years)",
      plan["year_affordable"] == saver.year + 4, plan)
saver.recurring_net = lambda: 600.0
check("an exact multiple of the income needs no extra year (1800 at 600 a year is three)",
      saving_plan(saver)["year_affordable"] == saver.year + 3)

row = saving_reason(saver)
check("the stuck row for a plan is a saving row naming the project and the affordable year",
      row["kind"] == "saving" and PROJECT in row["what"] and str(saver.year + 3) in row["why"], row)

default = _ask(saver, id=PROJECT)
check("no amount means the project's own cost", default["saving"]["target"] == round(saver.project_cost(PROJECT), 1), default)

losing = _saver(income=-10.0)
check("with no surplus there is no affordable year",
      _ask(losing, id=PROJECT, target=losing.capital + 5_000.0)["saving"]["year_affordable"] is None)
# presentation: the stuck row says the target is never reached
check("...and the stuck row says it is never reached",
      "never" in saving_reason(losing)["why"])
check("a zero income is no surplus either",
      saving_plan(SimpleNamespace(**dict(vars(losing), recurring_net=lambda: 0.0)))["year_affordable"] is None)

reached = _saver()
check("a target already in hand is affordable this year",
      _ask(reached, id=PROJECT, target=reached.capital - 1.0)["saving"]["year_affordable"] == reached.year)
check("...and a target exactly equal to the cash is too",
      _ask(reached, id=PROJECT, target=reached.capital)["saving"]["year_affordable"] == reached.year)
# presentation: the stuck row says the target is in hand
check("...and the stuck row says it is in hand", "in hand" in saving_reason(reached)["why"])

fresh = _saver()
check("an unknown project is refused", _ask(fresh, id="no_such_node").get("ok") is False)
check("a negative amount is refused", _ask(fresh, id=PROJECT, target=-5).get("ok") is False)
check("a flag is not an amount", _ask(fresh, id=PROJECT, target=True).get("ok") is False)
check("a refused target sets nothing", fresh.state.household.saving_for is None)

cleared = _ask(reached, off=True)
check("off clears the target", cleared["ok"] and cleared["saving"] is None, cleared)
standing = _saver()
_ask(standing, id=PROJECT, target=standing.capital + 1_800.0)
check("bare saving shows the standing plan", _ask(standing)["saving"]["id"] == PROJECT)
check("the printed stuck screen shows a saving row",
      "SAVING" in _RENDERERS["stuck"]({"what_is_holding_you_up": [saving_reason(standing)]}), None)
