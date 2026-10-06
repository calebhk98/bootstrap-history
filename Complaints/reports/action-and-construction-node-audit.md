# Audit: action and construction nodes in the tech tree

Audit for `Complaints/133-some-technologies-are-actions-not-research.md`.
Measured on 2026-10-06 on branch `structural-dedupe-and-owner-decisions`
(written on `action-and-construction-node-audit`). No code or data was
changed.

## Summary

The tree already has most of the vocabulary for built works and actions. A
node with running cost or revenue (`up_hours`, `rev_hours`) is a venture: it
can be opened and closed, and `running` tells a built-and-open work from a
merely completed one (`is_venture` and `running` in
`sim/engine/projects_capability.py`). A node's `grants` adds living stock when
it completes (`sim/engine/projects_completion.py`), and a dependent's `holds`
gates on that stock (`sim/engine/living_stock.py`). The benefactions branch
(`data/branches/56_benefactions.json`, described in
`data/branches/MECHANICS.md`) is the finished pattern for a built work:
derived upkeep, scalable units, effects that stop when the doors close.

The gap is on the dependent side. `pre` is checked against the set of
completed nodes only (`_check_missing_prereqs` in
`sim/engine/projects_starting.py`), so a node that needs a railway, a grid or a
telegraph network to exist and run is satisfied by having once finished the
project, even after the concern is closed. The only place a dependent can ask
for a work to be running is a `hazard_counters` entry's `requires_running`
(`sim/engine/society_hazards.py`). So the founder "knows" the grid into
existence, which is the complaint.

Further gaps are listed under Engine work: a built work has no place and no
size, an action result is declarable only as living stock, a completed node
cannot lapse unless it is a venture, and a number of constructions have no
upkeep so are not ventures at all.

## Method

1. Load every node in `data/branches/[0-9]*.json` (the files the tree is built
   from; `_MERGED_DUPLICATE_IDS.json` and `_META.json` are not nodes).
2. Keyword scan: id prefix `exp_` or `ben_`, or a whole word in the name or id
   from this list: expedition, voyage, survey, colony, grid, network, line,
   system, works, harbour, port, canal, railway, road, aqueduct, telegraph,
   census, map (plurals included). It is deliberately wide; most hits are
   knowledge ("line" matches Fraunhofer lines and log lines).
3. Infrastructure scan, for what the words miss: every node of `kind`
   INFRASTRUCTURE that the keyword scan did not match. The notes of all other
   nodes were also searched for expedition, voyage, colony, survey, grid,
   network, station and tower. Those note-only hits (potatoes, rubber, towers
   on mills, "grid" as a vacuum-tube electrode) are knowledge, or dependents of
   an action, and the ones that matter appear below as dependents.
4. Judge each candidate from its name, note, `kind`, `pre`, whether it carries
   running cost, and who depends on it. Classes:
   * knowledge: a technique, device design, measurement or science; completes
     once and is then known.
   * construction: a built work with a location, a capacity and upkeep that can
     be lost (grid, railway, network, harbour, water works).
   * action: an event with risk and a result (expedition, voyage, survey,
     securing a deposit).
   * institution: a going concern run by people (a bank, a school, a census
     office, a company). Already a venture; listed because the keyword scan
     catches it, and outside this complaint.
5. Dependents are the nodes naming the id in `pre` or in any `req_any` option.
   Many dependents are lineage (a technique descending from another) and
   rightly keep a `pre`; the section on what dependents should require names
   the ones that use the work itself.

The class column is a judgement from names and notes. The construction and
action rows were each read; the knowledge rows were judged quickly and may
hide a few more constructions.

### Script

Save as `candidates.py` outside `sim/` (CLAUDE.md section 5 forbids loose
scripts in `sim/`) and run from the repository root with `python3 candidates.py`.
It prints, tab-separated, one row per candidate: file, id, cat, kind,
dependents, whether the node has running cost or revenue, whether it has
`grants`, and why it matched. The class, mechanism and missing-piece columns
below are judgement and are not computed. The infrastructure scan is the same
loop filtered on `kind == "INFRASTRUCTURE"`.

```python
"""List tech-tree nodes that may be actions or constructions, not knowledge.

Run from the repository root:  python3 candidates.py
Prints one tab-separated row per candidate: file, id, cat, kind, number of
dependents, has running cost or revenue, has grants, why it matched.
"""
import glob
import json
import os
import re
import sys

ID_PREFIXES = ("exp_", "ben_")
KEYWORDS = ("expedition", "voyage", "survey", "colony", "colonisation", "grid",
            "network", "line", "system", "works", "harbour", "harbor", "port",
            "canal", "railway", "road", "aqueduct", "telegraph", "census", "map")

nodes = {}
for path in sorted(glob.glob("data/branches/[0-9]*.json")):
    for node in json.load(open(path)):
        node["_file"] = os.path.basename(path)
        nodes[node["id"]] = node

dependents = {node_id: set() for node_id in nodes}
for node in nodes.values():
    referenced = list(node.get("pre") or [])
    for group in node.get("req_any") or []:
        referenced += list((group.get("options") or {}).keys())
    for referenced_id in referenced:
        if referenced_id in dependents:
            dependents[referenced_id].add(node["id"])


def matches(node):
    reasons = []
    if node["id"].startswith(ID_PREFIXES):
        reasons.append("prefix")
    words = set(re.findall(r"[a-z]+", (node["name"] + " " + node["id"].replace("_", " ")).lower()))
    reasons += ["word:" + keyword for keyword in KEYWORDS
                if keyword in words or keyword + "s" in words]
    return reasons


rows = []
for node in nodes.values():
    reasons = matches(node)
    if reasons:
        rows.append((node["_file"], node["id"], node.get("cat"), node.get("kind"),
                     len(dependents[node["id"]]),
                     bool(node.get("rev_hours") or node.get("up_hours")),
                     "grants" in node, ",".join(reasons)))
for row in sorted(rows):
    print("\t".join(str(cell) for cell in row))
print("candidates:", len(rows), "of", len(nodes), "nodes", file=sys.stderr)
```

