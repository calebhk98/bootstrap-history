"""Which seats are playing, who a seat plays for, and joining a seat."""
from typing import Any, Dict, List, Optional

from sim.assembly.api import AddSeat
from sim.ledger.api import OpenPurse
from sim.projects.api import WatchActive
from sim.refusal import Refusal
from sim.ventures.api import WatchBusiness
from sim.workforce.api import WatchStaff

from . import country, join_rules, lists
from .commands import JoinCastSeats, JoinSeat, SetSeatHolder
from .state import COUNTRY_SEAT, SeatsSeat


class Run:

    def _slots(self) -> Dict[str, SeatsSeat]:
        """This module's state for every seat, in joining order."""
        return {seat_id: self.seat_of(seat_id) for seat_id in self.needs.registered_seats()}

    def seat_list(self) -> Dict[str, List[str]]:
        """{joined: every seat's id, households: the seats that play through a household, playing: those whose run has not
        ended}, in joining order."""
        slots = self._slots()
        return {"joined": list(slots), "households": lists.household_seats(slots), "playing": lists.seats_playing(slots)}

    def ended_seats(self) -> List[str]:
        """Ids of the seats whose run has ended."""
        return lists.seats_ended(self._slots())

    def run_over(self) -> bool:
        """Whether no seat has anything more to play."""
        return lists.run_is_over(self._slots())

    def acting_seat(self) -> Optional[str]:
        """The id of the seat acting now."""
        return self.clock.acting_seat

    def acting_country(self) -> Optional[str]:
        """The partner country the acting seat belongs to, or None for the game's own country: the markets, wages and
        prices the seat deals in are that country's own."""
        return country.partner_country_of_seat(self._slots(), self.clock.acting_seat,
                                               self.needs.civilisation().get("id"))

    def seat_country(self, seat_id: str) -> Optional[str]:
        """The country a seat plays for when it names one (None: the game's own, or no such seat)."""
        return self.seat_of(seat_id).country if seat_id in self.needs.registered_seats() else None

    def seat_kind(self, seat_id: str) -> str:
        """Whether the seat plays through a household or holds a country's government."""
        return self.seat_of(seat_id).kind

    def seat_holder(self, seat_id: str) -> Optional[str]:
        """The actor id of the government a country seat holds (None for a household seat)."""
        return self.seat_of(seat_id).holder

    def set_seat_holder(self, command: SetSeatHolder) -> None:
        self.seat.holder = command.holder

    def played_countries(self) -> List[str]:
        """The countries a country seat plays, sorted."""
        home = self._home()
        return sorted({seat.country or home for seat in self._slots().values() if seat.kind == COUNTRY_SEAT})

    def governed_countries(self) -> List[str]:
        """The countries that have a government a country seat can hold, the game's own first."""
        registry = self.needs.seeded_actor_registry()
        home = self._home()
        others = sorted(name for name in registry.state.countries if name != home)
        return [name for name in [home] + others if registry.government_of(name) is not None]

    def _home(self) -> str:
        return str(self.needs.civilisation().get("id"))

    def join_seat(self, command: JoinSeat) -> Any:
        """Add a player from data. The template may carry `capital` (at this society's prices) or `kit`, `country`,
        `base_tile`, `starting_techs`, `scholars`, `artisans` and `goal`; nothing about the seat is named here."""
        seat_id, template = command.seat_id, command.template
        missing = join_rules.unknown_starting_techs(template, self.needs.tree_nodes())
        if missing:
            return join_rules.unknown_techs_refusal(seat_id, missing)
        capital = join_rules.capital_of(template, self.needs.price_index(), self.needs.kit_capital)
        if template.get("kind") == COUNTRY_SEAT:
            held = join_rules.country_of(template, self._home())
            if held not in self.governed_countries():
                return join_rules.no_government_refusal(seat_id, held)
            template = join_rules.country_seat_template(template, held, self._home())
        life = self.needs.founder_life_terms()
        years = join_rules.founder_years(life["immortal"], life["minimum"], life["mean"], life["spread"],
                                         self.needs.game_random().gauss)
        refusal = self.needs.send(AddSeat(seat_id, template))
        if refusal is not None:
            return refusal
        holds_nothing = template.get("kind") == COUNTRY_SEAT   # a country seat acts through its government and holds nothing of its own
        if not holds_nothing:
            self.needs.send(OpenPurse(seat_id, float(capital)))   # the capital is already in the society's coin
        self.seat_of(seat_id).life_left = years
        with self.needs.act_as(seat_id):
            self.needs.send(WatchBusiness(seat_id))
            self.needs.send(WatchActive(seat_id))
            self.needs.send(WatchStaff(seat_id))
            if holds_nothing:
                self.needs.send(SetSeatHolder(self.needs.state_treasury().actor_id))
        return None

    def join_cast_seats(self, command: JoinCastSeats) -> Any:
        """Add the seats the civilisation's cast lists for the start of the game: their ids, or the refusal that stopped it."""
        joined = []
        for template in join_rules.cast_templates(self.needs.civilisation().get("cast")):
            seat_id = template["id"]
            if seat_id not in self.needs.registered_seats():
                answer = self.join_seat(JoinSeat(seat_id, template))
                if isinstance(answer, Refusal):
                    return answer
                joined.append(seat_id)
        return joined
