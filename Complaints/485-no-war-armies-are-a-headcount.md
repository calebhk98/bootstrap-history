# There is no war: armies are a headcount with no units, location, quality or supply line

**Status:** partly - armies, the campaign phase, battle, siege, conquest and the commands exist; the remainder is listed below

## Built

- An army is a located body of soldiers owned by an actor, with equipment, food, animals, pay owed and an order
  (`sim/world/army_record.py`, records in the campaigns module's state, `sim/campaigns/state.py` and `sim/campaigns/armies.py`). It is a slice
  of the soldiers the state keeps (`record.army`); its dead are struck from that force and a state that shrinks
  stands its armies down by the same share.
- The year has a `campaigns` phase (`sim/engine/year_phases.py`, `sim/campaigns/campaign_year.py`). An army marches the
  route graph's fastest route to its target (days by mode), eats from the land it crosses
  (`tile_stock_kg` in `sim/world/campaign_supply.py`, a share of the tile's food potential, drawn down within the year), from a pack-animal
  column bringing grain from the owner's tiles within reach (`carriage_kg_per_day`, the animal's own fodder out and
  back, `military_logistics`), then from its stock. Hunger, the tile's endemic disease (geography's
  `endemic_people_loss`) and desertion when the army line's arrears are owed take men (`sim/world/campaign_attrition.py`).
- Battle (`sim/world/battle.py`): effective strength is numbers times equipment quality (the iron and ammunition a soldier is
  supplied with, so a rifle burden counts for more by the same rule) times supply state times terrain (the tile's
  ruggedness for the defender); a draw from a seeded stream decides the winner by the strength shares; both sides lose
  men, the loser more.
- Siege (`siege_turn` in `sim/world/campaign_contest.py`; the orchestration is `Contest` in `sim/campaigns/contest.py`, which also holds the tile taking, the captive hooks and the conquest contact): shut-in defenders eat the tile's stores and no column reaches them; the
  besieger storms when its chance is good enough, waits while it is not, and withdraws when its own ration fails. The
  defence is the owner's armies on the tile plus its free soldiers shared over its tiles by their people.
- Conquest: a tile whose defenders are gone passes through `transfer_tile` (`sim/land/ownership.py`) at the level `data/world/control_levels.json`
  names (`conquest`), rising with the owner's authority on it (484); foreign countries' profiles follow the
  transfer, and the home budget's territory reads the owner map.
- Commands `army` (raise, march, recall, disband) and `armies` for a country seat (`sim/ui/proto/dispatch_armies.py`,
  `sim/PROTOCOL.md`). A state no seat plays raises and orders armies to threatened tiles and never attacks
  (`sim/agents/army_raising.py`).
- Tests: `sim/tests/test_campaign_rules.py` (rules on built inputs), `sim/tests/test_campaigns_year_smoke.py` (a two-country
  game) and `test_campaigns_module.py`. Sources opened: Engels, Alexander the Great and the Logistics of the Macedonian Army (ch. 1 and Appendix 1:
  ration, pack load, how far animals can carry food; the epub text has no page numbers); Roth, The Logistics of the Roman
  Army at War (ch. 1 p. 66, ch. 4 p. 222: grain ration, mule fodder and load). Haldon was not opened. Every other figure
  is a labelled heuristic with a `retire` (`campaign_*.py`, `battle.py`; `--compare` counts them).

## What is left

- No AI conquest policy: a state nobody plays only defends. Nothing yet weighs a frontier tile's value against the cost
  of holding it, so nothing makes expansion stop at barriers or low-value land.
- No declaration of war, alliance or peace: an army ending on another actor's tile is an attack on it, whoever owns it.
- No fleets, blockade or naval action (the navy is still a wage line, see 492), so no sea battle and no landing.
- No unit types: quality is equipment and readiness (`sim/world/army_readiness.py`: an army that does not fight loses drill and morale toward a
  floor, a year of battle restores it; the free soldiers that garrison tiles carry no readiness). Training as labour and unit kinds are not modelled.
- Fortification is read as nothing (`tile_fortification`); works that defend (walls, forts) should add to it.
- Taking food from a tile does not yet lower the food its people eat or the next harvest; a retreating attacker is ordered home and marches there from the next
  campaign (a routed defender still falls back at once); armies owned by a seat's colonies (a tile owner that is a seat
  id, not a country) have no state to raise soldiers.
- Rome's third-century crisis hazard still lists the neighbouring army under `causes_not_modelled`
  (`data/civilizations/rome_100ad.json`) until a state plays that neighbour.
- Disease and food figures are read through geography; the camp's multiplier on endemic disease and the seizable share
  of a tile's food are heuristics waiting for the disease model's contagion and a tile granary stock.
