# Passnote: Complaint 473, the agent economy's spin-up never settles

For whoever picks this up next. It says what the goal is, where the work stands, how to measure, what was learned,
what was tried, and what to do first. **Start with section 6g and section 7**; section 6f is where the standing
(`search`) rules were left, and sections 2 and 6a to 6e are the history that led there. The detail behind every claim is in
`Complaints/473-the-agent-economy-spin-up-never-settles-so-the-opening-is-a-point-on-a-cycle.md` (Updates 24-39) and the
owner's answers in `Complaints/reports/473-owner-questions.md`. Figures are not repeated here: each claim names
the command that measures it.

## 1. The goal

Before a game, a hidden spin-up (`sim/markets/spin_up_run.py`: a first stage, a workforce trim, a trimmed stage) runs
the agent economy until it is stationary, and `spin_up_settled` must pass: every watched quantity
(`sim/economy/spin_up_state.py`: price level, rate, real output, hired hours, producers' inventory value, unmet food
need, and the prices of the goods the opening basket spends most on) moves less than `SPIN_UP_TOLERANCE` a year over the
last `SPIN_UP_MEASURED_YEARS` (`sim/markets/spin_up_gap.py`). 473 closes when that holds for every shipped civilisation
(`england_1300`, `han_china_100ad`, `mexica_1500`, `norse_900ad`, `rome_100ad`). Complaints 970, 511, 519, 526, 607,
545, 608, 554, 557 and the Rome group 960-963 wait on it.

