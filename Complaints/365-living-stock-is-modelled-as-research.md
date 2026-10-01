# Living stock (silkworms, breeding animals, seed stock, rubber, spices) is modelled as research instead of something held

**Status:** partly - silkworm eggs, ramie stock and draught animals are held stock; the rest of the stock nodes remain

Silk needs silkworm eggs, not knowledge; today a research node stands for holding them (`tx2_silkworm_native_stock`, and the route-or-native `req_any`). The same pattern applies to draught and dairy animals, crop seed stock, rubber trees, spice plants. Having the stock is a possession at a place; knowing how to keep it alive or improve it is research that needs the stock.

What it would take: living stock as a material held at a location (the tree's `req_any` already accepts a material); each civilisation starts with what it held at its date; trade, gift or later smuggling transfers it and the tree opens by itself; breeding and improving stock are side branches with their own industry; a country refusing to sell its eggs is that country's policy as an actor, not a market rule. Related: 133 (some technologies are actions, not research).

## What is done

- A node may name `holds` ({material: units}); the start gate refuses it while the stock is not in the
  held-stock ledger, as a supply blocker (`sim/engine/living_stock.py`, `sim/world/living_stock.py`).
  A venture may name `grants`, stock it brings back on completion. A civilisation's `opening_stock`
  is what it held at its date. `needs_first` entries may name a `material` and `units`.
- Silkworms: `tx2_silkworm_stock` and the stand-in `tx2_silkworm_native_stock` are gone;
  `tx2_silk_fibre` and `tx2_sericulture` hold `silkworm_eggs_kg`. Han opens holding eggs and lists
  them in `will_not_sell`; the foreign trade (`foreign_economies.py`) and a purchase from a partner
  (`Sim.buy_stock_from_partner`) both respect the field.
- Crop seed stock: `tx2_ramie_plant_stock` is gone; `tx2_ramie_fibre` holds `ramie_stock_kg`, which
  Han opens holding (and now starts with `tx2_ramie_fibre`, the fibre it grew).
- Draught animals: the Mexica `needs_first` gate lifts by holding `draught_animal_kg`, however it
  came; `exp_import_draught_animals` stays an expedition and grants the founding herd.
- Production entries for the three materials are in `data/production/94_agri_organics_gaps.json`.

## What remains

Still research nodes that stand for holding stock: `tx2_cashmere_goat_stock`, `tx2_angora_goat_stock`,
`tx2_jute_seed_stock` (each behind `sea_monsoon_route`), `ag2_hop_stock`, `ag2_pyrethrum_stock`
(behind `ag2_botanic_garden`), the pepper vines in `fud_pepper_cultivation`, `mat_natural_rubber`
(behind `exp_coastal_africa`), dairy cattle in `fud_livestock_selective_cattle`, and the tea, coffee
and sugar cane voyages. Each needs a stock material, a production entry gated on a node some partner
holds, and `opening_stock` for the civilisation that held it. Draught animals are not yet in the
opening stock of the Old World civilisations (nothing there reads them). Held stock does not breed or
die and no command buys it: Complaints/366.
