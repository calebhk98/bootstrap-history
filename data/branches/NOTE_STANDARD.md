# Standard for node notes

The `note` of a node is the player's only description of it, and under fog it is the only clue.
A player who does not know the vocabulary cannot reason to the next step, so a note teaches
the thing from zero. Write it in plain English, in a few sentences, covering four parts:

1. **What it is.** Name the thing in ordinary words. Say what it is for before what it is called.
2. **How it works.** The physical or social mechanism: what acts on what, and what comes out.
3. **What it needs.** The inputs, tools, materials, skills or surrounding institutions that make it possible, and which prerequisite supplies each.
4. **Why it is hard, and what the founder must do.** What goes wrong (the failure mode, the scarce input, the resistance) and what the founder has to arrange or do in person to get past it.

## Rules

* A specialist term is explained where it first appears in the note (for example "retting, soaking
  flax stems until the woody part rots away from the fibre"). Do not leave the player a word they must look up.
* Spell names out. No abbreviations a newcomer would not know.
* Physical facts may be stated (a melting point, a ratio set by chemistry). Prices, wages, dates of
  adoption, output volumes and anything else the simulation computes are not written into a note,
  because they go stale and would hard-code an outcome.
* No audit markers, review tags, patch history or words such as "previously" (Complaints/122). A
  note is player text, not a changelog.
* If you are not sure how a technique works, say less. A short true note beats a long invented one.
* The knowledge doc named by the node's `kb` field is the source; the note summarises it for a
  player and does not contradict it.

## Audit

`python3 sim/simulator.py validate` prints how many notes fall below the minimum length and lists
the first few; any such note is an error. The screen is length only (`sim/engine/validate_note_quality.py`);
meeting the four parts is the author's job and the reviewer's.
