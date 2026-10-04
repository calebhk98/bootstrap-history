"""The command table: every accepted command name (and alias) mapped to the small handler that answers it, and the dispatcher that resolves names, guards fog, validates the command, and looks the handler up."""

import sim.engine.ui_port as ui_port
import importlib
import os
import pkgutil
import re

from sim.engine.ui_port import money_word
from sim.engine.ui_port import fuzzy_estimates, units

from .economy import _dashboard_snapshot
from . import command_registry
from .command_registry import command
from .compact import compact_state, compact_stuck, compact_why
from .help import _agent_help
from .nodes import NODE_NAME_NORM, _did_you_mean, _norm_name, _resolve_by_name
from sim.ui.memory import load_state, save_state
from .score import victory_report
from .state import (_agent_end_reason, _agent_state)
from .wave_summary import wave_summary
from . import step_progress
from .guidance import delay_kinds, delay_phrase
from .event_groups import group_disaster_events
from .event_severity import tag_events
from .step_alerts import step_alerts
from .step_stops import newly_startable_goal, severe_stop_reason
from .programme import programme_before_year
from .step_problems import route_nodes, route_startable, stalled_projects, step_problems
from .util import (_clean, _localise_money, _localise_words, _unsafe_path)

# Every dispatch_*.py module in this package registers its commands with
# @command when imported; they are found by name here, so a new module needs
# no edit. Each module's _cmd_* handlers are re-exported from this module so
# `from .proto.dispatch import _cmd_x` keeps working.
for _module_info in sorted(pkgutil.iter_modules([os.path.dirname(__file__)]),
                           key=lambda info: info.name):
    if _module_info.name.startswith("dispatch_"):
        _module = importlib.import_module("%s.%s" % (__package__, _module_info.name))
        globals().update({name: value for name, value in vars(_module).items()
                          if name.startswith("_cmd_")})


def id_commands():
    """Commands that name a technology. Under fog, NONE of them may say
    anything about one you have not heard of - including refusing it for a
    reason that describes it."""
    return command_registry.names_with_shape("tech")


def name_commands():
    """Commands whose `id` a typed NAME should resolve onto before anything
    else touches it: the id commands, plus those safe without the fog guard
    (you can only open something already done) that still take a name."""
    return command_registry.names_with_shape("tech", "tech_done")


@command("save", shape="file", group="game",
         summary="write the game to a file",
         usage=["save <file>", '{"cmd":"save","file":"mygame.json"}'],
         options={"<file>": "a file name (a relative name for scripts; typed in play, any path)"},
         description="Writes the whole game. See the sittings topic for scripting.")
def _cmd_save(sim, nodes, cmd, ended):
    command = cmd.get("cmd")  # this handler serves both "save" and "load"; see below
    path = cmd.get("file") or cmd.get("path")
    if not isinstance(path, str) or not path:
        return {"ok": False, "error": 'give a filename, e.g. {"cmd":"save","file":"mygame.json"}'}
    # A SAVE FILE IS A SAVE FILE, not a way to write anywhere on the disk:
    # an absolute path could write into /etc/, and an unguarded relative
    # path could scatter files through the repository root. The game is
    # played by pointing agents and scripts at it; "name a path and I will
    # write there" is not a thing it should offer.
    bad = _unsafe_path(path)
    if bad:
        return {"ok": False, "error": bad}
    try:
        if command == "save":
            save_state(sim, path)
            return {"ok": True, "saved": path, "year": sim.year}
        load_state(sim, path)
        return {"ok": True, "loaded": path, "year": sim.year}
    except Exception as error:
        return {"ok": False, "error": "could not %s %r: %s" % (command, path, error)}



@command("step", group="projects", aliases=("n", "next", "wait", "year"),
         summary="let time pass",
         usage=["step", "step <years>"], options={"<years>": "how many years (default 1)"},
         description="Advances the calendar and reports what completed and happened. "
                     "Founder hours do not bank between years.")
