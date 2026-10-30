# Sim as a composition root: modules that share views and commands, never each other

**Status:** proposal, revised 2026-10-25 at `347e583` (first written the same day). Changes no code. Supersedes the
recommendation in `SIM_DECOMPOSITION_REVISITED.md` section 7 (its stage 1 is built: the year is the phase registry in
`sim/engine/year_phases.py`). Builds on `PACKAGE_WALLS.md`, the ownership map in Complaint 508 and the kernels in
Complaint 661.

The first version of this document put each topic in a module behind a method contract. That made the coupling
visible and swappable but left all of it in place: every module could still call any contract method of any module
it required. This version reduces the coupling in kind, from shared state and method calls to named data and a small
set of commands. Section 4 says why the first version was not enough.

Owner decisions this plan assumes (2026-10-25): breaking the shipped mods is acceptable, and they are rewritten onto
the new interface; the work lands as one pull request when it is complete, with no partial merges.

Every number below came from the command or appendix script beside it at `0be2f72`. Re-run before acting on one.

---

## 1. The question

`Sim` should stop being a god object, the coupling between its parts should go down, and a mod must be able to add,
remove or edit any feature, down to swapping out a whole module or a single method.

These are one requirement. To swap something out, a mod needs a unit that owns its state, is reached only through a
stated interface, and is chosen in one place. Whether the swap is safe depends on how much the rest of the engine
knows about that unit: if other code calls a hundred of its methods, a replacement must reproduce a hundred
behaviours; if other code reads five named tables and sends it two kinds of command, a replacement must produce five
tables and accept two commands. So the width and kind of the coupling decide how swappable the features are.

---

## 2. What is there now

| Fact | Measure | At `0be2f72` |
|---|---|---|
| `Sim` direct bases, MRO length, callable names | command 1 in `sim/ARCHITECTURE.md` section 6 | 62, 126, 1054 |
| Mixin classes in the MRO | `python3 -c "import sys; sys.path.insert(0,'.'); from sim.engine.core import Sim; print(len([c for c in Sim.__mro__ if c.__name__.endswith('Mixin')]))"` | 124 |
| Direct bases after the fifth and sixth decomposition steps merged, and now | base count from `git show <commit>:sim/engine/core.py`, script in `SIM_DECOMPOSITION_REVISITED.md` section 8 | 55 at `eaf2ee3` and `6fe774d` (2026-10-20), 62 at `0be2f72` (2026-10-24) |
| References from one class's source to a method or property a different class of the MRO defines | appendix A | 1559, across 636 class pairs |
| Those references by what the target does | appendix B | at least 906 reach methods that only read; 640 reach methods that write somewhere below them; 13 pure |
| Share of references (same-class included) that stay inside one topic of `sim/ARCHITECTURE.md` section 2 | appendix A | 1396 of 2534 |
| Engine files that mention a cache or memo | `grep -rlE "cache\|memo" sim/engine --include=*.py \| wc -l` | 100 |
| Distinct `Sim` names the UI reads directly (package handles and imports excluded) | `grep -rnE "\b(s\|sim)\.[a-z_]+" sim/ui --include=*.py \| grep -vE "^\S+:\s*(from\|import) \|sim\.(engine\|ui\|agents\|labour\|geography\|economy\|world\|disease\|constants\|refusal)\b" \| grep -oE "\b(s\|sim)\.[a-z_]+" \| sed -E 's/^(s\|sim)\.//' \| sort -u \| wc -l` | 288 (a local named `s` that is not a `Sim` would count too) |
| Distinct members of a walled package used from outside it | `grep -rnoE "\b(self\|sim\|s)\.labour\.[a-zA-Z_]+" sim mods --include=*.py \| grep -v "^sim/labour/\|^sim/tests/" \| sed -E "s/.*\.labour\.//" \| sort -u \| wc -l` (substitute `geography`, `economy`) | labour 106, geography 27, economy 51 (calls through a local variable are missed) |
| The supported ways a mod changes the world | `grep -n "    def [a-z]" sim/engine/mod_effects.py` | pay, pay to an edge, receive from an edge, add goods, remove goods, kill people, move people, transfer a tile, write a store, record an event |

