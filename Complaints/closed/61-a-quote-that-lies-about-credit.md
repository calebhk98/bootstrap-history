# `quote forest` counts credit that `buy forest` will not take

## What the player saw

In the Rome run, `quote forest 100` reported affordability using cash plus
half the credit line, said about 68.6 hectares were affordable, and labelled
this explicitly: `"afford_means": "cash plus half the credit line"`. A later
attempt to buy 55 hectares - well inside that quoted figure - was refused,
because the purchase itself checks cash alone.

## Verified against current code

Confirmed, both sides read directly, unchanged in substance from the
player's report, only moved to different files during the module split.

`_cmd_quote()` moved from `dispatch.py` to `sim/engine/proto/dispatch_money.py:369`.
Its forest branch (`dispatch_money.py:377-392`):

    per = s.FOREST_COST_PER_HA * s.price_index
    return {"ok": True, "what": "forest", "hectares": n_f,
            "to_buy_it": round(per * n_f, 1),
            ...
            "you_could_raise": round(s.spending_power("buy"), 1),
            "you_can_afford_about": round(s.spending_power("buy") / max(per, 1e-9), 1),
            "afford_means": "cash plus half the credit line",
            ...}

`buy_forest()` moved from `economy.py` to `sim/engine/economy_mining.py:1054`:

    def buy_forest(self, ha):
        room = max(0.0, self.forest_land_ceiling() - self.household.forest_ha)
        if ha > room:
            ...
            ha = room
        if ha <= 0:
            return 0.0
        cost = ha * self.FOREST_COST_PER_HA * self.price_index
        if cost > self.household.capital:
            return 0.0
        self.household.capital -= cost
        self.household.forest_ha += ha
        return ha

`self.household.capital` is cash only - `spending_power()`
(`sim/engine/economy_credit.py:900`) is the function that adds
`credit_limit() * SPENDING_DRAW_SHARE_ORDINARY` on top of capital, and
`buy_forest()` never calls it. So the quote is computed from one household
function and the purchase gate from a different, stricter one, exactly the
contradiction the player describes: a player who reads the quote and commits
to a purchase within the quoted figure can still be refused, silently losing
nothing (the refusal is a hard `return 0.0`, not a partial purchase) but
being told something false about what they could do.

Status: **confirmed in current code, unfixed** - the two functions still
disagree on which resource forest purchases draw from.

## Cross-references

No existing complaint names this specific pair. `Complaints/16-finance-affordability-ceilings.md`
(closed) addressed a related but different class of bug - two affordability
ceilings conflicting elsewhere in the engine - and its fix evidently did not
reach `buy_forest`, which was apparently never brought in line with the
`spending_power()` convention `open_venture`, `hire`, `train`, `mine_quote`
and others already use (see `Complaints/58`/`59`/`60`'s neighbours in this
batch for other functions that DO consult `spending_power("buy")`
correctly, e.g. `open_venture` at `projects_ventures.py:307`, `320`). This
should probably be read as one instance of the general pattern
`Complaints/16` already flagged, recurring in a function that pattern's fix
missed, rather than a wholly new class of bug.

## What would resolve it

The player names both directions and both are legitimate design choices, not
a CLAUDE.md SS3.1/SS3.2 conflict either way - this is pure UI/mechanism
consistency, not a historical-outcome question:

1. **Make `buy_forest()` honour credit**, replacing
   `if cost > self.household.capital: return 0.0` with the same
   `spending_power("buy")` gate `open_venture` uses, and drawing the
   overage against credit the way other purchases already do. This is the
   smaller change and matches the quote's own promise.
2. **Make the quote say forests are cash-only**, computing
   `you_could_raise`/`you_can_afford_about`/`afford_means` from
   `self.household.capital` alone for this one branch of `_cmd_quote`.

Either way, the fix is cheap to verify: the player's own suggested
regression - "a quoted affordable amount is actually purchasable under
unchanged state" - is a direct, mechanical test: call `_cmd_quote` for
forest, then call `buy_forest` for the quoted `you_can_afford_about` figure
on the same `Sim` with nothing else changed, and assert the purchase
succeeds in full.

## The invariant

    a quoted affordable purchase should succeed if state is unchanged

This is one of the invariants the player's own document already lists under
ARCH-002, worth stating generically (it likely also covers `quote mine`,
`quote nitre_bed`, `quote slaves` - a quick pass at whether each of those
purchase functions' own gate matches its quote's `afford_means` would be
worth doing alongside a fix here, though only the forest case was
independently checked this session).