def _cmd_step(sim, nodes, cmd, ended):
    # Must refuse to advance the clock once the run has ended: doing so
    # silently would look identical to a working game that has simply
    # stopped progressing.
    if ended:
        return {"ok": False, "error": "the run has ended (%s); time cannot advance. "
                                      "Use {\"cmd\":\"state\"} to see the final position."
                                      % ended}
    raw_years = cmd.get("years", 1)
    # `True` is an int in Python and stepped one year silently. A player who
    # sends true meant something, and it was not that.
    if isinstance(raw_years, bool):
        return {"ok": False, "error": "years must be a number, not true or false"}
    try:
        years = int(raw_years)
    except (TypeError, ValueError):
        return {"ok": False, "error": "years must be an integer"}
    # 0.999 was rejected and 1.99 was silently floored to one year, which is
    # the worst pair of answers to give: the boundary is invisible and the
    # accepted side quietly does something other than what was asked. A
    # calendar advances in years; say so, rather than rounding on the
    # player's behalf and calling it "accepted".
    if float(raw_years) != years:
        return {"ok": False,
                "error": "years must be a whole number of years; %r is not. "
                         "Nothing was changed." % raw_years}
    if years < 1:
        return {"ok": False, "error": "years must be >= 1"}
    # Nothing is gained by accepting a number of years larger than the
    # game can contain: a typo that silently ends your run without saying
    # so is the worst kind of accepted input.
    left = max(0, sim.end_year - sim.year)
    if years > left:
        return {"ok": False,
                "error": "there are only %d years left before the horizon at "
                         "%d. Ask for %d or fewer, or fewer still if you want "
                         "to see what happens on the way."
                         % (left, sim.end_year, left)}
    # WARN BEFORE, NOT AFTER, A MULTI-YEAR STEP WASTES HOURS. "Founder-
    # hours do not bank. A player can have long calendar-floor projects
    # running, use `step 5`, and unintentionally throw away thousands of
    # usable founder-hours if they did not fill the portfolio first" -
    # from a player who had already won the game. Checked against THIS
    # year only, before any of the requested years run: free_hours_
    # going_unused is the exact same test `state` already uses (every
    # active project already calendar-locked, or nothing active at all,
    # with a real pool still free) - read here, not recomputed, so this
    # warning and that field can never disagree about what "idle" means.
    # Non-blocking: it says so and proceeds, it does not refuse the step.
    multi_year_hours_warning = None
    lone_dependencies = sim.labour.sole_supervisors() if years > 1 else []
    if years > 1:
        _pre_state = _agent_state(sim, nodes)
        _idle_note = _pre_state.get("free_hours_going_unused")
        if _idle_note:
            # A STARTABLE PROJECT HAS TO EXIST, or the warning would be
            # telling a player to do something they cannot do. Early
            # exit on the first hit - see `stuck`'s own _startable for
            # the same full-tree scan, accepted there for the same
            # reason: nothing cheaper tells you whether ANYTHING at all
            # is startable right now.
            _could_start = next(
                (node_id for node_id in nodes if node_id not in sim.done and node_id not in sim.active
                 and sim.can_start(node_id)), None)
            if _could_start:
                # DOES IT ACTUALLY BANK? Checked against step()'s own
                # code, not assumed: core.py's step() computes `pool`
                # fresh every year from director_pool() minus this
                # year's commitments, and whatever of it 5b's wage-work
                # branch does not spend either is simply never written
                # anywhere - no field on `self` carries a "leftover
                # hours" balance into the next call. It does not partly
                # bank; it does not bank at all.
                multi_year_hours_warning = (
                    "before stepping %d years: %s founder-hours this "
                    "year are already going to waste, and '%s' is one "
                    "thing you could start today that would use some of "
                    "them. Founder-hours do not bank at all: step() "
                    "draws a fresh pool every year, and what goes "
                    "unused this year is simply gone, never carried "
                    "into the next one - so 'step %d' spends this "
                    "year's slack exactly as idle as it is right now, "
                    "%d more times over, unless you start something "
                    "first. Running projects wait on: %s. Proceeding anyway."
                    % (years, "{:,.0f}".format(
                           _pre_state.get("founder_hours_available") or 0.0),
                       nodes[_could_start]["name"], years, years,
                       delay_phrase(delay_kinds(sim, nodes))))
    # LOST, not only completed: a game whose only score is what you have
    # built has to report subtraction at least as loudly as addition, so
    # anything that drops out of `done` during a multi-year step has to be
    # named here, the same way an arrival is.
    # STOP WHEN SOMETHING IT WARNED ABOUT ACTUALLY HAPPENS, rather than
    # running the rest of the years asked for on top of it: a `step 12`
    # that carries "CLOSE TO THE LIMIT ... while it is still your choice"
    # (see economy.warn_near_the_limit) straight through to CREDIT
    # EXHAUSTED must not spend the REMAINING years of the same call
    # compounding arrears with nobody able to react - the choice the
    # warning promises must still be theirs when the reply comes back. A
    # request for N years is not a promise to hide what happens in year 1
    # until year N has also gone by. So this breaks the loop, not only the
    # request, the moment it fires. The same applies to a mortal founder's
    # own death: a `step 60` that lands on it must not run on past it far
    # enough to also trip the no-successor catastrophe before the player
    # gets a turn to react.
    # MATCHED CASE-INSENSITIVELY BELOW, because this is prose and prose
    # gets rewritten: a case-sensitive match against one exact
    # capitalisation would silently stop matching the moment that prose is
    # edited, costing the step its stop and the reply its death field.
    # CLOSE TO THE LIMIT BELONGS IN THE STOP-MARKER TUPLE TOO: it is the
    # one event that still leaves a player options, so it is the one this
    # most needs to interrupt for - the fatal events need it least, since
    # there is nothing left to choose by the time they fire. Leaving it
    # out would let a batched step run straight past "stop a project...
    # while it is still your choice" and only break years later on the
    # fatal CREDIT EXHAUSTED that warning exists to prevent.
    _STEP_STOP_MARKERS = ("CREDIT EXHAUSTED", "FOUNDER DIES",
                          "CLOSE TO THE LIMIT")
    completed, lost, events = [], [], []
    disasters = []
    founder_died_this_step = None
    stopped_early = None
    end_year = sim.end_year
    ran = 0
    goal_before = sim.goal_snapshot()
    goal_year_before = sim.goal_year
    route = route_nodes(sim) if years > 1 else set()
    snapshots = []
    programme_log = []
    for _ in range(years):
        if sim.dead_reason or sim.year >= end_year:
            break
        before_done, before_log = set(sim.done), len(sim.log)
        # FOR `changes`: what a bare node-or-concern-set diff cannot tell
        # you on its own - WHEN it changed. revealed/operating only ever
        # grow or lose members silently; snapshotting the sets either
        # side of this one year's step() is the one place that year's
        # own diff can still be taken, cheaply, before it is gone.
        before_revealed = set(getattr(sim, "revealed", set()))
        before_operating = set(sim.operating)
        _arrival_snapshot = None if ui_port.dashboard_history(sim) else _dashboard_snapshot(sim)
        stalled_before = set(stalled_projects(sim))
        goal_was_startable = sim.goal in nodes and sim.can_start(sim.goal)
        population_before = sim.population.total
        programme_log.extend(programme_before_year(sim, nodes))
        sim.step()
        ran += 1
        population_change = sim.population.total / population_before - 1.0 if population_before > 0 else 0.0
        sim.state.population.population_change_last_year = round(population_change, 4)
        hist = ui_port.dashboard_history(sim)
        if hist is None:
            hist = []
            ui_port.set_dashboard_history(sim, hist)
        if not hist:
            # the arrival year is the first point `changes` can measure from
            hist.append({**_arrival_snapshot, "revealed_added": [], "concerns_opened": [],
                         "concerns_closed": [], "completed": []})
        _snap = _dashboard_snapshot(sim)
        _snap["revealed_added"] = sorted(
            set(getattr(sim, "revealed", set())) - before_revealed)
        _snap["concerns_opened"] = sorted(sim.operating - before_operating)
        _snap["concerns_closed"] = sorted(before_operating - sim.operating)
        _snap["completed"] = sorted(sim.done - before_done)
        hist.append(_snap)
        if route:
            snapshots.append({**_snap, "route_startable": route_startable(sim, route)})
        else:
            snapshots.append(_snap)
        step_progress.after_year(sim, {"year": sim.year, "capital": _snap["capital"],
                                       "completed": len(_snap["completed"]),
                                       "closed": len(_snap["concerns_closed"]), "years_asked": years,
                                       "population_change": population_change})
        # sorted(), because this is a set difference and a set of strings
        # iterates in an order that depends on PYTHONHASHSEED. Two runs of
        # the same game with the same seed reported the same completions in
        # different orders, which is a small thing that makes the protocol's
        # own output impossible to diff. Caught by fingerprinting the
        # engine before and after being split into modules: every number
        # matched and this list did not.
        for node_id in sorted(sim.done - before_done):
            # YOURS OR THE SOCIETY'S: anything in `granted` is this
            # civilisation's own work, credited free, and has to be
            # marked apart from a project the player paid for and waited
            # years on, or the same "COMPLETED" line reads as the player
            # having built something on turn one they never started.
            completed.append({"id": node_id, "name": nodes[node_id]["name"],
                              "year": sim.done_year.get(node_id),
                              "granted": node_id in sim.granted,
                              "kind": ("granted" if node_id in sim.granted
                                       else "concern" if sim.is_venture(node_id)
                                       else "technology")})
        for node_id in sorted(before_done - sim.done):
            lost.append({"id": node_id, "name": nodes[node_id]["name"], "year": sim.year,
                         "can_be_restored": node_id in getattr(sim, "mothballed", set())})
        _this_year = sim.log[before_log:]
        if getattr(sim, "disaster_this_year", None):
            disasters.append(sim.disaster_this_year)
        for year, message in _this_year:
            events.append({"year": year, "message": message})
            if "founder dies" in message.lower():
                _age = re.search(r"aged about (\d+)", message)
                _age_n = int(_age.group(1)) if _age else None
                founder_died_this_step = {"year": year, "aged_about": _age_n}
                # SAVED, NOT ONLY LOGGED - see _founder_death_info's own
                # comment on why the log alone cannot be trusted to
                # survive a save and a resume.
                ui_port.set_founder_death(sim, _age_n, year)
        # AND STOP THE YEAR YOU WIN: reaching the goal does not end the
        # run, so without this a `step 50` that crosses the finish line
        # would run on for the remaining years and mention it only in
        # passing. It is the one moment in a run most worth handing back.
        if ran < years and sim.goal_year == sim.year:
            stopped_early = ("stopped after %d of the %d years you asked "
                             "for: you reached it. Step again when you "
                             "have had a look around."
                             % (ran, years))
            break
        if ran < years and any(marker.lower() in message.lower() for _, message in _this_year
                               for marker in _STEP_STOP_MARKERS):
            stopped_early = ("stopped after %d of the %d years you asked "
                             "for: something happened that you warned "
                             "yourself about and should see before more "
                             "time passes. Step again when you are ready."
                             % (ran, years))
            break
        severe_reason = severe_stop_reason(
            [{"message": message} for _, message in _this_year],
            [nodes[node_id]["name"] for node_id in _snap["concerns_closed"]
             if sim.staff_closure_age(node_id) is not None],
            sorted(set(stalled_projects(sim)) - stalled_before),
            [name for name in [newly_startable_goal(sim, goal_was_startable)] if name])
        if ran < years and severe_reason:
            stopped_early = ("stopped after %d of the %d years you asked for: %s. "
                             "Step again when you have had a look." % (ran, years, severe_reason))
            break
    out = dict(ok=True, completed=completed, lost=lost, events=events)
    if programme_log:
        out["programme"] = programme_log
    if years > 1 and lone_dependencies:
        out["multi_year_staffing_warning"] = (
            "before stepping %d years: %s each rest on one person; a single departure closes them. "
            "'keep <id> staffed' or 'policy auto_replace_foreman on' protects them."
            % (years, ", ".join(row["concern"] for row in lone_dependencies[:3])))
    out["alerts"] = step_alerts(
        events, lost,
        [nodes[node_id]["name"] for snap in snapshots for node_id in snap.get("concerns_closed", ())],
        founder_died_this_step, sim.goal_year if goal_year_before is None else None,
        stopped_early, sim.state.population.population_change_last_year,
        staffing_line=sim.staffing_closure_summary())
    summary = wave_summary(completed, events, goal_before, sim.goal_snapshot())
    for disaster in disasters:
        out["events"] = group_disaster_events(out["events"], disaster["name"], disaster["messages"])
    out["events"] = tag_events(out["events"])
    if summary:
        out["summary"] = summary
    problems = step_problems(ran, snapshots, events, stalled_projects(sim))
    if problems:
        out["problems"] = problems
    if goal_year_before is None and sim.goal_year is not None:
        out["victory"] = victory_report(sim, nodes)
    if founder_died_this_step:
        out["the_founder_died_this_step"] = founder_died_this_step
    if stopped_early:
        out["stopped_early"] = stopped_early
    if multi_year_hours_warning:
        out["multi_year_hours_warning"] = multi_year_hours_warning
    out.update(_agent_state(sim, nodes))
    return out



