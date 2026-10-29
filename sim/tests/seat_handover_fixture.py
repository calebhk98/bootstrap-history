"""Two or three seats on the real root state, with the alias rebinding a handover needs (shared by the handover tests)."""
import random
from sim.engine import game_assembly
from sim.engine.state import FounderState, HouseholdState, SimulationState
from sim.engine.state_seat import FIRST_SEAT_ID, bind_seat, seat_from_template
from sim.scenario.api import OpenScenario, ScenarioSources
from sim.seats.api import HandOverSeat


class Game:
    """Two or three seats on the real root state, with the alias rebinding the handover needs."""

    def __init__(self, seat_ids):
        first = seat_ids[0]
        self.state = SimulationState(household=HouseholdState(capital=10.0), founder=FounderState())
        self.state.seats[first] = self.state.seats.pop(FIRST_SEAT_ID)
        self.state.acting_seat = first
        for seat_id in seat_ids[1:]:
            self.state.seats[seat_id] = seat_from_template({}, 5.0, {})
        bind_seat(self.state, first)
        self._seat_facades = {seat_id: None for seat_id in self.state.seats}
        self.session_seat = None
        self.year = 100
        self.civ = {"id": "home"}
        self.assembly = game_assembly.build(None, False)
        self.send(OpenScenario(
            civilisation=self.civ, configuration={"start_year": 100}, manual=False, events=True, bounty_set=set(),
            sources=ScenarioSources(load_civilisation=lambda civilisation_id: {"id": civilisation_id}, kit_capital=lambda kit, civ: 0.0,
                                    display_units=lambda: ({"units": {}}, {}, dict)), dice=random.Random(0)))
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
        return self.view("store_book")()

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
