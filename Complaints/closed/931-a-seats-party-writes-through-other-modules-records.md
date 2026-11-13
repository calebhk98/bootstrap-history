# A seat's party in an exchange writes through the seats module's dealings and the ventures module's business

**Status:** closed - the seat's party sends semantic commands that the seats module applies with the exchange's own plain-figure rules; the ventures views hand out copies.

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

**Closed.**
- The exchange's rules are functions of plain figures (`sim/agents/dealing_figures.py`: release and receive a patent, add a licensee, give and take
  shares, keep, drop and lapse offers). An actor's record applies them to itself (`sim/agents/record_dealings.py`); the seats module applies them
  to a seat's stored figures when it receives `ReleasePatent`, `ReceivePatent`, `AddLicensee`, `GiveShares`, `TakeShares`, `KeepOffer`,
  `DropOffer`, `DropLapsedOffers` and `NextOfferSerial` (`sim/seats/dealings.py`). The seat's record sends those commands instead of a whole
  field; `SetDealing` and the tracked copies are deleted.
- Every read of a seat's dealing is a fresh copy from the owner, so a figure held across another party's write is the caller's own copy and a
  new read sees the write (`test_seat_record_by_command`, two records for one seat).
- The ventures' views `operating`, `mothballed` and `operating_by_seat` return frozensets.
- Tests: `test_dealing_figures` (the rules with written-out figures), `test_seat_party_ports` (the seats module applying each command),
  `test_seat_record_by_command`, `test_seat_dealings`, `test_seat_as_actor`, `test_projects_and_ventures_seat_state`.
