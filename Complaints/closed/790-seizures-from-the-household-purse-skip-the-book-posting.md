# Seizures from the household purse skip the book posting that a payment to the state makes

**Status:** closed - the seat has one account object in the ledger (`sim/ledger/seat_account.py`), so `TakeFromHouseholdPurse` (confiscation, hidden-wealth seizure) is one posting between the purse and the taker, and `WithdrawHouseholdMoney` (a seat founding a bank) is one posting to `edge:exchange`, the edge the economy's bank capital comes from, entered in the cash book as an outlay under `bank capital`. Tests: `sim/tests/test_ledger_commands.py` (`TakeFromHouseholdPurseCommand`, `WithdrawHouseholdMoneyCommand`).

The household pays the state two ways. `Transfers.pay_state` (sim/polity/transfers.py) pays from the household as an actor: both
sides keep accounts in the one book, so it is one posting (`Purses.transfer`) and the cash book is told through `note_outlay`. The
confiscation and the found-hidden-wealth seizure (`Demands.lose_capital_to`, `settle_household_year` in sim/polity/demands.py, the
ledger's `TakeFromHouseholdPurse`) pay from the household's state (`HouseholdState`), which has no `purses` attribute, so
`sim/agents/ledger.py` `transfer` falls to `debit` and `credit`: the purse is set with `set_net(..., "set")` and the treasury is
credited against `EDGE_OUTSIDE`. The money moved is the same, but the book shows the household's loss as a "set" entry and not a
posting to the treasury, so the book's own audit of who paid whom does not see these seizures.

Found while routing the polity's payments through the ledger (phase 3.1): the two commands `PayActorFromHousehold` and
`TakeFromHouseholdPurse` keep both behaviours exactly. One rule with two drifted copies; the fix is to send the seizures through
`PayActorFromHousehold` and see the book entries and the cash-book causes change (every confiscation and hidden-wealth line in the
reporting and the ledger tests reads them).

A second path with the same shape: `WithdrawHouseholdMoney` (a seat founding a bank, sim/finance/bank.py) sets the household's
money lower without a posting, while the bank's capital enters the economy's book from `EDGE_EXCHANGE`; the actors' book never
sees the coin leave.
