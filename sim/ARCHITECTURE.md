# What this codebase actually is

Measured, not remembered. Every number here carries the command or script
that produced it, right next to the number, per CLAUDE.md SS8. Where no
script exists to re-derive a claim, that is said explicitly instead of
leaving the number to look authoritative. The older design notes in
`rome/*.md` describe a game that has since changed a great deal; treat them
as direction, not as fact. If you change the shape of the code, re-run the
scripts below and correct the numbers they produce.

## The one-paragraph version

`Sim` is a single large object that holds the entire state of one game.
Its base list in `core.py` names eight classes:

    class Sim(EconomyMixin, FogMixin, GeographyMixin, LabourMixin,
              ProjectsMixin, SocietyMixin, ForwardingPropertiesMixin,
              StepPhasesMixin):

Four of those eight - `EconomyMixin`, `LabourMixin`, `ProjectsMixin`,
`SocietyMixin` - hold no methods of their own; each is an empty composition
point that inherits from several further sub-mixins living in their own
files (seven under `EconomyMixin`, five under `LabourMixin`, six under
`ProjectsMixin`, four under `SocietyMixin` - see "The method count" below
for the full list). The other two new base classes, `ForwardingPropertiesMixin`
(`core_properties.py`) and `StepPhasesMixin` (`core_step_phases.py`), are
not composition points over anything further - they are code lifted
straight out of `core.py`'s own `class Sim(...)` body into a sibling file,
and `Sim` inherits each directly, the same way it inherits `FogMixin` or
`GeographyMixin`. See "The composition-point pattern" below for why the
four-mixin form and the two-mixin form are the same underlying move (get
code out of one over-large file without touching `class Sim(...)`'s own
base list) applied at different depths.

The **import** graph across every one of these files is clean and acyclic;
the **runtime** coupling between them is total, because they all talk to
each other through `self`. Moving code into more, smaller files moved it
into separate files without decoupling it. That is worth knowing before you
plan any refactor.

## Layout

