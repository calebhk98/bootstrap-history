"""One line naming the display unit chosen for each dimension."""
from sim.engine import settings, units


def summary_line(cfg):
    chosen = settings.resolve_display_units(cfg)
    return ", ".join("%s: %s" % (dimension, chosen.get(dimension, "as the game writes it"))
                     for dimension in units.registry()["dimensions"])
