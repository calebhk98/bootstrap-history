# Capability names are stored in the capital field of some nodes

**Status:** closed - 115 capability names moved into `pre` (84 added, 31 were already there), the stray `cap` strings removed; start kits that hold those nodes without the rungs are in 336

About a hundred nodes in `data/branches/50_textiles_consumer_deep.json` and
neighbouring files carry a capability name (for example `"cap_tol_1mm"`) under
the key `cap`, which is the capital field. The old number parser read the
first digit out of the name and used it as capital; the conversion to
`cap_hours` kept that value so behaviour did not change, and each such node
now has `cap_hours` beside the stray `cap` string.

## Why it matters

Their capital is an accident of the capability's name, and the capability
requirement they meant to state is not read as one. Find them with
`python3 -c "import json,glob;print(sum(isinstance(n.get('cap'),str) for f in glob.glob('data/branches/[0-9]*.json') for n in json.load(open(f)) if isinstance(n,dict)))"`.

## What it would take

For each node decide the real capital (from its labour, materials and
equipment) and the real capability prerequisite, move the latter into `pre`,
delete the `cap` string and set `cap_hours` honestly. Owned by the data-fix
work on `data/branches`.

## Done

Every `cap` string named a capability rung (`cap_tol_1mm`, `cap_tol_100um`, `cap_heat_0700`, `cap_heat_1100`, `cap_heat_1300`, `cap_heat_1600`, `cap_vac_1torr`, `cap_power_electric`), the kind `data/branches/CONTRACT.md` says belongs in `pre`. The capital those names had produced by accident (up to tens of thousands of labour hours for a spinning-frame part) is gone: the nodes' own labour and materials are their cost, as for the 46 siblings in the same file. Test: `sim/tests/test_node_capital_field_is_a_number.py`.
