"""Complaint 573: `stuck` reads the same work in hand as `state`, training included."""
from .harness import *  # noqa: F401,F403
from .agent_command_helpers import ask_agent

game = sim(civ="rome_100ad", capital=500000)
ask_agent(game, cmd="train", trade="machinist", n=1)
state = ask_agent(game, cmd="state", full=True)
stuck = ask_agent(game, cmd="stuck")
reasons = stuck["what_is_holding_you_up"]
rows = reasons if isinstance(reasons, list) else []
training_rows = [row for row in rows if row.get("each_training") is not None]
check("with only training running stuck does not report an idle household",
      "idle" not in [row.get("kind") for row in rows], rows)
check("stuck names the training state shows",
      bool(training_rows) and training_rows[0].get("each_training") == state["training_pending"],
      (training_rows, state["training_pending"]))
