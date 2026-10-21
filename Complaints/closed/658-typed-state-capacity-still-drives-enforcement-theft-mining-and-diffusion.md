# Typed `state_capacity` still drives enforcement, theft, mining ceilings and diffusion

**Status:** closed

620 replaced typed `state_capacity` for tax collection with a share that follows the officials a state pays and the
travel time from its seat. The same typed number is still read by other systems as if it were a measured fact:
theft exposure and charges, mining and forest ceilings, state demand answers, technique diffusion and adoption,
the economy's tax forms and tax farming, state pressure, and the cause book. List the readers:

    grep -rn "state_capacity" sim --include=*.py | grep -v tests

Why it matters (CLAUDE.md 4.1): a state's reach over theft, mines and the spread of techniques should follow from
what it employs and how far its tiles are, as collection now does; one typed figure makes all of them inputs.

What it would take: for each reader, use the collectible-share machinery of 620 (`sim/agents/collection.py`) or the
specific staff that system needs (guards, mine inspectors), or say why the reader is a true initial condition.
Tests: each reader, given a built state with more officials or a nearer tile, moves the way the rule says.

## Outcome

Typed `state_capacity` is gone from the civilisation records (and the `_civ_live` save field, the `state_capacity` tech
effects, the profile field and the fallback constants). `Sim.state_reach()` (`sim/engine/legitimacy.py`) is the 620
collectible share of the home state, kept while the year, works held, people and unpaid officials are unchanged;
`state_authority()` is that reach worn by consent. The agents' view (`BudgetView.state_reach`) reads authority; a
country's view (`CountryWorld.state_reach`) reads its own `collectible_share()`. Remaining readers, each decided:

- (a) the state's reach, same thing as collection: patent enforcement (`enforcement.py`), credit standing,
  requisition and concealment answers (`government.py`, `state_demand.py`, `demand_year.py`, `demand_commands.py`),
  interest-group response (`group.py`), notice and levy shares (`country_state.py`, `society_state_pressure.py`),
  medical compliance (`diffusion_rules.py`), patron funding ask (`economy_production.py`), cause book, the figures,
  the economy's tax forms (`economy_port_year.run_year` sets `setup.state_capacity` from the reach each year;
  `sim/economy` is untouched, its parameter is the share handed in), and a partner's smuggling catch chance
  (`partner_state_reach`, from the partner country's own officials and roads).
- (b) needs staff the state does not employ: theft order, the mine ceiling and the forest ceiling. No guard or
  inspector line exists, so they read the collection share; the missing lines are filed as Complaint 660.
- (c) no reader is a true initial condition. The economy setup starts its share at 1.0 for the opening spin-up, which
  has no officials yet; the first year sets it.
- Tech effects that raised typed capacity are dropped; techniques now move the reach through literacy, pay and roads.
- Tests: `sim/tests/test_state_reach_readers.py` calls each reader with the administration paid and unpaid; the
  other tests build their states with a `state_reach` stub.
- Slow topics that may move: any whole-game run (reach is below one for Norse, England and Mexica where officials go
  unpaid or roads are long): the spin-up of the economy (new cache key), fingerprints, openings, `opening-checks`,
  Norse state-notice and requisition trajectories, mining and forest ceilings, plague mitigation, tax-farming runs.