Measured on 2026-10-06 with `python3 candidates.py`. Counts by class, from the
tables below on the same date:

| Class | Keyword scan | Infrastructure scan | Both |
|---|---|---|---|
| knowledge | 96 | 52 | 148 |
| construction | 35 | 17 | 52 |
| action | 13 | 0 | 13 |
| institution | 22 | 1 | 23 |

## What already exists

* Venture machinery: `is_venture` is true for a node with upkeep or revenue
  (`sim/engine/projects_capability.py`); `open_venture` and `close_venture` are
  in `sim/engine/projects_ventures.py`; automatic closing and reopening are in
  `sim/engine/projects_staffing.py`. `running` is true for knowledge and for an
  open concern, and false for a completed concern that has been closed. The
  blocker kind `closed` ("built once but shut") is in `sim/engine/blockers.py`.
* Running-gated effects: a mechanic acts only while its node is running unless
  it says `gate: "has"` (`data/branches/MECHANICS.md`). So `reach`,
  `staff_capacity`, `hazard_counters` and the rest on a built work already stop
  when it closes. The power ladder (`electricity_gate`,
  `sim/engine/economy_electricity.py`) already makes every node downstream of
  `power_grid` or `cap_power_grid` draw generated electricity when operated.
* `grants` and `holds` for living stock (`sim/engine/projects_completion.py`,
  `sim/engine/living_stock.py`, rows in `data/world/living_stock.json`). Nodes
  carrying `grants` today: the draught-animal voyage, dairy cattle selection,
  pepper, sugar, tea, coffee, and the cashmere, jute, angora, hop and pyrethrum
  stock nodes. Complaint 133's progress paragraph lists tea, coffee and pepper
  as able to use `grants`; they already do.
* `hazard_counters` with `requires_running` (`sim/engine/society_hazards.py`;
  one use, in `data/branches/49_military.json`).
* `precaution` and the failure roll for actions
  (`sim/engine/projects_precaution.py`, `_complete` in
  `sim/engine/projects_completion.py`). A failure resets part of the work done
  and part of the cost; it does not lose a crew or a ship. `apply_staff_survival`
  in `sim/engine/society_hazards.py` is the existing way to lose people.
* `supplies_material_by_sea_route` (`sim/engine/economy_materials.py`): a node
  that brings named materials by an existing route.
* A civilisation's `needs_first` gate and the `unheld_reason` validation
  (`sim/engine/validate_unheld_gates.py`) for a holding a scenario does not
  start with.
* Geography: route modes take `needs_improvement` per edge, and
  `sim/geography/queries.py` accepts an `improvements` map of built roads and
  rails per edge (`data/world/geography/route_modes/modes.json`). No engine
  caller fills that map from the nodes a player has built, and a mode's
  `requires_nodes` is checked against held (completed) nodes.
* Benefactions as the model of a finished built work
  (`data/branches/56_benefactions.json`).

### Codes used in the tables

Mechanism (what already fits):

* V: venture (upkeep or revenue, open and close, `running`)
* B: benefaction pattern (derived upkeep, `capability.scalable` units)
* G: `grants` and `holds` (living stock)
* H: `hazard_counters` and `requires_running`
* P: `precaution` and the failure roll
* R: `supplies_material_by_sea_route`
* E: `electricity_gate` and the power ladder
* N: civilisation `needs_first` gate (a scenario start condition)
* "none" means the node has no running cost, so it is not a venture at all.

Missing piece:

* M1: dependents check `done`, not `running`; no running requirement on `pre`.
* M2: no place and no size; the work is one household-wide boolean, sized only
  where `capability.scalable` applies, and not tied to a tile, an edge or a
  route.
* M3: nothing lapses a completed work except closing a venture; neglect, war or
  unpaid upkeep do not remove the network from its dependents.
* M4: an action's result cannot be declared except as living stock (a route
  opened, a place known, access to a deposit, a post held are not results).
* M5: construction with no upkeep, so it cannot be opened, closed or lost; the
  data fix is derived upkeep as in the benefactions.
* M6: the same thing exists under more than one id (the dedupe work's concern;
  listed so a fix is not made twice).

## Findings

### What dependents should require

For each construction or action node with users that need the thing itself
(not lineage). Counts are in the tables.

