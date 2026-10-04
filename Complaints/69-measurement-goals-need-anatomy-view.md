# Measurement goals need a dedicated "anatomy" view

**Status:** partly - `anatomy` (`sim/ui/proto/anatomy.py`, test `sim/tests/test_ui_anatomy.py`) explains a measurement goal or a named metric: literacy from the education figures, epidemic relief from the defences, attribute and generation-share goals by their source, and a generic answer for any other metric; remains: the engine hook that would make every metric generic (422), and no shipped goal exercises the attribute or generation-share builders

For the literacy goal, the most useful information was scattered across `state`, `why`, population/labor screens, and technology effects. The goal card showed current literacy and a ceiling, but not enough explanation of why the ceiling was where it was or what was moving it.

## WHY IT MATTERS

A player working toward a non-research goal cannot understand or predict the goal metric without manually cross-checking multiple screens and subsystems. This makes strategic planning difficult.

## WHAT WOULD RESOLVE IT

For literacy, show together:
- current general literacy
- current elite literacy
- current general ceiling
- annual/expected literacy drift
- whether schools are actually teaching
- schooling flow / active school and academy capacity
- printing/information diffusion modifier
- percentage of agricultural labor considered freed
- major active constraints
- recent changes and their causes

This should not reveal fog-hidden node identities. It should explain the live equation.

Generalize to every non-research/measurement goal with the question: "What controls this number right now?"

## WHERE IT LIVES

Likely `sim/ui/proto/render_screens_big.py` or `render_screens_status.py` for goal presentation. May need new screen in `sim/ui/proto/` to handle goal-specific anatomy views.

## Confidence

Design recommendation

## Cross-references

Related to the goal/path UI systems touched by UX-030 (goal/path UI can teach wrong strategy).
