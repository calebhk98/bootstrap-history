# A seat's party in an exchange writes through the seats module's dealings and the ventures module's business

**Status:** partly - the party no longer holds or writes any record of the seats or ventures modules; what remains is that the seats' command replaces a stored field and does not apply the exchange's rule.

The actors module builds a seat's party for an exchange (`sim/actors/seat_parties.py`). The exchange (sim/agents) changes a party's record in place
for every actor, so the seat's patents, shares held, shares issued and offers (the seats module's stored dealings) and its plants (the ventures
module's business) used to be handed to it live and changed without a command of their owners.

**Done.** The party holds views only (`HouseholdParty`, `Ports` in `sim/actors/seat_parties.py`):
- Dealings: the view `seat_dealings` publishes a copy of the stored fields; `SeatRecord` (`sim/agents/household_party.py`) reads a fresh copy on
  every access, made of tracked dicts and lists (`sim/agents/tracked.py`) that report each change, deep ones too; the party sends the seats module
  `SetDealing(seat_id, field, value)` with the figure the deal left, and the seats module applies it (`Dealings.set_dealing`).
- Plants: the party reads `operating`, `venture_opened_year` and `venture_size`, and hands plants over with the ventures commands `ReleasePlant`
  and `AdoptPlant`. The view `seat_business` is gone.
- Tests: `sim/tests/test_seat_record_by_command.py` (the tracked figures, the record's writes, the party's plant moves, the ports' commands),
  `sim/tests/test_seat_party_ports.py` (`TheOwnersKeepTheirRecords`: the published copy, `set_dealing`, `apply_release_plant`,
  `apply_adopt_plant`), `sim/tests/test_seat_dealings.py` and `sim/tests/test_seat_as_actor.py` (a patent sale, an offer and shares through the
  real exchange).

**Remains.**
- `SetDealing` replaces a whole stored field. The exchange's rules (`patent.hand_over`, `joint_stock.hand_over`, `exchange.make_offer`) run on the
  party's copy, so the seats module cannot validate the move or apply it itself; a semantic command (grant a patent, move shares, keep an offer)
  needs those rules to be functions of plain figures that the seats module also calls, which is a redesign of the exchange.
- Two parties for the same seat built in one dealing each read the owner's figure on every access, so they agree, but a figure held across another
  party's write is stale; nothing does this now.
- The ventures' views `operating` and `mothballed` still hand out the business's own sets (read only by convention).
