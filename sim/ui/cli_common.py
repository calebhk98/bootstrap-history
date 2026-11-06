"""What the command-line entry points share: the horizon modes, the session-file and display helpers.
A leaf under cli.py and the cli_*.py command modules, so each imports alone."""
import os
import sys

from sim.engine.ui_port import DEFAULTS, default_civilisation_id, resolve_goal, settings
from . import protocol as _protocol
from . import cli_units_options
from .founder_budget import founder_budget
from .protocol import civ_of_save, goal_of_save

# ----------------------------------------------------------------------------
# DIFFICULTY, PRESENTED HONESTLY, AS WHAT IT ACTUALLY IS HERE: how long you
# have. The horizon was already a plain number the engine takes; a player who
# had just won the whole game proposed naming a few points on that same line
# - Challenge/Standard/Relaxed/Endless - rather than asking for four bare
# numbers with no sense of what any of them mean.

# NAMED, NOT INVENTED. Every one of these is the SAME knob the engine always
# had (a plain year count the run ends at) - nothing here scales a cost, a
# risk, or a failure rate. The request named Challenge 400, Standard 500 and
# Relaxed "600-700"; 650 is the middle of that range, still a single whole
# number because the engine only ever took one. Endless is not a bigger
# number wearing a disguise - see ENDLESS_HORIZON_YEARS below for exactly
# what it is and is not.
# The notes do not quote any measured floor or call a setting unreachable: the
# only per-goal number a player is given in this wizard is critical_path's,
# computed for the goal they actually picked.
# (key, label, years-or-None, one-line description)
HORIZON_MODES = (
    ("challenge", "Challenge", 400,
     "a tight run - enough calendar for the default goal if you play well, "
     "with little room left over for bad luck"),
    ("standard", "Standard", 500,
     "the game's own long-standing default"),
    ("relaxed", "Relaxed", 650,
     "room to recover from genuinely bad luck"),
    ("endless", "Endless", None,
     "no deadline at all - play until you choose to stop"),
)

# WHAT "ENDLESS" ACTUALLY IS: a very large, ordinary, finite number of years,
# not a true absence of one. A save file, `state`'s own JSON reply, and every
# bit of arithmetic anywhere in this engine that reads a horizon
# (`end_year - year`, `start_year + horizon_years`, and so on) expects a
# plain number, never `None` or infinity - and this file is not the place to
# teach all of those call sites a special "no limit" value, several of which
# live in protocol.py. 9,999 years is the answer instead: an order of
# magnitude past the longest dice-free floor measured for any civilisation
# above (1,019, for Rome) and further past that than any real game has ever
# been played, so nobody playing an actual game reaches it - which is the
# only property "endless" needs to have in practice. `run`/`compare`/`plan`
# and flag-driven `play`/`agent` never see this constant at all: it is
# reached only from the New Game wizard and the in-game 'options' command
# choosing it explicitly, never from a bare --horizon flag, whose own
# argparse default (500) is completely unchanged by any of this.
ENDLESS_HORIZON_YEARS = 9999


def _is_endless_horizon(end_year, start_year):
    """Whether an end_year amounts to the Endless mode above, for display
    purposes only - nothing about how the game actually runs checks this;
    it only decides whether a screen says 'no deadline' or a specific year."""
    return (end_year - start_year) >= ENDLESS_HORIZON_YEARS


# A founder's whole working life in hours: used only to say how big a number is, never to gate what a player can do.
# It is computed from the config's founder_hours_per_year and founder_life_mean (ui/founder_budget.py), never typed.
def _founder_lifetime_hours(cfg=None):
    """Founder-hours a whole working life holds: hours/year * expected
    working years, both read from `cfg` if given (a live Sim's config, which
    may override either) and otherwise from DEFAULTS - the same source
    the founder's hours ledger (sim/labour/labour_hours.py) and mortality draw
    (sim/scenario/rules.py) read.
    """
    return founder_budget(DEFAULTS, cfg)[2]


