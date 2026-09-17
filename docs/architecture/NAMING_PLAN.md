# Naming plan: the 3,813 short identifiers

This is a plan, not a patch. Nothing in `sim/` was changed to produce it. It
answers three questions: which of the short identifiers CLAUDE.md §7 counts
are safe to rename mechanically, what each name actually means at its real
call sites, and what tool should do the renaming. Part B scopes, but does not
plan, the separate and much harder data-schema problem.

## How this scan was done, and why its numbers differ from CLAUDE.md §7

CLAUDE.md §7 cites an earlier AST scan: **3,813 bindings, 332 distinct names,
83 files**, with `k`=568/53 files, `s`=264, `n`=198, `r`=197. This plan re-scans
`sim/` (83 `.py` files, matching that file count exactly) with a script built
for this task, walking every function/class/lambda/comprehension body and
recording every `Name` node in `Store` context, every `for`-target, `with...as`,
`except...as`, and every function/lambda parameter, for names of length ≤ 2
(excluding `_`). That scan finds **4,972 bindings, 176 distinct names, 72 of 83
files with at least one hit**.

The two scans disagree on the total (4,972 vs 3,813) and on distinct names
(176 vs 332) but **agree exactly on `k`'s file count (53 files)**, and a
second cross-check with Python's own `symtable` module (which counts one
binding per name *per scope* rather than one per occurrence — so a variable
reassigned five times in a loop counts once, not five) gives `k`=523, `n`=172,
`s`=158, `r`=151, a total of 2,704 after discarding `symtable`'s internal
`.0` comprehension-scope artifacts, or 3,759 before discarding them — much
closer to 3,813. The likely explanation is that the earlier scan counted
distinct (name, scope) pairs rather than every rebinding, and used a name
grammar wide enough to catch 332 distinct short tokens against this scan's
176 (real two-letter identifiers this scan may be missing include annotated
assignments and walrus targets in a few edge cases, and it excludes anything
in `data/`, `knowledge/`, or the four `.md` files, none of which were named
in scope here anyway).

**This plan uses the per-occurrence count (4,972) as the basis for tiering**,
because that is what a mechanical AST rename actually has to touch: every
`Store` site is one edit, whether or not it shares a scope with another edit
of the same name. Where CLAUDE.md's number is cited it is marked as such.
The ranking and per-file distribution match closely regardless of which
count is used; nothing below depends on resolving the discrepancy further.

Full per-name and per-file counts are reproducible with the scanner at
`/tmp/claude-0/-home-user-bootstrap-history/8a1c57be-aa95-517c-8bfe-098b63cca651/scratchpad/scan_short_names.py`
(not part of this repo; it is a throwaway analysis script, not a shipped tool
— see Part C for what should actually be built and committed).

---

## PART A — Code identifiers

### A.1 Per-file counts, worst first (72 of 83 files have ≥1)

```
389  sim/engine/cli.py
344  sim/tests/test_round2_policy_hazards_options.py
260  sim/treetool.py
258  sim/engine/economy.py
225  sim/engine/proto/render.py
222  sim/tests/test_scanners_and_scheduling.py
199  sim/engine/proto/dispatch.py
188  sim/engine/projects.py
186  sim/engine/society.py
164  sim/tests/test_early_playtest.py
163  sim/tests/test_round8_fixes.py
141  sim/tests/test_round9.py
138  sim/engine/proto/techtree.py
122  sim/engine/core.py
119  sim/engine/data.py
103  sim/engine/labour.py
 92  sim/planner.py
 88  sim/tests/test_labour_productivity.py
 86  sim/engine/proto/economy.py
 82  sim/build_index.py
 82  sim/tests/test_round10.py
 72  sim/tests/test_people_attrition_scholars.py
 71  sim/tests/test_craftsmen_wording.py
 67  sim/engine/proto/state.py
 65  sim/path_search.py
 61  sim/engine/proto/saveload.py
 59  sim/engine/proto/typed.py
 59  sim/tests/test_round8g_display.py
 59  sim/tests/test_sort_nearest.py
 50  sim/audit_costs.py
 45  sim/engine/commodities.py
 41  sim/engine/fog.py
 39  sim/tests/harness.py
 38  sim/engine/proto/nodes.py
 36  sim/tests/test_allocate.py
 34  sim/perf_fingerprint.py
 32  sim/engine/proto/util.py
 32  sim/tests/test_names_and_fog.py
 31  sim/tests/test_interface_honesty.py
 29  sim/repro_nondeterminism.py
 27  sim/tests/test_reputation.py
 24  sim/engine/settings.py
 23  sim/tests/test_arrears_visibility.py
 23  sim/tests/test_player_log.py
 22  sim/engine/proto/score.py
 22  sim/tests/test_five_things_winner.py
 22  sim/tests/test_mines.py
 21  sim/tests/__main__.py
 21  sim/tests/test_fog_leak3.py
 21  sim/tests/test_literacy_market_pricing.py
 21  sim/tests/test_round12_naive15.py
 20  sim/tests/test_goods_market.py
 17  sim/tests/test_suite_portability.py
 16  sim/tests/test_arrears_hours.py
 14  sim/tests/test_industrial_dashboard.py
 12  sim/engine/geography.py
 10  sim/tests/test_economic_levers_inventory.py
  7  sim/demo_commodities.py
  7  sim/tests/test_complaints_09_16.py
  6  sim/tests/test_complaint_13_specialist_supervision.py
  6  sim/tests/test_dynamic_wages.py
  6  sim/tests/test_parallelism_note.py
  5  sim/tests/test_affordability_warning.py
  4  sim/tests/test_complaints_17_24.py
  4  sim/tests/test_demographics.py
  4  sim/tests/test_hedge_chain.py
  4  sim/tests/test_realism_part02.py
  3  sim/engine/proto/help.py
  3  sim/tests/test_historical_events.py
  2  sim/tests/test_market_saturation.py
  2  sim/tests/test_realism_part05.py
  2  sim/tests/test_tierless_schema.py
```

