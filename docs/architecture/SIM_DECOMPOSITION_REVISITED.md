# Sim decomposition, revisited

**Status:** analysis, requested by the stakeholder specifically to reopen a
question `sim/ARCHITECTURE.md` and `CLAUDE.md` both call settled. Reopening
it openly is sanctioned by the stakeholder; pretending the prior decision
does not exist is not, so this document argues with that decision's own
reasons rather than working around them. It recommends action in section 7.
It changes no code.

Every number below either came from a command run against this checkout, or
is quoted from a named file with a line number, so the next person can
re-check it rather than trust it.

---

## 1. What was actually decided, and the reasons given

The decision is older than this repository's visible git history. The
rejection paragraph exists verbatim in the very first commit,
`aeff37a` ("Added 1st files, part 1"), inside `sim/ARCHITECTURE.md`. It has
been re-measured twice since (`def9a51`, `5bf7a58`) but never reversed.
Quoting the current text, `sim/ARCHITECTURE.md` lines 168-184:

> This is a distributed god object. It is also, honestly, a defensible shape
> for this problem: money genuinely does affect labour, which affects what
> can be built, which affects reputation, which affects money. Those
> couplings are the domain, not an accident. Moving the state into a `State`
> object passed to free functions would relocate the coupling, not remove
> it.
>
> **A full decomposition has been considered and rejected**, with reasons,
> so that the next person does not silently restart it:
>   * it means giving 157 shared fields explicit owners and converting ~200
>     implicit `self.x` couplings into arguments - a rewrite of most of
>     30,000 lines;
>   * the safety net does not exist for it. `perf_fingerprint.py` covers the
>     simulation loop well and covers `protocol.py` not at all, and protocol
>     is where a third of the code lives;
>   * the payoff is small, for the reason above.
> If you disagree, the bar is: propose it with a plan for proving
> `protocol.py` unchanged, because that is the part nothing currently
> guards.

