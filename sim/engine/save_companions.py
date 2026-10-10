"""What sits beside a session save: a plain-text summary and a few rotating checkpoint copies.

The summary is for a person who cannot open the save; the checkpoints are for a hosted container
whose last write was bad. Neither is read by the game when it loads a save, and a failure to write
either is ignored: the save itself is what matters."""
import os
import shutil

from sim.constants import declare
from sim.engine.saveload import save_state

CHECKPOINTS_KEPT = declare(
    "CHECKPOINTS_KEPT", 5, kind="temporary_heuristic", unit="copies of a session save",
    why="How many year-start copies of a session save are kept before the oldest is deleted; "
        "enough to step back a few years after a bad choice, small enough that the folder "
        "stays a few saves in size. A storage trade-off, not a game rule.")

SUMMARY_SUFFIX = ".summary.txt"
BACKUP_FOLDER_SUFFIX = ".backups"


def summary_text(sim):
    """A short readable description of the game as it stands."""
    state = sim.state
    return "\n".join([
        "Bootstrap History save",
        "civilisation: %s" % sim.civ.get("id"),
        "year: %s" % sim.year,
        "goal: %s" % sim.goal,
        "capital: %.0f" % sim.capital,
        "projects done: %d" % len(sim.done),
        "written by game version: %s" % state._game_version,
        "seed: %s" % state._seed,
        "",
        "This file is only a description. Play on with: play --session <the save file next to this one>.",
        "",
    ])


def checkpoint_folder(path):
    return path + BACKUP_FOLDER_SUFFIX


def _checkpoint_name(path, year):
    suffix = ".json.gz" if path.endswith(".gz") else ".json"
    return "year_%s%s" % (year, suffix)


def _write_summary(sim, path):
    text = summary_text(sim)
    summary_path = path + SUMMARY_SUFFIX
    try:
        with open(summary_path, encoding="utf-8") as handle:
            if handle.read() == text:
                return
    except OSError:
        pass
    with open(summary_path, "w", encoding="utf-8") as handle:
        handle.write(text)


def _write_checkpoint(sim, path, kept):
    folder = checkpoint_folder(path)
    target = os.path.join(folder, _checkpoint_name(path, sim.year))
    if os.path.exists(target):
        return
    os.makedirs(folder, exist_ok=True)
    shutil.copyfile(path, target)
    copies = sorted((os.path.join(folder, name) for name in os.listdir(folder)),
                    key=lambda copy: (os.stat(copy).st_mtime_ns, copy))
    for stale in copies[:max(0, len(copies) - kept)]:
        os.remove(stale)


def save_session(sim, path, kept=CHECKPOINTS_KEPT):
    """`save_state` for a session file, plus its summary and a checkpoint of the first save in each game year."""
    save_state(sim, path)
    try:
        _write_summary(sim, path)
        _write_checkpoint(sim, path, kept)
    except OSError:
        pass
    return path
