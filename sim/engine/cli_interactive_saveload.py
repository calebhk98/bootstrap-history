"""Mid-game save/load browsing, and the civilisation list both this file
and cli_interactive.py's menu/new-game code read from disk.

Split out of cli_interactive.py, which kept the "game loop" and "new game /
menu" pieces together because they call each other directly and repeatedly
(see that file's own docstring). This module is the other side of that
split: the part of the original file that IS close to a leaf - everything
here either calls only other functions in this module, or calls nothing at
all. Verified with the `ast` module, not by reading names: walking the call
graph among the original file's 15 top-level functions shows every
cross-module edge running cli_interactive.py -> here, and none the other
way, with one exception this module avoids by construction - `_load_game`
(cli_interactive.py) itself calls `cmd_play` (also cli_interactive.py) to
resume the game it just loaded, so `_load_game` stayed on that side of the
split rather than moving here with the rest of the save-browsing code it
otherwise resembles. `_load_civ_list` moved here rather than staying with
`cmd_menu`/`cmd_play`/`_new_game` for the same structural reason: it is a
leaf itself, but `_save_listing` below calls it, and keeping it on the
other side would have made THIS module depend on that one too - turning a
one-directional import into the same two-way cycle this split exists to
avoid.

Nothing in this module calls back into cli_interactive.py, and nothing here
should ever need to - if a change makes that necessary, the two modules'
reason for being split is gone and they belong back together, not wired
with a workaround.
"""

import json, os

from .data import CIVDIR, closure, load
from . import settings
from .protocol import load_state, save_state

from .cli import _pick_session_filename, _wrap


# ----------------------------------------------------------------------------
# SESSION COMMANDS, TYPED DIRECTLY WHILE PLAYING - no backing out to the main
# menu and back in. A player who had just won the whole game said autosaves
# plus the manual saves they made at moments that mattered to them were a
# real part of how they played, and none of 'saves' (what do I have),
# 'load' (switch to a different one) or 'menu' (go back without losing this
# one) existed as something you could simply type. 'save <file>' and
# 'load <file>' already worked mid-game - they are the JSON protocol's own
# sandboxed commands (see protocol.py's SAVE_SUFFIXES/_unsafe_path and help
# topic 'save'/'load'), reachable here because cmd_play's loop hands every
# typed line to the same parser and dispatcher the JSON protocol uses. What
# did not exist was anything that knows about the SAVE DIRECTORY cli.py
# itself manages (settings.resolve_save_dir, settings.list_saves) - the bare
# forms below, intercepted in cmd_play before a line ever reaches that
# parser, the same way 'options' already is.
# ----------------------------------------------------------------------------

def _ingame_saves(cfg, session):
    """'saves', typed bare mid-game: what is in the configured save
    directory, without leaving for the main menu's Load screen. Read-only -
    'load', typed bare, is what switches this session to one of them."""
    save_dir, rows, civ_index, need = _save_listing(cfg)
    print()
    print("-" * 78)
    print("   SAVES  (in %s)" % save_dir)
    print("-" * 78)
    if not rows:
        print(_wrap("Nothing there yet."))
        print()
        return
    cur_abs = os.path.abspath(session) if session else None
    for i, row in enumerate(rows, 1):
        marker = ("<- this game" if cur_abs
                  and os.path.abspath(row["path"]) == cur_abs else None)
        _print_save_row(i, row, civ_index, need, marker)
    print(_wrap("'load' switches this session to one of these; 'save' on "
                "its own keeps a new copy of exactly this moment, alongside "
                "whatever this game is already autosaving to."))
    print()


def _pick_milestone_filename(civ_id):
    """A distinct filename for a manual, in-play 'save' - never the name
    --session is already autosaving to, so a milestone asked for by name is
    never quietly overwritten by the very next ordinary turn's autosave.
    Same claim-by-creating discipline as _pick_session_filename, for the
    same reason: two milestones saved in the same second must not collide."""
    save_dir = settings.resolve_save_dir()
    prefix = os.path.join(save_dir, civ_id) + "_saved_"
    attempt = 1
    while True:
        candidate = "%s%d.json" % (prefix, attempt)
        try:
            os.close(os.open(candidate, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644))
            return candidate
        except FileExistsError:
            attempt += 1
        except OSError:
            return candidate


