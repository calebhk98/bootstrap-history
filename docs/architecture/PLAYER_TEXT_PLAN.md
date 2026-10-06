# Player text plan: the engine returns facts, sim/ui writes the words

Plan for Complaint 362 (and the text half of Complaint 285). Owner decision (2026-10-06): everything
that prints belongs in `sim/ui/`. The engine returns a structured result, a reason code plus its
quantities each tagged with a dimension, and `sim/ui` renders it in the player's language and units.
This document changes no code. Counts are measured by the command in section 1 and the appendix, on
the date shown; re-measure before acting on them (CLAUDE.md section 6).

## 1. Inventory

### How it was measured

The scanner in the appendix walks every `.py` file under `sim/` except `sim/ui/`, `sim/tests/` and
`sim/geography/layer_build/` with `ast`. It reports a string expression that looks like a sentence
(at least two words, or three for a fixed one) when it sits in one of these places:

| Sink | Meaning |
|---|---|
| `return` | a refusal or reason returned to a caller, often `return False, "..."` |
| `append` | a log or event line (`household.log.append((year, text))`, `lines.append(...)`) |
| `dict_field` | a dict value under `note`, `error`, `message`, `reason`, `warning`, `advice`, `text`, `why`, `hint`, `line`, `detail`, `meaning` |
| `assigned` | assigned to a name containing reason, note, message, text, why, warning, advice, hint, line, detail |
| `keyword` | a keyword argument of those names |
| `print` | `print(...)` outside the UI |
| `other` | any other `f"..."`, `"..." % x`, `"..." + x`, `"...".format(x)` |

"built" means the string interpolates something (f-string, `%`, `.format`, concatenation); "fixed"
means a plain sentence. Fixed sentences are only counted in the sinks above (docstrings, raised
developer errors, and the long rationale strings of parameter declarations are skipped).

Command (the appendix holds the source; the proposed home is `sim/tests/player_text_scan.py`):

```
python3 player_text_scan.py sim            # table by module
python3 player_text_scan.py sim --files    # one line per hit: file:line, sink, kind, template
```