What the measurements say:

1. **Folding mixins is losing to growth.** The decomposition steps took the base list to 55; four days of feature
   work took it to 62. Nothing in the current shape stops the next feature from adding a mixin.
2. **The coupling is common coupling.** Every mixin reads and writes one shared object through `self`; in the
   classic scale (content, common, control, stamp, data) that is the second worst kind. The parts are not tangled
   because the domain demands it at every edge, but because the shape lets any method reach any other.
3. **Most of it is reading derived values.** At least 906 of the 1559 cross-class references go to methods that only
   read; about 270 of those fetch a package handle (`labour`, `world_map`, `economy`, `geography`). Most of the
   most-referenced "writers" read too: `revenue`, `project_cost`, `living_cost`, `credit_limit`, `spending_power`,
   `mine_operating_cost` and the price tables count as writers because a callee far below them, the `actors`
   accessor (`sim/engine/society_actors.py`), creates `state.actors` on first read (appendix B, last note). Those derived
   values are recomputed on demand by whoever asks, kept fresh by hand-made caches and version counters, and computed
   in more than one place often enough that `STATE_OF_THE_PROJECT.md` has a rule against it.
4. **Real writes go through a small vocabulary.** What changes the world comes down to moving money, moving goods,
   people born, dying or moving, land changing hands, hours committed, projects started and finished, and recorded
   events. `mod_effects.py` already found most of that list for mods.
5. **The walls built so far are the right idea at the wrong width.** `sim.labour` is hard-wired
   (`Labour(LabourWorld(self))` in `sim/engine/labour_port.py`), so no mod can supply another; it shows at least 106
   members to the outside, and its adapter `LabourWorld` hands it the whole `Sim` member by member. Inside, `Labour` is
   itself a thirteen-class mixin composite.
6. **Each mod has grown its own hook.** Town size, town mortality, externalities, director overhead, wealth claims,
   phases, actor kinds, spawners, the world scope, policies and two command registries each have their own
   `register` function (`grep -rn "^def register\|^    def register" sim --include=*.py | grep -v tests`). A repeated
   name is silently replaced in some, appended unless identical in others, overwritten in a single slot in one and
   an assertion in another. All are process globals, so two games in one process cannot have different mods.
7. **Shipped mods reach past the mod interface** into engine modules and a private dispatcher function
   (`grep -rn "from sim\|import sim\." mods --include=*.py`), because the interface lacks what they need.
8. **A module held as a plain attribute is nearly free.** On this machine (`timeit`, appendix C): `self.method()` 18
   ns, `self.module.method()` through a plain attribute 20 ns, through today's cached-in-`__dict__` port property 51
   ns.

---

## 3. The options

