# Resource-shortage screens should offer direct remedy actions

The capacity screen was one of the strongest management tools and clearly identified shortages. However, it required the player to manually translate a measured shortage into separate commands to get a quote, inspect projects, or reduce demand.

## Why it matters

When a resource shortage is identified, the player should be able to act immediately from that screen rather than context-switching to separate commands. This reduces friction and makes the most actionable screens even more useful.

## What would resolve it

Make shortage displays actionable with embedded options:

```text
Coal: -493 t/year
Active mines: 3
Pending mines: 2
Market supply: 0

[quote ~500 t/year shaft]
[inspect coal projects]
[reduce demand]
```

The player should not have to manually translate a shortage into a quote or drill down through multiple screens.

## Where it lives

Likely in `sim/engine/proto/render_screens_economy.py` where the capacity screen is rendered, and `sim/engine/proto/dispatch.py` where commands are dispatched.

**Confidence:** Design recommendation
