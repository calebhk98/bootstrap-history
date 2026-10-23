"""SCENARIO (Complaint 640): One live process playing many commands leaves the same save as one process per command."""
from .harness import *  # noqa: F401,F403
from . import cli_in_process

_COMMANDS = [{"cmd": "state"}, {"cmd": "step", "years": 1}, {"cmd": "state"}, {"cmd": "step", "years": 1}]
_START = ["agent", "--civ", "norse_900ad", "--seed", "3", "--no-events"]


def _lines(commands):
    return "".join(json.dumps(command) + "\n" for command in commands)


def _dump(path):
    with open(path) as handle:
        return json.dumps(json.load(handle), sort_keys=True)


def _replies(result):
    return [line for line in result.stdout.splitlines() if line.startswith("{")]


def _per_command(session):
    """Each command in its own process: a load and a save every time."""
    replies = []
    for command in _COMMANDS:
        result = cli_in_process.run(_START + ["--session", session], _lines([command]))
        replies += _replies(result)
    return replies


def _one_process(session, extra):
    result = cli_in_process.run(_START + ["--session", session] + extra, _lines(_COMMANDS))
    return _replies(result)


_dir = tempfile.mkdtemp()
_each = os.path.join(_dir, "each.json")
_live = os.path.join(_dir, "live.json")
_deferred = os.path.join(_dir, "deferred.json")
_each_replies = _per_command(_each)
_live_replies = _one_process(_live, [])
_deferred_replies = _one_process(_deferred, ["--save-interval", "3600"])

check("one process writing every command ends in the save one process per command ends in",
      _dump(_live) == _dump(_each))
check("one process holding its writes back ends in that same save",
      _dump(_deferred) == _dump(_each))
check("the replies are the same in all three modes",
      _live_replies == _deferred_replies == _each_replies,
      (len(_live_replies), len(_deferred_replies), len(_each_replies)))

# A write is held back until something asks for it; the file is current once the process leaves.
_held = os.path.join(_dir, "held.json")
cli_in_process.run(_START + ["--session", _held, "--save-interval", "3600"],
                   _lines([{"cmd": "state"}]))
check("a held-back sitting still saves on leaving", os.path.exists(_held))

# The typed front door, with the same commands.
_typed_each = os.path.join(_dir, "typed_each.json")
_typed_live = os.path.join(_dir, "typed_live.json")
_play = ["play", "--civ", "norse_900ad", "--seed", "3"]
for _line in ["state", "step 1", "state", "step 1"]:
    cli_in_process.run(_play + ["--session", _typed_each], _line + "\nquit\n")
cli_in_process.run(_play + ["--session", _typed_live, "--save-interval", "3600"],
                   "state\nstep 1\nstate\nstep 1\nquit\n")
check("play: one deferred-save sitting ends in the save one sitting per command ends in",
      _dump(_typed_live) == _dump(_typed_each))
