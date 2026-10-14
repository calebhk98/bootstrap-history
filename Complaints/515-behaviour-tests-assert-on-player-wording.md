# Behaviour tests assert on player-facing wording

**Status:** open

Several tests that check what the model does read it from the text a screen prints (for example
`round8g_display`'s `path` checks and `interface_honesty`'s EARNS/YR checks, fixed in the
`fix-red-slow-ui-topics` merge). When the wording or the rounding changes, the check fails although the model
did not change; when the model changes, a reworded message can hide it. 362 (all player text moves to `sim/ui/`)
makes this worse if it is not fixed first.

Rule (owner, 2026-10-14): a test of model behaviour asserts on structured values (the engine's numbers or the
JSON reply's fields). Only a test whose subject is presentation (units, wording, rounding, layout) asserts on
text. What it would take: list the tests that match on reply text outside UI topics
(`grep -rln "in reply\[\|\"text\"\]\|assertIn(.*str(" sim/tests` is a starting point; no committed command yet),
move each onto the reply's fields, and add the rule to CLAUDE.md section 6.