| Option | Reduces coupling | Mod can replace | Mod can remove | Keeps today's results provable | Verdict |
|---|---|---|---|---|---|
| Keep folding and moving mixins (`SIM_DECOMPOSITION_REVISITED.md`, steps five and six) | No | No | No | Yes | Measured losing to growth |
| Walled packages behind `api.py` with engine adapters (`PACKAGE_WALLS.md`) | Moves it | No (hard-wired) | No | Yes | Right direction, too wide, not assembled |
| Modules behind method contracts, assembled from a registry (this document's first version) | No: it names it | Yes | Yes, checked | Yes | Not enough: a replacement must copy every contract method's behaviour |
| `__getattr__` forwarding | No | Could | Could | Yes | Rejected: measured 51 times a direct access (`HOUSEHOLD_EXTRACTION.md` section 2) |
| Mods monkeypatch or subclass `Sim` | No | Fragile | Partly | No | What code mods can do today |
| Events everywhere (a bus) | Hides it | No: an event adds, it cannot take away | No | Hard (order is implicit) | Only for additions |
| Message-passing actors (each module a process or mailbox) | Yes | Yes | Yes | No: delivery order becomes a design problem | Heavier than the problem; the year is already a fixed order |
| Entity-component-system | Yes | Systems, yes | Systems, yes | No | Its rule that systems never ask each other anything does not fit a project start that needs this year's wage now |
| Incremental query engine (every derived value a tracked query, invalidated automatically by recorded reads) | Yes | Yes | Yes | Yes | Right semantics, but tracking every read in Python costs on every access, and a general invalidation engine is its own project with subtle bugs |
| **Owners, views and commands (below)** | **Yes, to data coupling** | **Yes** | **Yes, checked** | **Yes** | **Recommended** |

The recommendation takes the useful half of three of these. From the entity-component-system: state is owned data,
and the year is a list of steps. From the query engine: derived values are named, cached and invalidated by version,
but invalidation is declared by the owner (the only writer, so it knows when its data changed) instead of traced on
every read. From the registry: one place assembles each game, and mods add, replace, extend or remove there.

---

## 4. The design

### 4.1 Four rules

1. **Each fact has one owner module, and only the owner writes it.** Complaint 508's table is the starting list of
   owners: the ledger (money and goods), workforce (people, skills, hours), land, production (plants and capacity),
   markets (orders, clearing), knowledge (what each actor knows), and so on.
2. **Modules read each other only through views.** A view is a named, typed, read-only table the owner publishes
   (`material_price`, `wage_by_trade`, `capabilities_running`, `tile_owner`). A consumer names the view, never the
   module behind it.
3. **Modules change each other only through commands.** A command is a typed request to the owner of a fact
   (`Transfer`, `MoveGoods`, `CommitHours`, `StartProject`, `TransferTile`, `KillPeople`). The owner applies it
   against its live state at once and answers with a result or a refusal with a `cause` (`sim/refusal.py`). Money
   cannot be spent twice and hours cannot be committed twice because one owner checks every request.
4. **Nothing holds another module.** A module is handed, at assembly, an object whose plain attributes are exactly
   the views and commands it declared. It cannot reach anything else, and an undeclared name is an assembly error.

What this replaces: the 1559 method references become reads of named views and sends of named commands; `Sim` and
its mixins go; the hand-made caches and version counters become one mechanism; the adapters (`LabourWorld`,
`GeographyWorld`, `SimWorld`, `ui_port`) become declared view lists.

### 4.2 Views

- **Kinds.** A *stored view* is a read-only window on the owner's own state (`tile_owner`). A *derived view* is a
  function of the owner's state and other views it declares (`revenue_by_node` from `capabilities_running`,
  `material_price`, `wage_by_trade`).
- **Freshness.** Every owner keeps a version per view and bumps it when it applies a write that changes the view's
  inputs. A derived view recomputes on first read after any input's version moved, and is cached otherwise. This is
  the `_done_seq` and `_done_changed` pattern done once for everything, so reads within a phase see the same values
  they see today, and the fingerprint can check each move.
- **Keyed reads.** A view is a mapping (`views.material_price[material]`) or a keyed function computed per key on
  demand and cached under the same version, for tables too large to build whole.
- **Quotes.** A question with parameters that does not change anything (what would this project cost, what would
  hiring these hours pay) is a quote: a read-only call the owner answers from its state and its declared views.
  Quotes are views with arguments, and follow the same freshness rule.
- **Seats.** A view about one seat's holdings is read for the acting seat. `act_as` stays the only switch, and an
  owner keeps per-seat versions.

### 4.3 Commands

- One small dataclass per command, owned by the module that applies it. The starting vocabulary is section 2 point
  4, which `mod_effects.py` already names.
- A command is applied synchronously and atomically: it applies whole, or it is refused with a `cause`. A
  cross-owner action (buy goods: money moves one way, goods the other) is one command to the ledger, which owns
  both.
- Commands are the only writes across modules, so `grep` over command classes lists every way the world can
  change.

### 4.4 What a module declares

