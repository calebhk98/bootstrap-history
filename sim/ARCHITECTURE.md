# What this codebase actually is

Measured, not remembered. Every number here was produced by a script against
the tree as it stands; none of it is aspirational. The older design notes in
`rome/*.md` describe a game that has since changed a great deal - treat them
as direction, not as fact. This file is meant to stay true, so if you change
the shape of the code, re-measure and correct it.

## The one-paragraph version

`Sim` is a single large object that holds the entire state of one game. Its
base list in `core.py` names six mixins - `EconomyMixin`, `FogMixin`,
`GeographyMixin`, `LabourMixin`, `ProjectsMixin`, `SocietyMixin`. Two of
those six, `EconomyMixin` and `SocietyMixin`, hold no methods of their own:
each is an empty composition point that inherits from four further
sub-mixins living in their own files (`MarketMixin`, `CreditMixin`,
`MiningMixin`, `ProductionMixin` under `EconomyMixin`; `HazardsMixin`,
`StatePressureMixin`, `AdoptionMixin`, `DiffusionMixin` under `SocietyMixin`).
`class Sim(...)` in `core.py` names only the six top-level mixins, never a
sub-mixin directly - see "The composition-point pattern" below for why a
future split of a large mixin should keep that shape. The **import** graph
across all fourteen mixin files (six top-level
plus eight sub-mixins) is clean and acyclic; the **runtime** coupling between
them is total, because they all talk to each other through `self`. Moving
code into more, smaller files moved it into separate files without
decoupling it. That is worth knowing before you plan any refactor.

## Layout

    simulator.py        the front door. Re-exports a large surface on purpose,
                        because every playtest note and instruction ever
                        written says `rome/sim/simulator.py`. Do not narrow it.
    engine/data.py      loads and annotates the tree, prices, civs, geography.
                        The only leaf module: it imports nothing from engine.
    engine/core.py      class Sim, and step() - a 42-line dispatcher over 14
                        `_step_*` phase methods, one simulated year. 4,929
                        lines total (see "What IS worth restructuring" below).
    engine/economy.py   598-line composition point:
                        `EconomyMixin(MarketMixin, MiningMixin, CreditMixin,
                        ProductionMixin)`. Money, prices, revenue, upkeep,
                        credit and materials live in the four files below it,
                        not in economy.py itself:
    engine/economy_market.py      prices, the goods market, trade (3,171 lines).
    engine/economy_mining.py      mines, deposits, extraction (1,075 lines).
    engine/economy_credit.py      loans, arrears, debt (1,105 lines).
    engine/economy_production.py  material production chains (773 lines).
    engine/labour.py    staff, trades, wages, teaching, hours.
    engine/projects.py  starting, running and finishing work. can_start.
    engine/society.py   45-line composition point:
                        `SocietyMixin(HazardsMixin, StatePressureMixin,
                        AdoptionMixin, DiffusionMixin)`. Reputation,
                        patronage, state interest and hazards live in the
                        four files below it, not in society.py itself:
    engine/society_hazards.py         events that can strike a civilisation
                                       (1,127 lines).
    engine/society_state_pressure.py  state capacity, scandal, denunciation
                                       (1,405 lines).
    engine/society_adoption.py        who takes up a technology and when
                                       (632 lines).
    engine/society_diffusion.py       how a technology spreads once adopted
                                       (718 lines).
    engine/hazard_window.py  45 lines: the hazard-timing arithmetic that
                        `FogMixin.knowledge_risk` and
                        `SocietyMixin.hazard_timeline` (now `HazardsMixin`)
                        used to each compute a separate, drifting copy of.
                        One shared function now, used by both callers.
    engine/fog.py       what the player is allowed to see.
    engine/geography.py where things are, per civilisation.
    engine/protocol.py  an 81-line shim, not touched by the mixin split
                        above. The JSON
                        command layer itself is engine/proto/, twelve
                        modules; `agent` mode. Everything importable from
                        engine.protocol still is.
    engine/proto/       dispatch (the command table), render, techtree, state,
                        economy, typed, help, saveload, score, util, nodes,
                        ventures.
    engine/cli.py       1,608 lines: argparse and `validate`/`path`/`costs`/
                        `run`/`compare`/`sensitivity`/`sweep`/`goals`. Three
                        more command groups now live in their own files:
    engine/cli_interactive.py  `play`/`civs`/`menu` - the interactive loop
                        (1,542 lines).
    engine/cli_analysis.py     `plan`/`search`/`why` - offline reporting
                        (319 lines).
    engine/cli_agent.py        `agent` mode's CLI entry point (207 lines).
    test_regressions.py a 41-line shim. The suite is tests/, subject-named
                        topic modules plus a harness and a runner. `--only
                        <topics>` runs part of it; `--list` names them.
    perf_fingerprint.py proves a change did not alter the simulation.

