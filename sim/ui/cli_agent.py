"""The machine-playable protocol: `agent`.

`cmd_agent` is the JSON-in/JSON-out driver a
script or another process talks to - see sim/PROTOCOL.md for
the protocol table. It deliberately does not call `_apply_display_prefs` (a
human terminal's own cosmetic settings have no business changing what a
script sees - see that function's own docstring in cli_common.py) and so needs
none of cli_interactive.py's display machinery, only the session-resolution
helpers cli_common.py also hands to the human-facing `play` command.
"""
import json, os, random, sys

from sim.engine.ui_port import load, load_civ
from sim.engine.ui_port import Sim
from . import replay
from .protocol import _agent_dispatch, _agent_end_reason, _agent_help, load_state, render_pretty, save_state
from .memory import save_session
from .save_policy import SavePolicy
from sim.engine.ui_port import settings, units
from sim.ui.proto import step_progress

# Session helpers shared with cli_interactive.py live in cli_common.py.
from .cli_common import _civ_for_session, _goal_for_session, _is_claimed_slot, _pick_session_filename
from sim.engine import ui_port
from sim.engine.ui_port import DetRNG, EconomyNotOpened, load_strategy


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
    cfg = {"start_kit": args.kit, "horizon_years": args.horizon,
           "immortal": not getattr(args, "mortal", False)}
    from sim.engine.ui_port import normal_seed
    seed = normal_seed(args.seed)
    session = getattr(args, "session", None)
    resuming = bool(session and os.path.exists(session) and not _is_claimed_slot(session))

    def build(defer_economy):
        # a game that is about to load a save leaves its own economy unopened: the save holds it
        built = Sim(nodes, order,
                    DetRNG(seed) if getattr(args, "deterministic", False) else random.Random(seed),
                    events=not args.no_events,
                    cfg=cfg, civ=load_civ(_civ_for_session(args)), bounty_set=set(), manual=True,
                    defer_economy=defer_economy)
        built.seed = seed
        built.session_seat = getattr(args, "seat", None)
        ui_port.begin_game(built, goal, built.view("game_config")()["start_year"] + args.horizon,
                           bool(getattr(args, "fog", False)), bool(getattr(args, "fuzzy_estimates", False)))
        return built

    sim = build(resuming)
    pretty = bool(getattr(args, "pretty", False))

    checkpoint_source = None
    if resuming:
        try:
            try:
                load_state(sim, session)
            except EconomyNotOpened:
                sim = build(False)     # the save cannot stand in for the economy's opening; build the game the long way
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
            session = _pick_session_filename(sim.view("civilisation")().get("id") or "game")
            save_session(sim, session)
            sys.stderr.write(json.dumps(
                {"checkpoint_resumed":
                 "%s is a frozen checkpoint; nothing further is written back "
                 "into it. This run is autosaving to %s instead."
                 % (checkpoint_source, session)}) + "\n")
            sys.stderr.flush()

    # after the load, so a resumed game keeps its carried routes
    route_file = getattr(args, "known_routes", None)
    if route_file:
        if not sim.view("fog_of_war")():
            sys.stderr.write(json.dumps({"known_routes": replay.fog_off_note()}) + "\n")
        else:
            applied = replay.apply_known_routes(sim, replay.read_known_routes(route_file), nodes)
            sys.stderr.write(json.dumps({"known_routes_carried": len(applied)}) + "\n")

    def emit(obj, command_name=None):
        emit_reply(obj, command_name, sim.view("civilisation")(), pretty)

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

    step_progress.set_after_year(step_progress.commit_and_report(session, sys.stderr))
    policy = SavePolicy(session, getattr(args, "save_interval", 0))
    try:
        return _agent_loop(sim, nodes, args, emit, policy)
    finally:
        policy.flush(sim)


def emit_reply(obj, command_name, civ, pretty):
    """Write one reply: the JSON line on stdout, always the same whatever `pretty` says, then, if asked, the
    readable rendering on stderr (in the civilisation's display units) so a script reading only stdout never
    sees the difference. Raises BrokenPipeError when stdout closes; callers save the session before calling."""
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()
    if pretty:
        units.set_civ_defaults(civ)
        try:
            sys.stderr.write(render_pretty(command_name, obj) + "\n\n")
        finally:
            units.set_civ_defaults(None)
        sys.stderr.flush()


def _agent_loop(sim, nodes, args, emit, policy):
    """Run the script or stdin commands of `cmd_agent`; `policy` decides when the session file is written."""
    session = policy.session
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
            policy.after_command(sim, command_obj, ended=bool(_agent_end_reason(sim)))
            if session and _agent_end_reason(sim):
                replay.record_end_of_run(sim, session)
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
        # `_agent_dispatch` has already mutated `sim` in memory - a `step`
        # command has already moved the calendar - so writing that to disk
        # cannot be left waiting on whether the reply is printed
        # successfully: piping `agent` through something like `head` closes
        # stdout, SIGPIPE kills the process on the write below, and
        # whatever had just happened must already be on disk by then, or it
        # is lost even though it genuinely happened. The game's own help
        # promises you can "close the terminal, anything" and come back; a
        # promise that holds only when nobody closes the pipe first is not
        # that promise.
        policy.after_command(sim, cmd, ended=bool(_agent_end_reason(sim)))
        if session and _agent_end_reason(sim):
            replay.record_end_of_run(sim, session)
        try:
            emit(resp, cmd.get("cmd") if isinstance(cmd, dict) else None)
        except (BrokenPipeError, OSError):
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
