"""Complaint 294, through a running game: `stuck` stops recommending the cheapest start while a savings target stands,
shows the saving row, and recommends it again once the target is cleared. The plan itself is test_saving_target."""
from .harness import *  # noqa: F401,F403


def ask(test_sim, **command):
    return S._agent_dispatch(test_sim, NODES, command)


saver = sim(capital=2_000.0)
cheapest = min((node_id for node_id in NODES if node_id not in saver.done and saver.start_reason(node_id)[0]),
               key=saver.project_cost)
before = ask(saver, cmd="stuck")
check("without a target stuck recommends starting the cheapest thing",
      cheapest in str(before["what_is_holding_you_up"]), before["what_is_holding_you_up"])

saver.recurring_net = lambda: 500.0
plan = ask(saver, cmd="saving", id=cheapest, target=saver.capital + 1_800.0)["saving"]
after = ask(saver, cmd="stuck")
saving_rows = [row for row in after["what_is_holding_you_up"] if row.get("kind") == "saving"]
check("while saving, stuck shows a saving row with the affordable year and no longer recommends the cheapest start",
      saving_rows and str(plan["year_affordable"]) in saving_rows[0]["why"] and cheapest in saving_rows[0]["what"]
      and not any(row.get("kind") != "saving" and cheapest in str(row) and "begin the cheapest" in str(row)
                  for row in after["what_is_holding_you_up"]), saving_rows)

ask(saver, cmd="saving", off=True)
check("stuck recommends the cheapest again once cleared",
      cheapest in str(ask(saver, cmd="stuck")["what_is_holding_you_up"]))
