"""Focused regressions for the second group of playtest complaints."""
from .harness import *  # noqa: F401,F403
from engine.protocol import _waiting_on as _waiting_on


# Complaint 02 requires two genuinely different states: a project that can
# consume revenue arriving later in the year, and one beyond all cash/credit
# that cannot progress until its finances change.
_money_node = "academy_network"
_money_state = dict(ph_left=0.0, yrs=1.0, spent=0.0, cost_left=9000.0)
_blocked = sim(capital=0.0)
_blocked.capital = -50_000.0
_blocked.credit_limit = lambda: 2_000.0
_blocked.project_cost = lambda k: 9_000.0
_blocked.active[_money_node] = dict(_money_state)
_blocked_message = _waiting_on(_blocked, NODES, _money_node,
                               _blocked.active[_money_node], 9000.0)
check("a project with no spending power is labelled fully blocked",
      _blocked_message.startswith("money: fully blocked"), _blocked_message)

_opportunistic = sim(capital=1.0)
_opportunistic.project_cost = lambda k: 9_000.0
_opportunistic.active[_money_node] = dict(_money_state)
_opportunistic_message = _waiting_on(
    _opportunistic, NODES, _money_node, _opportunistic.active[_money_node], 9000.0)
check("a project with some funding access is labelled opportunistic",
      _opportunistic_message.startswith(
          "money: unfunded now; will fund opportunistically"),
      _opportunistic_message)


# A binding material is a property of its consumers, not of the whole research
# portfolio.  Stub only the aggregate accounting result here; the project
# selector must inspect each node's own material inputs.
s = sim()
s.binding = "saltpetre"
s.resource_throttle = lambda: 0.05
check("a nitre shortage throttles a project that consumes nitre",
      s.project_resource_throttle("gunpowder") == 0.05)
check("the same nitre shortage leaves an unrelated research project at full pace",
      s.project_resource_throttle("scientific_method") == 1.0)


# Capacity is the diagnostic that explains those per-project limits.  It must
# be in the command index rather than discoverable only by guessing it, and it
# must distinguish annual flow from durable inventory.
_commands = S._agent_help(sim(), "commands")["commands"]
check("capacity is discoverable in the main command index",
      "capacity" in _commands, sorted(_commands))
check("capacity help distinguishes throughput from material stock",
      "throughput" in _commands["capacity"]
      and "stock" in _commands["capacity"]
      and "materials" in _commands["capacity"], _commands["capacity"])


# A zero-hour, zero-cost, zero-risk capability is a state transition, not a
# one-year undertaking.  Its prerequisite is supplied directly so the check
# isolates start_project's timing.
s = sim()
s.done.add("thermometer")
s._done_changed()
ok, why = s.start_project("cap_measure_temp")
check("a genuinely instantaneous capability completes when it is started",
      ok and "cap_measure_temp" in s.done and "cap_measure_temp" not in s.active,
      why)


# The credit forecast used to put the percentage itself in a field labelled
# "interest per year".  Pin both dimensions and their units independently.
s = sim(civ="england_1300", capital=1300.0)
out = S._agent_dispatch(s, NODES, {"cmd": "start", "id": "identity_cover"})
credit = out.get("on_credit", {})
check("credit forecasts label the percentage as a rate",
      credit.get("interest_rate_percent")
      == round(s.debt_interest_rate() * 100, 1), credit)
check("credit forecasts calculate the annual denarius charge",
      credit.get("estimated_annual_interest")
      == round(credit["you_would_borrow"] * s.debt_interest_rate(), 1), credit)
check("the misleading old interest-per-year field is gone",
      "interest_per_year_on_it" not in credit, credit)


# Recommendation size follows the live deficit.  Isolate it from the market
# so 1.1 t/year reproduces the reported shortage: 1,375 m2 bare, rounded to
# 1,700 m2 after the documented twenty-percent buffer.
s = sim()
s.annual_material_demand = lambda: {"saltpetre_kg": 1100.0}
s._material_market_tonnes = lambda material: 0.0
msg = s.shortage_remedy("saltpetre")
check("nitre advice is sized from the current deficit plus its stated buffer",
      "buy nitre 1700" in msg and "20% safety buffer" in msg, msg)
check("nitre advice no longer recommends a fixed twenty-thousand-square-metre bed",
      "buy nitre 20000" not in msg, msg)
