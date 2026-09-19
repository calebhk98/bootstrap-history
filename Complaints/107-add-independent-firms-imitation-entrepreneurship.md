# Add independent firms, imitation and entrepreneurship

**Source:** playtest findings document, LATE-001. **Status:** Major
roadmap-sized feature recommendation, not a fix.

## The player's reasoning

The founder stays disproportionately central through an entire run: founder
finances every project, opens every concern, hires all the labour, and
captures nearly all of the industrial surplus. The player's proposed loop:
the founder demonstrates a profitable technology, it diffuses (workers leave,
competitors copy), independent firms form, those firms hire labour and buy
materials, wages and input prices rise, national output and consumer income
rise, the founder's own monopoly margins fall while the total market
available to the founder can still grow. They list player-facing choices
that would follow from this (keep proprietary, license, publish, sell
patents, encourage state adoption, spin off firms, form joint-stock
companies), each trading monopoly profit for diffusion speed, political
influence, resilience and national growth.

## How this sits against CLAUDE.md

§3.3 (interventions propagate through normal rules) is the frame this
belongs in: a competitor firm has to be a real agent with its own capital,
labour demand and production, not a scripted rival with a hand-set output
number. §3.1 is satisfied by construction if built this way: a competitor's
existence and output would need to come from the same cost/labour/material
rules the founder's own ventures already use, not from a bespoke "rival
firm produces X" branch.

CLAUDE.md §4's closing instruction is directly on point: "make the founder's
mechanisms general enough that other actors can use them, rather than making
the founder less detailed." An independent firm is exactly a second actor
reusing the founder's own venture/production machinery. That reuse is why
`docs/architecture/HOUSEHOLD_EXTRACTION.md` exists in the first place: its
own opening line states plainly that today "there can be no government
actor, no firm, no rival, and no second player" because the founder's
attributes live directly on `Sim` rather than on an extractable actor
object, and that document explicitly plans a `Household`/`Firm` split for
exactly this reason (confirmed reading the file: "and `Firm` under it.
Resist it until there is a second actor to look at.").

## What already exists

- `docs/architecture/HOUSEHOLD_EXTRACTION.md` is Milestone 3 of
  `ENDOGENOUS_COSTS_AND_DOMAINS.md`, and `docs/architecture/STATE_OF_THE_
  PROJECT.md`'s own table marks Milestone 3 **done** ("`sim/engine/actors/
  household.py` (294 lines)"). That is the prerequisite this feature needs,
  already built, not merely planned.
- `docs/architecture/HISTORICAL_SIM_ARCHITECTURE.md` (the external design
  document, saved verbatim) already names firms, firm/organisation budgets
  and entrepreneurship among its target-model entities, and `ENDOGENOUS_
  COSTS_AND_DOMAINS.md` Part 3's domain table places "Economy: labour
  market, production, capital" at Layer 3 of the dependency-ordered build.
  This finding does not introduce a new idea to the project; it corroborates
  one already on the architecture roadmap with playtest evidence for why it
  matters (a founder who personally owns the whole industrial revolution).
- No live code implements a second economic actor today. `sim/world/labour_
  market.py` and `sim/world/demand.py` (see `Complaints/106`, `Complaints/
  119`) are prerequisites in the sense that a competing firm needs a real
  labour market and a real demand system to bid against, and neither is
  wired into the engine yet.

## Size

This is the single largest system on this list. It needs, at minimum: an
extracted `Firm` actor type built on the same base `HOUSEHOLD_EXTRACTION.md`
designed for the founder, a diffusion/imitation trigger tied to how long a
technology has been running and how visible it is, firm-side capital and
hiring that competes with the founder in the same labour and material
markets, and new player-facing choices (license, publish, patent, spin off)
with their own consequences. This is a multi-month roadmap item, sequenced
behind the labour market and demand wiring (`Complaints/106`), not a task to
pick up expecting a contained fix.

## Cross-references

`Complaints/106` (ECON-004) and `Complaints/119` (ARCH-001) both note that
`labour_market.py` and `demand.py` are unwired prerequisites for this.
`Complaints/105` (ECON-003, extreme wealth is not inherently a bug) should
be read alongside this: independent firms are the mechanism that is
supposed to erode founder margin over time, not a revenue nerf.
