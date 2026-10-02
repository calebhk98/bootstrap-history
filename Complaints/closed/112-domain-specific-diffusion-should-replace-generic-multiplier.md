# Domain-specific diffusion should replace some of the generic technology-count multiplier

**Status:** closed - the index is gone: `Sim.economy`, `economy_index()`, `ECONOMY_INDEX_PER_*_NODE`, `ECONOMY_OUTPUT_SCALING_EXPONENT` and `output_volume_scale()` are deleted; output is the quantity the market clears at the opening's prices (`sim/engine/real_output.py`, pinned by sim/tests/test_real_output.py). What remains is Complaints 369 and 370.

**Source:** playtest findings document, LATE-010. **Type:** Architecture/
realism recommendation, the direct companion to `Complaints/101` (ECON-002).

## The player's reasoning

Domain-specific effects already exist for some technologies (agricultural
tech affecting crop/labour productivity, printing affecting literacy,
public health affecting mortality). The recommendation is to let these
carry more of the aggregate economic-growth load, so `economy_index()`
(the flat per-node multiplier measured in `Complaints/101`) can carry less.
Examples the player names: agricultural tech to crop/labour productivity,
transport to freight and market radius, printing to literacy/information
diffusion, public health to mortality, machine tools to manufacturing
precision/productivity, power to usable mechanical/electrical capacity,
finance to capital mobilisation, communication to administrative span of
control.

## How this sits against CLAUDE.md

This is the direct, constructive half of the same §3.1 argument
`Complaints/101` makes about the current mechanism's coarseness: §3.1
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
technology to capital mobilisation (which would need `Complaints/106`'s
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

`Complaints/101` (ECON-002) measures the current mechanism this finding
proposes to shrink; read the two together. `docs/architecture/ENDOGENOUS_
COSTS_AND_DOMAINS.md` Part 3 is the domain-ordering plan this finding
endorses rather than duplicates.

Also reported (England 1300 fog playtest): the tester asked for a clearer distinction between personal discovery, local adoption and civilisation-wide diffusion, and for causal attribution of national diffusion ("if personal technologies are spreading into national public health or productivity, show which discoveries and institutions contribute and by roughly how much"). The Black Death event credited "the country's own public health" for softening the national loss without saying whether the player's work was part of it (see 198). They also want diffusion mechanics such as apprenticeships, textbooks, professional communities, regional diffusion and decay after practitioner loss. Report: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`.

Also reported (Han China 100 AD fog playtest, tester item(s) 124, 151, 178, 193; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): after 300 years the national population estimate was 600 million while the operated town stayed at 50 thousand, specialist trades were estimated at three nationwide, and completion messages (see 238) gave no coverage. They ask for adoption by region and installed units (clinics, tractors, refrigerators, schools) rather than one national multiplier. The military case works and was praised: an attack was repelled citing walls, guns and 73 to 95 percent diffusion to state armies. Reproduces: yes for the placeholder specialist counts (`population` at the start prints `chemist 0`, `engraver 5,800` with 2.9 in reach).

Also reported (final playtests, A; `Complaints/reports/final-playtests-triage.md`): asks for a public-adoption dashboard (how many cities have electrical power, how widespread mechanised workshops are, how many children attend school, how much independent manufacturing exists outside the player's holdings) so a technologically advanced private organisation can be told apart from an industrialised civilisation; B's version is the engineers-per-trade count above.