def _ingame_save_milestone(s, session):
    """'save', typed bare mid-game (no filename): a snapshot of exactly this
    moment, kept in the managed save directory alongside whatever --session
    is already autosaving to - so a player can come back to THIS point
    later even after the ongoing game has moved well past it. 'save <file>'
    with a name is untouched: that is still the JSON protocol's own
    sandboxed save, a relative path beside wherever the game was started."""
    path = _pick_milestone_filename(s.civ.get("id") or "game")
    try:
        save_state(s, path)
    except OSError as e:
        print("   -- could not write there: %s" % e)
        return
    # MARKED AS FROZEN, in the file's own sidecar - not only by its name. See
    # settings.is_checkpoint for why both signals exist: the filename alone
    # (matched by _pick_milestone_filename's own pattern) already says this is
    # a milestone, but this marker is what keeps that true if the file is
    # later renamed through the game's own "move this save" option, which
    # already carries a sidecar's fields to the new name
    # (settings.move_session_meta).
    settings.save_session_meta(path, {"checkpoint": True})
    print("   -- saved a copy of %d AD to %s" % (s.year, path))
    if session:
        print("      (this game's ongoing save at %s is untouched, and keeps "
              "saving after every command as before)" % session)


def _ingame_load(cfg, s, session, a):
    """'load', typed bare mid-game: switch this running game to a different
    save in the managed directory, without going back to the main menu.
    Returns the session path to use from here on - unchanged if nothing was
    picked or the load was refused. 'load <file>' with a name is untouched:
    that is still the JSON protocol's own sandboxed relative load.

    A save from a different civilisation is refused, loudly, by load_state
    itself (_validate_save checks `_civ` against this running game's own) -
    not re-checked here, so there is exactly one place that decides it.
    """
    save_dir, rows, civ_index, need = _save_listing(cfg)
    print()
    print("-" * 78)
    print("   LOAD A DIFFERENT SAVE  (in %s)" % save_dir)
    print("-" * 78)
    if not rows:
        print(_wrap("Nothing there to switch to."))
        print()
        return session
    for i, row in enumerate(rows, 1):
        _print_save_row(i, row, civ_index, need)
    print("   b) never mind, keep playing this one")
    try:
        raw = input("\n   Which one? [1-%d, or b] " % len(rows)).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print(); return session
    if raw in ("", "b", "back", "q", "quit"):
        return session
    if not (raw.isdigit() and 1 <= int(raw) <= len(rows)):
        print("   -- a number from the list above, or b.")
        return session
    chosen = rows[int(raw) - 1]["path"]
    try:
        load_state(s, chosen)
    except Exception as e:
        print("   -- could not load %s: %s" % (chosen, e))
        return session
    # THE HORIZON, AGAIN, THE SAME WAY _resolve_horizon DOES AT STARTUP. It
    # is not part of what load_state restores (see settings.py's module
    # docstring) - it lives in a sidecar keyed to THIS filename, so switching
    # files means reading that file's own sidecar, not keeping whatever
    # horizon the game just left behind.
    meta = settings.load_session_meta(chosen)
    horizon_years = meta.get("horizon_years")
    if isinstance(horizon_years, (int, float)) and horizon_years > 0:
        s.cfg["horizon_years"] = int(horizon_years)
        s.end_year = s.cfg["start_year"] + int(horizon_years)
    # A STALE "already said the ending" FLAG WOULD LIE HERE TWICE OVER: it
    # could suppress the scoreboard for a save that HAD already ended, or
    # (after this session later ends on its own) skip announcing THAT ending
    # because some earlier game's flag was still set. Either way, a load is
    # a new look at a position this process has not narrated yet.
    a._said_end = False
    # A CHECKPOINT SWITCHED TO IS STILL A CHECKPOINT - same guarantee as a
    # checkpoint named on the command line (see cmd_play's own comment on
    # `checkpoint_source`, right above the equivalent check there): switching
    # this running game to a frozen milestone must not turn the very next
    # command into the write that unfreezes it. This is the one other place
    # besides cmd_play/cmd_agent that can point the ongoing autosave at a
    # file, so it needs the identical fork.
    if settings.is_checkpoint(chosen):
        forked = _pick_session_filename(s.civ.get("id") or "game")
        save_state(s, forked)
        print("   -- switched to the checkpoint at %s: %d AD. A checkpoint "
              "stays exactly as it is - nothing you do now writes back into "
              "it. From here on, this game is autosaving to %s instead."
              % (chosen, s.year, forked))
        return forked
    print("   -- switched to %s: %d AD." % (chosen, s.year))
    return chosen


