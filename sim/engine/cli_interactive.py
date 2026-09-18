"""The interactive game: main menu, the New Game wizard, civilisation
listing, and the game loop (`play`'s REPL).

Split out of engine/cli.py. This is the human-facing front door - everything
here is reached by a person typing at a keyboard, never by `agent`'s JSON
protocol (see cli_agent.py) and never by the batch/analysis commands (which
stayed in cli.py itself, or moved to cli_analysis.py).

Kept together in ONE module, rather than split further into "game loop" and
"new game/menu" pieces, because the two call each other directly and
repeatedly: `cmd_play` calls `cmd_menu` and `_new_game` when a player types
"menu" or "new" mid-game, and `cmd_menu`/`_load_game` call `cmd_play` right
back to start the game they just picked or loaded. Splitting that mutual
recursion across two leaf modules would need the same module-attribute
indirection `engine/cli.py`'s own docstring warns about for `Sim` - not
worth it for a boundary the code itself does not actually respect.

Mid-game save/load browsing (listing what is on disk, printing one row of
that listing, and switching this session to a chosen save) DID split out
cleanly, to cli_interactive_saveload.py - verified with the `ast` module by
walking the call graph among the original file's 15 top-level functions,
not by reading names. That module is a true leaf with respect to this one:
every cross-module call in the original file ran from a function that
stayed here to one that moved there, and none the other way. `_load_game`
looks like it belongs with the save/load group it browses, and almost
moved there, but it ends by calling `cmd_play` right back (see `_load_game`
below) - the same mutual recursion described above for `cmd_menu` and
`_new_game` - so it stayed on this side rather than reopening a two-way
import between the two modules. `_load_civ_list` moved the other way for
the same reason: it is called from here (`cmd_menu`, `cmd_play`) but also
from `_save_listing` over there, so keeping it here would have made the
save/load module import back from this one.
"""
import json, os, random, sys, time

from .data import (CIVDIR, closure, critical_path, DEFAULTS, goal_catalog,
                   load, load_civ, load_geography, money_short, money_word,
                   STARTING_KITS, win_condition_describe)
from .core import Sim
from . import protocol as _protocol
from . import settings
from .protocol import (_agent_dispatch, _agent_end_reason, final_report,
                       load_state, parse_typed, render_final, render_pretty,
                       save_state)
from constants import declare

# Session/session-file and display-preference helpers live in cli.py because
# cli_agent.py needs the session helpers too, and _wrap/_apply_display_prefs
# mutate a module-level _DISPLAY_WIDTH that only means what it says while it
# stays beside the function that writes it - see cli.py's own comments on
# both for the full reasoning.
from .cli import (DetRNG, ENDLESS_HORIZON_YEARS, HORIZON_MODES,
                  _apply_display_prefs, _civ_for_session, _goal_for_session,
                  _is_claimed_slot, _is_endless_horizon, _pick_session_filename,
                  _resolve_horizon, _wrap, load_strategy)

# Save/load browsing and the civilisation list live in
# cli_interactive_saveload.py - see this file's own docstring for why that
# split, and not some other one, keeps the import direction one-way.
from .cli_interactive_saveload import (_ingame_load, _ingame_save_milestone,
                                       _ingame_saves, _load_civ_list,
                                       _print_save_row, _save_listing)