def _civ_for_session(args):
    """Which civilisation to start, honouring the save above the command line.

    A save says what game it is. Resuming should not need the flag repeated,
    and a flag that contradicts the file should say so rather than start the
    wrong game over the top of it, even when the contradicting command line
    is one the game itself printed for the player to reuse.
    """
    session = getattr(args, "session", None)
    asked = getattr(args, "civ", None)
    if session and os.path.exists(session) and not _is_claimed_slot(session):
        saved = civ_of_save(session)
        if saved:
            if asked and asked != saved:
                # Said out loud on stdout, where the player is looking, and then
                # a non-zero exit. A refusal only argparse can see is a refusal
                # nobody reads.
                print("that save is a %s game; you asked for %s. Drop the --civ "
                      "flag to resume it, or point --session somewhere else."
                      % (saved, asked))
                raise SystemExit(1)
            return saved
    return asked or default_civilisation_id()


def _goal_for_session(args, tree, nodes):
    """Which goal to start the strategy order for, honouring the save above
    the command line - same reasoning and same shape as _civ_for_session
    just above, and for the same reason: the order `load_strategy` hands
    back depends on the goal's own closure (see load_strategy's goal
    argument), so a resumed game has to know its goal BEFORE that call, not
    only after load_state runs.
    """
    session = getattr(args, "session", None)
    asked = getattr(args, "goal", None)
    if session and os.path.exists(session) and not _is_claimed_slot(session):
        saved = goal_of_save(session)
        if saved and saved in nodes:
            if asked and asked != saved:
                print("that save is playing toward %s; you asked for %s. Drop "
                      "the --goal flag to resume it, or point --session "
                      "somewhere else." % (saved, asked))
                raise SystemExit(1)
            return saved
    return resolve_goal(tree, nodes, asked)


def _horizon_explicit():
    """True if --horizon appeared on the actual command line this process was
    started with, as opposed to argparse's default of 500 that is present in
    `args.horizon` whether or not anyone typed it. A flag typed by hand always
    outranks anything remembered from an earlier sitting."""
    return any(tok == "--horizon" or tok.startswith("--horizon=")
              for tok in sys.argv)


def _resolve_horizon(args, session):
    """How many years this sitting gets: the --horizon flag if it was
    actually typed, otherwise whatever the horizon was last set to for this
    save (see the in-game 'options' command and the New Game wizard, both of
    which write it to session.meta.json - see settings.py's module docstring
    for why that lives beside the save rather than inside it), otherwise the
    flag's ordinary default. A save nobody ever touched 'options' or the menu
    for has no meta file, so this returns exactly args.horizon and nothing about
    the flag-driven path changes.
    """
    if session and not _horizon_explicit():
        meta = settings.load_session_meta(session)
        horizon_years = meta.get("horizon_years")
        if isinstance(horizon_years, (int, float)) and horizon_years > 0:
            return int(horizon_years)
    return args.horizon


# THE APPLICATION'S OWN DISPLAY WIDTH - see _apply_display_prefs below and
# settings.py's module docstring ("DISPLAY WIDTH"). Starts at the number
# this file's own _wrap always hardcoded, so a process that never calls
# _apply_display_prefs (nothing in this file does on import; every
# human-facing entry point calls it exactly once, at its own top) renders
# exactly as it always did.
_DISPLAY_WIDTH = 76


def _apply_display_prefs(cfg=None):
    """Read the application's display preferences once and apply them for
    the rest of this process: how wide a line wraps (here, and in
    protocol.py's renderers - see protocol.DISPLAY_WIDTH's own comment),
    how many rows a long table pages by default (protocol.
    DEFAULT_AVAILABLE_LIMIT), and which mine commission milestones to show
    in rendered text. Returns the config, so a caller that already
    needs it (cmd_menu, _new_game, _options_menu) is not reading the file
    twice.

    CALLED FROM EVERY HUMAN-FACING ENTRY POINT - cmd_menu and cmd_play - and
    from NOWHERE in cmd_agent. `agent` speaks a stable JSON protocol (and,
    with --pretty, a readable rendering alongside it) that a script or
    another process depends on looking the same regardless of whose
    terminal, or whose saved preferences, happen to be on the machine it
    runs on; a human's own cosmetic choices about their own terminal have no
    business changing what a script sees. See settings.py's module
    docstring for where these preferences actually live.
    """
    if cfg is None:
        cfg = settings.load_config()
    global _DISPLAY_WIDTH
    _DISPLAY_WIDTH = settings.resolve_display_width(cfg)
    _protocol.DISPLAY_WIDTH = _DISPLAY_WIDTH
    _protocol.DEFAULT_AVAILABLE_LIMIT = settings.resolve_rows_per_page(cfg)
    _protocol.COMMISSION_DISPLAY = settings.resolve_commission_display(cfg)
    cli_units_options.apply_saved_preferences(cfg)
    return cfg


