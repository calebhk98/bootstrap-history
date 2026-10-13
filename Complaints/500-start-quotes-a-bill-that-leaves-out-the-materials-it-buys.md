# `start` quotes a bill that leaves out the materials it buys

**Status:** open

`start <id>` prints "the bill you have taken on", and players read it as the price. It is only the
instalments still to pay. The materials the market can deliver that year are bought at start and do not
appear in it. In a Rome game (`play --civ rome_100ad --kit merchant --seed real25`), `start workshop_first`
quoted a bill about a quarter of what `why workshop_first` gives as the total cost, and the `cashbook` for
that year showed the difference as "materials bought for projects". `mat_copper` did the same. In the
playtest this took the founder from comfortable to broke in one year, from a quote that looked affordable.

Where it happens:

- `sim/engine/project_materials.py` `settle_project_materials` buys the deliverable materials and returns
  `project_cost_now - materials_paid`. The amount bought is discarded.
- `sim/engine/projects_starting.py` stores that remainder as `cost_left`.
- `sim/ui/proto/dispatch_ventures.py` prints `cost_left` as `the_bill_you_have_taken_on`. Its `on_credit`
  forecast uses the same partial figure and ignores the materials just drawn from cash.

The affordability check is right: `_money_refusal` compares the full `project_cost` and refuses when the
materials cannot be bought now. Only the report is wrong.

What it would take: return the materials bought from `settle_project_materials`. Then have `start` print
the total (`project_cost_now`), split into materials paid now and instalments still owed, and base the
`on_credit` forecast on both. Add a protocol test that the printed parts sum to the `why` total.
