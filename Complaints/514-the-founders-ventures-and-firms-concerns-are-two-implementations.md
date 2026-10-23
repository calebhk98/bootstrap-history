# The founder's ventures and other actors' concerns are separate implementations of running a business

**Status:** open - the arithmetic is shared and book-sold takings are paid by the clearing; the founder's estimated takings, upkeep and hiring still run their own code (see "Progress"); one design with 510 (`docs/architecture/FIRMS_OWN_PLANTS_PLAN.md`); 510 also carries the opening check for whether plants pay their way (was 528)

Found closing 479: firms took their crew from the plant while the founder's ventures still took it from takings,
and nothing stopped the two from diverging, because they are different code. The founder's ventures are `Sim`
mixin methods (`sim/engine/projects_ventures.py`, `projects_venture_quotes.py`: `open_venture`, upkeep, staffing,
closure); firms and player seats run concerns in `sim/agents/` (`business_books.operate`, `firm.operate`,
`player.operate`). Each rule a business follows (crew, upkeep, takings, closure, sale) can exist in two versions, one
of which only the founder sees. Measure: `grep -rn "def open_venture\|def operate" sim --include=*.py`.

Why it matters (CLAUDE.md "general actors"; multiplayer): every mechanism the founder uses must be usable by any
actor, and a fix in one path silently misses the other.

What it would take: one business object (a firm with plants, see 510) in `sim/agents/`, run by the same code for
every owner; the founder's commands act on the founder's firms through it, and `projects_ventures.py` keeps only
the founder's choices (what to open, whom to staff it with). A wall test that fails when the engine computes a
business's crew, upkeep or takings outside that object.

## Economy producers (outside review)

The split is wider than founder against firms: actor businesses run through `sim/agents/business_books.py`
(takings, upkeep, crew, payments) while the agent economy's `Producer` objects run recipes with their own
capacity, inputs, workforce, stock and cash, and founder concern output enters the economy through
`EDGE_LEGACY` (`sim/engine/economy_port_year.py`). Double counting was not established; the risk is a
constraint enforced on one path and bypassed on the other. Target: owners (founder, firm, state) decide
what to build and run, and one production machinery runs every plant.

## Progress (branch one-business-object)

Read again against the code: the crew rule (`business_crew_rule`), the takings product (`business_books.takings_of_size`), the ramp
(`plant_figures.ramp`), mothball and restore and the closing rules (`Business.review`) are one implementation for every owner, and the
founder's `projects_ventures.py`, `projects_venture_quotes.py` and `agents_port.py` are adapters that read the node and call them. What is
still two code paths, with the command that finds each (`python3 -m sim.tests --only business_wall` lists the allowlist that must shrink):

1. **Takings and upkeep at the economy's prices.** `economy_production.concern_takings`/`institution_upkeep`/`concern_revenue` (founder) and
   `economy_port.concern_upkeep`/`concern_takings`, `agents_port.entry_gross`/`concern_takings` (firms) each read the node's `rev` and `up`.
   Target: one function of (entry, prices, wages, size) in `sim/world/plant_figures.py`. After 507 stage 5 (the market factor as a function of
   (entry, prices), not of a node).
2. **The founder is paid from its sale account (done).** `_acting_seat_orders` offers each running concern's output
   (`concern_book_sales.concern_book_offer`, one rule for the clearing, the estimate and the forecast) and
   `economy_port_seats.settle_seats` (called by `_settle_seats`, in the `market` phase after the clearing) credits the seat's ledger
   the clearing's proceeds, gross ("concern sales"), and charges the inputs those concerns bought at the economy's prices
   ("inputs of concerns sold in the book"; the estimate was net of them, and the founder does not yet bid for them in the book).
   Upkeep and wages are charged in the money phase as before. The estimate (`estimated_revenue`, credited in `_step_money_seat`
   as "venture revenue") leaves those concerns out before the ceiling; `revenue()` is still estimate plus the forecast of the
   book concerns, read from last year's sale record with its `sale_basis`, so `ventures`, `why`, `revenue`, `money` and
   `revenue_sources` are unchanged in kind. A concern that offers nothing the economy trades is still paid by the estimate.
   Measure: `python3 -m sim.tests.income_probe` (opens concerns whose goods the economy trades on a Rome game and prints, per year,
   the credits by purpose beside the forecast); run it on `origin/main` and on the branch. The comparison and its meaning are in
   the branch report: the clearing paid several times what the estimate quoted for the one concern that survives staffing,
   which is the 510 opening question (do plants pay their way) showing up in the founder's books.
   Rules: `sim/tests/test_seat_paid_from_sales.py`; whole game: `sim/tests/test_seat_paid_from_sales_scenario.py`.
   Not done: the settlement runs once the year's market has cleared, so the purse the money phase tests (credit line, insolvency,
   `shed_loss_makers`) does not yet hold the year's sales; the forecast stands in for them there.
3. **The aggregate ceiling stays, for non-book concerns only.** Measured on the default Rome game (every concern the tree lets the
   founder open and the economy does not trade, all at full ramp, at the opening's output and price level), their quoted takings
   were a few percent of the ceiling `REVENUE_CEILING_LABOUR_HOURS_PER_POP_SCALE` sets (a one-off script summing `venture_real_earnings(fully_ramped=True)` over those nodes; no command keeps it), so it cuts at most that few percent in the worst case
   and nothing in an ordinary run (an earlier automatic-policy run measured under a tenth of a percent). Nothing needs it for
   compounding any more: the concerns that could compound sell in the clearing, which bounds them. It is kept only because the money
   screen's market deduction (`_what_the_market_will_not_absorb`, `where_the_market_squeeze_falls`, Complaint 216) is read from it;
   its `retire` now names this complaint. Retire both when services, institutions and workshop output are paid from a clearing or a
   stated demand.
4. **The founder hires (plan stage 4).** `venture_staff_free`, `venture_staff_used`, `venture_foreman_free`,
   `venture_staff_who_is_watching_what` are the household's supervision hands; delete them when the founder's business hires its crew through
   `sim.labour.market`. The opening fee (`venture_capex`) stays a share of the project cost until entries carry `capital` for every node.
5. **The wall test.** Items 1 and 4 empty most of `sim/tests/business_wall_allowlist.txt`; stage 5b empties the rest.
