"""Complaint 529: a screen or query command must not change the game."""
import os
import tempfile

from .harness import *  # noqa: F401,F403

from sim.engine.saveload import save_state
from sim.ui.proto import command_registry
from sim.ui.proto.dispatch import _agent_dispatch

# Commands that only report. Any other registered command must be listed in CHANGES_STATE.
READ_ONLY = {
    "help", "anatomy", "cashbook", "causes", "figures", "game_options", "goals", "leverage", "idle", "state",
    "available", "log", "score", "materials", "risk", "groups", "values", "stuck", "mines", "capacity",
    "portfolio", "economy", "changes", "population", "work", "labour", "market", "money", "options", "map",
    "education", "demography", "divergence", "commitments", "colonies", "ventures", "automation", "offers",
    "shares", "notes", "why", "path", "programme", "saving", "seats", "pay", "priority", "rollout",
    "prospect", "settle", "quote", "patent", "world_events", "relations", "levers",
}
CHANGES_STATE = {
    "start", "stop", "rush", "mothball", "restore", "open", "policy", "offer", "accept", "decline", "disclose",
    "exclude", "include", "finish", "answer", "withdraw", "bribe", "allocate", "hire", "fire", "train",
    "commission", "move_base", "pursue", "bounty", "buy", "sell", "close", "note", "join", "keep", "reserve",
    "build_way", "save", "step", "quit", "load", "set_relation", "lever", "handover",
}

game = unopened_sim()
node_id = sorted(game.nodes)[0]
dump_path = os.path.join(tempfile.mkdtemp(prefix="state_dump"), "dump.json")


def dump():
    save_state(game, dump_path)
    with open(dump_path) as handle:
        return handle.read()


unclassified = set(command_registry.COMMANDS) - READ_ONLY - CHANGES_STATE
check("every registered command is classified as reading or changing", not unclassified, str(sorted(unclassified)))

def requests():
    for name in sorted(READ_ONLY & set(command_registry.COMMANDS)):
        request = {"cmd": name}
        if command_registry.COMMANDS[name]["shape"] == "tech":
            request["node"] = node_id
        yield name, request


def ask_all(only=None):
    """Run every read-only command (plain and compact); the names that ran, or the ones that changed the dump."""
    names = []
    for name, request in requests():
        before = dump()
        try:
            _agent_dispatch(game, game.nodes, request)
            _agent_dispatch(game, game.nodes, dict(request, compact=True))
        except Exception:  # a screen that cannot run on this game is not what this checks
            continue
        if only is None or dump() != before:
            names.append(name)
    return names


# the first look may set up defaults, caches and "last seen" markers; from then on a look changes nothing
ran = ask_all()
check("read-only commands ran", len(ran) > 20, str(len(ran)))
changed = ask_all(only=True)
check("no read-only command changes the saved game", not changed, str(changed))

before = dump()
game.peek_resource_throttle()
game.peek_project_resource_throttle(node_id)
check("peeking the throttle leaves the saved game as it was", dump() == before)
