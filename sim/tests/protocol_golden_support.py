"""Replay a scripted agent session in-process and reduce each reply to its structured values.

A script is a list of steps. A step is either `{"run": [command, ...]}`, one `agent` invocation
fed those commands on stdin (arguments in the script's `arguments`), or the same with `"session"`
naming a save file kept between invocations. Replies are reduced by `normalise`: numbers, booleans,
null and identifier-like strings stay; free prose becomes PROSE, so a reworded message does not
differ but a changed figure, id, `cause` or `facts` does.
"""
import json
import os
import re
import tempfile

from . import cli_in_process

PROSE = "~prose~"
IDENTIFIER = re.compile(r"^[a-z0-9_:.\-]{1,48}$")
KEEP_WHOLE = ("cause", "event_kind", "kind", "cmd")     # always kept verbatim, whatever they look like


def normalise(value, key=None):
    """`value` with every free-prose string replaced by PROSE."""
    if isinstance(value, dict):
        return {name: normalise(inner, name) for name, inner in value.items()}
    if isinstance(value, list):
        return [normalise(inner, key) for inner in value]
    if isinstance(value, str):
        if key in KEEP_WHOLE or IDENTIFIER.match(value):
            return value
        return PROSE
    return value


def prose_free(reply):
    """Count of structured leaves (numbers, booleans, kept strings) in a normalised reply."""
    if isinstance(reply, dict):
        return sum(prose_free(inner) for inner in reply.values())
    if isinstance(reply, list):
        return sum(prose_free(inner) for inner in reply)
    return 0 if reply == PROSE or reply is None else 1


def replay(script):
    """The normalised transcript of a script: a list of {"cmd", "reply"} in order."""
    transcript = []
    with tempfile.TemporaryDirectory() as directory:
        for step in script["steps"]:
            arguments = ["agent"] + list(step.get("arguments", script["arguments"]))
            if step.get("session"):
                arguments += ["--session", step["session"]]
            lines = "".join(json.dumps(command) + "\n" for command in step["run"])
            result = cli_in_process.run(arguments, input_text=lines, cwd=directory,
                                        environment=_environment())
            replies = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
            if len(replies) != len(step["run"]):
                raise AssertionError("%s: sent %d commands, got %d replies (exit %s): %s" % (
                    script["name"], len(step["run"]), len(replies), result.returncode,
                    result.stderr[-600:]))
            for command, reply in zip(step["run"], replies):
                transcript.append({"cmd": command, "reply": normalise(reply)})
    return transcript


def _environment():
    environment = dict(os.environ)
    environment["COLUMNS"], environment["LINES"] = "80", "24"
    # The suite's own settings (sim/tests/harness.py): short hidden spin-up, so a game opens in seconds.
    environment["ROME_SPIN_UP_YEARS"], environment["ROME_DEFAULT_SEED"] = "3,2", "1"
    return environment


def first_difference(expected, actual, path=""):
    """The first path at which two JSON values differ as (path, expected, actual), else None."""
    if type(expected) is not type(actual) and not (
            isinstance(expected, (int, float)) and isinstance(actual, (int, float))
            and not isinstance(expected, bool) and not isinstance(actual, bool)):
        return path, expected, actual
    if isinstance(expected, dict):
        for name in list(expected) + [name for name in actual if name not in expected]:
            if name not in expected or name not in actual:
                return "%s.%s" % (path, name), expected.get(name, "<absent>"), actual.get(name, "<absent>")
            found = first_difference(expected[name], actual[name], "%s.%s" % (path, name))
            if found:
                return found
        return None
    if isinstance(expected, list):
        if len(expected) != len(actual):
            return path + ".length", len(expected), len(actual)
        for index, (left, right) in enumerate(zip(expected, actual)):
            found = first_difference(left, right, "%s[%d]" % (path, index))
            if found:
                return found
        return None
    return None if repr(expected) == repr(actual) else (path, expected, actual)


def compare(expected, actual):
    """A message naming the first differing command and key, or None when the transcripts agree."""
    for index in range(max(len(expected), len(actual))):
        if index >= len(expected) or index >= len(actual):
            return "command %d: transcript lengths differ (%d recorded, %d now)" % (
                index, len(expected), len(actual))
        found = first_difference(expected[index], actual[index])
        if found:
            path, was, now = found
            return "command %d %s: key %s was %r, now %r" % (
                index, json.dumps(expected[index]["cmd"]), path, was, now)
    return None
