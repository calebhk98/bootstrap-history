# `available sort earns` is silently ignored; only `sort:earns` works

**Status:** open

`available sort earns limit 25` returns rows in id order with EARNS/YR 0 at the top; the real earners (tex_hand_ginning, pwr_peat) are not on page one. `available sort:earns reverse` (the colon form from `help commands`) sorts correctly.

The hint printed under the `available` table itself says "add a 'sort' of price, hours, years, earns ...", which reads as the space form. So a new player following the on-screen hint gets an unsorted list with no refusal.

What it would take: accept `sort <key>` the way `sort:<key>` is accepted, or refuse an unknown word instead of ignoring it.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.
