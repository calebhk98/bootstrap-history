# Persistent shortages should become status conditions, not identical annual messages

**Status:** open

Messages such as "buy ~1 more hectare of coppice" repeated year after year with nearly identical wording.

## WHY IT MATTERS

A stable shortage that persists for years is important state information, but when it generates an identical message every turn, the player learns to ignore it. The signal disappears into noise.

## WHAT WOULD RESOLVE IT

Create persistent conditions:

```text
CHARCOAL CONSTRAINED
Throughput: 46%
Deficit: 12.4 t/year
Duration: 4 years
Trend: improving
Pending relief: 500 t/year coal shaft in 1 year
```

Only generate a new event when the condition materially changes.

## WHERE IT LIVES

`sim/engine/proto/render_screens_economy.py` for capacity/shortage display, `sim/engine/proto/render_screens_status.py` for status condition rendering. Also event generation logic that creates shortage messages.

## Confidence

Design recommendation

## Cross-references

Related to the repetition audit in the findings (section 5, item 5: "Persistent resource warnings"). UX-009 in findings is this complaint.

Also reported (England 1300 fog playtest): the annual charcoal message kept saying "about 1 more hectare" for years while the tester bought a hectare in each of several successive years (five in all) and clear glass was still throttled. They suspect it is correct because demand keeps moving, but it looks like a stuck recommendation; asked for the message to show supply against demand in tonnes a year so the causal picture is visible. The advice text is built in `sim/engine/economy_freight.py` ("Charcoal is grown, not bought: about N more hectare"). Report: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`.

Also reported (Han China 100 AD fog playtest, tester item(s) 101; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): the coal shortage warning kept recommending a new mine of the full demand size every year after 21,000 t/yr of coal mines had been commissioned (see 239 for the code path). Repeats each year unchanged until the mines are producing.
