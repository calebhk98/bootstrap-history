# The state's guards, mine inspectors and foresters are sized by labelled per-head heuristics, and the ceilings keep a scale

**Status:** partly - guards, mine inspectors and foresters are budget lines the state hires and pays; their per-head sizing and the ceiling scales remain heuristics

**Done.** The state's budget keeps a `guards`, an `inspectors` and a `foresters` line (`sim/agents/order.py`), staff hired in the
labour market and paid like the administration line. What they reach follows the 620 time rule over the road from the
seat (`CollectionView.order_share`, `inspection_share` in `sim/agents/collection_world.py`; `Sim.order_reach()` and
`Sim.inspection_reach()` in `sim/engine/legitimacy.py`). Theft and plunder order (`theft_charge.py`) read the guards
employed, and the mine land ceiling (`mine_land_ceiling`) reads the inspectors employed. The forest ceiling (`forest_land_ceiling`) reads the foresters employed (`CollectionView.forest_share`,
`Sim.forest_reach()`). Country states keep the same
lines. Tests: `sim/tests/test_state_guards_and_inspectors.py`.

**Still open.**

- The forest ceiling carries the labelled `FOREST_HA_PER_MILLION_KM2_PER_SC` scale per unit of forest reach; it should
  follow the woodland a forester can keep under tenure.
- How many guards and inspectors a state keeps is a labelled per-head time (`PATROL_DAYS_PER_PERSON`,
  `INSPECTION_DAYS_PER_PERSON`, `FORESTER_DAYS_PER_PERSON` in `sim/agents/tuning_order.py`, no source found); guards should follow the crimes a
  district has, inspectors the claims on the registry and foresters the woodland held.
- The mine ceiling still carries the tonnes-per-reach scale (`MINE_CEILING_*_SCALE_*`) per unit of inspection reach;
  the ceiling should follow tonnes an inspector can keep registered.
- Guards and foresters are booked in the unskilled trade and inspectors in the scribe trade; a watchman trade in
  `data/world/trades.json` would let the labour market price them apart.

**Research done** (`Complaints/reports/research-state-staffing.md`): the capital's standing watch (vigiles plus urban cohorts) gives an
upper bound on guard density, tested in `sim/tests/test_order_staffing_sourced.py`. No source was found for a state-wide guard
ratio, inspectors per tonne or claim, or foresters per hectare, so those stay labelled heuristics (the `MINE_CEILING_*` scales
gained `retire`).

**Research needed.** How pre-modern states kept order and enforced ceilings, from what the staff did rather than a ratio:
(a) the district watch or patrol cost per head of population for a province (Roman provincial police: the stationarii and
beneficiarii, Egyptian nome police; medieval England's hundred and shire constables), to size guards from the crimes a
district has; (b) how many claims or tonnes a mining procurator's staff registered (Vipasca regulations, Spanish mining
districts); (c) woodland a forester or warden held (medieval forest eyres and the royal forests' verderers). Each answer
cites the page opened.
