"""Bridge entries the seats module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old code did,
and is never cached. The seat registry (`state.seats`, the facades, `act_as`) stays on `Sim`, so the registry views and the
commands that change it are applied here for good. The `legacy_*` views are state the module shares with the engine; they go
when that state moves."""
from sim.assembly.api import KEYED, QUOTE
from sim.refusal import Refusal
from sim.seats.api import COUNTRY_SEAT, ForgetGoalCaches, MoveSeat, RegisterSeat, SetSeatHolder

from . import state_paths
from .bridge import bridge_command, bridge_view
from .seat_defaults import default_policy
from .seat_handover_empty import holds_that_would_be_lost
from .seat_move import move_seat
from .state_seat import seat_from_template

# ---- the seat registry ----


@bridge_view("registered_seats")
def registered_seats(sim):
    """The ids of the seats in the registry, in the order they joined."""
    return list(sim.state.seats)


@bridge_view("acting_as", kind=QUOTE)
def acting_as(sim, seat_id):
    """A context in which `seat_id` is the acting seat; the root aliases return to the previous seat on leaving it."""
    return sim.act_as(seat_id)


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


@bridge_command(RegisterSeat)
def register_seat(sim, command):
    if command.seat_id in sim.state.seats:
        return Refusal("seat_exists", "seat %r already exists" % (command.seat_id,), seat=command.seat_id)
    seat = seat_from_template(command.template, command.capital, default_policy(sim.manual))
    sim.add_seat(command.seat_id, seat)
    seat.modules["seats"].life_left = command.founder_years
    with sim.act_as(command.seat_id):
        sim._wrap_seat_containers()
        if seat.modules["seats"].kind == COUNTRY_SEAT:
            sim.send(SetSeatHolder(sim.view("state_treasury")().actor_id))
    return None


@bridge_command(MoveSeat)
def apply_move_seat(sim, command):
    return move_seat(sim, command.from_id, command.to_id)


@bridge_command(ForgetGoalCaches)
def forget_goal_caches(sim, command):
    sim.__dict__.pop("_goal_critical_floor", None)


# ---- the founder's death ----

# ---- goals and what they read ----

@bridge_view("game_attribute", kind=QUOTE)
def game_attribute(sim, path):
    """What the game holds under a plain attribute name, or None (an attribute-sourced win condition reads it)."""
    held = state_paths.plain_attribute(sim, path)
    return sim.view("staff")().get(path) if held is None else held   # the people the workforce module holds (slaves, scholars, ...)


