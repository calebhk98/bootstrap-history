"""The mechanics module's spec (sim/assembly).

Its reads are views of owners that have not moved yet, published by the engine bridge (sim/engine/bridge_mechanics.py)
under the name the owner will publish. Every view is uncached: the tree is replaced by the engine (a re-derivation of
the nodes) and what is running is written outside any command."""
from sim.assembly.api import KEYED, QUOTE, ModuleSpec, ViewSpec

from .module import Mechanics

READS_BY_OWNER = {
    "knowledge": ("tree_nodes", "techniques_held"),
    "production": ("running", "institution_units"),
    "workforce": ("money_per_labour_hour",),
}

_LIVE = dict(cached=False)

MODULE_SPECS = (ModuleSpec(
    "mechanics", Mechanics,
    publishes=(
        ViewSpec("mechanic", "mechanic", kind=KEYED, **_LIVE),
        ViewSpec("running_mechanics", "running_mechanics", kind=QUOTE, seat_scoped=True),
        ViewSpec("capability_sets", "capability_sets", **_LIVE),
        ViewSpec("staff_capacity_sources", "staff_capacity_sources", **_LIVE),
        ViewSpec("room_sources", "room_sources", **_LIVE),
        ViewSpec("labour_productivity_sources", "labour_productivity_sources", **_LIVE),
        ViewSpec("hazard_counter_rows", "hazard_counter_rows", **_LIVE),
        ViewSpec("effect_terms", "effect_terms", kind=QUOTE),
        ViewSpec("effect_holds", "effect_holds", kind=QUOTE, seat_scoped=True),
        ViewSpec("effect_value", "effect_value", kind=QUOTE, seat_scoped=True),
        ViewSpec("effects_in_force", "effects_in_force", kind=QUOTE, seat_scoped=True),
        ViewSpec("effect_values", "effect_values", kind=QUOTE, seat_scoped=True),
        ViewSpec("effect_sum", "effect_sum", kind=QUOTE, seat_scoped=True),
        ViewSpec("effect_factor", "effect_factor", kind=QUOTE, seat_scoped=True),
        ViewSpec("effect_best", "effect_best", kind=QUOTE, seat_scoped=True),
        ViewSpec("corpus_nodes", "corpus_nodes", **_LIVE),
        ViewSpec("corpus_hedge_tiers", "corpus_hedge_tiers", **_LIVE),
        ViewSpec("corpus_dispersed", "corpus_dispersed", kind=QUOTE),
        ViewSpec("corpus_diffusion_pace", "corpus_diffusion_pace", seat_scoped=True, **_LIVE),
        ViewSpec("approval_patron", "approval_patron", kind=QUOTE),
        ViewSpec("school_node", "school_node", **_LIVE),
        ViewSpec("patrons_lost_to_eminence", "patrons_lost_to_eminence", **_LIVE),
    ),
    reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
),)
