# Sim as a composition root: modules behind contracts, assembled from a registry

**Status:** proposal, written 2026-10-25 at `0be2f72`. Changes no code. Supersedes the recommendation in
`SIM_DECOMPOSITION_REVISITED.md` section 7 (its stage 1 is built: the year is the phase registry in
`sim/engine/year_phases.py`). Builds on `PACKAGE_WALLS.md`, the ownership map in Complaint 508 and the kernels in
Complaint 661.

Every number below came from the command beside it at that commit. Re-run before acting on one.

---

## 1. The question, and why it is one question

The owner asked for two things: `Sim` should stop being a god object, and a mod must be able to add, remove or edit
any feature, down to swapping out a whole module or a single method.

Those are the same requirement seen from two sides. To swap something out, a mod needs a unit that (a) owns its state,
(b) is reached only through an interface, and (c) is chosen at one place rather than named at every call site. That
unit is also exactly what a decomposed `Sim` would be made of. Today the engine has no such unit: a mixin is chosen by
`Sim`'s base list at import time, its methods are reached as `self.<name>` from anywhere, and its state lives in shared
dataclasses. So any decomposition that does not produce swappable units leaves the mod requirement unmet, and any mod
mechanism that does not produce owned units leaves the god object in place.

---

## 2. What is there now

| Fact | Measure | At `0be2f72` |
|---|---|---|
| `Sim` direct bases, MRO length, callable names | command 1 in `sim/ARCHITECTURE.md` section 6 | 62, 126, 1054 |
| Mixin classes in the MRO | `python3 -c "import sys; sys.path.insert(0,'.'); from sim.engine.core import Sim; print(len([c for c in Sim.__mro__ if c.__name__.endswith('Mixin')]))"` | 124 |
| Direct bases after the fifth and sixth decomposition steps merged, and now | the base count from `git show <commit>:sim/engine/core.py`, script in `SIM_DECOMPOSITION_REVISITED.md` section 8 | 55 at `eaf2ee3` and `6fe774d` (both 2026-10-20), 62 at `0be2f72` (2026-10-24) |
| References from one class's source to a method or property that a different class of the MRO defines | appendix script | 1559, across 636 class pairs |
| The same references grouped by the topic prefixes of `sim/ARCHITECTURE.md` section 2: share that stays inside a topic | appendix script, second half | 1396 of 2534 (same-class references included) |
| Distinct members of a walled package used from outside it (non-test code and mods) | `grep -rnoE "\b(self\|sim\|s)\.labour\.[a-zA-Z_]+" sim mods --include=*.py \| grep -v "^sim/labour/\|^sim/tests/" \| sed -E "s/.*\.labour\.//" \| sort -u \| wc -l` (substitute `geography`, `economy`) | labour 106, geography 27, economy 51 |
| Classes composing `Labour` itself | `python3 -c "import sys; sys.path.insert(0,'.'); from sim.labour.api import Labour; print(len(Labour.__mro__) - 1)"` | 13 |
| Hook registries a mod can reach | `grep -rn "^def register\|^    def register" sim --include=*.py \| grep -v tests` | see below |

What the measurements say:

1. **Folding mixins is losing to growth.** The fifth and sixth decomposition steps took the base list to 55; four days
   of feature work took it to 62. Extracting arithmetic into package functions (the sixth step) is good work, but it
   leaves the mixin, its name on `Sim` and its callers where they were, so nothing stops the next feature from adding
   a mixin.
2. **The coupling is calls more than fields.** Fourteen non-method names are read by four or more classes
   (appendix), most of them `state`, `nodes`, `civ`, `household`. The 1559 cross-class method references are the
   real coupling. Topics are real: a little over half the references stay inside one topic, so modules exist to be found, though
   not cleanly.
   The hub is the older economy code (`economy*.py` outside the port): the largest inbound count of any topic.
3. **The walls built so far are the right shape and are not swappable.** `sim.labour` is built by a hard-coded
   `Labour(LabourWorld(self))` inside a property (`sim/engine/labour_port.py`), so a mod cannot hand in another
   `Labour`. Inside the wall, `Labour` is itself a thirteen-class mixin composite; the wall is what makes it safe,
   not its inside.
4. **Each mod has added its own hook.** Town size, town mortality, externalities, director overhead, wealth claims,
   phases, actor kinds, spawners, the world scope, policies, protocol commands and player commands each have their
   own `register` function. They disagree on a repeated name: `register_town_provider` and the player
   `register_command` replace silently, `externalities.register` and `director_overhead.register` append unless the
   same function is already there, `register_world_scope` overwrites a single slot, the protocol `register_command`
   asserts. All of them are module globals, so they belong to the process, not to a game.
