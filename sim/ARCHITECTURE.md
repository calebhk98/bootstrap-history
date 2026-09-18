# What this codebase actually is

Measured, not remembered. Every number here was produced by a script against
the tree as it stands; none of it is aspirational. The older design notes in
`rome/*.md` describe a game that has since changed a great deal - treat them
as direction, not as fact. This file is meant to stay true, so if you change
the shape of the code, re-measure and correct it.

## The one-paragraph version

`Sim` is a single large object that holds the entire state of one game. It is
assembled from six mixins living in six files. The **import** graph between
those files is clean and acyclic; the **runtime** coupling between them is
total, because they all talk to each other through `self`. Splitting the
original 5,600-line module into `engine/` moved code into separate files
without decoupling it. That is worth knowing before you plan any refactor.

## Layout

    simulator.py        the front door. Re-exports a large surface on purpose,
                        because every playtest note and instruction ever
                        written says `rome/sim/simulator.py`. Do not narrow it.
    engine/data.py      loads and annotates the tree, prices, civs, geography.
                        The only leaf module: it imports nothing from engine.
    engine/core.py      class Sim, and step() - one simulated year.
    engine/economy.py   money, prices, revenue, upkeep, credit, materials.
    engine/labour.py    staff, trades, wages, teaching, hours.
    engine/projects.py  starting, running and finishing work. can_start.
    engine/society.py   reputation, patronage, state interest, hazards.
    engine/fog.py       what the player is allowed to see.
    engine/geography.py where things are, per civilisation.
    engine/protocol.py  an 81-line shim. The JSON command layer itself is
                        engine/proto/, twelve modules; `agent` mode. Everything
                        importable from engine.protocol still is.
    engine/proto/       dispatch (the command table), render, techtree, state,
                        economy, typed, help, saveload, score, util, nodes,
                        ventures.
    engine/cli.py       argparse, `run`/`compare`/`sweep`/`plan`/`search`/
                        `play`, reporting.
    test_regressions.py a 33-line shim. The suite is tests/, 32 topic modules
                        plus a harness and a runner. `--only <topics>` runs
                        part of it; `--list` names them.
    perf_fingerprint.py proves a change did not alter the simulation.

## The import graph is fine

    data.py  (imports nothing from engine)
      |
      +-- economy, fog, geography, labour, projects, society   (each -> data only)
      |
      +-- core.py      -> data + all six mixins
            |
            +-- protocol.py -> core, data, fog
                  |
                  +-- cli.py -> core, data, protocol

Acyclic, layered, correct. The mixins cannot import one another - they would
cycle - so the import graph tells you almost nothing about what actually
depends on what. That is the trap this document exists to spring.

## The runtime graph is one god object

**RE-MEASURED after the household extraction.** `Sim` now assigns **43**
instance attributes on `self`, and carries **109 forwarding properties** to a
`Household` object holding **68** of its own.

**43 AND CLAUDE.md'S 165 ARE BOTH RIGHT, AND THEY COUNT DIFFERENT THINGS** -
read this before "correcting" either. 43 is what `Sim.__init__` ASSIGNS, by
the script below. CLAUDE.md SS6's 165 is what `Sim` CARRIES: it adds the
attributes assigned outside `__init__`, the 8 reached only as `s.X` from
`proto/`, and the 3 written through `self.__dict__[...]`, none of which a
scan of `__init__` can see. Measured the same day, the assignment rule gives
43 in `__init__` and 45 anywhere in the class body. Quote whichever you mean
and say which, the way CLAUDE.md SS7 already demands for the naming counts -
the two previous attempts at that number disagreed and both were right, for
exactly this reason.

    grep "@property" sim/engine/core.py | wc -l      # properties: 109
    python3 - <<'EOCOUNT'                             # attributes: 43
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

The figure this file used to give was 157 attributes, and that was itself an
undercount: a later measurement found **165**, because eight attributes are
never touched through `self` anywhere in the mixins (they are only ever
reached as `s.X` from `engine/proto/`) and three more hide behind
`self.__dict__[...]`. See `docs/architecture/SIM_STATE_INVENTORY.md` for the
full table and the counting method.

THAT 165 IS NOW STALE, AND IS DELIBERATELY NOT REPLACED HERE. Wiring
`sim/world/demography.py` into the engine deleted `pop_deficit` and
`_pop_recovery_years`, turned `pop_scale` and `wage_index` from stored
attributes into computed properties, and added one new attribute
(`self.population`) and three forwarding properties for its cohorts. So the
true figure moved by roughly four, downward - but quoting `165 - 4` would be
arithmetic on a number rather than a measurement, and this file's whole
point is that the counts are measured.

