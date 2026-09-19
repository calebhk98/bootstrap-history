# Demographic catastrophes should dominate the main state screen

The Mexica population could collapse by 50-70% in a wave, but the main state presentation still gave substantial visual attention to workshop supervision and small project details.

## WHY IT MATTERS

Population collapse is one of the most important facts in the civilization. When it is buried among routine details on the state screen, players may miss or minimize its strategic importance, leading to poor decisions about recovery, resource allocation, and risk management.

## WHAT WOULD RESOLVE IT

When annual population change exceeds a threshold, put it near the top:

```text
DEMOGRAPHIC EMERGENCY
Population -69% this year
Working-age pool -...
Expected wage pressure +...
Farm labor / urban labor consequences...
```

This is one of the most important facts in the civilization.

## WHERE IT LIVES

`sim/engine/proto/render_screens_status.py` or main state screen rendering. Population change detection and alert priority logic.

## Confidence

Design recommendation

## Cross-references

Related to BUG-001 (local labor market larger than surviving civilization), BUG-013 (event quantities impossible after demographic collapse), and UX-014 in the findings.
