"""The machine-playable protocol: `agent`.

`cmd_agent` is the JSON-in/JSON-out driver a
script or another process talks to - see the module docstring in cli.py for
the protocol table. It deliberately does not call `_apply_display_prefs` (a
human terminal's own cosmetic settings have no business changing what a
script sees - see that function's own docstring in cli.py) and so needs
none of cli_interactive.py's display machinery, only the session-resolution
helpers cli.py also hands to the human-facing `play` command.
"""
import json, os, random, sys

from .data import load, load_civ, STARTING_KITS
from .core import Sim
from .protocol import _agent_dispatch, _agent_help, load_state, render_pretty, save_state
from . import settings

# Session helpers: shared with cli_interactive.py's cmd_play for the same
# reason (a --session file resumes the civilisation/goal it was started
# with), so they live in cli.py rather than in either front end alone.
from .cli import (DetRNG, _civ_for_session, _goal_for_session,
                  _is_claimed_slot, _pick_session_filename, load_strategy)


# ----------------------------------------------------------------------------
# Machine-playable interface: `agent`
#
# See the module docstring for the protocol table. In short: every line in,
# every line out, is one JSON object. `state` reports; `start`/`stop`/`bounty`/
# `buy` act; `step` advances the calendar. It is built on the same Sim.manual
# and start_project()/stop_project() this file's step()/can_start() comments
# already explain, so an agent driving this gets EXACTLY the consequences of
# its own choices, nothing the optimizer would have chosen for it.
# ----------------------------------------------------------------------------


