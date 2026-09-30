# `available` gives no net or payback figure, and hides the first-year loss of a new concern

**Status:** open

- `available` shows EARNS/YR and UPKEEP but no net: hom_toothbrush lists EARNS 202.1 and UPKEEP 269.5, so a player choosing by the earnings column picks a loss-maker.
- A newly opened concern pays full upkeep from day one while revenue ramps from a third over three years (`open pwr_peat`: 303 earnings, 270 upkeep), so a marginal concern loses money for years. The `open` reply says "expect less at first"; `available` does not.
- There is no payback sort. Finding that a 1,374 den loom returns +2,493/yr took paging `available` by hand.

What it would take: NET/YR and PAYBACK columns (with the ramp), and `sort:net` / `sort:payback`.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.
