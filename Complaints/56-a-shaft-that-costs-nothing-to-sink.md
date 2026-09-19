# A shaft that costs nothing to sink

`sim/world/deposits.py` has a SINKING COST mechanism, described at length in
its own module docstring as the thing that makes a poor deposit uneconomic at
low demand and economic at high demand. A one-time cost for the shaft,
timbering, hoist frame or aqueduct, amortised over the deposit's whole
assumed lifetime output, and therefore cheaper per kilogram the larger the
deposit is. `total_cost_labour_hours_per_kg` is the sum of the recurring
extraction cost and this amortised fixed cost, and it is what `supply_curve`
and `find_marginal_deposit` sort and price by.

**Measured, the fixed cost is at most 0.341% of a deposit's total cost, and
for five of the six metals at most 0.011%.**

    cd /home/user/bootstrap-history && PYTHONPATH=. python3 - <<'PY'
    from sim.world import deposits
    for metal in ("copper", "silver", "gold", "iron", "tin", "lead"):
        pool = deposits.load_deposits(metal)
        worst, worst_name = 0.0, None
        for dep in pool:
            total = deposits.total_cost_labour_hours_per_kg(dep)
            amort = deposits.amortized_sinking_cost_labour_hours_per_kg(dep)
            share = (amort / total) if total else 0.0
            if share > worst:
                worst, worst_name = share, dep.name
        stable = ([p.deposit.name for p in deposits.supply_curve(pool, 150.0)]
                  == [p.deposit.name for p in deposits.supply_curve(pool, 3.0)])
        print("%-8s n=%3d  max sinking share %6.3f%% (%s)  order stable 150y vs 3y: %s"
              % (metal, len(pool), 100 * worst, worst_name, stable))
    PY

    copper   n=  7  max sinking share  0.011% (italia_copper_generic)  order stable 150y vs 3y: True
    silver   n=  4  max sinking share  0.008% (italia_silver_generic)  order stable 150y vs 3y: True
    gold     n=  2  max sinking share  0.341% (las_medulas_alluvial)   order stable 150y vs 3y: True
    iron     n=  7  max sinking share  0.008% (levant_iron_generic)    order stable 150y vs 3y: True
    tin      n=  3  max sinking share  0.000% (None)                   order stable 150y vs 3y: True
    lead     n=  5  max sinking share  0.005% (laurion_lead)           order stable 150y vs 3y: True

The mechanism cannot flip a marginal deposit at those magnitudes. Cutting the
assumed working life by a factor of fifty, from 150 years to 3, multiplies
every amortised figure by fifty and still reorders no supply curve for any
metal. The docstring's claim about what the sinking cost achieves is
therefore not true of the numbers as they stand.

## Why it comes out that small, which is arithmetic rather than opinion

`SHAFT_SINKING_HOURS_SHALLOW_VEIN` is 2,000 labour-hours, one time, for the
whole works. It is divided by the deposit's assumed total lifetime output:

    total_reserve_kg = quantity_tonnes_per_year * working_life_years * 1000

`DEPOSIT_ASSUMED_WORKING_LIFE_YEARS` is 150. A deposit producing 1,000 tonnes
a year therefore has an assumed reserve of 150,000,000 kg, and 2,000 hours
spread over that is 0.000013 h/kg, against extraction costs in the range
0.1 to 0.6 h/kg seen above. Five orders of magnitude apart.

So there is no coding error to point at. The mechanism is wired up correctly
and the ratio between a one-time works cost and a century and a half of
output is simply what it is. What is wrong is the gap between that and the
docstring, which invites a reader to believe a lever exists that does not
move anything.

## The second finding, which is what led to the first

`working_life_years` is a parameter on seven public functions, defaulting to
`None` and resolved to `DEPOSIT_ASSUMED_WORKING_LIFE_YEARS` in two separate
places:

    amortized_sinking_cost_labour_hours_per_kg(deposit, working_life_years=None)
    total_cost_labour_hours_per_kg(deposit, working_life_years=None)
    supply_curve(deposits, working_life_years=None)
    find_marginal_deposit(deposits, quantity, working_life_years=None)
    init_deposit_states(deposits, working_life_years=None)
    simulate_depletion(deposits, quantity, years, working_life_years=None)
    load_deposits(geography=None, resources=None, deposits_data=None)

**No production code ever passes it.** Every caller outside the module is a
test:

    grep -rn "working_life_years" --include=*.py sim/ tools/ | grep -v "^sim/world/deposits.py"
    sim/tests/test_deposits.py:276, :303, :322, :325, :330, :516

Seven functions carry a sentinel-defaulted parameter through their
signatures so that one test file can build small scenarios. That alone is
only a smell. The part that is a hazard is what the number means at the two
places it is resolved, because they are not the same thing:

  - In `amortized_sinking_cost_labour_hours_per_kg` it is an **amortisation
    horizon**: the period over which a fixed cost is spread. That is an
    accounting choice.
  - In `init_deposit_states` it sets the deposit's **physical reserve**:
    `quantity_tonnes_per_year * working_life_years`. That is a geological
    stock.

`DEPOSIT_ASSUMED_WORKING_LIFE_YEARS`'s own `why` says it was written for the
second of those, and says so in terms that exclude the first: "It exists
purely so `simulate_depletion()` has a stock that actually runs out in a
demonstrable number of years." The amortisation site borrows it silently, and
`amortized_sinking_cost_labour_hours_per_kg`'s docstring acknowledges the
borrowing ("the same reserve figure DepositState's own initial reserve uses")
without defending it.

The consequence is invisible today only because of the first finding. A test
that passes `working_life_years=3.0` to `simulate_depletion` intends "make
this deposit run out quickly", and also, silently, multiplies every
shaft-bearing deposit's amortised cost by fifty. If the sinking cost were
large enough to matter, that would change which deposit is marginal, which is
the quantity those tests measure. Two physically distinct concepts share one
knob, and the knob is currently too weak for anyone to notice.

## What would resolve this

Not obvious, and deliberately not decided here. Three candidates, in
increasing order of ambition:

1. **Correct the docstring.** Cheapest, and honest. State that the sinking
   cost is presently negligible against extraction cost at these reserve
   assumptions, with the measurement above. Nothing else changes.
2. **Split the two meanings.** Give the amortisation horizon its own declared
   name and let the reserve keep `DEPOSIT_ASSUMED_WORKING_LIFE_YEARS`. This
   is correct regardless of the magnitudes, and it removes the trap without
   asserting anything new about the world.
3. **Ask whether the reserve assumption is the real problem.** A 150-year
   reserve at full annual output is what makes the fixed cost vanish. The
   declaration itself says this is not a geological reserve estimate and that
   the physically correct number would come from a surveyed ore-body volume
   times its grade, which this project has for none of these deposits. If the
   sinking cost is supposed to bite, the reserve figure is where to look, and
   that is a data question, not a code one. CLAUDE.md §3.1 would want the
   answer to come from ore-body volume rather than from tuning the number
   until the mechanism becomes visible.

Filed rather than fixed because 2 is a change to a public signature and 3 is
a modelling decision.

## Where the sentinel came from

Nowhere suspicious. It is the ordinary result of a module written to be
standalone and testable: a parameter added so a test can construct a small
world, defaulted so production callers need not care. The lesson is narrower
than "sentinel defaults are bad". It is that a test-only parameter threaded
through seven signatures stops being a test affordance the moment two
different quantities are reachable through it, and nobody reviewing any one
of those seven functions can see the collision from inside that function.