def cmd_agent(args):
    """Machine-playable driver: JSON in, JSON out. See the module docstring for
    the protocol. Runs in Sim.manual mode ALWAYS, regardless of any other flag:
    the entire point of this command is that a script chooses the research
    path, so the optimizer's own auto-start (step() 4b) is never in play here.
    That is different from `play --manual`, which is the same guarantee for a
    human at a keyboard; `agent` is that guarantee for a script or an LLM.
    """
    tree, prices, nodes, wages, goods = load()
    goal = _goal_for_session(args, tree, nodes)
    label, order, bounties = load_strategy(args.strategy, nodes, goal)
    # `run`/`compare`/`play` all take --mortal, so `agent` must accept it
    # too, or the founder is immortal in every scripted or JSON-driven game
    # no matter what was asked for.
    cfg = {"start_capital": STARTING_KITS[args.kit]["den"], "horizon_years": args.horizon,
           "immortal": not getattr(args, "mortal", False)}
    sim = Sim(nodes, order,
            DetRNG(args.seed) if getattr(args, "deterministic", False) else random.Random(args.seed),
            events=not args.no_events,
            cfg=cfg, civ=load_civ(_civ_for_session(args)), bounty_set=set(), manual=True)
    sim.goal = goal
    sim.done_year = {}
    sim.end_year = sim.cfg["start_year"] + args.horizon
    sim.fog = bool(getattr(args, "fog", False))
    sim.revealed = set()
    pretty = bool(getattr(args, "pretty", False))

    session = getattr(args, "session", None)
    checkpoint_source = None
    if session and os.path.exists(session) and not _is_claimed_slot(session):
        try:
            load_state(sim, session)
        except Exception as error:
            sys.stdout.write(json.dumps(
                {"ok": False, "error": "could not read the save file %r: %s" % (session, error)}
            ) + "\n")
            return 1
        # A FROZEN CHECKPOINT DOES NOT BECOME THE AUTOSAVE TARGET HERE EITHER
        # - same fix, same reason, as cmd_play's own `checkpoint_source` (see
        # its comment there for the whole story). `agent` has no screen to
        # print prose to, so this is said on stderr instead, the same channel
        # the opening "welcome" briefing already uses for anything the
        # protocol itself did not ask for.
        if settings.is_checkpoint(session):
            checkpoint_source = session
            session = _pick_session_filename(sim.civ.get("id") or "game")
            save_state(sim, session)
            sys.stderr.write(json.dumps(
                {"checkpoint_resumed":
                 "%s is a frozen checkpoint; nothing further is written back "
                 "into it. This run is autosaving to %s instead."
                 % (checkpoint_source, session)}) + "\n")
            sys.stderr.flush()

    def emit(obj, command_name=None):
        # THE JSON LINE IS UNCHANGED, ALWAYS, REGARDLESS OF --pretty. It is
        # written first, so a script reading only stdout sees byte-identical
        # output whether or not a human also asked for a readable view. The
        # readable view - if asked for - is a SEPARATE line on stderr, alongside the JSON, never
        # instead of it, so nothing that parses stdout has to change either.
        #
        # ALLOWED TO RAISE BrokenPipeError, on purpose. Every caller below
        # saves the session BEFORE calling this, so a pipe that closes mid-write
        # can only cost the reply, never the state change that produced it. See
        # the save-before-emit comment on the stdin loop for why that ordering
        # is load-bearing and not cosmetic.
        sys.stdout.write(json.dumps(obj) + "\n")
        sys.stdout.flush()
        if pretty:
            sys.stderr.write(render_pretty(command_name, obj) + "\n\n")
            sys.stderr.flush()

    # A player who has been told nothing but the path to this file must still be
    # able to start. On a new game the first line out is the whole briefing,
    # unasked, because there is nowhere else for them to learn it.
    # To STDERR, deliberately. stdout is the protocol and must stay exactly one
    # reply per command: an unsolicited line there shifts every index and
    # breaks anything parsing positionally.
    if not (session and os.path.exists(session)):
        sys.stderr.write(json.dumps(
            {"welcome": _agent_help(sim),
             "read this first": "This is the only instruction you get. Everything "
                                "else is here or in {\"cmd\":\"help\"}."},
            indent=1) + "\n")
        sys.stderr.flush()

    if args.script:
        try:
            cmds = json.load(open(args.script))
        except (OSError, ValueError) as error:
            emit({"ok": False, "error": "could not read script %r: %s" % (args.script, error)})
            return 1
        if not isinstance(cmds, list):
            emit({"ok": False, "error": "--script file must contain a JSON list of command objects"})
            return 1
        for command_obj in cmds:
            resp = _agent_dispatch(sim, nodes, command_obj)
            # SAVE BEFORE YOU SPEAK: see the stdin loop below for why. The
            # same reasoning applies here too - a --script run piped through
            # something that closes early must not lose state that already
            # happened, the same as the stdin loop below.
            if session:
                save_state(sim, session)
            try:
                emit(resp, command_obj.get("cmd") if isinstance(command_obj, dict) else None)
            except BrokenPipeError:
                try:
                    sys.stdout.close()
                except Exception:
                    pass
                return 0
        return 0

    # REPL over stdin/stdout: one JSON command per line in, one JSON object
    # per line out. This is the primary form; --script above is a thin
    # wrapper that replays a fixed list through the same dispatcher.
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            cmd = json.loads(line)
        except ValueError as error:
            try:
                emit({"ok": False, "error": "invalid JSON: %s" % error})
            except BrokenPipeError:
                break
            continue
        # The dispatcher guards non-object input and replies politely, but
        # cmd.get on a bare null, number, string or list is an
        # AttributeError, so THIS line needs its own isinstance guard too -
        # the dispatcher's guard does not cover it.
        try:
            resp = _agent_dispatch(sim, nodes, cmd)
        except Exception as error:                      # never lose a session to a bug
            resp = {"ok": False,
                    "error": "internal error handling that command: %s: %s. "
                             "The game is intact; try something else."
                             % (type(error).__name__, error)}
        # SAVE FIRST, THEN SPEAK - the same fix `play` already has (see its
        # own "SAVE FIRST, THEN SPEAK" comment). By this line
        # `_agent_dispatch` has already mutated `s` in memory - a `step`
        # command has already moved the calendar - so writing that to disk
        # cannot be left waiting on whether the reply is printed
        # successfully: piping `agent` through something like `head` closes
        # stdout, SIGPIPE kills the process on the write below, and
        # whatever had just happened must already be on disk by then, or it
        # is lost even though it genuinely happened. The game's own help
        # promises you can "close the terminal, anything" and come back; a
        # promise that holds only when nobody closes the pipe first is not
        # that promise.
        if session:
            save_state(sim, session)
        try:
            emit(resp, cmd.get("cmd") if isinstance(cmd, dict) else None)
        except BrokenPipeError:
            # Somebody closed the pipe. The game is saved; leave quietly, the
            # same way `play` does for the same reason.
            try:
                sys.stdout.close()
            except Exception:
                pass
            break
        if isinstance(cmd, dict) and cmd.get("cmd") == "quit":
            break
    return 0
