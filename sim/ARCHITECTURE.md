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

**RE-MEASURED after the household extraction.** `Sim` now assigns **55**
instance attributes on `self`, and carries **104 forwarding properties** to a
`Household` object holding **68** of its own. The founder's money, staff,
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

The method count is now **411** across the mixins, up from 314, which is
almost entirely the forwarding properties.

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

Measured code lines, excluding comments and blank lines:

    cli.py                2,128 code
    economy.py            1,514 code
    proto/dispatch.py     1,507 code
    proto/render.py       1,337 code
    society.py            1,114 code
    projects.py           1,071 code
    core.py                 913 code   ( 2,363 total, 61% comment)
    labour.py               739 code   ( 2,085 total, 65% comment)
    protocol.py              65 code   (the shim)
    test_regressions.py       5 code   (the shim)

Five of eight engine files are **majority comment**. `core.py` looks like a
2,200-line file and is 893 lines of code. Splitting those by line count would
shuffle prose between files and buy nothing; the comments are how agents hand
each other the reason a thing is the way it is, and they are load-bearing.

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
    now runs 44 checks in 2 seconds where the whole suite takes 68.

The engine mixins were left alone, for the reasons above. Splitting them by
line count would move prose between files and buy nothing.

## Where the data lives, and who reads it

    data/tech_tree.json    2.8 MB, 2,849 nodes. data.py loads it; core,
                           economy, projects, settings, cli read it through
                           data. treetool.py writes it.
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