All line counts above are `wc -l sim/engine/<file>.py`, run 2026-09-18
against HEAD.

## The import graph is fine

    data.py  (imports nothing from engine)
      |
      +-- economy_market, economy_mining, economy_credit, economy_production,
      |   society_hazards, society_state_pressure, society_adoption,
      |   society_diffusion, fog, geography, labour, projects
      |                                              (each -> data only,
      |                                               society_hazards also
      |                                               -> hazard_window)
      |
      +-- economy.py    -> the four economy_* sub-mixins
      +-- society.py    -> the four society_* sub-mixins
      |
      +-- core.py       -> data + all six top-level mixins (economy, fog,
      |                    geography, labour, projects, society)
            |
            +-- protocol.py -> core, data, fog
                  |
                  +-- cli.py -> core, data, protocol, then at its own bottom
                                cli_interactive, cli_agent, cli_analysis

Checked 2026-09-18 by reading every `from .` / `import .` line in each of the
fourteen mixin files: none of the eight sub-mixins imports another sub-mixin,
another top-level mixin, or `core`. Acyclic, layered, correct, same shape as
before the split - just one layer deeper under `economy.py` and `society.py`.
The mixins cannot import one another - they would cycle - so the import graph
tells you almost nothing about what actually depends on what. That is the
trap this document exists to spring, and it is exactly as true of the eight
new sub-mixins as it was of the original six: see "The composition-point
pattern" below.

## The runtime graph is one god object

`Sim` assigns **44** instance attributes on `self` in `__init__`, and
carries **109 forwarding properties** (`grep -c "@property"`) to a
`Household` object holding **68** of its own (`sim/engine/actors/
household.py`, same script).

A freshly built `Sim` (`sim.tests.harness.sim()`, before the test harness
pokes its own `goal` attribute onto it afterwards) has exactly those 44
attributes and nothing else - checked by diffing the static AST set against
`vars()` on a live instance.

**44 counts a narrower thing than "everything `Sim` carries."** It is what
`Sim.__init__` ASSIGNS, by the script below. A broader count - everything
`Sim` CARRIES - would add the attributes assigned outside `__init__`, the
ones reached only as `s.X` from `proto/`, and the ones written through
`self.__dict__[...]`, none of which a scan of `__init__` can see. That
broader counting method is described in
`docs/architecture/SIM_STATE_INVENTORY.md` but is not scripted anywhere, so
do not invent a figure for it. The assignment rule gives 44 in `__init__`
and **46** anywhere in the class body (self.X assignments in any method, not
only `__init__`). Quote whichever you mean and say which, the way CLAUDE.md
SS7 already demands for the naming counts - the two previous attempts at
that number disagreed and both were right, for exactly this reason.

    grep -c "@property" sim/engine/core.py            # properties: 109
    python3 - <<'EOCOUNT'                             # attributes: 44
    import ast
    code = open('sim/engine/core.py').read()
    tree = ast.parse(code)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == 'Sim':
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                    attrs = set()
                    for n in ast.walk(item):
                        if isinstance(n, ast.Assign):
                            for target in n.targets:
                                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                                    attrs.add(target.attr)
                    print(len(attrs))
                    break
    EOCOUNT

The founder's money, staff,
knowledge, inventory and standing left `Sim` for
`sim/engine/actors/household.py`; what stayed is the world, the scenario, and
eight fields biographical to one mortal person (`founder_alive`, `life_left`,
`dead_reason` and kin) which have no meaning for a government or a firm and
so are waiting for a second actor to say what they should become.

`docs/architecture/SIM_STATE_INVENTORY.md` has the full table and counting
method for the broader "everything `Sim` carries" question, including the
attributes reached only as `s.X` from `engine/proto/` and the ones hidden
behind `self.__dict__[...]`; it is not scripted, so treat any total it gives
as unverifiable against today's build rather than re-deriving one by
arithmetic on it.