The owner's requirements, which any change must keep:
- **Settled is a fixed point, and the economy must not be chaotic** (the owner's answer to question 1). The check is not
  to be weakened or redefined. A small nudge must move the economy a small step: doubling iron's price should move
  each good's price by about its iron cost share and leave the rest close to where it was.
- **Small goods do not decide it, and the economy takes a change without spiralling** (the owner, 2026-11-17: "I
  should be able to add a new good, remove a good, double the price, 1/10th the price of anything, and the economy
  would not suddenly spire out of control"). The settle measure therefore weighs each watched price by the year's
  spending on it (Update 35), and `perturb_probe.py` is the test of the second half.
- The project rules in `CLAUDE.md` (no hardcoded outcomes, no content ids in the engine, every heuristic declared with
  a `retire`, TDD, a test calls one function, no figures in markdown or comments).

## 2. Where it stands

Branch `economy-settles-not-chaotic` (on top of the merged `spin-up-settles`). Merged, each with a rule test (Updates
30 and 31 give the mechanism and evidence):
- Labour poaching is continuous in the employers' standing (`sim/labour/market/clearing.py`, `clearing_tail_kernel.py`).
- Household work is counted over the labour year's working days (owner question 7), and hiring servants is continuous
  in the budget and gradual (`households_work.py`, `household_servants.py`, `household_work_year.py`).
- The coin-metal opening check asks a metal-paid money that the mint's price covers the making cost (owner question 4).
- Households' durable purchases replace wear and close a share of the gap to the stock wanted; affordability falls
  smoothly (the former unmerged `durable-demand-continuous` patch).
- `requirements.txt` lists shapely (owner question 5).
- Expected inflation takes up a surveyed share of a year's surprise where it took up half, so the rate a lender asks
  no longer follows each year's price noise (Update 31).

Not settled. What moves, by civilisation (section 3 says how to measure):
- Norse: far calmer than before (household work was most of its swing); hired hours and output still move by one to
  two times the tolerance, the rate by about the tolerance, inventory value by many times it.
- England: hired hours, output, the price level and the rate move by about the tolerance or a little under it on
  average, with end gaps about at it; inventory value by several times it. Its price level falls through the whole
  spin-up because its money stock does (section 4).
- Han: hired hours, output and the price level move by one to two times the tolerance and the rate by under twice it;
  inventory value and the watched prices by many times it.
- Mexica: its output shrinks through the whole spin-up; not traced.
- Rome: not re-measured on this branch (its replay is slow and holds much memory).

## 3. How to measure (read this before changing anything)

**One run judges nothing, and eight end gaps judge little.** Two spin-ups whose households' cash differs at the
rounding level end in different places, and the end gap's spread across eight members is as large as its median. Use:

```bash
# every year of every member (members run one after another in one process), then each quantity's mean yearly move
# over the trimmed stage beside the end gap the check uses
PYTHONPATH=. python3 Complaints/reports/473-handoff/probes/ensemble_years.py england_1300 8 /tmp/years_england.jsonl
python3 Complaints/reports/473-handoff/probes/ensemble_moves.py head=/tmp/years_england.jsonl
# the committed command (end gaps and trends per member; members in parallel)
python3 sim/simulator.py spin-up-trace --civ england_1300 --stages --ensemble 8 --jobs 2
```

Compare two rules on the mean yearly move, on at least England, Norse and Han: a rule that calms one has more than once
made another swing.

**To find where a difference grows: twin runs** (`probes/twin_probe.py`, read with `show_twin.py`, `show_states.py`,
`show_detail.py`). Two economies from one opening, the second with households' cash scaled by a rounding-sized factor,
are stepped side by side and their whole records compared leaf by leaf after every year. `late_twin_probe.py` forks
the twins from one saved economy late in the trimmed stage; `phase_probe.py` compares what goes into and comes out of
the lending, planning and labour phases of one year; `hire_probe.py` looks inside the labour clearing. A difference
that jumps by many orders of magnitude in one year and one section is a discontinuity; follow it to the rule.

**To find what cycles: one run year by year.** `series_probe.py` (output by good, each labour market, each producer and
cohort, holdings by good) with `analyse_series.py`; `wage_probe.py` (one labour market's wage rule: last wage, goal,
reservation, hours offered, wanted and hired); `labour_totals_probe.py` (hours offered, wanted and hired over all
markets). The older probes of Updates 24-29 are beside them. All are scratch scripts written against the commit they
were used on: run them from a checkout with `PYTHONPATH` set to it.

**Pinned trees.** Run long measurements on a detached worktree pinned to the commit, never the checkout you are
merging into (`git worktree add --detach ../pin_<name> <commit>`).

**Machine limits.** A year of England or Norse takes about a second per economy with numba, Han a few times that, Rome
far more. Compiling the kernels for a tree takes several minutes and several GB in each process that does it, and a
new tree path or an edited kernel file compiles again; a replay holds one to a few GB. On a 16 GB, 4-core container
two compiles, or one compile and a Han ensemble, are the most that fit: more were killed for memory. A killed worker
aborts an ensemble with `BrokenProcessPool` and an empty output: check the `.err` file, not only the exit code. Do
not set `NUMBA_CACHE_DIR`: a directory kept by hand runs stale code after a kernel file that other kernels call is
edited (numba does not recompile the callers), and a round of measurements was lost to it (section 6e). The engine's
own cache directory is keyed on the source and shared by every worktree of the checkout (`sim/kernel_cache.py`).

**Environment.** `pip install -r requirements.txt` (numba, shapely). A container restart drops installed packages and
kills background runs silently. `ROME_KERNEL_CACHE_KEY=kernels` for edit-test loops.

## 4. What was learned

Each is in Complaint 473 with its evidence.

- **The first amplifier was poaching** (Update 30): hours moved between employers on which stood a hair higher.
  Fixed. The difference between twins forked late in England's trimmed stage grew several hundredfold a year before
  and grows about fourfold a year now (`late_twin_probe.py`): much slower, and still chaotic. The first years of the
  first stage amplify faster than the late ones. Until that growth is under one, members of an ensemble end in
  different places and the fixed-point test cannot pass.
- **England's and Norse's swing in hours was the households' own time** (Updates 27 and 30): household work counted
  over the civil year against a labour year of working days, and a yearly all-or-little choice to hire servants on last
  year's wage. Fixed.
- **A durable's purchase was the whole gap to the stock wanted** (Updates 29 and 30), an accelerator on a good whose
  making is most of England's measured output. Fixed by the stock-adjustment rule, which calmed England and Norse once
  the two causes above were gone (it had not, measured before them).
- **The money stock wears away** (Update 30). England's opening places its silver smelters on a route whose ore
  nothing in England mines, the mint strikes a small share of the coin wear, and the price level, the wage and the
  workers' reservation fall together at the wear rate with real balances level. Norse's and Han's money stocks also
  fall by their whole yearly loss on this branch. A fixed point of the price level needs a coin-metal chain the
  civilisation's tiles can supply at the opening, sized to the loss.
- **A quarter of England's offered hours go unsold in every year** and the wage stays a steady multiple of the
  reservation (Update 30; Complaints 608, 963).
- **The rate is the cheapest lender's ask every year** (Update 28): time preference plus expected inflation. The
  expectation took up half of each year's surprise; it now takes up a surveyed share (Update 31), and the rate moves
  by about the tolerance. What retires the share is a weight that follows how lasting the surprises have been.
- **The money stock falls in every metal-money civilisation, and prices and wages fall with it** (a correction:
  the settle test compares consecutive years, so a steady fall under the tolerance a year passes; the larger falls fail)
  (Update 31, Complaints 981 and 982). The opening's choice of the coin metal's recipes returns one phase of a cycle
  (`coin_passes_probe.py`); ores with no deposit on the economy's tiles, and the jarosite ore, which is tied to no
  deposit anywhere, are dug with no limit (`unsited_probe.py`); and the money stock is so large (households rest at
  years of income in coin, `money_ratios.py`) that its yearly loss is more metal than the ores give. On a scratch copy
  with a consistent silver chain England's money stock falls about a quarter as fast and its price level about a
  third as fast, and the lead that comes with the silver piles up unsold (Complaint 981). Owner questions 8 and 9 ask
  what to do; both are answered and Update 32 says what was built and what it showed.
- **Inventory value is a small share of a year's output**, so its relative move is the goods markets' yearly residual
  magnified. The bulk goods that carry it end a year with nothing left or a large share of a year's output left, in
  the same years as one another (`analyse_inventory.py`): look at the households' spending as a whole in those years
  before any one market.
- **Inventory value lumps come from buyers** (Update 29) and from single goods whose price creeps up and falls back.
- **The opening solver is not proportional** (Update 25).
- **Mexica's tool makers** (owner question 6): judging a learning crew on the cost of the crew it will become makes it
  run, but only a fraction of a run: entry sizes it to nothing (Update 30).

## 5. Tried and not merged

Patches are in `unmerged/` (against the `spin-up-settles` commit they were made on); branches are pushed.

| Patch or branch | Rule | Why not merged |
|---|---|---|
| branch `opening-cash-at-the-yearly-steady-state` (the `opening-grown-floor-budget` patch re-applied) | the opening meets own-plot floors before sizing the budget, as the yearly rule does (owner question 3, option a) | alone it calms England and Norse; on top of the durable rule England's hours move more and Han's hours and wage swing far more. The cause in Han is not traced |
| branch `learning-path-plan` | a crew still learning judges whether to run on the discounted cost of its learning path; entry takes the same path (owner question 6) | Mexica's wooden-tool crews go from no runs to a fraction of one: entry sizing still holds them to nothing, so it does not yet do what it is for |
| branch `sold-out-ramp-and-margin`; its halves on `ramp-only` and `margin-only` | (a) a producer counts its market's unmet demand in proportion to how nearly it sold out, on a narrow ramp where there was a rounding-share threshold; (b) the margin-entry streak is a standing that moves by how far the price stands from the entry price, entry goes ahead in proportion to it, and a recipe's entry is drawn in proportion to how far the price stands above its entry price | both rules are amplifiers the late twin probe found at the head, and both have rule tests; with both a late twin difference on England stays at rounding for three years and is orders of magnitude smaller after five, and with either alone it grows as at the head (Update 31). On the yearly moves England is level with all three; (a) alone makes Norse's hours and output move about twice as much, (b) alone somewhat more in the mean. So (a) is what swings Norse: anything that makes producers count more unmet demand makes them chase it, and the rule it smooths (a producer adding its market's unmet demand to its own expected sales) is the thing to change before the ramp can go in |
| `inflation-trimmed-mean.patch` | observed inflation a weighted trimmed mean | the rate moved as much or more |
| `stock-offered-in-tranches.patch` | held stock offered as up to four lots of a year's sales | inventory value moved as much |
| (not kept) | producers plan no stock cover and the ask only falls with unsold stock | prices fell every year: the step that raises an ask when stock is under its cover is what raises asks between years |

## 6. Owner questions

The first seven are answered (`Complaints/reports/473-owner-questions.md`, top). Done: 4, 5, 7. Question 1 is the
standing requirement of section 1. Question 2 needs nothing. Questions 3 and 6 are built on branches and not merged
(section 5). Questions 8 (what households hold their wealth in) and 9 (whether a civilisation has an ore the catalogue
lists nowhere on its tiles) are new in Update 31 and not answered; the price level waits on them.

## 6a. Where it stands after Update 32 (read this before section 7)

The owner answered questions 8 and 9; Update 32 says what was built (an ore with no deposit is dug nowhere, a deposit
type names its own ore, the opening's recipe choice settles, two researched deposits), what the research found (the
coin silver of England and the Norse was imported; the loss rates are not too high; coin was about a fifth of a
year's income) and one correction (the settle test compares consecutive years, so a steady fall under the tolerance
passes). Not merged: branch `money-at-the-yearly-steady-state` (opening without the coin hoard: the yearly rules
rebuild it out of the producers' coin and the economy ends smaller).

The thing in the way now is upstream of every amplifier: **the first years do not reproduce the opening.** Output
falls by a fifth in two years, households plan to spend about a third more than they can, the unspent coin piles up
with them and the wage and prices slide for decades (`household_accounts_probe.py`, `series_probe.py`). Update 33
starts on it with `first_year_probe.py`, `first_year_labour_probe.py` and `producer_inputs_probe.py`: one cause is
fixed and merged (an area short of people left the trades staffed last with nobody), together with the grinding
change that keeps Norse out of a zigzag the fix made more common. What Update 33 lists as found and not fixed is the
work to do next, in this order:
1. a producer hires and pays its hands before the year's inputs are bought, so one input that does not arrive (salt
   for the wool producer) costs it the wage bill and its coin, and everything downstream stops;
2. the opening sizes a producer past what its land or its tile's hands allow (wool at twice its pasture; the busiest
   tile wants a quarter more hours than it has);