5. **Shipped mods reach past the mod interface.** `mods/bh_cashshelter_z6f2/hooks.py` imports
   `sim.engine.theft_exposure`, `sim.engine.coin_hoard` and `sim.engine.state_demand` (and probes for
   `register_wealth_claims` with `getattr`); `mods/bh_towns_m8d4/hooks.py` calls the private
   `sim.ui.proto.dispatch._agent_dispatch_inner`. Each is a dependency on an engine name that no contract protects
   (`grep -rn "from sim\|import sim\." mods --include=*.py`).
6. **The port property costs more than the extra hop.** On this machine (`python3 -m timeit`, the three cases in the
   appendix): `self.method()` 18 ns, `self.module.method()` through a plain attribute 20 ns, through today's
   cached-in-`__dict__` property 51 ns. A module held as a plain attribute is nearly free; the property is not.

---

## 3. The suggestions, against the two requirements

| Suggestion | Where | Shrinks `Sim` | Mod can replace | Mod can remove | Verdict |
|---|---|---|---|---|---|
| Fold one-job mixins into their domain mixin, move methods between mixins | `SIM_DECOMPOSITION_REVISITED.md` stage 2, steps five and six | Briefly; measured growing back | No | No | Keep only as a step inside module extraction |
| Pull rules into plain functions with stated inputs | sixth step, CLAUDE.md section 6 | No (the mixin stays as glue) | Only by monkeypatching the function | No | Keep: it is how a mixin's logic becomes a module's inside, and the precondition for kernels |
| One owner per fact, narrow views | Complaint 508 | Yes, per group | Not by itself: nothing chooses the owner | Not by itself | Keep: it is the module boundary list |
| Walled packages behind `api.py` and an engine adapter | `PACKAGE_WALLS.md` | Yes | No: the constructor is hard-coded | No | Keep the shape, add assembly |
| Kernels: pure functions with sample inputs, replaceable if equivalent | Complaint 661 | No | Yes, for computations that must not change results | No | Keep, as the finest grain of swap |
| `__getattr__` forwarding so call sites stay unedited | rejected in `HOUSEHOLD_EXTRACTION.md` section 2 | Cosmetically | Could be made to | Could be made to | Rejected again: measured 51 times a direct access |
| Entity-component-system | not proposed in this tree; the usual answer elsewhere | Yes | Systems, yes | Systems, yes | Reject: see below |
| Events everywhere (a bus every mechanism publishes to) | common in game modding | No | No: an event adds behaviour, it does not take it away | No | Use only for adding, as extension points |
| Mods monkeypatch or subclass `Sim` | what code mods can do today | No | Yes, fragile | Partly | Reject: breaks silently on a rename, two mods cannot see each other |
| Grow in place, `Sim` stays the orchestrator | `CURRENT_CODE_ARCHITECTURE_REVIEW.md` section 2 | Slowly | No | No | Agree that `Sim` orchestrates; it should orchestrate modules and own nothing else |

Why not an entity-component-system, since it is the textbook answer for moddable simulations: two of its three
parts are already here. The phase registry is its systems; the state dataclasses are its components. The third part,
the rule that systems never call each other and talk only through component data, does not fit this model: a project
start asks the labour market for a wage this year, and a price solve asks every producer for a cost, synchronously.
Forcing those through component data means a frame of delay or a hand-built query layer, which is a module contract
under another name. It would also be a rewrite of the engine with no speed gain in pure Python.

---

## 4. Recommendation: modules behind contracts, assembled from one registry per game

`Sim` becomes a composition root. It holds the state, the random source, the seats and `act_as`, the year loop, and
one plain attribute per assembled module. Every rule lives in a module. A module is the unit of ownership, of
interface and of swap, at once.

### 4.1 What a module declares

```python
@dataclass(frozen=True)
class ModuleSpec:
    module_id: str                                   # "labour"; a mod's new module is "<mod_id>:<name>"
    contract: type                                   # a typing.Protocol: everything other modules may call
    implementation: type                             # the shipped class, and the reference for its tests
    requires: Tuple[str, ...] = ()                   # modules it calls; assembly fails without them
    optional: Tuple[str, ...] = ()                   # modules it calls when present; handed None when removed
    world_state: Optional[type] = None               # dataclass saved once per game
    seat_state: Optional[type] = None                # dataclass saved once per seat, rebound by act_as
    phases: Tuple[Phase, ...] = ()                   # its steps of the year (sim/engine/year_phases.py)
    extension_points: Tuple[ExtensionPoint, ...] = ()
    kernels: Tuple[Kernel, ...] = ()                 # Complaint 661
    contract_version: int = 1
```