The 11 files with zero short bindings: `sim/engine/__init__.py`,
`sim/engine/proto/__init__.py`, `sim/engine/proto/ventures.py`,
`sim/engine/protocol.py`, `sim/simulator.py`, `sim/test_regressions.py`,
`sim/tests/__init__.py`, `sim/tests/test_commodities_wired_in.py`,
`sim/tests/test_explicit_starting_techs.py`, `sim/tests/test_realism_part03.py`,
`sim/tests/test_realism_part04.py`. Nearly half the total (about 2,150 of
4,972) sits in five files: `cli.py`, `treetool.py`, `economy.py`, `render.py`,
and one test file.

### A.2 What the top 25 names actually mean

Ranked by occurrence count (files in parentheses). For each: 2–3 real call
sites with `file:line`, and a **CONSISTENT** / **VARIES** verdict — the thing
that decides whether one global rename is possible or every site needs a
human to read it first.

**`k` — 976 bindings, 53 files. Verdict: CONSISTENT (role), varies (referent).**
Always "the current dict key," and in the overwhelming majority of call sites
that dict is the tech tree, so `k` is a node id.
- `sim/engine/proto/dispatch.py:75` — `k = cmd.get("id")`, repeated verbatim
  at lines 119, 235, 518, 644, 912, 1829: the node id named by an incoming
  command.
- `sim/engine/proto/dispatch.py:300` — `n = nodes[k]`: `k` immediately used
  to key into `nodes`.
- `sim/treetool.py:33` — `return set(k for k in p["wage_rates_denarii_per_hour"] if not k.startswith("_"))`:
  here `k` is a *trade name*, not a node id — same role (dict key), different
  referent. This is true throughout: `k` is safe to read as "key of whatever
  dict is in scope," never safe to read as "always a node id" without
  checking the dict.

**`r` — 329 bindings, 33 files. Verdict: VARIES, no safe global rename.**
- `sim/engine/data.py:71` — `r = 6371.0` (Earth's radius, km, inside
  `haversine_km`).
- `sim/engine/economy.py:412` — `r = 0.12` (a base interest rate, in
  `debt_interest_rate`).
- `sim/engine/cli.py:528-529` — `n = len(results)` ... `ok = [r for r in results if r.goal_year]`:
  here `r` is a completed simulation *run/result object*, unrelated to either
  radius or rate.
Three incompatible meanings under one letter; every site must be read.

**`m` — 290 bindings, 31 files. Verdict: VARIES.**
- `sim/engine/cli.py:314` — `for m in dependants.get(k, ())`: `m` is a node id.
- `sim/planner.py:127` — `for m in need: for p in nodes[m]["pre"]:`: `m` is
  also a node id here — consistent with the line above.
- `sim/engine/society.py:16` — `m = dict(self.STATE_WEIGHTS)`: `m` is a fresh
  local mapping, not an id at all.
- `sim/engine/commodities.py:101` — `for m, q in (n.get("mat") or {}).items()`:
  `m` is a *material* id, a third referent.

**`s` — 272 bindings, 35 files. Verdict: locally consistent, globally VARIES.**
Inside `sim/engine/proto/dispatch.py`'s command handlers, every one of the
dispatch functions is literally `def _cmd_x(s, nodes, cmd, ended):` — `s` is
always the running `Sim`. That convention is real and load-bearing across
that file and `typed.py`/`render.py`'s handler functions. Outside it:
- `sim/build_index.py:40` — `s = heading.strip().lower()`: a Markdown-heading
  slug string.
- `sim/engine/economy.py:2684` — `s = getattr(self, "_material_stock_ledger", None)`:
  a `collections.Counter`.
- `sim/treetool.py:366` — `def grade(s): return "A" if s >= 90 else ...`: a
  numeric score.

**`n` — 267 bindings, 35 files. Verdict: mostly CONSISTENT (a node), one
real second meaning at the CLI/protocol boundary.**
- `sim/engine/society.py:14` — `def state_interest(self, n):` ... `n.get("traits", [])`.
- `sim/treetool.py:52-53` — `def normalise_v2(n): for k, v in DEFAULTS.items(): n.setdefault(k, ...)`.
- `sim/engine/proto/techtree.py:536-538` — `for k in ok: g = groups.setdefault(_subject_of(nodes[k]), [])`
  — note `nodes[k]` is fetched fresh rather than reusing a variable called
  `n` here, which is itself a small tell that `n` "means node" strongly
  enough that authors reach for a fresh `nodes[k]` rather than risk `n`
  meaning something else in that scope.
- **But**: `sim/engine/cli.py:528` — `n = len(results)` is a count, not a
  node, and the *JSON protocol* has an actual field named `"n"` (quantity —
  see `sim/engine/proto/dispatch.py:1778`, `n, err = _qty(cmd, "n", 1)`) and
  Python's own `difflib.get_close_matches(q, list(nodes), n=limit, ...)`
  (`sim/engine/proto/nodes.py:175`) takes a keyword argument literally
  called `n`. That stdlib keyword must never be touched by any rename.

**`t` — 211 bindings, 29 files. Verdict: VARIES, "trade" dominant.**
- `sim/engine/cli.py:337` — `for t in n["lab"]: if t not in wages: ...`: a
  trade id.
- `sim/engine/society.py:21` — `sum(m.get(t, 0.0) for t in n.get("traits", []))`:
  a trait name.
- `sim/engine/proto/typed.py:105` — `for w in rest: t = str(w)`: a raw
  command token.

**`v` — 200 bindings, 30 files. Verdict: CONSISTENT.**
The value half of a `(k, v)`/`(key, value)` pair, everywhere sampled:
`sim/audit_costs.py:87` (`for k, v in (...).items()`), `sim/treetool.py:54`
(`for k, v in DEFAULTS.items()`), `sim/engine/settings.py` and others. Safe
to treat as one concept.

**`p` — 166 bindings, 30 files. Verdict: VARIES.**
- `sim/planner.py:118` — `for p in n["pre"] if p in need`: a prerequisite
  node id.
- `sim/treetool.py:32` — `p = json.load(open(os.path.join(DATA, "prices.json")))`:
  the entire prices *file*, a dict, not an id.
