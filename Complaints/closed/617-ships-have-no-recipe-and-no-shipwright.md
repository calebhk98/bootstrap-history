# Ships have no recipe and no shipwright: they are a state budget line paying carpenters and sailors

**Status:** closed

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming).

Blocks 629 (vessels as carrier capital).

**What is wrong.** Ships are a state budget line paying `carpenter` and `sailor` hours; there is no ship good.

**Evidence.** `sim/agents/budget_lines.py`.

**Why it matters.** A ship is an object with maintenance (CLAUDE.md 4.3) and the carriage chain needs it (552).

**What it would take.** A shipwright trade and ship goods with recipes and sourced service lives; the state's ship line buys ships rather than hours.

**Test.** `validate` passes; a test: the state's ship line draws shipwright hours and produces ships.

**Resolution.** Counted merchant hulls and warships have recipes, source notes,
service lives and shipwright labour. The navy bids for missing hulls through
the market and staffs their declared operating crew. Delivered hulls remain
in the state's asset account and wear through the economy's durable-stock
mechanism; only filled orders add stock. Repair and refit remain folded into
replacement wear until carrier-capital maintenance is separated in 629.
`python3 -m sim.tests --only ship_purchases` checks the bid-to-shipyard value
chain, shipwright hiring, delivered stock, wear, conservation and save/load.
See `sim/agents/NAVY.md` for the data fields and mechanism.