| Node | Dependents that should require it | Should require |
|---|---|---|
| `power_grid`, `cap_power_grid` | arc furnace and electrolysis nodes, `hom_electric_lighting`, `civ_street_lighting`, the `el2_` distribution, tram and trolleybus nodes, `tl_electric_tram`, hydro and pumped storage, `mat_aluminium`, `mat_magnesium`, `cap_heat_3000` | a grid that is running (open, staffed, upkeep paid). The power ladder already makes their operation draw electricity; the start gate does not ask. |
| `telegraph_electric` | `fin_telegraph_business`, `com_stock_ticker`, `com_teleprinter`, `mil_chain_home`, `mil_field_telephone`, `el2_load_dispatch_and_scheduling`, `lnd_block_system`, the cable nodes | the network running. The Morse, relay, battery and sounder nodes are devices and keep `pre`. |
| `semaphore_telegraph` | `patron_imperial` | the chain built and a message carried; it has no upkeep, so it cannot be held or lost. |
| `railway` | `fin_railway_company`, `fud_cold_chain_refrigerated_shipping`, `mil_railway_mobilisation`, `tl_level_crossing`, `tl_horse_tram` | the railway running; `met_rail_mill` is the rail rolling technique and keeps `pre`. |
| `civ_aqueduct_roman`, `cn_aqueduct` | `civ_water_treatment`, `md2_sand_filtration`, `ben_civic_water_works`, `civ_pumping_station` | a water supply running; the rest are lineage. |
| `civ_harbour_dock`, `sea_harbours_pozzolana` | `ben_harbour_and_lighthouse`, `sea_buoy` | a harbour that exists and is kept up. |
| `civ_sewer_roman`, `cn_sewer_system` | `civ_sewer_separate`, `md2_sewage_separation`, `ben_civic_water_works` | a sewer system running; the separate-sewer standard is partly lineage. |
| `lnd_paved_road_network` | `lnd_cursus_publicus`, `lnd_macadam` | the road network. Its `pre` is empty, so it is free knowledge for every start and is not gated on a state able to maintain it. |
| `exp_atlantic_crossing` | `ag2_potato_newworld`, `ag2_maize_newworld`, `exp_americas_factory` | the crossing having succeeded. The node has no running cost, so no vessel or crew is held. |
| `exp_americas_factory` | `fud_potato`, `fud_maize`, `fud_cacao`, `fud_chinampa`, `mat_newworld_crops`, `mat_quinine`, `mat_chile_nitrate`, `med_coca_alkaloid`, `tex_backstrap_loom` | the post established and having returned seed stock or access. It is a venture, so a post can be closed, but dependents ask only for `done`. Crops want `holds` on seed stock; quinine and nitrate want a held post or route. |
| `exp_coastal_africa` | `mat_natural_rubber`, `exp_colony_administration`, `exp_africa_circumnavigation` | the voyage having succeeded; rubber is then a supply route, not a technique. |
| `exp_trade_route_extend` | `nitre_beds`, `mat_gutta_percha`, `mat_cryolite`, `mat_platinum_bulk`, the sugar and coffee voyages | the route open. It already carries `supplies_material_by_sea_route`. |
| `ag2_guano_deposit_access` | `ag2_guano` | access to the deposit, held. |
| `exp_transplant_botany` | none | the node is generic, so its result cannot be named; the per-crop voyages already carry the stock. |

### Data fixes available now (existing mechanisms, no engine change)

1. Crops from the Americas as held stock. Add rows for the seed stock to
   `data/world/living_stock.json`, give `exp_americas_factory` a `grants`
   (the pattern of `exp_import_draught_animals`), and give `fud_potato`,
   `fud_maize` and `fud_cacao` a `holds` beside or in place of the `pre` on the
   post. Run `python3 sim/simulator.py validate`. This is the pattern in
   `Complaints/closed/365-living-stock-is-modelled-as-research.md`.
2. Give each construction that has no upkeep a derived upkeep, with an
   `_internal` working like the benefactions, so it becomes a venture that can
   be opened, closed and lost: `semaphore_telegraph`, `sea_harbours_pozzolana`,
   `med_aqueducts_latrines`, `com_trunk_lines`, `mil_chain_home`,
   `civ_street_lighting`, `hom_public_bath`, `md2_sand_filtration`,
   `md2_sewage_separation`, `md2_activated_sludge`, `md2_isolation_hospital`,
   `hom_sewer_stormwater_separation`. Caution: upkeep was deliberately stripped
   from technique nodes, and giving a node upkeep changes its bill and whether
   it counts as a venture; record `python3 -m sim.tests.fingerprint` before and
   after, and expect behaviour to change.
3. A `hazard_counters` entry on a construction can name the works it rests on
   with `requires_running` (the powder works under guns on the walls is the one
   existing use). The water, sewage and harbour counters are the candidates.
4. Actions returning only living stock already carry `grants` (draught animals,
   tea, coffee, sugar, pepper). The one remaining stock-returning action is
   `exp_americas_factory` (fix 1).
5. Correct Complaint 133's progress paragraph: it lists tea, coffee and pepper
   as still able to use `grants`, and they already do.

Nothing else in the tables can be fixed with data alone: every other gap needs
a dependent to ask for a work that is running, and no field the engine reads
says that yet.

