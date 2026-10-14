# Display and wording bugs found in a Rome playtest

**Status:** partly - fixed in `fix-playtest-display-bugs`; still open: `market <material>` filter, quote preview for `sell concern`, the alum `why` item (the 'still on offer to you' units are fixed in `fix-unhired-trade-wage`, see closed 503)

Each of these is small, and each misled or confused a player in a Rome game started from `menu`
(`play --civ rome_100ad --kit merchant --seed real25` reproduces the game).

- **"Still on offer to you" is a market total in the wrong units.** `money` prints it next to a credit limit
  many orders of magnitude smaller. It is `credit_room` (`sim/engine/economy_port_year.py`), which returns
  the whole market's headroom in economy units without the `coin_per_unit` conversion its neighbours apply.
  It even comes out larger than "funds lenders hold". Convert it to coin and label it as the market's
  headroom, or show the founder's own room.
- **"The blame lands on you" is printed on every petition** (`sim/agents/group.py`), whatever the founder's
  share of the cause (`blame_share`, floored by `BLAME_PROTECTION_FLOOR`). Print it only when that share is
  material, and say how much.
- **"the The Roman Empire under Trajan artisans".** `strata_seed.py` builds stratum names from the country
  name, and `sim/agents/group_strata.py` prefixes "the " to them (three places).
- **`leverage` prints raw Python dictionaries** (`figures={'literacy_general': ...}`) from
  `sim/ui/proto/guidance.py` `leverage_points`, with no text renderer.
- **The `path` usage hint names a node that does not exist**, `fud_wheelbarrow` (the node is
  `lnd_wheelbarrow`): `sim/ui/proto/typed.py`, `sim/ui/proto/help.py`. Also, a bare `path` could default to
  the goal.
- **MATERIALS rows always use the mass unit** (`sim/ui/proto/render_screen_why.py`), so `hectare_land`,
  `timber_m3` and `parchment_sheet` print in "lib". For `endowment_land`, land, which no market produces,
  also got "the market and your own output supply this in about" a nine-figure number of years.
- **`market <material>` ignores the material** and prints the whole table. It accepts only paging, so the
  extra word should be refused or used as a filter.
- **No way to preview a sale.** `quote` cannot price `sell concern <id>`, so selling is blind.
- **`quit` prints `bye: True`**, the raw protocol field (`sim/ui/proto/dispatch.py`).
- **The civ menu shows a BC start year as a negative number** after a name that already gives it
  ("Ptolemaic Egypt, 100 BC, -100", from the sample Egypt mod).
- **The supervision note's arithmetic is wrong:** "2.13 craftsmen means ... two of them plus a little over a
  third of a third one's" (`sim/ui/proto/ventures.py`). 0.13 is about an eighth.
- **The `portfolio` money blocker** says "the bill outruns what you can raise" for a small project the
  founder could easily pay, when what held it was the yearly draw rate (`sim/engine/blockers.py`).
- **A shortage names a material `why` cannot explain.** "SHORT OF ALUM_KG" ran every year, including years
  with no project running, and `why alum_kg` answers "unknown node". The throttling itself is 480.

What it would take: one fix each, and a protocol test per item where the output is asserted.

## Fixed

Blame line only when the founder's share is material; the doubled article in stratum group names; `leverage` and
`quit` render as text; the `path` hint names a real node and a bare `path` is the route to the goal; MATERIALS
rows count a non-mass material in its own unit and say a material nobody produces is not produced; the civ menu
writes the year as AD or BC (once); the supervision note's fraction; the portfolio money blocker names the
yearly draw rate as well as the bill (the blocker kind cannot tell which held the project). Tests:
`sim/tests/test_complaint_506_display_bugs.py`.
