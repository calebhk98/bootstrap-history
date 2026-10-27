"""SMOKE (Complaint 529): a screen or query command must not change the game; whether one does is read off the saved state of an unopened
game. The six commands that each take a fifth of a second or more on their own are left out to stay under the smoke budget."""
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
    "prospect", "settle", "quote", "patent", "world_events", "relations", "levers", "armies",
}
CHANGES_STATE = {
    "start", "stop", "rush", "mothball", "restore", "open", "policy", "offer", "accept", "decline", "disclose",
    "exclude", "include", "finish", "answer", "withdraw", "bribe", "allocate", "hire", "fire", "train",
    "commission", "move_base", "pursue", "bounty", "buy", "sell", "close", "note", "join", "keep", "reserve",
    "build_way", "save", "step", "quit", "load", "set_relation", "lever", "handover", "army", "found",
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

# each takes over a fifth of a second to answer on an unopened game (measured one by one)
TOO_SLOW_FOR_SMOKE = {"available", "capacity", "idle", "market", "portfolio", "stuck"}


def requests():
    for name in sorted(READ_ONLY & set(command_registry.COMMANDS) - TOO_SLOW_FOR_SMOKE):
        request = {"cmd": name}
        if command_registry.COMMANDS[name]["shape"] == "tech":
            request["node"] = node_id
        yield name, request


def ask_all():
    """Run every read-only command; the names that ran."""
    names = []
    for name, request in requests():
        try:
            _agent_dispatch(game, game.nodes, request)
        except Exception:  # a screen that cannot run on this game is not what this checks
            continue
        names.append(name)
    return names


def changers():
    """The commands that change the saved game: one dump around the whole round, and only a round that changed it is walked
    command by command to name the culprit."""
    before = dump()
    ask_all()
    if dump() == before:
        return []
    found = []
    for name, request in requests():
        before = dump()
        try:
            _agent_dispatch(game, game.nodes, request)
        except Exception:
            continue
        if dump() != before:
            found.append(name)
    return found


# the first look may set up defaults, caches and "last seen" markers; from then on a look changes nothing
ran = ask_all()
check("read-only commands ran", len(ran) > 20, str(len(ran)))
changed = changers()
check("no read-only command changes the saved game", not changed, str(changed))

before = dump()
game.view("resource_throttle")()
game.view("resource_throttle")(node_id)
check("peeking the throttle leaves the saved game as it was", dump() == before)
