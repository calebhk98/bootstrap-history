# Add a stronger international economy

**Source:** playtest findings document, LATE-007. **Status:** Feature
recommendation, roadmap-sized, partially named in the architecture plan.

## The player's reasoning

The current geography/mineral/freight logic is a strong foundation. Late-
game expansion should add imports and exports, foreign consumer demand,
shipping capacity, ports, tariffs, embargoes/sanctions, exchange or coinage
issues, foreign competitors, technology theft, strategic resources and
colonial/concession politics. This would make geography and the map matter
more as wealth grows, rather than less.

## Checked against the architecture documents

`docs/architecture/ENDOGENOUS_COSTS_AND_DOMAINS.md` Part 3's domain table
lists "Trade: one market becomes many, linked by real freight cost" at
Layer 4. That is domestic multi-market trade (already partly wired:
`sim/engine/economy.py` imports `sim/world/transport.py` for freight cost
between a civilisation's own regions), not specifically a foreign/
international layer with tariffs, embargoes or foreign competitors. Direct
search of `HISTORICAL_SIM_ARCHITECTURE.md` for "tariff", "export", "foreign
trade", "colonial" and "international" returned no matches. So the domestic
half of this finding overlaps with an already-planned Layer 4 domain; the
specifically international/foreign-policy half (tariffs, embargoes, foreign
competitors, technology theft, colonial politics) is not currently named
anywhere in the architecture documents and is a genuine addition.

## What already exists

`sim/engine/economy_freight.py` computes freight cost between a
civilisation's own regions and to trading partners using centroid distances;
`data/world/geography.json`'s `located_materials` and `reach_levels` already
encode which resources are reachable at what trade-route investment level
(the platinum-via-eastern-trade-routes case in `Complaints/TOP_PROBLEMS.md`
item 3 is a live example of this mechanism). There is no foreign-demand
model (a trading partner's own population and income setting how much it
will buy), no tariff or embargo mechanic, and no foreign-competitor actor.

## How this sits against CLAUDE.md

§3.1 and §3.3 apply as everywhere else on this list: a tariff rate or
foreign demand level needs to come from the trading partner's own economic
state (which itself would need at least a stub demand model, connecting
this to `Complaints/106`'s wiring of `sim/world/demand.py`) rather than a
flat "foreign buyers absorb X% of surplus output" assumption.

## Size

Roadmap-sized. The domestic multi-market piece is already sequenced (Layer
4); the foreign-policy piece (tariffs, embargoes, foreign competitors,
colonial politics) is comparable in scope to `LATE-001`'s independent firms,
since a foreign competitor is essentially a firm actor located outside the
player's own civilisation.

## Cross-references

`Complaints/106` (ECON-004) for the demand-model prerequisite a foreign
buyer needs. `Complaints/107` (LATE-001) for the actor-extraction machinery
a foreign competitor firm would reuse. `docs/architecture/ENDOGENOUS_COSTS_
AND_DOMAINS.md` Part 3 for the Layer 4 domestic-trade overlap.
