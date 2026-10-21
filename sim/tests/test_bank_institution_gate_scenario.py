"""SCENARIO (Complaint 640): the wiring from a state's knowledge to the economy's institutions, on a game (Complaint 106).
The rules are in test_bank_institution_gate.py."""
from .harness import *  # noqa: F401,F403

from sim.engine import economy_port_institutions
from sim.engine.mechanics import nodes_declaring
from sim.economy import api as economy_api

declaring = nodes_declaring(NODES, "deposit_banking")

# scenario: the wiring from a state's knowledge to the economy's institutions, on a game
game = sim()
before = economy_port_institutions.held(game)
game.state_treasury().knowledge.add(declaring[0][0])
after = economy_port_institutions.held(game)
check("scenario: Rome starts without the institution; a state that then holds the node gives the economy it",
      before == () and after == (economy_api.DEPOSIT_BANKING,), (before, after))
