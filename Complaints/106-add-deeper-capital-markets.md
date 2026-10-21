# Add deeper capital markets

**Status:** partly - pooled credit, shares, banks and state bonds are built; secondary trading, bank runs on solvent banks, insurance, funds, a player-founded bank and non-state bond issuers remain (design note: Complaints/reports/agent-economy-capital-markets.md)

**Source:** playtest findings document, LATE-004. **Type:** Major
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
household could draw on. `LATE-001`'s independent firms (`Complaints/closed/103`)
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

`Complaints/closed/103` (LATE-001, independent firms) and `Complaints/closed/105`
(LATE-003, state fiscal model) are the natural prerequisites in practice,
even though nothing formally blocks starting this first.

## Agent economy (current)

The agent economy has pooled credit with household lenders (`sim/economy/credit.py`, `credit_claims.py`, `lending.py`). What exists, what is missing and the heuristics needed are in `Complaints/reports/agent-economy-capital-markets.md`. Complaint 307 no longer applies there (the state offers no funds); the retired engine loan market (`sim/engine/economy_capital_market.py`) is not described here.

Priority: lower than the work that makes the opening settle (473); it is picked up when that allows. Banks must not exist before a society holds a banking institution; that is already built (step 2 below gates on the `deposit_banking` node).

## Built on the agent economy

- **Shares (step 1).** A producer whose plant request the loan market left unmet sells shares for the rest
  (`sim/economy/shares.py`, `share_market.py`, called from `Economy._lend`). Savers still holding funds after the
  year's lending bid; buyers are taken cheapest required rate first and the last needed sets the rate. A share is
  priced at the present value of the dividends the producer is then expected to pay (the dividend it paid last
  plus what the new plant earns), discounted at that rate plus the premium a lender would charge it, because a
  shareholder ranks behind its lenders; a project that does not beat that rate sells nothing. Dividends are split by share
  in `ownership.spread`, and `equity.holdings` gives holders their part of the producer's worth instead of the
  owner tile's pro-rata split. The expansion path is untouched: the money the shares raise is plant like a loan's
  (the one hook is the list of funded amounts in `_lend`). Still open: shares trading between holders after issue,
  a firm choosing equity over debt on cost, and the closed-producer path (`close_idle_producers`) paying its cash
  to the owner alone. Measure: `Economy` fixture tests in `sim/tests/test_economy_shares.py`; on Rome compare the
  rate, `funds_offered` and `lent_by_borrower` of the first years (`share_issuers` is `len(record.shares)`).

- **Banks (step 2).** A bank is an agent id with a purse (`sim/economy/banks.py`, `bank_service.py`); a society
  founds banks only once it holds a node declaring `deposit_banking` (`fin_deposit_bank`;
  `sim/engine/economy_port_institutions.py` hands the economy the names), and its richest household founds one
  when none stands (any agent may call `banks.found`). Households pledge their offered funds to the bank; the
  bank offers its free cash plus the pledges less a reserve, asking its depositors' rates plus a margin, and takes
  a deposit only for the loans it makes (the pool's way: interest is paid on no more than was lent), then returns
  idle cash. A deposit is a term loan in the shared registry (depositor lender, bank borrower), so wealth, claims
  and the one default rule need nothing new. A bank whose assets as its lenders value them fall short of its
  deposits (its capital gone) is run on: every deposit falls due, the bank pays what it holds in proportion, and
  what it cannot pay is arrears the default rule writes off, borne by the depositors. The founder is paid only
  earnings above the capital it paid in. Heuristics: `BANK_MARGIN_SHARE_OF_OPENING_RATE`,
  `BANK_FOUNDING_SHARE_OF_CASH`, `BANK_CAPITAL_SHARE_OF_LOANS` (reserve share reuses `LENDER_RESERVE_SHARE`).
  Still open: depositors choosing among several banks by anything but cover, withdrawals for cash needs, a run
  on a bank that is solvent but illiquid, credit creation beyond the deposits, the player founding a bank by
  command (the economy call is `banks.found`; no engine command yet). On Rome with the node granted the
  founder's own capital covers the loans, so no deposits are taken and the rate is a margin higher
  (measure with the Rome series of `lent_by_borrower` and `base_rate` with and without the node).

- **State bonds (step 3).** A state raises cash by selling bonds (`sim/agents/bonds.py`, `Purses._draw`) instead of
  drawing on the pool at par. Each year `Government.set_bond_terms` sets the coupon (the going rate) and the yield
  the market asks of this state (its borrowing rate, which carries Complaint 623's default-record premium); the
  pool's depositors pay the present value of coupons and face at that yield, so a state with a default on its
  record sells the same coupon for less and owes more face for the same cash. The state's debt is the face, its
  interest the fixed coupon (the floating rate applies only to what is not bonds, `Borrower.settle_interest`),
  bonds fall due after `BOND_TERM_YEARS` and are repaid by selling new ones if the purse is short, and a default
  costs the named depositors what they paid. Still open: bonds changing hands after issue (a holder's wealth
  marked to the price), insurance and investment funds, the term chosen by the issuer, and non-state issuers.
  On Rome no state borrowing occurs in the first years, so the series is unchanged.
