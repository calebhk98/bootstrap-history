# Capital markets build research (Complaint 106)

Research for the remaining half of Complaint 106: banks, deposits, bonds, equity, insurance and crises on the
agent economy (`sim/economy/`). It reads the code as it stands, summarises how each institution first worked,
how agent-based models represent it, and proposes a staged build with relationship tests. No code or data is
changed. It extends `Complaints/reports/agent-economy-capital-markets.md` (the first-step note) and does not
repeat it; read that first.

Source tags: **read** = page or abstract opened or returned by search in this session; **snippet** = only a
search-result excerpt seen; **recalled** = from memory, unchecked, treat as a lead to verify. Any figure in this
document is a cited date or is marked as such; no other numbers are asserted.

## 1. What exists

Engine side (old, not run by the agent economy): `sim/world/capital_market.py` (pure rate-from-balance
functions) and `sim/engine/economy_capital_market.py` (yearly meeting). Complaint 106 describes this as built
and notes the game no longer runs it. Its reusable idea is only the shape: rate follows scarcity of funds.

Agent economy (what a build extends):

| Piece | File | What it does |
|---|---|---|
| Offers, requests, loans | `sim/economy/types.py` (`FundsOffer`, `LoanRequest`, `Loan`) | A loan has one lender, one borrower, principal, rate, years left, collateral value, arrears, issue year. No kind, no maturity-on-demand, no transferability marker. |
| Clearing | `sim/economy/credit.py` `clear` | One base rate per currency from lenders' ask and borrowers' ceiling, moved only part way each year (`RATE_ADJUSTMENT_SHARE_PER_YEAR`); each borrower pays base plus `risk_premium` (leverage, arrears history); rationing falls out of ceilings. |
| Servicing and default | `credit.py` `service` | Pays loans in loan id order until borrower cash runs out; arrears accumulate; a write-off past `DEFAULT_ARREARS_SHARE` removes the loan with no money moved. Amortises by `principal / years_left`. |
| Claims as wealth | `sim/economy/credit_claims.py` | `claim_value` (principal plus arrears less doubt), `claims_by_lender`, `debts_by_borrower`, `wealth`, remembered defaults, `losses_by_lender`. |
| Year wiring | `sim/economy/lending.py` | `service` after sales (first payment a year after issue), books lender losses to `record.credit_losses`, builds household and merchant requests. |
| Borrowers | `households_credit.py`, `merchants_credit.py`, producers (`producers_close`), state (`state_finance.py`) | Each sizes a request from its own income or route returns, bounded by a service share or a leverage share. |
| Lenders | `households_orders.py` | The only source of `FundsOffer`: cash beyond bids and target, minimum rate from time preference plus expected inflation. |
| Money | `sim/economy/accounts.py` `Book.transfer`, `transfer_many`, `post` | Two-sided, atomic, refuses overdraft for non-edge payers; `edge:` agents are the counterparty for flows with no real other side. |
| Equity (old actor layer) | `sim/agents/joint_stock.py` | `holdings` (issuer to share of equity), `issued`, `hand_over`, `shares_worth` (last margin times valuation horizon), `pay_dividends` through `ledger.transfer`. Lives in `sim/agents/`, not wired to `sim/economy/`. |
| Exclusive rights (old actor layer) | `sim/agents/patent.py` | A tradable right as plain data on a record, granted only where the state knows the institution (`world.state_grants_patents`). A model for gating by what a state knows. |
| Policy | `sim/agents/policy.py` (`Option`, `Decision`, `ValuePolicy`, `CallbackPolicy`) | An actor lists options with worth, cost, chance; any policy (value, human, mod) chooses. |
| Ledger | `sim/agents/ledger.py` `transfer` | One two-sided posting with a purpose label. |
| Ownership income | `sim/economy/ownership.py` | Dividends and rents to a tile's owner cohort are spread over the tile's cohorts: income from owning, but no tradable share. |
| Tree | `data/branches/40_finance_institutions.json` | Finance nodes already authored: `fin_argentarii`, `fin_societas`, `fin_maritime_loan`, `fin_double_entry`, `fin_bill_exchange`, `fin_endorsement`, `fin_promissory_note`, `fin_deposit_bank`, `fin_fractional_reserve`, `fin_clearing_house`, `fin_joint_stock`, `fin_limited_liability`, `fin_share`, `fin_stock_exchange`, `fin_bond`, `fin_public_debt`, `fin_central_bank`, `fin_paper_money`, `fin_marine_insurance`, `fin_fire_insurance`, `fin_life_insurance`, `fin_mortality_table`, `fin_reinsurance`, `fin_savings_bank`, `fin_usury_law`, `fin_bankruptcy`, `fin_pawnshop`, `fin_mortgage`. Prerequisites are authored (for example `fin_deposit_bank` needs `fin_argentarii` and `fin_double_entry`; `fin_marine_insurance` needs `fin_maritime_loan`, `fin_argentarii`, `fin_contract_law`; `fin_bond` needs `fin_promissory_note`). Some carry `mechanics` for the old engine (`fin_argentarii`: a debt rate discount; `fin_marine_insurance`: a hazard counter). |
| Civilisation start | `data/civilizations/*.json` `institutions` | Free text per vehicle (`bank`, `corporation`, `charter`, `partnership`, `patent`, `testament`). Rome: argentarii, no corporation. England: merchant banks, perpetual corporations. These are initial conditions, which CLAUDE.md 4.1 allows. |

