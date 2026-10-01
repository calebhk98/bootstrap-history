# Add a generic "why did this number change?" inspector

**Status:** partly - `figures` / `why <figure>` (sim/engine/figures.py, figures_headline.py) show last year, this year and named causes for cash, income, upkeep, recurring net, population, literacy, price index and one hazard, and the cash figure's causes come from the cash book (292, closed); still open: causes for wages, state notice, epidemic severity, project throughput and venture shutdowns

Many important numbers change significantly each turn. A player trying to understand the civilization's trajectory needs to see what caused each major change.

## Useful for

- literacy
- population
- wages
- recurring income
- state notice / eminence
- epidemic severity
- project throughput
- material price

## What would resolve it

Provide a command or inline explanation showing the delta components:

```text
why recurring_net
Recurring net rose 14,200 this year:
  +8,100 newly ramped ventures
  +4,700 economy / productivity change
  +2,300 cheaper inputs
  -900 higher wages
  net change: +14,200
```

Or inline when state shows a major change:

```text
Recurring net: 45,600/year (+14,200 this year)
  newly ramped ventures: +8,100
  economy change: +4,700
  input prices: +2,300
  wage pressure: -900
```

## Why it matters

The game's central design is that systems feed back into each other. A player trying to understand civilization dynamics needs to see these connections. Currently they are hidden in code.

## Where it lives

Likely a new command or enhancement in `sim/engine/proto/dispatch.py` and `sim/engine/proto/state.py` where change accounting could be added.

**Confidence:** Design recommendation

Also reported (England 1300 fog playtest): the tester asked repeatedly for a "what changed this year and why" causal summary covering why a hazard was softened, why wages changed (after the famine they stayed about 9 percent high, with the cause spread over several screens), and what caused a venture to shut, plus a built-in yearly retrospective. They noted `recap` (a five-year summary of completions, new branches and events) is useful but does not attribute causes. Related: 177 (closed), 198, 207. Report: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`.

Also reported (Han China 100 AD fog playtest, tester item(s) 17, 26, 30, 43, 136, 209; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): the tester could not reconcile cash in a year: pre-step cash, plus recurring net, minus project payments did not equal the arrival cash after a hire (+643,878 against `changes`' +267,937), a departure (exactly the annual wage), a failure (larger than quoted, see 214), a reopening (other revenue moving by millions) or a sacking. They ask for a per-year cash-flow ledger: opening cash, each immediate command payment, receipts, upkeep, wages and advances, interest, refunds, hazards, closing cash, and a "this action changed other operations by X because Y" line on `open` and `mothball`. Reproduces: yes for the missing ledger; the individual deltas need a played game.
