"""One-line forwarders from `Sim` to the seats module, for callers not yet in a module.

Each goes when its last caller reads the view (`sim.view(name)`) or sends the command itself."""
from sim.refusal import Refusal
from sim.seats.api import (AnswerOffer, ApplyForPatent, HandOverSeat, JoinCastSeats, JoinSeat, MakeOffer, RecordGoalReached,
                           SetGoal)


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

    def acting_country(self):
        return self.view("acting_country")()

    def governed_countries(self):
        return self.view("governed_countries")()

    def society_techs_now(self):
        return set(self.view("society_techs")())

    def join_seat(self, seat_id, template):
        _raised_if_refused(self.send(JoinSeat(seat_id, template)))
        return self.state.seats[seat_id]

    def join_cast_seats(self):
        return _raised_if_refused(self.send(JoinCastSeats()))

    def hand_over_seat(self, from_id, to_id):
        return self.send(HandOverSeat(from_id, to_id))

    def seat_place(self, seat_id):
        return self.view("seat_place")[seat_id]

    def dealing_party(self):
        return self.view("dealing_party")()

    def dealings_listing(self):
        return self.view("dealings_listing")()

    def seat_patent(self, node_id):
        return self.send(ApplyForPatent(node_id))

    def seat_offer(self, to, give, take):
        return self.send(MakeOffer(to, give, take))

    def seat_answer(self, offer_id, accept):
        return self.send(AnswerOffer(offer_id, accept))

    def set_goal(self, node_id):
        self.send(SetGoal(node_id))

    def record_goal_reached(self, node_id, year):
        self.send(RecordGoalReached(node_id, year))

    def win_condition_anatomy(self, condition):
        return self.view("win_condition_anatomy")(condition)

    def _win_condition_value(self, condition):
        return self.view("win_condition_value")(condition)

    def forget_goal_caches(self):
        """Drop everything derived from the current goal."""
        for name in ("_goal_closure", "_goal_critical_floor"):
            self.__dict__.pop(name, None)
