# A plague line names the national health sources of the acting seat, not the seat it is told to

**Status:** open

`Shocks.staff_loss_seats` (`sim/hazards/shocks.py`, `ShockYearMixin._shock_staff_loss_seats` before the move) builds each seat's
message after the `act_as` blocks have closed, so `national_sources_words()` reads the medical work built by whichever seat is acting
(the first playing seat), and every seat's line says "(medical work you built: ...)" about that seat's work. The sources are what the
country has adopted of medicine some seat built and the state holds, counted for the acting seat only (`techniques_held` and
`techniques_granted` are per seat). With two seats the second is told the first's sources as its own.

The module keeps this (a move does not change behaviour): the fix is to build each message
under `act_as(seat_id)`, or to name the sources without the "you built" and from every seat's work (`seat_holders`).
