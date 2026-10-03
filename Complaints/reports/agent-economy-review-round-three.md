# The agent economy, round three

Follows `agent-economy-review.md`. In this round only `sim/economy/` could change, and new files in
`Complaints/`. Regression tests therefore ran as scratch unittest files outside the repository. Their
sources are in `agent-economy-scratch-tests.md`, to be copied into `sim/tests/` (Complaint 396).

Unless a table says otherwise, measurements use
`python3 sim/economy_validate.py --years 30 --seeds 1,2,3,4,5,6`, summarised as medians over the seeds.
Two seeds proved too few: metal volatility moves by 30-70% between seeds, so every keep-or-drop
decision below was taken on six seeds.

## Merged

- **Rent damping** (`land_lease.py`).
  - Cause: rent jumped from zero to a large value as soon as a tile's use spilled into its second-best
    land band. Producers planned with last year's rent, so demand and rent chased each other.
  - Change: the posted rent now closes a share of the gap to the clearing rent each year, like a lease
    being renegotiated.
  - Effect (Rome, seed 1, 16 years): the mean year-on-year swing of the maximum rent per hectare fell
    from about 20 to about 5, and its average level barely moved.
- **The audit's metal gap is timing, not a leak** (`money_audit.py`). Coin wear is booked at year
  close, after the mint last matches its metal to the coin; the mint removes that metal early the next
  year. Each year's gap equalled that year's wear in Rome, England and Norse. The audit now reports the
  wear separately as `metal_awaiting_wear`.
- **Speed (390)**, with prices, wages and rate byte-identical before and after:
  - each good's market areas are cached;
  - merchants price carriage once per source tile;
  - ledger posting is faster;
  - household price ceilings are built once per tile;
  - the yearly save no longer deep-copies with `asdict`.

  A Rome year went from about 2.8 s to about 1.3 s, measured on a busy machine.
- **Goods without a mass** (`good_mass.py`):
  - draught animals weigh their live weight from `sim/world/transport.py`;
  - land and energy cannot be carried;
  - a `_tons` unit is a tonne;
  - one-item recipes take the mass of their inputs;
  - a 1 kg fallback remains only as a declared heuristic.

  The data gaps are Complaint 399.
- **Ledger underflow**: a balance left below zero by less than the smallest normal float is rounding
  residue, not an overdraft. Before this, a -5e-324 residue stopped a Rome year.

## Tried and not merged

- **Entry on price** (`entry_price.py`, branch `price-entry-diagnosis`).
  - What it does: makers enter where a known recipe's return, rent included, beats the rate, sized at a
    small share of last year's volume.
  - Six seeds, baseline → with entry:

    | | England | Han | Mexica | Norse | Rome |
    |---|---|---|---|---|---|
    | wage, kg per hour | 0.25 → 0.37 | 0.31 → 0.37 | 0.10 → 0.18 | 0.39 → 0.60 | 0.15 → 0.17 |
    | hungry mean | | | 0.006 → 0.045 | | 0.025 → 0.014 |
    | metal volatility | | 0.30 → 0.40 | | 0.38 → 0.78 | 0.85 → 1.02 |

  - Wages rose everywhere, as competition should make them, but Mexica's hunger rose about sevenfold
    and Norse metal volatility doubled.
  - At a larger entry share, wheat's price falls most of the way to its cost, but the overshoot doubles
    grain volatility.
  - A sizing rule that ties an entrant to the price-over-cost gap and the market's demand slope is the
    next step.
  - Price entry is not what makes metals swing: with entry off, Rome metal volatility is about 0.98.
- **Competitive storage for durable goods** (branch `merchant-storage-durables`).
  - Storage was limited to goods with low spoilage and a low warehousing cost against their price.
  - With two seeds the results were mixed. Grain volatility rose in Rome although no grain is stored:
    storage cash is taken before arbitrage.

## Diagnoses

- **Labour is mostly idle and prices sit far above cost (Complaint 398).**
  - Hiring: in every civilisation only 5-14% of offered hours are hired, so the unskilled wage sits at
    the family floor per offered hour.
  - Income: wages are 10-14% of household income; most of the rest is dividends.
  - Prices: wheat sells at 11-25 times its labour cost, with rent at 4% of the price or less.
  - Wheat wage: the low wheat wage in Rome and Mexica (388) is mostly wheat's relative price. In
    food-need units the civilisations are close. Mexica has no maize good.
