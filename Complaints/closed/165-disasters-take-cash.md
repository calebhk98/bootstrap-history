# Wealth exposure: disasters take cash, confiscation risk is hidden, and nothing shelters money

**Status:** closed - deferred to mods; listed in mods/TASKS.md

"fire in the insula district ... destroyed" 10,763 (120 AD), 77,957 (132), 1,662,217 (177), 3,597,323 (218), 3,825,853 (227); "banditry or a frontier war ... cost you" 757,232 (177), 1,399,197 (197). In 177 the two took about a quarter of the cash held. Sackings in the third-century crisis took most of the cash each time (14.1M of ~17M in 235).

It is unclear what a tenement fire burns when the wealth is coin. If exposure of idle money is intended, `risk`/`help money` should say so. There is no way to protect cash (no bank, deposits elsewhere, or letters of credit), so the correct play before a known crisis is to spend everything.

What it would take: say what the loss is proportional to; give at least one data-driven way to spread or shelter wealth.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.

## Merged from 182: treasury confiscation and lapsed hedges

"THE TREASURY IS LOOKING AT YOUR FORTUNE: a 1% chance this year of outright confiscation" (568 AD), "a 5% chance" (593 AD), each shown only in that year's step output; `risk` and `state` never list it. Its protections ("holdings too dispersed to be seized at a stroke") are not explained anywhere else. Converting ~200M of cash into land (forest, farm) was followed by no further warnings.

Similarly "(lapsed)" hedges in plague messages (boiled water, quarantine, smallpox vaccine) mean the concern providing them is closed; nothing tells the player which concern to reopen.

What it would take: list confiscation chance and its current protections on `risk`; name the concern behind each lapsed hedge.

(Merged from 182.) Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.

Also reported (Han China 100 AD fog playtest, tester item(s) 47, 118, 132, 149, 185; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): a fire destroyed nothing when cash was already negative (123 AD) and 10 billion when it was positive, which reads as a cash-only hazard with no physical premises; property seizures of 7, 11, 25 and 74 billion came after treasury notices that printed a rounded 0 percent, later 5 and 10 percent; 92 percent protection did not prevent them. They ask for decimals or "less than 1 percent", exposure separated from eminence, and ways to shelter money (endowments, diversified assets). Reproduces: untested (late game).

**Remaining (audit check):** `risk` now prints "TREASURY CONFISCATION: N% chance this year" with what holds it off and what is not yet in force (`confiscation_status` via `sim/ui/proto/dispatch_inspection.py`, rendered by `_confiscation_lines` in `sim/ui/proto/render_screens_status.py`), and step output names the closed concern behind a "(lapsed: ...)" hedge (`sim/ui/proto/step_problems.py`); both checked with `risk` in a new Rome game. Still open: what a cash-only disaster is proportional to is not stated, there is no way to shelter cash (held as a candidate mod), and the treasury notice rounds small chances.
