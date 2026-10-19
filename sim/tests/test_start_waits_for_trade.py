"""Complaint 572: `start` states at once what the first year would show: a trade with no hands yet."""
from .harness import *  # noqa: F401,F403
from .agent_command_helpers import ask_agent

PROJECT = "mfg_cutting_fluid"      # owes hours to the machinist, a trade Rome lacks at the start
game = sim(civ="rome_100ad", capital=500000)
ask_agent(game, cmd="train", trade="machinist", n=1)
reply = ask_agent(game, cmd="start", id=PROJECT)
waits = reply.get("waits_for_trades") or {}
check("a start whose trade is still in training is accepted and names the trade and the wait",
      reply.get("ok") is True and set(waits) == {"machinist"} and waits["machinist"] > 0, reply)

late = sim(civ="rome_100ad", capital=500000)
ask_agent(late, cmd="train", trade="machinist", n=1)
late.state.household.training[0][1] = late.state.scenario.year + 10
late_reply = ask_agent(late, cmd="start", id=PROJECT)
check("a start whose trainees arrive after the stall limit is refused with the staffing cause",
      late_reply.get("ok") is False and late_reply.get("blocked_cause") == "none_left_trades", late_reply)
check("...and nothing was started", PROJECT not in late.active, list(late.active))