3. a thin, cheap good takes most of a need's planned spending (cap a good's share by what its market usually trades);
4. labourers are offered exactly the hours wanted and seven eighths are hired; farmers' spare hours take no labouring
   work within the year.
Complaints 608 and 960 to 963 are the same fall on Rome. Owner questions 10 to 12 are open. Judge Norse on 24
members, not eight: its members fall into a calm kind and a zigzag kind, and eight cannot tell a change in how many.

## 6b. Where it stands after Update 34 (history; section 6f replaces its order)

Update 34 took the first item of section 6a (the first years do not reproduce the opening) and found four faults in
how the opening is built and one in the hiring rounds, each fixed with a rule test: a site-bound recipe with no
declared site stood whole on one tile; a processor tied to its input's site got no tile when the hands there were
spoken for; an employer with most of a market's posts could not staff them;
the opening ignored the land limits it had itself cleared (holding producers to them closes wheat and cheese, whose
plough teams and milk no opening producer makes: owner question 15); an input's price limit ignored the wages
already committed. The settle test now reads inventory
value against a year's output (owner question 11).

Measured on the head (`ensemble_years.py`, then `ensemble_moves.py`; England 8 members, Norse 24, Han 12):
- **England: every total (hired hours, output, price level, inventory value, rate, unmet need) and the wage move
  under the tolerance, on average and at the end gap.** What still fails the check is single watched prices: steel
  slides and zigzags, carts zigzag, and shoes (and in some members bread) have no price for years, which counts as a
  full move.
