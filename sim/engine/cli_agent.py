"""The machine-playable protocol: `agent`.

Split out of engine/cli.py. `cmd_agent` is the JSON-in/JSON-out driver a
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


def cmd_agent(a):
    """Machine-playable driver: JSON in, JSON out. See the module docstring for
    the protocol. Runs in Sim.manual mode ALWAYS, regardless of any other flag:
    the entire point of this command is that a script chooses the research
    path, so the optimizer's own auto-start (step() 4b) is never in play here.
    That is different from `play --manual`, which is the same guarantee for a
    human at a keyboard; `agent` is that guarantee for a script or an LLM.
    """
    tree, prices, nodes, wages, goods = load()
    goal = _goal_for_session(a, tree, nodes)
    label, order, bounties = load_strategy(a.strategy, nodes, goal)
    # `run`/`compare`/`play` all take --mortal; `agent` silently did not, so
    # the founder was immortal in every scripted or JSON-driven game no
    # matter what was asked for - and the menu (below) was printing a
    # "--mortal" flag on its suggested agent command line that argparse would
    # have rejected outright, because the flag did not exist here at all.
    cfg = {"start_capital": STARTING_KITS[a.kit]["den"], "horizon_years": a.horizon,
           "immortal": not getattr(a, "mortal", False)}
    sim = Sim(nodes, order,
            DetRNG(a.seed) if getattr(a, "deterministic", False) else random.Random(a.seed),
            events=not a.no_events,
            cfg=cfg, civ=load_civ(_civ_for_session(a)), bounty_set=set(), manual=True)
    sim.goal = goal
    sim.done_year = {}
    sim.end_year = sim.cfg["start_year"] + a.horizon
    sim.fog = bool(getattr(a, "fog", False))
    sim.revealed = set()
    pretty = bool(getattr(a, "pretty", False))

    session = getattr(a, "session", None)
    checkpoint_source = None
    if session and os.path.exists(session) and not _is_claimed_slot(session):
        try:
            load_state(sim, session)
        except Exception as e:
            sys.stdout.write(json.dumps(
                {"ok": False, "error": "could not read the save file %r: %s" % (session, e)}
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

    def emit(obj, op=None):
        # THE JSON LINE IS UNCHANGED, ALWAYS, REGARDLESS OF --pretty. It is
        # written first, exactly as before pretty rendering existed, so a
        # script reading only stdout sees byte-identical output whether or
        # not a human also asked for a readable view. The readable view - if
        # asked for - is a SEPARATE line on stderr, alongside the JSON, never
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
            sys.stderr.write(render_pretty(op, obj) + "\n\n")
            sys.stderr.flush()

    # A player who has been told nothing but the path to this file must still be
    # able to start. On a new game the first line out is the whole briefing,
    # unasked, because there is nowhere else for them to learn it.
    # To STDERR, deliberately. stdout is the protocol and must stay exactly one
    # reply per command: an unsolicited line there shifts every index and breaks
    # anything parsing positionally, which it promptly did to my own tests.
    if not (session and os.path.exists(session)):
        sys.stderr.write(json.dumps(
            {"welcome": _agent_help(sim),
             "read this first": "This is the only instruction you get. Everything "
                                "else is here or in {\"cmd\":\"help\"}."},
            indent=1) + "\n")
        sys.stderr.flush()

    if a.script:
        try:
            cmds = json.load(open(a.script))
        except (OSError, ValueError) as e:
            emit({"ok": False, "error": "could not read script %r: %s" % (a.script, e)})
            return 1
        if not isinstance(cmds, list):
            emit({"ok": False, "error": "--script file must contain a JSON list of command objects"})
            return 1
        for command_obj in cmds:
            resp = _agent_dispatch(sim, nodes, command_obj)
            # SAVE BEFORE YOU SPEAK. See the stdin loop below for why: the same
            # ordering bug lived in both loops, and only the stdin one is what a
            # human normally drives, so it is the one the playtesters actually
            # hit, but a --script run piped through something that closes early
            # loses exactly the same way.
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
        except ValueError as e:
            try:
                emit({"ok": False, "error": "invalid JSON: %s" % e})
            except BrokenPipeError:
                break
            continue
        # The dispatcher guards non-object input and replies politely, and then
        # THIS line used to kill the process: cmd.get on a bare null, number,
        # string or list is an AttributeError. A playtester reopened the
        # "malformed input ends your game" class through the quit check, one
        # line after the guard that was supposed to prevent exactly that.
        try:
            resp = _agent_dispatch(sim, nodes, cmd)
        except Exception as e:                      # never lose a session to a bug
            resp = {"ok": False,
                    "error": "internal error handling that command: %s: %s. "
                             "The game is intact; try something else."
                             % (type(e).__name__, e)}
        # SAVE FIRST, THEN SPEAK - the same fix `play` already has (see its own
        # "SAVE FIRST, THEN SPEAK" comment), missing here until now. By this
        # line `_agent_dispatch` has already mutated `s` in memory - a `step`
        # command has already moved the calendar - so writing that to disk
        # cannot be left waiting on whether the reply is printed successfully.
        # Two testers found the gap independently, the same way: piping `agent`
        # through `head` closes stdout, SIGPIPE kills the process on the write
        # below, and whatever had just happened - for one of them, a hundred
        # years of `step` - was never written to the save at all, though it had
        # genuinely happened. The game's own help promises you can "close the
        # terminal, anything" and come back; a promise that holds only when
        # nobody closes the pipe first is not that promise.
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
