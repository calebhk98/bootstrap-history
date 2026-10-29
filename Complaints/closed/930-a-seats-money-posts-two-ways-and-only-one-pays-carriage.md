# A seat's money is posted two ways, and only one of them pays coin carriage

**Status:** closed - `SeatActor` is gone: the ledger builds one `SeatAccount` per command, a party in the book that stands at the home country's centre, so every payment of a seat is one posting between two accounts and pays coin carriage, as does the seat's exchange party (`HouseholdParty.stands_at_home`). `credit` and `debit` stay only for `CreditSeat` and `DebitSeat`, the one-sided movements a party sends when the other side is posted elsewhere. Tests: `sim/tests/test_coin_carriage_between_places.py`, `sim/tests/test_ledger_commands.py` (`PayEdgeCommand`).

The ledger moves a seat's purse through two objects (`sim/ledger/seat_account.py`). `SeatAccount` is the seat's own purse: a payment
through it moves the seat's account against the account outside the book (two postings, the first labelled `set`) and the other party
separately. `SeatActor` is the seat as a party in the book: `ledger.transfer` makes one posting between the two accounts. The commands
`PayEdge`, `ReceiveFromEdge`, `PayWages` and `TakeFromHouseholdPurse` use the first; `PayActorFromHousehold`, `SettleWithEdge`,
`WithdrawHouseholdMoney`, `PayActor` and every exchange use the second. The split is the one the household's state and its facade always
had (`HouseholdState` had no `purses`, the facade did); it was kept so the book's postings stay identical through the migration.

Two consequences: the book's history for the same payment differs by command (the outside-the-book postings are noise in the audit of
what crossed an edge), and `sim/coin/carriage.py` charges coin carriage to a payer that `stands_at_home` (the first object) and to no
party in the book (the second), so a seat's wages pay carriage and its tax to the state does not.

Evidence: `python3 -m sim.tests --only coin_carriage_between_places,ledger_commands` (the tests that state each side); the postings of the
two paths over a game are in the book's history (`Book.transfer` calls).

Fix: pick one posting for a seat's payment (the single posting between accounts), decide whether the seat stands at the home country's
centre for carriage in every path (or whether carriage belongs to the places the parties stand in), delete `SeatAccount`'s `credit`, `debit`
and `stands_at_home`, and re-record the equivalence baselines, since the book's postings change.
