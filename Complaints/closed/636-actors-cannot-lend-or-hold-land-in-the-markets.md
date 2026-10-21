# A mod's actor cannot lend into the credit market, hold land in the land market, or replace its base civilisation as a partner

**Status:** closed - land holding is 538's

Found building `mods/bh_religion_h5p1` (religious houses that hold land, mill and lend). The complaint behind the mod
(`closed/269`) is that religious bodies competed with the founder for land, labour and credit. The filename stays because
`mods/bh_religion_h5p1/README.md` cites it.

## What the mod cannot do

1. **Lend.** The year's lenders are fixed in `lender_offers` (`sim/engine/economy_capital_market.py`): the savers, the
   state's reserve and each firm's purse. An actor of any other kind, however rich, is never offered to borrowers, so a
   house's purse earns nothing and does not compete with the founder for credit. Without it a house only collects rent
   and pays stipends.
2. **Hold land.** Moved to 538. Land titles, tenancy and a title price exist now (`sim/economy/titles.py`, `land_market.py`);
   what is left is whether any actor kind a mod registers can hold a title and bid for land. CLAUDE.md sections 2 and 4.3
   answer the design question: land holding is one mechanism for every actor, so it goes through the titles of 538 and not
   through a tile transfer (`ModEffects.transfer_tile` hands a whole tile and is not a stand-in). The mod's
   `land_share_of_surplus` and `land_ceiling_hectares` stay labelled stand-ins until then.
3. **Be a variant of a shipped civilisation.** `partner_countries` (`sim/engine/foreign_economies.py`) excludes only the
   exact civilisation id the player plays, so a copy of `han_china_100ad` plays beside the original as a foreign partner
   on the same tiles and the first year raises `NoCountryEconomy` (`sim/agents/country_view.py`). Reproduce: play
   `bh_religion_h5p1:han_monasteries` with the mod's branch. The mod hides that civilisation until this is fixed. Without
   it any "same country, different cast" scenario from a mod is impossible for a civilisation that is also a partner.

## What it would take

* `lender_offers` also offers the purse of every actor whose class sets `lends_from_purse = True` (any mod kind, any
  actor), so its loans and the interest on them run through the existing purse book.
* A civilisation field `variant_of` naming a base civilisation: `partner_countries` skips that base while the variant is
  played.
* Tests: a lending actor's purse is in the offers; a variant is played without its base as a partner (a proof of concept
  had `sim/tests/test_actor_lenders_and_variants.py`).

Tried: branch `engine-actor-lenders` did both bullets; it was never merged (`grep -rn "lends_from_purse\|variant_of" sim`
is empty on main).

## Done

- Lending: `lender_offers` (`sim/engine/economy_capital_market.py`, the place offers are gathered; `sim/economy/credit.py`
  is untouched) also offers the purse and deposit of every actor `ActorRegistry.purse_lenders` returns, those whose class
  sets `lends_from_purse` and that are still in play (`sim/agents/registry.py`). The religion mod's house sets it.
  Tests: `sim/tests/test_actor_lenders.py` (rules on stand-ins), `sim/tests/test_actor_lenders_scenario.py` (a game).
- Variants: a new civilisation file with `variant_of` is that civilisation with the file's fields merged over it
  (`variant_of_base`, `sim/engine/mods_civ.py`; `data.load_civ`), with `append` / `remove_items` for inherited lists; a loop or
  a missing base is an error. `partner_countries` leaves the base out while a variant is played
  (`sim/engine/foreign_economies.py`). The religion mod's three civilisations and the urbanisation mod's tenement
  civilisation are now patches of a few lines, and the Han variant is no longer hidden. Tests:
  `sim/tests/test_mod_civilization_variants.py`, `sim/tests/test_actor_lenders.py` (partners).
- Land holding stays with 538.