- **Norse: the price level, rate, unmet need and wage are under the tolerance on average; hired hours are about at
  it, output and inventory value about half as much again.** Its economy now keeps about three quarters of the
  opening's hours where it kept about half.
- **Han: the price level is under the tolerance and the rate about at it; hired hours, output and the wage are
  between one and a half and two times it** (hours were over three times it and the wage many times). Its hours and
  output still shrink through the trimmed stage, and unmet need and inventory value move by several times the
  tolerance.
- All three still fail on the watched prices. `spin_up_settled` passes for none.

Tried in this round and not merged, each measured on ensembles (Update 34 has the figures): the households' mix
anchored on usual spending, producers hiring within their inputs' reach, a sited-input processor placed per market
(better first year in Han, larger yearly moves in Norse and Han), holding the coin stock, and leaving wheat and
cheese open.

What is in the way now, in the order to take it:
1. **Han and the Norse lands are hungry from the first year** (`hunger_probe.py`): about two fifths of Han's food
   need and a sixth of Norse's. In Han the hungry tiles are fertile ones where producers outbid the household plots
   for all the land and then work about two fifths of their runs, because the iron tools the runs wear do not arrive
   and the work is done by hand; in the Norse lands they are the tiles with no farmland, with coin and no food
   reaching them. For Han start with the tools: why its iron chain opens at next to nothing while its ores are dug
   (`opening_sizes.py`), and whether the farms get the wooden tools the opening sizes in their place
   (`producer_inputs_probe.py` on a millet farm and on a wooden-tool maker). Then trace what the merchants carry in
   the first year against what the opening's placement needs moved (`first_year_probe.py` shows England's makers one
   tile away from the only ore working a third of their runs).