```python
@dataclass(frozen=True)
class ModuleSpec:
    module_id: str                                  # "workforce"; a mod's new module is "<mod_id>:<name>"
    implementation: type
    owns: Tuple[type, ...] = ()                     # its state dataclasses, world or per seat; saved automatically
    publishes: Tuple[ViewSpec, ...] = ()            # views and quotes, each with its declared inputs
    applies: Tuple[type, ...] = ()                  # command classes it is the owner of
    reads: Tuple[str, ...] = ()                     # views and quotes it uses, by name
    optional_reads: Tuple[str, ...] = ()            # used when provided; None when no module provides them
    sends: Tuple[type, ...] = ()                    # commands it may send
    phases: Tuple[Phase, ...] = ()                  # its steps of the year (sim/engine/year_phases.py)
    extension_points: Tuple[ExtensionPoint, ...] = ()
    kernels: Tuple[Kernel, ...] = ()                # Complaint 661
```

From these declarations the engine prints the whole dependency graph (which module reads what, sends what), so the
coupling is measured from data rather than by the AST scripts in the appendix.

### 4.5 What a mod can do

```python
def register(api):
    api.replace_module("disease", HumoralDisease)                  # must publish what the replaced one published
    api.remove_module("campaigns")                                 # refused while a remaining module reads its views
    api.add_module(ModuleSpec("religion", ...))                    # its own state, views, commands, phases
    api.extend_module("workforce", CheaperApprentices)             # a class layer: edit single methods
    api.adjust_view("wage_by_trade", lambda wages, views: {trade: wage * 0.9 for trade, wage in wages.items()})
    api.provide("workforce.town_population", town_size)            # an extension point: add to an answer
    api.kernel("markets.clear_goods", faster_clear)                # refused unless it matches the reference
```

- **Replace** a module: the replacement publishes the same views and applies the same commands (checked at
  assembly). A replacement need only reproduce those, not the old module's internals.
- **Remove** a module: refused while any remaining module reads one of its views or sends one of its commands, unless
  another module provides them; the error names the remover and each reader. A reader that declared the view
  optional receives `None` and must say what it does without it; its tests run with each optional view absent.
- **Add** a module: new names are `<mod_id>:<name>`.
- **Adjust a view**: a stackable function over a published view, applied in mod load order. This is the stable way
  to edit an outcome: it depends on a view's name and shape, which change far less often than method names.
- **Extend** a module: assembly builds the class once, `type(name, (later_layer, earlier_layer, Shipped), {})`, so
  `super()` reaches the layer below and layers stack. This edits internals, so `validate` labels it unstable.
- **Provide** to an extension point: one mechanism replacing every `register_*` in section 2 point 6, with a
  declared signature, a declared way to combine answers (sum, first answer that is not `None`, ordered list) and one
  clash rule.
- **Kernel**: Complaint 661 unchanged, owned by a module.

### 4.6 Assembly, saves, determinism, speed

- **Assembly** happens once per game, at construction and after a load, from that game's mods in load order. Each
  view and command name is bound to exactly one provider: none is an error naming the reader, two is an error naming
  both. Registrations are kept per mod id, so two games in one process can run different mods; the process globals
  go.
- **Saves** are derived from the owned dataclasses, as now (`get_save_fields`, `serialize_state`); a module's state
  enters the save when it is assembled and leaves when it is removed. Views are never saved. The save records the
  assembly (modules, layers, adjusters, mod ids and versions); a load with a different one is refused, naming the
  difference (CLAUDE.md 4.6).
- **Determinism**: assembly order, phase order and adjuster order are pure functions of the mod set. Iteration inside
  views follows the save-order rule of CLAUDE.md section 5.
- **Speed**: views and commands are plain attributes on the handed object (section 2 point 8). A derived view read
  costs a version comparison and a dictionary lookup when fresh. A view whose inputs change often must be keyed per
  item, or its recompute dominates: measure each with `timeit` and the fingerprint's timing output.

### 4.7 What `Sim` keeps

The state, the random source, the seats and `act_as`, the year loop over phases, and the assembled modules. It
defines no rule. The UI and the protocol read views and send commands like any module (`ui_port` becomes a list of
views), so a mod's views appear in the protocol and figures the same way.

### 4.8 What reduces, and what does not

