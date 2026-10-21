# The founder's ventures and other actors' concerns are separate implementations of running a business

**Status:** open - the arithmetic is shared, the founder's takings, upkeep and hiring still run their own code (see "Progress"); one design with 510 (`docs/architecture/FIRMS_OWN_PLANTS_PLAN.md`); 510 also carries the opening check for whether plants pay their way (was 528)

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
2. **The founder is not paid from its sale account.** `_acting_seat_orders` offers every running concern's output in the clearing and
   `_settle_seats` stores the proceeds (`stored["seat_takings"]`), but nothing reads them: the ledger credits the engine's estimate in
   `_step_money_seat` (`receive_from_edge(EDGE_CUSTOMERS, revenue)`), one year behind the clearing. Paying the seat as a firm is paid needs
   (a) the credit moved into `_settle_seats`, (b) the book-sold concerns' estimate taken out of the credit in `_step_money_seat` (the
   estimate is summed before the saturating ceiling, so it cannot be split after it), and (c) the proceeds are gross while the estimate is
   net of the inputs the concern buys, so the founder's input purchases must be bid for in the book or subtracted. Display keeps the estimate
   (`ventures`, `why`, `revenue_sources`). Whole-game money tests (capital change equals revenue less costs) will need porting.
3. **The aggregate ceiling stays.** Measured on the default Rome game under the automatic policy (`manual=False`, 23 years from the first
   year with concerns), the ceiling `REVENUE_CEILING_LABOUR_HOURS_PER_POP_SCALE` cut revenue by under a tenth of a percent, so it does not bind
   in an ordinary run; it is the guard for a run that compounds, and non-book concerns (services, institutions, workshop output) are still
   unbounded by any clearing. Retire it when item 2 is done and those pay from a clearing or a stated demand.
4. **The founder hires (plan stage 4).** `venture_staff_free`, `venture_staff_used`, `venture_foreman_free`,
   `venture_staff_who_is_watching_what` are the household's supervision hands; delete them when the founder's business hires its crew through
   `sim.labour.market`. The opening fee (`venture_capex`) stays a share of the project cost until entries carry `capital` for every node.
5. **The wall test.** Items 1 and 4 empty most of `sim/tests/business_wall_allowlist.txt`; stage 5b empties the rest.