`CLAUDE.md` section 6 restates this as a hard rule: "A full decomposition
has been considered and rejected with reasons in `sim/ARCHITECTURE.md`. Do
not silently restart it." An external design review, saved verbatim at
`docs/architecture/CURRENT_CODE_ARCHITECTURE_REVIEW.md` (its own file lists
it as "External design review, saved verbatim, direction rather than an
approved plan" - `docs/architecture/README.md`), reaches the same
conclusion independently in its own section 13, lines 1608-1614:

> Do not refactor merely to produce small files.
>
> The existing `Sim` can continue to orchestrate the system.

Being fair to this decision means noting what it is actually an argument
against. It rejects **one specific shape of change**: giving every one of
`Sim`'s shared fields an explicit owner object and rewriting every call site
that touches `self.x` into an argument pass. It does not reject decomposition
in general, and the project has since done two smaller decompositions
successfully under the same standing rule (section 4 below). The three
reasons given were, at the time: the coupling is real and moving it does not
remove it; the safety net (`perf_fingerprint.py`) does not reach a third of
the code; and the payoff for a full field-by-field split is small relative
to a ~30,000-line rewrite. All three were true when written. Section 2 checks
each of them against what exists now.

---

## 2. Which reasons still hold, and which have been overtaken

**"The coupling is real and moving it does not remove it" still holds, in
full.** Nothing measured for this document contradicts it. `sim/
ARCHITECTURE.md` lines 163-166 record 35 attributes touched by four or more
of the six mixin files and 202 implicit `self.x` couplings between them; nothing
about the passage of time makes a `capital` read by economy, labour and
projects alike into three independent facts. Any proposal in section 4 that
pretends this coupling can be split away by moving files around is wrong for
the same reason it was wrong before, and none of what follows tries to.

**"The safety net does not reach a third of the code" still holds, exactly
as stated**, and is the single most important fact in this document. Verified
by reading `perf_fingerprint.py` itself (section 5) rather than by trusting
the old claim: it hashes `SAVE_FIELDS` after every simulated year across nine
scenarios, and its own header says nothing about `protocol.py`. This reason
does not get weaker with age; if anything, `protocol.py`'s share of the code
has only grown since it was split into `engine/proto/`'s twelve modules
(`sim/ARCHITECTURE.md`, "Layout"). Any stage of a proposal that touches
`protocol.py` inherits this exact gap, unchanged.

**"The payoff is small" is the reason that has moved, because the size of
the file it was weighed against has not stood still.** Measured against the
same commit the rejection paragraph's own numbers came from
(`git show aeff37a:sim/engine/core.py | wc -l`) and against `HEAD`
(`wc -l sim/engine/core.py`, commit `a3b05ef`):

    core.py:  2,363 lines (aeff37a, the decision's own baseline)
           -> 4,861 lines (HEAD)                          +105.7%

    Sim + six mixins, total methods (script in sim/ARCHITECTURE.md,
    "The runtime graph is one god object"):
             314 methods (quoted in the original rejection text)
          -> 524 methods (re-run today)                    +66.9%

`sim/ARCHITECTURE.md` itself records that the attribute count the decision
was weighed against, 157, was later found to be an undercount (165 carried,
counting fields reached only via `s.X` from `proto/` and three hidden behind
`self.__dict__[...]`), and that even 165 is now stale after the demography
wiring changed which fields are stored versus computed - and, its own words,
"deliberately not replaced here" with a corrected figure, because the
counting method was never scripted. The honest statement is: the object the
decision was made about no longer exists in the shape it was measured in,
and every dimension anyone has re-measured has grown, never shrunk.

The single largest method in the file, `Sim.step()`, illustrates the same
point on its own:

    python3 -c "
    import ast
    tree = ast.parse(open('sim/engine/core.py').read())
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == 'Sim':
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == 'step':
                    print(item.lineno, item.end_lineno,
                          item.end_lineno - item.lineno + 1)
    "
    # 3024 4783 1760

1,760 lines in one method, 36.2% of `core.py`'s current 4,861 lines, in a
single function whose own docstring-comments describe it as having at least
nine internal phases (section 4). The payoff calculus in the original
rejection was never about whether the coupling was real; it was a comparison
of a large one-time cost against a benefit judged small **for the code as it
stood then**. A file that has roughly doubled and a hot method that has grown
alongside it change the second side of that comparison, not the first.

**What none of this argues:** none of the growth above is, by itself, a
reason to run the rejected refactor. It is a reason the comparison needs to
be redone rather than assumed settled, which is exactly the stakeholder's
request.

---

## 3. The constraint nobody weighed the first time

The original decision is a pure cost/benefit/safety argument about the
*simulation*. It says nothing about the *people editing the simulation*,
because when it was written there was no reason to. That has changed: the
stakeholder's stated reason for reopening this is that several engineers and
agents can no longer work in these files concurrently, and a fault in one
person's change cannot be isolated from another's.

This is not hypothetical; the repository already has a recorded incident.
`Complaints/33-two-undefined-global-reads-inside-Sim-step.md` documents a
real collision **inside `Sim.step()` specifically**: six agents shared one
checkout and its git index; `git commit` commits the index rather than the
files named on the command line; one agent's half-finished rename (a local
`n` renamed to `node` at its binding site, with two reads roughly 500 lines
further into the same function not yet reached) was swept into another
agent's unrelated commit and landed in history looking like a real
`NameError`-producing bug. It was caught, but only after a second agent spent
real effort diagnosing a bug that did not exist, and the complaint's own
retrospective calls this "the same failure one level up" from the `id()`
non-determinism bug in `Complaints/closed/27`. Two mechanisms compounded:
the shared git index, which a commit hygiene fix (`git commit -o <pathspec>`)
addresses directly, and the sheer distance between related lines inside one
1,760-line function, which no git workflow fix touches at all. A rename left
half-finished at line 1971 with its matching reference at line 2438 of the
same function is exactly the kind of thing that is easy to miss under review
and easy to lose track of mid-edit; the same rename split across two
40-line methods in two different files is not.

Two more independent, dated observations from documents already in this
tree confirm this is routine rather than a one-off: `docs/architecture/
WIRING_MILESTONE_4.md` was written "while four other agents edited
`sim/world/deposits.py`, `sim/solve_prices.py`, `sim/prove_rename_safe.py`
and `sim/engine/economy.py` concurrently in the same checkout," to the point
that its author had to read every cited file's content from a fixed anchor
commit rather than the live working tree, specifically because the working
tree could not be trusted to hold still. `docs/architecture/
STATE_OF_THE_PROJECT.md` records the same thing independently: "several
other agents were live in this checkout while this document was written."
This document's own research hit a live instance of the same fact: at the
time of writing, `git status` in this checkout shows 37 files modified but
uncommitted, `sim/engine/core.py` among them, left over from work already in
progress before this analysis began.

None of this contradicts section 2's finding that the coupling is real.
Two engineers can be assigned disjoint, correctly-scoped pieces of work and
still collide, not because the domain forces them to touch the same fields,
but because both pieces of work happen to live in the same 4,861-line file
and the same 1,760-line function, so their diffs overlap by proximity alone
even when their actual concerns do not. That is a file-shape problem, and it
is a different problem from the coupling problem the original decision
weighed. Fixing it does not require removing the coupling; it requires
giving unrelated pieces of work separate homes to edit, which is a weaker
and cheaper property than what the original decision rejected.

---

## 4. A staged proposal

The project has already run two decompositions since the rejection was
written, under the same standing rule, and both succeeded. They are the
template for what follows, not a new idea:

* **`protocol.py`'s dispatch.** A single `if`/`elif` chain with measured
  cyclomatic complexity 395 became forty handlers behind a dict, complexity
  34, with an import-time assertion tying the dict to `KNOWN_COMMANDS` so the
  two cannot drift (`docs/architecture/CURRENT_CODE_ARCHITECTURE_REVIEW.md`
  lines 300-308, quoting the project's own measurement). Extracting it
  immediately exposed a handler referencing a variable that only existed in
  the old enclosing scope, dead from the moment it was extracted and
  unfindable while it was buried.
* **The household extraction.** Roughly eighty founder-specific attributes
  moved off `Sim` onto `sim/engine/actors/household.py`'s `Household`
  object (`docs/architecture/HOUSEHOLD_EXTRACTION.md`; confirmed live at
  `sim/engine/core.py:377`, `self.household = Household(...)`, with 109
  forwarding properties measured by `grep -c "@property" sim/engine/
  core.py`). This is explicitly **not** the rejected refactor - `HOUSEHOLD_
  EXTRACTION.md` section 5 says so in its own words, because it gives one
  coherent group of fields one owner instead of giving all 157-165 fields
  independent owners.

Both worked because they picked a **coherent subset** (one control-flow
mess, one group of fields that already belonged together) instead of
attempting all of it at once, and both had a specific tool proving the
specific claim they were making (section 5). The staged proposal below is
the same pattern applied to `Sim.step()` and, past that, to individual
mixin-sized pieces of the god object, and it deliberately does not propose
finishing the job the original decision rejected.

### Stage 1: decompose `Sim.step()` into named methods, in place

No files move. No attribute moves to a different owner. No mixin gains or
loses a field. This is a pure textual restructuring of one method into
several, all still defined on `Sim`, all still reading and writing exactly
the same `self.*` state they read and write today.

The method already names its own seams. Its interior comments mark eight
numbered phases (`grep -n "^        # [0-8]\. " sim/engine/core.py`,
restricted to lines 3024-4783), and the line spans between them account for
the entire method exactly:

    preamble (cfg/year locals, before phase 0)                 15 lines
    phase 0: apprenticeship completions                        38 lines
    phase 1: staff                                            271 lines
    phase 2: money                                            203 lines
    phase 3: dated shocks                                     440 lines
    phase 5: progress (project work)                          554 lines
    phase 6: reputation/familiarity/protection/scandal        174 lines
    phase 7: founder mortality                                 62 lines
    phase 8: random events + year increment                     3 lines
    total                                                    1,760 lines

(Phase numbering in the source skips 4; nothing is missing, the spans above
sum exactly to `step()`'s measured length of 1,760.)

A literal cut along these boundaries gives nine private methods
(`_step_apprenticeships`, `_step_staff`, `_step_money`, `_step_dated_shocks`,
`_step_progress`, `_step_reputation`, `_step_founder_mortality`,
`_step_random_events`, plus the short preamble folded into `step()` itself),
each still taking only `self`, called in the same order `step()` calls them
today. That is not the end of the work: phase 3 (440 lines) and phase 5 (554
lines) are each larger than `__init__` (378 lines) and would need a second
internal pass before either one reads as one idea. Costed honestly, Stage 1
is closer to fifteen to twenty short methods once those two are further
split, not nine.

**What this buys, and what it does not.** It makes `step()` readable and
`git blame`-able at method grain instead of line-in-a-1,760-line-function
grain, and it means two engineers working on unrelated phases produce
diffs that touch different, named, non-overlapping regions of the same file
- which directly narrows the kind of collision `Complaints/33` recorded,
where a half-finished cross-cutting edit inside one giant function was easy
to lose track of. It does **not** by itself solve the concurrent-file
problem from section 3: `core.py` is still one file, still 4,861 lines
minus whatever this trims from comment overhead, and two engineers each
assigned a different phase are still committing to the same file and can
still conflict on the same diff hunk if their phases sit next to each other
in the method-ordering. It is a precondition for Stage 2, not a substitute
for it.

### Stage 2: give phases that already belong to one mixin a home there

Once Stage 1 exists as named methods, each one has a measurable attribute
footprint: which `self.*` names it reads and writes, and which mixin's
territory those names belong to (economy, labour, society, and so on - the
same classification `sim/ARCHITECTURE.md` already uses for its distinct-
`self.*`-names-per-file counts). Some phases will be dominated by one mixin
already; `sim/ARCHITECTURE.md` lines 158-166 show the mixins are not evenly
coupled - core -> economy is 62 calls, core -> society only 15 - so it would
be surprising if every phase turned out equally entangled.

For a phase whose footprint is genuinely dominated by one mixin, Stage 2
moves that phase's method (not its data) onto that mixin's class, so it is
defined in `society.py` instead of `core.py`, and `step()` calls
`self._step_reputation()` exactly as it called the in-place version. The
engineer working on reputation now edits `society.py`; the engineer working
on staff edits `labour.py`. This is the first point at which file-level
separation, the thing section 3 asks for, actually exists.

This stage is per-phase, not all-at-once, for the same reason `HOUSEHOLD_
EXTRACTION.md` moved one coherent group of fields rather than all of them:
a phase whose footprint spans three or four mixins roughly evenly should
stay on `Sim` rather than be forced into an artificial home, because forcing
it would be the exact mistake the original decision already named - "moving
the state into a `State` object... would relocate the coupling, not remove
it." Measuring the footprint has to happen before deciding to move a phase,
not after.

### What Stage 2 explicitly does not do, and the option this document does
### not recommend going further into

Neither stage gives the remaining shared fields independent owners, and
neither converts implicit `self.x` reads into passed arguments. That is
still the rejected refactor, it is still a rewrite of most of the engine
by the same estimate the original decision made, and section 2 found no
new evidence that its payoff has grown to match its cost. If Stages 1 and 2
turn out not to be enough - if, after Stage 2, engineers still cannot work
concurrently because the remaining shared surface (mostly `economy.py`,
still the largest file at 6,570 lines and the one every other mixin calls
into most) is still one file everyone touches - that is a real possibility
and section 6 names it as a reason to stop and re-measure rather than push
through to a full field-by-field split by default.

**One thing this document states as a hard constraint, not a design choice,
for any stage that moves an attribute to a different object:** never route
the hot path through `__getattr__` forwarding. `docs/architecture/
HOUSEHOLD_EXTRACTION.md` section 2 measured `self.capital` at 10.2ns per
access, `self.household.capital` at 17.4ns, an `@property` forwarder at
60.3ns, and `__getattr__` forwarding at 519.4ns - 51x the direct access - and
the same document records `revenue()` alone being called 61 million times in
a 45-year run. `__getattr__` is the version that looks elegant because it
leaves every call site unedited, and it is also disproven by this repo's own
benchmark. It has already been re-proposed twice by agents who had not read
this measurement. If Stage 2 or any later stage moves a field, engine-
internal call sites get rewritten to the direct `self.household_or_new_
owner.field` form; a forwarding `@property` (never `__getattr__`) exists
only on the outside surface - the JSON protocol, save/load, the CLI, the
tests - where it is not hot. And for any field that is lazily created today
(its absence in `SAVE_FIELDS` meaning "this has never happened"), the
forwarding property must raise `AttributeError` on absence rather than
returning a default, for the exact reason `HOUSEHOLD_EXTRACTION.md` section
3 and `sim/ARCHITECTURE.md`'s own "green tests" trap both record: an
`getattr(self, x, default)` promoted to a real attribute passed the entire
suite once while silently breaking save-file semantics.

---

## 5. The verification story

This matters more than the plan, because every prior warning in this repo
says the same thing from a different angle: green tests do not mean
unchanged behaviour (`CLAUDE.md` section 6), and the suite "asserts on
outputs and messages... not that the simulation is the same simulation"
(`sim/ARCHITECTURE.md`, "Two things that will bite you").

**`prove_rename_safe.py` does not apply to Stage 1, and this needs to be
said plainly because it is easy to assume otherwise.** It proves that a
change to a function's bytecode is *only* a local-variable rename, by
comparing `co_code` name-aware, `co_names` and `co_consts` exactly
(`sim/prove_rename_safe.py` header, "co_code, name-aware... co_names...
co_consts... must be identical"). Pulling a block of code out of `step()`
into `self._step_staff()` changes `step()`'s own code object: it now
contains a method call that was not there before, in place of the inlined
instructions. That is a real difference by design, and the tool correctly
reports it as one rather than as a safe rename. There is no way to make
`prove_rename_safe.py` bless a method extraction, and no version of Stage 1
should try to lean on it for that purpose. It remains the right tool for a
different job this proposal does not need: if any stage also renames local
variables while it is in a function anyway (`CLAUDE.md` section 7 already
invites this - "fix bad names you pass through, where it is cheap" - and
several one-letter locals live inside `step()`), that rename, and only that
rename, can be proven by this tool, separately from the extraction itself.

**`perf_fingerprint.py record`/`check` is the tool that actually covers
Stage 1, and it covers it well.** It hashes every `SAVE_FIELDS` value after
every simulated year, across nine scenarios spanning five civilisations,
fog on and off, random events on and off, seeded for determinism
(`sim/perf_fingerprint.py`, `SCENARIOS`), and reports the first year any run
diverges. `step()` is exactly the function those nine scenarios exercise
every single year, so this is close to the best-matched case this repo has
for the tool: `Sim.step()` is not a cold path buried behind rarely-hit
`protocol.py` commands, it is called once per simulated year in every
scenario the fingerprint runs, 200 years each. The correct process is: run
`record` before touching `step()`; extract one phase; run `check`; if it
diverges, the report names the first year and the field, which localises
the bug to that one phase's extraction, not to the whole file; fix or
revert that one phase before extracting the next. One phase at a time, one
`record`/`check` cycle at a time, keeps any mistake's blast radius to a
single, independently revertible commit. At roughly six minutes per
`record`/`check` pair (`CLAUDE.md` section 5), extracting the nine phases
one at a time costs on the order of an hour of machine time total, run in
the background between edits rather than as nine consecutive six-minute
blocks.

**Stage 2 needs the same tool, for the same reason**, because moving a
method between classes is exactly as much a change to `step()`'s call graph
as extracting it in place was, and `prove_rename_safe.py` is equally unable
to bless it.

**What neither tool covers, honestly:**

* `perf_fingerprint.py` compares `SAVE_FIELDS`, and `log` is explicitly
  excluded from the compared fields ("`log` is dropped: it is prose, it is
  enormous, and a change to the wording of a message is not a change to the
  simulation" - `sim/perf_fingerprint.py`). A phase extraction that
  accidentally reordered two independent side effects in a way that changed
  only what gets printed, and not any `SAVE_FIELDS` value, would not be
  caught. This is a narrow gap and the kind of thing a diff read catches,
  but it is a real gap, not a rounding error.
* Nine scenarios are nine draws, not an exhaustive branch cover. A rare
  branch inside a phase - the kind that only fires under a specific
  combination of civilisation, year and random draw that none of the nine
  fixed seeds happens to hit in 200 years - can be broken by an extraction
  and pass both `record` and `check` cleanly. This is the same caveat this
  tool has always carried and is why the suite runs alongside it, not
  instead of it.
* Nothing here proves `protocol.py` unchanged, because `step()` is not
  called from `protocol.py`'s hot paths in a way `perf_fingerprint`
  exercises directly, and the original rejection's own bar - "propose it
  with a plan for proving `protocol.py` unchanged" - is still unmet by this
  proposal, on purpose. This proposal does not touch `protocol.py`, and
  should not until that bar has a real answer. `protocol.py`'s own dispatch
  split (section 4) shipped without `perf_fingerprint` coverage and caught
  its one dead-code bug through the test suite and the code becoming
  legible enough to notice on read, not through a mechanical proof - which
  is weaker verification than Stage 1 gets here, not a precedent that
  weaker verification is fine for `step()` too.
* Save/load round-tripping needs its own explicit check per stage, the way
  `HOUSEHOLD_EXTRACTION.md` section 4 already lists it: a save written
  before a stage's change loads after it, and a field absent before stays
  absent after. Neither `perf_fingerprint` nor `prove_rename_safe` verifies
  this on its own; it is a `--session` round trip run by hand or by the
  suite's own save/load tests.
* Wall-clock cost: `perf_fingerprint`'s per-scenario timing output should be
  compared before and after each phase move, specifically to check that
  fifteen to twenty extra Python-level method calls per simulated year do
  not show up as a measurable regression. Given `revenue()` alone runs 61
  million times in a 45-year run and a handful of extra call-frames per year
  is a rounding error against that, this is expected to be free, but
  "expected" is not "measured," and the timing numbers come with the same
  command that proves correctness, at no extra cost.

---

## 6. What could go wrong, and what would stop this

* **The performance trap, stated once more as a hard constraint rather than
  a risk to monitor:** any Stage 2-or-later proposal that reaches for
  `__getattr__` forwarding to avoid rewriting call sites is wrong on its
  face, per the 51x measurement in section 4. If this happens, it is not a
  risk to weigh, it is a rejected design, full stop, the same way it was
  rejected the first two times it was proposed.
* **A `perf_fingerprint` divergence that cannot be explained.** If `check`
  reports a mismatch after a phase extraction and the cause is not obvious
  from the named field and year within, say, one focused debugging session,
  the right move is to revert that one commit, not to keep pushing forward
  on the assumption it will turn out to be cosmetic. This is exactly the
  discipline `Complaints/closed/27`'s postmortem argues for: a plausible-
  looking mechanism is not evidence until it is checked against the actual
  input, and pushing through an unexplained mismatch is how a real bug gets
  waved off as noise.
* **A phase whose footprint does not localise.** If, when Stage 2 measures
  a phase's `self.*` footprint, it turns out to be spread roughly evenly
  across three or more mixins rather than dominated by one, that phase
  should stay on `Sim`. Forcing it into a home it does not have is the same
  mistake the original decision already named for the full refactor, at
  smaller scale.
* **Stage 1 lands but the concurrency complaint does not improve.** If,
  after `step()` is fully decomposed into named methods, engineers report
  the collision problem is unchanged, that is evidence the actual
  contention was never `step()`'s length in the first place - `economy.py`
  at 6,570 lines is the largest file in the engine and the one the other
  mixins call into most (`sim/ARCHITECTURE.md` lines 158-161: `economy ->
  projects` 43 calls, `core -> economy` 62) - and Stage 2's premise, that
  moving phases to their natural mixin home reduces contention, needs to be
  checked against real collision data before more effort goes into it. This
  is also worth separating from a pure code-shape question: `Complaints/33`
  ultimately turned on a shared git index across agents, a workflow problem
  `git commit -o <pathspec>` fixes directly and no file split fixes at all.
  If most future collisions turn out to be that kind, the right fix is a
  commit-hygiene rule, and no amount of decomposition substitutes for it.
* **Scope creep back toward the rejected refactor.** The clearest failure
  mode is Stage 2 succeeding on a few phases and someone reading that as
  license to keep going until all 165 carried attributes have explicit
  owners. That is the change section 2 found no new evidence for. Each
  stage should be justified on its own, against real contention data, not
  as a down payment on the full rewrite.

---

## 7. Recommendation

Do Stage 1. Do not do more than Stage 2, and only do Stage 2 where a
phase's footprint measurably belongs to one mixin. Do not restart the full
field-by-field decomposition the original text rejected; nothing measured
here changes that comparison's conclusion, only the size of the file it was
made about.

Stage 1 is cheap, independently revertible phase by phase, has a
well-matched verification tool (`perf_fingerprint.py`, run once per phase,
roughly six minutes each), and is valuable even if Stage 2 never happens:
`step()` at 1,760 lines is unreadable and un-review-able regardless of which
file it lives in, and `Complaints/33` already shows what that costs in a
shared checkout. Start it now.

Stage 2 should follow only where the footprint measurement (a prerequisite
this document has not done, because it requires Stage 1's named methods to
exist first) shows a phase genuinely belongs to one mixin. Where it does not,
leave the phase on `Sim` and say so, rather than force a home that
recreates the coupling one file over - which is the specific mistake the
original decision was written to prevent, and remains a mistake regardless
of who is asking to reopen the question.

After Stage 2, stop and re-measure against the actual complaint: are
engineers colliding less. If yes, this was the right amount of change and
the full refactor stays rejected. If no, the next document should look
directly at `economy.py`, not at reopening the field-by-field split by
default, because section 6 already names `economy.py` as the file most
mixins call into and the more likely site of real contention.