Findings that shape the build:

- `credit.service` pays in loan id order. That is an unlabelled priority rule. Eisenberg and Noe's clearing
  rule (proportional payment, debt before equity, limited liability) is the standard that removes it, and a
  bank with many depositors needs it (see the sources section).
- The service step treats every loan as amortising. A deposit repayable on demand does not fit; it needs its
  own servicing rule, not an `if kind` branch inside `service` for content ids (CLAUDE.md 4.7 forbids ids, a
  claim kind is fine).
- Credit and service are annual. A run is faster than a year. The build must either order withdrawals
  within the year or allow a sub-step; see open questions.
- `sim/economy/` has no read of known tech nodes (no `knows` call found in the package). Gating the
  institutions is new wiring, not an existing hook.

## 2. How each institution first worked, and how agent models represent it

Dates are those the sources give; they are not simulation inputs (4.2).

**Roman argentarii and societates publicanorum.** Argentarii took deposits, made loans, assayed and changed
coin; jurists defined a bank by receiving deposits and advancing credit. Some deposits were safekeeping and
bore no interest, others bore interest and could be lent on, which is a deposit as a use-of-funds contract.
Banking was regulated and accounts were kept (read: Andreau via the Liberty Street summary and a legal-basis
paper below). The societates publicanorum were large partnerships that leased state revenue and works; their
shares (partes, small ones particulae) resemble stock, but scholars dispute that partes were actively traded
(snippet: Wikipedia, Berkeley paper, Bocconi note). Lesson for the sim: the engine must allow a share claim
without assuming a secondary market; the market comes from a separate gate.

**Han lending.** Lending against collateral was widespread; Sima Qian's economic chapters describe merchants
and lenders (snippet). Buddhist monastic endowments lent and ran pawnshops from a later period (snippet).
Lesson: the lender need not be a bank; a long-lived institution with an endowment lends from its capital, which
is the same shape as a bank with no deposits. Han detail is the weakest part of this research; verify before use.

**Bottomry and marine insurance.** Bottomry (Greek and Roman nauticum foenus) is a loan on ship or cargo
repaid only if the voyage succeeds, at a high rate that prices the hazard; fraud (sinking ships to avoid
repayment) is documented in Demosthenes' speeches (read: Wikipedia, Smith's dictionary entry). Marine
insurance as a separate contract appears in Genoa; a cargo policy is attested for 1343 and the oldest surviving
policy for 1347 (snippet). In London, underwriting gathered around Lloyd's coffee house from 1688 (snippet).
Lesson: insurance grows out of a contingent loan; the moral hazard is part of the original institution, so
the sim should include it.