### Engine work the rest needs

1. A general running gate on dependents. A node field (name to be chosen; the
   `requires_running` on counters is the model) listing nodes that must be
   running, read beside `_check_missing_prereqs` in
   `sim/engine/projects_starting.py` as a blocker (kind `closed` or
   `knowledge`), and re-checked each year so a dependent's effect lapses when
   the work closes, as `_counter_strength` in `sim/engine/society_hazards.py`
   does. A validation rule beside `sim/engine/validate_unheld_gates.py` that
   every id named is a venture, since `running` equals `done` for anything
   else. Then migrate the dependents in the section above. This one change
   covers the grid, telegraph, railway, harbour, aqueduct and sewer rows.
2. Where a work is. A built work has no tile, edge, owner or size. The
   geography package already takes an `improvements` map per edge and a mode's
   `needs_improvement` (`sim/geography/queries.py`,
   `data/world/geography/route_modes/modes.json`); nothing populates it from
   what an actor has built, and `requires_nodes` on modes and sea lanes asks for
   held nodes. A works register on the actor (owner, edge or tile, size), filled
   when a construction node completes and read as `improvements`, would make
   railway, road, canal and harbour real for freight. It belongs to the actor,
   not the founder, so a state or another player can build.
3. Size. `capability.scalable` sizes institutions by units; a grid, a railway
   or a telegraph network should scale by the length or load built, with cost
   rising with size, as the benefactions already do for each repeat foundation.
4. Action results. `grants` covers living stock only. Routes opened, places
   known, deposits secured and posts held need a declared result a dependent
   can check, for example a record that this actor has sailed this lane, read
   by sea lanes in place of `requires_nodes`.
5. Action failure and loss. A failed voyage resets hours and cost
   (`FAILURE_RESET_SHARE` in `sim/engine/projects_completion.py`); it does not
   lose a hull, a crew or the cargo, and success does not consume provisions as
   stock. `apply_staff_survival` and the ledger's material stock are the pieces
   to reuse.
6. Lapse of a completed node. A completed node never leaves the done set; only
   venture closure makes `running` false. Works that fall into disuse, are
   destroyed in war or are lost with a sacked city have no representation
   beyond that, and a construction with no upkeep cannot lapse at all.
7. Duplicates, for the dedupe work: the electric telegraph exists as
   `telegraph_electric` and `if_electric_telegraph`, the submarine cable as
   `sea_submarine_cable` and `com_submarine_cable`, the aqueduct as
   `civ_aqueduct_roman` and `cn_aqueduct`, the Roman sewer as `civ_sewer_roman`
   and `cn_sewer_system`. A running requirement added to one and not the others
   leaves the founder a way round it.

## Table of candidates

Class: knowledge, construction, action, institution (see Method). Dependents:
nodes naming the id in `pre` or a `req_any` option, measured on 2026-10-06 by
`candidates.py`. Mechanism and missing piece use the codes above; `-` means
nothing is needed. Rows are ordered by file then id.

### Keyword scan

