# The capacity screen and the throttle disagree because the screen only keeps the last tag it saw

## What the player saw

At one point the `capacity` response showed a small charcoal surplus, while
the same state/project reporting identified charcoal as the binding material
and showed severe throughput throttling.

## Verified against current code, with the exact mechanism identified

Confirmed - and I traced this past "strongly suspected" to an exact,
reproducible structural bug, on the very material the player named.

`sim/engine/economy_materials.py`'s `MATERIAL_CHECKS` maps `charcoal_kg` and
`firewood_kg` onto the **same** `emp_key` ("charcoal") but **different**
tags (`economy_materials.py:558-572`):

    "charcoal_kg": ("charcoal", "forest1"),
    "firewood_kg": ("charcoal", "forest4"),

`_demand_by_supply_tag()`'s own docstring explains this is deliberate -
charcoal and firewood come off the same forest at different yields per
hectare and are "not simply additive tonne-for-tonne"
(`economy_materials.py:710-751`), so it keeps them as two distinct
`(emp_key, tag)` buckets: `("charcoal", "forest1")` and
`("charcoal", "forest4")`.

`resource_throttle()` (`sim/engine/economy_electricity.py:451-562`) handles
this correctly: it iterates `for emp_key, tag in sorted(all_tags)`, i.e. once
per distinct `(emp_key, tag)` pair, threading a shared, mutated `stock[emp_key]`
across both charcoal-tagged iterations so consumption from either tag
correctly draws down the same pool. This is why the throttle correctly finds
charcoal short when `charcoal_kg` demand is high, even though `firewood_kg`
demand (a different tag, same emp_key) is low.

`_material_capacity_rows()` - the function behind the `capacity` command,
`sim/engine/proto/economy.py:70-112` - does not do the equivalent:

    for (emp_key, tag), need in by_tag.items():
        own = s._own_material_supply(tag)
        market = s._material_market_tonnes(emp_key)
        rows[emp_key] = {
            "material": emp_key,
            ...
            "surplus_t_per_yr": round(own + market - need, 1)}

`rows` is keyed by `emp_key` alone. When both `("charcoal", "forest1")` and
`("charcoal", "forest4")` are present in `by_tag`, the second one processed
**overwrites** `rows["charcoal"]` entirely - the first tag's `own`, `need`
and `surplus` are silently discarded, not merged. Reproduced directly
against the live function, no scenario needed:

    PYTHONPATH=. python3 -c "
    import sys; sys.path.insert(0, 'sim/tests')
    from harness import sim
    s = sim(capital=1_000_000.0)
    demand = {'charcoal_kg': 5000.0, 'firewood_kg': 10.0}
    by_tag = s._demand_by_supply_tag(demand)
    print('by_tag:', dict(by_tag))
    rows = {}
    for (emp_key, tag), need in by_tag.items():
        own = s._own_material_supply(tag)
        market = s._material_market_tonnes(emp_key)
        rows[emp_key] = {'tag': tag, 'own': own, 'market': market, 'need': need,
                          'surplus': own + market - need}
    print(\"capacity-screen row for 'charcoal':\", rows.get('charcoal'))
    "

Output:

    by_tag: {('charcoal', 'forest1'): 5000.0, ('charcoal', 'forest4'): 10.0}
    capacity-screen row for 'charcoal': {'tag': 'forest4', 'own': 0.0, 'market': 1000.0, 'need': 10.0, 'surplus': 990.0}

A genuine 5,000 t/yr industrial charcoal demand (the `forest1` tag) is
entirely invisible on the row the `capacity` command would print: the row
that survives is the `forest4` (firewood) tag's, showing `need: 10.0,
surplus: 990.0` - a comfortable surplus, for a material the throttle is
correctly treating as the year's binding shortage. This is the exact
symptom the player reported, on the exact material they named, and it is
not a timing or stock-vs-flow subtlety - it is a dict key collision that
silently drops one of two demand rows sharing a material name.

Status: **confirmed in current code**, elevated from the player's own
"strongly suspected" - the mechanism is exact, the collision is real in the
current `MATERIAL_CHECKS` table (not a hypothetical one), and both
`charcoal_kg` (58 tree nodes) and `firewood_kg` (6 tree nodes) are live,
used material keys:

    python3 -c "
    import json
    tree = json.load(open('data/tech_tree.json'))['nodes']
    print(sum(1 for n in tree if 'charcoal_kg' in (n.get('mat') or {})),
          sum(1 for n in tree if 'firewood_kg' in (n.get('mat') or {})))
    "
    58 6

## Cross-references

No open complaint names this. Adjacent to `Complaints/09-global-resource-throttle.md`
(closed - a different bug, one shortage throttling unrelated projects
globally) only in subject area; the fix that closed `09` does not touch
this dict-overwrite. Also adjacent to `Complaints/65` (auto-mine ignoring
pending capacity, this same batch) as another instance of `MATERIAL_CHECKS`'s
bucket structure being a recurring source of exactly this shape of bug - the
"iron ore AND iron bar" example already documented in `core_step_phases.py`'s
own auto-mine comment (`887-892`) is the same lesson applied to mining
sizing rather than to this display function.

## What would resolve it

`_material_capacity_rows()` should key its output the same way
`resource_throttle()` internally tracks state: either key `rows` by the full
`(emp_key, tag)` pair and merge same-`emp_key` rows for display (summing
`need`, and being careful that `own`/`market` are not double-counted since
they are already emp_key/tag-scoped correctly), or explicitly aggregate all
tags sharing an `emp_key` into one row the way `resource_throttle()`
aggregates consumption into one shared `stock[emp_key]`. The second is
probably right for a player-facing screen: charcoal should show one row with
total demand (`forest1` + `forest4` demand) against total effective supply,
not two rows nor one row that silently drops the other. This is a pure
display/aggregation bug, unrelated to CLAUDE.md SS3.1/SS3.2.

## The invariant

    displayed annual resource surplus should not simultaneously be an
    unexplained throttle

The player's own ARCH-002 phrasing. Direct regression, using the
reproduction above as the test body: construct demand with two material
keys sharing an `emp_key` but different tags (charcoal_kg/firewood_kg is
the real, already-present case), assert the `capacity` command's row for
that `emp_key` reflects the combined demand of both, and assert its
`surplus_t_per_yr` sign agrees with whether `resource_throttle()` picks
that `emp_key` as `binding` that year.
