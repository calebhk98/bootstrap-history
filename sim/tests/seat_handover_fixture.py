"""Two or three seats on the real root state, with the alias rebinding a handover needs (shared by the handover tests)."""
from sim.engine import game_assembly
from sim.engine.mod_stores import StoreBook
from sim.engine.state import FounderState, HouseholdState, ProjectsState, ScenarioState, SimulationState
from sim.engine.state_seat import FIRST_SEAT_ID, bind_seat, seat_from_template
from sim.seats.api import HandOverSeat


class Game:
    """Two or three seats on the real root state, with the alias rebinding the handover needs."""

    def __init__(self, seat_ids):
        first = seat_ids[0]
        self.state = SimulationState(household=HouseholdState(capital=10.0), projects=ProjectsState(), founder=FounderState())
        self.state.seats[first] = self.state.seats.pop(FIRST_SEAT_ID)
        self.state.acting_seat = first
        self.state.scenario = ScenarioState(year=100)
        for seat_id in seat_ids[1:]:
            self.state.seats[seat_id] = seat_from_template({}, 5.0, {})
        bind_seat(self.state, first)
        self._seat_facades = {seat_id: None for seat_id in self.state.seats}
        self.session_seat = None
        self.year = 100
        self.civ = {"id": "home"}
        self.assembly = game_assembly.build(None, False)
        game_assembly.attach(self)

    def view(self, name):
        return self.assembly.views[name]

    def send(self, command):
        return self.assembly.handlers[type(command)](command)

    def hand_over_seat(self, from_id, to_id):
        return self.send(HandOverSeat(from_id, to_id))

    def _switch_seat(self, seat_id):
        bind_seat(self.state, seat_id)
        game_assembly.switch_seat(self, seat_id)

    def _reset_economic_caches(self):
        pass

    @property
    def stores(self):
        return StoreBook(self.state.stores)

    def ended_seats(self):
        return [seat_id for seat_id, held in self.state.seats.items() if held.founder.dead_reason]

    def act_as(self, seat_id):
        import contextlib

        @contextlib.contextmanager
        def acting():
            previous = self.state.acting_seat
            bind_seat(self.state, seat_id)
            try:
                yield self
            finally:
                if previous in self.state.seats:
                    bind_seat(self.state, previous)
        return acting()
