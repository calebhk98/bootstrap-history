# The hand needle has no node, and fireclay needs a node no start can hold

**Status:** closed

Found while making the starts agree with themselves (Complaints/336, 127).

- `tx2_needle` ("polished iron or steel with eye") and `tx2_eye_pointed_needle` (the machine-sewing needle) both require `cap_tol_100um`, whose chain runs through `precision_three_plate` and `case_hardening`. Roman, medieval and Norse hand needles were made without that rung, so those starts could not honestly hold either node and lost them. The tree needs a hand-needle node on `cap_tol_1mm` (bone, bronze or drawn-iron needle), and the two existing nodes should keep the 0.1 mm rung. `python3 sim/simulator.py why tx2_needle` shows the chain.
- `cap_heat_1100` requires `refractory_fireclay`, which requires `workshop_first` (the founder's own setup node, which needs `patron_local` and `identity_cover`). Rome, England, Norse and Han hold the first two, so each is a pinned prerequisite violation (`sim/tests/test_civilisation_prerequisites.py`). Either the tree should not require the founder's workshop for a refractory that existing societies use, or the starts should hold the setup chain; neither was decided here.

**Resolved:** `tx2_needle_hand` (millimetre rung, iron or bone) is held by Rome, England, Norse and Han; `tx2_needle` and `tx2_eye_pointed_needle` keep the 0.1 mm rung. `refractory_fireclay` now requires `cap_heat_0700` (clay, sand and a kiln; nothing physical needs the founders workshop), so the four fireclay-holding starts hold its prerequisite and the pin shrank by four. Mexica does not hold the hand needle: its recipe uses iron bar, which Mexica cannot make.
