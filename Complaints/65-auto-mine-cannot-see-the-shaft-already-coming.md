# Auto-mine sizes the new shaft against active capacity only, blind to what is already sinking

## What the player saw

A coal shaft had already been commissioned and was due to come online.
Before it visibly contributed output, auto-mine observed the temporary
shortage and commissioned another shaft. The first shaft came online on the
next tick and was already sufficient, leaving redundant capacity.

## Verified against current code

Confirmed, one expression, moved from `core.py` into
`sim/engine/core_step_phases.py:885-914` (the `_step_*` split the
architecture doc describes).

The auto-mine branch:

    elif (self.household.binding in self.MINE_CAPEX_PER_T_YR
            and self.policy.get("auto_mine", not self.manual)):
        dem = self.annual_material_demand()
        keys = tuple(sorted(material for material, (bucket, _tag)
                            in self.MATERIAL_CHECKS.items()
                            if bucket == self.household.binding))
        short = sum(dem.get(material, 0.0) for material in keys)
        want = max(0.0, short - self.mine_capacity.get(self.household.binding, 0.0))
        self.open_mine(self.household.binding, min(want, self.household.capital * 0.25
                                         / max(1.0, self.MINE_CAPEX_PER_T_YR[self.household.binding])))

`want` subtracts only `self.mine_capacity.get(...)` - active, already-commissioned
capacity. It never subtracts `self.household.mine_pending.get(binding, 0.0)`,
the tonnage already sunk into a tranche waiting on `MINE_LEAD_YEARS` (3.0
years, `economy_mining.py:75-84`) to commission.

That `mine_pending` is exactly the right thing to subtract is not a guess -
two other functions in the same file already do it, for the same reason.
`mine_quote()` (`economy_mining.py:662-681`):

    room = max(0.0, ceiling - self.mine_capacity.get(mat, 0.0)
               - self.household.mine_pending.get(mat, 0.0))

and `open_mine()` itself (`economy_mining.py:794-830`), which the auto-mine
branch calls straight into:

    t_per_yr = min(t_per_yr, max(0.0, ceiling - have_cap.get(mat, 0.0)
                                      - self.household.mine_pending.get(mat, 0.0)))

So `open_mine()`'s own *land-ceiling* clamp correctly accounts for pending
tranches - it will not let a mine exceed `mine_land_ceiling()` even counting
what is already sinking. What it cannot do is stop the auto-mine branch from
*asking* for a second tranche in the first place, because the `want` figure
handed to `open_mine()` was already computed against the wrong ceiling (the
demand shortfall, not the land ceiling) and already ignores pending supply.
A shortage that pending capacity is about to cover in full still reads as a
live shortfall to this one `want` calculation, every single year until the
pending tranche actually commissions.

Status: **confirmed in current code** - a direct read of the expression,
no scenario needed. The player's report that this reproduced in actual play
(redundant capacity commissioned the year before the first shaft came
online) is consistent with the code as it stands.

## Cross-references

None of the existing complaints in the index name auto-mine or
`mine_pending` specifically. Worth reading alongside `Complaints/56-a-shaft-that-costs-nothing-to-sink.md`
only in the sense that both are mining-economics findings in the same
module; they are otherwise unrelated (56 is about the sinking-cost
amortisation being too small to matter, not about auto-investment sizing).

## What would resolve it

The player's minimum fix is correct and small - subtract pending capacity
before sizing the new tranche:

    want = max(0.0, short - self.mine_capacity.get(self.household.binding, 0.0)
                          - self.household.mine_pending.get(self.household.binding, 0.0))

The player's further suggestion - weight pending capacity by time-to-completion
when the shortage is severe (a tranche one year from commissioning should
count more toward relieving this year's shortage than one that just started)
- is a reasonable refinement but not necessary for the minimum fix; the
literal subtraction above already stops the specific redundant-shaft case
the player hit, since a pending tranche that fully covers the shortfall
makes `want` exactly zero regardless of how many years remain on it. Nothing
here touches CLAUDE.md SS3.1/SS3.2 - this is auto-investment sizing
arithmetic, not a historical-outcome or hardcoded-value question.

## The invariant

    auto-investment should include active + pending capacity

The player's own ARCH-002 phrasing. Direct regression: construct a `Sim`
with `self.household.binding` set to a material, `mine_pending[binding]`
set to a value that fully covers the current shortfall, and
`mine_capacity[binding]` at zero or partial; call the auto-mine step (or
the relevant `_step_*` phase directly) and assert `open_mine` is not
called, or is called with `t_per_yr == 0`.
