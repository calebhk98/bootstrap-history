# Add deeper capital markets

**Source:** playtest findings document, LATE-004. **Status:** Major
roadmap-sized feature recommendation. Genuinely new; not currently named in
the architecture documents.

## The player's reasoning

The household credit line is a workable early-game abstraction, but late
industrialisation, once projects cost millions and the national economy
dwarfs the founder's own purse, should involve banks and deposits, bonds,
equity/joint-stock firms, insurance, public borrowing, investment funds,
financial crises, interest-rate changes and capital allocation toward
independent firms.

## Checked against the architecture documents

Searched `docs/architecture/HISTORICAL_SIM_ARCHITECTURE.md`, `ENDOGENOUS_
COSTS_AND_DOMAINS.md` and `PM_ASSESSMENT.md` directly for "bank", "bond",
"capital market", "credit market", "joint-stock" and "insurance": no
matches in any of the three. Unlike `LATE-001` (firms) and `LATE-003`
(state finance), which the external design document already names as
target entities, capital markets beyond the founder's own credit line are
not currently on record anywhere in `docs/architecture/`. This is a genuine
addition to the roadmap, not a duplicate.

## What already exists

`sim/engine/economy_credit.py` (the `CreditMixin`) is the entire live capital
mechanism: a household credit line with an interest rate and an affordability
ceiling. There is no banking sector, no bond market, no equity instrument and
no independent capital pool that a firm other than the founder's own
household could draw on. `LATE-001`'s independent firms (`Complaints/107`)
would need somewhere to raise capital from other than the founder personally
underwriting them, which is exactly what this finding would supply.

## How this sits against CLAUDE.md

§3.1 applies the same way it does to `LATE-003`: an interest rate, a bond
yield or a bank's lending capacity has to fall out of the scarcity of
loanable funds, risk and institutional trust in the simulation rather than
being asserted as a flat percentage. §3.5 is worth stating explicitly:
adding persisted bank/bond/equity state is fine and needs no save-migration
plan, per the standing project rule; a save from before this feature existed
simply does not need to load after it lands.

## Size

Roadmap-sized, and lower priority than `LATE-001` and `LATE-003` in
practical sequencing, since capital markets are mostly useful once there
are independent firms and a state that borrows to lend against. Treat this
as a follow-on to those two rather than a parallel track.

## Cross-references

`Complaints/107` (LATE-001, independent firms) and `Complaints/109`
(LATE-003, state fiscal model) are the natural prerequisites in practice,
even though nothing formally blocks starting this first.
