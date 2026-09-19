# Interface repetition is a class of UX problem worth addressing systematically

Repetition was a significant UX cost in the playtests. The underlying simulation did not feel repetitive when values and consequences changed; the interface often did.

A useful rule:

> Repetition is bad when the same information is shown with the same wording and no new decision.

## Ten sources of repetition identified

1. **Fog blockers** - repeated "something you have not heard of" with little/no improved direction. See UX-002.

2. **Research filters** - blocked items continue appearing when the practical question is "what can I do now?" Needs startable-vs-blocked modes. See UX-003.

3. **Project-start boilerplate** - fixed-price/quote semantics repeatedly re-explained. See UX-008.

4. **FTE/supervision explanations** - valuable tutorial text, excessive once understood. See UX-008.

5. **Persistent resource warnings** - same coppice/charcoal suggestion repeated every year with identical wording. See UX-009.

6. **Event fragmentation** - one invasion/sack creates many similarly weighted log lines. See UX-010.

7. **Large completion waves** - dozens of individual completion messages after strategic information becomes aggregate. See UX-012.

8. **Tiny failure narration** - insignificant failures receive too much prose. See UX-013.

9. **Closing concerns message** - "you know how to run N more concerns" useful early, less useful when player knows dozens intentionally. Related to UX-020.

10. **Huge project lists** - project-by-project statuses remain verbose after bottleneck summaries become meaningful. See UX-020.

## Recommended UI philosophy for mature turns

Default mature-turn output should follow this structure, making major changes prominent and supporting progressive disclosure:

```text
YEAR 1606 -> 1607

MAJOR CHANGES
- 12 projects completed, 1 failed
- Literacy 28.5% -> 29.1%
- Population -3.2% from epidemic
- Recurring net +158k -> +162k/year

NEW PROBLEMS
- Machinists now constrain 3 projects

PERSISTENT CONDITIONS
- Charcoal shortage, year 4 of 5, improving
- Scribes 101% utilized

DETAILS
[expand completions]
[expand failures]
[expand events]
```

## Where it lives

Distributed across:
- `sim/engine/proto/state.py` (state structure and output)
- `sim/engine/proto/dispatch.py` (default summaries)
- `sim/engine/proto/render_screens_*.py` (various screens)
- All related complaint instances (71-86, 87-101) for specific examples

**Confidence:** Design recommendation - this is a class of UX problem, not a single bug. Each instance (UX-008, UX-009, UX-012, etc.) should be addressed individually, but this complaint unifies the observation that interface repetition is a systematic problem worth designing for.