Every file directly under `sim/engine/` (`ls sim/engine/*.py | wc -l` = 43,
excluding `__pycache__`), grouped by what it does rather than alphabetically:

    simulator.py        the front door. Re-exports a large surface on purpose,
                        because every playtest note and instruction ever
                        written says `rome/sim/simulator.py`. Do not narrow it.
    engine/__init__.py  package docstring only: names the (now stale - see
                        below) six-subject grouping. Not re-measured here
                        because it is prose inside a .py file, out of this
                        document's ownership.
    engine/data.py      loads and annotates the tree, prices, civs, geography
                        (803 lines). Not a pure leaf any more: `load()` and
                        `goods_provenance()` both do a lazy, function-local
                        `from . import prices as price_solver` when a caller
                        asks for solved prices - see "Where the data lives"
                        below.

    engine/core.py           class Sim, and step(): 2,273 lines total.
                              `wc -l sim/engine/core.py`
    engine/core_properties.py  ForwardingPropertiesMixin: 87 one-line
                              `@property`/`@x.setter` pairs forwarding onto
                              `self.household`/`self.population`, moved out of
                              `core.py` verbatim because they are mechanically
                              identical and were pushing every other reader of
                              `core.py` past all of them to reach anything
                              else. 842 lines. `grep -c "^    @property"
                              sim/engine/core_properties.py`
    engine/core_step_phases.py  StepPhasesMixin: the 14 `_step_*` phase
                              methods `step()` (still in core.py) calls, in
                              the order they always ran in. 1,756 lines. See
                              "Sim.step()" below.
    engine/state.py           authoritative typed simulation state objects:
                              `ActiveProjectState`, `HouseholdState`,
                              `ProjectsState`, `EconomyState`,
                              `GovernanceState`, `FounderState`,
                              `ScenarioState`, `PopulationState`, and
                              `SimulationState`, plus recursive state
                              serialization/deserialization and v2->v3
                              schema migration.

    engine/economy.py   604-line composition point:
                        `EconomyMixin(GoodsMixin, MaterialSupplyMixin,
                        ElectricityMixin, FreightMixin, MiningMixin,
                        CreditMixin, ProductionMixin)`, plus standing/
                        reputation, project cost and a handful of constants
                        genuinely shared across more than one sub-mixin (see
                        the class's own docstring for exactly which and why).
    engine/economy_goods.py       the goods market: cloth, preserved food,
                                   print, cameras - price that moves (1,106
                                   lines).
    engine/economy_materials.py   raw-material supply: nine hand-named
                                   commodities plus the generic mechanism
                                   covering the rest (945 lines).
    engine/economy_electricity.py electricity as a physical quantity, not a
                                   capability flag (591 lines).
    engine/economy_freight.py     moving a material from source to buyer,
                                   and what the market actually charges once
                                   scarcity, standing and distance are folded
                                   in (670 lines).
    engine/economy_mining.py      mines, deposits, extraction (1,067 lines).
    engine/economy_credit.py      loans, arrears, debt (1,076 lines).
    engine/economy_production.py  revenue, practices, workshops (750 lines).
    engine/prices.py    the price SOLVER (`docs/architecture/
                        ENDOGENOUS_COSTS_AND_DOMAINS.md` Part 2): reads
                        `data/production/` and computes a price for a
                        material from physical recipe data where one is
                        derivable, falling back to `data/prices.json`'s book
                        figure otherwise. Called from `data.py` only, behind
                        `use_solved_prices` (default `False` - every existing
                        call site still calls `load()` with the old
                        behaviour). Not imported by `economy.py` or any
                        economy sub-mixin - "economy.py, which actually
                        spends a price on something, is another agent's file
                        this round," per this file's own docstring. Not a
                        mixin: a standalone module `data.py` calls into.
    engine/commodities.py  commodities as first-class things - iron, wool,
                        coffee, copper, gold and the rest - with their own
                        price/national-output machinery, read from
                        `data/world/commodities.json`. Imported by
                        `economy_materials.py` and `economy_freight.py`.

    engine/labour.py    49-line composition point:
                        `LabourMixin(CapacityMixin, PopulationMixin,
                        WagesMixin, TrainingMixin, BondageMixin)`.
    engine/labour_capacity.py    literacy, institutional and supervisory
                                  ceilings on hiring, teaching, owning or
                                  directing people, plus the founder's own
                                  hour budget (1,263 lines).
    engine/labour_population.py  the local labour market: depth, price
                                  response to recent hiring, population
                                  estimates (626 lines).
    engine/labour_wages.py       what staff cost every year, and what it
                                  costs to be one yourself (299 lines).
    engine/labour_training.py    hiring, firing, teaching, commissioning,
                                  what a technology does to an hour once
                                  bought (703 lines).
    engine/labour_bondage.py     buying people, freeing them, and the pool
                                  bookkeeping that keeps trained/granted
                                  staff honest (350 lines).

    engine/projects.py  202-line composition point:
                        `ProjectsMixin(CapabilityMixin, VenturesMixin,
                        StaffingMixin, StartingMixin, ProgressMixin,
                        CompletionMixin)`, plus constants shared across more
                        than one of the six (see the class's own docstring).
    engine/projects_capability.py  what a capability or institution IS:
                                    built, scaled, still running (292 lines).
    engine/projects_ventures.py    opening/closing a venture by hand: cost,
                                    staff, the two player-typed verbs (421
                                    lines).
    engine/projects_staffing.py    the automatic, year-by-year counterpart:
                                    auto-close, auto-reopen, auto-open,
                                    mothball/restore (859 lines).
    engine/projects_starting.py    whether a project may begin, the
                                    money-for-progress levers, starting and
                                    stopping (915 lines).
    engine/projects_progress.py    what happens to an ACTIVE project every
                                    further year (602 lines).
    engine/projects_completion.py  what finishing or failing a project
                                    actually does, plus the hazard-mitigation
                                    table (449 lines).

    engine/society.py   44-line composition point:
                        `SocietyMixin(HazardsMixin, StatePressureMixin,
                        AdoptionMixin, DiffusionMixin)`.
    engine/society_hazards.py         dated hazards, their timelines, the
                                       losses they cause (1,177 lines).
    engine/society_state_pressure.py  state capacity, scandal, denunciation,
                                       the state's own fiscal/military
                                       interest (1,400 lines).
    engine/society_adoption.py        how THIS population takes up what has
                                       been built (629 lines).
    engine/society_diffusion.py       how what has been built spreads to
                                       imitators and other civilisations
                                       (706 lines).

    engine/hazard_window.py  49 lines: the hazard-timing arithmetic
                        `FogMixin.knowledge_risk` and
                        `HazardsMixin.hazard_timeline` both need (open
                        `civ["hazards"]`, widen a one-element `years` list
                        into a start/end, skip anything already lived past)
                        - one shared function, used by both callers, instead
                        of two drifting copies.
    engine/fog.py       what the player is allowed to see (521 lines).
    engine/geography.py where things are, per civilisation (282 lines).

    engine/actors/household.py  `Household`: the founder's money, staff,
                        knowledge, plant and standing, extracted off `Sim`
                        so a second economic actor (a firm, a government)
                        can use the same class later without importing the
                        whole engine. 339 lines, 68 `__init__` attributes
                        (script under "The runtime graph" below). Its own
                        package (`engine/actors/`) rather than one more
                        module under `engine/`, for the same reason.

    engine/protocol.py  78 lines: a re-export shim, not touched by the
                        mixin split above. `wc -l sim/engine/protocol.py`.
                        The JSON command layer itself is `engine/proto/`,
                        19 real modules (`ls sim/engine/proto/*.py | wc -l`
                        = 21, of which `__init__.py` is one line of package
                        docstring plumbing and `ventures.py` is a 23-line
                        one-constant module).
    engine/proto/dispatch.py            the command table (55 entries -
                        `_AGENT_DISPATCH_TABLE`, several names aliasing the
                        same handler) and the dispatcher that resolves
                        names, guards fog, validates and looks the handler
                        up, plus an import-time assertion tying
                        `KNOWN_COMMANDS` to that table so the two cannot
                        silently drift (655 lines).
    engine/proto/dispatch_inspection.py  read-only inspection commands:
                        state, available, why, path, log, score, risk,
                        values, stuck, mines, capacity, portfolio, economy,
                        changes, population (495 lines).
    engine/proto/dispatch_labour.py      work, allocate, labour, hire, fire,
                        train, commission (461 lines).
    engine/proto/dispatch_money.py       bounty, buy, sell, money, quote,
                        close, withdraw, bribe (455 lines).
    engine/proto/dispatch_ventures.py    start, stop, rush, mothball,
                        restore, open, ventures, policy (733 lines).
    engine/proto/techtree.py    the tech tree through the protocol:
                        why/available, node-explain, subject grouping
                        (1,407 lines).
    engine/proto/state.py       the state/status screen and the event log
                        (1,079 lines).
    engine/proto/economy.py     portfolio, capacity, mines, economy/changes
                        reports (892 lines).
    engine/proto/typed.py       parsing what a person types at `play`'s
                        prompt into the one JSON command dict the protocol
                        already understands (895 lines).
    engine/proto/help.py        the `{"cmd":"help"}` topic tree (484 lines).
    engine/proto/saveload.py    reading, writing and validating a save file;
                        `SAVE_FIELDS` (536 lines).
    engine/proto/score.py       scoring the run, at any point or at the end
                        (415 lines).
    engine/proto/nodes.py       node id/name resolution and small graph
                        queries (190 lines).
    engine/proto/util.py        small dependency-free helpers shared across
                        the package (291 lines).
    engine/proto/ventures.py    one shared supervision-hours explanation, so
                        every screen that shows it agrees (23 lines).
    engine/proto/render.py      33 lines: re-exports the render_* pieces
                        below. Pure presentation - every function reads an
                        already-built reply dict and returns text, never
                        touching the live `Sim` (render.py's own docstring
                        points back at this file for that claim).
    engine/proto/render_screens_big.py     render_state, render_why and the
                        other large per-screen renderers (866 lines).
    engine/proto/render_screens_economy.py render_capacity, render_materials,
                        render_portfolio and the other accounting screens
                        (756 lines).
    engine/proto/render_screens_status.py  render_values, render_final,
                        render_score, render_error, render_stuck, render_risk
                        (399 lines).
    engine/proto/render_typed.py           typed-command rendering and the
                        `--pretty` entry point (175 lines).

    engine/settings.py  where a player's stuff lives on disk, and what they
                        told the menu to remember - config and per-session
                        meta, not part of `SAVE_FIELDS` (536 lines). Read by
                        the CLI layer (`cli.py`, `cli_interactive.py`,
                        `cli_agent.py`, `cli_interactive_saveload.py`), not
                        by the engine mixins.
    engine/cli.py       1,765 lines: argparse and `validate`/`path`/`costs`/
                        `run`/`compare`/`sensitivity`/`sweep`/`goals`, plus
                        shared CLI infrastructure and `main()`. Three more
                        command groups live in their own files, imported at
                        `cli.py`'s own bottom:
    engine/cli_interactive.py  `play`/`civs`/`menu` - the interactive loop
                        (1,513 lines).
    engine/cli_interactive_saveload.py  mid-game save/load browsing and the
                        civilisation list, split out of cli_interactive.py
                        as the near-leaf half of it (295 lines).
    engine/cli_analysis.py     `plan`/`search`/`why` - offline reporting
                        (321 lines).
    engine/cli_agent.py        `agent` mode's CLI entry point (202 lines).

    test_regressions.py a 41-line shim over `sim/tests/`, topic-named
                        modules plus a harness and a runner. `--only
                        <topics>` runs part of it; `--list` names them.
    perf_fingerprint.py proves a change did not alter the simulation.

All line counts above are `wc -l sim/engine/<file>.py` (or
`sim/engine/proto/<file>.py`), run against this HEAD; re-run the same
command against yours before trusting any of them.

**`engine/__init__.py`'s own docstring still describes "six subject
modules"** (data, geography, economy, labour, society, fog, projects, core,
protocol, cli - actually ten, and it was already inexact when written). It
has not been updated to match the shape this file now describes; that is a
`.py` file's own prose, outside this document's ownership, flagged here
rather than silently left to contradict the Layout section above it.

## Two package roots, and what breaks when you forget

`sim/` has no `__init__.py` (`ls sim/__init__.py` fails) - it is a plain
PEP 420 namespace package, not a real one. Two different things put two
different directories on `sys.path`, for two different reasons, and most
processes end up with both on it at once:

- **`sim/` itself.** `simulator.py` inserts its own directory
  (`sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))`) so
  that `engine`, `world` and `data` resolve as bare top-level packages -
  `import engine.core`, not `import sim.engine.core`. `sim/tests/
harness.py` does the same (`HERE`). This is why every bare `from .data
import X` inside `sim/engine/*.py` works: those files load as
  top-level `engine.data`, not `sim.engine.data`.
- **The repository root**, one level up from `sim/`. `sim/
test_regressions.py` adds it (`_ROOT`) so `from sim.tests.__main__
import main` resolves - `sim.tests` is a real package (has
  `__init__.py`), reached through the namespace package `sim`. `sim/
engine/core.py` adds it too, defensively, with its own guarded
  `if _REPO_ROOT not in sys.path` check, because `sim/world/
demography.py` and `sim/world/agriculture.py` import `sim.constants`
  and `sim.world.shared_constants` fully qualified, and a leading `from
..world import demography` inside `engine.core` (loaded bare, as
  established above) has nowhere to go - `engine` has no parent package
  under that scheme, so relative import can't reach `sim.world` from it.

**What breaks:** the same file, imported once through each root, loads
twice, as two separate entries in `sys.modules` (`world.agriculture` and
`sim.world.agriculture`) holding two separate class objects. Nothing
checks this at import time or at `validate`; it surfaces only in a
class-level cache - see `economy_materials.py`'s own CLASS-LEVEL CACHE
comment for a cache that would silently stop hitting if the class it is
keyed to and the class actually running the code drifted apart into two
objects this way. `sim/engine/core.py`'s own header comment works through
this exact case for `sim.world.shared_constants` and imports it fully
qualified on purpose, specifically to avoid loading it a second time under
the bare name. Whoever adds a new cross-package import between `sim/
world/` and `sim/engine/` should read that comment before choosing bare vs.
fully-qualified.

## The import graph is fine

    data.py  (mostly leaf: its own imports of `.prices` are lazy,
             inside `load()`/`goods_provenance()`, not at module top)
      |
      +-- economy_goods, economy_materials, economy_electricity,
      |   economy_freight, economy_mining, economy_credit,
      |   economy_production, labour_capacity, labour_population,
      |   labour_wages, labour_training, labour_bondage,
      |   projects_capability, projects_ventures, projects_staffing,
      |   projects_starting, projects_progress, projects_completion,
      |   society_hazards, society_state_pressure, society_adoption,
      |   society_diffusion, fog, geography      (each -> data only,
      |                                            society_hazards and fog
      |                                            also -> hazard_window)
      |
      +-- economy.py    -> its seven sub-mixins
      +-- labour.py     -> its five sub-mixins
      +-- projects.py   -> its six sub-mixins
      +-- society.py    -> its four sub-mixins
      +-- core_properties.py, core_step_phases.py   (own file, no
      |                                              `.` imports of a sibling
      |                                              mixin)
      |
      +-- core.py       -> data + all eight base classes (economy, fog,
      |                    geography, labour, projects, society,
      |                    core_properties, core_step_phases)
            |
            +-- protocol.py -> proto/ (below)
                  |
                  +-- proto/*.py -> data, and (help.py, techtree.py) -> core,
                  |                 and (techtree.py, fog.py's caller) -> fog
                  |
                  +-- cli.py -> core, data, protocol, settings, then at its
                                own bottom cli_interactive, cli_agent,
                                cli_analysis
                        |
                        +-- cli_interactive.py -> core, data, protocol,
                            settings, cli, cli_interactive_saveload
                        +-- cli_analysis.py -> core, data, cli
                        +-- cli_agent.py -> core, data, protocol, settings, cli

Checked by grepping every file's own `from .`/`from ..` lines (the command
below); re-run it whenever a file moves:

    grep -n "^from \.\|^from \.\." sim/engine/*.py sim/engine/proto/*.py

No sub-mixin imports another sub-mixin, another top-level composition
point, or `core` - they would cycle if they did, so the import graph tells
you almost nothing about what actually depends on what. That is the trap
this document exists to spring, and it is exactly as true of the
twenty-two current sub-mixins (economy's seven, labour's five, projects'
six, society's four) as it was of the original eight: see "The
composition-point pattern" below.

## The runtime graph is one god object

`Sim` assigns **44** instance attributes on `self` in `__init__`
(**45** anywhere in the class body - one more, `goal`, is assigned by
`run()` rather than `__init__`, so a `Sim` built directly and never run
does not have it yet. `sim.tests.harness.sim()`, the fixture the test
suite builds every `Sim` from, does not call `run()` either; it pokes
`test_sim.goal` directly right after construction, so a harness-built
instance also ends up with all 45, by a different route than `run()`'s
own assignment; `vars()` on a `sim.tests.harness.sim()` instance gives
exactly this same 45-name set, confirming both routes land on the same
attributes -
`(cd sim && python3 -c "from tests.harness import sim; print(len(vars(sim())))")`).
It carries **90**
properties (87 `@property`/`@x.setter` pairs in `core_properties.py`'s
`ForwardingPropertiesMixin`, forwarding to `self.household`/
`self.population`; 2 more, `pop_scale` and `wage_index`, that stayed in
`core.py` itself because each computes a value from more than one `Sim`
attribute rather than one-line-forwarding a single field, and moving them
would put real logic in a file whose whole point is that everything in it
is inert boilerplate; 1 more, `mine_capacity`, defined on `MiningMixin` in
`economy_mining.py`). `Household` (`sim/engine/actors/household.py`) holds
**68** of its own `__init__` attributes.

    python3 - <<'EOCOUNT'
    import ast
    def self_init_attrs(filepath, class_name):
        code = open(filepath).read()
        tree = ast.parse(code)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                        attrs = set()
                        for n in ast.walk(item):
                            if isinstance(n, (ast.Assign, ast.AnnAssign)):
                                targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                                for t in targets:
                                    if (isinstance(t, ast.Attribute)
                                            and isinstance(t.value, ast.Name)
                                            and t.value.id == 'self'):
                                        attrs.add(t.attr)
                        return len(attrs)
    print("Sim.__init__ attrs:", self_init_attrs('sim/engine/core.py', 'Sim'))
    print("Household.__init__ attrs:", self_init_attrs('sim/engine/actors/household.py', 'Household'))
    EOCOUNT

    grep -c "^    @property" sim/engine/core_properties.py   # 87
    grep -c "\.setter$" sim/engine/core_properties.py        # 87
    grep -c "^\s*@property" sim/engine/core.py                # 2 (pop_scale, wage_index)
    grep -c "^\s*@property" sim/engine/economy_mining.py      # 1 (mine_capacity)

`Household` exists because the founder's money, staff, knowledge,
inventory and standing left `Sim` for `sim/engine/actors/household.py`
(`docs/architecture/HOUSEHOLD_EXTRACTION.md`); what stayed directly on
`Sim` is the world, the scenario, and a handful of fields biographical to
one mortal person (`founder_alive`, `life_left`, `dead_reason` and kin)
that have no meaning for a government or a firm and are waiting for a
second actor to say what they should become.
`docs/architecture/SIM_STATE_INVENTORY.md` has a broader "everything `Sim`
CARRIES" count (adding attributes assigned outside `__init__`, ones reached
only as `s.X` from `engine/proto/`, and ones hidden behind
`self.__dict__[...]`) - it is not scripted anywhere, so treat any total it
gives as unverifiable against today's build rather than re-deriving one by
arithmetic on it, the same caution CLAUDE.md SS7 gives for the naming
counts.

## The composition-point pattern

Splitting a large mixin into sub-mixins does not touch `class Sim(...)` in
`core.py`. `economy.py` still defines a class called `EconomyMixin` -
`labour.py` a `LabourMixin`, `projects.py` a `ProjectsMixin`, `society.py`
a `SocietyMixin` - each now one line of inheritance
(`class EconomyMixin(GoodsMixin, MaterialSupplyMixin, ElectricityMixin,
FreightMixin, MiningMixin, CreditMixin, ProductionMixin)`) standing in for
what would otherwise be a few thousand lines of methods on one class.

`core_properties.py` and `core_step_phases.py` are the same move at one
level up: instead of introducing a new composition point beneath an
existing mixin, a self-contained block was cut straight out of `core.py`'s
own `class Sim(...)` body into a sibling file as its OWN mixin
(`ForwardingPropertiesMixin`, `StepPhasesMixin`), and `Sim`'s base list grew
by one name each time, rather than being rewritten. Either shape keeps the
same property: nobody has to touch the line that names `Sim`'s own bases
(or a composition point's own bases) to move code out from under it.

This is the pattern to use for every future split of a class that has
grown too large: pick the class Python already resolves methods through,
keep its name and its place in whatever base list it appears in fixed, and
move its method bodies out to sibling files it either inherits from (a new
sub-mixin under an existing composition point) or that `Sim` inherits
directly (a new mixin lifted whole out of `core.py`). The alternative -
renaming or replacing a mixin in `Sim`'s base list, or splitting `Sim`
itself into several classes - would put a line inside `core.py`'s
`class Sim(...)` statement in the diff of every future split. Two agents
splitting different domains in the same week would then collide on the
same line for reasons that have nothing to do with each other. Composing
beneath (or lifting out into) a fixed name means a split of, say,
`labour_capacity.py` next month touches that file and whatever new file it
creates, and nothing in `core.py`'s own base-list line at all.

It costs nothing at runtime: Python's MRO resolves a method on
`MaterialSupplyMixin` through `EconomyMixin` through `Sim`, or a property on
`ForwardingPropertiesMixin` through `Sim` directly, exactly as it would if
the method or property were written on `Sim` itself - every mixin's `self`
is still the same one `Sim` instance it always was. This pattern does not
touch the "runtime coupling is total" problem, and was never meant to.

## The method count

`Sim` and everything it inherits from have **537** methods between them
(every `FunctionDef`/`AsyncFunctionDef` directly in a class's own body, so
a `@property` getter and its `@x.setter` each count once - `core_properties.py`'s
174 entries below are 87 pairs):

    Sim                        19   (own methods only: __init__, step, and
                                      the threshold-goal/starting-tech
                                      machinery that stayed in core.py)
    ForwardingPropertiesMixin 174   (87 @property + 87 @x.setter)
    StepPhasesMixin             19   (14 named _step_* phases + 5 progress
                                      helpers under _step_progress - see
                                      "Sim.step()" below)
    EconomyMixin                10   composed of:
      GoodsMixin                13
      MaterialSupplyMixin       21
      ElectricityMixin           7
      FreightMixin              14
      MiningMixin                29
      CreditMixin                11
      ProductionMixin           16    (economy total: 111, +10 own = 121)
    LabourMixin                  0   composed of:
      CapacityMixin              15
      PopulationMixin            15
      WagesMixin                  4
      TrainingMixin              11
      BondageMixin                 5    (labour total: 50)
    ProjectsMixin                 0   composed of:
      CapabilityMixin             6
      VenturesMixin               11
      StaffingMixin               14
      StartingMixin               26
      ProgressMixin               13
      CompletionMixin              1    (projects total: 71)
    SocietyMixin                  0   composed of:
      HazardsMixin                21
      StatePressureMixin          17
      AdoptionMixin                11
      DiffusionMixin               20    (society total: 69)
    FogMixin                       8
    GeographyMixin                  6
    TOTAL                          537

**A method-counting script must walk into a composition point's
sub-mixins, or it will silently undercount** - `EconomyMixin`,
`LabourMixin`, `ProjectsMixin` and `SocietyMixin` define 10, 0, 0 and 0
methods respectively in their OWN class bodies; the other 517 live one
level down. That is the sub-mixin trap in numeric form, and it is exactly
as real for these twenty-two sub-mixins as it was for the original eight:
an import-clean split can make a perfectly good script quietly start
undercounting.

    python3 - <<'EOCOUNT'
    import ast
    def count_class_methods(filepath, class_name):
        with open(filepath) as f:
            tree = ast.parse(f.read())
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return len([item for item in node.body
                            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))])
        raise SystemExit("class %s not found in %s" % (class_name, filepath))
    pieces = [
        ('sim/engine/core.py', 'Sim'),
        ('sim/engine/core_properties.py', 'ForwardingPropertiesMixin'),
        ('sim/engine/core_step_phases.py', 'StepPhasesMixin'),
        ('sim/engine/economy.py', 'EconomyMixin'),
        ('sim/engine/economy_goods.py', 'GoodsMixin'),
        ('sim/engine/economy_materials.py', 'MaterialSupplyMixin'),
        ('sim/engine/economy_electricity.py', 'ElectricityMixin'),
        ('sim/engine/economy_freight.py', 'FreightMixin'),
        ('sim/engine/economy_mining.py', 'MiningMixin'),
        ('sim/engine/economy_credit.py', 'CreditMixin'),
        ('sim/engine/economy_production.py', 'ProductionMixin'),
        ('sim/engine/labour.py', 'LabourMixin'),
        ('sim/engine/labour_capacity.py', 'CapacityMixin'),
        ('sim/engine/labour_population.py', 'PopulationMixin'),
        ('sim/engine/labour_wages.py', 'WagesMixin'),
        ('sim/engine/labour_training.py', 'TrainingMixin'),
        ('sim/engine/labour_bondage.py', 'BondageMixin'),
        ('sim/engine/projects.py', 'ProjectsMixin'),
        ('sim/engine/projects_capability.py', 'CapabilityMixin'),
        ('sim/engine/projects_ventures.py', 'VenturesMixin'),
        ('sim/engine/projects_staffing.py', 'StaffingMixin'),
        ('sim/engine/projects_starting.py', 'StartingMixin'),
        ('sim/engine/projects_progress.py', 'ProgressMixin'),
        ('sim/engine/projects_completion.py', 'CompletionMixin'),
        ('sim/engine/society.py', 'SocietyMixin'),
        ('sim/engine/society_hazards.py', 'HazardsMixin'),
        ('sim/engine/society_state_pressure.py', 'StatePressureMixin'),
        ('sim/engine/society_adoption.py', 'AdoptionMixin'),
        ('sim/engine/society_diffusion.py', 'DiffusionMixin'),
        ('sim/engine/fog.py', 'FogMixin'),
        ('sim/engine/geography.py', 'GeographyMixin'),
    ]
    total = sum(count_class_methods(fname, cname) for fname, cname in pieces)
    print(total)
    EOCOUNT

This list is a hardcoded file/class pairing: if any file on it stops
existing, the script raises `FileNotFoundError` rather than silently
printing a wrong number - at least honest, per CLAUDE.md's own standard
for a script that breaks, but a break all the same. Whoever adds or
removes a sub-mixin file must add or remove its
line here, or this script will either crash cleanly (a file removed) or
silently undercount (a file added and forgotten). There is no way to
derive this list automatically without walking `Sim`'s actual MRO at
runtime instead of parsing source, which would answer a different, also
useful, question - "what does a live `Sim` actually resolve a method
through" - rather than this one - "how many methods did the source commit".

This is a distributed god object. It is also, honestly, a defensible shape
for this problem: money genuinely does affect labour, which affects what
can be built, which affects reputation, which affects money. Those
couplings are the domain, not an accident. Moving the state into a `State`
object passed to free functions would relocate the coupling, not remove
it.

**Coupling, re-measured against the current file set** (a regex-based
approximation - `self\.(\w+)\(` for calls, `self\.(\w+)` for any touch -
grouped by subsystem folder, so it undercounts anything routed through a
local alias rather than `self.` directly, but needs no hand-maintained
call graph and is cheap to re-run after any split):

    core      -> economy    62        society  -> projects   29
    economy   -> projects   43        labour   -> projects   30
    core      -> labour     39        projects -> labour     19
    projects  -> economy    32        core     -> projects   13

Distinct `self.*` names touched per subsystem: economy 271, core 234,
society 213, projects 158, labour 135, fog 16, geography 13. `economy` and
`core` touch the most distinct names because standing/reputation and the
year's own phase sequence both reach into every other subsystem's state at
some point; `fog` and `geography` touch the fewest because each answers a
narrower question (what can the player see; where is it) that mostly
depends on the tree and the civilisation record, not on the other
subsystems' running state.

    python3 - <<'EOCOUNT'
    import ast, os, re, collections
    groups = {
        'core': ['core.py', 'core_properties.py', 'core_step_phases.py'],
        'economy': ['economy.py', 'economy_goods.py', 'economy_materials.py',
                    'economy_electricity.py', 'economy_freight.py',
                    'economy_mining.py', 'economy_credit.py', 'economy_production.py'],
        'labour': ['labour.py', 'labour_capacity.py', 'labour_population.py',
                   'labour_wages.py', 'labour_training.py', 'labour_bondage.py'],
        'projects': ['projects.py', 'projects_capability.py', 'projects_ventures.py',
                     'projects_staffing.py', 'projects_starting.py',
                     'projects_progress.py', 'projects_completion.py'],
        'society': ['society.py', 'society_hazards.py', 'society_state_pressure.py',
                    'society_adoption.py', 'society_diffusion.py'],
        'fog': ['fog.py'], 'geography': ['geography.py'],
    }
    base = 'sim/engine'
    defined_in = collections.defaultdict(set)
    for group, files in groups.items():
        for fn in files:
            tree = ast.parse(open(os.path.join(base, fn)).read())
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            defined_in[item.name].add(group)
    call_re = re.compile(r'self\.([A-Za-z_]\w*)\s*\(')
    attr_re = re.compile(r'self\.([A-Za-z_]\w*)')
    cross_calls, distinct_touched = collections.Counter(), collections.defaultdict(set)
    for group, files in groups.items():
        for fn in files:
            src = open(os.path.join(base, fn)).read()
            distinct_touched[group].update(attr_re.findall(src))
            for name in call_re.findall(src):
                for tg in defined_in.get(name, set()):
                    if tg != group:
                        cross_calls[(group, tg)] += 1
    for g, names in sorted(distinct_touched.items(), key=lambda kv: -len(kv[1])):
        print(g, len(names))
    for (a, b), c in cross_calls.most_common(12):
        print(a, '->', b, c)
    EOCOUNT

No mixin could be constructed, tested or reasoned about on its own, and
the mixin split does not change that; it moves code into more files
without decoupling it (see "The one-paragraph version" above).

**A full decomposition has been considered and rejected**, with reasons,
so that the next person does not silently restart it:

- it means giving every shared field an explicit owner and converting the
  couplings mixins currently reach through `self` into arguments, a
  rewrite of most of the engine;
- the safety net does not fully exist for it. `perf_fingerprint.py`
  covers the simulation loop well and covers `protocol.py` not at all,
  and roughly a quarter of the engine's code lives under `engine/proto/`
  (11,246 of 41,746 lines, 27% -
  `find sim/engine/proto -name "*.py" | xargs wc -l | tail -1` against
  `find sim/engine -name "*.py" -not -path "*/__pycache__/*" | xargs wc -l | tail -1`);
- the payoff is small, for the reason above - the couplings are the
  domain.
  If you disagree, the bar is: propose it with a plan for proving
  `protocol.py` unchanged, because that is the part nothing currently
  guards.

## What IS worth restructuring

Code lines, counted as **lines that are neither blank nor comment-only**
(docstrings count as code under this rule). The composition points
(`economy.py` 604, `labour.py` 49, `projects.py` 202, `society.py` 44) are
thin now, so they are not among the largest files any more; the table below
lists the **eight largest files under `sim/engine/` (including
`engine/proto/`) by total line count**, found fresh rather than assumed:

    find sim/engine -name "*.py" -not -path "*/__pycache__/*" \
        | xargs wc -l | sort -rn | grep -v " total$" | head -8

    core.py                       2,273 total
    cli.py                        1,765 total
    core_step_phases.py           1,756 total
    cli_interactive.py            1,513 total
    proto/techtree.py             1,407 total
    society_state_pressure.py     1,400 total
    labour_capacity.py            1,263 total
    society_hazards.py            1,177 total

Both comment-density rules, scripted against exactly those eight files (the
list has to travel with the number, because which eight files are "largest"
changes as the code is split further):

    python3 - <<'EOCOUNT'
    import ast
    engine_files = ["sim/engine/core.py", "sim/engine/cli.py",
                    "sim/engine/core_step_phases.py", "sim/engine/cli_interactive.py",
                    "sim/engine/proto/techtree.py", "sim/engine/society_state_pressure.py",
                    "sim/engine/labour_capacity.py", "sim/engine/society_hazards.py"]
    for path in engine_files:
        source = open(path).read()
        lines = source.splitlines()
        blank_or_comment = sum(1 for line in lines
                               if not line.strip() or line.strip().startswith("#"))
        docstring_lines = set()
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, (ast.Module, ast.ClassDef,
                                     ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if ast.get_docstring(node, clean=False) is None:
                continue
            opening_statement = node.body[0]
            docstring_lines.update(range(opening_statement.lineno,
                                         opening_statement.end_lineno + 1))
        print("%-30s %6d total %5.0f%% doc-as-code %5.0f%% doc-as-doc"
              % (path, len(lines),
                 100.0 * blank_or_comment / len(lines),
                 100.0 * (blank_or_comment + len(docstring_lines)) / len(lines)))
    EOCOUNT

    file                          total   doc-as-code   doc-as-doc
    core.py                       2,273          32%          59%
    cli.py                        1,765          29%          42%
    core_step_phases.py           1,756          57%          58%
    cli_interactive.py            1,513          22%          38%
    proto/techtree.py             1,407          38%          56%
    society_state_pressure.py     1,400          15%          35%
    labour_capacity.py            1,264          31%          45%
    society_hazards.py            1,177          33%          51%

(`labour_capacity.py` prints 1,264 lines here against `wc -l`'s 1,263 in
the table above it: the file's last line has no trailing newline, which
`wc -l` does not count and Python's `splitlines()` does. Both commands ran;
neither is wrong, they are counting slightly different things.)

**One of eight is majority comment counting docstrings as CODE**
(`core_step_phases.py`, 57%: it is fourteen phase methods, each carrying
inline the reasoning for what that phase does and why it runs where it
does in the year's order - moving the phases out of `step()` moved that
reasoning with them, rather than leaving it behind). **Four of eight are
majority comment counting docstrings as DOCUMENTATION**: `core.py` (59%),
`core_step_phases.py` (58%), `proto/techtree.py` (56%) and
`society_hazards.py` (51%). The two rules disagree with each other on
three of the eight (`core.py`, `proto/techtree.py` and `society_hazards.py`
cross the 50% line only under the doc-as-documentation rule, staying under
it as code) for the reason the rule has to travel with the number at all: a
substantial share of what looks like "comment" in each of these files is a
docstring carrying real reasoning, not a `#`-prefixed aside, and whether
that counts as documentation or as code is a genuine judgement call with
no single right answer. The comments are how agents hand each other the
reason a thing is the way it is; they are load-bearing, and must not be
stripped to "clean up" regardless of which way a percentage falls.

`test_regressions.py` and `protocol.py` are split for cyclomatic reasons,
not line-count ones. `protocol.py` itself is a 78-line re-export shim; the
command dispatcher lives in `engine/proto/dispatch.py`, as
`_agent_dispatch_inner` - a single function that resolves a command name
against `_AGENT_DISPATCH_TABLE` (55 dict entries, several names aliasing
one handler - read the dict literal in that file directly to see which)
and an import-time assertion tying that table to `KNOWN_COMMANDS` so the
two cannot drift, rather than a flat `if`/`elif` chain over every command:

    python3 - <<'EOCOUNT'
    import ast
    src = open('sim/engine/proto/dispatch.py').read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == '_agent_dispatch_inner':
            complexity = 1
            for n in ast.walk(node):
                if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler)):
                    complexity += 1
                if isinstance(n, ast.BoolOp):
                    complexity += len(n.values) - 1
            print("lines:", node.end_lineno - node.lineno + 1)
            print("approx McCabe complexity:", complexity)
    EOCOUNT

gives 146 lines and an approximate McCabe complexity of 27 for the function
that resolves a command once its own handler is looked up from the table -
the dict itself, not this function, is what actually grew to 55 entries as
commands were added; this script measures only the resolution logic that
stays constant size regardless of how many commands the table holds.

`test_regressions.py` was a flat script, so checks ran at import in file
order and nothing could be run selectively. `--only mines,demographics`
runs a handful of checks in about a second where the whole suite runs
**2,141** checks in the time printed at its own end (12 slow checks
skipped, 3 slow topics not run):

    python3 sim/test_regressions.py --only mines,demographics 2>&1 | tail -1
    python3 sim/test_regressions.py 2>&1 | tail -1

Measure the full-suite figure against a clean checkout of HEAD rather than
a working tree with other agents' edits in it: a single uncommitted test
file shifts the count. In a SHALLOW clone
(`git rev-parse --is-shallow-repository` says true), one check fails here
that does not fail in a full clone: the byte-identical rename-safety proof
needs `git show <rev>:<path>` for a commit the shallow history does not
have, and reports "is this checkout shallow?" when it cannot get it. That
is the checkout, not the code - confirm with
`git rev-parse --is-shallow-repository` before treating a lone failure
there as a regression.

The engine mixins were left alone for line-count purposes; splitting them
further by line count alone would move prose between files and buy
nothing. What moved `core_step_phases.py` and the properties out of
`core.py` was the same cyclomatic reasoning as `protocol.py`'s split, not a
line-count target - see "`Sim.step()`" below.

## `Sim.step()`

`step()` stayed in `core.py` and is **43 lines**
(`python3 -c` below) that call, in the same order the phases always ran
in, **14** extracted `_step_*` phase methods now living in
`core_step_phases.py`'s `StepPhasesMixin`: `_step_apprenticeships`,
`_step_staff`, `_step_money`, `_step_dated_shocks`, `_step_teach_trades`,
`_step_standing_work_directive`, `_step_start_projects`, `_step_materials`,
`_step_progress_project`, `_step_progress`, `_step_wage_fallback`,
`_step_reputation`, `_step_bondage`, `_step_founder_mortality`. Each phase
still reads and writes exactly the `self.*` state it always did; only a
handful of values cross phase boundaries as arguments and return values
instead of through `self`: `pool`/`hired_left` from `_step_start_projects`
into `_step_progress`; `remaining`/`remaining_after_projects`/
`hours_effective_total` from `_step_progress` into `_step_wage_fallback`
and `_step_reputation`. This is a line-count and cyclomatic-complexity fix,
not a coupling fix - the "runtime coupling is total" fact applies to the 14
phase methods exactly as it applied to the one method they replaced,
because they are still all reading and writing `self`.

    python3 - <<'EOCOUNT'
    import ast
    source = open('sim/engine/core.py').read()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'step':
            print("step() total lines:", node.end_lineno - node.lineno + 1)

    source2 = open('sim/engine/core_step_phases.py').read()
    tree2 = ast.parse(source2)
    names = [n.name for n in ast.walk(tree2)
             if isinstance(n, ast.FunctionDef) and n.name.startswith('_step_')]
    print("_step_* count:", len(names))
    EOCOUNT

That count includes `_step_progress_project`, a per-project helper called
from inside `_step_progress` rather than from `step()` directly; it shares
the `_step_` prefix and lives in the same file as the fourteen phases
`step()` itself calls, which is why both the script above and `step()`'s
own comment name it alongside them. `core_step_phases.py` also holds five
smaller,
unprefixed helpers used only from within `_step_progress`
(`_project_progress_trade_gate`, `_project_progress_offer_hours`,
`_project_progress_labour_and_bill`, `_project_progress_afford_gate`,
`_project_progress_finish`) - together with the 14 `_step_*` methods, that
is `StepPhasesMixin`'s 19 methods in "The method count" above.

## Where the data lives, and who reads it

    data/tech_tree.json    2.8 MB, 2,864 nodes (its top-level "nodes" key
                           holds a JSON list, not an object keyed by id -
                           `len()` on it still gives the node count).
                           data.py loads it; core, economy, projects,
                           settings, cli read it through data. treetool.py
                           writes it.

                           python3 -c "import json; print(len(json.load(open('data/tech_tree.json'))['nodes']))"
    data/prices.json       the book prices data.py always loads as a
                           fallback. Read directly by data.py; consulted
                           (not yet spent by economy.py - see below) by
                           `sim/engine/prices.py`'s solver.
    data/production/       physical recipe data (yields, stoichiometry,
                           ore grades) `sim/engine/prices.py` reads to
                           compute a price instead of looking one up, when
                           `data.py`'s `load(use_solved_prices=True)` or
                           `goods_provenance()` is asked for it.
                           `use_solved_prices` defaults to `False`, and
                           `economy.py` and its sub-mixins - the code that
                           actually SPENDS a price on something - do not
                           call either function, so the running engine's
                           behaviour is unchanged by this file existing;
                           it is wired into `data.py` as a measurable,
                           opt-in burndown of `prices.json`, not yet into
                           what a game actually charges. See
                           `sim/engine/prices.py`'s own docstring and
                           `docs/architecture/ENDOGENOUS_COSTS_AND_DOMAINS.md`
                           Part 2.

                           python3 sim/audit_costs.py --materials
    data/civilizations/    five playable civs. data.py, cli.py.
    data/world/            geography and commodities. data.py, geography.py,
                           commodities.py.
    data/branches/         authoring input, merged into the tree by
                           treetool.py: **40** files
                           (`ls data/branches/*.json | wc -l`).
    data/judgement.json    written by `treetool.py judge`. READ BY NOTHING.
                           A report artifact that is committed.

## Four things that will bite you

**The tree tools write to the repository.** `treetool.py merge|judge|repair|
apply-caps` each rewrite a committed data file, and `judge` in particular
reads like a report command while doing so. Every subcommand now reports by
default and writes nothing; `--write` is what commits the result
(`ls -la data/judgement.json` to see whether it did).

**Green tests do not mean unchanged behaviour.** The suite asserts on
outputs and messages. It does not assert that the simulation is the same
simulation. An "obviously safe" cleanup - promoting `getattr(self, x,
default)` calls to real `__init__` attributes - once passed the entire
suite while silently breaking save-file semantics, because several of
those names are in `SAVE_FIELDS` where a _missing_ attribute is
meaningful; `Household.__init__`'s own docstring (`sim/engine/actors/
household.py`) still calls this out by name for exactly the fields it
deliberately leaves unassigned. `perf_fingerprint.py` catches this
class of bug and the suite alone does not. Run it:

    python3 sim/perf_fingerprint.py record before.json
    ...make your change...
    python3 sim/perf_fingerprint.py check before.json

It hashes every field of state after every year of nine runs across five
civilisations, fog on and off, and names the first year that differs. It
does NOT cover `topo_order`, `protocol.py`, or anything outside the
simulation loop - those need their own proof.

**An import-time check cannot catch a bare module-global reference that
moved.** A class object used as a process-wide cache slot - a bare name,
read and written at call time, not through `self` and not through an
import alias - breaks silently if that class moves to another file:
`import simulator` still succeeds, `sim/simulator.py validate` still
passes, every module still compiles, because none of those checks execute
the line that reads the name. `economy_materials.py`'s own CLASS-LEVEL
CACHE comment names three of its own methods that would break exactly
this way if moved without updating the class name their cache is keyed
to. Only a command that actually runs that code path raises the
`NameError`. A split is not verified until something runs the code, not
just imports it. The cheapest thing that does:

    echo '{"cmd": "state"}' | python3 sim/simulator.py agent --civ rome_100ad

**Tests that read source text with `inspect.getsource` test prose shape,
not behaviour.** `grep -rln "getsource" sim/tests/ --include="*.py"` names
them - nine as of this HEAD. Each asserts on the literal text of a
function body, so moving code between methods can break one of these
while the property it guards still holds. `test_affordability_warning.py`
reads `step()` concatenated with every `_step_*` phase method on `Sim`
(now split across `core.py` and `core_step_phases.py`), not `step()`
alone, precisely because the phrase it looks for can live in either.
Whoever next moves code between methods should run that grep first, not
discover the list from a failure.

## Authoritative Simulation State & Subsystem Ownership

Historically, `Sim` was a massive object whose state was mixed into a shared namespace across mixins, with active project progress tracked via unstructured `Dict[str, Any]` and save/load maintained via a handwritten 102-field tuple (`SAVE_FIELDS`).

The canonical architecture partitions persistent simulation state into authoritative typed dataclasses in `sim/engine/state.py`, with clear subsystem ownership boundaries:

| State Class       | Subsystem Domain                    | Authoritative Owner               | Key State Responsibilities                                                                    |
| ----------------- | ----------------------------------- | --------------------------------- | --------------------------------------------------------------------------------------------- |
| `HouseholdState`  | Founder finances & household        | `sim.household` (`Household`)     | Capital, wages, debt/bondage, reputation, standing, workforce (`employees`), training         |
| `ProjectsState`   | Technology research & ventures      | `ProjectsMixin` / `sim.household` | Active projects (`active`), completed tech (`done`), `operating`, `mothballed`, `opened_year` |
| `EconomyState`    | Physical plants & flows             | `EconomyMixin`                    | Extraction workings (`mines`), material stock, shortages, market pressure, output factor      |
| `GovernanceState` | Civic institutions & administration | `Sim` / `GovernanceMixin`         | Scaled civic units (`inst_units`), administrative capacity (`gov`)                            |
| `FounderState`    | Biological founder status           | `Sim`                             | Biological lifespan (`life_left`), founder survival (`founder_alive`), living costs           |
| `ScenarioState`   | Timeline & scenario context         | `Sim`                             | Simulation year (`year`), goal completion (`goal_year`), milestone warnings (`_said_*`)       |
| `PopulationState` | World demography & agriculture      | `sim.population` / `LabourMixin`  | Population brackets (`pop_children`, `pop_working_age`, `pop_elderly`), food bonus            |
| `SimulationState` | Root state coordinator              | `Sim`                             | Aggregates all subsystem states, civ identity (`_civ`), goal, fog of war, RNG state           |

## Authoritative Simulation State & Live Subsystem Ownership

The simulation architecture clearly separates **behavior and coordination**, **persistent authoritative state**, **transient derived state**, and **serialization**.

### 1. Architectural Roles

- **Behavior / Coordination (`Sim`)**: `Sim` is the coordinator and behavior engine. It orchestrates year advancement (`step()`), phase dispatch, player and automated policies, and high-level interaction between domains. `Sim` does not maintain a second copy of persistent state.
- **Persistent Authoritative State (`SimulationState`)**: `sim.state` is the single live authoritative repository of mutable simulation data. Persistent data is owned by typed dataclasses grouped by domain. There is exactly one storage location for each persistent field.
- **Transient Derived State**: Version counters (`_operating_ver`, `_done_ver`, `_active_ver`, `_workforce_ver`, `_inst_units_ver`), memoization caches (such as `_revenue_cache`, `_goods_mkt_op_factor_cache`, `_annual_mat_demand_cache`), and container invalidation listeners (`_InvalidatingSet`, `_InvalidatingDict`) are transient. They are excluded from serialization and cleanly reconstructed on load via `sim._reconnect_state_hooks()`.
- **Serialization & Deserialization**: Save/load operates directly on the live `SimulationState` without duplicate snapshot extraction or copying. Serialization is generic and type-driven: declared Python dataclass field types determine how fields are serialized and reconstructed, so adding a standard persistent field requires editing only the dataclass definition.

### 2. Domain & Runtime Ownership Hierarchy

The running simulation owns a live `SimulationState` instance (`sim.state`) which holds the authoritative subsystem state objects:

| Domain                  | Runtime owner                              | Description & Authoritative Fields                                                                  |
| ----------------------- | ------------------------------------------ | --------------------------------------------------------------------------------------------------- |
| household finances      | `HouseholdState` (`sim.state.household`)   | Capital, wages, debt, bondage, reputation, standing, workforce (`employees`), training              |
| projects                | `ProjectsState` (`sim.state.projects`)     | Active projects (`active`), completed tech (`done`), `operating`, `mothballed`, `opened_year`       |
| economy / resources     | `EconomyState` (`sim.state.economy`)       | Extraction workings (`mines`), material stocks, shortages, market pressure, output factor, farmland |
| governance              | `GovernanceState` (`sim.state.governance`) | Scaled civic units (`inst_units`), administrative capacity (`gov`)                                  |
| founder                 | `FounderState` (`sim.state.founder`)       | Biological lifespan (`life_left`), founder survival (`founder_alive`), living costs                 |
| timeline / scenario     | `ScenarioState` (`sim.state.scenario`)     | Simulation year (`year`), goal completion (`goal_year`), milestone warnings (`_said_*`)             |
| population              | `PopulationState` (`sim.state.population`) | Demography cohorts (`pop_children`, `pop_working_age`, `pop_elderly`), food bonus                   |
| coordination / behavior | `Sim`                                      | Step execution, dispatch phases, automation policies, runtime mixins                                |

### ActiveProjectState

`ActiveProjectState` replaces loose `Dict[str, Any]` entries in `household.active`. It inherits from `_InvalidatingDict` and provides:

- Explicit typed attributes (`ph_left`, `cost_left`, `lab_left`, `spent`, `directed_ph_this_year`, `arrears_hours_lost`, `hired_ph_used`, `yrs`)
- Full backward-compatible dictionary mapping interface (`proj["ph_left"]`, `proj.get(...)`, `.items()`, `|=`, `.pop()`, etc.)
- Automatic cache invalidation: any mutation to an active project's fields or nested dicts automatically bubbles up and increments `sim.household._active_ver`, invalidating memoized revenue and material demand caches.

### Automatic Serialization (No Legacy Migration)

Save/load is derived directly from authoritative state definitions:

- `SAVE_FIELDS`: Generated dynamically from dataclass fields (`get_save_fields()`), guaranteeing zero field drift without maintaining handwritten field lists.
- `serialize_state`: Recursively serializes dataclasses, typed sets (`{"__set__": [...]}`), Counter/defaultdict, and `ActiveProjectState`.
- `deserialize_state`: Reconstructs typed dataclasses and runtime invalidating wrappers (`_InvalidatingSet`, `_InvalidatingDict`).
- No save migration: Saves from older format versions are refused with a clear error per project policy (CLAUDE.md §3.5), avoiding migration shims and format drift.

### 3. Compatibility Façade & Invalidation

To preserve existing callers and compatibility while enforcing a single authoritative source of truth:

- `ForwardingPropertiesMixin` (`sim/engine/core_properties.py`) provides 106 forwarding properties on `Sim` that delegate directly to `self.state.<subsystem>.<field>`.
- `Household` (`sim/engine/actors/household.py`) serves as a live façade delegating property and attribute access directly to `self._state.<subsystem>`.
- `ActiveProjectState` provides typed attributes, dictionary compatibility, and deep change notification bubbling to `self.state.projects._active_ver`.
- Invalidation hooks and version counters attach directly to the respective subsystem state owners (`ProjectsState`, `HouseholdState`, `GovernanceState`).

### 4. Automatic Type-Driven Serialization

- **Save**: `save_state(sim, path)` directly serializes `sim.state` to structured nested v3 JSON format.
- **Load**: `load_state(sim, path)` validates v3 structural schema, deserializes into `sim.state` using generic type introspection (`dataclasses.fields`, `typing.get_origin`, `typing.get_args`), and calls `sim._reconnect_state_hooks()` to reattach transient invalidation listeners and version counters.

## Direct Subsystem Live State Ownership & Internal Access Rules

### 1. Internal Engine State Access Architecture

All internal simulation code across all engine mixins (`sim/engine/geography.py`, `fog.py`, `economy_*.py`, `labour_*.py`, `projects_*.py`, `society_*.py`, `core_step_phases.py`, and `core.py`) accesses persistent live simulation state exclusively through its authoritative subsystem owner:

- `sim.state.household` (`HouseholdState`): Capital, workforce, wages, financial ledgers, debt, standing, and household capacity.
- `sim.state.projects` (`ProjectsState`): Active, done, revealed, operating, mothballed, and shut projects, attempts, and work trackers.
- `sim.state.economy` (`EconomyState`): Extraction workings (`mines`), material stocks, shortages, market pressure, output factor, farmland, and energy.
- `sim.state.governance` (`GovernanceState`): Scaled civic institution units (`inst_units`) and state interest/quality (`gov`).
- `sim.state.founder` (`FounderState`): Founder biological lifespan (`life_left`), health/survival (`founder_alive`), living costs, and operating policies.
- `sim.state.scenario` (`ScenarioState`): Simulation progression (`year`), win criteria (`goal_year`), milestone warnings, and debasement tracking.
- `sim.state.population` (`PopulationState`): Civilisation demographic cohorts (`pop_children`, `pop_working_age`, `pop_elderly`) and agricultural bonuses.

### 2. Internal Access Rules & Invariants

1. **No Cross-Subsystem Delegation Through Household**: Internal engine modules do not access projects, economy, governance, founder, scenario, or population state through `self.household.<prop>` or `household.<prop>`. Such access routes were historical storage tunnels and are mechanically prohibited by AST analysis.
2. **Authoritative Subsystem Access**: Domain mixins receive their required subsystem state directly or unpack it from `self.state.<subsystem>`. Mixin helper signatures explicitly take the subsystem state dataclass (e.g., `projects: ProjectsState`, `economy: EconomyState`, `household: HouseholdState`), preserving modular decoupling and testability.
3. **Compatibility Façade Boundary**: `ForwardingPropertiesMixin` on `Sim` (`sim/engine/core_properties.py`) defines exactly 85 outward-facing compatibility properties for external consumers and integration tests. Internal engine files do not access pruned forwarding properties on `self` or `sim`.
4. **Mechanical AST Enforcement**: `sim/tests/test_state_ownership_enforcement.py` statically inspects all engine code using Python's `ast` parser on every test run. Any internal code attempting to access non-household state via `.household` or accessing pruned properties fails the build.
5. **Bidirectional Synchronisation**: `sim/tests/test_live_state_ownership.py` continuously validates that modifications via direct state mutation, method encapsulation (`cost_capital`, `add_capital`, `add_reputation`, `add_scandal`), or external compatibility properties maintain identical underlying state across all 7 subsystem models.