**Medieval bills of exchange and deposit banks.** The bill let a merchant pay in one place and settle in
another through a correspondent, disguising credit as exchange; the Medici bank ran branches in several cities
as separate partnerships (read: de Roover via search results; recalled for detail). Cashless payment between
accounts grew from the Genoese fairs (snippet). Lesson: the claim a bill creates (a payable by a named party at
a place) is the first claim that changes hands, and acceptance and endorsement create chains of liability.

**Italian merchant banks.** Partnership banks funded by partners' capital and by deposits, lending to princes
and merchants; the large failures came from concentrated lending to sovereigns and branch overextension
(recalled: de Roover). Lesson: concentration limit and sovereign default are the failure channels, and both
exist as heuristic slots already named in the first-step note.

**Amsterdam Wisselbank.** Opened 1609 as a municipal exchange bank to settle bills in good money; it
held coin against deposits and later (from 1683) restricted withdrawal of coin and so operated as fiat
money (read: Quinn and Roberds, as found by search). Lesson: the warehouse bank, a full-reserve deposit,
is a real historical first stage, and the move to partial backing is a decision with a visible trigger.

**Bank of England and state bonds.** The 1672 Stop of the Exchequer was a repudiation that ruined goldsmith
bankers who had lent to the Crown; after 1688 parliamentary control made royal borrowing credible and the Bank
of England followed in 1694 as a loan contract with the government (snippet: Wikipedia, Tax Research UK,
North and Weingast). Lesson: a sovereign borrower's default is a decision with a reputational cost, and the
cost is what makes lending to it possible. In the sim, the state's default must be a choice weighed against
the loss of its credit standing, not a script.

**Joint-stock companies.** The VOC (1602) combined permanent capital with transferable shares and a secondary
market from the outset (snippet). Limited liability and perpetual existence are separate legal gates; Rome's
partnerships dissolve on a partner's death while England's corporations do not (civilisation file text).
Lesson: three separable properties: share claim, transferability, limited liability.

### Agent-based representations

- **Delli Gatti and colleagues, credit network** (snippet): firms and banks linked by productive and credit
  relations; net worth constrains output and borrowing; a shock with high leverage causes bankruptcy avalanches
  through the credit network (financial accelerator). Use: net-worth-driven credit supply, and a default that
  becomes a creditor's loss and then the creditor's own default.
- **Gai and Kapadia, contagion** (snippet): interbank exposures on arbitrary network, failure when losses
  exceed capital buffers, robust-yet-fragile: contagion is rare but wide when it occurs, and depends on asset
  market liquidity. Use: banks lend to banks; capital buffer is a state variable; fire-sale price is a channel.
- **Eisenberg and Noe, clearing** (snippet): given obligations, a unique clearing payment vector exists under
  limited liability, debt priority over equity and proportional payment. Use: replace id-order servicing
  with proportional clearing inside a year.
- **Diamond and Dybvig, runs** (snippet): demand deposits give liquidity but have a run equilibrium: if you
  expect others to withdraw, withdrawing first is individually best, and runs cause real damage; deposit
  insurance removes the incentive. Use: depositors' withdrawal is a decision with expectations over others,
  with sequential service.
- **Bank of England agent-based models** (snippet): corporate bond and housing markets, macroprudential
  policy experiments (Hinterschweiger and others, Staff Working Paper on housing); the Bank's RAMSI is a
  stress-test framework with banks as balance sheets (snippet, weak on detail). Use: policy levers (capital and
  loan limits) are parameters an actor or player sets, the same stance as the first-step note's bank policy fields.

## 3. Per-institution table