The domain's dependencies stay: revenue still depends on prices, which still depend on wages. What goes is
everything else around them: which code computes a value (a consumer depends on `material_price`, whoever provides
it), every hidden write path (writes are commands to owners), duplicate computations of one number, hand-made cache
invalidation, and `Sim` as the hub of all of it. The coupling that remains is data coupling, the weakest kind, and it
is declared, so it can be printed and checked.

---

## 5. Costs and risks

- **The catalogue is the design.** Too fine (a view per old method) recreates the method graph under new names; too
  coarse (one `economy` view) recreates the god object as a table. The catalogue is drafted from the measured read
  targets (appendix B lists them), grouped by owner, and tested on prototype domains before the bulk of the work
  (section 6, phase 1).
- **Iterative inner loops stay inside one owner.** The price solve and the staffing allocation each iterate over
  many producers' costs. They belong inside the module that owns the result, reading other modules' inputs as views.
  The solver is already close to this: `sim/engine/solve_prices*.py` reads almost nothing from `Sim`
  (`grep -ohE "\b(self|sim)\.[a-zA-Z_]+" sim/engine/solve_prices*.py | sort | uniq -c`).
- **Owner discipline.** The design fails if a module keeps a reference to another's state "just for speed". Rule 4
  makes that an assembly error rather than a review comment.
- **One long branch on a busy repository.** The base list grew by seven mixins in four days; every feature merged to
  `main` during the work is written in the old shape and has to be ported. Either engine feature work stops for the
  duration, or the branch merges `main` daily and ports each new mixin as it arrives. This is the largest practical
  risk of doing it in one pull request.
- **Verification without partial merges.** Each move inside the branch is still proven on its own commit (section
  6), so the final pull request is a series of checked steps rather than one unreviewable diff.
- **Code mods stay unsandboxed.** Nothing here changes `mod_code.py`'s consent boundary.
- **Removal is checked, not free.** Removing workforce means replacing everything that reads it. The assembly says
  so; it cannot make it cheap.

---

## 6. One branch, in phases

Each step is its own commit with its own proof; nothing merges to `main` until all phases are done. A refactor step
proves behaviour unchanged: the fingerprint `--quick` where it finishes in well under twenty minutes on the machine
(the branch makes it nearly always worth the wait), otherwise targeted topics plus a sha256 of the moved views over
stepped years on a base worktree and the branch. Tests call one function each, which views make easy: a test writes
the input views as plain dictionaries and calls the one rule.

| Phase | Work | Proof |
|---|---|---|
| 0 | Decide the `main` policy (freeze or daily merge). Record the fingerprint baseline at the branch point. | The baseline file |
| 1 | The framework: `ModuleSpec`, views with versions, quotes, commands, assembly with its errors, extension points, adjusters, the assembly record in the save, the dependency printout. Draft the view and command catalogue from appendix B, grouped by Complaint 508's owners. | Tests on toy modules: binding, a missing and a doubled provider, removal refused naming the reader, optional absent, stacking order, two assemblies in one process |
| 2 | Prototype on three domains of different shapes: a leaf (living stock), a heavy reader (project starting, which reads prices, wages and capabilities), and the ledger (the busiest command owner). Revise the framework and catalogue from what they show. | Fingerprint after each; a written list of what changed in the design |
| 3 | The owners of conserved quantities (ledger, workforce hours, land, people) with their commands; every write to those facts goes through a command. | Fingerprint; the conservation tests |
| 4 | The walled packages (labour into workforce, geography into land, economy into markets, disease) become modules; their adapters become declared views. | Fingerprint; save round trip |
| 5 | The remaining mixins, one topic per step, leaves first (campaigns, revolts and captives; hazards; coin and theft; foreign trade), then society, projects and production, the older economy code last because everything reads it. Re-run appendix A and B before choosing each. | Per step: fingerprint, base count down |
| 6 | The UI and protocol read views and send commands; `ui_port` and the forwarding properties in `core_properties.py` go. | Protocol tests; save round trip |
| 7 | The shipped mods rewritten onto the new interface; the old `register_*` functions and the process globals deleted. Each shipped mod becomes the acceptance test of one mod operation. | Each mod's own tests; one SMOKE test per operation (replace, remove, add, extend, adjust, provide) |
| 8 | Kernels (Complaint 661) for the computations Complaint 497 measures as largest. | The equivalence check is the test fixture |
| 9 | The full `--slow` suite, the fingerprint against phase 0's baseline (any divergence explained by a named step), the baseline ensemble checks, then the pull request. | All of it, named in the pull request |