Two different questions give two different right answers for the property
count, too: `grep -c "@property"` on `core.py` gives **109** (getters only);
`[n for n in dir(type(sim)) if isinstance(getattr(type(sim), n), property)]`
on a live instance gives **110**, because that walks the MRO and one
property is inherited from a mixin rather than defined with its own
`@property` line in `core.py`'s grep-able text. Exactly the trap CLAUDE.md
section 7 describes for the naming counts.

## The composition-point pattern

Splitting `EconomyMixin` and `SocietyMixin` into sub-mixins did NOT touch
`class Sim(EconomyMixin, FogMixin, GeographyMixin, LabourMixin, ProjectsMixin,
SocietyMixin)` in `core.py`. `economy.py` still defines a class called
`EconomyMixin`, and `society.py` still defines a class called `SocietyMixin`
- they are just now one line each of inheritance
(`class EconomyMixin(MarketMixin, MiningMixin, CreditMixin, ProductionMixin)`)
instead of holding a few thousand lines of methods themselves.

This is the pattern to use for every future split of a mixin that has grown
too large: pick the class Python already resolves methods through, keep its
name and its place in `Sim`'s base list fixed, and move its method bodies
out to sub-mixins it inherits from. The alternative - renaming or replacing
`EconomyMixin` in `Sim`'s base list, or splitting `Sim` itself into several
classes - would put a line inside `core.py`'s `class Sim(...)` statement in
the diff of every future split. Two agents splitting different domains in
the same week would then collide on the same line for reasons that have
nothing to do with each other. Composing beneath a fixed name means a split
of `LabourMixin` next month touches `labour.py` and whatever new files it
creates, and nothing in `core.py` at all.

It costs nothing at runtime: Python's MRO resolves a method on
`MarketMixin` through `EconomyMixin` through `Sim` exactly as it would if the
method were written directly on `EconomyMixin`, and every mixin's `self` is
still the same one `Sim` instance it always was - this pattern does not
touch the "runtime coupling is total" problem, and was never meant to.

## The method count

`Sim` and its mixins have **538** methods between them. Counted as every
`FunctionDef` directly in a class's own body, which is why a `@property`
getter and its `@x.setter` each count as one method, matching the 109/107
properties/setters folded into `Sim`'s own total below:

    Sim                    246   (independently: 109 @property + 107 @x.setter
                                   + 30 plain methods = 246)
    EconomyMixin            10   composed of:
      MarketMixin           55
      CreditMixin           11
      MiningMixin           29
      ProductionMixin       16     (economy total: 121)
    SocietyMixin              0   composed of:
      HazardsMixin           13
      StatePressureMixin     17
      AdoptionMixin          11
      DiffusionMixin         20     (society total: 61)
    LabourMixin              50
    ProjectsMixin             46
    FogMixin                   8
    GeographyMixin             6
    TOTAL                    538

