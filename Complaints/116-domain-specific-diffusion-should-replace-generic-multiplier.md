# Domain-specific diffusion should replace some of the generic technology-count multiplier

**Source:** playtest findings document, LATE-010. **Status:** Architecture/
realism recommendation, the direct companion to `Complaints/104` (ECON-002).

## The player's reasoning

Domain-specific effects already exist for some technologies (agricultural
tech affecting crop/labour productivity, printing affecting literacy,
public health affecting mortality). The recommendation is to let these
carry more of the aggregate economic-growth load, so `economy_index()`
(the flat per-node multiplier measured in `Complaints/104`) can carry less.
Examples the player names: agricultural tech to crop/labour productivity,
transport to freight and market radius, printing to literacy/information
diffusion, public health to mortality, machine tools to manufacturing
precision/productivity, power to usable mechanical/electrical capacity,
finance to capital mobilisation, communication to administrative span of
control.

## How this sits against CLAUDE.md

This is the direct, constructive half of the same §3.1 argument
`Complaints/104` makes about the current mechanism's coarseness: §3.1
forbids standing in a hardcoded outcome for a derivable one, and this is
literally the "derive it instead" side of that coin. It also matches §4's
architecture direction precisely: `ENDOGENOUS_COSTS_AND_DOMAINS.md`'s whole
Part 3 domain table is organised around exactly this principle, letting
Layer 2 (agriculture, demography), Layer 3 (labour, production, price solve)
and Layer 4 (infrastructure/transport, trade) each produce a real,
derived economic effect rather than have one flat index stand in for all of
them.

## What already exists

Several domain-specific links already exist and work, per the playtest: the
Mexica literacy run saw the literacy ceiling respond to agricultural
mechanisation through `agrarian_slack()`, and actual literacy responded to
operating schools and later printing. `sim/engine/labour.py`'s
`wage_cost_factors()` already builds the wage from food/housing/tool-input
scarcity, independent of the price solver, per `docs/architecture/STATE_OF_
THE_PROJECT.md`'s Milestone 5 entry. What does not yet exist: a domain-
specific link from transport technology to freight cost/market radius
distinct from the flat economy index, from machine-tool technology to
manufacturing precision/productivity as a distinct multiplier, from power
technology to usable capacity as a distinct multiplier, or from finance
technology to capital mobilisation (which would need `Complaints/110`'s
capital markets to have somewhere to attach to).

## Size

This is not one task; it is a standing direction that gets applied
incrementally as each domain (agriculture, labour, transport, finance) gets
its own real mechanism wired in, exactly as `ENDOGENOUS_COSTS_AND_DOMAINS.md`
already sequences. Treat this finding as the acceptance criterion for that
migration ("as X gets wired in, `economy_index()`'s weight for the
technologies X already covers should shrink"), not as a single ticket to
close.

## Cross-references

`Complaints/104` (ECON-002) measures the current mechanism this finding
proposes to shrink; read the two together. `docs/architecture/ENDOGENOUS_
COSTS_AND_DOMAINS.md` Part 3 is the domain-ordering plan this finding
endorses rather than duplicates.