def cmd_play(a):
    """The game, typed, for a person at a keyboard.

    This used to be its own little REPL with six commands of its own - next
    year, available, status, start, stop, quit - and its own copy of what each
    one meant. Everything built since (money, hire, fire, train, work,
    commission, labour, policy, quote, close, mothball, restore, bribe, risk,
    save, load) went into the JSON protocol and none of it into here, so the
    human front door showed a fraction of the game and the menu's answer was to
    put a person in front of a JSON prompt.

    It now parses a typed line into the SAME command the JSON protocol takes
    (protocol.parse_typed) and hands it to the SAME dispatcher (_agent_dispatch),
    printing the readable rendering the --pretty path already uses. There is no
    second implementation to fall behind: a command added to the protocol is
    typeable here the day it is added.

    It is also always manual. The old default mode let the optimizer keep
    starting things regardless of what you typed, and its own docstring called
    that "advisory, not a real choice". A front door should not be the mode
    where your choices do not count; `run --trace` is still the way to watch
    the optimizer work.
    """
    # THE APPLICATION'S OWN PREFERENCES, APPLIED ONCE, HERE - not only from
    # the menu. `play` typed directly (no menu at all) is still a human at a
    # keyboard, on their own terminal, and display width/rows-per-page/
    # whether the tutorial prints are preferences about THAT, not about
    # which flags were passed - see _apply_display_prefs and settings.py's
    # module docstring. None of this touches `agent`. Named app_cfg, not
    # cfg: `cfg` below is the Sim's own config dict (immortal/horizon_years/
    # start_capital) and already existed under that name; the two must not
    # collide.
    app_cfg = _apply_display_prefs()
    tree, prices, nodes, wages, goods = load()
    goal = _goal_for_session(a, tree, nodes)
    label, order, bounties = load_strategy(a.strategy, nodes, goal)
    session = getattr(a, "session", None)
    # HOW MANY YEARS THIS SITTING GETS. Ordinarily just the --horizon flag,
    # but a save the New Game wizard started or the in-game 'options' command
    # touched remembers its own horizon between sittings - see
    # _resolve_horizon and settings.py's module docstring for why that is not
    # simply part of the save file. A flag typed by hand always wins.
    horizon = _resolve_horizon(a, session)
    cfg = {"immortal": not getattr(a, "mortal", False),
           "horizon_years": horizon}
    kit = getattr(a, "kit", None)
    if kit:
        cfg["start_capital"] = STARTING_KITS[kit]["den"]
    sim = Sim(nodes, order,
            DetRNG(a.seed) if getattr(a, "deterministic", False) else random.Random(a.seed),
            events=True, bounty_set=set(),
            manual=True, civ=load_civ(_civ_for_session(a)), cfg=cfg)
    sim.goal = goal
    sim.done_year = {}
    sim.end_year = sim.cfg["start_year"] + horizon
    sim.fog = bool(getattr(a, "fog", False))
    sim.revealed = set()
    # The reader is a person typing words, so the worked examples inside every
    # reply should be words too. See protocol.to_typed_hints.
    _protocol.TYPED_HINTS = True
    _protocol.MONEY_SHORT = money_short(sim.civ)

    # A --session THAT DOES NOT EXIST IS A TYPO, NOT AN INVITATION. Naming a
    # save file that is not there used to start a brand new default game -
    # Rome 100 AD, whatever you were playing - and then write it over that
    # filename on the first command. A tester nearly lost a forty-year England
    # run to a mistyped path. Starting a new game is what you do by naming a
    # civilisation, so require that to be explicit.
    if session and not os.path.exists(session) and not getattr(a, "civ", None):
        print("there is no save at %r, and no --civ given, so I do not know "
              "what game you meant. To resume, check the path; to start a new "
              "game there, say which civilisation with --civ." % session)
        return 1
    fresh = not (session and os.path.exists(session)) or _is_claimed_slot(session)
    # A CHECKPOINT DOES NOT GET AUTOSAVED OVER, EVER - see settings.is_checkpoint's
    # own comment for the whole story. `checkpoint_source` stays None for an
    # ordinary resume, in which case nothing below this differs from before:
    # `session` keeps naming the same file it always did, and it goes on
    # autosaving to it after every command, exactly as an ongoing session
    # always has. Only when the file being resumed is a frozen milestone does
    # `session` get reassigned - to a freshly claimed file, the same way a
    # brand new game's session file is claimed (_pick_session_filename) - so
    # that looking at a checkpoint to diagnose something never becomes the act
    # that moves it.
    checkpoint_source = None
    if not fresh:
        try:
            load_state(sim, session)
        except Exception as e:
            print("could not read the save file %r: %s" % (session, e))
            return 1
        if settings.is_checkpoint(session):
            checkpoint_source = session
            session = _pick_session_filename(sim.civ.get("id") or "game")
        else:
            print("Resumed from %s: %d AD." % (session, sim.year))

    if (fresh or checkpoint_source) and session:
        # WRITE IT NOW, not after the first command. The menu tells the player
        # "Saved to X. Come back with ..." and a break tester quit before
        # typing anything, found no file, followed the printed line anyway and
        # was dropped into a different civilisation's fresh game. A save the
        # game has promised has to exist from the moment it is promised. The
        # same promise holds for a checkpoint's forked session file: it has
        # been named out loud below, so it has to be real from that moment on.
        save_state(sim, session)
    if checkpoint_source:
        print("Resumed the checkpoint at %s: %d AD. A checkpoint stays "
              "exactly as it is - nothing you do now writes back into it. "
              "From here on, this game is autosaving to %s instead."
              % (checkpoint_source, sim.year, session))
    # THE WELCOME AND TUTORIAL TEXT IS A PREFERENCE NOW (Options: "show the
    # welcome message and tutorial on new games"). A player on their fifth
    # new game does not need the five starter verbs explained again every
    # time; a player who has never seen this game does. Gated as one block,
    # not line by line, because it is all the same kind of text - what a
    # first-timer needs and nobody else does - and a veteran who has turned
    # it off still gets the arrival capital/year from 'state' on request.
    if fresh and app_cfg.get("show_welcome", True):
        print()
        print(_wrap("You arrive in %d AD with %d %s and nothing else: no "
                    "employees, no slaves, and nobody who owes you anything. "
                    "What you have is everything you know."
                    % (sim.year, sim.capital, money_word(sim.civ))))
        # THE KIT SAID 4,000 AND YOU ARRIVED WITH 3,000, SILENTLY. Every
        # kit's figure (STARTING_KITS) is priced in Rome 100 AD denarii, the
        # same currency project_cost and everything else is calibrated
        # through - see price_index's own comment in data.py - and is then
        # converted at THIS civilisation's prices before a denarius of it
        # ever reaches the ledger. A blind Han playthrough picked "merchant,
        # 4,000 den" off the kit list and read "You arrive ... with 3000
        # cash" one screen later with no statement anywhere that the two
        # numbers were the same kit. The arithmetic was always right; only
        # the silence was a bug.
        if kit and abs(sim.price_index - 1.0) > 0.002:
            _quoted = STARTING_KITS.get(kit, {}).get("den")
            if _quoted:
                print(_wrap('The "%s" kit is quoted in Rome\'s prices (%d den); '
                            "here, prices run at %.3gx Rome's, so that arrived "
                            "as %d %s, not %d."
                            % (kit, _quoted, sim.price_index, sim.capital,
                               money_word(sim.civ), _quoted)))
        print()
        # `open` BELONGS IN THE OPENING. Finishing a project earns you
        # nothing until you open its doors, auto_open ships off for a player
        # by design, and this list of what to type first did not mention it -
        # so a play tester finished seven concerns worth 1,713 a year, left
        # every one of them shut, and walked into a debt spiral in year three.
        # The one rule a first-timer must know cannot be the one thing the
        # first screen leaves out.
        print(_wrap("Type commands in plain words. The five to start with are "
                    "'state' (where you stand), 'available' (what you could "
                    "begin today), 'why <name>' (what a thing is for and what "
                    "it costs), 'start <name>' (begin it) and 'step' (let a "
                    "year pass). When something is FINISHED it earns nothing "
                    "until you 'open' it. 'stuck' says why you are not getting "
                    "on; 'quit' leaves."))
        print()
        # THE FIVE ABOVE ARE A START, NOT THE WHOLE GAME, and saying so only
        # in passing - "'help' explains the rest", one clause at the end of a
        # paragraph about something else - undersold it badly: a player who
        # went on to win the entire game reported believing there were only
        # five help topics in total, and reached for `help` for the first
        # time only once a command she typed did not exist. There are far
        # more commands than these five, and `help` is where the rest of them
        # actually live, a topic at a time - named here, not left as a single
        # word to take on faith.
        print(_wrap("These five are a beginning, not the whole of it - there "
                    "are far more commands than this. 'help' lists the rest, "
                    "one topic at a time: %s. Reach for it the moment you "
                    "type a word the game does not know, not only once you "
                    "are stuck." % ", ".join(_protocol.HELP_TOPICS)))
        # THE WALKTHROUGH, NOT BURIED. `path <goal>` lays out everything
        # still standing between here and one thing AND which of it you
        # could start today, and it used to be findable only inside `help
        # commands`. An England player spent about forty minutes guessing
        # before finding it and said it reorganized the rest of play once
        # they had; two other players separately asked for exactly the join
        # it does. It has no business being harder to find than the five
        # above, once a player has a goal in mind - which, on arrival, they
        # already do.
        if not sim.fog:
            print()
            print(_wrap("Once you have a goal in mind: 'path <name>' lays "
                        "out everything still standing between here and "
                        "there, and which of it you could start TODAY. "
                        "This is the walkthrough."))
        print()
        print(_wrap("'options' shows the few things you can change without "
                    "restarting - right now, the horizon and whether the "
                    "founder can die of old age - and where this game is "
                    "being saved."))
        print()

    while True:
        # The same figure state reports: the pool LESS hours already sold for
        # wages. The prompt disagreeing with state about the one number on it
        # is how a tester found the accounting wrong in the first place.
        free_hours = max(0.0, sim.director_pool() - sim.director_hours_committed())
        # The prompt is built here and never passes through the renderer, so it
        # was the last place still saying "den" in a game counted in pence.
        # THE SAME TWO NUMBERS `why` PRINTS, for the same reason the hours
        # figure above matches state's: the prompt showed hired heads only
        # (s.scholars, s.artisans) while `why` compares a project's
        # requirement against effective_scholars() and craft_hands_available()
        # - both of which count the founder, and the second of which counts
        # hours under contract. A play tester read "sch 0 art 0" in the prompt
        # and "(you have 1, 0)" in `why` on the same turn and reported the
        # game as having lost count of their staff.
        prompt = ("[%d AD | %d %s | you:%d hr | sch %.0f art %.0f | rep %.0f] > "
                  % (sim.year, sim.capital, money_short(sim.civ), free_hours,
                     sim.effective_scholars(), sim.craft_hands_available(),
                     sim.reputation))
        try:
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            # Piped input runs out, and a person presses ctrl-D. Neither is a
            # crash, and the old loop raised EOFError out of the process.
            print()
            break
        # 'options' IS ANSWERED HERE, NOT BY THE DISPATCHER. It changes
        # things about the SITTING (the horizon, mortality, where this save
        # lives) rather than the game state the JSON protocol speaks about,
        # so it never becomes a command an agent script could send - see
        # _ingame_options and settings.py's module docstring for what it
        # covers and why each of those, specifically, is honest to change
        # without restarting.
        _tokens = line.strip().split()
        _word0 = _tokens[0].lower() if _tokens else ""
        if _word0 in ("options", "option", "settings"):
            session = _ingame_options(sim, session)
            continue
        # SESSION COMMANDS, BARE ONLY - see the block comment above
        # _ingame_saves for why these four exist and why each is intercepted
        # here rather than reaching parse_typed. 'save <file>'/'load <file>'
        # WITH an argument are deliberately left alone: those still fall
        # through to the JSON protocol's own sandboxed save/load below,
        # unchanged from before any of this existed.
        if _word0 == "saves" and len(_tokens) == 1:
            _ingame_saves(app_cfg, session)
            continue
        if _word0 == "save" and len(_tokens) == 1:
            _ingame_save_milestone(sim, session)
            continue
        if _word0 == "load" and len(_tokens) == 1:
            session = _ingame_load(app_cfg, sim, session, a)
            continue
        if _word0 == "menu" and len(_tokens) == 1:
            # NOT A LOSS. This game has already been saved after every
            # command that reached this point (see "SAVE FIRST, THEN SPEAK"
            # below) and --session itself is untouched - 'menu' only means
            # "I am done looking at this one for now", and cmd_menu's own
            # Load screen (or a bare resume with --session) is how to come
            # straight back to it.
            print()
            return cmd_menu(a)
        if _word0 == "restart" and len(_tokens) == 1:
            _confirm = _ask("   Start a different game? This one stays "
                            "exactly as saved, and you can resume it later. "
                            "[y/N] ", ["y", "n"], "n")
            if _confirm == "y":
                print()
                return _new_game(_load_civ_list(), app_cfg)
            continue
        cmd, err = parse_typed(line)
        if err:
            print("   " + err)
            continue
        if cmd is None:
            continue
        # HOW LONG THAT TOOK. Agents play this game as well as people do, and
        # an agent has no feel for which commands are slow: it cannot notice
        # that `step 50` always takes a while the way a person drumming their
        # fingers does, so it cannot tell you, and a real complaint about speed
        # goes unreported for rounds. Measured from the command being accepted
        # to its output being rendered, which is the interval the player
        # actually waits through.
        _t0 = time.time()
        try:
            resp = _agent_dispatch(sim, nodes, cmd)
        except Exception as e:            # never lose a session to a bug
            resp = {"ok": False,
                    "error": "internal error handling that command: %s: %s. "
                             "The game is intact; try something else."
                             % (type(e).__name__, e)}
        # SAVE FIRST, THEN SPEAK. The state change is already committed by the
        # time we get here, so writing it must not be contingent on the output
        # succeeding. A weird-play tester piped the game through `head`, which
        # closed the pipe and killed the process on the first print - and
        # twelve years of play went with it, twice, in a game whose own help
        # promises "progress is written to this file after every command...
        # close the terminal, anything".
        if session:
            save_state(sim, session)
        try:
            # 'state json' / 'portfolio json' / 'risk json': the raw reply,
            # one line, instead of the rendered screen. Every player of this
            # game is an AI agent parsing text, and several have lost runs
            # to parsing a prose table that was never meant to be a machine
            # interface - `agent` already gives a script this on every
            # command; this is the same line, on demand, inside `play`. It
            # is THE SAME resp dict `render_pretty` below would otherwise
            # render, produced by the one dispatcher both paths call, so
            # the prose and this JSON can never disagree about what
            # happened, and fog is scrubbed exactly once, upstream of both.
            if cmd.get("json"):
                _text = json.dumps(resp)
            else:
                _text = render_pretty(cmd.get("cmd"), resp)
            _took = time.time() - _t0
            # Only when it is worth knowing. A tenth of a second on every line
            # is noise that would bury the one command that took nine seconds.
            print(_text + ("\n   (took %.1fs)" % _took if _took >= 0.5 else ""))
            print()
        except BrokenPipeError:
            # Somebody closed the pipe. The game is saved; leave quietly.
            try:
                sys.stdout.close()
            except Exception:
                pass
            break
        if cmd.get("cmd") == "quit":
            break
        # NOT A BREAK. This used to end the process the moment the horizon was
        # reached, so a weird-play tester who ran out of years could type
        # exactly one more command and was then dropped back to the shell,
        # unable to read their own final position. The dispatcher already
        # refuses anything that would move the game on once it has ended; what
        # is left is looking at it, which is the whole point of finishing.
        end = _agent_end_reason(sim)
        if end and not getattr(a, "_said_end", False):
            a._said_end = True
            # THE SCOREBOARD, not one sentence. See protocol.final_report.
            print(render_final(final_report(sim, nodes)))
            print()
            print(_wrap("You can still look at anything; 'quit' when you are "
                        "done."))
            print()
    if _agent_end_reason(sim) and not getattr(a, "_said_end", False):
        print(render_final(final_report(sim, nodes)))
        print()
    print("Ended %d AD. %s" % (sim.year, _agent_end_reason(sim) or "stopped"))
    if session:
        print("Saved to %s. Come back with:" % session)
        print("   python3 sim/simulator.py play --session %s" % session)
    return 0