- **Metals swing from the input chain and from forced dumping (387).**
  - The iron price is mostly the inverse of the same year's quantity, against very steep demand. There
    is no period-two cobweb on capacity.
  - Producers cost a run at last year's raw input prices but value its output at smoothed expectations,
    so an input chain (ore, charcoal, bloom, bar) hands swings down the chain.
  - Each producer's cash target is a year of costs at full capacity while it works 5-30% of it, so it
    always looks short of cash and offers its stock at a price of zero.
  - A fix smoothing input expectations and measuring distress at the scale actually worked lowered
    metal volatility over five seeds, but raised Rome grain volatility and hunger a little. Its six-seed
    result is below.
- **Six-seed baseline of the branch** (before the goods-mass change):

  | | grain | metal (range) | wage kg/h | hungry |
  |---|---|---|---|---|
  | england_1300 | 0.155 | 0.48 (0.35-0.72) | 0.25 | 0 |
  | han_china_100ad | 0.184 | 0.30 (0.24-0.41) | 0.31 | 0.014 |
  | mexica_1500 | 0.112 | 0.25 (0.23-0.27) | 0.10 | 0.006 |
  | norse_900ad | 0.148 | 0.38 (0.20-1.34) | 0.39 | 0.004 |
  | rome_100ad | 0.110 | 0.85 (0.76-1.07) | 0.15 | 0.025 |

  Rome's metal volatility is robust across seeds; it is not noise.

## Merged after the six-seed comparison: input smoothing and distress at working scale

`producers.py` now does two things differently:
- A producer plans with smoothed expectations of its input prices, while still bidding at the live
  market price.
- It judges cash distress against the scale it can reach next year, not its whole plant, so it holds
  stock instead of offering it at zero.

Six seeds, current branch (with the goods-mass change) → with this change:

| | grain | metal | wage kg/h | hungry |
|---|---|---|---|---|
| england_1300 | 0.16 → 0.15 | 0.50 → 0.29 | 0.25 → 0.27 | 0 → 0 |
| han_china_100ad | 0.13 → 0.11 | 0.28 → 0.27 | 0.36 → 0.48 | 0.007 → 0.014 |
| mexica_1500 | 0.095 → 0.100 | 0.24 → 0.23 | 0.094 → 0.099 | 0.004 → 0.006 |
| norse_900ad | 0.15 → 0.16 | 0.47 → 0.69 | 0.36 → 0.38 | 0.002 → 0.001 |
| rome_100ad | 0.099 → 0.097 | 0.94 → 0.22 | 0.150 → 0.159 | 0.017 → 0.012 |

Correction: these six seeds share one spin-up per civilisation (Complaint 400), so this table is one
draw of the economy each civilisation starts from. Rome's 0.94 to 0.22 was largely luck in that draw.
The draws-based result is in the next section.

Two results went the wrong way:
- Norse metals got worse; this is being traced.
- Han's hunger went back to the level of the first six-seed baseline.

The goods-mass change alone (first six-seed baseline → current branch) halved Han's hunger and cut
Rome's by a third.

## Tried and not merged: growth from retained profit

Branch: `producer-growth-from-profits`.

The diagnosis, from Rome seed 1:
- Producers whose recipe has no plant (`plant_life_years` 0) cannot expand at all. `_expansion` in
  `producers_close.py` makes no request for them, so they grow only through entry, and entry fires
  only where buyers are turned away.
- In each year, about a quarter of all producers earn above the rate and work at least 90% of
  capacity. About 95% of those have no plant.
- Plant-recipe expansion does reach the credit market. It is limited by borrowers' rate ceilings, not
  by lenders.

The trial let a sold-out, profitable plantless producer grow from retained profit before paying
dividends, capped at a share of capacity a year (results below are seeds 1-3, Rome, England and
Mexica):
- The unskilled wage roughly tripled.
- Grain volatility roughly tripled.
- England's hunger rose from zero.
- The limestone spread did not narrow.

