# Generalising the economy: what is done, what is deliberately left, and what was not measured

This is the design note the task brief asked for when a piece of work is
committed unfinished. Read `rome/data/review/COMMODITY_DYNAMISM.md` first;
this note assumes it.

## What is actually done

1. **Every material key the tech tree uses (162, not 13) now gets a real
   supply/demand price response.** `economy.py`'s `_material_tag()` resolves
   any material key to a commodity - a curated one (the original 9) where
   one exists, its own bare key otherwise - and `material_price_factor()`/
   `material_market_factor()` no longer bail out at 1.0 for anything not on
   the original hand-written list. The MARKET half of supply
   (`_material_market_tonnes`) and the OWN-PRODUCTION half
   (`open_mine`/`mine_quote`/`close_mine`, generalised beyond the seven
   hand-named metals) both fall back to a generic figure derived from the
   material's own book price when no curated number exists. See
   `economy.py`'s own comments on `GENERIC_OUTPUT_ANCHOR_T_PER_YR` and
   `GENERIC_MINE_CAPEX_MULTIPLE` for the fit and its reasoning.
2. **The goods market has real cross-elasticity.** `goods_market_factor()`
   now shares one total-supply figure across every concern in the same
   `GOODS_CATEGORIES` category (`_goods_category_state()`), instead of each
   concern pricing off its own private per-node age clock. Two identical
   concerns measurably compete; a lone concern's day-one behaviour is
   unchanged (mathematically identical to the prior formula when
   `n_active == 1`).
3. **`GOODS_CATEGORIES` covers the tree's real consumer/entertainment
   nodes**, not just textiles/processing/printing/photography:
   fermentation (brewing, distilling), leisure (toys, games, books),
   sound (phonographs, radio broadcasting), media (newspapers,
   advertising), commerce (inns, hotels, restaurants), luxury/spectacle/law
   (gambling, theatre, racecourses), personal (perfume, cosmetics).
4. **An income effect exists.** `income_factor()`/`essential_price_ratio()`
   couple a cheaper, more saturated essential (food/`processing`) market to
   more spending on discretionary categories - the brief's own worked
   example, verified against a real gambling-house node in
   `test_regressions.py`.
5. Player visibility: `money` now surfaces `materials_costing_you_a_premium`
   (new) alongside the existing `the_market_you_sell_into`, and
   `goods_market_note()`/`goods_market_summary()` both say when competition,
   not just time, is why a concern earns less.

788 checks pass (757 from the merged baseline + 31 new), and
`simulator.py validate` passes.

## What is deliberately NOT done, and why

- **`commodities.json` still defines only 9 commodities.** The
  generalisation is in CODE (a generic fallback derived from a material's
  own book price), not in DATA (a hand-authored entry per material). This
  was a deliberate choice: authoring ~150 more curated entries would be a
  large, unauditable data-entry exercise and would not actually be more
  general than the code-side fallback - a new, never-anticipated material
  key added to the tech tree tomorrow gets a working price response with
  zero further edits under the code-side approach, which is the actual
  standard the brief set ("a commodity nobody anticipated must behave
  correctly... not because somebody wrote a rule for it").
- **Population's effect on demand is still indirect.** `tau` (how fast a
  goods category's price/quantity settles) scales with `pop_scale**0.5`,
  which dilutes a fixed supply's saturating effect in a bigger market - but
  there is still no independent, absolute "population wants N tonnes of
  bread a year" demand baseline anywhere in the model, for the goods side
  or the raw-material side. This is a real, named scope limit, not an
  oversight: building an absolute per-capita demand table for 162 materials
  and ~15 goods categories, calibrated against real consumption estimates,
  is a substantially larger research task than generalising the existing
  ratio-based mechanism was, and doing it badly (unsourced numbers dressed
  as data) would be worse than naming the gap honestly.
- **The income effect has one essential category (`processing`, food).**
  `ESSENTIAL_CATEGORIES` is a set precisely so this can grow, but nothing
  else in the tree was judged an unambiguous physical necessity the way
  food is, and the brief's own worked example is specifically about food.
- **No multi-agent market.** This remains a solo-player economy against a
  static empire backdrop (COMMODITY_DYNAMISM.md's own scope note): "does
  anyone else's project get cheaper" has no answer because there is no
  concept of another economic agent buying the same market.

## What was and was not measured

`timeout 1800 python3 rome/sim/test_regressions.py` (788 checks, 0
failures, ~110s) and `python3 rome/sim/simulator.py validate` (OK) were
both run to completion and passed, repeatedly, through this work.

The Monte Carlo win-rate/median-year/median-technology measurement the
brief asked for (`--mc 6 --horizon 700`) was **not obtained at that scale**.
On this shared machine a single `--mc 6 --horizon 700` trial run took
15-20+ minutes (CPU contention from several other agents' sessions running
concurrently), which is not a budget this task can spend twice for a
before/after comparison, and a single-sided number with no baseline to
compare against would not have supported any conclusion anyway.

What WAS run, at the cheaper `--mc 2 --horizon 500` setting, both before
this change (commit `f9a8207`, the merged baseline before this branch's
economy work) and after (this branch): **both score 0/2 reaching the goal,
both fail by "ran out of horizon," with comparable material-shortage
patterns (iron and coal binding in both).** This is not informative about
win rate - `--horizon 500` (year 600 AD) is shorter than this strategy's
own median completion year under the *previous, larger* measurement this
branch captured before being told to stop (below), so neither run was ever
going to reach the goal in that window - but it is a real, if narrow, check
that this change did not introduce an obvious new failure mode or block
reachability outright at the start of a run.

One number from earlier in this session, run to completion before the
budget correction above, is worth recording for context even though it has
no controlled after-comparison at the same scale: `--mc 6 --horizon 700`
on the pre-generalisation code (commit `c349a17`, before even the
labour_productivity merge) reached the transistor goal in 5 of 6 trials
(83%), median completion year 766 AD (666 years elapsed), with iron (103
run-years), coal (90) and saltpetre (12) as the binding shortages. No
equivalent post-change number exists. **This is stated as an unmeasured
gap, not implied by omission**: whether the generalised material pricing
measurably changes win rate at the game's intended scale is an open
question this pass did not answer.

## If this makes the game harder

The generalisation is honest in the sense the brief asked for: prices can
now genuinely rise for materials that used to be free lunches (glass,
silk, industrial-age alloys bought in bulk with no price consequence
before this pass), and the goods market's cross-elasticity means a player
who builds many concerns of the same kind no longer gets each one at full
price. Both are more realistic and both could, in principle, make an
already-tight game (the existing GOODS_CATEGORIES floors were themselves
tuned up once already, per that section's own comment, because a harsher
first pass turned a marginal win into a loss for han_china_100ad) harder to
win. The regression suite and `validate` both stayed green throughout,
which rules out a *mechanical* break, but it does not by itself rule out a
*balance* regression, since the suite tests behaviour, not win rate. The
honest position, absent the larger measurement above: this is more
realistic, it plausibly tightens the game rather than loosens it (more
things cost more when demand is real; competition reduces windfall
revenue), and confirming the direction and size of that effect at the
game's intended scale is the next thing to do with a properly-budgeted
measurement run, not something this pass can respectably claim from a
500-year, 2-trial smoke test.
