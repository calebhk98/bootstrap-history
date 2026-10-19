# A mod's actor cannot lend into the credit market, hold land in the land market, or replace its base civilisation as a partner

**Status:** open

Found building `mods/bh_religion_h5p1` (religious houses that hold land, mill and lend). Three things a mod
actor or mod civilisation needs had no hook; the mod does what it can without them.

## What the mod could not do

1. **Lend.** The year's lenders are fixed in `sim/engine/economy_capital_market.py:64-72` (`lender_offers`): the
   savers, the state's reserve and each firm's purse. An actor of any other kind, however rich, is never offered to
   borrowers, so a house's purse earns nothing and does not compete with the founder for credit.
2. **Hold land.** The land market has rents per tile (`sim/economy/api.py:81-99`) and no owners:
   `land_rent_per_hectare` is a mean, and the church's `endowment_hectares` (`sim/agents/foundation.py:56`) is only
   a number multiplied by it. Land a house buys does not leave the supply the founder or a firm can rent or buy.
   Not built as a proof of concept: it needs ownership in the land model (`sim/world/land.py`), a design decision
   beyond a hook.
3. **Be a variant of a shipped civilisation.** `partner_countries` (`sim/engine/foreign_economies.py:67-73`)
   excludes only the exact civilisation id the player plays, so a copy of `han_china_100ad` plays beside the
   original as a foreign partner on the same tiles and the first year raises `NoCountryEconomy`
   (`sim/agents/country_view.py:90`). Reproduce: play `bh_religion_h5p1:han_monasteries` with the mod's branch.
   The mod hides that civilisation until this is fixed.

## Why it matters

The complaint behind the mod (`closed/269`) is that religious bodies competed with the founder for land, labour and
credit. Without 1 and 2 they only collect rent and pay stipends; without 3 any "same country, different cast"
scenario from a mod is impossible for a civilisation that is also a partner.

## Proof of concept: branch `engine-actor-lenders`

Not pushed or merged. It adds, with tests (`sim/tests/test_actor_lenders_and_variants.py`):

* `lender_offers` also offers the purse of every actor whose class sets `lends_from_purse = True` (any mod kind,
  any actor), so its loans and the interest on them run through the existing purse book;
* a civilisation field `variant_of` naming a base civilisation: `partner_countries` skips that base while the
  variant is played.

Item 2 (land owners in the land market) is the open part.
