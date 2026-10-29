"""Bridge entries the seats module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old code did,
and is never cached. The seat registry (`state.seats`) stays on `Sim`; the commands that change it are applied here for good. The `legacy_*` views are state the module shares with the engine; they go
when that state moves."""
from sim.ledger.api import OpenPurse
from sim.refusal import Refusal
from sim.seats.api import COUNTRY_SEAT, ForgetGoalCaches, MoveSeat, RegisterSeat, SetSeatHolder

from .bridge import bridge_command, bridge_view
from .seat_defaults import default_policy
from .seat_move import move_seat
from .state_seat import seat_from_template

# ---- the seat registry ----


@bridge_view("society_techs", seat_scoped=True)
def society_techs(sim):
    """The techniques the society holds now (its own at the start, and what its firms and government have since learnt)."""
    return sim._society_held_techs()


@bridge_command(RegisterSeat)
def register_seat(sim, command):
    if command.seat_id in sim.state.seats:
        return Refusal("seat_exists", "seat %r already exists" % (command.seat_id,), seat=command.seat_id)
    seat = seat_from_template(command.template, default_policy(sim.manual))
    sim.add_seat(command.seat_id, seat)
    if seat.modules["seats"].kind != COUNTRY_SEAT:   # a country seat acts through its government and holds nothing of its own
        sim.send(OpenPurse(command.seat_id, float(command.capital)))   # the capital is already in the society's coin
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
