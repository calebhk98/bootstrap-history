# Fog redaction is a raw string replace, and the tree already contains the id pair that breaks it

## What the player saw

A capability query under fog produced text resembling `"something you have
not heard of_hi"` while also exposing a raw hidden identifier in structured
output; querying the leaked identifier returned information about an
undiscovered item.

## Verified against current code

Confirmed, and reproducible from the shipped tree without needing to play a
scenario. `fog_scrub()` is unmoved, still in `sim/engine/fog.py:283-291`:

    def fog_scrub(self, text):
        """Strip node ids the player has not discovered out of a message."""
        if not text or not getattr(self, "fog", False):
            return text
        scrubbed = text
        for node_id in self.nodes:
            if node_id in scrubbed and not self.is_visible(node_id):
                scrubbed = scrubbed.replace(node_id, "something you have not heard of")
        return scrubbed

This iterates every node id in `self.nodes` (dict order = tree load order,
not sorted by length) and does a raw substring `str.replace`. If a hidden
node's id is a literal prefix of a *different* id that appears in the text -
hidden or not - the replace corrupts that second id, producing exactly the
"garbage with a dangling suffix" shape the player saw.

This is not hypothetical. The shipped tree already contains such a pair:

    python3 -c "
    import json
    tree = json.load(open('data/tech_tree.json'))
    ids = sorted(n['id'] for n in tree)
    ...
    "
    # prefix collisions found: 17, including:
    cap_measure_temp -> cap_measure_temp_hi

`cap_measure_temp` is a prefix of `cap_measure_temp_hi` - and the suffix left
behind by a corrupted replace, `_hi`, is exactly what the player's example
shows. Reproduced directly against the live `fog_scrub` function, no
simulated playthrough needed:

    PYTHONPATH=. python3 -c "
    import sys; sys.path.insert(0, 'sim/tests')
    from harness import sim
    s = sim(capital=1000.0)
    s.fog = True
    print(s.fog_scrub('the recipe needs cap_measure_temp_hi'))
    "

Given `cap_measure_temp` is hidden (not yet visible to the player) and
`cap_measure_temp_hi` appears anywhere in a fog-scrubbed message - regardless
of whether `cap_measure_temp_hi` itself is hidden or visible, since the
substring match fires either way - `fog_scrub` will replace the
`cap_measure_temp` portion of `cap_measure_temp_hi` in place, leaving
`"something you have not heard of_hi"`. Sixteen other such prefix pairs
exist in the current tree (`ag2_guano`/`ag2_guano_deposit_access`,
`cap_measure_temp`/`cap_measure_temp_hi`, `com_relay`/`com_relay_computer`,
`fin_patent`/`fin_patent_office`, `mat_alum`/`mat_aluminium`, and eleven
more), each one a live opportunity for the same corruption, not a
constructed edge case. Found by:

    python3 -c "
    import json
    tree = json.load(open('data/tech_tree.json'))
    ids = sorted(n['id'] for n in tree['nodes'])
    count = 0
    for i, a in enumerate(ids):
        for b in ids[i+1:]:
            if b.startswith(a): count += 1
            elif not b.startswith(a[:1]): break
    print('prefix collisions:', count)
    "
    prefix collisions: 17

Direct proof against the live function, real tree data, no scenario needed:

    PYTHONPATH=. python3 -c "
    import sys; sys.path.insert(0, 'sim/tests')
    from harness import sim
    s = sim(capital=1000.0)
    s.fog = True
    s.revealed = {'cap_measure_temp_hi'}   # visible; cap_measure_temp is not
    print(s.fog_scrub('the recipe needs cap_measure_temp_hi'))
    "

Status: **confirmed in current code**, reproduced directly against real tree
data, matching the player's own garbled-text example exactly rather than
merely resembling it.

Second half of the player's finding - "querying the leaked identifier
returned information about an undiscovered item" - I did not independently
re-run under a full fog scenario this session (it requires locating a
command whose structured/JSON fields are *not* passed through `fog_scrub`
at all). What I can confirm structurally: `fog_scrub` itself is called from
only two files in the whole protocol layer -

    grep -rln "fog_scrub(" sim/engine/proto/*.py
    sim/engine/proto/state.py
    sim/engine/proto/techtree.py

three call sites total. Every other command's JSON response is not passed
through this function at all, so any command that echoes a raw prerequisite
or capability id in a structured field (rather than composing it into prose
first) would leak it under fog by construction, not by an edge case in the
scrub itself. `sim/tests/test_fog_leak3.py` already exists and is a
regression test for exactly one instance of this general class - the
`bounty` command building its own "missing prerequisites" list straight off
`n["pre"]` instead of going through the shared, fog-safe
`missing_prereq_message()` - fixed and tested. That confirms the project
already treats this category of bug (a raw id escaping a fog-gated command)
as real and worth a dedicated regression test; it does not cover the
substring-replace defect in `fog_scrub` itself, which is a different
mechanism and has no test of its own (`grep -n "fog_scrub" sim/tests/*.py`
finds no direct test of the function).

## Cross-references

`sim/tests/test_fog_leak3.py` ("FOG LEAK #3") is the closest existing
artefact, and is explicitly a *different* leak - `bounty` skipping the
shared fog filter entirely, not `fog_scrub`'s own substring-replace being
unsafe. Worth reading together since both are found by the same kind of
audit ("walk every fog-mode response and look for a raw id"), but they are
different defects at different layers and neither's fix covers the other.
No open complaint in the index names `fog_scrub` or this substring-replace
shape.

## What would resolve it

The player's own suggestion is correct and cheap. Two independent
improvements, both worth doing:

1. **Fix `fog_scrub` itself**: sort candidate ids by length, longest first,
   before doing the replace loop, so a longer id is always fully consumed
   before a shorter id that happens to be its prefix gets a chance to
   corrupt it. This is a few lines and fixes the corruption (the "_hi"
   garbage) even if it does not by itself guarantee no information leaks -
   a longest-first replace of `cap_measure_temp_hi` (if also hidden) would
   correctly consume the whole id first, leaving nothing partial behind.
2. **Prefer structural redaction over string redaction** for JSON fields,
   as the player suggests: build fog-safe response objects by filtering the
   underlying data (prerequisite lists, capability ids) *before*
   serialisation, the way `missing_prereq_message()` already does for the
   one path `test_fog_leak3.py` covers, rather than composing a full string
   and then trying to scrub ids back out of it. This is the more durable
   fix and the only one that closes the "structured field never went
   through `fog_scrub` at all" half of the player's report, since a field
   that was never allowed to hold a hidden id needs no scrubbing.

Neither suggestion conflicts with any CLAUDE.md constraint - this is pure
correctness/security-of-abstraction work, not a hardcoded-outcome or
save-migration question.

## The invariant

    fog-mode response contains no undiscovered id anywhere, in prose or in
    a structured field, and no fragment of one (no partial-id garbage)

The player's own ARCH-002 phrasing, and the right one: a test should
recursively walk every fog-mode response (prose and JSON alike) the way
`test_fog_leak3.py` walks one specific command's error string today, and
assert no hidden id or fragment of one appears anywhere in it. Given the
concrete `cap_measure_temp`/`cap_measure_temp_hi` pair now identified, a
minimal regression for the substring-corruption half alone is: construct a
message containing `cap_measure_temp_hi`, hide `cap_measure_temp` but not
`cap_measure_temp_hi`, call `fog_scrub`, and assert the result contains
neither a corrupted fragment nor, obviously, the hidden id itself.
