# A plague plan you shut down still protects you from the plague

`plague_preparedness` is a venture. It can be opened, it costs upkeep, and
it can be closed:

    python3 -c "import sys, os; sys.path.insert(0, os.path.abspath('sim'))
    sys.path.insert(0, os.path.abspath('sim/tests'))
    from harness import sim as make_sim
    print(make_sim().is_venture('plague_preparedness'))"
    True

Its hazard relief is read through `HAZARD_COUNTERS`, and
`SocietyMixin.hazard_relief` resolves every counter with `self.has(node)`:

    got = self.has(node)          sim/engine/society_hazards.py

and `has` is one line:

    def has(self, k):
        return k in self.household.done          sim/engine/core.py

`done` means finished, ever. So a player who builds a plague preparedness
programme, then closes it a century before the Antonine plague arrives,
keeps the entire staff-loss relief. Nothing in the engine asks whether the
programme is still open when the plague lands.

## The three-way disagreement

There are two questions and the codebase answers them inconsistently.

`has(node)` asks: was this ever finished?
`running(node)` asks: is it finished AND still a going concern?

For most capabilities the engine is careful about the difference.
`projects_capability.py`'s `NOT_OPERATING_BENEFIT` table exists precisely to
warn a player that closing an institution costs them something, and it names
what each one pays for: academy_network's training and standing,
collegium_licensed's capacity and credit, and so on. `running()` gates those.

`plague_preparedness` is deliberately absent from that table, and the comment
says why:

> `plague_preparedness` is the one `CAPABILITY_INSTITUTIONS` member
> deliberately absent: its only `running()`-gated reference left in the
> engine is a dead local (`prep` in society.py's `_shocks`) that nothing
> reads, and its real hazard relief (`HAZARD_COUNTERS`) is `has()`-gated
> like corpus - so closing it costs nothing measurable today. Warning about
> it anyway would be exactly the false alarm this exists to avoid.

Read that carefully. The reasoning is sound given its premise, and the
premise is the bug. Closing plague preparedness costs nothing measurable
BECAUSE the relief is `has()`-gated, and the question nobody asked is
whether `has()` is the right gate for a plague plan.

## Why corpus is not the precedent it looks like

The comment justifies `has()` by analogy with the corpus, and for the corpus
the analogy is argued properly, at `core.py`'s own `has`:

> a corpus that is written and dispersed does not stop existing because the
> scriptorium that produced it closed - copies already in other people's
> hands are still in other people's hands

That is a real physical argument. Copies exist independently of the
institution that made them, so `has()` is correct there, and that same
comment records that the sack path and the `risk` screen once disagreed
about exactly this and drifted apart until one was fixed and the other was
not.

A plague preparedness programme is not copies in other people's hands. It is
quarantine procedure, stockpiles, trained people and a standing plan. Those
are the things that decay when nobody is paid to maintain them. The corpus
argument does not transfer, and nothing in the repository argues the
transfer.

## The evidence that a different answer was once intended

`SocietyMixin._shocks` opened with

    prep = self.running("plague_preparedness")

computed once per year, immediately before the hazard loop, and never read.
Somebody wrote the `running()` call, in the right function, at the right
moment in the year, and the branch that would have used it either never
landed or was replaced by the `HAZARD_COUNTERS` mechanism without anyone
deciding which gate was correct.

That line has now been deleted, as an unused local, in commit `ad627c2`.
Deleting it was right on its own terms and it has a side effect worth
recording here: the comment quoted above cites that dead local as evidence
for its own decision, so it now points at a line that no longer exists.
Anyone re-deriving the reasoning will find the citation dangling.

## What is actually being asked

Three defensible answers, and the project should pick one on purpose rather
than inherit this one:

1. **`has()` is right.** A plague plan once made leaves permanent residue:
   people who know what to do, written procedure, a public that has been
   through it once. Then say so where `HAZARD_COUNTERS` is defined, and add
   `plague_preparedness` back to `NOT_OPERATING_BENEFIT` with "nothing", so
   the absence is a decision rather than a gap.
2. **`running()` is right.** Stockpiles rot and trained people disperse, so
   closing the programme should cost the relief. Then the counter needs a
   `running()` gate and the warning table needs the entry.
3. **Neither, and it decays.** Relief falls off over the years since the
   programme closed, which is the most honest of the three and the only one
   that needs new mechanism rather than a changed call.

CLAUDE.md SS3.4 requires that a heuristic nobody can yet derive be labelled.
This one is not labelled, because nobody noticed a choice was being made.

## How to see it

Build `plague_preparedness`, close it, and run an Antonine plague. The
staff-loss relief is identical either way, and the ledger says nothing about
the closed programme still paying out. The cheapest version is to read
`hazard_relief` and `has` side by side, which is four lines between them.

## Status

Filed, not fixed. Fixing it means choosing one of the three answers above,
and that is a modelling decision rather than a defect to patch. The
`NOT_OPERATING_BENEFIT` comment should be corrected either way, because its
citation is now dangling whichever answer wins.