@command("quit", shape="bare", group="game", aliases=("q", "exit", "bye"),
         summary="stop",
         usage=["quit"], options={},
         description="Ends the session.")
def _cmd_quit(sim, nodes, cmd, ended):
    return {"ok": True, "bye": True}




# "load" shares the save handler.
command_registry.register_command(
    "load", group="game", shape="file", summary="read a game from a file",
    usage=["load <file>"], options={"<file>": "a file written by save"},
    description="Replaces the current game with a saved one.",
    handler=_cmd_save)

# Every command word and alias mapped to its handler, from the registry.
_AGENT_DISPATCH_TABLE = command_registry.handlers()

# Every command name, read from the registry.
KNOWN_COMMANDS = tuple(command_registry.COMMANDS)

# 'compact' replaces the reply with a short summary (see compact.py); a
# command not listed here falls through untouched.
_COMPACT_BUILDERS = {
    "why": compact_why,
    "state": compact_state,
    "step": compact_state,
    "stuck": compact_stuck,
}


def _add_compact_fields(command, out, sim=None, nodes=None):
    build = _COMPACT_BUILDERS.get(command)
    return build(out, sim, nodes) if build else out


def _agent_dispatch(sim, nodes, cmd):
    """Every reply, in the money of the place you are standing in."""
    _out = _agent_dispatch_inner(sim, nodes, cmd)
    if sim.fuzzy_estimates and isinstance(cmd, dict):
        _entry = command_registry.resolve(cmd.get("cmd") if isinstance(cmd.get("cmd"), str) else "")
        _out = fuzzy_estimates.fuzz_reply(sim, _entry["name"] if _entry else None, cmd, _out)
    _out = _localise_money(_out, money_word(sim.civ))
    _out = _localise_words(_out, ((sim.civ.get("local_words") or {}).get("pairs")))
    _out = units.add_display(_out, sim)
    # Compact runs last so the short summary already carries the local vocabulary.
    if isinstance(cmd, dict) and cmd.get("compact"):
        _out = _add_compact_fields(cmd.get("cmd"), _out, sim, sim.nodes)
    return _out