"Claim" reads: holder has a claim on issuer. "Gate" is a tech-tree node (or institution flag) the engine reads
as a capability; the engine never names the id (CLAUDE.md 4.7), the node's `mechanics` declare a capability
such as `accepts_deposits`, and the actor must also have it known.

| Institution | Claims it adds (holder on issuer) | Decisions (actor: option, as `Option` with worth, cost, chance) | Gate | Failure mode |
|---|---|---|---|---|
| Money changer and warehouse deposit (argentarii, Wisselbank) | Depositor on bank: demand claim, backed by bank's purse in full | Depositor: place cash with a bank or hold it, worth is safety and payment convenience, cost is foregone return. Bank: accept the deposit and keep it whole or lend. | `fin_argentarii`, then `fin_deposit_bank` | Embezzlement or lending out against promise (agency problem); with full backing no run, the loss is theft or debasement. |
| Fractional-reserve bank | Depositor on bank (demand); bank on borrowers (term loans) | Bank: reserve share, margin, lending to one borrower; depositor: stay or withdraw given expected solvency | `fin_fractional_reserve` | Maturity mismatch: borrower defaults reduce bank assets, withdrawals exceed purse, bank fails; run (Diamond and Dybvig). |
| Interbank and clearing | Bank on bank (overnight or term) | Bank: lend surplus purse to another bank at a rate reflecting its own estimate of that bank | `fin_clearing_house` | Cascade through exposures (Gai and Kapadia); freeze when banks stop lending to each other. |
| Bill of exchange, promissory note, endorsement | Payee on drawee, transferable | Holder: keep to maturity or sell (discount) now; drawee: accept or refuse; bank: discount at a rate | `fin_bill_exchange`, `fin_endorsement`, `fin_discounting` | Chain of endorsers each liable; a default propagates back along the chain; discounting banks hold the loss. |
| Bond and state debt | Holder on issuer (state, firm), tradable | State: borrow or tax or cut; holder: buy, hold, sell at a price; state: honour or default weighing lost credit | `fin_bond`, `fin_public_debt` | Sovereign default (Stop of the Exchequer) transmits to banks holding it; price falls before default and raises the state's rate. |
| Equity, joint stock | Shareholder on firm: residual claim and dividends | Owner: issue shares or borrow; investor: buy at a price vs expected dividends; firm: pay dividends | `fin_societas` (shares of a partnership), `fin_joint_stock`, `fin_share`, `fin_limited_liability`, `fin_stock_exchange` (market) | Overvaluation and price collapse; with limited liability a firm failing loses only equity, creditors take the loss; a falling share price lowers wealth and demand. |
| Marine, fire, life insurance | Policyholder on insurer: contingent payout; insurer on policyholder: premium | Insurer: price from loss frequency it has seen, accept or decline; insured: buy cover or bear risk; fraud choice | `fin_maritime_loan` (contingent loan), `fin_marine_insurance`, `fin_mortality_table`, `fin_fire_insurance`, `fin_life_insurance`, `fin_reinsurance` | Correlated losses exhaust the pool (a storm season, a city fire); underpricing from short memory; moral hazard. |
| Central bank, lender of last resort, deposit insurance | Banks on central bank; depositors guaranteed by an insurer or state | Authority: lend against collateral in a run; price the loan; levy | `fin_central_bank`, `fin_paper_money` | Moral hazard; the authority's own solvency; note issue beyond backing (inflation, which `currency.py` would meet). |
| Savings bank, pawnshop, mortgage | Small depositor on bank; bank on collateral | As above with collateral and small balances | `fin_savings_bank`, `fin_pawnshop`, `fin_mortgage` | Collateral value falls with the asset market. |
| Rules around them | None directly (they change the rules) | State: set usury cap, bankruptcy procedure | `fin_usury_law`, `fin_bankruptcy`, `fin_contract_law` | A cap below the clearing rate rationed credit away (existing rationing code can show it); weak enforcement raises the premium. |

## 4. What each build reuses

