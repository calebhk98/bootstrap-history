# Year zero's wage clears on a knife edge, and a held opening wage loses hours for decades

**Status:** open - two candidate changes parked as patches; neither merged

Part of Complaint 608 (the opening's labour market clears below the opening wage).

**What is wrong.** On `stationary_setup()` (`sim/economy/fixture_setups.py`), the fixture built to rest, the opening
wage is the stated wage, yet year zero clears well below it, and how far below turns on tenths of a per cent of
labour supply:

- The first year has no remembered ask, so `asks.scale_of` is one and the ask is the bare reservation wage (survival per
  hour). Households' hours sold barely rise with the wage (the plot keeps a fixed share,
  `households_hours_offered.py`), so the supply schedule is nearly vertical down to the reservation. When hours
  offered exceed hours wanted by a sliver, the clearing target falls to where that vertical schedule meets demand, far
  under the opening wage; the reported wage is the mean of seeded contracts (`opening_resting.resting_labour_contracts`)
  and new hires at that low offer (separations put about half the held hours back on the market each year).
- Measured: with demand and supply equal to about one part in a billion the wage clears at about four fifths of the
  opening wage; adding a cost that moves the opening's hours sold per worker by a few tenths of a per cent (the
  working-capital charge below) leaves a sliver of idle hours and the year-zero wage falls to about three fifths, with a
  dip toward a quarter by year three. Measure with `python3 sim/simulator.py spin-up-trace --fixture stationary --years 60`.

**Two changes tried, parked** (patches in `Complaints/reports/`, apply with `git am`):

1. `960-opening-ask-at-contract-wage.patch.txt`: the first year's ask starts at the hours-weighted contract wage over
   the reservation (Eurace's `Household_receive_wage` resets a hired worker's reservation to the wage paid), and
   producers keep their safety stock off the market. Year zero then clears at the opening wage. But with the wage
   held, hired hours fall by about a third over the following decades on the stationary fixture, and the small fixture's
   hiring falls too: the opening sits at revenue equal to cost, the steepest point of `producers.share_working`
   (elasticity about 2.7 at break-even), so a few per cent of price dip in year zero cuts runs twice as much, and a
   wage that does not fall cannot absorb it.
2. `960-working-capital-charge.patch.txt`: runs charge the return on the outlay tied up before the sale (inputs and
   labour times the rate over the cash target's share of a year), in both the year rule (`producers.plan`,
   `share_working`, the shedding margin, the labour-bid ceiling) and the opening (`covering_prices`, `working_share`,
   `opening_runs.unit_costs`). A real cost (Eurace's unit costs include interest), but it does not stop the held-wage
   decline in 1, and on its own it moves year zero onto the low side of the knife edge.

**Why it matters.** Every number a player sees at the opening depends on a sliver of seeded supply (CLAUDE.md 4.2), and
the more realistic sticky first-year wage exposes an opening that has no margin to absorb a price dip.

**What it would take.** A first-year supply schedule that does not fall to survival on a sliver of excess (1 is the
Eurace answer); an opening whose producers are not at the knife edge of their working share (a normal return in the
opening's costs, or seeding whole heads so supply is at least demand, `labour_state.opening_workforce`); then apply
1 and 2 and re-measure the 60-year stationary trace and the small fixture.

## Producers' short-run supply response (branch producer-supply-elasticity)

Opened sources put the short-run supply elasticity of staple output far below what `producers.share_working`'s spread
gives at break-even (`Complaints/reports/research-short-run-supply-elasticity.md`). `producer_supply_spread.py`
derives the spread from a target elasticity, but wiring it in fails: a normal cost spread wide enough for a low
elasticity at the margin gives a fat lower tail, so a producer earning a small share of its cost still runs a large
share of its capacity and the exit and shedding rules stop working. Needed first: a cost distribution steep only near
the margin (thin lower tail), or a closure rule. Measured with the held opening wage (patch 1 above) and the sourced
elasticity together: the decline of hired hours over decades survives, so the producers' curve is not its main cause.

A candidate rule is parked as `Complaints/reports/960-producer-run-share-with-cash-floor.patch.txt`: workplaces' costs
rise from a cash floor (no run below a share of the cash cost) as a power whose exponent gives the sourced elasticity at
break-even. Quick tier green with it, exit and shedding intact, the stationary fixture's hired hours flat. Not merged:
matching a low elasticity at break-even with a hard floor puts a large share of capacity just above the floor (a cliff
at the shutdown price), the stationary wage settles lower than without it, and it is not measured on a civilisation.