So more capacity without a demand-side brake reproduces the cobweb.

The high limestone prices are a different trap: a stale ask. Those areas hold unsold stock, produce
nothing (`runs_for_stock` caps runs at near-zero expected sales) and trade nothing, so their
remembered price freezes. The cure is in `producers.py`: cut an ask far above any bid, and let the
expectation fall while stock sits unsold.

## Merged: an idle producer is not pressed to dump stock

The Norse trace found three things:
- Norse's metal chain barely exists after the spin-up. Copper, lead and tin makers have almost no
  capacity, so their prices sit at opening values until a thin market prints one.
- The copper maker dumped its stock at zero while holding plenty of cash. Its working-capital target
  was priced at the shadow price of an input nobody makes.
- Whether a chain exists at all is a spin-up lottery: a copper entrant got its plant built in one code
  version and not in another.

Fix (`producers.py`): the cash a producer lacks is measured against the share of its next-year runs
that would pay. A producer whose runs do not pay, or cannot be priced, needs no working capital and
keeps its holding reservation.

Since six seeds are one spin-up draw, the change was measured over six draws instead: Rome, Norse and
England, seeds 1-3, with an expectation constant set to six values between 0.4 and 0.65, each giving
a different spin-up. Mean (max) metal volatility over those draws:

| | before | after |
|---|---|---|
| norse | 0.45 (0.86) | 0.28 (0.40) |
| england | 0.26 (0.47) | 0.22 (0.34) |
| rome | 0.64 (1.07) | 0.57 (1.11) |

On the shipped constant alone, Rome reads 0.95 after, against 0.22 before. That is a draw lost, not a
systematic effect. Han's hunger rose slightly, from 0.014 to 0.017.

The robust fixes left for metals are in entry sizing and plant purchase. A Rome bronze entrant of
about 12,000 runs, and a copper entrant that could buy too little clay to build its plant, both
decide the draw.

## Merged: newcomers sized to the trade they can see

`entry_sizing.py`, called from `entry.entry_plans`, sizes a new maker by the smallest of four limits:
- its old share of the unmet demand;
- a share of what its market traded last year;
- a share of what each input's and plant good's market traded, per unit the maker would use;
- where its market or an input's traded nothing, a small trial size.

Before, 39% of new makers in a Rome game (seed 2, spin-up included) went into markets that had
traded nothing, at sizes up to about 10^16 times the trade. Mean and worst metal volatility over five
spin-up draws (seeds 1-3 each), before → after:
- Rome: 0.55 and 1.11 → 0.20 and 0.23.
- England: 0.24 and 0.34 → 0.18 and 0.28.
- Norse: the mean is unchanged (0.23), but the worst draw went from 0.29 to 0.57.

Grain volatility and wages were unchanged. Rome's hunger rose slightly, from 0.016 to 0.018. This is
the first change whose metal gain holds over every draw.

## The stale-ask trap needs the market side

A producer holding unsold stock now marks its expected price down (branch `producer-stale-ask`). That
alone did not unfreeze the limestone markets. In those markets nobody bids at all, so
`year_goods._unsold_signal` has no signal and the remembered price never moves. Buyers plan from that
frozen price, find their runs do not pay, and never bid: a circular trap.

Making a no-bid market remember the lowest ask unfroze the markets, but the prices then cycled. That
combined fix is being built.

## The frozen-market fix, not yet merged

The change is on branch `frozen-markets`. A market with offers and no bids now moves its remembered
price part of the way toward the lowest ask. The first trade after quiet years also moves the
remembered price only part of the way. In Rome (seed 1, 30 years), the limestone markets that traded
within the year went from 4 of 88 to 82 of 88.

Over six spin-up draws:
- Grain volatility, wage and hunger were flat or slightly better.
- Metal volatility worsened:
  - Rome: mean 0.24 → 0.31, worst draw 0.30 → 0.51.
  - Norse: mean 0.10 → 0.22, and one seed reached 1.10.

The remaining limestone cycling traces to merchants bidding in every area at once, for far more than
local supply, at very high price ceilings. That and the Norse case are being traced.

## Pending

The merchant bids and the Norse metal case on top of the frozen-market fix.