- `sim/audit_costs.py:98` — `p = producer_of(key, nodes)`: a producer node id
  (or `None`).
- `sim/engine/cli.py:555` — `q = lambda xs, p: xs[min(len(xs)-1, int(p*len(xs)))]`:
  `p` is a percentile fraction 0–1, a fourth, numeric meaning.

**`x` — 157 bindings, 28 files. Verdict: CONSISTENT role (generic item), but
never actually a coordinate.**
`grep` of `sim/engine/geography.py` (the one file that does real lat/long
math) turns up zero uses of `x` or `y` as coordinates — `haversine_km` uses
`lat1, lat2` spelled out. Every sampled `x` is a generic loop item: a
filename (`sim/engine/data.py:219`), a node id (`sim/path_search.py:366`,
`sim/engine/society.py:2429`), a closure-search stack element. CLAUDE.md
§7's exemption for `x`/`y` "as coordinates" describes an aspiration, not
current usage; there is no coordinate `x`/`y` in this codebase to protect.

**`i` — 141 bindings, 22 files. Verdict: CONSISTENT — leave it.**
Always an `enumerate()` loop index (`sim/engine/core.py:1481`,
`sim/repro_nondeterminism.py:97`, `sim/build_index.py:198`). This is exactly
the one case CLAUDE.md §7 already blesses; no work needed here beyond
confirming it (done).

**`c` — 135 bindings, 23 files. Verdict: VARIES, one of the worst.**
- `sim/audit_costs.py:155` — `c = a["fields_populated"][f]`: a count.
- `sim/engine/commodities.py:80` — `for cid, c in self.commodities.items()`:
  a commodity record dict.
- `sim/path_search.py:418-420` — `order, c, extras, staffing = _planner.backward_plan(...)`:
  an opaque return-tuple element (cost, from context — undocumented at the
  call site, itself a readability problem independent of the short name).
- `sim/treetool.py:287-288` — `stack = [k]; ... c = stack.pop()`: a
  descendant node id during a closure walk.

**`e` — 131 bindings, 18 files. Verdict: two well-established idioms, not
really "VARIES" in the risky sense.**
- `sim/engine/economy.py:166` — `e = 1.0 + 0.055 * diffused` (a diffusion
  exponent; the same shape recurs at `sim/engine/labour.py:2077`,
  `e = 1.85`).
- `sim/treetool.py:113` — `except Exception as e:` — the universal Python
  exception-variable convention.
Recommend leaving `except ... as e` alone (idiomatic, arguably deserves the
same exemption as `i`) and renaming only the exponent uses.

**`w` — 131 bindings, 17 files. Verdict: VARIES, includes a persistent
attribute.**
- `sim/engine/labour.py:855` — `w = WAGES.get(trade)`: a wage rate.
- `sim/engine/society.py:16,27` — `w = self.w`: **`self.w` is itself a short
  object attribute** (the society weights table), not just a local — a
  rename here touches an attribute name, not only a local variable.
- `sim/engine/economy.py:3683` — `for w in getattr(self, "mines", ())`: a
  mine/"workings" record dict.

**`f` — 122 bindings, 19 files. Verdict: VARIES.**
- `sim/audit_costs.py:153-156` — `for f, unit in (("lab", ...), ("mat", ...), ("ph", ...)): c = a["fields_populated"][f]`:
  `f` is a schema-field-name string (see Part B).
- `sim/engine/society.py:1660-1664` — `f = mult(cat); ... f *= mult(t) ** 0.25; return f`:
  a cost multiplier float.
- `sim/build_index.py:50` — `for f in files:` a file path.

**`a` — 101 bindings, 25 files. Verdict: locally consistent, globally VARIES.**
Inside `sim/engine/cli.py`, `a` is the argparse `Namespace` and nothing
else, in every one of `cmd_validate(a)`, `cmd_path(a)`, and roughly two
dozen more `cmd_*(a)` functions (`sim/engine/cli.py:329`, `:432`, and on).
Outside that file:
- `sim/audit_costs.py:146` — `def report(a, show_materials=False): n = a["nodes"]`:
  `a` is the audit-result dict.
- `sim/treetool.py:87` — `a = json.load(open(f)); return a.get("alias", {})`:
  `a` is an alias-map dict.

**`h` — 93 bindings, 23 files. Verdict: VARIES between two units.**
- `sim/engine/cli.py:857`, `:1521` — `h = meta.get("horizon_years")` (an
  integer *years* setting), the identical pattern copy-pasted at both sites.
- `sim/engine/core.py:1933` — `sum(h for _, h in _arrears_hours_lost)` (a
  float *hours* quantity).
Years and hours sharing one letter is the kind of thing that produces a
silent unit-confusion bug if ever conflated; worth flagging even though the
current uses look correct.

**`_k` — 85 bindings, 15 files. Verdict: CONSISTENT — the underscored twin
of `k`.**
- `sim/engine/proto/dispatch.py:1202` — `def _capex_now(_k): _fee = s.venture_capex(_k)`:
  used specifically because an outer `k` already exists in the enclosing
  function and `_k` avoids shadowing it.
- `sim/engine/core.py:1953` — `for _k, _hr, _why in sorted(_directed_hours_unused):`.
Same referent as `k` (an id/key), just scope-shadowed.

**`g` — 61 bindings, 15 files. Verdict: VARIES in shape, not just referent.**
- `sim/engine/data.py:520` — `bad = [g["node"] for g in goals if g.get("node") not in nodes]`:
  a goal record dict.
- `sim/engine/economy.py:2418` — `for g in (self.nodes[k].get("req_any") or []):`:
  a requirement-group dict.
- `sim/engine/proto/techtree.py:538` — `g = groups.setdefault(_subject_of(nodes[k]), []); g.append(k)`:
  **`g` here is a list**, not a dict — a shape change, not just a different
  referent of the same shape.