The obstacle is that the counting method behind 165 is described in
`docs/architecture/SIM_STATE_INVENTORY.md` but is not scripted anywhere, and
it is NOT the number a runtime `vars(sim_instance)` returns: a live `Sim`
carries 42 instance attributes and 110 properties, because most of the
fields the 165 counts now live on sub-objects behind forwarding properties.
Two different questions, two different right answers - exactly the trap
CLAUDE.md section 7 describes for the naming counts. Whoever next needs this
number should script the static method first, so the re-measurement is
repeatable, and then quote it saying which one it is.

The method count is now **523** across the mixins, up from the original 314
counted before the household extraction. This substantial increase is from:
231 methods in Sim + 121 in EconomyMixin + 50 in LabourMixin + 46 in ProjectsMixin + 61 in SocietyMixin + 8 in FogMixin + 6 in GeographyMixin, plus 109 properties.

    python3 - <<'EOCOUNT'
    import ast
    def count_class_methods(filepath, class_name):
        with open(filepath) as f:
            tree = ast.parse(f.read())
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return len([item for item in node.body if isinstance(item, ast.FunctionDef)])
        return 0
    total = count_class_methods('sim/engine/core.py', 'Sim')
    for fname, cname in [('sim/engine/economy.py', 'EconomyMixin'), ('sim/engine/labour.py', 'LabourMixin'),
                         ('sim/engine/projects.py', 'ProjectsMixin'), ('sim/engine/society.py', 'SocietyMixin'),
                         ('sim/engine/fog.py', 'FogMixin'), ('sim/engine/geography.py', 'GeographyMixin')]:
        total += count_class_methods(fname, cname)
    print(total)
    EOCOUNT

The paragraph below is left as written, because its argument is still the
argument - the coupling is the domain, and the extraction did not remove it,
it gave one coherent group of fields an owner.

`Sim` had **157 distinct instance attributes** and **314 methods** across six
mixins. Calls between mixin files, counted by `self.<method>()`:

    core      -> economy    62        society  -> projects   30
    economy   -> projects   43        labour   -> projects   30
    core      -> labour     33        projects -> labour     19
    projects  -> economy    33        core     -> society    15

Distinct `self.*` names touched per file: core 205, economy 195, society 152,
projects 120, labour 94. **Thirty-five attributes are touched by four or more
different files.** No mixin can be constructed, tested or reasoned about on
its own.

This is a distributed god object. It is also, honestly, a defensible shape for
this problem: money genuinely does affect labour, which affects what can be
built, which affects reputation, which affects money. Those couplings are the
domain, not an accident. Moving the state into a `State` object passed to free
functions would relocate the coupling, not remove it.

**A full decomposition has been considered and rejected**, with reasons, so
that the next person does not silently restart it:
  * it means giving 157 shared fields explicit owners and converting ~200
    implicit `self.x` couplings into arguments - a rewrite of most of 30,000
    lines;
  * the safety net does not exist for it. `perf_fingerprint.py` covers the
    simulation loop well and covers `protocol.py` not at all, and protocol is
    where a third of the code lives;
  * the payoff is small, for the reason above.
If you disagree, the bar is: propose it with a plan for proving `protocol.py`
unchanged, because that is the part nothing currently guards.

## What IS worth restructuring

Code lines, counted as **lines that are neither blank nor comment-only**
(docstrings count as code under this rule). Re-measured 2026-09-18, after
the household extraction, four naming rounds, the economy.py constants
migration, and additional growth in economy.py and other modules:

    economy.py            4,846 code   (6,570 total, 26% comment)
    cli.py                2,616 code   (3,547 total, 26% comment)
    society.py            2,773 code   (3,809 total, 27% comment)
    proto/dispatch.py     1,692 code   (2,738 total, 38% comment)
    projects.py           2,296 code   (3,471 total, 33% comment)
    core.py               2,546 code   (4,577 total, 44% comment)
    proto/render.py       1,440 code   (1,764 total, 18% comment)
    labour.py             2,273 code   (3,217 total, 29% comment)
    protocol.py              78 code   (     81 total,  3% comment)
    test_regressions.py      24 code   (     41 total, 41% comment)

    python3 - <<'EOF'
    import os
    paths = ['sim/engine/economy.py', 'sim/engine/cli.py', 'sim/engine/society.py',
             'sim/engine/proto/dispatch.py', 'sim/engine/projects.py', 'sim/engine/core.py',
             'sim/engine/proto/render.py', 'sim/engine/labour.py', 'sim/engine/protocol.py',
             'sim/test_regressions.py']
    for p in paths:
        if os.path.exists(p):
            lines = open(p).read().splitlines()
            code = sum(1 for l in lines if l.strip() and not l.strip().startswith("#"))
            print(p, code, len(lines))
    EOF