def _wrap(text, width=None, indent="   "):
    if width is None:
        width = _DISPLAY_WIDTH
    words, lines, cur = text.split(), [], ""
    for word in words:
        if len(cur) + len(word) + 1 > width:
            lines.append(indent + cur); cur = word
        else:
            cur = (cur + " " + word).strip()
    if cur:
        lines.append(indent + cur)
    return "\n".join(lines)


def _resuming_a_save(args):
    """Whether the sitting resumes a save, so the Sim need not open its own economy (the save holds it)."""
    session = getattr(args, "session", None)
    return bool(session and not _is_claimed_slot(session) and os.path.exists(session))


def _is_claimed_slot(path):
    """A session file that exists but holds nothing yet.

    _pick_session_filename claims its name by creating the file, so between
    the menu picking a name and the first command being saved there is a
    zero-byte file on disk. That is a NEW GAME, not a corrupt save, and
    treating it as one made a freshly started game unresumable.
    """
    try:
        return os.path.getsize(path) == 0
    except OSError:
        return False


def _pick_session_filename(civ_id):
    """A save name for a game the menu is about to start, picked so it never
    silently overwrites an existing one.

    An absolute path into the save directory (see settings.resolve_save_dir):
    ~/.rome-saves by default, or wherever a player has redirected saves to
    from the Options menu, ROME_SAVE_DIR, or both. This is a different path
    from the one `_unsafe_path` in protocol.py governs - that one is for the
    typed/JSON 'save' command, a deliberately sandboxed relative filename
    beside wherever the game was started; this one is for the file the menu
    and --session write to after every command, which has always been
    allowed to be absolute.
    """
    # CLAIMED, NOT MERELY CHECKED. This tested os.path.exists and returned the
    # name without creating anything, so six games started at once all saw the
    # same gap and all picked the same file name: five of them overwrote each
    # other, under a banner promising you can resume exactly where you left
    # off. O_EXCL makes the check and the claim one operation.
    #
    # And it counts UP FROM THE HIGHEST rather than filling the first gap, so
    # moving a save out of the directory does not turn its number into a slot
    # some later game takes.
    # IN A DIRECTORY OF ITS OWN. Save files must not accumulate in the
    # repository root beside the source. A game that writes a file after
    # every command has to put them somewhere a person can find and delete -
    # and, now, somewhere a player stuck with a non-persistent $HOME can move
    # away from entirely. See settings.py's module docstring.
    save_dir = settings.resolve_save_dir()
    civ_id = os.path.join(save_dir, civ_id)
    highest = 1
    prefix = civ_id + "_"
    try:
        for save_name in (os.path.join(save_dir, filename) for filename in os.listdir(save_dir)):
            if save_name.startswith(prefix) and save_name.endswith(".json"):
                try:
                    highest = max(highest, int(save_name[len(prefix):-5]))
                except ValueError:
                    pass
    except OSError:
        pass
    attempt = highest if os.path.exists("%s.json" % civ_id) else 1
    while True:
        candidate = ("%s.json" % civ_id) if attempt == 1 else ("%s_%d.json" % (civ_id, attempt))
        try:
            os.close(os.open(candidate, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644))
            return candidate
        except FileExistsError:
            attempt += 1
        except OSError:
            # Cannot write here at all; hand back a name and let `save` report
            # the real error rather than looping for ever.
            return candidate
