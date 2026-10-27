"""The knowledge module's spec (sim/assembly).

Its reads are views of owners that have not moved yet, published by the engine bridge (sim/engine/bridge_knowledge.py)
under the name the owner will publish, except the `legacy_*` ones: the state the module still shares with the engine (the
tree, the held and heard-of sets of the acting seat, every seat's held sets, the fog switch). They go when that state
moves. Every view is uncached: the held set, the heard-of set and the done-year record are written outside the module's
commands (docs/architecture/catalogue/knowledge.md lists each writer), and the engine replaces the tree object."""
from sim.assembly.api import KEYED, QUOTE, ModuleSpec, ViewSpec

from .commands import ForgetTechnique, LearnTechnique, RevealFrom, RevealNodes
from .module import DONE, REVEALED, Knowledge
from sim.production.api import RefreshDoneCaches
from .state import KnowledgeSeat

READS_BY_OWNER = {
    "projects": ("start_check", "relied_on_running", "legacy_projects"),
    "mechanics": ("corpus_hedge_tiers",),
    "seats": ("on_road_to_goal", "legacy_seats"),
    "core": ("legacy_tree", "legacy_fog", "category_trait"),
}

_LIVE = dict(cached=False)

MODULE_SPECS = (ModuleSpec(
    "knowledge", Knowledge, channels=(DONE, REVEALED), seat_state=KnowledgeSeat,
    publishes=(
        ViewSpec("tree", "tree", kind=KEYED, **_LIVE),
        ViewSpec("tree_nodes", "tree_nodes", **_LIVE),
        ViewSpec("techniques_held", "techniques_held", channels=(DONE,), seat_scoped=True, **_LIVE),
        ViewSpec("techniques_granted", "techniques_granted", channels=(DONE,), seat_scoped=True, **_LIVE),
        ViewSpec("techniques_forgotten", "techniques_forgotten", channels=(DONE,), seat_scoped=True, **_LIVE),
        ViewSpec("done_year", "done_year", channels=(DONE,), seat_scoped=True, **_LIVE),
        ViewSpec("earliest_done_year", "earliest_done_year", kind=QUOTE),
        ViewSpec("corpus_hedge", "corpus_hedge", seat_scoped=True, **_LIVE),
        ViewSpec("visibility", "visibility", kind=QUOTE, seat_scoped=True),
        ViewSpec("visible_to_player", "visible_to_player", kind=QUOTE, seat_scoped=True),
        ViewSpec("prerequisite_message", "prerequisite_message", kind=QUOTE, seat_scoped=True),
        ViewSpec("fog_scrub", "fog_scrub", kind=QUOTE, seat_scoped=True),
        ViewSpec("fog_summary", "fog_summary", kind=QUOTE),
        ViewSpec("never_abandon", "never_abandon", kind=KEYED, seat_scoped=True, **_LIVE),
    ),
    applies=((LearnTechnique, "learn_technique"), (ForgetTechnique, "forget_technique"), (RevealFrom, "reveal_from"),
             (RevealNodes, "reveal_nodes")),
    reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
    sends=(RefreshDoneCaches,),
),)
