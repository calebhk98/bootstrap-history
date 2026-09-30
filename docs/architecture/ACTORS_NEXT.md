# Actors, next: the country as a player

Direction for making the government actor a real participant rather than a
scaffold. Current behaviour is in `ACTORS.md`; the tracked problems are
`Complaints/189` (actors run but nothing reads them) and `Complaints/107`.
Stakeholder decision recorded in 189: no quick fix. Do not skip the actor
phase and do not wire a token consumer. Even a single-player game is
multiplayer, because the country (Rome, China, ...) is another player, without
the founder's knowledge of the future and with very different economics.

## What exists now, measured by reading the code

Re-check any line with the command beside it.

**Government** (`actors/government.py`). Each year `advance_actors`
(`engine/society_actors.py`, called from `core_step_phases.py`) creates it if
missing, credits its purse a fixed share of `SimWorld.state_revenue()`
(society output times the civilisation's tax share times state capacity), then
it looks at the founder's demonstrated inventions, ranks them by the
civilisation's trait weights, and starts copies it can afford. Copies cost
wages and money and complete or fail.

**Firm** (`actors/firm.py`). Enters a founder concern that has run at a
profit, copies it, and takes `takings / (1 + rivals)` less upkeep.

**What reads their results.** Nothing outside `actors/` and `tests/`:

    grep -rn "\.actors\b\|of_kind\|active_firms\|\.government(" sim --include=*.py | grep -v "sim/engine/actors/\|sim/tests/"

Specific disconnects, each with the player-visible behaviour it duplicates:

| Actor output | What the engine does instead |
|---|---|
| The state's purse and what it learns | The state's armies carry the founder's military work at a rate from a generic half-life curve (`state_military_diffusion`, `society_diffusion.py`); the government's own copies are ignored. |
| The state's take from the founder | Requisition, pressed office, military supply and confiscation (`_state_pressure`, `society_state_pressure.py`) are shares of the founder's revenue set by civilisation data and a notice score. The founder's capital is reduced and the money vanishes: the government actor never receives it. |
| The state's payments to the founder | Patron funding (`state_funding`, `economy_production.py`) is a labelled heuristic formula; its own `why` says a real answer needs a state budget. |
| A firm's takings | Firms split takings with "rivals", but the founder's concern earns the same as before. Money appears in the firm's purse without leaving anyone's. The goods market (`economy_goods.py`) counts only the founder's own concerns as supply. |
| Actor staff | `workforce` records hours worked, but no labour pool is drawn down, so a firm or state hiring never raises a wage the founder pays. |

The common cause is that actors keep private books. Nothing conserves money
between an actor and the rest of the world, so nothing they do can be seen
from outside, and nothing outside can be attributed to them.

## Principles for the sequence

- The state is an actor like any other. A mechanism that the state uses (taking
  a levy, paying wages, buying goods) is written against an actor and works for
  a firm, a second state or another player. No civilisation or node ids.
- The state observes, it does not know the future. Its valuation already reads
  only what the founder has demonstrated (`SimWorld.founder_inventions`,
  exposure by visibility and distance). Every new state decision reads through
  `SimWorld` and never the founder's private state.
- Money is conserved between actors. Only the edge of the model (wages paid to
  the population, goods bought from it, imports) creates or destroys it, and
  each such edge is named.
- A consumer is built only after its producer has a real budget. A state
  spending rule sitting on an invented purse would be numbers on numbers
  (the same argument `Complaints/109` makes about state finance).
- Heuristics stay labelled (`declare(..., kind="temporary_heuristic")`) and
  each increment says which ones it retires.

## Increments

Each names what it reads, what it changes, the player-visible behaviour it
replaces, and how it is checked. Fingerprint check for all of them:

    python3 sim/perf_fingerprint.py record before.json --quick    (before the change)
    python3 sim/perf_fingerprint.py check before.json --quick     (after; every divergence explained)

Run `--quick` for iteration and the full set before merging.

### 1. Money between actors is conserved and audited

Reads: the founder's household purse, the government record.
Changes: a general `transfer(payer, payee, amount, purpose)` between any two
actors; every recorded actor keeps an income and outlay ledger by purpose, and
its purse equals its opening money plus income minus outlays; the state's
takings from the founder are received by the government actor.
Replaces: the founder's levy vanishing. The founder's own numbers do not
change; the state's do.
Tests: `sim/tests/test_actor_treasury.py`. Fingerprint: expected identical on
every household field, because the founder is charged exactly as before.
Retires: nothing yet. It is the precondition for 2 to 5, because a state
whose purse is not fed by real flows cannot be given real spending.

### 2. Firms and the state are taxed and assessed by the same rule

Reads: an actor's visible wealth and staff (the same `household_scale` idea,
computed for any actor from what an observer can see), the civilisation's
state capacity and tax share.
Changes: the yearly levy is decided by the government actor's policy, looking
at every actor it can see, founder and firms alike. Firm margins pay it into
the treasury.
Replaces: a levy only the founder pays, so the founder is no longer the only
taxpayer and the state's revenue has an endogenous part.
Tests: a firm and the founder with equal visible scale are assessed equally;
a state with no capacity collects nothing from either. Fingerprint: firm
years only.

### 3. The state's know-how is the state's adoption

Reads: the government's knowledge and copies in progress.
Changes: `state_military_diffusion` and the state's other adoption effects read
what the government actor actually holds, not a half-life curve.
Replaces: the generic diffusion curve for the state, and the labelled
heuristics `DIFFUSION_HALF_LIFE_MILITARY_YEARS` and its relief caps for that
use. This is the first place the player's war outcomes depend on the actor.
Depends on 1 and 2: without a real purse the state adopts almost nothing and
war relief collapses (acceptable under the baseline-may-get-worse rule, but
it should be caused by a budget model, not an arbitrary constant).
Tests: fewer funded copies, less relief; the existing craftsmen-wording
checks on state military diffusion are rewritten to the mechanism.

### 4. Firm output reaches the market

Reads: every actor's concerns as supply into a goods category.
Changes: the founder's goods market factor counts firm supply. A firm's takings
come out of the same demand the founder sells into, so takings are no longer
created.
Replaces: `diffusion_share` and the category supply counting only the
founder's concerns (heuristic retired: the leak to unnamed competitors).
Touches economy code; needs the demand wiring in `Complaints/106`.

### 5. The state's demand and labour

Reads: the state's outlays by purpose from 1.
Changes: what the state spends on wages and goods is demand: staff hired by
any actor are drawn from the labour pool (`sim/world/labour_market.py`), and
the state's purchases enter the goods market. Patron funding to the founder
becomes a payment from the treasury to the founder, replacing
`state_funding` and its labelled constants.
Replaces: `state_funding`, the wage the founder pays for trades the state
also hires.

### 6. The state's need drives the levy

Reads: a spending model (standing costs, war, garrison from
`sim/world/military_logistics.py`) against receipts.
Changes: the shortfall between need and revenue is what the state seeks to
raise, from those it can see, instead of a per-civilisation share of revenue.
Replaces: `requisition_base_share`, `office_base_share` and the military demand
shares as civilisation data (`Complaints/109`).

### 7. Other countries and fog

Several governments, each with its own location, purse and view. A foreign
state sees only what reaches it (`Complaints/113`). Interest groups
(`Complaints/114`) are actors that press the state's policy.

## Not decided here

How a state's policy is chosen when a human plays it (the callback policy
exists); credit and bonds for the state (`Complaints/110`).