THE RULE IS SPELLED OUT AND THE COMMAND IS GIVEN because the previous
version of this table recorded neither, and the numbers could not be
reproduced. Two plausible readings of "excluding comments and blank lines"
- with and without docstrings counted as code - both disagree with the old
figures, so nobody can now tell what was measured or extend the table
consistently. Per CLAUDE.md SS8, a count in a prose document has to be
something the next person can re-run, not a number they have to trust.

Two things this re-measurement shows.

economy.py has roughly tripled and is now by a wide margin the largest file
in the engine, most of that from the constants migration turning 240 bare
literals into declare() calls with sourced `why` text. Its comment share
FELL to 26% while its real documentation went sharply up, because a `why`
string is code under this rule and a `#` line is not. That is a good
illustration of why the rule has to be stated.

"Five of eight engine files are majority comment" was stale when this
document last said so, and it is staler now. The answer depends entirely on
whether a docstring counts as documentation or as code, which is precisely
why the original figure was unreproducible - it never recorded which. BOTH
rules are scripted here, so neither has to be taken on trust. An earlier
re-measurement claimed the docstring-as-documentation rule "cannot be
reproduced"; it can, by walking the AST for docstring line spans:

    python3 - <<'EOCOUNT'
    import ast
    engine_files = ["sim/engine/economy.py", "sim/engine/cli.py",
                    "sim/engine/society.py", "sim/engine/proto/dispatch.py",
                    "sim/engine/projects.py", "sim/engine/core.py",
                    "sim/engine/labour.py", "sim/engine/protocol.py"]
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

Measured 2026-09-18 against HEAD, not against a working tree that had other
agents' uncommitted edits in it:

    file                  total   doc-as-code   doc-as-doc
    economy.py             6,570          26%          46%
    core.py                4,577          44%          54%
    cli.py                 3,547          26%          37%
    society.py             3,809          27%          44%
    projects.py            3,471          34%          46%
    labour.py              3,217          29%          46%
    proto/dispatch.py      2,738          38%          39%
    protocol.py               81           4%          20%

**One of eight** counting docstrings as documentation (core.py, 54%), and
**zero of eight** counting them as code. CLAUDE.md SS6 still says four and
one; that was true when written and this measurement supersedes it. Note the
direction: the files got denser, not better documented.

THE CLAIM THAT MATTERS IS UNAFFECTED. The comments are how agents hand each
other the reason a thing is the way it is, they are load-bearing, and they
must not be stripped to "clean up". That was never really an argument about
percentages.

`core.py` is 4,577 lines total and 2,098 of them are code under the
docstrings-as-documentation rule above. Splitting it by line count would
shuffle prose between files and buy nothing.

The two genuine outliers WERE `test_regressions.py` and `protocol.py`, and
both have since been split - see the layout above. What made them worth
splitting was not their line count:

  * `protocol.py`'s `_agent_dispatch_inner` was a single if/elif chain with a
    cyclomatic complexity of **395**, about eight times the point at which a
    function stops being readable. It is now forty handlers behind a dict,
    complexity 34, with an import-time assertion tying that dict to
    KNOWN_COMMANDS so the two cannot drift. Pulling it apart immediately
    exposed a handler referencing a variable that only existed in the old
    enclosing scope - dead from the moment it was extracted, and unfindable
    while it was buried.
  * `test_regressions.py` was a flat script, so checks ran at import in file
    order and nothing could be run selectively. `--only mines,demographics`
    runs 43 checks in 1 second where the whole suite runs **2,316** checks
    in 91 seconds (measured 2026-09-18 against HEAD in a clean `git archive`
    checkout, with 13 slow checks skipped). Measure this one against HEAD
    rather than the working tree: a single uncommitted test file shifts the
    count, which is how an earlier pass reported 2,317.

        python3 sim/test_regressions.py --only mines,demographics 2>&1 | tail -1
        python3 sim/test_regressions.py 2>&1 | tail -1

The engine mixins were left alone, for the reasons above. Splitting them by
line count would move prose between files and buy nothing.

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

## Two things that will bite you

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

    python3 rome/sim/perf_fingerprint.py record before.json
    ...make your change...
    python3 rome/sim/perf_fingerprint.py check before.json

It hashes every field of state after every year of nine runs across five
civilisations, fog on and off, and names the first year that differs. It does
NOT cover `topo_order`, `protocol.py`, or anything outside the simulation
loop - those need their own proof.
