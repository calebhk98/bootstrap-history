# WITHDRAWN: the "undefined global in `Sim.step`" was an artefact I created and then diagnosed

**Type:** Retracted finding / process failure
**Priority:** The retraction is low. The lesson is high.

**Status: the bug described below DOES NOT EXIST and never did.** This file is
kept rather than deleted because the way it came to be written is worth more
than the thing it claimed.

## What this complaint originally said

That `sim/engine/core.py` contained two reads of an undefined global `n`
inside `Sim.step`, at lines 1971 and 2438, which would raise `NameError` if
reached and were therefore dead code sitting in the engine's main tick. It
was asserted with a disassembly, a count of `LOAD_GLOBAL` instructions, and a
list of every non-builtin non-module global in the function. It was
confidently wrong.

## What was actually true

```
c25259b  (before naming round 3)   LOAD_GLOBAL 'n' in Sim.step: 0
39f5d14  (before naming round 3)   LOAD_GLOBAL 'n' in Sim.step: 0
993b2c7  (the commit that introduced it)  LOAD_GLOBAL 'n' in Sim.step: 2
```

At every real commit in this repository's history, `n` in `Sim.step` is a
plain local: present in `co_varnames`, absent from `co_names`. The two
`LOAD_GLOBAL` instructions exist in exactly one commit, `993b2c7`, and that
commit is mine.

## How I created it and then found it

`993b2c7` is the burndown fix. I staged three files explicitly. It committed
six, because six agents shared this checkout AND its git index, another
session had staged into that index first, and `git commit` commits the index
rather than what you just added. One of the three extra files was
`sim/engine/core.py`, caught mid-rename: an agent had renamed the local `n`
to `node` at its binding site but had not yet reached those two references,
so `n` there was briefly an unbound name that compiled to `LOAD_GLOBAL`.

I then ran `prove_rename_safe.py` against HEAD. HEAD was my own broken
commit. The prover correctly reported that `co_names` had lost `n`, meaning
the working tree was closer to correct than the thing I was comparing it to.
I read that backwards, disassembled the broken commit, found exactly what a
half-finished rename looks like, and wrote it up as a latent engine bug -
including a section on how not to fix it, and a paragraph congratulating the
bytecode proof for finding something the test suite could not.

Then I messaged the agent and told it to revert the two sites to match the
broken state. **It refused, with evidence**, and was right to. An agent that
had done as it was told would have reintroduced a `NameError` that had never
existed, in a commit whose message said it was restoring correctness.

## The lesson, which is the reason this file survives

`CLAUDE.md` 6 already says "when you instrument a bug, the instrument is
part of the experiment". This is the same failure one level up: **the commit
was part of the experiment.** I created a state, made it the baseline,
compared against it, and could not tell my own artefact from the code's
history - because once committed, an artefact looks exactly like history.

Three specific things to carry forward:

1. **In a shared checkout, `git commit` takes the INDEX, not your files.**
   Use `git commit -o <pathspec>`, which commits only the named paths
   whatever else is staged. I learned this the shallow way once already this
   session - after a directory-level `git add` swept in a file another agent
   was still writing - and wrote down "stage files, not directories", which
   was too weak a rule to prevent the recurrence.

2. **`HEAD` is not a baseline in a shared checkout.** Prove against a fixed
   commit chosen before the work started. Two agents worked this out
   independently and both anchored to `39f5d14` instead of `HEAD`, which is
   why their proofs were sound while my diagnosis was not.

3. **A finding that arrives with a clean mechanism deserves MORE suspicion,
   not less.** Every piece of evidence here was real: the instruction counts,
   the `co_names` diff, the absent module-level binding. The disassembly was
   correct. The input was wrong, and a correct method on a wrong input
   produces a confident, well-evidenced, wholly fictitious result.

## Also withdrawn

The claim, made in `dcf84a0`'s commit message and elsewhere, that this was
"the first time on this branch the bytecode proof found something the test
suite could not". It found a mid-edit file, which is what it is for, and the
suite would have caught the same thing had it been run against that commit.
The prover's real wins on this branch are the naming rounds, where it proved
roughly 900 renames inert across sixteen files - which is a better result
than the one I invented for it.
