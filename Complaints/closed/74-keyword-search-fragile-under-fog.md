# Literal keyword search is too fragile under fog

Searching terms such as `education`, `literacy`, or `academy` could miss visible technologies that were obviously relevant because their names used different vocabulary. Surveying mechanical power required trying many literal words such as gear, shaft, belt, crank, steam, rotary, drive.

## WHY IT MATTERS

Players cannot discover relevant technologies efficiently. Useful items hidden behind synonym mismatches become effectively undiscovered, forcing brute-force exploration or knowledge of naming conventions.

## WHAT WOULD RESOLVE IT

Add semantic/tag filters:
- Education
- Public health
- Agriculture
- Mechanical power
- Transmission
- Precision measurement
- Printing/information
- Transport
- Finance
- Institutions
- Military logistics

Fog can safely expose a visible node's broad category without exposing hidden descendants.

## WHERE IT LIVES

`sim/engine/proto/techtree.py` for research tree, `sim/engine/proto/dispatch.py` for search command handling. Tag/category metadata would live in `data/` tree structure or tech node definitions.

## Confidence

Design recommendation

## Cross-references

Related to UX-003 (filter views need better state visibility). UX-002 (fog directional hints) overlaps - better categories also help under fog.
