"""The main menu's Options screen, generated from settings_table.SETTINGS.

Preferences about the program, plus the defaults a new game starts from.
Each row says when it applies; one that is only read when a game starts says
so instead of being hidden. `agent` games reach the same table through the
`options` command (proto/dispatch_options.py).
"""
import os

from sim.engine import settings, settings_table
from . import cli_units_options
from .cli import _apply_display_prefs, _wrap


def _ask_yes_no(prompt, current):
    """y or n, or None for blank, end of input or anything else."""
    try:
        answer = input(prompt % ("y" if current else "n")).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    return {"y": True, "yes": True, "n": False, "no": False}.get(answer)


def _edit_setting(cfg, key):
    """Show what the setting means, read a new value, save it. Returns cfg."""
    spec = settings_table.SETTINGS[key]
    print(_wrap(spec.description))
    if not spec.editable:
        print("   -- set by the New Game wizard, which remembers your last answers.")
        return cfg
    if spec.kind == "units":
        return cli_units_options.edit_display_units(cfg, cfg.get("default_civ"), input)
    if key == "save_dir" and os.environ.get(settings.SAVE_DIR_ENV):
        print(_wrap("Note: %s is set to %r right now and overrides this until it is unset."
                    % (settings.SAVE_DIR_ENV, os.environ[settings.SAVE_DIR_ENV])))
    current = settings_table.display_value(key, cfg)
    if spec.kind == "flag":
        answer = _ask_yes_no("   %s? [y/n, now %%s]: " % spec.label, cfg.get(key))
        if answer is None:
            return cfg
        raw = answer
    else:
        hint = ", ".join(spec.choices) if spec.choices else "blank to leave unchanged"
        try:
            raw = input("   New value [now %s; %s]: " % (current, hint)).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return cfg
    value, problem = settings_table.parse_value(key, raw)
    if problem:
        print("   -- %s." % problem)
    elif value is not settings_table.UNCHANGED:
        cfg[key] = value
        settings.save_config(cfg)
        print("   -- saved.")
    return cfg


def options_menu(cfg):
    """Loop on the generated screen until the player goes back. Returns cfg."""
    while True:
        cfg = _apply_display_prefs(cfg)
        print()
        print("-" * 78)
        print("   OPTIONS")
        print("-" * 78)
        print(_wrap("Preferences about this PROGRAM, and the defaults a new game "
                    "starts from. A row marked 'applies when a game starts' is read "
                    "when you begin a game and cannot change one already running; "
                    "inside a game, `options` offers the few things that can."))
        print()
        for line in settings_table.screen_lines(cfg):
            print(line)
        print("   b) back to the main menu")
        try:
            words = input("\n   > ").strip().lower().split()
        except (EOFError, KeyboardInterrupt):
            print()
            return cfg
        if not words or words[0] in ("b", "back"):
            return cfg
        key = settings_table.find(words[0])
        if key is None:
            print("   -- 1 to %d, or b." % len(settings_table.SETTINGS))
        else:
            cfg = _edit_setting(cfg, key)
