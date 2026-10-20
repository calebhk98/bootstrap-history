"""Complaint 106: a society founds banks only once it holds a node declaring the `deposit_banking` mechanic; the
engine hands the economy the institutions the home state's society holds (a civilisation with no banking
institution yet must not get banks)."""
from .harness import *  # noqa: F401,F403

from sim.engine import economy_port_institutions
from sim.economy import api as economy_api

game = sim()
nodes = game.nodes_with_mechanic("deposit_banking")
check("a finance node in the tree declares the deposit_banking mechanic, with a source",
      bool(nodes) and nodes[0].startswith("fin_") and game.mechanic(nodes[0], "deposit_banking").get("source"), nodes)
check("Rome starts without the institution, so its economy is told of none",
      economy_port_institutions.held(game) == (), economy_port_institutions.held(game))

game.state_treasury().knowledge.add(nodes[0])
check("a state that holds the node gives the economy the institution",
      economy_port_institutions.held(game) == (economy_api.DEPOSIT_BANKING,), economy_port_institutions.held(game))
