# Capability names are stored in the capital field of some nodes

**Status:** open

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
