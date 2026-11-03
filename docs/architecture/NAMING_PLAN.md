# Naming plan: the short identifiers

CLAUDE.md section 5 ("Naming") sets the rule: spell names out; `i` and `x`/`y` are the only short names. This
document says how to work down the remaining short names safely. It holds no counts, because they go stale; measure
them with `python3 -m pylint sim/ | grep C0103`, which is the worklist.

## Part A - code identifiers

### A.1 Replacement vocabulary

Where one short name means one thing everywhere, rename it to the word below. Where it varies, read the call site and
choose per site; no tool can choose between `node_id`, `material_id` and `prices` for you.

| name | usual meaning | replacement | consistency |
|---|---|---|---|
| `k` | dict key, usually a node id | `node_id` (tree code), `key` (generic dict loops), `trade_id` or `material_id` for a wage or price table | varies by dict |
| `r` | radius, rate, result | `radius_km`, `rate`, `result` per site | varies |
| `m` | node id, mapping, material id | `node_id`, `weights`, `material` | varies |
| `s` | Sim in handlers, string, Counter, score | `sim` in dispatch and render code; `slug`, `stock`, `score` elsewhere | locally consistent |
| `n` | node | `node` | consistent |
| `t` | trade id, trait name, token | `trade`, `trait`, `token` per site | varies |
| `v` | value in a key/value pair | `value` | consistent |
| `p` | prerequisite id, prices dict, producer id, percentile | `prereq`, `prices`, `producer`, `percentile` per site | varies |
| `c` | count, commodity, cost, descendant id | `count`, `commodity`, `descendant` per site | varies |
| `e` | exponent, exception | `exponent`; keep `as e` for exceptions | idiomatic split |
| `w` | wage, weights table, mine record | `wage`, `weights`, `working` (take care: a few are attributes) | varies |
| `f` | field name, cost factor, file path | `field`, `factor`, `path` per site | varies |
| `a` | argparse namespace, audit dict, alias dict | `args`, `audit`, `aliases` | locally consistent |
| `h` | horizon in years, hours | `horizon_years`, `hours`, never the same word | varies |
| `g` | goal dict, requirement group, accumulator list | `goal`, `group`, `bucket` per site | varies |
| `q` | quantity, quality score, quote | `quantity`, `quality`, `quote` per site | varies |
| `d` | default, accumulator list, demand Counter | `default`, `totals`, `demand` per site | varies |
| `l` | throwaway line string (tests only) | `line` | consistent |
| `_k`, `_y`, `_p` | discarded key, year, prices or pay | `_node_id`, `_year`, `_prices` or `_pay` | consistent except `_p` |

### A.2 Tiers by risk

1. **Safe**: comprehension targets, `except ... as`, function-local assignments, for-targets and `with ... as`, and
   lambda parameters. Each is its own scope, so no caller can observe the name; a scope-aware tool cannot get it wrong.
2. **Care**: function parameters (a keyword call elsewhere can name the parameter, so search every call site first),
   and module-level assignments (an importer can name the global).
3. **Human decision**: any site where the same short name carries two meanings in one function, or where an attribute
   shares the name (`self.w`, `self.gov`).

### A.3 Tooling

- Do not use a regex sweep: a one-letter name matches inside strings, longer identifiers and attribute suffixes.
- Use a concrete-syntax-tree renamer (libcst) scoped to tier 1, one name and one function at a time. It keeps comments
  and formatting, which the stdlib `ast` round trip does not.
- Tier 2 needs its own tool that finds every call site of a function and checks for a keyword argument with the
  parameter's name. Ship it separately from the tier 1 renamer.
- Rename the names whose meaning is already consistent first (`v`, `n`, `l`, `_y`, `_k`); leave the varying names until
  each site has been read.
- Run the quick tier of `python3 -m sim.tests` after each name, not after a batch.

## Part B - data schema fields

The short tech-tree fields (`lab`, `mat`, `ph`, `sch`, `art`, `sus`, `gov`, `conf`, `pre`, `yrs`,
`kb`; `req_any` is already a full word, and `rev_hours` and `up_hours` already carry their unit; the branch files have no `cap` field) are authored in `data/branches/` and merged by `sim/content/tree_merge.py`, so a
rename touches both the branch files and every code read of the key. Measure the read sites with
`grep -rn '"<field>"' sim --include=*.py`.

- Saves store node ids, not node records, so a field rename needs no save change (and CLAUDE.md 4.6 forbids a
  migration shim in any case).
- The player and agent protocol already emits long names (`sim/ui/proto/`), so the visible surface does not change.
- `gov` is both a per-node field and a seat attribute that accumulates it over time; rename them separately.
- Run `python3 sim/simulator.py validate` after each field, not after all of them at once.
