"""The 'display units' entry of the options menus (Complaint 285).

One preference per dimension, saved in the application config like the other
options. Nothing chosen means every quantity is shown in the civilisation's own
units when its file names some, else exactly as the game writes it. Commands
take the units their help names, or another unit of the same kind given as a
`unit` (`buy farm 10 acre`).
"""
from sim.engine.ui_port import settings, units
from sim.engine.ui_port import summary_line


def apply_saved_preferences(cfg):
    units.set_preferences(settings.resolve_display_units(cfg))


def edit_display_units(cfg, civ_id, ask_line):
    """Walk the player through one dimension at a time. `ask_line(prompt)` returns
    the typed answer (blank leaves the dimension unchanged, 'default' clears it)."""
    registry = units.registry()
    chosen = dict(settings.resolve_display_units(cfg))
    for dimension in registry["dimensions"]:
        options = units.available_units(registry, dimension, civ_id)
        print("   %s: now %s; choose from: %s"
              % (dimension, chosen.get(dimension) or units.CIV_DEFAULTS.get(dimension)
                 or "as the game writes it", ", ".join(options)))
        answer = ask_line("   %s unit (blank to keep, 'default' to clear): " % dimension).strip()
        if not answer:
            continue
        if answer.lower() == "default":
            chosen.pop(dimension, None)
        elif answer in options:
            chosen[dimension] = answer
        else:
            print("   -- %r is not one of those; unchanged." % answer)
    cfg["display_units"] = chosen
    settings.save_config(cfg)
    apply_saved_preferences(cfg)
    return cfg