2. **A good in short supply is rationed for years because its price cannot leave the band above its cost, and the
   rationing is pro rata among households and makers alike** (Update 34). England's shoemakers lose their leather
   and Han's farms their tools to household spending, and Han's hunger follows from the second. Serve first the bids
   that would pay most (a bid's maximum price) inside a priority tier: `goods_market_ration.ration` and its kernel
   twin `goods_market_kernels.serve`, with the packers that order bids into tiers (`goods_market.py`,
   `bid_columns.py`, `goods_pack_kernel.py`, `goods_market_demand.tier_bounds`). Probably the largest single step
   left for Han.
3. **The money stock falls every year in every civilisation** (owner question 13). Holding it for the length of the
   spin-up does not help the check (England the same, Norse a little worse); over a long run the fall takes the wage
   and the price level with it. A long-run matter, behind the two above.
4. The single goods: steel, carts and draught animals (zigzags), the unsold co-product, and the data that makes
   raw leather clothe a household better than the shoes made from it (owner question 14).
5. Rome and Mexica have not been measured on this tree.

## 6c. Where it stands after Update 35 (history; section 6f replaces its order)

Update 35 followed the owner's direction of 2026-11-17 (section 1). Five fixes, each with a rule test: the settle
measure weighs each watched price by the year's spending on it; the opening's supply fit serves a maker's plant
upkeep before it cuts the other users; the opening never sizes plant on a working share under the one at
break-even (a price a tenth of cost had sized plant and coin larger by many orders of magnitude); a producer
that lost money no longer closes workplaces its expected sales still call for; and a price under what a unit costs
is pulled up to it in full, sold out or not. The fourth removed the Norse lands' tipping point: an input shortage
made the farms work by hand at a loss in a market short of grain, and the loss rule closed a quarter of them a
year (Update 35 traces the whole chain from the tar burners' wood to the farms).

Measured on the head (`ensemble_years.py`, then `ensemble_moves.py` and `member_gaps.py`):
- **England:** every total under the tolerance on average; five of eight members pass the whole check, the rest
  fail by a hair on one quantity or two.
- **Norse:** every checked quantity under the tolerance on average, no split into a collapsed branch, hired hours
  near the opening's; two of twenty-four members pass. A slow rise of output and hours remains, and about a fifth of
  the food need is unmet for good.
- **Han:** about as it was: hired hours and output a little over the tolerance, unmet need and inventory value two
  to three times it, no member passing, hired hours falling through the whole spin-up and a third of the food need
  unmet from the first year.
- Perturbed runs (`perturb_probe.py`) stay bounded in England and the Norse lands; the Norse ones land far apart.

What is in the way now, in the order to take it:
1. **Unmet demand does not draw supply across market areas** (Update 35, "Found and not fixed", first item; the
   Norse lands' hungry seventh). Three steps, each small: (a) a market with buyers and nothing on offer should not
   remember the national making cost, which is under the price where the good is grown; let its remembered price
   rise with the unserved bids at the pace a sold-out seller raises its ask (`goods_remember_kernel.signals`,
   `year_remember.remember_one`, `market_quote.no_trade_quote`, `goods_market_rows.bids_only_quote`), capped at the
   best unfilled bid; taking the bid itself is wrong, since a household's ceiling for a dear good is its whole need
   budget (`quote_probe.py` shows it); (b) the volume merchants learn for a market should count its unmet demand
   (`year_close.learned_prices`, `record.goods.unmet`), so `merchants_shares.room_left` is not nothing where nothing
   is sold; (c) the opening's merchants (`opening._open_merchants`) sized on what its placement needs moved between
   areas. Two more rules meet these on the way and need the same look: households bid only for what is on offer
   (`market_memory.offered_price`), so after the first year the only bids for grain in those areas are the mills',
   whose ceilings sit under the landed cost; and a market whose only ask stands above its best bid remembers the
   bid, which is not a price a household can see. Measure with `hunger_probe.py`, `hungry_area_probe.py`,
   `quote_probe.py` and `merchant_beliefs_probe.py`.
2. **A maker closed for want of buyers does not come back when they return** (the iron-ore miners in Update 35):
   closure at a sliver of past scale and regrowth by a share of what is left. Let a maker with no plant grow toward
   its buyers' call from any size (`capacity_growth.grown_capacity` takes a step of the capacity it has), and look
   at whether a maker with no plant needs a capacity at all.
3. **A price moves a few per cent a year and capacity a quarter** (`ask_adjust`, `producers.OUTPUT_CHANGE_SHARE_PER_YEAR`):
   a good opened at a wrong price loses its makers before the price finds its cost, which is why the perturbed
   Norse runs land low. A sold-out maker whose cost a unit rose (hand work, a dearer input) should pass it on.
4. Han's hunger (section 6b, items 1 and 2: the farms' tools and pro-rata rationing).
5. England's last hair: steel's slide and zigzag, bread's makers (their ask is capped under their cost).
6. The money stock (question 13), then Rome and Mexica, unmeasured on this tree.

## 6d. Where it stands after Update 36 (history; section 6f replaces its order)

Update 36 traced Han's first-year hunger to the opening contradicting its own first year, and fixed three things,
each with a rule test: a recipe bound to its own site (felling) takes no cropland; households open with the tools
their plots wear; each opening pass sizes its demand on the plots the solve's land markets have left. Update 35's
last fix (a price under cost is pulled up in full) took England from two to five of eight members passing.

Measured on the head (`ensemble_years.py`, `ensemble_moves.py`, `member_gaps.py`):
- **England:** five of eight members pass the whole check; the rest fail by a hair on one quantity or two.
- **Norse:** one of twenty-four passes. Hired hours and output move about a third over the tolerance on average
  (medians under it); about a fifth of the food need unmet late in the run, less in the first twenty years.
- **Han:** none passes. About a twentieth of the food need unmet for thirty years where over a third was; output
  and the wage move by several times the tolerance while hired hours fall to a third of the first year's.

What is in the way now, in the order to take it:
0. **Trade between food areas comes first after all** (section 6c, item 1). Update 36's last trace shows the Norse
   tool shortage, and so the farms' hand work behind item 1 below, starts in an unfed area: the ore tile's
   households stop selling hours when no food reaches them. Han's one area with no grain farm is the same gap. The
   whole of it: (a) the remembered price of a market with buyers and nothing on offer; (b) the volume merchants
   learn where nothing is delivered; (c) a household sees a seller's ask only when the market's remembered kind is
   an ask, and a market with a low bid and a higher ask remembers the bid (`goods_table_quotes.quote_of`,
   `market_memory.offered_price`); (d) one merchant dares a share of a market, and the Norse lands open with one
   (`merchants.MERCHANT_MARKET_SHARE`, `opening._open_merchants`); (e) a merchant sells a year after it buys, so
   the opening must also put a year's carried goods in the importing areas. Seeding the opening's merchants with
   the flows its placement implies (stock landed, prices and volumes expected) and fixing (a) to (c) is the build.
1. **The workforce trim and the tight labour market after it** (Norse; Update 36). The grain farms slump for three
   years after the trim and the farmers' wage then alternates year by year. Look at what
   `economy_api.trim_workforce_to_expected_hours` leaves a trade whose employers work part of their runs by hand
   (the hours hand work takes are not the hours the runs' recipe states), and at a labour market with no idle
   hands (`recipe_coin_probe.py norse_900ad 0 45 millet_kg` shows both).
2. **Land between plots and farms** (Han; Update 36). Strict priority by bid hands every contested hectare to one
   side: the farms at the opening (a plot's own return is nothing at the opening's prices), the plots later. A rule
   that shares contested land in proportion to the bids, or leases that last, would stop the forty-five-year slide.
   Then the opening and the years would agree on who works the land.
3. **Trade between food areas** (section 6c, item 1): the Norse lands' unfed seventh and Han's one area with no
   grain farm (`area_first_year_probe.py`). Still the largest gap between the opening and the first year.
4. Section 6c, items 2 and 3 (a maker closed for want of buyers does not come back; prices move slower than
   capacity).
5. Owner question 16 (pasture and forest recipes take cropland; Han's poppy), question 13 (the money stock).
6. Rome and Mexica, unmeasured on this tree.

## 6e. Where it stands after Update 37 (history; section 6f replaces its order)

**A measuring rule first: never set `NUMBA_CACHE_DIR`.** The pinned worktrees of this work did, to keep their
caches apart. numba checks only the file a kernel is defined in, so a kernel that calls one in another file kept
the old code after that file changed, and a whole round of ensembles ran stale market kernels (Update 37). The
engine keys its cache directory on the source (`sim/kernel_cache.py`): leave it to that. A sign of a stale run is
two trees that differ in a kernel giving the same figures to four digits.

The owner (2026-11-18): the opening's figures are guesses that should be replaced by the years' own steady state, and
prices should clear as in a real economy. The upward half was built (a sold-out seller's ask rises as far as its
buyers' money goes, no band above cost, every producer a price taker), reported as harmless on stale kernels, and
reverted when a clean run showed it sets England swinging by a quarter a year. The code under `sim/` is the tree of
section 6d again; the change is `tried/prices_clear_upward.patch`.

Not measured, whatever earlier notes in the scratch outputs say: the four patches of `tried/` that make output or
prices answer faster, and the placement patch. Each needs a clean run alone.

Clean baselines on this tree (Update 37): England five of eight, the Norse lands one of twenty-four, Han none of
twelve. The sold-out raise with no band is, alone, what sets England off; with a seller reading its buyers'
schedules at cost in place of the buyers the band turned away, the swing is under half as large and still many
times the band's.

Order from here:
1. **The opening places makers where the years cannot supply them** (Han; Update 37 lists them: kilns on two tiles,
   presses away from the olives, farms sized on tools the ore cannot give). `tried/placement_beside_inputs.patch`
   holds two rules with tests: a market area that holds a processor's fixed input makes its own share; a crop only
   some tiles grow pulls its processors as a mine does. Measure each alone on the Norse lands and Han. The first,
   alone, leaves England's quantities as they are and its weighted prices a hair over (clean). The one run of both
   together on the Norse lands was on the reverted change's tree, so it is not a reading; it showed more hunger,
   which would fit mills moved away from where flour is eaten, so the second rule may need the pooling
   `_where_it_crops` does.
2. **Prices that clear**, the owner's direction. Under the band a sold-out seller sees the buyers it turned away
   and expands; a clearing price turns nobody away, so the seller needs another steady answer to a high price.
   Measure the patches of `tried/` together with `prices_clear_upward.patch`, one at a time, with the engine's
   cache; none of them alone is the test.
3. **Trade between food areas** (section 6d, item 0); `tried/trade_rules.patch` holds the two rules written so far.
4. **The workforce trim** (Norse; section 6d, item 1).
5. Han's slide is not the money stock and not the land rule (Update 37). What is left to test: the first year not
   reproducing the opening (item 1), and employers wanting fewer hours every year while labour stands idle
   (`labour_totals_probe.py`).
6. Owner questions 13 and 16; Rome and Mexica, unmeasured on this tree.

## 6f. Where it stands after Update 38 (read this first; it replaces the order in every section 6 before it)

**Measuring rules that cost a round of work each to learn.**
- Never set `NUMBA_CACHE_DIR` (section 6e). Run probes and ensembles with the engine's own cache, from a worktree
  pinned to one commit, with `PYTHONPATH` set to that worktree.
- Compare a change with a baseline run on the same commit with the same cache. Two trees that differ in a kernel
  and give the same figures to four digits mean a stale run.
- England eight members, the Norse lands twelve to twenty-four, Han four to twelve (Han's members take minutes
  each). Run at most two ensembles at once on a 4-core, 15 GB machine; a third, or a kernel compile beside two,
  gets processes killed for memory.

**The tree.** The code under `sim/` is what Updates 30 to 36 built; prices that clear upward were reverted
(Update 37). Clean baselines, all with the engine's cache: England five of eight members pass `spin_up_settled`,
the Norse lands one of twenty-four, Han none of twelve (`ensemble_years.py`, `ensemble_moves.py`,
`member_gaps.py`, `series_means.py`).

**Tried and kept as patches** (`tried/`, each with its tests; "clean" means measured with the engine's cache):

| Patch | Applies to | What it does | Measured |
|---|---|---|---|
| `prices_clear_upward.patch` | this tree | sold-out ask rises as far as buyers' money goes, no band; every producer a price taker; yearly ask step with no ceiling | clean, England: violently unsteady (Update 37); its no-band raise alone is the cause |
| `wanted_at_makers_cost.patch` | on top of the one above | a market's wanted quantity read at its makers' cost, so a seller still sees demand beyond what it sold | clean, England, with the one above: less than half its swing, many times the baseline's |
| `demand_at_revenue_over_cost.patch`, `sell_out_holds_expected_sales.patch`, `unsold_floor_at_cost.patch` | on top of `prices_clear_upward.patch` | other answers of output or price to a price that clears | **not measured cleanly** |
| `placement_beside_inputs.patch` | this tree | (a) a market area holding a processor's fixed input makes its own share; (b) a crop only some tiles grow pulls its processors | (a) alone, clean: England's quantities as the baseline's with its weighted prices a hair over (two of eight pass), Han as the baseline, the Norse lands a little calmer (Update 38); (b) not measured cleanly |
| `resting_producer_purse.patch` | this tree | producers open with the cash the year's close keeps | clean: England calmer, the Norse lands worse, Han as the baseline (Update 38) |
| `trade_rules.patch` | written before Update 37 | what a market with buyers and nothing on offer remembers; the market size a merchant learns | not measured; not enough alone to carry grain |

**What the readings say** (Updates 37 and 38):
- Under the band a sold-out seller sees the buyers it turned away and grows; a price that clears turns nobody away,
  output that has fallen does not come back, and the price runs up. Prices that clear need a steady answer of
  supply to a high price first.
- The opening's figures are not the years' resting figures: incomes (the opening counts about twice the property
  income the first year pays), producers' coin, capacity, some prices (England's steel glides down all run),
  where makers stand. Each corrected alone moves another (the purse calms England and unsettles the Norse lands).
  This is the owner's point that the opening is a guess.
- Han's slide (hired hours and output to about a third) is not the money stock, not the land rule, not the kilns'
  placement and not the producers' opening coin. Read so far: a third of hours offered unhired from the first year,
  the hours employers want falling every year, households' coin rising, producers' falling, most of the vessels and
  shelter floors unmet.

**The owner's open decision.** Two directions pull against each other: prices that clear (the owner's ask) and a
settled economy (the goal). The recommendation given was to keep the band for now, make the opening the years'
resting state and fix trade between areas, and come back to clearing once supply answers a high price steadily.
No answer had come when this note was written; ask before building on either side of it.

## 6g. Where it stands after Update 39 (read this first)

**The owner's direction (2026-11-20).** Rebuild the two core loops as "find the clearing value inside the year, then
move what carries between years a fixed share toward it", swapped in beside the standing rules and not in place of
them; and the headline test, "an economy should settle close to the same thing, even with a 5% change". The first
pull request is done when the hand-built economy rests and England passes the unchanged settle check. Neither
direction of section 6f's open decision was waited for: prices that clear are what was built.

**The smallest economy is the place to work.** The three-tile economy (`sim/economy/fixture_setups.py`) has the
fault on the standing rules and runs ninety years in seconds without numba (`ROME_NO_JIT=1`):

```bash
python3 sim/simulator.py spin-up-trace --fixture stationary --rules search --twin --years 90     # never rests; the twin drifts off
python3 sim/simulator.py spin-up-trace --fixture stationary --rules clearing --twin --years 90   # rests; the twin stays close
python3 -m unittest sim.tests.test_economy_rest_smoke                                            # what the clearing set is held to
```

A change is judged there first, by three things: the yearly moves once it rests, the gap to the twin, and where it
rests from a start five per cent off. Only then on a civilisation. The earlier rounds worked on civilisations, where
one reading takes minutes to hours and differs from run to run.

**The tree.** `sim/economy/rule_sets.py` names the year's swappable rules; a setup names its set and each phase asks
for its rule. `search` is the rules of section 6f, untouched and the default; `clearing` is the new set
(`docs/architecture/ECONOMY_AGENTS.md`, "Rule sets"). A game opens on `search` unless its configuration names
`economy_rule_set`. To run a civilisation's spin-up on another set without a configuration, swap `rule_sets.of` in a
scratch runner before running `sim/simulator.py` (Update 39 says how it was done), with its own `ROME_CACHE_DIR`:
the spin-up's cache key does not know about the swap.

**What holds and what does not** (Update 39 has each with its command).
- On the three-tile economy the clearing set rests, keeps a twin close, and answers a better yield or fewer people
  the way an economy should.
- A start five per cent off rests somewhere else (three expected failures in the smoke test): a producer's capacity
  depends on the path, and one bankruptcy idles every workplace of a recipe on a tile for a year.
- England on the clearing set slumps from the seventh year and ends far from settled. Not traced.
- The clearing set's object-level parts are about ten times too slow for a civilisation's year.
- Three capacity rules were tried and taken out (by margin; both ways toward what sales call for; growth only).
  Each failed for the same reason: the coin a producer keeps follows its whole capacity.

## 7. What to do first

After Update 39 (the list under it is the order for the standing rules, kept for when they are worked on again):

1. Build the smallest economy that slumps on the clearing set as England does (a recipe with plant, a chain of
   inputs, a floor wage that binds, hours idle) and make it rest. First suspect: production with no hold where
   labour does not bind.
2. Bankruptcy by share: a producer stands for many workplaces, so a share of them fails.
3. A capacity rule with one rest point, after the coin a producer keeps follows its working scale.
4. Kernels for the clearing set's object-level parts.
5. England on the clearing set again; then make it the game's set (`sim/markets/port_setup.py` `GAME_RULE_SET`),
   run the fingerprint on `search` against main, the slow suite, and rebuild the openings.

Before Update 39:

1. Reproduce the England baseline yourself: `PYTHONPATH=<checkout> python3 Complaints/reports/473-handoff/probes/ensemble_years.py england_1300 8 out.jsonl`,
   then `ensemble_moves.py base=out.jsonl` and `member_gaps.py out.jsonl`. Five of eight should pass.
2. **The opening as the years' resting state, England first** (the owner, 2026-11-18). Not designed yet. Work out
   which of the opening's figures the years move away from and where they rest (`series_means.py` over a long run;
   `price_cost_probe.py`, `stock_probe.py`, `opening_income_probe.py`), then whether the opening can take them from
   a late year of its own spin-up instead of solving them from guesses. Check first what `openings/` stores and how
   `sim/engine/opening_checks.py` reads it, so the change fits the shipped-opening machinery.
3. Han's slide: test the reading above. `first_year_limits_probe.py`, `first_year_takers_probe.py` and
   `hours_fall_probe.py` show which makers are short of what; `labour_totals_probe.py` and
   `household_accounts_probe.py` show the hours and the coin.
4. Only after the owner answers the decision above: prices that clear, starting from the table's patches, each
   measured cleanly on top of `prices_clear_upward.patch`.
5. Trade between food areas (section 6d, item 0), the workforce trim (section 6d, item 1), owner questions 13 and 16,
   Rome and Mexica (unmeasured on this tree).

Before any PR: `python3 -m sim.tests --slow`, then rebuild openings as the last commit
(`python3 sim/simulator.py openings --prune`) and check `python3 tools/check_openings_current.py` lists none stale.