**Done** when `Sim` defines no rule and inherits only the composition root; every write across modules is a command;
every read across modules is a declared view or quote; no module imports another module's code; no `register_*`
global remains outside the assembly; the shipped mods import only the mod interface; and the dependency printout is
the coupling measure. Each condition is a grep or a printout.

**Stop and rethink** if phase 2 shows that a domain's natural catalogue is close to one view per old method: the
grouping is wrong there, and continuing would rename the coupling rather than reduce it.

---

## Appendix A: cross-class references and topics

Run from the repository root (save as a scratch file outside `sim/`).

```python
import ast, collections, inspect, re, sys, textwrap
sys.path.insert(0, ".")
from sim.engine.core import Sim
definer = {}
for klass in Sim.__mro__:
    if klass is not object:
        for name, value in vars(klass).items():
            if callable(value) or isinstance(value, (property, staticmethod, classmethod)):
                definer.setdefault(name, klass)
topic_rules = [("steps", r"^(year_steps|step_phase_|year_run|shock_year|core$)"),
    ("projects", r"^(projects|project_|blockers|failure_|planner|path_search|completion|capital_builds|seat_builds)"),
    ("seats", r"^(seat_|state_seat|founder_sales|cash_|goals|fog|win_)"),
    ("markets", r"^(prices|solve_prices|making_cost|long_run|rent_standin|solve_cache|goods_market|market_|incumbent|producer_costs|entry_cost|wage_|money_units|real_|economy_goods|economy_cost)"),
    ("node_money", r"^(node_|industry_|concern_)"),
    ("foreign_coin", r"^(foreign_|economy_freight|domestic_haul|trader_cargo|coin_|theft_|route_dues)"),
    ("economy_port", r"^economy_port"), ("economy_old", r"^economy"),
    ("labour", r"^(labour_port|staff|projects_staffing|payroll|apprentice)"),
    ("geography", r"^(geography_port|ways|works|held_works|colonies|mine_|food_|soil_|regional_|urban_|demographic)"),
    ("society", r"^(society|interest_groups|legitimacy|benefactions|hazard_|visibility|world_hazards|campaign|revolt|captives|disease_port)"),
    ("living_stock", r"^(living_stock|food_relief|defence_stores)"), ("mods", r"^(mods|mod_)"),
    ("properties", r"^core_properties"), ("mechanics", r"^(mechanics|techniques|material_|capability)")]
def topic(klass):
    module_name = klass.__module__.split(".")[-1]
    return next((label for label, pattern in topic_rules if re.search(pattern, module_name)), "other:" + module_name)
cross_class = collections.Counter(); by_topic = collections.Counter(); field_readers = collections.defaultdict(set)
for klass in Sim.__mro__:
    if klass is object or not klass.__module__.startswith("sim."):
        continue
    tree = ast.parse(textwrap.dedent(inspect.getsource(klass)))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
            if node.attr in definer:
                by_topic[(topic(klass), topic(definer[node.attr]))] += 1
                if definer[node.attr] is not klass:
                    cross_class[(klass.__name__, definer[node.attr].__name__)] += 1
            else:
                field_readers[node.attr].add(klass.__name__)
print("cross-class references", sum(cross_class.values()), "class pairs", len(cross_class))
print("inside one topic", sum(count for (source, target), count in by_topic.items() if source == target), "of", sum(by_topic.values()))
inbound = collections.Counter()
for (source, target), count in by_topic.items():
    if source != target:
        inbound[target] += count
print("inbound by topic", inbound.most_common(8))
print("fields read by four or more classes", sorted(name for name, readers in field_readers.items() if len(readers) >= 4))
```

## Appendix B: what each referenced method does