**`_y` — 56 bindings, 9 files. Verdict: CONSISTENT — a discarded year.**
- `sim/engine/economy.py:3822` — `_y, cost = self.mining_tech(mat)`.
- `sim/engine/fog.py:323` — `for k, _y in (getattr(self, "forgotten", None) or {}).items()`:
  the year a technology was forgotten, unused by the caller. Always "a year
  value, conventionally unused" — the underscore-prefix convention is doing
  real work here and should probably survive as a convention even after the
  letter itself is spelled out (e.g. `_year`).

**`q` — 54 bindings, 12 files. Verdict: VARIES severely, including a shape
change (a function, not a value).**
- `sim/engine/commodities.py:101` — `for m, q in (n.get("mat") or {}).items()`:
  a material quantity.
- `sim/engine/cli.py:555` — `q = lambda xs, p: xs[min(len(xs) - 1, int(p * len(xs)))]`:
  **`q` is bound to a function**, not a value — it computes a percentile.
- `sim/engine/projects.py:1502-1527` — `q = 1.0; for g in groups: ... q *= best`:
  a substitution-quality score accumulator.
- `sim/engine/proto/dispatch.py:823`, `:1781` — `q = s.slave_quote(...)`,
  `q = s.mine_quote(...)`: a price quote.

**`d` — 54 bindings, 14 files. Verdict: VARIES.**
- `sim/treetool.py:44` — `def _num(v, d=0.0):`: a default value.
- `sim/engine/proto/economy.py:472` — `d = families.setdefault(fam, [0.0, 0.0])`:
  a 2-element `[supply, used]` accumulator list.
- `sim/engine/commodities.py:103` — `d[m] += float(q) / span / 1000.0`: a
  per-material demand `Counter`.

**`l` — 52 bindings, 8 files. Verdict: CONSISTENT, and test-only.**
All 52 occurrences are in `sim/tests/`; there are zero production uses. Always
a throwaway per-line string in a comprehension, e.g.
`sim/tests/test_round9.py:674` — `[l for l in _RP("state", _st_sc).splitlines() if "dangerous above" in l]`.
Lower risk than most of this list simply because it never touches engine code.

**`ok` — 42 bindings, 15 files. Verdict: mostly CONSISTENT (a boolean), one
outlier, and arguably a defensible exemption.**
- `sim/engine/core.py:1157` — `ok, _msg = self.train(t, 2)`.
- `sim/engine/labour.py:1883` — `ok, _why = self.commission(best, hours); if ok: return (k, best, hours)`.
Both follow the repo's own `(ok, message)` return-tuple convention used
throughout `core.py`/`labour.py`/`dispatch.py`. The outlier:
`sim/engine/cli.py:529` — `ok = [r for r in results if r.goal_year]` — here
`ok` is a **list** of successful runs, not a bool, immediately followed by
`k = len(ok)`. `ok` is also a real English word, not an abbreviation, so it
may be worth a fourth exemption alongside `i`/`x`/`y` rather than forcing
`success` everywhere — that is a judgement call for whoever approves this
plan, not a technical one.

**`_p` — 38 bindings, 11 files. Verdict: VARIES.**
- `sim/engine/cli.py:1825` — `tree, _p, nodes, _w, _g = load()`: `_p` is the
  *discarded* prices dict from a 5-tuple unpack (note `_w`=wages and
  `_g`=goods are discarded the same way in the same line — three different
  domain objects sharing the underscore-prefix throwaway convention).
- `sim/engine/labour.py:955` — `_p, _l = round(pay), round(lost)`: a rounded
  pay amount.
- `sim/engine/proto/dispatch.py:279` — `for _t, _p in s.trade_draw_plan(k, None).items()`:
  an hours-committed value per trade.

### A.3 Proposed replacement names

Matching the repo's existing style (CLAUDE.md §7 already names the target
vocabulary: `node`, `node_id`, `sim`, `trade`, `material`, `rate`, `key`,
`total`). Where a name VARIES, no single replacement is proposed — the table
says so, and the actual rename has to happen call-site by call-site.

