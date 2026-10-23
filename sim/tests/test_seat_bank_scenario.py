"""SCENARIO (Complaint 640): the found command on a game. A seat that does not hold the deposit-banking node is refused; once
it holds one, its capital leaves its money and stands as a bank of the agent economy. The rules are in test_seat_bank.py."""
from .harness import *  # noqa: F401,F403

from sim.engine.mechanics import nodes_declaring
from sim.ui.proto.dispatch_bank import _cmd_found

banking_node = nodes_declaring(NODES, "deposit_banking")[0][0]

game = sim()
refused = _cmd_found(game, NODES, {"cmd": "found", "what": "bank", "capital": 10.0}, None)
check("scenario: a seat without the banking node is refused with its cause",
      refused["ok"] is False and refused["cause"] == "no_banking_institution", refused)

game.state.projects.done.add(banking_node)
game.economy.open_agent()
before = game.dealing_party().money
founded = _cmd_found(game, NODES, {"cmd": "found", "what": "bank", "capital": 10.0}, None)
check("scenario: a seat that holds the node founds a bank and its capital leaves its money",
      founded["ok"] is True and abs((before - game.dealing_party().money) - 10.0) < 1e-9, (founded, before, game.dealing_party().money))
economy = game.economy.agent.economy()
check("scenario: the bank stands in the economy with the seat as founder",
      founded["bank"] in economy.record.banks and economy.record.banks[founded["bank"]].founder == game.state.acting_seat,
      list(economy.record.banks))