# THE SAME FLOOR core.py's Sim.__init__ APPLIES AT YEAR ZERO (see
# _ingame_options below, "THE SAME DRAW core.py's Sim.__init__ makes"), kept
# as its own declared name because core.py has not migrated its own copy to
# declare() yet - two independent literals with the same value, not one
# shared source, so a change to one will not reach the other.
INGAME_MORTALITY_MIN_REMAINING_LIFE_YEARS = declare(
    "INGAME_MORTALITY_MIN_REMAINING_LIFE_YEARS", 5, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="Floor under the gaussian draw for a founder's remaining lifespan, "
        "so a bad roll (or a mean/sd combination that puts real weight below "
        "zero) cannot hand a newly-mortal founder a negative or "
        "vanishingly short life. Not derived from any mortality curve; "
        "picked to guarantee a few years of remaining play regardless of "
        "the draw.")


def _ingame_options(s, session):
    """The 'options' command, typed mid-game. Returns the session path to use
    from here on (unchanged, unless 'move this save' was used).

    ONLY THE THINGS THAT ARE HONEST TO CHANGE WITHOUT RESTARTING ARE OFFERED
    HERE. Three of the five things a new game asks about are NOT, on purpose:

      - civilisation: the whole world (prices, values, what is missing, what
        is coming) is keyed to it. There is no "change civilisation" that
        would not just be starting a different game while pretending to be
        this one.
      - starting kit: it names an amount of money the founder arrived with.
        The founder arrived however many years ago this save's year 1 was;
        re-picking that now would only ever mean handing yourself money you
        did not start with, i.e. cheating, dressed as a settings screen.
      - fog of war: see protocol.load_state's own comment on this - a save
        played with fog cannot be resumed without it, because there is no
        way to make a player un-know the whole tree they have already seen.
        The reverse is just as dishonest: turning fog ON after playing
        without it would claim to hide a tree this sitting has already been
        shown in full.

    Horizon and mortality are not like that. The horizon is a date the
    player is choosing to stop by, not a fact about the world - moving it,
    either direction, changes nothing about what has already happened.
    Mortality can honestly move exactly one way: choosing, from this year on,
    to let the founder age and die is a real choice a person can make midway
    through anything; choosing to UNDO having already accepted that is not a
    choice available to anyone in this founder's position, so it is not
    offered here either - see the menu below, which only ever offers "on".
    """
    while True:
        mortal_on = not s.cfg.get("immortal", True)
        cur_end = getattr(s, "end_year",
                          s.cfg["start_year"] + s.cfg.get("horizon_years", 500))
        print()
        print("-" * 78)
        print("   OPTIONS")
        print("-" * 78)
        print("   civilisation : %s, %d AD                (fixed for this game)"
              % (s.civ.get("name", s.civ.get("id", "?")), s.cfg["start_year"]))
        print("   fog of war   : %-3s                          (fixed for this game)"
              % ("on" if getattr(s, "fog", False) else "off"))
        print("   mortality    : %s"
              % ("on - the founder ages, and can die of it" if mortal_on
                 else "off - the founder does not age"))
        # NO DEADLINE, SAID PLAINLY - not a nine-digit year nobody asked to
        # read. Endless is still, underneath, the large-but-ordinary number
        # ENDLESS_HORIZON_YEARS describes (see its own comment on why); this
        # is the one screen in cli.py that knows that and says the honest
        # thing instead of the literal one.
        if _is_endless_horizon(cur_end, s.cfg["start_year"]):
            print("   horizon      : none - Endless. Play until you choose to stop.")
        else:
            print("   horizon      : ends %d AD  (now %d AD, %d years left)"
                  % (cur_end, s.year, max(0, cur_end - s.year)))
        print("   this save    : %s"
              % (session or "(not being saved anywhere - restart with --session "
                            "to change that)"))
        print()
        print("   1) change the horizon")
        print("   2) turn mortality on from this year forward%s"
              % ("  (already on)" if mortal_on else ""))
        if session:
            print("   3) move this save to a different file")
        print("   b) back to the game")
        try:
            raw = input("\n   > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return session
        word = raw.split()[0] if raw.split() else ""

        if word in ("", "b", "back"):
            return session

        elif word in ("1", "horizon"):
            try:
                raw2 = input("   New end year (a whole number of AD, > %d), "
                             "or 'endless' for no deadline at all: "
                             % s.year).strip()
            except (EOFError, KeyboardInterrupt):
                print(); continue
            if not raw2:
                print("   -- unchanged.")
                continue
            if raw2.lower() in ("endless", "none", "forever", "no deadline",
                               "no limit", "unlimited"):
                new_end = s.year + ENDLESS_HORIZON_YEARS
            else:
                try:
                    new_end = int(raw2)
                except ValueError:
                    print("   -- that is not a whole number of years, or "
                          "'endless'.")
                    continue
                if new_end <= s.year:
                    print("   -- %d AD has already passed (or is now); the "
                          "game would end the moment you left this menu. Pick "
                          "a later year." % new_end)
                    continue
            new_horizon = new_end - s.cfg["start_year"]
            s.end_year = new_end
            s.cfg["horizon_years"] = new_horizon
            if session:
                meta = settings.load_session_meta(session)
                meta["horizon_years"] = new_horizon
                settings.save_session_meta(session, meta)
            print("   -- done. This game now has no deadline (Endless)."
                  if _is_endless_horizon(new_end, s.cfg["start_year"]) else
                  "   -- done. This game now ends in %d AD." % new_end)

        elif word in ("2", "mortal", "mortality") and not mortal_on:
            print(_wrap("From this year on the founder ages, and can die of "
                        "it, the same as anyone in this world - see 'why' on "
                        "any of the nodes that outlive one lifetime. This "
                        "cannot be undone: there is no honest way to give "
                        "the founder back an immortality already spent part "
                        "of a life without."))
            confirm = _ask("   Turn mortality on now? [y/N] ", ["y", "n"], "n")
            if confirm == "y":
                # THE SAME DRAW core.py's Sim.__init__ makes for a mortal
                # founder at year zero (self.life_left = ... rng.gauss(...)),
                # made here instead because that constructor only ever runs
                # once, at the start of the game, and this founder is
                # choosing to become mortal partway through it. See core.py
                # around "founder remaining lifespan" for the line this
                # mirrors.
                mean = s.cfg.get("founder_life_mean", DEFAULTS["founder_life_mean"])
                std_dev = s.cfg.get("founder_life_sd", DEFAULTS["founder_life_sd"])
                s.cfg["immortal"] = False
                s.life_left = max(INGAME_MORTALITY_MIN_REMAINING_LIFE_YEARS,
                                  s.rng.gauss(mean, std_dev))
                s.founder_alive = True
                print("   -- done. Mortality is on from %d AD." % s.year)
            else:
                print("   -- unchanged.")

        elif word in ("3", "move", "movesave") and session:
            try:
                raw3 = input("   New path for this save (ending .json): ").strip()
            except (EOFError, KeyboardInterrupt):
                print(); continue
            if not raw3:
                print("   -- unchanged.")
                continue
            newp = os.path.expanduser(raw3)
            if not newp.lower().endswith(".json"):
                newp += ".json"
            if os.path.abspath(newp) == os.path.abspath(session):
                print("   -- that is where it already is.")
                continue
            if os.path.exists(newp):
                print("   -- %s already exists; pick a name that is not taken."
                      % newp)
                continue
            try:
                parent = os.path.dirname(os.path.abspath(newp))
                if parent and not os.path.isdir(parent):
                    os.makedirs(parent, exist_ok=True)
                save_state(s, newp)
            except OSError as e:
                print("   -- could not write there: %s" % e)
                continue
            settings.move_session_meta(session, newp)
            old = session
            session = newp
            try:
                os.remove(old)
            except OSError:
                pass
            print("   -- moved. This game now saves to %s" % session)
            print("   Come back to it with:")
            print("      python3 sim/simulator.py play --session %s" % session)

        else:
            print("   -- not a choice right now.")


# THE SAME DEFAULT engine/society.py DECLARES AS EMINENCE_DANGER_WEIGHT_DEFAULT
# (0.5) - kept as its own name because this file has no Sim/SocietyMixin
# instance to read that constant from (cmd_civs works from the raw civ JSON
# files directly, before any game has started), same shape as
# INGAME_MORTALITY_MIN_REMAINING_LIFE_YEARS just above.
CIVS_EMINENCE_DANGER_DEFAULT = declare(
    "CIVS_EMINENCE_DANGER_DEFAULT", 0.5, kind="temporary_heuristic",
    unit="dimensionless weight", source=None, confidence="D",
    why="What this screen shows for 'eminence is dangerous' when a "
        "civilisation's own JSON does not set w_eminence_danger - a mid-scale "
        "default rather than a claim about any specific civilisation. "
        "Matches engine/society.py's EMINENCE_DANGER_WEIGHT_DEFAULT, which "
        "is the value actually used if a live game hits the same missing "
        "field; declared separately here so the two can be told apart if "
        "they are ever retuned independently, and so a reader of this file "
        "alone can see this number is not invented for display.")


def cmd_civs(a):
    """List the civilizations you can play, and what makes each one different.

    home_regions and base_reach used to be printed here and read NOWHERE
    ELSE: that was the entire bug this session fixed. They now actually
    drive Sim.region_reach() and Sim.material_reach() (see simulator.py),
    which is a much better reason to show them, so this now also names the
    home ground itself rather than just the region ids.
    """
    geo = load_geography()
    region_names = {rid: region_record.get("name", rid)
                    for rid, region_record in (geo.get("regions") or {}).items()
                    if not rid.startswith("_")}
    for civ_filename in sorted(os.listdir(CIVDIR)):
        # Files starting with "_" are schema/reference data, not a playable
        # civilization (e.g. _TECH_EFFECTS.json), same convention this file
        # already uses everywhere else for "_"-prefixed keys and entries.
        if not civ_filename.endswith(".json") or civ_filename.startswith("_"):
            continue
        civ_data = json.load(open(os.path.join(CIVDIR, civ_filename)))
        value = civ_data["values"]
        print("%-16s %s, %s" % (civ_data["id"], civ_data["name"], civ_data["year"]))
        print("   %s" % civ_data.get("blurb", ""))
        homes = [region_names.get(region_id, region_id) for region_id in civ_data.get("home_regions") or []]
        print("   home ground: %s" % (", ".join(homes) if homes else "(none set)"))
        print("   population %s   state capacity %.2f   base_reach %d (how far it already "
              "routinely travels)   starts with %d technologies"
              % (f"{civ_data.get('population',0):,}", civ_data.get("state_capacity", 0),
                 civ_data.get("base_reach", 0), len(civ_data.get("starting_techs", []))))
        print("   fears the inexplicable %.2f | fears heterodoxy %.2f | resents machines %+.2f "
              "| bribable %.2f | habituates %.2f"
              % (value["w_magic_fear"], value["w_religious_rigidity"], value["w_labour_saving"],
                 value["bribability"], value["adaptation_rate"]))
        print("   eminence is dangerous %.2f  (how much prominence ITSELF endangers you)"
              % value.get("w_eminence_danger", CIVS_EMINENCE_DANGER_DEFAULT))
        mults = civ_data.get("cost_multipliers") or {}
        if mults:
            easy = sorted((cost_pair for cost_pair in mults.items() if cost_pair[1] < 1.0), key=lambda x: x[1])[:4]
            hard = sorted((cost_pair for cost_pair in mults.items() if cost_pair[1] > 1.0), key=lambda x: -x[1])[:4]
            if easy:
                print("   good at : " + ", ".join("%s x%.2f" % cost_pair for cost_pair in easy))
            if hard:
                print("   bad at  : " + ", ".join("%s x%.2f" % cost_pair for cost_pair in hard))
        print()
    print("starting kits (--kit):")
    for kit_id, kit_data in STARTING_KITS.items():
        print("   %-14s %9s den   %s" % (kit_id, f"{kit_data['den']:,}", kit_data["desc"]))
    return 0


def _ask(prompt, options, default=None):
    """Ask until the answer is one of options. Empty input takes the default."""
    while True:
        try:
            raw = input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if not raw and default is not None:
            return default
        if raw in ("q", "quit", "exit"):
            return None
        for option in options:
            if raw == option or (len(raw) == 1 and option.startswith(raw)):
                return option
        print("   -- I did not understand that. Options: %s" % ", ".join(options))


def _new_game(civs, cfg):
    """The wizard: pick a civilisation, read where you have landed, choose
    fog/kit/mortality/goal/horizon, and start. Returns cmd_play's exit code once a
    game has actually begun, or None if the player backed out first - in
    which case cmd_menu's own loop is what should run next, not this
    function again."""
    tree, _prices, nodes, _wages, _goods = load()
    print("-" * 78)
    print("   WHERE, AND WHEN")
    print("-" * 78)
    for i, civ_record in enumerate(civs, 1):
        print()
        print("   %d) %s, %d" % (i, civ_record.get("name", civ_record["id"]), civ_record.get("year", 0)))
        print(_wrap(civ_record.get("blurb", ""), indent="      "))
        print("      %s people   state capacity %.2f   prices %.2fx Rome"
              % (f"{civ_record.get('population', 0):,}", civ_record.get("state_capacity", 0),
                 civ_record.get("price_index", 1.0)))
    print()
    default_i = next((i for i, civ_record in enumerate(civs, 1)
                      if civ_record.get("id") == cfg.get("default_civ")), None)
    prompt = ("   Which one? [1-%d%s, or b to go back] "
              % (len(civs), (", default %d" % default_i) if default_i else ""))
    while True:
        try:
            raw = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print(); return None
        if raw.lower() in ("q", "quit", "exit", "b", "back"):
            return None
        if not raw and default_i:
            civ = civs[default_i - 1]
            break
        if raw.isdigit() and 1 <= int(raw) <= len(civs):
            civ = civs[int(raw) - 1]
            break
        print("   -- a number from 1 to %d." % len(civs))

    opening = civ.get("opening") or {}
    print()
    print("=" * 78)
    print(("   %s, %d" % (civ.get("name", civ["id"]), civ.get("year", 0))).upper())
    print("=" * 78)
    for key, heading in (("arrival", None),
                         ("what_you_can_see", "What you can see"),
                         ("what_is_missing", "What is missing"),
                         ("what_is_coming", "What is coming, and only you know it"),
                         ("what_this_models", "The size of your own reach")):
        if not opening.get(key):
            continue
        print()
        if heading:
            print("   %s" % heading.upper())
        print(_wrap(opening[key]))
    if not opening:
        print()
        print(_wrap(civ.get("blurb", "")))
    print()

    print("-" * 78)
    print(_wrap("FOG OF WAR. With it on you see what you have built, what you "
                "could begin today as a one-line summary, and things you have "
                "heard of but cannot yet start. You cannot see where anything "
                "leads. With it off you can see the whole tree and plan a "
                "route through it. This cannot be changed once you start - a "
                "save played with it on can never be resumed without it, and "
                "one played without it has already seen too much to fog "
                "again.", indent="   "))
    fog_default = "y" if cfg.get("default_fog", True) else "n"
    fog = _ask("\n   Fog of war? [%s] " % ("Y/n" if fog_default == "y" else "y/N"),
               ["y", "n"], fog_default)
    if fog is None:
        return None
    print()
    print("-" * 78)
    print("   WHAT YOU ARRIVED WITH")
    for name, kit in STARTING_KITS.items():
        print("      %-14s %9s den" % (name, f"{kit['den']:,}"))
        if kit.get("desc"):
            print(_wrap(kit["desc"], indent="         "))
    kit_default = cfg.get("default_kit", "poor_scholar")
    if kit_default not in STARTING_KITS:
        kit_default = "poor_scholar"
    kit = _ask("\n   Which? [%s, default %s] " % ("/".join(STARTING_KITS), kit_default),
               list(STARTING_KITS), kit_default)
    if kit is None:
        return None
    print()
    print("-" * 78)
    print(_wrap("MORTALITY. By default the founder does not age, which measures "
                "the tree rather than a lifespan lottery. Turned on, you get one "
                "human life and everything you have not made permanent dies with "
                "you. The premise of the whole game is that one is the honest "
                "number. You can turn this on later, mid-game, without "
                "restarting (see the in-game 'options' command) - but not off "
                "again once it is on, the same as fog.", indent="   "))
    mortal_default = "y" if cfg.get("default_mortal", False) else "n"
    mortal = _ask("\n   Let the founder age and die? [%s] "
                 % ("Y/n" if mortal_default == "y" else "y/N"),
                 ["y", "n"], mortal_default)
    if mortal is None:
        return None
    print()
    print("-" * 78)
    print(_wrap("THE GOAL. The transistor (1951) is the original target and "
                "still the default, and from scratch it takes centuries - which "
                "is the whole reason the founder does not age by default. Below "
                "are the alternatives: achievements a single lifetime can "
                "actually finish, and a handful almost as large as the "
                "transistor itself. 'closure' is how many other things it needs "
                "first; 'floor' is the fewest calendar years that work could "
                "possibly take, with every dice roll going your way.",
                indent="   "))
    print()
    goals = goal_catalog(tree, nodes)
    default_goal_id = cfg.get("default_goal") or tree["meta"]["goal_node"]
    if default_goal_id not in nodes:
        default_goal_id = tree["meta"]["goal_node"]
    default_gi = next((i for i, goal_row in enumerate(goals, 1)
                       if goal_row["node"] == default_goal_id), 1)
    for i, goal_row in enumerate(goals, 1):
        node = goal_row["node"]
        need = closure(nodes, node)
        yrs, _chain = critical_path(nodes, node)
        print("   %d) %s  (closure %d, floor %.0fy%s)"
              % (i, goal_row.get("name", node), len(need), yrs,
                 ", %s" % goal_row["scale"] if goal_row.get("scale") else ""))
        if goal_row.get("blurb"):
            print(_wrap(goal_row["blurb"], indent="         "))
        if nodes[node].get("win_condition"):
            print(_wrap("Won by measurement, not by building: %s."
                        % win_condition_describe(nodes[node]), indent="         "))
    print()
    while True:
        try:
            rawg = input("   Which one? [1-%d, default %d, or b to go back] "
                         % (len(goals), default_gi)).strip()
        except (EOFError, KeyboardInterrupt):
            print(); return None
        if rawg.lower() in ("q", "quit", "exit", "b", "back"):
            return None
        if not rawg:
            goal = goals[default_gi - 1]["node"]
            break
        if rawg.isdigit() and 1 <= int(rawg) <= len(goals):
            goal = goals[int(rawg) - 1]["node"]
            break
        print("   -- a number from 1 to %d." % len(goals))
    print()
    print("-" * 78)
    print(_wrap("HORIZON. The game ends automatically this many years after "
                "arrival, mostly so a run that is truly stuck stops rather than "
                "running forever. Unlike the choices above, this one you CAN "
                "change later without restarting - the in-game 'options' "
                "command.", indent="   "))

    print("-" * 78)
    print(_wrap("DIFFICULTY, IN THIS GAME, MEANS ONE THING: how long you have. "
                "Nothing below changes what anything costs or how likely it is "
                "to fail - the tree and the risk are the same whatever you "
                "pick here. What changes is only the calendar you are racing.",
                indent="   "))
    print()
    # THE ONE HONEST THING A MODE MENU CAN SAY HERE: the same number of years
    # is a completely different offer depending which civilisation it is
    # attached to - see DICE_FREE_FLOOR_YEARS's own comment for the measurement
    # and data/review/PATH_SEARCH.md for the method. Said to the player
    # NOW, about the civilisation they just picked, rather than left for them
    # to discover by overshooting a horizon that was never going to be enough.
    # THE FLOOR OF THE GOAL YOU JUST PICKED, not of the default one. This said
    # "reaching the transistor takes about N years" from a table of per-civ
    # figures, which was right while there was one goal and is wrong now that
    # there are seventeen - a lifetime goal with a 5-year floor and the
    # transistor with a 142-year one cannot share a sentence. critical_path is
    # the same measurement, computed for the actual choice, so there is nothing
    # to keep in step. It is a floor and not a forecast: it assumes every roll
    # goes your way and no year is ever spent short of money, people or
    # material, which no real run manages.
    _floor_yrs, _ = critical_path(nodes, goal)
    _goal_label = nodes.get(goal, {}).get("name", goal)
    if _floor_yrs:
        print(_wrap("What you just chose - %s - cannot be done in fewer than "
                    "about %d years even with every roll going your way, and a "
                    "real run takes substantially longer than its floor. Pick a "
                    "calendar with that in mind."
                    % (_goal_label, _floor_yrs), indent="   "))
        print()

    for i, (_key, _label, _yrs, _note) in enumerate(HORIZON_MODES, 1):
        print("   %d) %-10s %s" % (i, _label,
              ("%d years - %s" % (_yrs, _note)) if _yrs else _note))
    print("   %d) an exact number of years" % (len(HORIZON_MODES) + 1))
    # THE REMEMBERED DEFAULT MUST STILL ACCEPT IN ONE BLANK LINE, the same
    # contract every other question in this wizard already has (see "REMEMBERED
    # FOR NEXT TIME" below) - whether last time's horizon happens to match a
    # named preset or not. A player who remembered 321 years specifically
    # must not be routed through an extra "how many years?" prompt just
    # because 321 is not one of the four named numbers.
    default_h = cfg.get("default_horizon", 500)
    _mode_by_years = {mode[2]: mode[0] for mode in HORIZON_MODES if mode[2]}
    _mode_by_years[ENDLESS_HORIZON_YEARS] = "endless"
    _default_key = _mode_by_years.get(default_h)
    _default_idx = (next(i for i, mode in enumerate(HORIZON_MODES, 1)
                         if mode[0] == _default_key)
                    if _default_key else len(HORIZON_MODES) + 1)
    while True:
        try:
            rawh = input("\n   Which? [1-%d, default %d, or b to go back] "
                         % (len(HORIZON_MODES) + 1, _default_idx)).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(); return None
        if rawh in ("q", "quit", "exit", "b", "back"):
            return None
        if not rawh:
            if _default_key:
                _key, _label, _yrs, _note = HORIZON_MODES[_default_idx - 1]
                horizon = _yrs if _yrs else ENDLESS_HORIZON_YEARS
                break
            # No preset matches the remembered horizon - accept IT directly,
            # not the custom prompt's own separate default, with no second
            # question asked.
            horizon = default_h
            break
        if rawh.isdigit() and 1 <= int(rawh) <= len(HORIZON_MODES) + 1:
            choice = int(rawh)
        else:
            _match = next((i for i, mode in enumerate(HORIZON_MODES, 1)
                          if rawh in (mode[0], mode[1].lower())), None)
            if _match is None:
                print("   -- a number from 1 to %d, a name, or b."
                      % (len(HORIZON_MODES) + 1))
                continue
            choice = _match
        if choice == len(HORIZON_MODES) + 1:
            try:
                rawh2 = input("   How many years? [default %d, or b to go "
                              "back] " % default_h).strip()
            except (EOFError, KeyboardInterrupt):
                print(); return None
            if rawh2.lower() in ("q", "quit", "exit", "b", "back"):
                return None
            if not rawh2:
                horizon = default_h
                break
            try:
                horizon = int(rawh2)
                if horizon <= 0:
                    raise ValueError
            except ValueError:
                print("   -- a whole number of years, more than 0.")
                continue
            break
        else:
            _key, _label, _yrs, _note = HORIZON_MODES[choice - 1]
            horizon = _yrs if _yrs else ENDLESS_HORIZON_YEARS
            break

    # REMEMBERED FOR NEXT TIME, SILENTLY - not a settings screen's job. A
    # player who favours one civilisation and kit should not have to retype
    # them every game, and used to be able to set that from the main-menu
    # Options screen; that screen is for the APPLICATION now (see
    # settings.py's module docstring), so the wizard remembers its own
    # answers instead, the way a file dialog remembers its last folder. This
    # writes back exactly the six fields CONFIG_DEFAULTS calls "default_*",
    # and nothing else cfg might hold (display width, rows per page, the
    # welcome toggle) - those are the player's, set from Options, and this
    # wizard has no business overwriting them.
    cfg["default_civ"] = civ["id"]
    cfg["default_kit"] = kit
    cfg["default_fog"] = (fog == "y")
    cfg["default_mortal"] = (mortal == "y")
    cfg["default_goal"] = goal
    cfg["default_horizon"] = horizon
    settings.save_config(cfg)

    # THIS USED TO STOP HERE: print the command for the JSON protocol and ASK
    # whether to play. A tester put it plainly - "it should be the save
    # starting. It should have you pick, then you immediately jump in" - and
    # they were right: everything above this point is a choice about WHAT
    # game to start, not whether to start one, and a menu that ends by
    # handing you a command line to go run yourself is not a front door, it
    # is a man page. So: pick where the save goes, say so once, and go.
    #
    # AND IT USED TO GO INTO `agent`, which speaks JSON. The reason given at
    # the time was that only `agent` had a session file, and that `play`
    # without --manual was not a real choice. Both were true and neither was
    # a good enough reason to sit a person down in front of
    # {"cmd":"available"}: the answer was to fix `play`, which now takes a
    # --session of its own and is always manual, and speaks typed words over
    # the same dispatcher the JSON protocol uses. `agent` is still there, and
    # is still the right thing for a script.
    session = _pick_session_filename(civ["id"])
    # THE HORIZON HAS TO SURVIVE A RESUME TOO, and it is not part of what
    # save_state writes (see settings.py's module docstring) - so it gets
    # the same sidecar the in-game 'options' command uses to change it later.
    settings.save_session_meta(session, {"horizon_years": horizon})
    print()
    print("=" * 78)
    print(_wrap(
        "Starting now. Progress is written to this file after every command, "
        "so you can stop any time - close the terminal, anything - and come "
        "back to exactly where you left off with:"))
    print()
    print("      python3 sim/simulator.py play --session %s" % session)
    print()

    class Args:
        pass
    args = Args()
    args.strategy = "recommended"
    args.goal = goal
    args.seed = 1
    args.horizon = horizon
    args.civ = civ["id"]
    args.kit = kit
    args.mortal = (mortal == "y")
    args.fog = (fog == "y")
    args.session = session
    args.manual = True
    return cmd_play(args)


def _load_game(cfg):
    """List what is in the configured save directory and resume one.

    See _print_save_row for what each entry shows and why.
    """
    save_dir, rows, civ_index, need = _save_listing(cfg)

    print("-" * 78)
    print("   LOAD A SAVED GAME")
    print("-" * 78)
    print("   looking in: %s" % save_dir)
    print()
    if not rows:
        print(_wrap("Nothing there yet. Start a new game first, or type the "
                    "path to a save file below if you have one somewhere else."))
        print()
    for i, row in enumerate(rows, 1):
        _print_save_row(i, row, civ_index, need)

    print("   b) back to the main menu")
    if rows:
        prompt = "   Which one? [1-%d, p to type a path instead, or b] " % len(rows)
    else:
        prompt = "   p) type a path to a save file, or b) back"
    while True:
        try:
            raw = input("\n" + prompt + "\n   > ").strip()
        except (EOFError, KeyboardInterrupt):
            print(); return None
        low = raw.lower()
        if low in ("b", "back", "q", "quit", "exit"):
            return None
        if low in ("p", "path"):
            try:
                path = input("   Path to the save file: ").strip()
            except (EOFError, KeyboardInterrupt):
                print(); return None
            if not path:
                continue
            path = os.path.expanduser(path)
            if not os.path.exists(path):
                print("   -- nothing at %s" % path)
                continue
            chosen = path
            break
        if raw.isdigit() and rows and 1 <= int(raw) <= len(rows):
            chosen = rows[int(raw) - 1]["path"]
            break
        print("   -- a number from the list above, 'p', or 'b'.")

    class Args:
        pass
    args = Args()
    args.strategy = "recommended"
    args.seed = 1
    args.horizon = 500
    args.civ = None
    args.kit = "poor_scholar"
    args.mortal = False
    args.fog = False
    args.session = chosen
    args.manual = True
    return cmd_play(args)


def _options_menu(cfg):
    """Preferences about the APPLICATION, not about any one game: where
    saves go, how wide a line wraps, how many rows a long table shows
    before paging, and whether the welcome/tutorial text prints on a new
    game. See settings.py's module docstring for why this screen holds
    exactly these and none of the things a playthrough itself decides
    (civilisation, starting kit, fog, mortality, horizon) - those are
    remembered from the New Game wizard's last answers instead (see
    _new_game), and the couple of them that are honestly changeable
    mid-game (horizon, mortality) have their own, much smaller, in-game
    'options' command (_ingame_options) for a game already running.
    """
    while True:
        cfg = _apply_display_prefs(cfg)
        cur_width = settings.resolve_display_width(cfg)
        width_src = ("override" if isinstance(cfg.get("display_width"), (int, float))
                                   and cfg["display_width"] else
                    "detected from your terminal")
        print()
        print("-" * 78)
        print("   OPTIONS")
        print("-" * 78)
        print(_wrap("Preferences about this PROGRAM, not about any one game - "
                    "they apply whether you are starting a new one, loading an "
                    "old one, or running it from the command line with flags. "
                    "What a single playthrough is (civilisation, starting kit, "
                    "fog, mortality, the horizon) is asked when that game "
                    "starts, not here."))
        print()
        print("   1) save location      : %s"
              % settings.resolve_save_dir(cfg, ensure=False))
        print("   2) display width      : %d columns (%s)" % (cur_width, width_src))
        print("   3) rows per table      : %d" % settings.resolve_rows_per_page(cfg))
        print("   4) welcome/tutorial text on new games : %s"
              % ("on" if cfg.get("show_welcome", True) else "off"))
        print("   b) back to the main menu")
        try:
            raw = input("\n   > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(); return cfg
        word = raw.split()[0] if raw.split() else ""

        if word in ("", "b", "back"):
            return cfg

        elif word in ("1", "save", "location"):
            cur = settings.resolve_save_dir(cfg, ensure=False)
            print(_wrap("Where new games are saved, and where 'Load a saved "
                        "game' looks. Existing save files are not moved - use "
                        "'options' inside a game in progress to move that one "
                        "game's save."))
            if os.environ.get(settings.SAVE_DIR_ENV):
                print(_wrap("Note: the %s environment variable is set to %r "
                            "right now and overrides whatever is chosen here "
                            "until it is unset."
                            % (settings.SAVE_DIR_ENV,
                               os.environ[settings.SAVE_DIR_ENV])))
            try:
                raw2 = input("   New save directory [currently %s, blank to "
                             "leave unchanged]: " % cur).strip()
            except (EOFError, KeyboardInterrupt):
                print(); continue
            if not raw2:
                continue
            newdir = os.path.expanduser(raw2)
            try:
                os.makedirs(newdir, exist_ok=True)
                probe = os.path.join(newdir, ".rome-write-test")
                with open(probe, "w"):
                    pass
                os.remove(probe)
            except OSError as e:
                print("   -- could not use that directory: %s" % e)
                continue
            cfg["save_dir"] = newdir
            settings.save_config(cfg)
            print("   -- saved. New games, and 'Load a saved game', will use %s"
                  % newdir)

        elif word in ("2", "width", "display"):
            print(_wrap("How many columns text wraps to and tables are sized "
                        "for. Left alone, the game asks your terminal and uses "
                        "that (right now it reads %d). Set a number to "
                        "override it - for a terminal that cannot be asked, or "
                        "one you simply want narrower or wider - or type "
                        "'auto' to go back to asking the terminal."
                        % settings.resolve_display_width(
                            dict(cfg, display_width=None))))
            try:
                raw2 = input("   New width [currently %d (%s), a number, "
                             "'auto', or blank to leave unchanged]: "
                             % (cur_width, width_src)).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print(); continue
            if not raw2:
                continue
            if raw2 in ("auto", "detect", "default"):
                cfg["display_width"] = None
                settings.save_config(cfg)
                print("   -- saved. Width will be asked from your terminal "
                      "from now on.")
                continue
            try:
                display_width = int(raw2)
                if display_width < 20:
                    raise ValueError
            except ValueError:
                print("   -- a whole number of columns (at least 20), 'auto', "
                      "or blank.")
                continue
            cfg["display_width"] = display_width
            settings.save_config(cfg)
            print("   -- saved. %d columns from now on." % display_width)

        elif word in ("3", "rows", "page"):
            try:
                raw2 = input("   Rows per table before paging [currently %d, "
                             "blank to leave unchanged]: "
                             % settings.resolve_rows_per_page(cfg)).strip()
            except (EOFError, KeyboardInterrupt):
                print(); continue
            if not raw2:
                continue
            try:
                rows_per_page = int(raw2)
                if rows_per_page <= 0:
                    raise ValueError
            except ValueError:
                print("   -- a whole number of rows, more than 0.")
                continue
            cfg["rows_per_page"] = rows_per_page
            settings.save_config(cfg)
            print("   -- saved.")

        elif word in ("4", "welcome", "tutorial"):
            value = _ask("   Show the welcome message and tutorial on new games? "
                     "[y/n] ", ["y", "n"],
                     "y" if cfg.get("show_welcome", True) else "n")
            if value:
                cfg["show_welcome"] = (value == "y")
                settings.save_config(cfg)
                print("   -- saved.")

        else:
            print("   -- 1 to 4, or b.")


def cmd_menu(a):
    """The front door for a person, rather than for a script.

    Everything here can be done with command-line flags, and the flags are
    what a script should use. This exists because "what do I type" was the
    first thing every human tester had to be told out of band, and because a
    game about arriving somewhere should be able to tell you where you have
    arrived before it asks you to make decisions about it.

    Three doors: start a new game, resume one from a list rather than a
    remembered filename, or change a few things that should not need a flag
    every time (chiefly where saves go - see settings.py). Five playtesters
    reached for --help before this existed; the point of this function is
    that none of them should have had to know that flag existed at all.
    """
    civs = _load_civ_list()
    # THE APPLICATION'S OWN PREFERENCES, BEFORE THE FIRST LINE IS PRINTED, so
    # even this opening banner wraps to a player's chosen/detected width -
    # see _apply_display_prefs. Reloaded every time the loop comes back
    # around (below) so a width or welcome-text change made from Options
    # takes effect the moment the player is back at this menu, with no
    # restart.
    cfg = _apply_display_prefs()

    if cfg.get("show_welcome", True):
        print()
        print("=" * 78)
        print("   ONE PERSON, AND EVERYTHING THEY KNOW".center(78))
        print("=" * 78)
        print()
        print(_wrap(
            "You are one person, dropped into a pre-industrial society, carrying "
            "the knowledge of how modern technology works and none of the industry "
            "that makes it. Knowing how a thing works is free. Building it is not: "
            "it costs your own hours, other people's hours, money, materials, and "
            "years you do not get back."))
        print()
        print(_wrap(
            "You arrive alone. No employees, no slaves, nobody who owes you "
            "anything, and about enough money to eat for a few months."))
        print()

    while True:
        cfg = _apply_display_prefs()
        print("-" * 78)
        print("   MAIN MENU")
        print("-" * 78)
        print()
        print("   1) New game")
        print("   2) Load a saved game")
        print("   3) Options")
        print("   q) Quit")
        try:
            raw = input("\n   > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(); return 0
        word = raw.split()[0] if raw.split() else ""

        if word in ("q", "quit", "exit"):
            return 0
        elif word in ("1", "new", "start"):
            print()
            return_code = _new_game(civs, cfg)
            if return_code is not None:
                return return_code
            print()
        elif word in ("2", "load", "resume", "continue"):
            print()
            return_code = _load_game(cfg)
            if return_code is not None:
                return return_code
            print()
        elif word in ("3", "options", "option", "settings"):
            _options_menu(cfg)
            print()
        else:
            print("   -- 1, 2, 3 or q.\n")