| id | file | class | dependents | fitting mechanism | missing piece |
|---|---|---|---|---|---|
| `cap_power_grid` | 00_capabilities | construction | 3 | V E | M1 |
| `cap_vac_1e9` | 00_capabilities | knowledge | 0 | - | - |
| `academy_network` | 00_core | institution | 3 | V | - |
| `exp_import_draught_animals` | 00_core | action | 0 | G P | done; M4 for non-stock results |
| `power_grid` | 00_core | construction | 25 | V E P | M1 M2 M3 |
| `railway` | 00_core | construction | 6 | V P | M1 M2 M3 |
| `semaphore_telegraph` | 00_core | construction | 2 | none: up_hours is 0 | M1 M5 |
| `telegraph_electric` | 00_core | construction | 22 | V P | M1 M2 M3 M6 |
| `water_power_scale` | 00_core | knowledge | 31 | - | - |
| `world_map` | 00_core | knowledge | 2 | - | - |
| `tex_textile_factory` | 10_textiles | institution | 0 | V | - |
| `fud_cold_chain_refrigerated_shipping` | 11_food_agriculture | construction | 0 | V | M1 M2 |
| `prn_cataloguing_system` | 13_media | knowledge | 0 | - | - |
| `lnd_assembly_line` | 14_land_transport | knowledge | 0 | - | - |
| `lnd_block_system` | 14_land_transport | knowledge | 0 | - | - |
| `lnd_macadam` | 14_land_transport | knowledge | 4 | - | - |
| `lnd_magneto` | 14_land_transport | knowledge | 0 | - | - |
| `lnd_motor_road_network` | 14_land_transport | construction | 0 | V | M1 M2 M3 |
| `lnd_paved_road_network` | 14_land_transport | construction | 2 | V N (initial holding) | M1 M2; pre is empty, so it is free knowledge |
| `lnd_signal_railway` | 14_land_transport | knowledge | 1 | - | - |
| `lnd_standard_gauge` | 14_land_transport | knowledge | 1 | - | - |
| `lnd_tarmacadam` | 14_land_transport | knowledge | 1 | - | - |
| `sea_canal_lock` | 15_ships | knowledge | 0 | - | - |
| `sea_harbours_pozzolana` | 15_ships | construction | 1 | none: up_hours is 0; ben_harbour_and_lighthouse is the model | M1 M2 M5 |
| `sea_lead_line_hydro` | 15_ships | knowledge | 0 | - | - |
| `sea_log_line` | 15_ships | knowledge | 0 | - | - |
| `sea_sounding_lines` | 15_ships | knowledge | 1 | - | - |
| `sea_submarine_cable` | 15_ships | construction | 0 | V | M1 M2 M6 |
| `air_helicopter_rotor` | 16_aviation | knowledge | 0 | - | - |
| `pwr_electric_motor_industry` | 17_energy | knowledge | 0 | - | - |
| `pwr_gas_main` | 17_energy | construction | 1 | V | M1 M2 |
| `pwr_load_factor_economics` | 17_energy | knowledge | 0 | - | - |
| `met_mine_pumping` | 19_metallurgy_mining | knowledge | 1 | - | - |
| `prc_apprentice_system` | 20_precision | institution | 1 | V | - |
| `med_aqueducts_latrines` | 21_medicine | construction | 0 | none: up_hours is 0; ben_civic_water_works is the model | M2 M5 |
| `civ_aqueduct_roman` | 22_civil | construction | 5 | V B | M1 M2 |
| `civ_canal_pound_lock` | 22_civil | knowledge | 0 | - | - |
| `civ_harbour_dock` | 22_civil | construction | 1 | V B | M1 M2 |
| `civ_precise_levelling` | 22_civil | knowledge | 0 | - | - |
| `civ_road_paved` | 22_civil | knowledge | 1 | - | - |
| `civ_sewage_treatment` | 22_civil | construction | 0 | V | M1 M2 |
| `civ_water_tower` | 22_civil | construction | 0 | V | M1 M2 |
| `civ_water_treatment` | 22_civil | construction | 0 | V | M1 M2 |
| `opt_fraunhofer_lines` | 23_optics_instruments | knowledge | 0 | - | - |
| `opt_spectroscopy_absorption` | 23_optics_instruments | knowledge | 1 | - | - |
| `opt_spectroscopy_emission` | 23_optics_instruments | knowledge | 1 | - | - |
| `com_antenna_ground` | 24_comms_computing | knowledge | 4 | - | - |
| `com_baudot_code` | 24_comms_computing | knowledge | 0 | - | - |
| `com_binary_arithmetic` | 24_comms_computing | knowledge | 3 | - | - |
| `com_duplex_telegraph` | 24_comms_computing | knowledge | 1 | - | - |
| `com_heliograph` | 24_comms_computing | knowledge | 0 | - | - |
| `com_loading_coil` | 24_comms_computing | knowledge | 1 | - | - |
| `com_morse_sounder` | 24_comms_computing | knowledge | 2 | - | - |
| `com_multiplexing` | 24_comms_computing | knowledge | 0 | - | - |
| `com_quadruplex_telegraph` | 24_comms_computing | knowledge | 0 | - | - |
| `com_relay` | 24_comms_computing | knowledge | 7 | - | - |
| `com_stock_ticker` | 24_comms_computing | knowledge | 0 | - | - |
| `com_submarine_cable` | 24_comms_computing | construction | 1 | none: up_hours is 0 | M5 M6 |
| `com_telegraph_battery` | 24_comms_computing | knowledge | 0 | - | - |
| `com_teleprinter` | 24_comms_computing | knowledge | 1 | - | - |
| `com_trunk_lines` | 24_comms_computing | construction | 1 | none: up_hours is 0 | M2 M5 |
| `com_vacuum_tube_pentode` | 24_comms_computing | knowledge | 0 | - | - |
| `com_vacuum_tube_tetrode` | 24_comms_computing | knowledge | 1 | - | - |
| `exp_africa_circumnavigation` | 30_expeditions | action | 0 | V P | M1 M4 (a route known, no dependents) |
| `exp_americas_factory` | 30_expeditions | action | 9 | V P G(not used) | M1 M4 (a post, plus seed stock via grants, is what it returns) |
| `exp_atlantic_crossing` | 30_expeditions | action | 3 | P | M4 M5 (up_hours 0: no vessel or crew is held) |
| `exp_coastal_africa` | 30_expeditions | action | 3 | V P R | M1 M4 |
| `exp_colony_administration` | 30_expeditions | institution | 2 | V P | M4 (a post that can be lost) |
| `exp_conquest_resource` | 30_expeditions | action | 0 | V P | M4 |
| `exp_oceangoing_hull` | 30_expeditions | knowledge | 3 | - | - |
| `exp_openocean_navigation` | 30_expeditions | knowledge | 4 | - | - |
| `exp_provisioning_scurvy` | 30_expeditions | knowledge | 3 | - | - |
| `exp_trade_route_extend` | 30_expeditions | action | 9 | V P R | M1 M4 |
| `exp_transplant_botany` | 30_expeditions | action | 0 | V P G(not used) | M4 (crop is generic, grants needs a named material) |
| `fin_canal_company` | 40_finance_institutions | institution | 1 | V | M1 M2 (the canal itself has no node) |
| `fin_census` | 40_finance_institutions | institution | 1 | V | - |
| `fin_railway_company` | 40_finance_institutions | institution | 1 | V | M1 (should need railway running) |
| `fin_survey_map` | 40_finance_institutions | institution | 1 | V | - |
| `fin_telegraph_business` | 40_finance_institutions | institution | 2 | V | M1 (should need telegraph_electric running) |
| `fin_toll_bridge` | 40_finance_institutions | institution | 0 | V | - |
| `fin_turnpike_trust` | 40_finance_institutions | institution | 0 | V | - |
| `el2_earthing_grounding_system` | 42_electrical_deep | knowledge | 0 | - | - |
| `el2_impedance_matching_transformer_network` | 42_electrical_deep | knowledge | 1 | - | - |
| `el2_load_dispatch_and_scheduling` | 42_electrical_deep | institution | 0 | V | - |
| `el2_ring_main_distribution` | 42_electrical_deep | construction | 0 | V | M1 M2 |
| `el2_synchronous_motor` | 42_electrical_deep | knowledge | 6 | - | - |
| `el2_telephone_exchange_switching_network` | 42_electrical_deep | construction | 0 | V | M1 M2 |
| `el2_tetrode_four_electrode_tube` | 42_electrical_deep | knowledge | 3 | - | - |
| `el2_three_wire_distribution_system` | 42_electrical_deep | knowledge | 0 | - | - |
| `el2_transmission_line_coaxial_cable` | 42_electrical_deep | knowledge | 2 | - | - |
| `mfg_assembly_line` | 43_manufacturing_deep | knowledge | 0 | - | - |
| `mfg_tolerance_limit` | 43_manufacturing_deep | knowledge | 2 | - | - |
| `md2_endocrine_system` | 44_medicine_deep | knowledge | 2 | - | - |
| `md2_immunity` | 44_medicine_deep | knowledge | 13 | - | - |
| `md2_nervous_system` | 44_medicine_deep | knowledge | 1 | - | - |
| `md2_notifiable_disease` | 44_medicine_deep | institution | 1 | none | - |
| `md2_vital_registration` | 44_medicine_deep | institution | 3 | none | - |
| `tl_anti_siphon_valve` | 45a_transport_land_deep | knowledge | 0 | - | - |
| `tl_cambered_drainage` | 45a_transport_land_deep | knowledge | 0 | - | - |
| `tl_concrete_roadway` | 45a_transport_land_deep | knowledge | 0 | - | - |
| `tl_hydraulic_brake_line` | 45a_transport_land_deep | knowledge | 0 | - | - |
| `tl_level_crossing` | 45a_transport_land_deep | knowledge | 0 | - | - |
| `tl_macadam_road` | 45a_transport_land_deep | knowledge | 0 | - | - |
| `tl_pressure_relief_valve` | 45a_transport_land_deep | knowledge | 0 | - | - |
| `tl_road_roller` | 45a_transport_land_deep | knowledge | 0 | - | - |
| `tr_ballast_tank` | 45b_transport_rail_marine_deep | knowledge | 0 | - | - |
| `tr_block_signalling` | 45b_transport_rail_marine_deep | knowledge | 1 | - | - |
| `tr_canal_lift` | 45b_transport_rail_marine_deep | knowledge | 0 | - | - |
| `tr_canal_lock` | 45b_transport_rail_marine_deep | knowledge | 2 | - | - |
| `tr_fore_and_aft_rigging` | 45b_transport_rail_marine_deep | knowledge | 0 | - | - |
| `tr_lifeboat` | 45b_transport_rail_marine_deep | knowledge | 0 | - | - |
| `tr_semaphore_signal` | 45b_transport_rail_marine_deep | knowledge | 3 | - | - |
| `tr_ship_telegraph` | 45b_transport_rail_marine_deep | knowledge | 0 | - | - |
| `ag2_coffee_voyage` | 47_agri_food_deep | action | 0 | G P | done; the dependent crop nodes still use pre |
| `ag2_pure_line_selection` | 47_agri_food_deep | knowledge | 1 | - | - |
| `ag2_sugar_voyage` | 47_agri_food_deep | action | 1 | G P | done; the dependent crop nodes still use pre |
| `ag2_tea_voyage` | 47_agri_food_deep | action | 0 | G P | done; the dependent crop nodes still use pre |
| `in2_geodetic_apparatus` | 48_instruments_deep | knowledge | 0 | - | - |
| `in2_sextant_navigation` | 48_instruments_deep | knowledge | 0 | - | - |
| `in2_sounding_machine_lead_line` | 48_instruments_deep | knowledge | 0 | - | - |
| `mil_belt_feed` | 49_military | knowledge | 0 | - | - |
| `mil_chain_home` | 49_military | construction | 0 | none: up_hours is 0 | M2 M5 |
| `mil_iff_system` | 49_military | knowledge | 0 | - | - |
| `mil_railway_mobilisation` | 49_military | institution | 0 | none | - |
| `mil_track` | 49_military | knowledge | 2 | - | - |
| `tx2_sizing_systems` | 50_textiles_consumer_deep | knowledge | 3 | - | - |
| `cn_aqueduct` | 51_construction_deep | construction | 1 | V B | M1 M2 M6 |
| `cn_central_heating` | 51_construction_deep | knowledge | 0 | - | - |
| `cn_crane_derrick` | 51_construction_deep | knowledge | 0 | - | - |
| `cn_dewatering` | 51_construction_deep | knowledge | 0 | - | - |
| `cn_expansion_joint` | 51_construction_deep | knowledge | 0 | - | - |
| `cn_forced_ventilation` | 51_construction_deep | knowledge | 0 | - | - |
| `cn_formwork_shuttering` | 51_construction_deep | knowledge | 1 | - | - |
| `cn_plumbing_stack` | 51_construction_deep | knowledge | 3 | - | - |
| `cn_scaffolding` | 51_construction_deep | knowledge | 0 | - | - |
| `cn_sewer_system` | 51_construction_deep | construction | 0 | V | M1 M2 |
| `cn_suspension_bridge` | 51_construction_deep | knowledge | 0 | - | - |
| `en_battery_charging` | 52_energy_deep | knowledge | 0 | - | - |
| `en_fuel_injection` | 52_energy_deep | knowledge | 0 | - | - |
| `en_grid_interconnection` | 52_energy_deep | construction | 0 | V | M1 M2 |
| `en_hydraulic_power_main` | 52_energy_deep | construction | 0 | V | M1 M2 |
| `en_liquid_propellant` | 52_energy_deep | knowledge | 0 | - | - |
| `en_pumped_storage` | 52_energy_deep | construction | 0 | V | M1 M2 |
| `en_transmission_line` | 52_energy_deep | knowledge | 3 | - | - |
| `en_turbine_condenser_vacuum` | 52_energy_deep | knowledge | 0 | - | - |
| `if_electric_telegraph` | 53_information_deep | construction | 0 | V | M1 M6 |
| `if_index_card_system` | 53_information_deep | knowledge | 1 | - | - |
| `if_telegraph_relay` | 53_information_deep | knowledge | 2 | - | - |
| `sc2_notation_metric_unit` | 54_science_method_deep | knowledge | 1 | - | - |
| `sc2_statistics_regression` | 54_science_method_deep | knowledge | 1 | - | - |
| `ag2_guano_deposit_access` | 55_realism_part02 | action | 1 | V N | M4 (access to a located deposit) |
| `ben_civic_water_works` | 56_benefactions | construction | 0 | V B H | none: already the model |
| `ben_free_school_foundation` | 56_benefactions | construction | 0 | V B | none: already the model |
| `ben_grain_dole` | 56_benefactions | construction | 0 | V B H | none: already the model |
| `ben_harbour_and_lighthouse` | 56_benefactions | construction | 0 | V B H R | none: already the model |
| `ben_hospital_foundation` | 56_benefactions | construction | 0 | V B H | none: already the model |
| `ben_house_bank` | 56_benefactions | institution | 0 | V B | - |
| `ben_public_games` | 56_benefactions | institution | 0 | V B | - |
| `ben_public_library` | 56_benefactions | construction | 0 | V B | none: already the model |
| `ben_research_foundation` | 56_benefactions | institution | 0 | V B | - |
| `ben_scholar_and_artist_patronage` | 56_benefactions | institution | 0 | V B | - |
| `ben_state_subvention` | 56_benefactions | institution | 0 | V B | - |
| `ben_survey_and_trade_expedition` | 56_benefactions | action | 0 | V B R P | M4 (a survey result is not declared) |
| `ben_telegraph_network` | 56_benefactions | construction | 0 | V B | none: already the model; no dependents |
| `ben_temple_endowment` | 56_benefactions | institution | 0 | V B | - |
| `ben_underwriting_syndicate` | 56_benefactions | institution | 0 | V B | - |

