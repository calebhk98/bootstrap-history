# A mid-game year costs many times an early year

**Status:** closed - a legitimate agent game on this branch steps its second century at the same seconds a year as its first

Found after closing 575, on the legitimate agent playtest's save (`Complaints/reports/playtest-rome-seed11-agent-legitimate-log.md`,
Rome, seed 11, 143 AD, about thirty concerns running): a year from that save takes minutes, where the same game's
years near 100 AD took seconds. 575's profile puts most of the rest in price calculation.

Why it matters: the release criterion is a whole game played by an agent; a year whose cost grows with the game's
activity makes the second and later centuries unplayable however fast the opening is. Complaint 497 tracks the
opening's per-year cost; this is the growth on top of it.

What it would take: profile a year from a mid-game save, find which costs grow with the number of concerns, firms,
plants, contracts or recorded history rather than with the year's own activity (caches keyed on state that changes
every year, solves repeated per concern, histories kept and scanned), and make them linear in the year's activity;
a test on call counts that a year's work does not grow with the number of past years.

## Progress (still open)

Profiled by loading the 143 AD save in-process (the economy's opening skipped, the save restores it) and stepping
one year, with a per-phase timer and cProfile. What grew with the number of firms, not with the year's activity:

- The theft charge read the loans total (`lent_share`, a scan of every facility contract) once per actor: now once per
  pass (`charge_actors_for_theft`). This was the largest single cost.
- A concern's price table (`_concern_prices_in_hours`) and the techniques it may reach (`entries_in_reach`, with each
  node's requirements) were rebuilt for every concern, because their memo was dropped whenever any firm changed size.
  They now key on what they read: the techniques held and the civilisation; the catalogue and the arguments.
- The producers list and the input haul days were rebuilt per concern for the same reason (and the list twice per
  call); they now key on the economy's producer stamp only (`_producers_memo`).
- `techniques_in_use` walked every firm after every size change; it now watches only changes to the set of concerns
  (`concern_set_version`). `techniques_spread` is kept for the same techniques in the same year.
- `Purses._repay` and `Contracts.tidy_facility` did several passes over a facility of many lenders for every interest
  receipt; same arithmetic in fewer passes.

Measure: `python3 -m sim.tests --only year_cost_shared_across_concerns` (call counts), and a year from the save with
the per-phase timer. The cost left is the interest cascade (each borrower pays every lender, each lender that is
itself a borrower scans its own facility: lenders per borrower squared per firm, a consequence of
`LENDER_MATERIALITY`, Complaint 580), the labour quotes that rebuild a shared answer whenever a firm changes size
(`view_share._view_world_stamp` includes the registry version), `tiles_held` rescanning the owner map per call, and the
patent and entry scans over all actors per firm.

## Progress, round two (still open)

Exact cuts (a year from the mid-game save and a fresh game's first years hash the same before and after; the save
hash of a year is the check, since the cut is only exact if the state after the year is byte-identical):

- `tiles_held` with the owner map read the whole map for every labour quote: the home country's tiles and each
  actor's tiles are now indexed once and rebuilt only when `transfer_tile` or a replaced owner map changes them
  (`tile_ownership.py`).
- `techniques_in_use` walked every firm's concerns after any new concern: it now reads the registry's holder index
  (`ActorRegistry.concerns_of_active_firms`).
- The labour hiring cap was worked out for every quote because the quotes run outside a view and
  `view_share._view_world_stamp` was never reached; it is now a `standalone` shared answer under its own stamp
  (`_standalone_stamp`: the year, the techniques in force, the people), which skips the price and trade parts of the
  view stamp. A view's answers no longer drop when a firm changes size (the registry version and actor count left the
  view stamp); both were checked by recomputing every cached answer in a year and comparing.
- Patent entry scanned and sorted every actor per question: `patent_index.py` keeps node -> holders, rebuilt only
  when a patent changes hands (`PatentBook` counts the changes).
- `of_kind` rescanned every actor; a new actor now joins its kind's list in id order.
- `note_sale` scanned every noted sale per sale; it now looks the seller and material up. `forget_orders` keeps a
  list nothing left, so the index survives.
- `concern_input_availability` rebuilt a table of every production entry per call; the market-area tile sets were
  rebuilt per price query (now kept on the area map).

What is left: the interest cascade (each borrower pays about every lender; each lender that is in debt repays its own
lenders from the receipt) is now the largest single cost and is `LENDER_MATERIALITY` (Complaint 580), which pooling
through an intermediary would retire; the sweep of a lender's facility on each receipt is exact arithmetic that
cannot be regrouped without changing the postings. After it: the entry round's per-founding column insertion in the
registry (a running sum re-added from the new actor's place), the merchants' route searches, and the per-call
labour pressure and staff reads. Measure with `python3 -m sim.tests --only year_cost_shared_across_concerns` and a
year from the save with the per-phase timer; the mid-game year is still a small multiple of an early year, so this
stays open.

## Progress, round three (still open)

The interest cascade is retired by pooled lending (Complaint 580): a borrower's interest is one posting to the pool and
the lenders are paid once a year, so the cost no longer grows with lenders per borrower squared. Measured with the
mid-game save regrouped into the pool's form (the save predates it): one year fell from about twenty-nine seconds to
about eighteen, still more than twice an early year. What is left in the profile: the merchants' route searches
(`routes_search._tree`), the registry's per-founding column insertion, `forget_orders`, and the tile cost lookups.

## Resolution

Measured by an agent playtest played legitimately from a fresh game to 221 AD on the branch with both rounds of cuts
and pooled lending (580): seconds per game year stayed flat by decade over the whole run, and the save grew only a
little (`Complaints/reports/playtest-rome-seed11-agent-to-221.md`, per-command timings). The growth this complaint
names is gone; the yearly cost itself is Complaint 497.