| Need | Existing machinery | Change |
|---|---|---|
| Deposit as a claim | `Loan` with the depositor as lender and the bank as borrower, `credit_claims.claims_by_lender` already counts it in wealth, `debts_by_borrower` counts it against the bank | Add a claim kind (term, demand) so `service` does not amortise a demand claim and a withdrawal is a transfer of principal. A bank's purse is an ordinary `Book` purse. |
| Move of money | `Book.transfer_many`, `ledger.transfer` for the old layer | None. A withdrawal, premium, coupon and dividend are transfers with a purpose label. |
| Bank as lender | `FundsOffer`, `credit.clear` | Bank emits an offer from its lendable purse; minimum rate from its deposit rate plus margin. |
| Bank as borrower | `LoanRequest` | Not needed for deposits (they are placed, not asked for); needed for interbank. |
| Bank decisions | `Option`, `Decision`, `ValuePolicy`, `CallbackPolicy` | Reserve share, margin, concentration limit are an actor's policy; a human or mod can run a bank by `CallbackPolicy`. |
| Depositor choice and withdrawal | `Option` with worth, cost, chance; `claim_value` as the depositor's expectation | New: `chance` is the probability the bank pays in full, from observed bank state and remembered failures (`credit_claims.remember_defaults` generalised to banks). |
| Trust | `remembered_defaults` and `credit_losses` | Generalise from borrower to any debtor; a depositor reads a bank's record and the fade rate is already a declared heuristic. |
| Tradable claim | `Loan.lender` field | A sale is a change of lender plus a transfer of the price; the price is `claim_value` discounted at the market rate, so no price table (4.5). |
| Share | `sim/agents/joint_stock.py` `holdings`, `issued`, `hand_over` | Port the idea to the economy: a share claim has holder, issuer, fraction; dividends use the existing `ownership.SPREAD_PURPOSES` path. Value is expected dividends over the issuer's own cash flow, not `last_margin` times a flat horizon. |
| Producer failure | `producer_exit` already pays lenders first then the owner | Equity holders rank after lenders by this rule: limited liability is the existing behaviour; an unlimited-liability partnership needs the owner to cover the gap, gated by `fin_limited_liability`. |
| Insurance | Hazard events already in the economy (harvest, freight loss); `Transfer` with a purpose | Insurer is an agent with a purse and a book of policies; payout is a transfer on a loss event the world already generates. |
| Gating | `patent.py` pattern (state knows the institution) | A capability set per actor from known nodes plus the civilisation `institutions` start; the engine reads capabilities, not ids. |
| Conservation checks | `money_audit.py`, `accounts.py` supply bookkeeping | Deposits stay claims, so supply conservation is unchanged until credit creation is chosen (a separate stage). |

## 5. Staged build plan

Order is chosen so each stage is testable alone and no stage invents a crisis. Crises are not a stage; they are
what stages 2, 3 and 4 produce when the numbers allow it.

**Stage 0: groundwork (small, before any institution).**
- A claim kind on `Loan` (term or demand); `credit.service` skips demand claims; withdrawal is its own function.
- Proportional clearing in `service` (Eisenberg and Noe): when a borrower cannot pay all, pay every due claim
  in proportion, replacing id order. Declare any residual priority as a `temporary_heuristic`.
- Debtor-generic remembered losses (the field names say borrower already; check callers).
- A capability gate: a node's `mechanics` can declare capabilities; an actor holds the union of capabilities of
  nodes it knows plus the civilisation's `institutions` start. Reads in `sim/economy/` go through one function.
- Tests: proportional payment conserves money and pays no creditor more than another per unit owed;
  a demand claim is not amortised; an actor without the capability cannot take deposits.

**Stage 1: warehouse deposit bank (first to build).**
- `sim/economy/banks.py`: a bank is an agent id with a purse; cohorts place cash as demand claims; the bank
  keeps every deposit in its purse (full reserve) and earns a fee. No lending.
