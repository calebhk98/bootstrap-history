"""Which seats are playing, who a seat plays for, and joining a seat."""
from typing import Any, Dict, List, Optional

from sim.refusal import Refusal

from . import country, join_rules, lists
from .commands import JoinCastSeats, JoinSeat, RegisterSeat


class Run:

    def seat_list(self) -> Dict[str, List[str]]:
        """{joined: every seat's id, playing: the household seats whose run has not ended}, in joining order."""
        seats = self.needs.legacy_seats()
        return {"joined": list(seats), "playing": lists.seats_playing(seats)}

    def ended_seats(self) -> List[str]:
        """Ids of the seats whose run has ended."""
        return lists.seats_ended(self.needs.legacy_seats())

    def run_over(self) -> bool:
        """Whether no seat has anything more to play."""
        return lists.run_is_over(self.needs.legacy_seats())

    def acting_seat(self) -> Optional[str]:
        """The id of the seat acting now."""
        return self.clock.acting_seat

    def acting_country(self) -> Optional[str]:
        """The partner country the acting seat belongs to, or None for the game's own country: the markets, wages and
        prices the seat deals in are that country's own."""
        return country.partner_country_of_seat(self.needs.legacy_seats(), self.clock.acting_seat,
                                               self.needs.civilisation().get("id"))

    def played_countries(self) -> List[str]:
        """The countries a country seat plays, sorted."""
        home = self._home()
        return sorted({seat.country or home for seat in self.needs.legacy_seats().values()
                       if getattr(seat, "kind", None) == join_rules.COUNTRY_SEAT})

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
        if template.get("kind") == join_rules.COUNTRY_SEAT:
            held = join_rules.country_of(template, self._home())
            if held not in self.governed_countries():
                return join_rules.no_government_refusal(seat_id, held)
            template = join_rules.country_seat_template(template, held, self._home())
        life = self.needs.founder_life_terms()
        years = join_rules.founder_years(life["immortal"], life["minimum"], life["mean"], life["spread"],
                                         self.needs.legacy_dice().gauss)
        return self.needs.send(RegisterSeat(seat_id, template, capital, years))

    def join_cast_seats(self, command: JoinCastSeats) -> Any:
        """Add the seats the civilisation's cast lists for the start of the game: their ids, or the refusal that stopped it."""
        joined = []
        for template in join_rules.cast_templates(self.needs.civilisation().get("cast")):
            seat_id = template["id"]
            if seat_id not in self.needs.legacy_seats():
                answer = self.join_seat(JoinSeat(seat_id, template))
                if isinstance(answer, Refusal):
                    return answer
                joined.append(seat_id)
        return joined
