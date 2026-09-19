# Project-start boilerplate repeats too often

Repeated `start` commands re-explain fixed-price/quote behavior and related model semantics. The explanation is useful once and then becomes noise.

## WHY IT MATTERS

Tutorial-level text repeated hundreds of times becomes cognitive overhead. Players who understand the mechanic waste time re-reading the same explanations instead of seeing information that has changed.

## WHAT WOULD RESOLVE IT

Use progressive disclosure:
- first occurrence: full explanation
- later: compact indicator such as "price locked at start"
- detailed explanation available through `help` or an expanded field

The same principle applies to repeated FTE/supervision explanations.

## WHERE IT LIVES

`sim/engine/proto/dispatch_money.py` or venture command rendering. Likely also `sim/engine/proto/render.py` or related output formatting for project-start messages.

## Confidence

Design recommendation

## Cross-references

Related to UX-008 in Complaints/08 pattern. Also connects to the repetition audit in section 5 of the findings document.
