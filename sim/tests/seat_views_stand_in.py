"""The seats module's views over a state that holds its seats, for stand-in games: each answers from the seat's own slot
with the module's list rules, so a test sets the facts in the slots and reads them through the views."""
from sim.seats import lists
from sim.seats.state import SeatsSeat


def slots_of(seats):
    """The seats module's state for each seat of a registry, by seat id."""
    return {seat_id: seat.modules["seats"] for seat_id, seat in seats.items()}


def give_seats_slots(state):
    """Give every seat of a state built by hand the seats module's state, as the assembly does for a game; answers the state."""
    for seat in state.seats.values():
        seat.modules.setdefault("seats", SeatsSeat())
    return state


def seat_views(state):
    """{view name: answer} for the views a stand-in game with `state.seats` publishes."""
    def slots():
        return slots_of(state.seats)

    def seat_list():
        held = slots()
        return {"joined": list(held), "households": lists.household_seats(held), "playing": lists.seats_playing(held)}

    return {"registered_seats": lambda: list(state.seats), "seat_list": seat_list,
            "seat_country": lambda seat_id: slots()[seat_id].country if seat_id in state.seats else None,
            "seat_kind": lambda seat_id: slots()[seat_id].kind, "seat_holder": lambda seat_id: slots()[seat_id].holder,
            "ended_seats": lambda: lists.seats_ended(slots())}
