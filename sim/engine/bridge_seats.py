"""Bridge entries the seats module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old code did,
and is never cached. The seat registry (`state.seats`, the facades, `act_as`) stays on `Sim`, so the registry views and the
commands that change it are applied here for good. The `legacy_*` views are state the module shares with the engine; they go
when that state moves."""
from sim.assembly.api import KEYED, QUOTE
from sim.refusal import Refusal
from sim.seats.api import ForgetGoalCaches, MoveSeat, RegisterSeat, RememberGoalClosure

from . import state_paths
from .bridge import bridge_command, bridge_view
from .data import kit_capital as kit_capital_of, win_condition_describe
from .seat_defaults import default_policy
from .seat_handover_empty import holds_that_would_be_lost
from .seat_move import move_seat
from .state_seat import COUNTRY_SEAT, seat_from_template

# ---- the seat registry ----


@bridge_view("legacy_seats")
def legacy_seats(sim):
    """Every seat's saved state, by seat id (the live registry)."""
    return sim.state.seats


@bridge_view("seat_party", kind=KEYED)
def seat_party(sim, seat_id):
    """The seat as an actor an exchange can deal with."""
    return sim.seat_party(seat_id)


@bridge_view("seat_party_with_margins", kind=QUOTE)
def seat_party_with_margins(sim, seat_id, margins):
    """The seat as a party to an exchange, with what each concern it runs earns a year."""
    return sim.seat_party(seat_id, margins)


@bridge_view("seat_holds", kind=KEYED)
def seat_holds(sim, seat_id):
    """What the seat holds in the engine's own state that a handover to it would overwrite."""
    return holds_that_would_be_lost(sim.state.seats[seat_id])


@bridge_view("society_techs", seat_scoped=True)
def society_techs(sim):
    """The techniques the society holds now (its own at the start, and what its firms and government have since learnt)."""
    return sim._society_held_techs()


@bridge_view("kit_capital", kind=QUOTE)
def kit_capital(sim, kit_id):
    """A starting kit's money at the opening wage of this civilisation."""
    return kit_capital_of(kit_id, sim.civ)


@bridge_view("founder_life_terms")
def founder_life_terms(sim):
    """What a new founder's lifespan is drawn from."""
    return {"immortal": sim.cfg["immortal"], "minimum": sim.FOUNDER_MIN_REMAINING_LIFE_YEARS,
            "mean": sim.cfg["founder_life_mean"], "spread": sim.cfg["founder_life_sd"]}


@bridge_command(RegisterSeat)
def register_seat(sim, command):
    if command.seat_id in sim.state.seats:
        return Refusal("seat_exists", "seat %r already exists" % (command.seat_id,), seat=command.seat_id)
    seat = seat_from_template(command.template, command.capital, default_policy(sim.manual))
    sim.add_seat(command.seat_id, seat)
    seat.modules["seats"].life_left = command.founder_years
    with sim.act_as(command.seat_id):
        sim._wrap_seat_containers()
        if seat.kind == COUNTRY_SEAT:
            seat.holder = sim.view("state_treasury")().actor_id
    return None


@bridge_command(MoveSeat)
def apply_move_seat(sim, command):
    return move_seat(sim, command.from_id, command.to_id)


@bridge_command(RememberGoalClosure)
def remember_goal_closure(sim, command):
    sim._goal_closure = command.nodes


@bridge_command(ForgetGoalCaches)
def forget_goal_caches(sim, command):
    sim.forget_goal_caches()


# ---- the founder's death ----

@bridge_view("patronage", seat_scoped=True)
def patronage(sim):
    """The founder's age and the deputies the programme could go on with: {founder_age, deputies, deputy_hours,
    deputies_carry_the_work}."""
    return {"founder_age": sim.founder_age(), "deputies": sim.view("staff")()["directors_extra"], "deputy_hours": sim.deputy_hours(),
            "deputies_carry_the_work": sim.deputies_carry_the_work()}


@bridge_view("dissolution_terms")
def dissolution_terms(sim):
    """The heuristics of a programme left without its founder (declared on `Sim`)."""
    return {"life_extension_years": sim.SANITATION_LIFE_EXTENSION_YEARS, "years_before_forgetting": sim.DISSOLUTION_YEARS_BEFORE_FORGETTING,
            "forget_fraction_divisor": sim.DISSOLUTION_FORGET_FRACTION_DIVISOR, "years_until_end": sim.DISSOLUTION_YEARS_UNTIL_END}


# ---- goals and what they read ----

@bridge_view("win_condition_text", kind=QUOTE)
def win_condition_text(sim, node):
    return win_condition_describe(node)


@bridge_view("legacy_goal_closure")
def legacy_goal_closure(sim):
    """What the goal needs, as the game keeps it for the labour package and the screens too (None until worked out): a debt."""
    return getattr(sim, "_goal_closure", None)


@bridge_view("game_attribute", kind=QUOTE)
def game_attribute(sim, path):
    """What the game holds under a plain attribute name, or None (an attribute-sourced win condition reads it)."""
    held = state_paths.plain_attribute(sim, path)
    return sim.view("staff")().get(path) if held is None else held   # the people the workforce module holds (slaves, scholars, ...)