Precision is heuristic. It over-counts (a `__repr__`, a generated constant id such as
`DEPOSIT_GRADE_%s`, a note on a declared parameter) and under-counts (a sentence assembled from a
helper's return value, a string reaching the player through a data file). Treat the totals as the size
of the job to within a factor of about two, and the per-file ranking as reliable.

### Counts by module (measured 2026-10-06, on `structural-dedupe-and-owner-decisions`)

| Module | Built (interpolates) | Fixed sentence | Total | Files |
|---|---|---|---|---|
| `sim/engine/` | 404 | 68 | 472 | 69 |
| `sim/labour/` | 58 | 8 | 66 | 9 |
| `sim/agents/` | 22 | 6 | 28 | 11 |
| `sim/constants.py` | 5 | 8 | 13 | 1 |
| `sim/world/` | 11 | 0 | 11 | 4 |
| `sim/geography/` | 11 | 0 | 11 | 5 |
| `sim/economy/` | 5 | 0 | 5 | 3 |
| Total | 516 | 90 | 606 | 102 |

Hits by sink (all modules, same date):

| Sink | Built | Fixed |
|---|---|---|
| `return` | 157 | 50 |
| `append` | 167 | 11 |
| `other` | 132 | 0 |
| `assigned` | 30 | 7 |
| `dict_field` | 12 | 14 |
| `keyword` | 13 | 0 |
| `print` | 5 | 8 |

Heaviest files: `projects_starting.py`, `validate_production.py`, `society_hazards.py`,
`labour/labour_training.py`, `projects_staffing.py`, `society_state_pressure.py`, `saveload.py`,
`core_step_phases.py`, `projects_ventures.py`, `economy_credit.py`, `economy_mining.py`,
`tree_merge.py`, `invariants.py`, `economy_freight.py`, `labour/labour_capacity.py`. By family inside
`sim/engine/` the largest are `projects_*`, `society_*`, `economy_*` and `step_phase_*`.

A separate measure of the "about 69 files format numbers themselves" claim of Complaint 362:

```
grep -rlE "%[-+ 0-9.,]*[fdg]|\{[^}]*:[,.0-9]*[fdg]\}" sim --include=*.py --exclude-dir=ui --exclude-dir=tests | wc -l
```

This gave 92 files on 2026-10-06 (engine 58, geography 10, agents 10, labour 9, economy 8, world 7,
`constants.py` 1). It includes number formatting that never reaches a player (logs, reprs), so it is
an upper bound for step 7 below.

### Two populations

Roughly a fifth of the hits are developer or auditor output, not game text: the `validate_*` family,
`civ_start_check.py`, `civ_basket_check.py`, `tree_merge.py`, `saveload.py` (load errors),
`invariants.py`, `mods_*.py`, `automation_audit.py`, `constants.py`. Measure (on the `--files`
listing saved as `hits.tsv`):

```
grep -cE "^sim/(engine/(validate_|civ_start_check|civ_basket_check|tree_merge|saveload|invariants|mods_|automation_audit|solve_prices)|constants.py|unit_conversions)" hits.tsv
```

That gave 115 of 606 on 2026-10-06. Per the owner rule these still print, so they move under
`sim/ui/` (the `validate` subcommand already lives in `sim/ui/cli`), but they need no catalogue or
translation: they move as developer text, English only, in one mechanical pass (step 6).

## 2. Classification

Measured over the "built" hits by the template text (a short regex pass over the `--files` listing:
numeric format spec, `%s` or bare slot, dimension keywords on the template; a hit can fall in several
dimension rows and a few land in none). Date measured: 2026-10-06.

| Pattern | Count | Notes |
|---|---|---|
| Fixed sentences, no slot | 90 | Move verbatim into the catalogue under a code. Cheapest. |
| Built, content-name slots only (`%s` or a bare slot, no number format) | 243 | The slot is a node, material, trade, civilisation, place or person name. Needs a typed reference parameter so the UI looks the display name up (later per language). |
| Built, with a numeric format (`%d`, `%.0f`, `{:,.0f}`, `{:.1f}`) | 221 | Quantities. Needs a dimension tag so the UI converts to the player's unit. |
| Of those numeric: calendar time (years, months, days) | 61 | Dimension `calendar_time`; not a unit the player chooses today, but the wording is language dependent. |
| money | 51 | Dimension `money`. Prints the coin word through `money_word` in places, hand-built `denarii` in others (the 285 remainder). |
| ratio or share | 35 | Dimension `ratio`; formatting only, no unit choice. |
| count (people, places, steps, households) | 35 | Dimension `count`; needs plural forms in the catalogue. |
| labour hours | 15 | Dimension `labour_hours`. |
| mass | 7 | Dimension `mass` (tonnes, kilograms). |
| area | 6 | Dimension `area` (hectares). |

The built hits with no number or name slot are sentences with a computed fragment
(`"..." + helper(...)`), the hard cases: the fragment is itself a sentence built elsewhere
(`purchase_rule.remedies_text`, blocker text, `condition_line`). Those become nested messages
(section 3, `parts`) rather than strings.

Structural facts that shape the design:

- Refusals are mostly returned as `(False, text)` or text-or-`None` and travel through several
  layers (`start_reason`, `start_refusal`, `start_blockers` entries `{kind, text, ids}`) before the
  protocol puts them in an `error` or `why` field. The blocker entries already carry a `kind`, the
  nearest thing to a code today.
- Event lines are `(year, text)` tuples in the founder's log and `{message}` dicts in replies. The UI
  then classifies severity by lowercase text markers (`sim/ui/proto/event_severity.py`: "famine",
  "failed", "short of"), and `projects_completion.FAILED_PREFIX` and `MINOR_MARK` are text
  conventions the UI parses. Structured messages replace this guessing with a severity field.
- The UI already patches finished prose after the fact (`sim/ui/units_text.py` rewrites headings and
  `_display` siblings). A typed parameter removes the need to find numbers inside sentences.

## 3. The mechanism

### 3.1 The structured message

One small JSON-safe record in a shared top-level module (`sim/messages.py`, importable by the engine
and every package, importing nothing from them; CLAUDE.md section 5 allows shared top-level modules):

```
message(code, severity=None, **parameters) -> dict
{
  "code": "project.start.over_credit",
  "parameters": {
      "owed":     {"value": 1234.0, "dimension": "money", "native": "civ_coin"},
      "node":     {"id": "bloomery", "kind": "node"},
      "years":    {"value": 3,      "dimension": "calendar_time"},
      "workers":  {"value": 4,      "dimension": "count"}
  },
  "parts": []
}
```

- **code**: names the situation, never the wording. Dotted, lower case, namespaced by domain
  (`project.`, `labour.`, `society.`, `economy.`, `agents.`). A mod's codes are `<mod_id>:<code>`
  (same rule as unit ids, `check_new_id`).
- **parameters**: a quantity (`value`, `dimension`, and `native`, the unit the engine keeps it in,
  the same `native` the unit field rules of Complaint 285 use), a reference (`id` and `kind` in
  `node`, `material`, `trade`, `civilisation`, `place`, `person`, `goal`), or an opaque `text` for a
  data-supplied string. Constructors keep call sites short: `money(owed)`, `mass(amount)`,
  `area(land)`, `hours(labour)`, `years(span)`, `count(workers)`, `share(fraction)`, `node(node_id)`.
- **severity**: one of `info`, `notice`, `warning`, `refusal`, `failure`, `crisis`, `run_end`,
  `completion`. The catalogue entry gives the usual one and a call may override it. It replaces the
  marker-matching tiers of `event_severity.py` (its eight tier names map onto this set).
- **parts**: nested messages (a refusal with its remedies); a template places one with `{parts.0}`.

The engine builds messages and nothing else. It never formats a number for a player, never looks up a
display name, never chooses a unit symbol.

Where a call site still returns a string, the same record carries it as the code `legacy.text` with
one `text` parameter. This keeps migration incremental (section 4): the UI renders `legacy.text`
verbatim, the allow-list counts legacy sites, and each replacement by a real code shrinks the list.

### 3.2 The catalogue in sim/ui

```
sim/ui/messages/<language>/<domain>.json         e.g. sim/ui/messages/en/project.json
mods/<mod_id>/data/messages/<language>/*.json    a mod adds codes, or a whole language
```

Data, not Python, so a mod needs no engine edit and a translator needs no code. One entry per code:

```
"project.start.over_credit": {
  "severity": "refusal",
  "parameters": {"owed": "money", "total": "money", "ceiling": "money", "short_by": "money"},
  "template": "you already owe {owed} on work in hand; this would take it to {total}, and between cash and your credit line you can raise {ceiling}, so you are {short_by} short. Finish or stop something first, or earn or pay down that amount.{parts.0}"
},
"labour.training.students": {
  "parameters": {"students": "count"},
  "plural": {"students": {"one": "{students} student", "other": "{students} students"}},
  "template": "taking on {students}"
}
```

- `{name}` renders by the parameter's dimension: quantities through the one formatting path of
  Complaint 285 (`units.format_<dimension>` with the player's preference), references through the
  display name of the content (the `name` in the data; later a per-language name field), counts
  through the entry's `plural` table keyed by the language's plural categories.
- Loading mirrors `units.load_units`: the base files first, then each mod in `get_ordered_mods`
  order. A code defined twice is an error unless the mod entry says `"override": true` (so a mod can
  reword a base message and a language pack can ship alone).
- Fallback chain: the player's language, then English, then a visible `[code]` placeholder. A
  `language` setting joins `display_units` in `sim/engine/settings.py` (saved like other options,
  default English, so nothing changes).
- `event_severity.py`, `explain_once.py` and `event_groups.py` read `severity` and `code` and stop
  parsing text.

### 3.3 The JSON protocol keeps numbers

Every existing key keeps its current text, so agents that read `error`, `note`, `why` or `message`
see the same strings in the default language and units. Beside each rendered field the reply adds the
structure:

```
{"ok": false,
 "error": "you already owe 1,200 denarii on work in hand; ...",
 "error_code": "project.start.over_credit",
 "error_parameters": {"owed": {"value": 1234.0, "dimension": "money", "native": "civ_coin",
                               "display": "1,200 denarii"}}}
```

`value` is always in the engine's `native` unit and `display` is what the text shows, the same pairing
as the `_display` siblings of Complaint 285 and under the same rule: base-unit numbers stay
available, so an agent never parses prose or guesses a unit. Event entries gain `code`, `severity`
and `parameters` beside `message`. `sim/PROTOCOL.md` documents `<field>_code` and
`<field>_parameters` once as a general rule, not per command. Text screens render from the message
dict and no longer need `units_text.for_text` to rewrite finished prose.

Nothing in the engine reads a rendered string back. Code that tests text today (`FAILED_PREFIX`,
`MINOR_MARK`, `startswith`) tests `code` or `severity` once its module migrates.

### 3.4 The check that fails on new sentence-building

A new test topic `sim/tests/test_player_text_in_engine.py`, with the scanner as
`sim/tests/player_text_scan.py` and the allow-list as `sim/tests/player_text_allowlist.json`
(owned by `sim/tests`):

- The scanner counts hits per file outside `sim/ui/`, `sim/tests/` and declared developer tools.
- The allow-list maps each file to a ceiling. The test fails when a file has more hits than its
  ceiling, or has any hit and is not listed. It also fails when a ceiling is above the measured count,
  so a migration lowers the number in the same change. The report mode prints what remains, as the
  worklist. One line per file, sorted, keeps merge conflicts rare.
- This ratchet only blocks growth. It is not a burndown target in the sense of the owner decision
  of 2026-10-02 (do not drive this with a burndown test): no deadline, and no failure for legacy
  that is still there.
- `test_message_catalogue` loads the English catalogue and checks that every `message("code", ...)`
  call found by `ast` has an entry, its parameters match the declared dimensions, and every entry is
  used (or marked `mod_api`). It also renders every entry with sample values in a fake language and
  fake units (the technique of the `blob` unit test of Complaint 285), proving no template hardcodes
  a unit or a currency word.
- A new `message("legacy.text", ...)` counts like a new sentence and fails the same way.

Tests that already guard text (`test_ui_mod_neutral_text`, `test_player_text_names_own_civilisation`,
`test_complaint_285_text_screens`) stay and also run over the catalogue files.

### 3.5 Rules the migration follows

- A message is created where the fact is known, with raw quantities and ids (general actors: the same
  message serves a firm, a state or another player).
- No code in the engine switches on a rendered string.
- Content names are references, never pasted names, so mods and a translated civilisation work
  (CLAUDE.md 4.7).
- A catalogue template never contains a unit, a coin word or a content id: they arrive as typed
  parameters.
- Messages kept in the save (the founder's log) are stored as the dict. No migration of old saves
  (4.6).

## 4. Migration order

Each step is one pull request. The fingerprint (`python3 -m sim.tests.fingerprint record
before.json`, then `check before.json`) proves the simulation unchanged; the topics named below run
with `python3 -m sim.tests --only ...`; `--slow` runs before each PR.

### How expected strings stay stable

1. The English templates reproduce today's sentence exactly at default units. Each migrated site gets
   a rendering test: the engine's message, rendered by `sim/ui` with default preferences, equals the
   string the site produced before (the expected value copied from the old code into that module's
   test, written before the change).
2. The protocol tests that assert on messages are not edited in the same change. They keep passing
   against the rendered `error`, `note` and `message` fields. If one fails after a step, the template
   drifted and the template is fixed, not the test.
3. Until a site is migrated it returns `legacy.text`, rendered verbatim. The renderer exists and is
   exercised from step 1, with no change in output.
4. A sentence that embeds another (refusal plus remedies) migrates bottom up: the inner message
   first, as a part.

### Steps

| Step | Scope | Risk | Test |
|---|---|---|---|
| 0 | This plan, the scanner moved to `sim/tests/player_text_scan.py`, the allow-list at the measured counts, the check of 3.4. No engine edit. | none | the new topic; suite unchanged |
| 1 | `sim/messages.py` (record, constructors, severity set), the renderer and catalogue loader in `sim/ui/messages/`, code `legacy.text`, the `language` setting, JSON `<field>_code` and `<field>_parameters`, the `sim/PROTOCOL.md` rule. No engine call site migrated; `ui_port` exports the renderer. | low | catalogue test; a sample mod adds a code and a language; existing reply keys unchanged |
| 2 | Consumers that parse text: `event_severity.py`, `projects_completion.FAILED_PREFIX` and `MINOR_MARK`, blocker entries (`text` becomes a message beside `kind`). Log entries become message dicts, still `legacy.text`. | medium (event stream) | `hazard_messages_match_mechanics`, `blocker_readouts_agree`, `screen_text_defects`, event protocol tests; fingerprint |
| 3 | Small, least shared engine modules: `fog.py`, `purchase_rule.py`, `cash_remedies.py`, `founder_sales.py`, `hazard_hedge_timing.py`, `projects_exclusions.py`, `blockers.py`, `failure_cause.py`, `planner.py`, `path_search.py`. Mostly fixed sentences and a few quantities; the first real codes. | low | `refusal_cash_remedies`, `small_text_remains`, `command_search_and_text`, plus a rendering test per site |
| 4 | `society_*` (hazards, state pressure, adoption, disclosure), `interest_groups.py`, `step_phase_*`, `core_step_phases.py`. Event text with many quantities and names. | medium | `hazard_messages_match_mechanics`, `player_text_names_own_civilisation`, society tests, fingerprint |
| 5 | `projects_*` (starting, staffing, ventures, progress, precaution, completion): the densest area and the refusal path agents read. Migrate `start_reason` one `_check_*` at a time, keeping `start_refusal` rendering identical. | medium-high | `refusal_*`, `alerts_staffing_finish`, `affordability_*`, `complaint_96_schooling_message`; golden JSON `error` and `why` replies recorded before the step |
| 6 | Developer text: `validate_*`, `civ_start_check.py`, `civ_basket_check.py`, `tree_merge.py`, `saveload.py`, `invariants.py`, `mods_*.py`, `settings_table.py`, `constants.py`: moved under `sim/ui/` (or declared developer tools in the allow-list), English only, no catalogue. | low | `simulator.py validate` output diff before and after; the tests that call them |
| 7 | Number formatting sweep: remaining files that format numbers for players without a message, converted with the same constructors. | low-medium | `complaint_285_text_screens` extended so the fake-unit test also renders migrated messages (closes the 285 "prose built inside the engine" remainder) |
| 8 | Walled packages after their in-flight work merges: `sim/economy/`, `sim/agents/`, `sim/labour/`, `sim/geography/`. The package returns messages through its `api.py` objects, the engine adapter passes them up unchanged, `sim/ui` renders. Packages import only `sim/messages.py`, never `sim.ui` (two-way wall). | medium | each package's tests and text tests; wall import tests |
| 9 | Retire `legacy.text`: allow-list at zero for engine modules, fallback dropped, catalogue documented for modders in `mods/README.md`. | low | the 3.4 check with an empty list |

### Work in flight

Other branches edit these areas now (worktrees seen 2026-10-06). Their migration is scheduled after
those merge, and each step re-runs the scanner at its start instead of trusting the table above.

| In flight | Area | Affects step |
|---|---|---|
| `labour-core-sets-economy-wages` | `sim/economy/` labour files, `sim/labour/` | 8 (labour, economy); `labour_training.py` text stays until then |
| `every-posting-names-a-counterparty` | money postings in `sim/engine/` (`cash_book`, `cash_remedies`, `step_phase_money`, `economy_credit`) | 3 (`cash_remedies`) and part of 4; after the merge |
| `civilisations-hold-tiles-and-roads` | `sim/geography/` and its engine adapter | 8 (geography) |
| `dashboard-history-cap-option` | `sim/ui/` options and settings | 1 (the `language` setting shares `settings.py` and `cli_options.py`); rebase after it merges |

Steps 0 to 2 touch only new files, `sim/ui/`, the event-parsing helpers and `ui_port.py`, so they can
start at once. From step 3 on, give each parallel agent a disjoint file set and say so in its prompt
(CLAUDE.md section 1).

## 5. Size of the job

By the 2026-10-06 measure: of the order of six hundred sentence sites in about a hundred files, about
a fifth of them developer text. Fewer distinct codes are needed than sites, because one refusal is
built at several places (the repeated "must be greater than zero" guards in `labour_training.py` and
`labour_wages.py`). Per-site work is mechanical; the nested-sentence sites need judgement. Haiku suits
the fixed-sentence modules (step 3); Sonnet suits `projects_*` and `society_*`, with a regression test
for each refusal written first (CLAUDE.md section 6).

## Appendix: the scanner

The counts above came from this source. Save as `player_text_scan.py`; `python3 player_text_scan.py
sim` prints the table and `--files` prints one tab-separated hit per line. It moves into `sim/tests/`
in step 0.

```python
"""Count player-text sentence building outside sim/ui and sim/tests.

usage: python3 player_text_scan.py [root=sim] [--files]
"""
import ast
import collections
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "sim"
SKIP = ("sim/ui", "sim/tests", "sim/geography/layer_build")
KEYS = {"note", "error", "message", "reason", "warning", "advice", "text", "why", "hint", "msg",
        "line", "notes", "detail", "meaning"}
NAMEHINT = re.compile(r"(reason|note|msg|message|text|why|warning|advice|hint|refus|line|detail|sentence)", re.I)
APPENDS = {"append", "insert", "extend", "add", "write"}


def is_str(node):
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def words(text):
    return len(re.findall(r"[A-Za-z]{2,}", text))


def flatten_add(node, parts):
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        flatten_add(node.left, parts)
        flatten_add(node.right, parts)
    else:
        parts.append(node)


def classify(node):
    if isinstance(node, ast.JoinedStr):
        literal = "".join(v.value if isinstance(v, ast.Constant) else
                          "{%s:%s}" % (ast.unparse(v.value), ast.unparse(v.format_spec) if v.format_spec else "")
                          for v in node.values)
        if any(isinstance(v, ast.FormattedValue) for v in node.values) and words(literal) >= 2:
            return "built", literal
        if words(literal) >= 3:
            return "fixed", literal
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod) and is_str(node.left) \
            and words(node.left.value) >= 2:
        return "built", node.left.value + " <- " + ast.unparse(node.right)[:100]
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        parts = []
        flatten_add(node, parts)
        if any(is_str(p) and words(p.value) >= 2 for p in parts) and any(not is_str(p) for p in parts):
            return "built", " ".join(p.value for p in parts if is_str(p))
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "format" \
            and is_str(node.func.value) and words(node.func.value.value) >= 2:
        return "built", node.func.value.value
    elif is_str(node) and words(node.value) >= 3 and " " in node.value.strip():
        return "fixed", node.value
    return None


def inner(node):
    if isinstance(node, (ast.Tuple, ast.List)):
        for element in node.elts:
            yield from inner(element)
    elif isinstance(node, ast.IfExp):
        yield from inner(node.body)
        yield from inner(node.orelse)
    else:
        yield node


class Scan(ast.NodeVisitor):
    def __init__(self):
        self.hits = []
        self.claimed = set()

    def claim(self, node, sink):
        for expression in inner(node):
            found = classify(expression)
            if found and sink == "keyword" and found[0] == "fixed":
                continue  # parameter rationale strings are for developers
            if found and id(expression) not in self.claimed:
                for sub in ast.walk(expression):
                    self.claimed.add(id(sub))
                self.hits.append((sink, found[0], found[1], expression.lineno))

    def visit_Expr(self, node):
        if is_str(node.value):
            self.claimed.add(id(node.value))  # docstrings
        self.generic_visit(node)

    def visit_Raise(self, node):
        if isinstance(node.exc, ast.Call) and node.exc.args:
            for sub in ast.walk(node.exc.args[0]):
                self.claimed.add(id(sub))  # developer errors are not player text
        self.generic_visit(node)

    def visit_Return(self, node):
        if node.value is not None:
            self.claim(node.value, "return")
        self.generic_visit(node)

    def visit_Dict(self, node):
        for key, value in zip(node.keys, node.values):
            if is_str(key) and key.value in KEYS:
                self.claim(value, "dict_field")
        self.generic_visit(node)

    def visit_Call(self, node):
        function = node.func
        if isinstance(function, ast.Name) and function.id == "print":
            for argument in node.args:
                self.claim(argument, "print")
        elif isinstance(function, ast.Attribute) and function.attr in APPENDS:
            for argument in node.args:
                self.claim(argument, "append")
        for keyword in node.keywords:
            if keyword.arg and (keyword.arg in KEYS or NAMEHINT.search(keyword.arg)):
                self.claim(keyword.value, "keyword")
        self.generic_visit(node)

    def visit_Assign(self, node):
        for target in node.targets:
            name = target.id if isinstance(target, ast.Name) else target.attr if isinstance(target, ast.Attribute) else None
            if name and NAMEHINT.search(name):
                self.claim(node.value, "assigned")
        self.generic_visit(node)

    def visit_JoinedStr(self, node):
        if id(node) not in self.claimed:
            found = classify(node)
            if found:
                self.hits.append(("other", found[0], found[1], node.lineno))
                for sub in ast.walk(node):
                    self.claimed.add(id(sub))
        self.generic_visit(node)

    def visit_BinOp(self, node):
        if id(node) not in self.claimed:
            found = classify(node)
            if found and found[0] == "built":
                self.hits.append(("other", "built", found[1], node.lineno))
                for sub in ast.walk(node):
                    self.claimed.add(id(sub))
        self.generic_visit(node)


rows = []
for directory, _, names in os.walk(ROOT):
    if any(directory.startswith(skipped) for skipped in SKIP):
        continue
    for name in names:
        if name.endswith(".py"):
            path = os.path.join(directory, name)
            scan = Scan()
            scan.visit(ast.parse(open(path).read()))
            rows += [(path,) + hit for hit in scan.hits]
if "--files" in sys.argv:
    for row in rows:
        print("%s:%d\t%s\t%s\t%s" % (row[0], row[4], row[1], row[2], row[3][:90].replace("\n", " ")))
    sys.exit()
by = collections.defaultdict(collections.Counter)
for path, sink, kind, template, line in rows:
    parts = path.split("/")
    module = "/".join(parts[:2]) if len(parts) > 2 else path
    by[module][kind] += 1
    by[module]["total"] += 1
    by[module]["files:" + path] = 1
print("%-24s %6s %6s %6s %6s" % ("module", "built", "fixed", "total", "files"))
for module, counter in sorted(by.items(), key=lambda item: -item[1]["total"]):
    files = sum(1 for key in counter if key.startswith("files:"))
    print("%-24s %6d %6d %6d %6d" % (module, counter["built"], counter["fixed"], counter["total"], files))
print("TOTAL", collections.Counter(row[2] for row in rows), "files", len(set(row[0] for row in rows)))
print(sorted(collections.Counter((row[1], row[2]) for row in rows).items()))
```
