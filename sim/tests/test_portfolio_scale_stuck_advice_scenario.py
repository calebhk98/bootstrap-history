"""Scenario (Complaints 88 and 98): in a running game `stuck` carries live lever figures and `portfolio` replies with paging.
The paging, readout and advice rules are in test_portfolio_scale_stuck_advice."""
from .harness import *  # noqa: F401,F403

live = sim()
reply = S._agent_dispatch(live, NODES, {"cmd": "stuck"})
check("stuck on a real game carries live lever figures and the filler note",
      reply.get("lever_figures") and "filler" in str(reply.get("the_cheapest_start_is_filler")), reply)
check("portfolio on a real game replies with paging", S._agent_dispatch(live, NODES, {"cmd": "portfolio"})["paging"]["total"] == 0)
