"""Typed-line parsing for rollout: `rollout`, `rollout <id> 50`, `rollout <id> 0.5`."""
from . import typed


def parse_rollout(command, rest, words, nums, want_json):
    if not rest:
        return {"cmd": "rollout"}, None
    node_id = str(rest[0])
    if not nums:
        return None, "rollout <id> needs the share to serve, e.g. 'rollout %s 50'." % node_id
    return {"cmd": "rollout", "id": node_id, "share": nums[-1]}, None


typed._COMMAND_PARSERS.setdefault("rollout", parse_rollout)
