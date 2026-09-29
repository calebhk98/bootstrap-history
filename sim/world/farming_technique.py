"""A society's farming technique, derived from the technologies it holds.

Standalone like sim.world.agriculture: no engine imports. Each technology
that changes how food is grown points at an entry in the agriculture tables
(rotation, toolkit, crop); a society's technique is those entries, each
weighted by how much of the society has adopted the technology.
"""
import collections

from sim.constants import declare
from sim.world import agriculture

Technique = collections.namedtuple("Technique", ["crop", "rotation", "toolkit"])

DEFAULT_TECHNIQUE = Technique(
    agriculture.DEFAULT_CROP, agriculture.DEFAULT_ROTATION, agriculture.DEFAULT_TOOLKIT)

# Which table entry each technology brings.
ROTATION_TECHNOLOGIES = {
    "crop_rotation": agriculture.THREE_FIELD,
    "fud_three_field_rotation": agriculture.THREE_FIELD,
}
TOOLKIT_TECHNOLOGIES = {
    "horse_collar": agriculture.HORSE_COLLAR_AND_MOULDBOARD,
    "fud_heavy_mouldboard_plough_coulter": agriculture.HORSE_COLLAR_AND_MOULDBOARD,
    "fud_mechanical_reaper": agriculture.MECHANICAL_REAPER,
    "ag2_reaper": agriculture.MECHANICAL_REAPER,
}
CROP_TECHNOLOGIES = {
    "mat_newworld_crops": agriculture.POTATOES,
}

TECHNIQUE_TECHNOLOGY_IDS = tuple(sorted(
    set(ROTATION_TECHNOLOGIES) | set(TOOLKIT_TECHNOLOGIES) | set(CROP_TECHNOLOGIES)))

# Which way is "better" for each numeric field, per table.
_BETTER_IS_LOWER = {
    "fallow_share_of_holding", "labour_hours_multiplier",
}

ADOPTION_HALF_LIFE_YEARS = declare(
    "ADOPTION_HALF_LIFE_YEARS", 25.0, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="Years for half the farms of a society to take up a farming "
        "technology after it first exists there. A neighbour can copy a "
        "better field without reading anything; not fitted to a source.")


def adoption_share(age_years):
    """Share of a society using a technology `age_years` after it arrived."""
    return 1.0 - 0.5 ** (max(0.0, age_years) / ADOPTION_HALF_LIFE_YEARS)


def _blend(base, other, share):
    """Move every numeric field of `base` toward `other` by `share`."""
    fields = {name: value + share * (getattr(other, name) - value)
              for name, value in base._asdict().items()
              if isinstance(value, (int, float))}
    return base._replace(**fields)


def _best_per_field(entries):
    """Combine several entries of one table: each numeric field takes the
    most favourable value any of them offers."""
    combined = entries[0]
    for entry in entries[1:]:
        fields = {}
        for name, value in combined._asdict().items():
            if not isinstance(value, (int, float)):
                continue
            candidate = getattr(entry, name)
            fields[name] = (min if name in _BETTER_IS_LOWER else max)(value, candidate)
        combined = combined._replace(**fields)
    return combined


def _axis(default, table, adoption):
    entries = [_blend(default, table[node_id], adoption[node_id])
               for node_id in sorted(table) if adoption.get(node_id, 0.0) > 0.0]
    return _best_per_field(entries) if entries else default


def technique_from_adoption(adoption):
    """Technique for `adoption`: technology id -> adopted share (0..1)."""
    crop = DEFAULT_TECHNIQUE.crop
    for node_id in sorted(CROP_TECHNOLOGIES):
        crop = _blend(crop, CROP_TECHNOLOGIES[node_id], adoption.get(node_id, 0.0))
    return Technique(
        crop,
        _axis(DEFAULT_TECHNIQUE.rotation, ROTATION_TECHNOLOGIES, adoption),
        _axis(DEFAULT_TECHNIQUE.toolkit, TOOLKIT_TECHNOLOGIES, adoption))


def hours_per_hectare(technique):
    """Labour hours one hectare takes at this technique's reference intensity."""
    return (technique.crop.base_labour_hours_per_hectare
            * technique.toolkit.labour_hours_multiplier)