- Tests: a deposit conserves the book to the unit; a depositor can withdraw all at any time; with
  no loans a bank cannot fail except by its operator's choice (embezzlement option); depositors' choice of
  bank rises with the bank's record (relationship below).

**Stage 2: fractional reserve and runs.**
- The bank lends part of its purse through `FundsOffer`; reserve share and margin are its policy; depositors
  decide each year (and each within-year step, see open questions) whether to stay.
- Tests: deposits rise with trust and fall after a default; a run follows when withdrawals exceed the purse
  (the bank defaults on demand claims through the stage 0 rule, depositors' `claim_value` falls); a bank that
  keeps everything in reserve survives the same borrower defaults that break a thin-reserve bank; no engine
  code names a bank id.

**Stage 3: transferable claims (bills, discounting, interbank).**
- A claim can change lender at a price. Discount houses and banks buy bills; banks lend to banks.
- Tests: selling a claim conserves money and wealth for the pair (price versus claim value); price falls when
  the market rate rises; a default of a drawee reaches the discounter and, through it, its depositors.

**Stage 4: bonds and public debt.**
- The state's loans become tradable claims with coupons; the state's default is a policy decision weighing the
  loss of credit standing (the rate premium after default and the borrower memory already in `credit_claims`).
- Tests: a state that defaults pays a higher rate afterwards and for a fading period; banks holding its bonds
  take a loss and may fail; a state with spare reserve and no deficit does not borrow.

**Stage 5: equity.**
- Share claims on producers and merchants; issue as an alternative to a loan request; price from expected
  dividends; limited liability gate decides whether owners cover a gap.
- Tests: dividends equal what the firm paid and conserve; a failing firm pays lenders before shareholders;
  without the limited liability capability an owner's other assets are exposed; share price falls with
  the firm's margin.

**Stage 6: insurance.**
- Bottomry as a contingent loan (repayment waived on a loss event), then marine insurance with an insurer
  agent pricing from its own claims record.
- Tests: premium rises after a bad season and falls after good ones; an insured merchant runs a route an
  uninsured one declines at the same expected return; correlated losses exhaust a small insurer, who then
  defaults on policies.

**Stage 7: stabilisers.**
- Central bank or lender of last resort and deposit insurance as agents any state may found.
- Tests: with the stabiliser a run that failed a bank in stage 2 does not; its presence raises the chosen
  risk (reserve share falls), the moral hazard relationship.

**Crisis diagnostics (alongside stage 2 onward).** No crisis flag. A diagnostic reports the share of deposit
claims in default, banks failed in a year, and the share of lenders' loss that came through another
lender's failure. Measure by a `simulator.py` subcommand or a test, not a script (CLAUDE.md section 5).

## 6. How a crisis emerges without a script

1. A shock hits borrowers (harvest failure, freight loss, price fall). Their cash falls short; arrears rise.
2. The bank's assets are valued by `claim_value`; arrears reduce its expected collections and its capital.
3. Depositors see the bank's record (remembered losses, observed delays) and update the chance their claim is
   paid in full. A depositor whose option value of withdrawing exceeds staying withdraws. Others'
   withdrawals lower the bank's purse, which raises the chance of failure: the Diamond and Dybvig feedback
   emerges from each depositor's expectation of others, with no flag.
4. When withdrawals exceed the purse, the bank cannot pay; the proportional rule shares the shortfall;
   depositors' wealth falls, they spend less, firms' sales fall and more borrowers default.
5. Banks lending to banks (stage 3) pass the loss on (Gai and Kapadia). Asset sales at a falling price
   (stage 3 onward) spread it further.
6. A bank that fails leaves a record; depositors move to others or hold cash; credit contracts through the
   existing rationing in `credit.clear`; the base rate and premiums rise as lenders' funds fall.

What is not scripted: no year, no named event, no bank id. Test by ensemble: across seeds crisis frequency is
neither zero nor constant (CLAUDE.md 4.2), and removing the reserve policy or trust memory changes it in the
expected direction.

## 7. Heuristics to declare (`temporary_heuristic`)

Reserve share and how a bank sets it; margin between lending and deposit rates; depositors' choice among banks
and the speed at which trust forms and fades; how depositors form the chance a bank pays; concentration limit
per borrower; discount applied to a claim sold in a hurry; insurer's memory length for loss frequency;
the share of an owner's wealth exposed without limited liability; fee of a warehouse bank. Each stands in for
information, search or law the sim does not model; name that in the `why` as the existing declarations do.

## 8. Dependencies on in-flight work

- **Complaint 382 (every posting names a counterparty).** Engine postings that name no counterparty are booked
  against `edge:legacy`. A bank's flows with the founder, the state and foreign actors must have a real payee.
  Stage 1 can start inside `sim/economy/` where counterparties already exist; engine-side founder deposits and
  state borrowing wait on 382's step on counterparties, and until then ride `edge:legacy`. Measure the volume
  of that edge before relying on it.
- **Complaint 103 (independent firms) and 105 (state fiscal model).** 106 says capital markets follow these in
  practice. Stage 4 needs a state that borrows to a ceiling and sets a budget (`state_finance.py` has the request);
  stage 5 needs firms as agents (producers exist in `sim/economy/producers.py`).
- **Complaint 307** no longer applies: the state offers no funds (the first-step note says so).
- **`sim/agents/` and `sim/economy/` are separate worlds.** `joint_stock.py` and `patent.py` are written
  against the old actor record. Port the idea, not the module; check `docs/architecture/PACKAGE_WALLS.md` for how
  to reach across walls (reached only through `api.py`).
- **`currency.py` and the money supply.** Stages 0 to 6 leave deposits as claims and do not change supply.
  Credit creation (a loan booking a deposit) and note issue are a decision for `currency.py`, outside this plan.
- **Several moneys** (`agent-economy-several-moneys.md`): a bank holds deposits per currency; keep `currency` on
  every claim as `Loan` already does.

## 9. Open questions

1. **Time step.** A run is faster than a year. Options: a within-year withdrawal queue ordered by a declared
   rule (random arrival from a seeded stream, ranked), or a finer clock for banks only. Which is cheaper to test?
2. **Withdrawal order and fairness.** Sequential service (first come first paid) is the Diamond and Dybvig
   result that drives runs; proportional service (Eisenberg and Noe) removes the first-mover advantage and
   hence the run. Which one a bank uses is a legal rule; make it a policy field and test both.
3. **Gating source.** Is the capability read from the tech tree per actor (who knows `fin_deposit_bank`) or
   from the civilisation file `institutions` text (free text today)? The text needs a structured form
   (data decision for the owner); the node route needs the economy to read known nodes.
4. **Where equity lives.** Ports of `joint_stock` into the economy: a new claim list next to `record.loans`, or
   a generalised claim type covering loans, deposits, bonds and shares? A single claim table is "dynamic over
   enumerated" but a bigger change to `credit_claims` and the save.
5. **Trust and information.** What can a depositor see: bank balance, remembered failures, neighbours' behaviour?
   Information choices drive the run equilibrium.
6. **Han and non-bank lenders.** Should institutions with endowments (temples, guilds, states) lend by the
   same stage 1 and 2 code? It seems free if lending is an actor capability, but the research on this is thin.
7. **Moral hazard in insurance and bottomry.** Model sinking-for-profit as an option in the borrower's
   decision, or leave out until risk is endogenous in `freight`? Needs the owner's call.
8. **Credit creation.** Whether banks create deposits when they lend (fractional-reserve multiplier) changes the
   money supply; stage 2 deliberately does not. When to take that step?
9. **Calibration.** Reserve ratios, spreads and failure frequencies are not given here by design. Validation is
   against relationships (stage tests above) and ensemble distributions, not historical dates.

## 10. Sources

- Andreau, Banking and Business in the Roman World, via Liberty Street Economics summary:
  https://libertystreeteconomics.newyorkfed.org/2012/11/historical-echoes-how-do-you-say-wall-street-in-latin
  (read, search excerpt); Cambridge excerpt: https://assets.cambridge.org/97805213/89327/excerpt/9780521389327_excerpt.pdf (snippet).
- Contracts of loan and deposit in ancient Rome: https://unz.univer.km.ua/index.php/unz/en/article/view/109_5-18 (snippet).
- Publicani and partes: https://en.wikipedia.org/wiki/Publicani (snippet); https://eml.berkeley.edu/~ulrike/Papers/Publicani_Article_v5.pdf (snippet);
  https://www.unibocconi.it/en/news/ancient-rome-stock-exchange-myth (snippet; source for the doubt about share trading).
- Han lending and monastic endowments: https://en.wikipedia.org/wiki/History_of_pawnbroking (snippet); Sima Qian chapters in
  https://www.worldhistory.org/Sima_Qian/ (snippet). Weak; interest-rate detail not found.
- Bottomry: https://en.wikipedia.org/wiki/Bottomry (read excerpt); https://penelope.uchicago.edu/Thayer/E/Roman/Texts/secondary/SMIGRA*/Fenus.html (snippet).
- Marine insurance origins and Lloyd's: https://www.gresham.ac.uk/node/12775 (snippet); https://insurance.museum/insurance-history-snippet (snippet).
- De Roover, The Medici Bank: https://www.Gwern.net/doc/history/medici/1963-deroover-theriseanddeclineofthemedicibank.pdf (snippet);
  Journal of Economic History note https://www.cambridge.org/core/journals/journal-of-economic-history/article/medici-bank-financial-and-commercial-operations/E8865702110452B1C5B0341407C0DBAC (snippet).
- Genoese fairs and cashless payment: https://www.bundesbank.de/resource/blob/616616/9ed646d315f7c6e0e1782d0921a838b4/mL/the-origins-of-cashless-payments-data.pdf (snippet).
- Quinn and Roberds on the Bank of Amsterdam: https://www.frbatlanta.org:443/-/media/documents/research/publications/wp/2006/wp0613.pdf and
  https://fraser.stlouisfed.org/files/docs/historical/frbatl/wp/frbatl_wp_2010-17.pdf (snippet each).
- Stop of the Exchequer and the Bank of England: https://en.wikipedia.org/wiki/Stop_of_the_Exchequer (snippet);
  https://www.cambridge.org/core/product/5E8F87F595E76EA2CBE3838C3A0080D1 (snippet); North and Weingast 1989 (recalled).
- VOC: https://en.wikipedia.org/wiki/Euronext_Amsterdam (snippet); https://scholarlypublications.universiteitleiden.nl/access/item%3A2907003/view (snippet).
- Gai and Kapadia, Contagion in financial networks (2010):
  https://www.bankofengland.co.uk/working-paper/2010/contagion-in-financial-networks (snippet).
- Delli Gatti and colleagues, Business fluctuations in a credit-network economy (2006), The financial accelerator in an evolving
  credit network (2010): https://business.columbia.edu/sites/default/files-efs/imce-uploads/Joseph_Stiglitz/2006_Business_Fluctuations.pdf (snippet);
  https://pmc.ncbi.nlm.nih.gov/articles/PMC3534113/ (snippet).
- Bank of England agent-based models: https://www.bankofengland.co.uk/-/media/boe/files/quarterly-bulletin/2016/agent-based-models-understanding-the-economy-from-the-bottom-up.pdf (snippet);
  https://www.sfipress.org/eecs-iv-17 (snippet).
- Diamond and Dybvig (1983): https://minneapolisfed.org/research/quarterly-review/bank-runs-deposit-insurance-and-liquidity (snippet).
- Eisenberg and Noe (2001), Systemic risk in financial systems, Management Science: https://www.citedrive.com/en/discovery/systemic-risk-in-financial-systems/ (snippet).