A method writes if it assigns through `self` or a local alias of something reached from `self`, or calls a
container mutator or a write-like verb on one, and the written name is not a cache, memo, version counter, warn-once
marker, log or private `self._` lazy value; writing is inherited from callees. This is static and approximate: a
write through an object passed in as an argument is missed, and a cache with an ordinary name counts as a write, so
"reads only" is a lower bound.

```python
import ast, collections, inspect, sys, textwrap
sys.path.insert(0, ".")
from sim.engine.core import Sim
CONTAINER_WRITES = {"append", "extend", "update", "pop", "add", "setdefault", "clear", "remove", "insert", "discard", "popitem", "sort"}
WRITE_VERBS = ("pay", "spend", "transfer", "receive", "hire", "fire", "add_", "remove_", "set_", "record", "grant", "take", "give",
               "post", "book", "charge", "credit", "debit", "settle", "buy", "sell", "start", "finish", "complete", "kill", "move", "apply", "assign", "release")
CACHE_WORDS = ("cache", "memo", "__dict__", "_seq", "version", "said", "log", "notice", "warn")
def root_name(node):
    while isinstance(node, (ast.Attribute, ast.Subscript, ast.Call)):
        node = node.func if isinstance(node, ast.Call) else node.value
    return node.id if isinstance(node, ast.Name) else None
def written_text(node):
    text = ast.unparse(node)
    return "cache" if text.startswith("self._") or text.startswith("scope[") else text
classes = [klass for klass in Sim.__mro__ if klass is not object and klass.__module__.startswith("sim.")]
trees = {klass: ast.parse(textwrap.dedent(inspect.getsource(klass))) for klass in classes}
definer, bodies = {}, {}
for klass in classes:
    for item in trees[klass].body[0].body:
        if isinstance(item, ast.FunctionDef) and item.name not in definer:
            definer[item.name], bodies[item.name] = klass, item
reads, writes, calls = {}, {}, {}
for name, function in bodies.items():
    aliases = {node.targets[0].id for node in ast.walk(function) if isinstance(node, ast.Assign) and len(node.targets) == 1
               and isinstance(node.targets[0], ast.Name) and root_name(node.value) == "self" and not isinstance(node.value, ast.Call)}
    owned = aliases | {"self"}
    reads[name], writes[name], calls[name] = False, False, set()
    for node in ast.walk(function):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
            if node.attr in bodies: calls[name].add(node.attr)
            else: reads[name] = True
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AugAssign) else []
        for target in targets:
            if isinstance(target, (ast.Attribute, ast.Subscript)) and root_name(target) in owned \
                    and not any(word in written_text(target).lower() for word in CACHE_WORDS):
                writes[name] = True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and root_name(node.func.value) in owned \
                and not (isinstance(node.func.value, ast.Name) and node.func.value.id == "self") \
                and (node.func.attr in CONTAINER_WRITES or node.func.attr.startswith(WRITE_VERBS)) \
                and not any(word in written_text(node.func.value).lower() for word in CACHE_WORDS):
            writes[name] = True
changed = True
while changed:
    changed = False
    for name in bodies:
        for flags in (reads, writes):
            if not flags[name] and any(flags[callee] for callee in calls[name]):
                flags[name] = changed = True
kinds = collections.Counter(); targets = collections.defaultdict(collections.Counter)
for klass in classes:
    for node in ast.walk(trees[klass]):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self" \
                and node.attr in definer and definer[node.attr] is not klass:
            kind = "writes" if writes[node.attr] else "reads only" if reads[node.attr] else "pure"
            kinds[kind] += 1; targets[kind][node.attr] += 1
print("cross-class references by what the target does:", dict(kinds))
print("distinct targets:", {kind: len(names) for kind, names in targets.items()})
print("most referenced readers:", targets["reads only"].most_common(30))
print("most referenced writers:", targets["writes"].most_common(30))
```

To see why a method counts as a writer, walk its callees to the first one with a direct write; that is how the
chains in section 2 point 3 were found.

## Appendix C: access cost

`timeit.repeat` over `instance.method()`, `instance.module.method()` with `module` a plain attribute, and the same
through a property that returns `self.__dict__.get("_module")`, two million calls, best of five.
