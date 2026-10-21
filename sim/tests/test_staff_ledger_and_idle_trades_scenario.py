"""Scenarios in a whole game for Complaints 167, 164 and the auto_replace_foreman part of 180: the yearly staff step replaces
only the taught trades something draws on, `state` shows idle specialists and the single-person dependency, logged
losses reconcile with the headcount over years of stepping, and the policy gates the foreman's replacement. The rules are in
test_staff_ledger_and_idle_trades."""
import re

from .harness import *  # noqa: F401,F403


def _lost_from_log(log, first_line=0):
    """Total people named in 'you lose ...' lines, by trade."""
    totals = collections.Counter()
    for _year, message in log[first_line:]:
        if message.startswith("you lose "):
            for count, trade in re.findall(r"(\d+(?:\.\d+)?) ([a-z_]+?)s?(?:,| to )",
                                           message.split(" to ")[0] + " to "):
                totals[trade] += float(count)
    return totals


def _machinist_sim():
    s = sim(capital=5_000_000, manual=False)
    s.trades_created.add("machinist")
    s.employees.pop("machinist", None)
    s.labour._resync_pools()
    return s


# 171: auto_hire does not re-hire a taught trade nothing draws on, but does when an open concern's foreman is that trade.
s = _machinist_sim()
s.trades_created.add("glassblower")
s.done.add("mirror_amalgam")
s.operating.add("mirror_amalgam")
s._step_staff()
check("the staff step replaces a taught trade an open concern draws on, and not one nothing uses",
      s.employees.get("glassblower", 0.0) >= 0.5 and s.employees.get("machinist", 0.0) < 0.5, dict(s.employees))

# 171, 180: state shows idle specialists, and warns when an open concern hangs on one specialist.
s = sim(capital=5_000_000)
s.employees["machinist"] = 2.0
s.done.add("mirror_amalgam")
s.operating.add("mirror_amalgam")
s.employees["glassblower"] = 1.0
s.labour._resync_pools()
state = S._agent_dispatch(s, NODES, {"cmd": "state"})
check("state shows the idle machinists and not the foreman an open concern draws on, and warns of the one-person dependency",
      any(row["trade"] == "machinist" for row in (state.get("idle_specialists") or []))
      and all(row["trade"] != "glassblower" for row in (state.get("idle_specialists") or []))
      and (state.get("depends_on_one_person") or [{}])[0].get("trade") == "glassblower",
      (state.get("idle_specialists"), state.get("depends_on_one_person")))

# 168: logged artisan losses reconcile with the labour headcount over years of stepping.
s = sim(capital=5_000_000, events=False)
s.labour.hire("artisan", 10)
start = s.employees["artisan"]
mark = len(s.log)
for _ in range(15):
    s._step_staff()
lost_total = _lost_from_log(s.log, mark)["artisan"]
check("logged artisan losses reconcile with the labour headcount over years of stepping",
      s.employees.get("artisan", 0.0) <= start and abs(start - s.employees.get("artisan", 0.0) - lost_total) < 0.06 * 15,
      (start, s.employees.get("artisan"), lost_total))

# 180: the policy gates the yearly replacement of a lost foreman, and `policy` lists it.
s = sim(capital=5_000_000)
s.trades_created.add("glassblower")
s.done.add("mirror_amalgam")
s.operating.add("mirror_amalgam")
s.policy["auto_replace_foreman"] = False
s._step_staff()
off = s.employees.get("glassblower", 0.0)
s.policy["auto_replace_foreman"] = True
s._step_staff()
check("with the policy off the step does not re-hire the foreman, with it on the step does, and `policy` lists it",
      off < 0.5 and s.employees.get("glassblower", 0.0) >= 0.5
      and "auto_replace_foreman" in S._agent_dispatch(s, NODES, {"cmd": "policy"})["what_each_does"], dict(s.employees))