def _load_civ_list():
    civs = []
    for civ_filename in sorted(os.listdir(CIVDIR)):
        if not civ_filename.endswith(".json") or civ_filename.startswith("_"):
            continue
        civs.append(json.load(open(os.path.join(CIVDIR, civ_filename))))
    civs.sort(key=lambda c: c.get("year", 0))
    return civs


def _save_listing(cfg):
    """(save_dir, rows, civ_index, need) - everything both `_load_game` (the
    main-menu door) and `_ingame_saves`/`_ingame_load` (the same list, typed
    mid-game - see PLAYER REQUEST #3 below) print a save row from. One
    implementation, so the two screens cannot quietly drift apart the way
    the fog-progress fraction almost did when this was still duplicated.
    """
    tree, prices, nodes, wages, goods = load()
    default_goal = tree["meta"]["goal_node"]
    # EACH SAVE NAMES ITS OWN GOAL NOW (see protocol.py's _goal/save_state),
    # so the closure a save's progress is measured against has to be THAT
    # goal's, not always the transistor's.
    _need_cache = {}
    def _need_for(goal_id):
        goal_id = goal_id if goal_id in nodes else default_goal
        hit = _need_cache.get(goal_id)
        if hit is None:
            hit = _need_cache[goal_id] = closure(nodes, goal_id)
        return goal_id, hit
    civ_index = {civ_record["id"]: civ_record for civ_record in _load_civ_list()}
    save_dir = settings.resolve_save_dir(cfg)
    rows = settings.list_saves(save_dir)
    # EACH ROW CARRIES ITS OWN GOAL AND ITS OWN CLOSURE. _need_for above was
    # written for this and then never wired to the rows, because the save-row
    # renderer was factored out in a different branch at the same time; a
    # listing that measured every save against the transistor's 168 nodes would
    # report a save playing a five-node lifetime goal as 3/168 done.
    for _row in rows:
        _gid, _gneed = _need_for(_row.get("goal"))
        _row["goal_id"] = _gid
        _row["goal_name"] = nodes.get(_gid, {}).get("name", _gid)
        _row["goal_need"] = _gneed
    # The fourth element is the DEFAULT goal's closure, kept only as the
    # fallback a row without a readable goal uses. Each row carries its own
    # above, which is the number that actually gets printed.
    _default_gid, _default_need = _need_for(None)
    return save_dir, rows, civ_index, _default_need


def _print_save_row(i, r, civ_index, need, marker=None):
    """The lines `_load_game`, `_ingame_saves` and `_ingame_load` all print
    for one save: which civilisation, how far along, when it was last
    touched. A save played WITH fog does not get the goal-progress fraction
    shown here: that number (X of Y toward the transistor) says how big the
    whole tree is, which is exactly what fog exists to keep a player from
    knowing before they have earned it, and a listing screen is not exempt
    from that just because no Sim object exists yet.
    """
    if not r["readable"]:
        print("   %d) %s" % (i, r["filename"]))
        print("      could not be read as a save from this game; skipping "
              "its details")
        print()
        return
    civ_record = civ_index.get(r["civ_id"], {})
    name = civ_record.get("name", r["civ_id"] or "unknown civilisation")
    start = civ_record.get("year")
    year = r["year"]
    elapsed = ("  (%d years in)" % (year - start)
              if isinstance(start, (int, float)) and isinstance(year, (int, float))
              else "")
    print("   %d) %s%s" % (i, r["filename"], "   %s" % marker if marker else ""))
    print("      %s  -  now %s AD%s" % (name, year, elapsed))
    status = []
    if r.get("goal_year"):
        # NAMED, because there are seventeen goals now and "reached the
        # transistor" is wrong for sixteen of them. Safe to name even for a
        # fogged save: this one was finished, so the player knows what it was.
        status.append("REACHED %s in %s AD"
                      % ((r.get("goal_name") or "its goal").upper(),
                         r["goal_year"]))
    elif r.get("dead_reason"):
        status.append("ended: %s" % r["dead_reason"])
    elif r.get("founder_alive") is False:
        status.append("founder has died")
    done = r.get("done") or []
    if r["fog"]:
        status.append("%d technologies built" % len(done))
    else:
        _need = r.get("goal_need") or need
        progress = len(_need.intersection(done))
        status.append("%d/%d toward %s"
                      % (progress, len(_need), r.get("goal_name") or "the goal"))
    status.append("fog %s" % ("on" if r["fog"] else "off"))
    if r.get("reputation") is not None:
        status.append("rep %.0f" % r["reputation"])
    print("      " + "  |  ".join(status))
    print("      last played %s" % settings.humanize_age(r["mtime"]))
    print()
