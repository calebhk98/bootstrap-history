# Add independent firms, imitation and entrepreneurship

**Status:** partly - actor model, government imitation, firm entry (market-bounded: an entrant expects its share after the entrants' own supply reaches the market and must beat the market rate; Complaint 330, 331), shared labour pool and shared goods market built; the per-invention choice (keep secret, license, publish; the `disclose` command) built; selling patents, joint-stock companies and spin-off firms remain

**Source:** playtest findings document, LATE-001. **Type:** Major
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
  market.py` and `sim/world/demand.py` (see `Complaints/102`, `Complaints/
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
behind the labour market and demand wiring (`Complaints/102`), not a task to
pick up expecting a contained fix.

## Cross-references

`Complaints/102` (ECON-004) and `Complaints/115` (ARCH-001) both note that
`labour_market.py` and `demand.py` are unwired prerequisites for this.
`docs/architecture/DESIGN_PRINCIPLES.md` (ECON-003, extreme wealth is not inherently a bug) should
be read alongside this: independent firms are the mechanism that is
supposed to erode founder margin over time, not a revenue nerf.

## Progress

Built: the `Actor` base with a policy interface, `Household`, `Government` and
`Firm` actors, value-derived imitation of the founder's inventions, and firm
entry into proven concerns. See `docs/architecture/ACTORS.md`.

Remaining: firms hiring from and competing in the shared labour and material
markets (their staff do not yet draw on the society's labour pool), erosion of
the founder's own margin from competitors, the player's choices (license,
publish, patent, keep secret, spin off), joint-stock companies, other
countries as full players with their own locations and policies, fog of war
for actor observation, and workers leaving the founder to found firms.

Update: actors now keep a ledger (`docs/architecture/ACTORS_NEXT.md`, increment 1), so a firm's takings, upkeep, copying and founding capital are booked by purpose and its purse always equals its ledger. Firm takings are still not taken from the founder's market and firm staff are still not drawn from the labour pool (increments 4 and 5).

Also reported (final playtests, A and B; `Complaints/reports/final-playtests-triage.md`): A: independent competitors adopting technologies and affecting prices, industrial growth undermining older businesses, 'independent domestic adoption' of what the founder demonstrates. B: at 302 AD the whole empire had about 18 engineers, chemists, machinists and electricians each, 10 of them on the player's payroll, while the player ran a power grid: 'the revolution stays inside one household'; asks for copycat firms and native trade counts that grow with what you run. Both liked the trades-becoming-native milestone text that already exists.

Update: firms now compete for the founder's labour pool and sell into the founder's goods market (`docs/architecture/ACTORS_NEXT.md`, increments 2 and 4; `sim/tests/test_actor_firms_compete.py`). A firm's staff are the people its concerns need by the founder's own rule (`venture_hands`, `venture_foreman`) plus its copying crews. They are counted in `Sim.actor_staff_fte(trade)`, which `market_supply` and `hire_check` subtract from what the founder can reach, and new hires press the one local market (`_add_labour_pressure`), so the founder's `labour_price_factor` and the actors' own `hiring_wage_per_hour` respond. A firm that cannot find its staff in the pool earns in proportion. Concerns that actors run count as sellers in a goods category (`actor_concerns_in`), so the founder's share falls and a firm's takings are the same shared demand; `Sim.actor_supply(material)` sums the tonnes a year all actors put on the market for the market code to read.

Remains: the player's choices (license, publish, patent, keep secret, spin off) need a command and a royalty flow; staff in trades nobody here practises yet (taught-only trades) are not drawn from a pool; firm entry still values a concern by the founder's gross split by operators rather than the shared market; materials made by a concern with no declared `annual_output_t` have no physical supply; joint-stock companies, fog of war, workers leaving to found firms, other countries.