A module reaches another only through the handle it was given at assembly for something it `requires` or lists as
`optional` (`self.geography.tile_facts(tile)`), and only for members of that module's contract. That replaces the
hand-written adapters (`LabourWorld`, `GeographyWorld`, `SimWorld`): the contract is the adapter, and it is typed.

### 4.2 What a mod can do

```python
def register(api):
    api.extend_module("labour", CheaperApprentices)        # a layer over the current implementation; layers stack
    api.replace_module("disease", HumoralDisease)          # one replacer per module; a second is an error naming both
    api.remove_module("campaigns")                         # refused while any remaining module requires it
    api.add_module(ModuleSpec("religion", ...))            # namespaced as <mod_id>:religion
    api.provide("labour.town_population", town_size)       # an extension point: what register_town_provider is today
    api.kernel("markets.clear_goods", faster_clear)        # refused unless it matches the reference on sample inputs

class CheaperApprentices:
    def training_cost(self, trade, seat_id):
        return super().training_cost(trade, seat_id) * 0.8
```

- **Add** a module: new id, its own contract, state, phases, commands.
- **Replace** a module: a class implementing the same contract. Whole-subsystem swaps (another disease model, another
  market) go here.
- **Extend** a module: the "edit one method" case. Assembly builds the class once per game,
  `type(name, (later_mod_layer, earlier_mod_layer, ShippedLabour), {})`, so `super()` reaches the layer below and
  several mods stack in load order. An override of a member outside the contract is allowed but reported as unstable
  by `validate`, since internal names carry no promise.
- **Remove** a module: allowed when nothing left `requires` it; otherwise the error names the remover and each module
  that still needs it, the same rule data removal follows (`mods/README.md`). An `optional` caller is handed `None`
  and must say what it does without the module (CLAUDE.md section 5: a missing input must not silently stop its
  users); its contract tests run with each optional module removed.
- **Provide** to an extension point: adding behaviour without replacing anything. One mechanism with a declared
  signature and a declared way to combine answers (sum, first answer that is not `None`, ordered list). Every
  `register_*` function in section 2 point 4 becomes an extension point of the module that owns the question, with a
  name clash handled one way.
- **Kernel**: the speed swap of Complaint 661, unchanged in design, owned by a module.

### 4.3 Assembly

- Once per game, at `Sim` construction and after a load, from the game's mod list in load order. The result is a
  plain attribute per module (`sim.labour`), never a property, so a call costs what section 2 point 6 measured for a
  plain attribute. Nothing is looked up per call; a stack of extend layers adds one frame per layer, only on the
  methods a mod overrides.
- Registrations are kept per mod id, and each game assembles only from its own mods, so two games in one process (the
  test runner, a server) can run different mod sets. This retires the process-wide registry globals.
- The order is a pure function of the mod set, so a game assembles identically on every run and after every load.
- The save records the assembly: each module's implementation and its layers, with mod ids and versions. A load whose
  assembly differs is refused with the difference named (CLAUDE.md 4.6: no migration). Multiplayer compares the same
  record (Complaint 661 point 4).

### 4.4 State

