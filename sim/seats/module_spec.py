"""The seats module's spec (sim/assembly).

Its reads are views of owners that have not moved yet, published by the engine bridge (sim/engine/bridge_seats.py and the
other bridge files) under the name the owner will publish, except the `legacy_*` ones: the seat registry, the acting seat's
projects and fog switch, the actor registry, the agent economy's world and the game's random source, all state the module
still shares with the engine. They go when that state moves. Every view is uncached: the registry, a founder's death and
the held sets are written outside the module's commands (docs/architecture/catalogue/seats.md lists each writer)."""
from sim.assembly.api import FIRST, KEYED, QUOTE, ExtensionPoint, ModuleSpec, PhaseHook, ViewSpec
from sim.diffusion.api import RekeyDisclosures
from sim.knowledge.api import ForgetTechnique, LearnTechnique, RevealNodes
from sim.reporting.api import RecordEvent

from .commands import (AnswerOffer, ApplyForPatent, EndRun, ForgetGoalCaches, HandOverSeat, JoinCastSeats, JoinSeat, MakeOffer,
                       MoveSeat, RecordGoalReached, RegisterSeat, RememberGoalClosure, SetFounderLife, SetGoal, SetPolicy)
from .module import Seats
from .state import SeatsSeat

READS_BY_OWNER = {
    "core": ("legacy_seats", "legacy_fog", "legacy_dice", "civilisation", "year", "price_index", "kit_capital",
             "founder_life_terms", "game_attribute", "legacy_goal_closure", "tree_closure"),
    "knowledge": ("tree", "tree_nodes", "techniques_held", "techniques_granted"),
    "mechanics": ("running_mechanics", "corpus_dispersed", "patronage", "losable_node_ids"),
    "projects": ("legacy_projects",),
    "diffusion": ("disclosures", "copy_difficulty", "literacy"),
    "actors": ("seeded_actor_registry", "cast", "actor_world", "seat_party", "seat_party_with_margins"),
    "workforce": ("seat_base_tile",),
    "materials": ("generation_breakdown",),
    "hazards": ("hazard_relief", "hazard_relief_entries"),
    "engine (registry)": ("seat_holds", "dissolution_terms"),
}

_LIVE = dict(cached=False)

MODULE_SPECS = (ModuleSpec(
    "seats", Seats, seat_state=SeatsSeat,
    publishes=(
        ViewSpec("acting_seat", "acting_seat", **_LIVE),
        ViewSpec("acting_country", "acting_country", seat_scoped=True, **_LIVE),
        ViewSpec("seat_list", "seat_list", **_LIVE),
        ViewSpec("ended_seats", "ended_seats", **_LIVE),
        ViewSpec("run_over", "run_over", **_LIVE),
        ViewSpec("played_countries", "played_countries", **_LIVE),
        ViewSpec("governed_countries", "governed_countries", **_LIVE),
        ViewSpec("seat_holders", "seat_holders", kind=QUOTE, **_LIVE),
        ViewSpec("built_by_any_seat", "built_by_any_seat", kind=QUOTE, **_LIVE),
        ViewSpec("seat_place", "seat_place", kind=KEYED, **_LIVE),
        ViewSpec("distance_between_seats", "distance_between_seats", kind=QUOTE, **_LIVE),
        ViewSpec("goal", "goal", seat_scoped=True, **_LIVE),
        ViewSpec("on_road_to_goal", "on_road_to_goal", kind=QUOTE, seat_scoped=True, **_LIVE),
        ViewSpec("founder", "founder", seat_scoped=True, **_LIVE),
        ViewSpec("dead_reasons", "dead_reasons", **_LIVE),
        ViewSpec("win_condition_value", "win_condition_value", kind=QUOTE, seat_scoped=True, **_LIVE),
        ViewSpec("win_condition_anatomy", "win_condition_anatomy", kind=QUOTE, seat_scoped=True, **_LIVE),
        ViewSpec("dealing_party", "dealing_party", seat_scoped=True, **_LIVE),
        ViewSpec("dealings_listing", "dealings_listing", seat_scoped=True, **_LIVE),
    ),
    applies=((JoinSeat, "join_seat"), (JoinCastSeats, "join_cast_seats"), (HandOverSeat, "hand_over_seat"),
             (SetGoal, "set_goal"), (RecordGoalReached, "record_goal_reached"), (ApplyForPatent, "apply_for_patent"),
             (MakeOffer, "make_offer"), (AnswerOffer, "answer_offer"), (EndRun, "end_run"),
             (SetFounderLife, "set_founder_life"), (SetPolicy, "set_policy")),
    reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
    sends=(RegisterSeat, MoveSeat, ForgetGoalCaches, RememberGoalClosure, LearnTechnique, ForgetTechnique, RevealNodes, RekeyDisclosures, RecordEvent),
    phases=(PhaseHook("hear_of_other_seats", "hear_of_other_seats"), PhaseHook("win_conditions", "check_win_conditions"),
            PhaseHook("founder_mortality", "founder_mortality")),
    # (condition) -> [(label, value, unit)] rows for a measurement goal's anatomy, or None for the shipped rows
    extension_points=(ExtensionPoint("win_condition_rows", FIRST),),
),)