`Sim` itself accounts for 246 of the 538: `step()` is now `step()` plus 14
`_step_*` phase methods - see "`Sim.step()`" below for why. **A
method-counting script must walk into a composition point's sub-mixins, or
it will silently undercount.** A script that counts only `EconomyMixin`'s
and `SocietyMixin`'s own class bodies, not their sub-mixins, reports 366,
because it cannot see the 121 + 61 = 182 methods those two composition
points inherit rather than define. That is the sub-mixin trap in numeric
form: an import-clean split can make a perfectly good script quietly start
undercounting. The corrected script:

    python3 - <<'EOCOUNT'
    import ast
    def count_class_methods(filepath, class_name):
        with open(filepath) as f:
            tree = ast.parse(f.read())
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return len([item for item in node.body if isinstance(item, ast.FunctionDef)])
        return 0
    pieces = [
        ('sim/engine/core.py', 'Sim'),
        ('sim/engine/economy.py', 'EconomyMixin'),
        ('sim/engine/economy_market.py', 'MarketMixin'),
        ('sim/engine/economy_credit.py', 'CreditMixin'),
        ('sim/engine/economy_mining.py', 'MiningMixin'),
        ('sim/engine/economy_production.py', 'ProductionMixin'),
        ('sim/engine/labour.py', 'LabourMixin'),
        ('sim/engine/projects.py', 'ProjectsMixin'),
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

Whoever splits another mixin next must add its new sub-mixin files to this
list, or this script will make exactly the same silent-undercount mistake
the old one just did.

This is a distributed god object. It is also, honestly, a defensible shape for
this problem: money genuinely does affect labour, which affects what can be
built, which affects reputation, which affects money. Those couplings are the
domain, not an accident. Moving the state into a `State` object passed to free
functions would relocate the coupling, not remove it.

The clearest illustration is a coupling count taken when `Sim` had 157
distinct instance attributes and 314 methods across six mixins, both since
superseded by the 44/46 and 538 given above; nobody has re-run the coupling
count itself against the current fourteen files, so treat the numbers below
as illustrating the shape of the coupling, not as current. Calls between
mixin files, counted by `self.<method>()`:

    core      -> economy    62        society  -> projects   30
    economy   -> projects   43        labour   -> projects   30
    core      -> labour     33        projects -> labour     19
    projects  -> economy    33        core     -> society    15

Distinct `self.*` names touched per file: core 205, economy 195, society 152,
projects 120, labour 94. Thirty-five attributes were touched by four or more
different files. No mixin could be constructed, tested or reasoned about on
its own - and the mixin split did not change that; it moved code into more
files without decoupling it (see "The one-paragraph version" above).

**A full decomposition has been considered and rejected**, with reasons, so
that the next person does not silently restart it:
  * it means giving every shared field an explicit owner and converting the
    couplings mixins currently reach through `self` into arguments - a
    rewrite of most of 30,000 lines;
  * the safety net does not exist for it. `perf_fingerprint.py` covers the
    simulation loop well and covers `protocol.py` not at all, and protocol is
    where a third of the code lives;
  * the payoff is small, for the reason above.
If you disagree, the bar is: propose it with a plan for proving `protocol.py`
unchanged, because that is the part nothing currently guards.

## What IS worth restructuring

Code lines, counted as **lines that are neither blank nor comment-only**
(docstrings count as code under this rule). `economy.py`, `society.py` and
the top-level `cli.py` are thin composition points now (598, 45 and 1,608
lines respectively - see Layout above), so they are not the largest files
any more; the table below lists the **eight largest files in `engine/` by
total line count**:

    core.py                2,812 code   (4,929 total, 43% comment)
    projects.py            2,294 code   (3,468 total, 34% comment)
    labour.py               2,271 code   (3,214 total, 29% comment)
    economy_market.py       2,310 code   (3,171 total, 27% comment)
    proto/dispatch.py       1,688 code   (2,730 total, 38% comment)
    proto/render.py         1,434 code   (1,754 total, 18% comment)
    cli.py                  1,146 code   (1,608 total, 29% comment)
    cli_interactive.py      1,173 code   (1,542 total, 24% comment)

    python3 - <<'EOF'
    import os
    paths = ['sim/engine/core.py', 'sim/engine/projects.py', 'sim/engine/labour.py',
             'sim/engine/economy_market.py', 'sim/engine/proto/dispatch.py',
             'sim/engine/proto/render.py', 'sim/engine/cli.py', 'sim/engine/cli_interactive.py']
    for p in paths:
        if os.path.exists(p):
            lines = open(p).read().splitlines()
            code = sum(1 for l in lines if l.strip() and not l.strip().startswith("#"))
            print(p, code, len(lines))
    EOF

The rule and the command travel with the table because "excluding comments
and blank lines" has two plausible readings - with and without docstrings
counted as code - that disagree with each other, so nobody can tell what was
measured or extend the table consistently unless both the rule and the paths
are pinned down. Per CLAUDE.md SS8, a count in a prose document has to be
something the next person can re-run, not a number they have to trust. This
table is not comparable to a line count of the pre-split `economy.py`/
`society.py`/`cli.py`, since those files no longer hold the code being
measured; `economy_market.py` (3,171 lines) is the closest present-day
equivalent of the old `economy.py`'s bulk, but it is one of four files that
now hold what one file used to.

The smaller composition points are worth a separate note: `economy.py`
(598 lines) and `society.py` (45 lines) are themselves majority comment under
the docstring-as-documentation rule below (52% and 98%), because nearly all
that is left in them, once the methods moved out, is the class statement and
the prose explaining why it is shaped that way. A tiny file can be "mostly
comment" for a completely different reason than a huge one.

Whether a docstring counts as documentation or as code changes the answer to
"how much of this file is comment", which is precisely why a bare percentage
is not enough - the rule has to travel with the number. Both rules, scripted
against the eight largest current engine files:

    python3 - <<'EOCOUNT'
    import ast
    engine_files = ["sim/engine/core.py", "sim/engine/projects.py",
                    "sim/engine/labour.py", "sim/engine/economy_market.py",
                    "sim/engine/proto/dispatch.py", "sim/engine/proto/render.py",
                    "sim/engine/cli.py", "sim/engine/cli_interactive.py"]
    for path in engine_files:
        source = open(path).read()
        lines = source.splitlines()
        blank_or_comment = sum(1 for line in lines
                               if not line.strip()
                               or line.strip().startswith("#"))
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
        print("%-26s %6d total %5.0f%% doc-as-code %5.0f%% doc-as-doc"
              % (path, len(lines),
                 100.0 * blank_or_comment / len(lines),
                 100.0 * (blank_or_comment + len(docstring_lines)) / len(lines)))
    EOCOUNT

    file                  total   doc-as-code   doc-as-doc
    core.py                4,929          43%          55%
    projects.py            3,468          34%          46%
    labour.py              3,214          29%          46%
    economy_market.py      3,171          27%          49%
    proto/dispatch.py      2,730          38%          39%
    proto/render.py        1,754          18%          23%
    cli.py                 1,608          29%          42%
    cli_interactive.py     1,542          24%          34%

**One of eight** is majority comment counting docstrings as documentation -
`core.py`, at 55%. **Zero of eight** is, counting them as code. That answer
would be different on a list that still included the now-tiny `economy.py`/
`society.py` (52% and 98% "comment" respectively, for the reason given
above - there is almost nothing left in them BUT the explanation), which is
why the file list has to travel with the number as much as the rule does.
The files that stayed large are denser, not better documented, than the
ones that shrank to composition points. The comments are how agents hand
each other the reason a thing is the way it is; they are load-bearing, and
must not be stripped to "clean up".

`core.py` is 4,929 lines total and 2,205 of them are code under the
docstrings-as-documentation rule above - the script's own exact
`blank_or_comment`/`docstring_lines` counts, not a percentage rounded back
into a line count. Splitting it by line count alone
would shuffle prose between files and buy nothing; the part of `core.py`
that WAS worth splitting out - `step()` - was split for cyclomatic reasons,
not line-count ones. See "`Sim.step()`" below.

`test_regressions.py` and `protocol.py` were split for cyclomatic reasons,
not line-count ones - see the layout above for their current shape:

  * `protocol.py`'s `_agent_dispatch_inner` was a single if/elif chain with a
    cyclomatic complexity of **395**, about eight times the point at which a
    function stops being readable. It is now forty handlers behind a dict,
    complexity 34, with an import-time assertion tying that dict to
    KNOWN_COMMANDS so the two cannot drift.
  * `test_regressions.py` was a flat script, so checks ran at import in file
    order and nothing could be run selectively. `--only mines,demographics`
    runs 43 checks in 1 second where the whole suite runs **2,080** checks
    in 66-68s (12 slow checks skipped, 3 slow topics not run). Measure this
    against a clean checkout of HEAD rather than a working tree with other
    agents' edits in it: a single uncommitted test file shifts the count.

        python3 sim/test_regressions.py --only mines,demographics 2>&1 | tail -1
        python3 sim/test_regressions.py 2>&1 | tail -1

    In a SHALLOW clone (`git rev-parse --is-shallow-repository` says true),
    one check fails here that does not fail in a full clone: the
    byte-identical rename-safety proof needs `git show <rev>:<path>` for a
    commit the shallow history does not have, and reports "is this checkout
    shallow?" when it cannot get it. That is the checkout, not the code -
    confirm with `git rev-parse --is-shallow-repository` before treating a
    lone failure there as a regression.

The engine mixins were left alone, for the reasons above. Splitting them by
line count would move prose between files and buy nothing.

## `Sim.step()`

`step()` was 1,760 lines - the single largest method in the codebase - and
is now **42 lines** (`3026`-`3068` in `core.py` at time of measurement) that
call, in the same order the phases always ran in, **14** extracted
`_step_*` phase methods: `_step_apprenticeships`, `_step_staff`,
`_step_money`, `_step_dated_shocks`, `_step_teach_trades`,
`_step_standing_work_directive`, `_step_start_projects`, `_step_materials`,
`_step_progress_project`, `_step_progress`, `_step_wage_fallback`,
`_step_reputation`, `_step_bondage`, `_step_founder_mortality`. Each phase
still reads and writes exactly the `self.*` state it always did; only a
handful of values cross phase boundaries as arguments and return values
instead (`pool`/`hired_left` from `_step_start_projects` into
`_step_progress`; `remaining`/`remaining_after_projects`/
`hours_effective_total` from `_step_progress` into `_step_wage_fallback` and
`_step_reputation`).
This is a line-count fix, not a coupling fix - the same "runtime coupling is
total" fact applies to the 14 phase methods as applied to the one method
they replaced, because they are still all reading and writing `self`.

    python3 - <<'EOCOUNT'
    import ast
    source = open('sim/engine/core.py').read()
    lines = source.splitlines()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'step':
            start, end = node.lineno, node.end_lineno
            print("step() total lines:", end - start + 1)
    print("_step_* phase methods:",
          sum(1 for node in ast.walk(tree)
              if isinstance(node, ast.FunctionDef)
              and node.name.startswith('_step_')))
    EOCOUNT

## Where the data lives, and who reads it

    data/tech_tree.json    2.8 MB, 2,864 nodes. data.py loads it; core,
                           economy, projects, settings, cli read it through
                           data. treetool.py writes it.

                           python3 -c "import json; print(len(json.load(open('data/tech_tree.json')).get('nodes', {})))"
    data/prices.json       data.py, economy.py.
    data/civilizations/    five playable civs. data.py, cli.py.
    data/world/            geography and commodities.
    data/branches/         authoring input, merged into the tree by treetool.
    data/judgement.json    written by `treetool.py judge`. READ BY NOTHING.
                           A report artifact that is committed; it has drifted
                           from what its own generator now produces.

## Four things that will bite you

**The tree tools write to the repository.** `treetool.py merge|judge|repair|
apply-caps` each rewrite a committed data file. `judge` reads like a report
command and rewrites 244 KB of game data. Every subcommand now takes
`--dry-run`; use it if you only mean to look.

**Green tests do not mean unchanged behaviour.** The suite asserts on outputs
and messages. It does not assert that the simulation is the same simulation.
An "obviously safe" cleanup - promoting `getattr(self, x, default)` calls to
real `__init__` attributes - passed the entire suite while silently breaking
save-file semantics, because several of those names are in `SAVE_FIELDS` where
a *missing* attribute is meaningful. `perf_fingerprint.py` caught it and the
suite did not. Run it:

    python3 sim/perf_fingerprint.py record before.json
    ...make your change...
    python3 sim/perf_fingerprint.py check before.json

It hashes every field of state after every year of nine runs across five
civilisations, fog on and off, and names the first year that differs. It does
NOT cover `topo_order`, `protocol.py`, or anything outside the simulation
loop - those need their own proof.

**An import-time check cannot catch a bare module-global reference that
moved.** A class object used as a process-wide cache slot - a bare name,
read and written at call time, not through `self` and not through an import
alias - breaks silently if that class moves to another file: `import
simulator` still succeeds, `sim/simulator.py validate` still passes, every
module still compiles, because none of those checks execute the line that
reads the name. Only a command that actually runs that code path raises the
`NameError`. A split is not verified until something runs the code, not
just imports it. The cheapest thing that does:

    echo '{"cmd": "state"}' | python3 sim/simulator.py agent --civ rome_100ad

**Tests that read source text with `inspect.getsource` test prose shape, not
behaviour.** `grep -rln "getsource" sim/tests/ --include="*.py"` names them -
nine as of this HEAD. Each asserts on the literal text of a function body,
so moving code between methods can break one of these while the property it
guards still holds. `test_affordability_warning.py` reads `step()` plus
every `_step_*` method on `Sim`, not `step()` alone, precisely because the
phrase it looks for can live in either. Whoever next moves code between
methods should run that grep first, not discover the list from a failure.