A module's `world_state` and `seat_state` are registered into the saved state when the module is assembled, so the
save stays derived from dataclasses (`get_save_fields`, `serialize_state`) and removing a module removes its fields
with no list to edit. `act_as` rebinds every module's seat slice the way it rebinds `household` today
(`sim/engine/core_seats.py`). This is the step `PACKAGE_WALLS.md` names as next ("giving each package its own saved
state"), and each group moved deletes its forwarding properties in `core_properties.py`.

### 4.5 Phases and commands belong to modules

The shipped order of the year stays one explicit list of phase names (today's `SHIPPED`, reviewable in one place);
each name's handler comes from the module that owns it. Removing a module drops its phases from the list; a mod
module places its phases with `after`/`before` as now. A module's protocol commands and figures are registered with
it, so they leave with it.

### 4.6 What this does not do

It does not remove the domain's coupling. Money still affects labour, which affects building, which affects money;
modules will still call each other often. What changes is that every such call names its target module and a
contract member, so a change can see its readers, a mod can stand in for either side, and removal is checked. That is
the property Complaint 508 asks for.

---

## 5. Costs and risks

- **Size.** It touches most of the engine. It is a strangler, not a rewrite: mixins and modules coexist, each module
  extraction merges alone, and the year keeps running throughout.
- **Contracts become public.** Renaming a contract member breaks mods. That is the point: the break is a load error
  naming the mod and the member, where today a renamed engine function breaks a monkeypatch silently. Contract
  versions (`contract_version`, a mod declaring `"modules": {"labour": ">=2"}`) make it checkable.
- **Wide first contracts.** Labour's starts near the members used from outside (section 2). Narrowing a contract is
  ordinary work inside one module later.
- **Removal is honest, not free.** Removing labour means replacing everything that requires it. The registry says so;
  it cannot make it cheap.
- **Seat leaks.** A module must not keep a seat slice across `act_as` (the rule `MULTI_ACTOR_STATE_PLAN.md` section
  2.1 already states for `state.household`). The identity test it describes extends to module slices.
- **Code mods stay unsandboxed.** Nothing here changes `mod_code.py`'s boundary; consent still protects the player.
- **Performance.** Moving a hot mixin method behind a module adds about two nanoseconds per call (section 2 point 6);
  replacing today's port properties with plain attributes saves about thirty per access. Measure per extraction with
  the fingerprint's timing output or a `timeit` of the hot call.

---

## 6. Stages

Each stage merges on its own. A refactor stage proves behaviour unchanged (fingerprint `--quick` where it finishes in
well under twenty minutes on the machine, otherwise the targeted topics and a sha256 of the moved computations over
stepped years on a base worktree and the branch, as section 8 of `SIM_DECOMPOSITION_REVISITED.md` records). Tests
call one function each (CLAUDE.md section 6).

| Stage | Work | Proof |
|---|---|---|
| A | The registry: `ModuleSpec`, `ExtensionPoint`, assembly, the four mod operations, the assembly record in the save, `validate` reporting unstable overrides. New small modules under `sim/engine/`. | Tests on toy specs: assembly order, stacking, a second replacer refused naming both, removal refused naming the requirer, optional handed `None`, two assemblies in one process independent |
| B | Register the walled packages (labour, geography, economy, disease) as modules built by the registry, held as plain attributes. Their adapters become the first contracts. | Fingerprint or the hash harness; save round trip; a SMOKE test mod that extends one labour method and one that replaces geography with a subclass |
| C | Turn every `register_*` hook into an extension point of its owning module; update `ModCodeApi` and the shipped mods in the same change. | The shipped mods' own tests; one clash rule tested once |
| D | Phases: each `SHIPPED` handler comes from its module; the name list stays. | Phase order unchanged (a test on `ordered_phases()` names); fingerprint or hash harness |
| E | Strangle the engine mixins into modules, one topic per change. Methods move into the module class, callers change from `self.x()` to `self.<module>.x()`, the mixin leaves the base list. Leaves first (living stock; campaigns, revolts and captives; hazards; coin and theft; foreign trade), then society and projects, the older economy code last because everything calls it. Re-run the appendix script before picking each. | Per change: the hash harness on the moved methods, targeted topics, base count down by the mixins removed |
| F | State slices move with their modules (section 4.4); each group's forwarding properties go. | Save round trip; `get_save_fields` names unchanged except the moved prefix |
| G | Kernels (Complaint 661) registered by their modules, starting with what Complaint 497 measures as largest. | The kernel equivalence check is the test fixture |

Stages A and B alone give mods whole-module and per-method swaps for the four walled packages. E is the long one.

**Done** when `Sim`'s bases are only the composition root (seats, state, year loop, assembly), every shipped phase
has an owning module, no `register_*` global remains outside the registry, and the shipped mods import nothing from
`sim.engine` but `mod_code`'s interface. Each condition is a grep or the base-count command.

**Stop and re-measure** if a stage E extraction leaves the moved module calling back into `Sim` mixins for most of
its work: the topic boundary is wrong there, and the appendix script should be re-run with a different grouping
before forcing it.

---

## Appendix: measurement script

Run from the repository root with `python3 -c` on the text below, or paste into a scratch file outside `sim/`.

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
topic_rules = [("steps", r"^(core_step_phases|step_phase_|year_run|shock_year|core$)"),
    ("projects", r"^(projects|project_|blockers|failure_|planner|path_search|completion|capital_builds|seat_builds)"),
    ("seats", r"^(core_seats|seat_|state_seat|founder_sales|cash_|goals|fog|win_)"),
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

The access-cost figures: `python3 -m timeit` (or `timeit.repeat`) over `instance.method()`, `instance.module.method()`
with `module` a plain attribute, and the same through a property that returns `self.__dict__.get("_module")`.
