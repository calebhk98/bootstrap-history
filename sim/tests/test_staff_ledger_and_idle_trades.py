"""staff_ledger_and_idle_trades: complaints 171, 168 and the auto_replace_foreman part of 180."""
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


def _machinist_sim(manual=False):
    s = sim(capital=5_000_000, manual=manual)
    s.trades_created.add("machinist")
    s.employees.pop("machinist", None)
    s._resync_pools()
    return s


# 171: auto_hire does not re-hire a taught trade nothing draws on.
s = _machinist_sim()
s.step()
check("auto_hire does not hire a taught trade nothing uses",
      s.employees.get("machinist", 0.0) < 0.5, s.employees.get("machinist"))

# ...but does replace it when an open concern's foreman is that trade.
s = _machinist_sim()
s.trades_created.add("glassblower")
s.done.add("mirror_amalgam")
s.operating.add("mirror_amalgam")
check("mirror_amalgam draws on a glassblower foreman",
      "glassblower" in s.venture_foremen_used(), s.venture_foremen_used())
s.step()
check("auto_hire still replaces a taught trade an open concern draws on",
      s.employees.get("glassblower", 0.0) >= 0.5, dict(s.employees))

# 171: idle specialists are surfaced with their wage bill.
s = sim(capital=5_000_000)
s.employees["machinist"] = 2.0
s._resync_pools()
idle = s.idle_specialists()
check("idle_specialists lists an unused machinist with a wage bill",
      any(row["trade"] == "machinist" and row["wage_bill_per_year"] > 0 for row in idle), idle)
state = S._agent_dispatch(s, NODES, {"cmd": "state"})
check("state shows idle specialists",
      any(row["trade"] == "machinist" for row in (state.get("idle_specialists") or [])),
      state.get("idle_specialists"))
s.done.add("mirror_amalgam")
s.operating.add("mirror_amalgam")
s.employees["glassblower"] = 2.0
check("a specialist an open concern draws on is not idle",
      all(row["trade"] != "glassblower" for row in s.idle_specialists()), s.idle_specialists())

# 168: every staff reduction is logged with its cause.
s = sim(capital=5_000_000, events=False)
s.hire("artisan", 10)
before_headcount = s.employees.get("artisan", 0.0)
mark = len(s.log)
s.STAFF_LOSS_HAZARD_ANNUAL_CHANCE = 1.0
s._shock_staff_loss({"name": "Test plague", "staff_loss": 0.3}, s.year)
lost_lines = [m for _, m in s.log[mark:] if m.startswith("you lose ") and "artisan" in m]
after_headcount = s.employees.get("artisan", 0.0)
check("a plague trims artisans and says so in a 'you lose' line with its cause",
      after_headcount < before_headcount and len(lost_lines) == 1 and "Test plague" in lost_lines[0],
      (before_headcount, after_headcount, lost_lines))
check("the plague line's count matches the drop",
      abs(_lost_from_log(s.log, mark)["artisan"] - (before_headcount - after_headcount)) < 0.06,
      (_lost_from_log(s.log, mark), before_headcount - after_headcount))

s = sim(capital=5_000_000, events=False)
s.hire("artisan", 10)
start = s.employees["artisan"]
mark = len(s.log)
for _ in range(15):
    s.step()
lost_total = _lost_from_log(s.log, mark)["artisan"]
check("logged artisan losses reconcile with the labour headcount over years of stepping",
      s.employees.get("artisan", 0.0) <= start
      and abs(start - s.employees.get("artisan", 0.0) - lost_total) < 0.06 * 15,
      (start, s.employees.get("artisan"), lost_total))

# 180: auto_replace_foreman.
s = sim(capital=5_000_000)
check("auto_replace_foreman is a policy, off in manual play",
      s.policy.get("auto_replace_foreman") is False, s.policy.get("auto_replace_foreman"))
check("policy lists auto_replace_foreman",
      "auto_replace_foreman" in S._agent_dispatch(s, NODES, {"cmd": "policy"})["what_each_does"],
      list(S._agent_dispatch(s, NODES, {"cmd": "policy"})["what_each_does"]))
s.trades_created.add("glassblower")
s.done.add("mirror_amalgam")
s.operating.add("mirror_amalgam")
s.employees["glassblower"] = 1.0
s._resync_pools()
warned = S._agent_dispatch(s, NODES, {"cmd": "state"}).get("depends_on_one_person")
check("state warns when an open concern hangs on one specialist",
      bool(warned) and warned[0]["trade"] == "glassblower", warned)
s.employees.pop("glassblower")
s.replace_lost_foremen()
check("replace_lost_foremen hires the missing foreman", s.employees.get("glassblower", 0.0) >= 1.0,
      dict(s.employees))
s.employees.pop("glassblower")
s.policy["auto_replace_foreman"] = False
s.step()
check("with the policy off the step does not re-hire the foreman",
      s.employees.get("glassblower", 0.0) < 0.5, dict(s.employees))
s.policy["auto_replace_foreman"] = True
s.operating.add("mirror_amalgam")
s.employees.pop("glassblower", None)
s.step()
check("with the policy on the step re-hires the foreman",
      s.employees.get("glassblower", 0.0) >= 0.5, dict(s.employees))
