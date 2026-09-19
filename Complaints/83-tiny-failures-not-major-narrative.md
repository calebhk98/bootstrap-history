# Tiny failures should not get the same narrative weight as major failures

A failed near-zero-cost technique should be one compact line. A failed blast furnace, power grid, vacuum tube, or crystal-growth program deserves detailed consequences.

## WHY IT MATTERS

When all failures receive the same narrative attention regardless of consequence, the important failures are lost in noise. Players cannot distinguish between a bump in the road and a strategic setback.

## WHAT WOULD RESOLVE IT

Scale output by lost:
- capital
- hours
- calendar years
- strategic importance

Provide multiple verbosity levels - compact for trivial failures, detailed for major ones.

## WHERE IT LIVES

Failure event rendering and narration logic in `sim/engine/proto/render_screens_big.py` or project-failure modules.

## Confidence

Design recommendation

## Cross-references

Related to UX-011 (event severity needs visual hierarchy), UX-012 (large completion waves), and the repetition audit (section 5, item 8: "Tiny failure narration").
