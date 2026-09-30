# Request: staff and labour needs shown as uncertain estimates while something is unknown

**Status:** open

The stakeholder's request: an option (in the spirit of `--fog`) where, before and while you research something, the screens do not tell you exactly how many people of which trade it needs. You know roughly what making toys involves, not the exact crew. Today `why`, `available` and `start` give exact figures (STAFF NEEDED, STAFF TO KEEP IT OPEN, the specialist foreman, HIRED LABOUR hours), which makes planning a new venture more certain than it should be.

## The proposed number

For each labour figure the player sees, show

    shown_value = real_value - real_value * random_a + real_value * random_b

with `random_a` and `random_b` independent uniform draws on [0, 1]. That is `real_value * (1 - random_a + random_b)`: never negative, at most twice the real value, a triangular spread centred on the real value (the most likely shown figure is the true one, and the average over many draws is exact). A true need of 4 craftsmen could show anywhere from 0 to 8, usually near 4.

Possible extension from the request: list several trades as candidates (including some the work turns out not to need), each with an estimate, so the player is also unsure which trades matter, not only how many.

## Design constraints (from CLAUDE.md and the existing fog code)

- Draw each estimate once per actor per node and store it (save/load round-trips it); re-rolling on every `why` would let a player average the noise away by asking repeatedly.
- The estimate should tighten as knowledge grows: when the project starts, as its hours are spent, and when a closely related node is already built. Completion reveals the true figure.
- Only the display is fuzzy. Hiring, the start check and supervision keep using the real value, so a player who under-hires finds out when `start` or `open` refuses (the refusal message then states the real need).
- General actors: a firm, state or other player sees its own estimate, not the founder's.
- A settings/`play` option, off by default, alongside `--fog` (the existing fog code in `sim/engine/fog.py` is the place to look).
- No content ids; the noise applies to whatever labour fields a node has.

## Stakeholder decisions

1. Fuzzy: labour counts and trades, and also money cost, founder hours and the calendar floor.
2. Wrong trades: yes, list a few candidate trades the work does not need, each with an estimate, alongside the real ones.
3. When the truth is revealed (left to the project manager): estimates are drawn when a node is first shown; they tighten at `start` (the spread halves) and keep narrowing in proportion to the work done; completion shows the exact figures. A refusal at `start`/`open` states the real need of the refused resource. The decoy trades drop out at `start`.