| name | dominant meaning | proposed replacement | consistency |
|---|---|---|---|
| `k` | dict key, usually a node id | `node_id` (tree code), `key` (generic dict loops), `trade_id`/`material_id` where the dict is a wage/price table | varies by dict |
| `r` | radius / rate / result | *(no single name — `radius_km`, `rate`, `result` per site)* | VARIES |
| `m` | node id / mapping / material id | `node_id`, `weights` (society.py's fresh dict), `material` | VARIES |
| `s` | Sim (in engine/proto handlers) / string / Counter / score | `sim` inside dispatch/render/typed; `slug`, `stock`, `score` elsewhere | locally consistent only |
| `n` | node | `node` | mostly CONSISTENT |
| `t` | trade id / trait name / token | `trade`, `trait`, `token` per site | VARIES |
| `v` | value (in a key/value pair) | `value` | CONSISTENT |
| `p` | prerequisite id / prices dict / producer id / percentile | `prereq`, `prices`, `producer`, `percentile` per site | VARIES |
| `x` | generic loop item (never a coordinate in practice) | `item` (or a context word per site: `filename`, `node_id`, `descendant`) | CONSISTENT role |
| `i` | enumerate index | *(keep — already exempt)* | CONSISTENT |
| `c` | count / commodity / cost / descendant id | `count`, `commodity`, `descendant` per site | VARIES |
| `e` | diffusion exponent / exception | `exponent` for the constant; keep `as e` for exceptions | idiomatic split |
| `w` | wage / weights table / mine record | `wage`, `weights` (careful: `self.w` is an attribute), `working` | VARIES, incl. an attribute |
| `f` | field-name string / cost factor / file path | `field`, `factor`, `path` per site | VARIES |
| `a` | argparse Namespace (in cli.py) / audit dict / alias dict | `args` in cli.py; `audit`, `aliases` elsewhere | locally consistent only |
| `h` | horizon (years) / hours | `horizon_years`, `hours` — never the same word | VARIES between units |
| `_k` | shadowed node/venture id | `_node_id` (keep underscore-shadow convention) | CONSISTENT |
| `g` | goal dict / req-group dict / accumulator list | `goal`, `group`, `bucket` per site | VARIES (incl. shape) |
| `_y` | discarded year | `_year` | CONSISTENT |
| `q` | quantity / percentile fn / quality score / quote | `quantity`, `percentile_of` (rename the function itself), `quality`, `quote` | VARIES (incl. shape) |
| `d` | default / accumulator list / demand Counter | `default`, `totals`, `demand` per site | VARIES |
| `l` | throwaway line string (tests only) | `line` | CONSISTENT, test-only |
| `ok` | boolean success flag (one list outlier) | keep `ok` (candidate 4th exemption), or `success` | mostly CONSISTENT |
| `_p` | discarded prices / pay / hours-per-trade | `_prices`, `_pay`, `_hours` per site | VARIES |

### A.4 Tiering by risk

Using the per-occurrence count (4,972), classified from the same AST walk:

| Tier | Definition | Count | Share |
|---|---|---|---|
| **1 — SAFE** | Comprehension targets (always their own scope), `except...as` (always auto-cleared), function-local `assign`/`for-target`/`with-as`, and lambda parameters | **3,599** | **72.4%** |
| **2 — CARE** | Named-function parameters (316), module-level `assign`/`for-target`/`with-as` (1,055), the 2 module-level `def`/`class` names | **1,373** | **27.6%** |
| **3 — RISKY** | See below — a cross-cutting hazard list, not a disjoint bucket; every Tier-3 case is also a Tier-1 or Tier-2 site that needs a human, not the renamer, to decide | *(enumerated, not counted separately — see A.5)* | — |

So **almost three-quarters of the 4,972 is mechanically safe**: purely local
to one function or comprehension, no caller anywhere can observe the name
itself (only the value), and an AST-aware tool cannot get it wrong by
construction. The remaining ~27.6% (module globals, class-scoped params,
function parameters) is not necessarily dangerous, just not push-button — it
needs the caller check in A.5 before a rename, not a full redesign.

Breakdown of the Tier 1 bucket, for calibration:
- comprehension targets: 1,180
- function-local `assign`: 1,776
- function-local `for-target`: 448
- lambda parameters: 151 (incl. `*args`/`**kwargs`-style)
- `with...as` / `except...as` (function-local): 32
- (lambda-scope comprehension/assign, a handful): 12

Breakdown of the Tier 2 bucket:
- function parameters: 316
- module-level `assign`/`for-target`/`with-as` (real globals, not
  comprehension leakage — Python comprehensions have their own scope even at
  module level, so a module-level comprehension target is Tier 1, not
  counted here): 1,055
- module/class-scoped `def`/parameter-of-a-method: rolled into the 316 above
  (107 of the 316 parameters belong to methods, i.e. `scope_kind == "class"`)

### A.5 Specific hazards found

**Found the hard way in round 2, on the six standalone tools. Both make a
rename that is correct in isolation fail `prove_rename_safe.py`, and both
look like the prover is broken. It is not; it is right, and these are real
bytecode changes.**

- **One short name bound twice in one function for two different meanings
  shares one local slot.** Give the two occurrences two different new names
  and that one slot becomes two, shifting every `LOAD_FAST`/`STORE_FAST`
  index after it - so the bytecode is genuinely different even though every
  individual rename reads correctly. Every occurrence of such a name inside
  one function must map to a SINGLE new name, or be left alone. Hit on `q`
  in `treetool.py`'s `cmd_merge`, where it meant a resolved prerequisite id
  in one half and a material quantity in the other. This is the mechanical
  consequence of the thing CLAUDE.md §7 already warns about in the abstract
  (`q` is four different things in four places) - when the four places are
  one function, you cannot fix them separately.

- **CPython orders CELL variables alphabetically, not by first appearance.**
  A local captured by a nested `def`, `lambda` or comprehension body becomes
  a cell variable, and `co_cellvars` is sorted. So a captured local's NEW
  name has to sort into the same position among the other captured names as
  the old one did, or the indices move although only one name changed. Hit
  on `k` in `treetool.py`'s `cmd_repair`: `dict_key` failed and `ident`
  passed, purely because `ident` sorts between `goods` and `node` exactly
  where `k` did.

- **Renaming a local ONTO a name that already exists in the same scope merges
  two slots into one.** The inverse of the first hazard, and it reads as
  correct right up until the prover refuses it. Hit in `proto/render.py`'s
  `render_money`, where the loop key `k` was renamed to `label` and there was
  already a different local called `label`, computed from `k` one line later.
  Renamed to `raw_key` instead. Grep the enclosing function for the new name
  before using it.

- **The cell-variable hazard above was hit independently by two agents in the
  same round**, on different files, both concluding at first that the prover
  was broken. It is not rare and it is not a corner case. `proto/nodes.py`'s
  `_did_you_mean` needed `x` to become `result_id` rather than `node_id`,
  purely so the captured names kept their original alphabetical order.

- **A NEW name that collides with a captured OUTER name turns a read into a
  crash.** Round 3, `cli.py:1751` inside `cmd_sensitivity`'s nested
  `trial()`:

        trimmed_order = [node_id for node_id in order if node_id != drop]

  `order` is a free variable captured from the enclosing function. The
  natural name for the left-hand side was `order`, and using it would have
  made `order` a LOCAL of `trial()`, so the comprehension's own iterable
  `order` becomes an unbound local and the function raises
  `UnboundLocalError`. This one fails loudly rather than silently, which is
  luck rather than design - rearrange the statement and the same mistake
  reads the wrong binding instead. Before giving a local a new name, grep the
  enclosing function for that name, including names it captures from
  further out.

- **A regex renamer cannot tell an identifier from a printf placeholder.**
  `\bs\b -> sim` rewrote `"%s: %s" % (...)` into `"%sim: %sim" % (...)`,
  because `%s` contains an isolated word `s`. Same for `%d`, `%r`, `%f`.
  This repo's engine files are dense with format strings, so a line-based
  rename will hit it. Two defences: rename from `ast.Name` node positions
  rather than by pattern, which never touches literal text at all; and grep
  the diff for `%[a-zA-Z_]{2,}` afterwards regardless.

- **An AST renamer that ignores lexical scope is the other half of the same
  trap.** Renaming every `ast.Name` whose `id` matches, within a line range,
  will also rewrite the name inside a nested `lambda`, comprehension or
  `def` that has its OWN binding of it. Where the nested binding is that
  scope's own local or parameter, the result is harmless but is a PARAMETER
  rename, which `prove_rename_safe.py` reports separately and does not
  cover. Where the nested use is a free variable, it changes which binding
  is read. Resolve each name through a real scope analysis - libcst's
  `ScopeProvider` was used successfully for `proto/` in round 2 - rather
  than matching ids.

- **THE CELL-VARIABLE ORDERING HAZARD BIT THREE OF THE FOUR AGENTS IN ROUND
  3**, on different files, each initially suspecting the prover. In
  `cli.py`'s `_summarise` the captured `ys` could not become `goal_years` or
  `success_years`, because both sort before its cellvar sibling `need` and
  would have shifted every cellvar index; it became `years_reached`, a name
  nobody would pick in isolation. Treat this as the default case for any
  captured local, not as an exception.

- **THE COUNTS IN A.1 OVERSTATE THE RENAMEABLE SURFACE, BY A LOT.** A
  name inventory that does not separate a function-local from a module-level
  binding counts both, and only the first is renameable by this method. A
  module-level assignment compiles to `STORE_NAME`, not `STORE_FAST`, so
  renaming it moves `co_names` on the `<module>` code object and the prover
  refuses it correctly as a global change. Most of this repository's test
  topics are flat scripts - `from .harness import *` followed by top-level
  `check(...)` calls - so most of their short names live at module scope.
  Re-measured across `sim/`:

        Tier-1 locals, inside a def/lambda/comprehension     234
        module-level globals, out of scope for a local sweep 352

  Round 4 hit this repeatedly: `test_literacy_market_pricing.py` was sized at
  19 and had 2 real locals; `test_mines.py` 14 and 6; `test_names_and_fog.py`
  16 and 6. Two agents diagnosed it independently. Size a naming round by
  walking `compile()`'s nested code objects and reading `co_varnames` minus
  parameters, which is exactly what the prover checks, rather than by
  counting identifiers in the source.

- **A NEW NAME CAN COLLIDE WITH A STAR-IMPORTED GLOBAL, and this one nearly
  went into the guidance as advice.** The test topics do `from .harness
  import *`, which brings harness's own `sim(civ=..., capital=...)` FACTORY
  FUNCTION into the module namespace. A nested `def` that does `s = sim(...)`
  therefore cannot rename `s` to `sim`: Python decides locals statically, so
  `sim` becomes a local for the whole function and the right-hand side of
  that very line raises `UnboundLocalError`. This is the captured-outer-name
  hazard again, reached through a star import instead of a closure. Use a
  contextual name - `starved_sim`, `hazard_sim`, `tree_sim` - and grep the
  module's star-imported names before choosing any new name at all.

- **`audit_costs.py`'s `report()` has a second documented shared slot**,
  alongside `treetool.py`'s `q`: `c` is a per-field count in one half of the
  function and the price-confidence dict in the other. Left alone
  deliberately. Recorded so the next reader does not "fix" it.

**A NOTE ON THE FORCED-WORSE-NAME LIST ABOVE.** Round 4 was carried out
against a PINNED copy of the prover from before the slot-split work landed,
so its agents were still constrained by hazards 1 to 4. The prover now
proves slot splits, cellvar reorders, comprehension-scope renames and nested
`def` renames. Every name in that list is worth re-attempting - among them
`q` in `cmd_merge`, `ys` in `_summarise`, `m` in `materials_report`, `a` in
`_room_advice`, and `yr` in `_plague_line2`, which wanted `hazard_year` and
got `years_started` because its cellvar siblings are parameters.

**WORTH BUILDING NEXT, from round 4's own evidence:** a mode that answers
"is this target a cellvar, and what are its alphabetical neighbours" BEFORE
a rename is attempted. Every cellvar case in three rounds was found by
trial and error through `--check-params`, and the information needed to
pick a safe name the first time is sitting in `co_cellvars`.

  The cheap pre-check that avoids both: before renaming a local, ask whether
  it is referenced inside a nested `def`/`lambda`/comprehension body. Being a
  comprehension's outermost iterable does NOT force capture. Round 2's other
  five files were analysed that way up front and proved clean on the first
  attempt; the two that were not took several passes each.

- **A real `getattr`/`setattr` check came back clean.** Grepped for
  `getattr(self, <1-2 char var>)` / `setattr(self, <1-2 char var>, ...)`
  across `sim/`: zero hits. No short *code* identifier is used as a dynamic
  attribute-name argument anywhere. This means the AST rename does not have
  to worry about a string secretly meaning the same thing as one of these
  variables — Part B's schema fields are a different story (see below).
- **`SAVE_FIELDS` (`sim/engine/proto/saveload.py`) has zero entries ≤ 2
  characters** — checked programmatically against all 100 entries. No save
  field is a short code identifier. (`"gov"` is 3 characters and is a
  cross-cutting Part B hazard — see B.3.)
- **`KNOWN_COMMANDS` (`sim/engine/proto/dispatch.py:30`) has zero entries ≤ 2
  characters.** No protocol command token is a short name.
- **The JSON protocol does have a short field, and it collides with `n`'s
  dominant code meaning.** `sim/engine/proto/util.py`'s `_qty(cmd, "n", ...)`
  reads a literal `"n"` key out of incoming commands (quantity), used at
  `sim/engine/proto/dispatch.py:697,846,1592,1614,1635,1730,1746,1764,1778`.
  An AST-based rename of the *variable* `n` never touches this string literal
  (it's a `Constant`, not a `Name`), so it is not a code-rename risk — but it
  is a **documentation/reasoning hazard**: a reader who has just internalised
  "`n` means node" will misread `_qty(cmd, "n", 1)` unless they know the
  protocol field and the Python variable are unrelated.
- **A confirmed keyword-argument hazard.** `sim/engine/proto/nodes.py:162` —
  `def _did_you_mean(k, nodes, limit=8, s=None):` — is called with an
  explicit keyword at three sites: `sim/engine/proto/dispatch.py:95`,
  `:1835`, `:2546`, all `_did_you_mean(k, nodes, s=s)`. Renaming this `s`
  parameter is Tier 2 exactly because of this: any AST tool must find and
  rewrite the keyword at all three call sites, not just the `def`. A plain
  per-file rename would miss two of the three (`dispatch.py` has both the
  parameter's own definition-adjacent uses and, separately, these
  keyword-call sites, but a naive tool scoped to one function body would not
  see them).
- **A stdlib keyword must never be touched.** `sim/engine/proto/nodes.py:175`
  — `difflib.get_close_matches(q, list(nodes), n=limit, cutoff=0.6)` — the
  `n=` here is `difflib`'s own parameter name, not this codebase's. Any
  rename tool that matches on "keyword argument named n" without checking
  the callee is a stdlib function will corrupt this line.
- **A short name that is also a persistent object attribute.**
  `sim/engine/society.py:16,27` — `w = self.w` — `self.w` (the society
  weights table) is itself a two-character attribute, not just a local.
  Renaming the local `w` is Tier 1; renaming `self.w` is a different,
  Tier-2-or-3 exercise (an attribute is part of the object's implicit
  interface — check for `.w` reads anywhere `self` isn't the receiver, e.g.
  on a passed-in `Sim`, before touching it).
- **Two units sharing one letter.** `h` means *years* in
  `sim/engine/cli.py:857,1521` (`h = meta.get("horizon_years")`) and *hours*
  in `sim/engine/core.py:1933` (`sum(h for _, h in _arrears_hours_lost)`).
  Not currently a bug, but exactly the kind of collision a rename should
  eliminate rather than reproduce with longer names that still collide.

---

## PART B — Data schema fields (scope only, not a plan)

CLAUDE.md §7 lists the short tech-tree schema fields: `lab`, `mat`, `cap`,
`rev`, `up`, `ph`, `sch`, `art`, `sus`, `gov`, `conf`, `pre`, `yrs`, `kb`
(plus `req_any`, already a full word). This is a data migration, not a
refactor, and is scoped here, not planned.

### B.1 Where each field lives, and how big it is

`data/tech_tree.json` has **2,864 nodes**, and **every single one carries all
15 fields** (verified: `lab`=2864, `mat`=2864, `cap`=2864, `rev`=2864,
`up`=2864, `ph`=2864, `sch`=2864, `art`=2864, `sus`=2864, `gov`=2864,
`conf`=2864, `pre`=2864, `yrs`=2864, `kb`=2864, `req_any`=2864). That figure
matches CLAUDE.md's "2,864 nodes" exactly.

The tree is not hand-edited as one file: `data/branches/` holds **41** JSON
source files (11 to 115 node records each) that `sim/treetool.py`'s `merge`
command combines into `tech_tree.json`. Any field rename has to happen in
both places, or in the merge step, not just in the merged output.

Read-site counts (`grep -rn '"<field>"' sim --include=*.py`, so string-key
reads/writes, not just the field's own definition):

| field | occurrences in sim/*.py | top files |
|---|---|---|
| `pre` | 179 | test_round2_policy_hazards_options.py (23), test_reputation.py (20), treetool.py (18), test_scanners_and_scheduling.py (18) |
| `rev` | 130 | projects.py (22), economy.py (19), test_round8_fixes.py (11) |
| `up` | 92 | projects.py (21), economy.py (14), test_round8_fixes.py (7) |
| `ph` | 87 | test_people_attrition_scholars.py (9), cli.py (8), techtree.py (7), projects.py (7) |
| `yrs` | 84 | projects.py (15), test_scanners_and_scheduling.py (10), test_people_attrition_scholars.py (9) |
| `lab` | 67 | test_scanners_and_scheduling.py (10), projects.py (9), core.py (8) |
| `mat` | 36 | treetool.py (7), economy.py (7), audit_costs.py (5) |
| `art` | 21 | techtree.py (8), test_round8_fixes.py (3), projects.py (3) |
| `sch` | 20 | techtree.py (8), projects.py (3) |
| `kb` | 15 | treetool.py (7), techtree.py (4), build_index.py (3) |
| `cap` | 13 | treetool.py (5), cli.py (3) |
| `conf` | 12 | treetool.py (4), cli.py (4) |
| `gov` | 11 | cli.py (5), treetool.py (3) |
| `sus` | 8 | treetool.py (3), cli.py (3) |

(`req_any`: 29 occurrences — already a full word, listed for completeness
since it travels with this group semantically.)

### B.2 Save files and the protocol: mostly already insulated

- **Save files do not duplicate the schema.** `sim/engine/proto/saveload.py`'s
  `SAVE_FIELDS` never includes `nodes` or any per-node blob — a save stores
  node **ids** (in `done`, `granted`, `active`, etc.), not node records. A
  save file therefore does not need its own migration for a schema-field
  rename; it only needs the renamed code to still resolve the same ids
  against the newly-shaped tree at load time.
- **The outward-facing JSON protocol already translates most of these to
  readable names.** Checked every dict-literal construction in
  `sim/engine/proto/*.py` for a raw short key (`{"ph": ...}`-shaped
  literals): none found. What's actually sent to a player/agent renames on
  the way out — e.g. `sim/engine/proto/state.py:336`:
  `"founder_hours_total": n["ph"]`, and `sim/engine/proto/techtree.py:298-302`:
  `"hours": lambda s, n, k: n[k]["ph"]`, `"earns": ... n[k]["rev"]`,
  `"upkeep": ... n[k]["up"]`. The short keys are read from `n[...]`
  internally and re-emitted under long names. This means **the compatibility
  shim's job is narrower than "rewrite the wire protocol"** — it is
  "rewrite `data/tech_tree.json` (and `data/branches/*.json`) and every
  internal `n["ph"]`-style read," while the player/agent-visible surface
  mostly does not need to change at all.
- **One real cross-artifact collision.** `"gov"` is both the per-node schema
  field (a trait score baked into each tech, e.g.
  `sim/engine/proto/techtree.py:945` —
  `"state_interest_trait_score": n.get("gov", 0)`) **and** a `Sim` instance
  attribute of the same name that accumulates it over time
  (`sim/engine/core.py:253` — `self.gov = 0.0`;
  `sim/engine/projects.py:2568` — `self.gov += self.state_interest(n)`) which
  **is** in `SAVE_FIELDS` (`sim/engine/proto/saveload.py:58`). These are
  related but distinct things (a per-tech constant vs. a running total) that
  happen to share a name. A migration must rename them independently and
  must not assume "rename `gov` everywhere" is one operation — it's at least
  two: the JSON field, and the unrelated (but confusingly-matching) save
  field / attribute.

### B.3 Rough size of a compatibility shim

Not designed here — only bounded. A shim would need to:
1. Accept both old and new field names when loading `data/tech_tree.json`
   and each of the 41 `data/branches/*.json` files (or run the rename once,
   as a `treetool.py` migration command, and require regeneration —
   `treetool.py merge` already exists as the choke point all 41 files pass
   through).
2. Update every one of the ~13 files in the read-site table above that does
   `n["<short field>"]` or `n.get("<short field>", ...)`, on the order of
   **700–750 individual read/write sites** (summing the table; `pre` alone is
   179).
3. Decide, separately, what happens to `self.gov` (B.2) — this is not a
   schema-field rename at all, it's an unrelated attribute that happens to
   share the string.
4. Re-run `python3 sim/simulator.py validate` and the full
   `sim/test_regressions.py` suite (~68s) after each field, not all 14 at
   once — the tests assert on structure derived from these fields (e.g.
   `test_tierless_schema.py`), so a batched rename that breaks one field
   would be hard to attribute.

This is consistent with CLAUDE.md §7's own instruction: "Do not start it
casually." Nothing above is a green light to start; it is the measurement
that instruction asked for before anyone tries.

---

## PART C — Tooling

### C.1 What's installed

Checked in this environment:
```
$ python3 -c "import libcst"   -> ModuleNotFoundError
$ python3 -c "import rope"     -> ModuleNotFoundError
$ python3 -c "import bowler"   -> ModuleNotFoundError
$ pip install --dry-run libcst -> would install libcst-1.9.0 (resolves fine, network reachable)
```
**None of libcst, rope, or bowler are installed**, but `pip install libcst`
resolves immediately from this network, so it is one command away. Python
3.11's stdlib `ast` module is present and has `ast.unparse()`, which can
*technically* parse and regenerate Python — but `ast` throws away comments
and original formatting on round-trip, and CLAUDE.md §6 is explicit that
"five of eight engine files are majority comment" and that stripping them
"to clean up" is against the working agreement. **A stdlib-`ast`-based
rewriter is disqualified for this codebase specifically, not in general** —
it would silently delete the majority of several files' content on save.

### C.2 Recommendation

1. **Do not use a regex sweep.** A single-letter identifier like `k`, `n`,
   `s`, or `a` matches constantly as a substring, a string-literal fragment
   (e.g. inside `"%s: unpriced material %s"`), an attribute suffix, or an
   unrelated token, and this file's own findings (A.2) show that even the
   *AST-visible* meaning of these names varies within a single file. A
   regex tool cannot tell `k` the dict-key loop variable from `k` inside a
   string, from `_k`, from `k` as part of a longer identifier without
   word-boundary logic that then still can't tell "this `k` means node id"
   from "this `k` means trade id" — which matters for choosing the
   replacement word, not just for finding the site.
2. **Install `libcst`** (`pip install libcst`) and write a small,
   purpose-built renamer against it, scoped only to Tier 1 (A.4): comprehension
   targets, function-local assignments/for-targets/with-targets, and lambda
   parameters, one name at a time, one function at a time. `libcst` is the
   right choice over stdlib `ast` specifically because it is a *concrete*
   syntax tree — it preserves comments, whitespace, and formatting exactly,
   which this repo's own working agreement requires. It also preserves scope
   information well enough to guarantee a Tier-1 rename never touches a
   same-named binding in a different function (the actual safety property
   Tier 1 is claiming).
3. **Do not attempt Tier 2 or Tier 3 with the same blanket tool.** Tier 2
   (function parameters, module globals) needs a caller-site search per name
   per function — `_did_you_mean`'s `s=s` keyword call (A.5) is exactly the
   case a Tier-1-only tool would miss if scope-creep let it touch parameters
   too. A second, smaller pass — "find every call site of this specific
   function, check for a keyword argument matching this specific parameter
   name" — is a reasonable follow-up tool, but it is a different, riskier
   tool and should ship separately with its own review, not be bundled into
   the Tier-1 renamer's first version.
4. **Rope** and **bowler** were considered and are not recommended: `rope`
   is IDE-refactoring-oriented and heavier to script headlessly for a
   one-shot batch job across 83 files; `bowler` (built on `lib2to3`, not
   maintained past Python 3.8's grammar in its released form) risks
   mis-parsing newer syntax this codebase may use (walrus operator, match
   statements, etc.) that `libcst` tracks against current CPython grammars.
   Neither offers anything `libcst` doesn't for this specific job.
5. **Sequence:** rename one name at a time (e.g. all Tier-1 `i`-adjacent...
   no — start with names that are already CONSISTENT in meaning, since those
   are the ones where "what do I rename it to" is not itself a research
   question: `v`→`value`, `_y`→`_year`, `_k`→`_node_id`, `l`→`line` (test-only),
   `i` stays. Defer `r`, `c`, `q`, `g`, `d`, `p`, `t`, `m`, `w`, `f`, `h` — the
   VARIES names — until each has been read site-by-site and given a per-site
   name, since no tool can choose "node_id" vs "material_id" vs "prices" for
   you. Run `python3 sim/test_regressions.py` after each name, not after a
   batch, matching CLAUDE.md's own instruction to re-measure rather than
   assume.