def _agent_dispatch_inner(sim, nodes, cmd):
    nodes = sim.nodes   # the tree in this civilisation's coin
    if not isinstance(cmd, dict) or "cmd" not in cmd:
        return {"ok": False, "error": "each line must be a JSON object with a 'cmd' field, "
                                      "e.g. {\"cmd\":\"state\"}"}
    # A NAME RESOLVES TO AN ID, BEFORE ANYTHING ELSE READS IT: every screen in
    # this game prints the human NAME - "Horizontal loom" - while every
    # command that acts on a technology takes only the machine id -
    # "tex_horizontal_loom". This has to run before the fog guard just below: that guard reads cmd["id"] straight off
    # the command, so a name that resolves to exactly one id must already BE
    # that id by the time the guard looks at it, or a perfectly good name
    # would be refused as something the player had never heard of. `id` still
    # takes a raw id unchanged - this only fires when what was given is NOT
    # already one, so scripts and the `agent` protocol lose nothing.
    if (isinstance(cmd.get("cmd"), str) and isinstance(cmd.get("id"), str)
            and cmd["cmd"].strip().lower() in name_commands()
            and cmd["id"] not in nodes):
        _name_cands = _resolve_by_name(cmd["id"])
        if sim.fog:
            # ONLY WHAT THE PLAYER HAS ACTUALLY HEARD OF. Two nodes can share
            # a name where one is built and the other is still beyond the
            # fog; handing back the hidden one as a candidate to disambiguate
            # between is exactly the leak the fog guard below exists to close,
            # so the filter runs before a player ever sees the list, not after.
            _name_memo = {}
            _goal = sim.goal
            # THE GOAL'S NAME GETS THE SAME NARROW EXCEPTION ITS ID ALREADY
            # HAS, on `why` alone - see the fog guard's own comment on
            # _goal_why just below. Without this, a player who only ever
            # learned the goal's NAME (under fog its id is never shown; see
            # _agent_state's "goal" field) typed it into `why` and was told
            # "you have never heard of any such thing" about the one thing
            # they were told by name on arrival. It is gated on an EXACT match
            # of the goal's own name, not the prefix/substring tiers: a vague
            # guess like "transistor" must stay refused, the same way
            # `_did_you_mean` already refuses to suggest the goal for one.
            _exact_here = NODE_NAME_NORM.get(_norm_name(cmd["id"]), ())
            _op_lc = cmd["cmd"].strip().lower()
            _name_cands = [
                node_id for node_id in _name_cands
                if sim.is_visible(node_id, _memo=_name_memo)
                or (node_id == _goal and _op_lc == "why" and node_id in _exact_here)]
        if len(_name_cands) == 1:
            cmd = dict(cmd, id=_name_cands[0])
        elif len(_name_cands) > 1:
            _name_cands = sorted(_name_cands, key=lambda k: (nodes[k]["name"], k))
            return {"ok": False,
                    "error": ("more than one thing is called that; say which "
                              "by id: %s%s"
                              % (", ".join("%s (%s)" % (node_id, nodes[node_id]["name"])
                                           for node_id in _name_cands[:10]),
                                 " and %d more" % (len(_name_cands) - 10)
                                 if len(_name_cands) > 10 else ""))}
        # Otherwise: no match by name either. Fall through with cmd["id"]
        # untouched, so the ordinary unknown-id handling further down - and
        # the fog guard immediately below it - answer it exactly as they
        # already do for a mistyped id, did-you-mean included.
    # ONE GUARD, FOR EVERY COMMAND THAT TAKES AN ID: a command that checks
    # prerequisites before visibility can leak hidden ids by naming them
    # in a refusal, and crawling that error recursively can recover the
    # entire hidden dependency graph, with fog on the whole time.
    # Patching one command alone would leave the next command that grows
    # an id to make the same mistake, so the check lives here, once,
    # before any handler sees the id.
    if sim.fog and isinstance(cmd.get("cmd"), str):
        _op = cmd["cmd"].strip().lower()
        _node_id = cmd.get("id")
        # THE SAME ANSWER WHETHER OR NOT IT EXISTS: refusing an unheard-of
        # node with "you have never heard of that" and a nonexistent one
        # with "unknown node 'X'" would make the two distinguishable, and
        # that difference IS the tree - asking about any name at all and
        # getting a true answer to whether it is real is a way to view
        # the whole tree. `help fog` promises there is no such way.
        # THE ONE EXCEPTION IS `why` ON THE GOAL: the status line names the
        # goal every single turn - "Aiming at: Point-contact transistor" -
        # so refusing `why point_contact_transistor` with "you have never
        # heard of any such thing" would be a contradiction, not fog.
        # It is `why` alone that gets the exception, and not is_visible
        # itself, because making the goal fully visible would reopen the
        # exact exploit this guard exists to close: `bounty` on the goal
        # would then print its missing prerequisites by name, recoverable
        # recursively into the hidden dependency graph. `why` under fog
        # already says only "this needs N other things you have not heard
        # of yet", which is the honest answer.
        _goal_why = (_op == "why" and _node_id == sim.goal)
        if _op in id_commands() and isinstance(_node_id, str) and not _goal_why and (
                _node_id not in nodes or not sim.is_visible(_node_id)):
            if _node_id == sim.goal:
                # You know its name; you were handed it on arrival. Telling you
                # that you have never heard of the thing you are aiming at, and
                # then guessing you meant fin_contract_law, is absurd on its
                # face. Saying nothing MORE than "not yet" leaks nothing.
                return {"ok": False,
                        "error": "that is what you are aiming at, and you cannot "
                                 "act on it yet: everything it rests on is still "
                                 "beyond what you have heard of. 'why %s' is all "
                                 "of it you can see from here." % _node_id}
            near = _did_you_mean(_node_id, nodes, sim=sim)
            # SAY WHERE THE SUGGESTIONS COME FROM: the suggestions are
            # already filtered through is_visible, so nothing hidden is
            # ever named - but listing ids right after saying "nothing
            # tells you what lies beyond that" would read as a
            # contradiction, a fog leak that is not actually one. The
            # sentence has to say which of the two the suggestions are:
            # things already known.
            return {"ok": False,
                    "error": "you have never heard of any such thing. You know "
                             "what you have built and what you could begin next; "
                             "nothing tells you what lies beyond that.%s"
                             % ((" Among the things you DO know, did you mean: "
                                 + ", ".join(near)) if near else "")}
    command = cmd.get("cmd")
    ended = _agent_end_reason(sim)

    if command in ("help", "?", "commands"):
        return {"ok": True, "help": _agent_help(sim, cmd.get("topic"))}

    # One central guard rather than five: an id that is not a string (a
    # dict or list, say) would crash on `k not in nodes` with an
    # unhashable-type TypeError wherever it first reaches that test,
    # losing the whole session. A malformed command must cost you the
    # command, never the game.
    if "id" in cmd and not isinstance(cmd["id"], str):
        return {"ok": False,
                "error": "id must be a name in quotes, not %s. Nothing was changed."
                         % type(cmd["id"]).__name__}

    # NaN and Infinity, anywhere in the command, before anything is touched.
    bad = sorted(field for field, value in cmd.items() if not _clean(value))
    if bad:
        return {"ok": False,
                "error": "%s must be a real number; NaN and Infinity are not "
                         "quantities. Nothing was changed." % ", ".join(bad)}

    _handler = command_registry.handlers().get(command)
    if _handler is not None:
        return _handler(sim, nodes, cmd, ended)

    # THE LIST MUST NOT GO STALE. This was ten commands hard-coded into a
    # string while the game had grown to twenty-four, so a player who mistyped
    # was handed a list that silently omitted labour, hire, train, commission,
    # money, risk, policy, quote, close, mothball, restore, work and bribe.
    # A help message that is wrong is worse than none, because it is believed.
    return {"ok": False,
            "error": "unknown cmd %r. Use one of: %s. %s"
                     % (command, ", ".join(command_registry.COMMANDS),
                        'Or {"cmd":"help"} for what each one does.')}