### Infrastructure scan (kind INFRASTRUCTURE, not matched above)

| id | file | class | dependents | fitting mechanism | missing piece |
|---|---|---|---|---|---|
| `hom_bath_piped_hot_water` | 12_household | knowledge | 0 | - | - |
| `hom_flush_latrine_simple` | 12_household | knowledge | 2 | - | - |
| `hom_flush_toilet_trap` | 12_household | knowledge | 0 | - | - |
| `hom_latrine_water_trap` | 12_household | knowledge | 2 | - | - |
| `hom_lead_plumbing` | 12_household | knowledge | 2 | - | - |
| `hom_public_bath` | 12_household | construction | 0 | none: up_hours is 0 | M2 M5 |
| `hom_sewer_stormwater_separation` | 12_household | construction | 0 | none: up_hours is 0 | M2 M5 |
| `sea_drydock` | 15_ships | construction | 0 | V | M1 M2 |
| `med_clinical_trials` | 21_medicine | knowledge | 0 | - | - |
| `med_epidemiology_statistics` | 21_medicine | knowledge | 2 | - | - |
| `med_quarantine_sanitation` | 21_medicine | knowledge | 1 | - | - |
| `med_vector_control` | 21_medicine | knowledge | 0 | - | - |
| `civ_cofferdam` | 22_civil | knowledge | 4 | - | - |
| `civ_dam_arch` | 22_civil | construction | 0 | V | M1 M2 |
| `civ_dam_earth_fill` | 22_civil | construction | 0 | V | M1 M2 |
| `civ_dam_gravity` | 22_civil | construction | 1 | V | M1 M2 |
| `civ_gate_sluice` | 22_civil | knowledge | 1 | - | - |
| `civ_pumping_station` | 22_civil | construction | 4 | V | M1 M2 |
| `civ_sewer_roman` | 22_civil | construction | 3 | V | M1 M2 |
| `civ_sewer_separate` | 22_civil | construction | 1 | V | M1 M2 |
| `civ_street_lighting` | 22_civil | construction | 0 | none: up_hours is 0 | M1 M2 M5 |
| `fin_postal_service` | 40_finance_institutions | institution | 2 | V | M1 M2 (the post road network is not a node) |
| `el2_power_factor_correction_capacitor` | 42_electrical_deep | knowledge | 0 | - | - |
| `el2_protective_relaying_differential` | 42_electrical_deep | knowledge | 0 | - | - |
| `el2_standardised_frequency_nominal` | 42_electrical_deep | knowledge | 1 | - | - |
| `el2_standardised_voltage_nominal` | 42_electrical_deep | knowledge | 0 | - | - |
| `el2_substation_voltage_regulation` | 42_electrical_deep | knowledge | 2 | - | - |
| `el2_synchroscope_phase_angle_indicator` | 42_electrical_deep | knowledge | 0 | - | - |
| `el2_tap_changer_load_compensator` | 42_electrical_deep | knowledge | 0 | - | - |
| `md2_activated_sludge` | 44_medicine_deep | construction | 0 | none: up_hours is 0 | M2 M5 |
| `md2_child_clinic` | 44_medicine_deep | knowledge | 0 | - | - |
| `md2_chlorination` | 44_medicine_deep | knowledge | 0 | - | - |
| `md2_contact_tracing` | 44_medicine_deep | knowledge | 0 | - | - |
| `md2_food_adulteration_law` | 44_medicine_deep | knowledge | 0 | - | - |
| `md2_hospital_infection_control` | 44_medicine_deep | knowledge | 0 | - | - |
| `md2_isolation_hospital` | 44_medicine_deep | construction | 0 | none: up_hours is 0 | M2 M5 |
| `md2_maternal_clinic` | 44_medicine_deep | knowledge | 0 | - | - |
| `md2_meat_inspection` | 44_medicine_deep | knowledge | 0 | - | - |
| `md2_milk_pasteurisation` | 44_medicine_deep | knowledge | 0 | - | - |
| `md2_mosquito_net` | 44_medicine_deep | knowledge | 0 | - | - |
| `md2_pit_latrine` | 44_medicine_deep | knowledge | 0 | - | - |
| `md2_sand_filtration` | 44_medicine_deep | construction | 1 | none: up_hours is 0 | M2 M5 |
| `md2_sewage_separation` | 44_medicine_deep | construction | 1 | none: up_hours is 0 | M2 M5 |
| `md2_vector_control` | 44_medicine_deep | knowledge | 1 | - | - |
| `tl_kerbing` | 45a_transport_land_deep | knowledge | 0 | - | - |
| `cn_arch_bridge_steel` | 51_construction_deep | knowledge | 0 | - | - |
| `cn_bascule_bridge` | 51_construction_deep | knowledge | 0 | - | - |
| `cn_cable_anchorage` | 51_construction_deep | knowledge | 0 | - | - |
| `cn_pontoon_bridge` | 51_construction_deep | knowledge | 0 | - | - |
| `cn_siphon` | 51_construction_deep | knowledge | 0 | - | - |
| `cn_stiffening_truss` | 51_construction_deep | knowledge | 0 | - | - |
| `cn_swing_bridge` | 51_construction_deep | knowledge | 0 | - | - |
| `cn_water_main` | 51_construction_deep | construction | 1 | V | M1 M2 |
| `en_circuit_breaker` | 52_energy_deep | knowledge | 1 | - | - |
| `en_draft_tube` | 52_energy_deep | knowledge | 0 | - | - |
| `en_flywheel_storage` | 52_energy_deep | knowledge | 0 | - | - |
| `en_frequency_standardisation` | 52_energy_deep | knowledge | 1 | - | - |
| `en_fuse` | 52_energy_deep | knowledge | 0 | - | - |
| `en_gas_holder` | 52_energy_deep | knowledge | 0 | - | - |
| `en_hydraulic_accumulator` | 52_energy_deep | knowledge | 1 | - | - |
| `en_hydroelectric_station` | 52_energy_deep | construction | 1 | V E | M1 M2 |
| `en_insulator` | 52_energy_deep | knowledge | 2 | - | - |
| `en_lightning_arrester` | 52_energy_deep | knowledge | 0 | - | - |
| `en_load_factor_diversity` | 52_energy_deep | knowledge | 0 | - | - |
| `en_penstock` | 52_energy_deep | knowledge | 0 | - | - |
| `en_power_factor_correction` | 52_energy_deep | knowledge | 0 | - | - |
| `en_substation` | 52_energy_deep | knowledge | 7 | - | - |
| `en_switchgear` | 52_energy_deep | knowledge | 3 | - | - |
| `en_thermal_station` | 52_energy_deep | construction | 0 | V E | M1 M2 |
| `en_transformer` | 52_energy_deep | knowledge | 4 | - | - |
