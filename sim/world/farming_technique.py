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



def entries_by_axis(declarations):
    """Group technology declarations into {axis: {node id: table entry}}.

    A declaration is {"axis": "rotation"|"toolkit"|"crop", "entry": <name of an
    entry in sim.world.agriculture>}, taken from a node's `farming_technique`.
    """
    grouped = {"rotation": {}, "toolkit": {}, "crop": {}}
    for node_id, declaration in declarations.items():
        grouped[declaration["axis"]][node_id] = getattr(agriculture, declaration["entry"])
    return grouped


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


def technique_from_adoption(adoption, declarations):
    """Technique for `adoption` (technology id -> adopted share, 0..1), given the
    technologies' `farming_technique` declarations (node id -> declaration)."""
    entries = entries_by_axis(declarations)
    crop = DEFAULT_TECHNIQUE.crop
    for node_id in sorted(entries["crop"]):
        crop = _blend(crop, entries["crop"][node_id], adoption.get(node_id, 0.0))
    return Technique(
        crop,
        _axis(DEFAULT_TECHNIQUE.rotation, entries["rotation"], adoption),
        _axis(DEFAULT_TECHNIQUE.toolkit, entries["toolkit"], adoption))


def hours_per_hectare(technique):
    """Labour hours one hectare takes at this technique's reference intensity."""
    return (technique.crop.base_labour_hours_per_hectare
            * technique.toolkit.labour_hours_multiplier)
