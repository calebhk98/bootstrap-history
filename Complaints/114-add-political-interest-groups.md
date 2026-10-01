# Add political interest groups created by industrialisation

**Status:** partly - interest groups are actors (`group.py`): producers whose sales the founder displaces and employers whose hands his hiring bids up organise by what they lost, press the state, and it answers by capacity and purse (budget line raised through the levy, a start-gate prohibition, blame on the founder); landholders, organised workers, firm owners, clergy and the military remain open (430, 431, 432)

**Source:** playtest findings document, LATE-008. **Type:** Feature
recommendation, roadmap-sized, substantially overlapping already-planned
architecture direction.

## The player's reasoning

Generic suspicion, eminence and state notice already provide political
pressure, but late industrialisation should create actors with genuinely
conflicting interests: landowners, merchants, industrialists, organised
workers, military, bureaucracy, clergy, urban poor and academics.
Technological and economic success should change politics, not merely raise
a scalar danger meter.

## Checked against the architecture documents

`docs/architecture/HISTORICAL_SIM_ARCHITECTURE.md` already names this
almost exactly. Direct quotes, confirmed by reading the file: "rulers and
political actors," "political competition," "political coups," and, most
directly on point, "a new technology that makes one group extraordinarily
wealthy or militarily powerful should alter political incentives and
coalitions." That is the player's finding, already written into the
external design document this project treats as direction. `ENDOGENOUS_
COSTS_AND_DOMAINS.md` Part 3 places "Politics and governance: the state as
an organisation with a balance sheet" at Layer 6, alongside "Institutions
and law." So this is not a new idea; it is a playtest-confirmed argument for
work already on the roadmap, sequenced behind economy (Layer 3), trade
(Layer 4) and settlement (Layer 5).

## What already exists

`sim/engine/society_state_pressure.py` implements a single scalar pipeline:
`state_notice()`, gated by `household_scale()` (a weighted mix of headcount,
visible wealth and eminence, each saturating at a fixed threshold), driving
hazards like confiscation. There is no faction or coalition structure; every
political consequence in the live engine is one number crossing one
threshold. This is precisely the "scalar danger meter" the player contrasts
with distinct interest groups with their own goals.

## How this sits against CLAUDE.md

§3.1: a faction's stance (landowners resent mechanisation reducing their
labour rents, workers organise once factory employment reaches some real
density) needs to be derived from the same economic state that would drive
it in reality, not asserted as a scripted reaction to a tech-tree node
completing. §3.3: political actors are agents with their own interests and
should compete for state attention through the same mechanisms other actors
would, once `LATE-001`'s actor extraction exists.

## Size

Roadmap-sized, and this is one of the later-sequenced items even within the
already-late Layer 6 slot, because faction interests only mean something
once there are real economic winners and losers to be a faction of (real
wages, real firm profits, real land rents) - all upstream work.

## Cross-references

`docs/architecture/HISTORICAL_SIM_ARCHITECTURE.md`'s own political-actor
language, quoted above, is the direct overlap; a future agent scoping this
should start from that document's existing entity list rather than
reinventing one. `Complaints/107` (LATE-001) and `Complaints/109` (LATE-003)
share the actor/state-balance-sheet prerequisites.

Also reported (England 1300 fog playtest): by 1350 the household ran medicine, textiles, power and infrastructure, had created new professions, and had measurably cut national plague mortality; by 1375 it employed about two thirds of the reachable chemists, engineers, machinists, glassblowers and opticians, ran a university, and was the dominant local employer. The tester found the social reaction small for that scale and asked for political attention proportional to a dominant founder: crown demands and taxation, patronage offers, monopolies and patents, guild hostility, poaching of staff, espionage, foreign invitations, church scrutiny, and losers from technological change. They singled out the patronage gate on Newtonian mechanics as the best example of this kind of constraint and want more of it as wealth and disruption grow. See also 118. Report: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`.

Also reported (Han China 100 AD fog playtest, tester item(s) 89, 110, 132, 149, 189; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): state requisition (imperial workshops took 39 to 106 million, later sums larger), monopolies, post charges and property seizures (7 to 74 billion) are applied as automatic deductions; the requisition text says refusal is not free and compliance is cheaper but offers no choice, and protection at 92 percent did not stop the seizures. The tester asks for compliance, negotiation, concealment or refusal with uncertain consequences, or an explicit label "compulsory". Reproduces: untested (late game).

Also reported (final playtests, A; `Complaints/reports/final-playtests-triage.md`): the state adopted much of the tester's technical work for military purposes and confiscated wealth; asks for the state's demands to change with industrialisation (military production, infrastructure, communications, medical help) and for an influential inventor to become a political liability. Liked: the existing reputation, resistance and government-attention systems.

## First increment (built)

`groups` lists who is organised, how many people they speak for, what they lost and to what, and what the state does (`sim/PROTOCOL.md`, INTEREST GROUPS). Size and grievance are measured, never scripted: the market's displaced tonnes at the quoted price for producers, the labour pool's premium on the hands the other employers pay for employers; pull is the loss as a share of the state's revenue from the territory the group lives in. The state's answer uses its own capacity (how much of the pull it can act on) and its own budget (a state in deficit compensates and raises the money from the taxpayers it sees, a state not in deficit may also forbid the technique). Code: `sim/engine/actors/group.py`, `world_groups.py`, `group_tuning.py`, `sim/engine/interest_groups.py`; tests `sim/tests/test_interest_groups.py`.
