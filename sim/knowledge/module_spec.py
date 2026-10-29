"""The knowledge module's spec (sim/assembly).

Its reads are views of owners that have not moved yet, published by the engine bridge (sim/engine/bridge_knowledge.py) under
the name the owner will publish, except the `legacy_*` ones: the tree and the fog switch, state the module still shares with
the engine. They go when that state moves. What a seat holds, has heard of and has forgotten is the module's own seat state,
written only by its commands, so the views over it are cached on the channels those commands bump; the tree is replaced by
the engine, so the views over it are uncached."""
from sim.assembly.api import KEYED, QUOTE, ModuleSpec, ViewSpec

from .commands import (ForgetTechnique, HandOverTechniques, LearnTechnique, ReceiveTechniques, RevealFrom, RevealNodes,
                       StartDoneYearRecord)
from .module import DONE, REVEALED, Knowledge
from sim.production.api import RefreshDoneCaches
from .state import KnowledgeSeat

READS_BY_OWNER = {
    "projects": ("start_check", "relied_on_running", "active_projects"),
    "mechanics": ("corpus_hedge_tiers", "corpus_dispersed"),
    "seats": ("on_road_to_goal", "seat_list"),
    "core": ("legacy_tree", "legacy_fog", "category_trait"),
}

_LIVE = dict(cached=False)

MODULE_SPECS = (ModuleSpec(
    "knowledge", Knowledge, channels=(DONE, REVEALED), seat_state=KnowledgeSeat,
    publishes=(
        ViewSpec("tree", "tree", kind=KEYED, **_LIVE),
        ViewSpec("tree_nodes", "tree_nodes", **_LIVE),
        ViewSpec("tree_closure", "tree_closure", kind=QUOTE),
        ViewSpec("critical_path", "critical_path", kind=QUOTE),
        ViewSpec("hard_prerequisites", "hard_prerequisites", kind=KEYED, **_LIVE),
        ViewSpec("techniques_held", "techniques_held", channels=(DONE,), seat_scoped=True),
        ViewSpec("techniques_revealed", "techniques_revealed", channels=(REVEALED,), seat_scoped=True),
        ViewSpec("techniques_granted", "techniques_granted", channels=(DONE,), seat_scoped=True),
        ViewSpec("techniques_by_seat", "techniques_by_seat", **_LIVE),
        ViewSpec("techniques_forgotten", "techniques_forgotten", channels=(DONE,), seat_scoped=True, **_LIVE),
        ViewSpec("losable_node_ids", "losable_node_ids", kind=QUOTE, seat_scoped=True),
        ViewSpec("done_year", "done_year", channels=(DONE,), seat_scoped=True),
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
             (RevealNodes, "reveal_nodes"), (ReceiveTechniques, "receive_techniques"),
             (StartDoneYearRecord, "start_done_year_record"), (HandOverTechniques, "hand_over_techniques")),
    reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
    sends=(RefreshDoneCaches,),
),)
