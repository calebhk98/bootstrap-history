"""The seats module's spec (sim/assembly).

Every view is uncached: the registry, a founder's death and the held sets are written outside the module's commands
(docs/architecture/catalogue/seats.md lists each writer). The registry is the assembly's: the module adds and moves seats by the
assembly's commands `AddSeat` and `MoveSeat`."""
from sim.assembly.api import FIRST, KEYED, QUOTE, AddSeat, ExtensionPoint, ModuleSpec, MoveSeat, PhaseHook, ViewSpec
from sim.diffusion.api import RekeyDisclosures
from sim.knowledge.api import ForgetTechnique, LearnTechnique, RevealNodes
from sim.ledger.api import OpenPurse
from sim.projects.api import WatchActive
from sim.reporting.api import RecordEvent
from sim.ventures.api import StopOperating, WatchBusiness
from sim.workforce.api import WatchStaff

from .commands import (EndRun, ForgetGoalClosure, HandOverSeat, JoinCastSeats, JoinSeat, RecordGoalReached,
                       RememberGoalClosure, RememberGoalFloor, SetFounderLife, SetGoal, SetPolicy, SetSeatHolder)
from .module import Seats
from .state import SeatsSeat

READS_BY_OWNER = {
    "core": ("fog_of_war", "game_random", "civilisation", "year", "price_index", "kit_capital",
             "founder_life_terms", "tree_closure", "automation", "game_config"),
    "knowledge": ("tree", "tree_nodes", "techniques_held", "techniques_granted", "techniques_revealed", "techniques_by_seat"),
    "mechanics": ("running_mechanics", "corpus_dispersed", "losable_node_ids"),
    "content": ("win_condition_labels",),
    "workforce (people)": ("staff",),
    "ventures": ("operating", "operating_by_seat"),
    "diffusion": ("disclosures", "copy_difficulty", "literacy"),
    "actors": ("seeded_actor_registry", "cast", "actor_world", "state_treasury"),
    "workforce": ("seat_base_tile",),
    "materials": ("generation_breakdown",),
    "hazards": ("hazard_relief", "hazard_relief_entries"),
    "assembly": ("registered_seats", "seat_holds"),
}

_LIVE = dict(cached=False)

MODULE_SPECS = (ModuleSpec(
    "seats", Seats, seat_state=SeatsSeat,
    publishes=(
        ViewSpec("acting_seat", "acting_seat", **_LIVE),
        ViewSpec("acting_country", "acting_country", seat_scoped=True, **_LIVE),
        ViewSpec("seat_list", "seat_list", **_LIVE),
        ViewSpec("seat_country", "seat_country", kind=KEYED, **_LIVE),
        ViewSpec("seat_kind", "seat_kind", kind=KEYED, **_LIVE),
        ViewSpec("seat_holder", "seat_holder", kind=KEYED, **_LIVE),
        ViewSpec("ended_seats", "ended_seats", **_LIVE),
        ViewSpec("run_over", "run_over", **_LIVE),
        ViewSpec("played_countries", "played_countries", **_LIVE),
        ViewSpec("governed_countries", "governed_countries", **_LIVE),
        ViewSpec("seat_holders", "seat_holders", kind=QUOTE, **_LIVE),
        ViewSpec("built_by_any_seat", "built_by_any_seat", kind=QUOTE, **_LIVE),
        ViewSpec("seat_place", "seat_place", kind=KEYED, **_LIVE),
        ViewSpec("seats_holding_patent", "seats_holding_patent", kind=QUOTE, **_LIVE),
        ViewSpec("distance_between_seats", "distance_between_seats", kind=QUOTE, **_LIVE),
        ViewSpec("goal", "goal", seat_scoped=True, **_LIVE),
        ViewSpec("on_road_to_goal", "on_road_to_goal", kind=QUOTE, seat_scoped=True, **_LIVE),
        ViewSpec("founder", "founder", seat_scoped=True, **_LIVE),
        ViewSpec("automatic_policy", "automatic_policy", kind=QUOTE, seat_scoped=True, **_LIVE),
        ViewSpec("patronage", "patronage", seat_scoped=True, **_LIVE),
        ViewSpec("dissolution_terms", "dissolution_terms", **_LIVE),
        ViewSpec("goal_closure", "goal_closure", **_LIVE),
        ViewSpec("goal_critical_floor", "goal_critical_floor", seat_scoped=True, **_LIVE),
        ViewSpec("win_condition_text", "win_condition_text", kind=QUOTE, **_LIVE),
        ViewSpec("dead_reasons", "dead_reasons", **_LIVE),
        ViewSpec("win_condition_value", "win_condition_value", kind=QUOTE, seat_scoped=True, **_LIVE),
        ViewSpec("win_condition_anatomy", "win_condition_anatomy", kind=QUOTE, seat_scoped=True, **_LIVE),
        ViewSpec("seat_dealings", "seat_dealings", kind=KEYED, **_LIVE),
        ViewSpec("dealings_listing", "dealings_listing", seat_scoped=True, **_LIVE),
    ),
    applies=((JoinSeat, "join_seat"), (JoinCastSeats, "join_cast_seats"), (HandOverSeat, "hand_over_seat"),
             (SetGoal, "set_goal"), (RecordGoalReached, "record_goal_reached"), (EndRun, "end_run"),
             (SetFounderLife, "set_founder_life"), (SetPolicy, "set_policy"), (SetSeatHolder, "set_seat_holder"),
             (RememberGoalClosure, "remember_goal_closure"), (ForgetGoalClosure, "forget_goal_closure"),
             (RememberGoalFloor, "remember_goal_floor")),
    reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
    sends=(AddSeat, MoveSeat, OpenPurse, WatchActive, WatchBusiness, WatchStaff, LearnTechnique, ForgetTechnique, RevealNodes, RekeyDisclosures, RecordEvent, StopOperating),
    phases=(PhaseHook("hear_of_other_seats", "hear_of_other_seats"), PhaseHook("win_conditions", "check_win_conditions"),
            PhaseHook("founder_mortality", "founder_mortality")),
    # (condition) -> [(label, value, unit)] rows for a measurement goal's anatomy, or None for the shipped rows
    extension_points=(ExtensionPoint("win_condition_rows", FIRST),),
),)
