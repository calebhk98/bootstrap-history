"""One-line forwarders from `Sim` to the seats module, for callers not yet in a module.

Each goes when its last caller reads the view (`sim.view(name)`) or sends the command itself."""
from sim.refusal import Refusal
from sim.seats.api import HandOverSeat, JoinCastSeats, JoinSeat


def _raised_if_refused(answer):
    """The old join raised ValueError for a seat it could not add; a refusal is that error's message."""
    if isinstance(answer, Refusal):
        raise ValueError(str(answer))
    return answer


class ForwardSeatsMixin:

    def playing_seats(self):
        return self.view("seat_list")()["playing"]

    def ended_seats(self):
        return self.view("ended_seats")()

    def run_over(self):
        return self.view("run_over")()

    def join_seat(self, seat_id, template):
        _raised_if_refused(self.send(JoinSeat(seat_id, template)))
        return self.state.seats[seat_id]

    def join_cast_seats(self):
        return _raised_if_refused(self.send(JoinCastSeats()))

    def hand_over_seat(self, from_id, to_id):
        return self.send(HandOverSeat(from_id, to_id))

    def forget_goal_caches(self):
        """Drop everything derived from the current goal."""
        for name in ("_goal_closure", "_goal_critical_floor"):
            self.__dict__.pop(name, None)
