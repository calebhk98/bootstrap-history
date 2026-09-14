# CONTRACT for tech-tree branch authors

You are writing ONE JSON file: a list of technology nodes for one domain, for a
tree that runs from the Roman Empire of 100 AD to modern technology.

## Non-negotiable rules

1. **Output a JSON array of node objects and nothing else.** No prose, no
   markdown fence, no trailing commas. It must parse with `json.load`.
2. **Every id in `pre` must either be defined in YOUR OWN file, or appear in
   `VOCABULARY.md`.** Anything else is rejected.
3. **Every id you define must be globally unique and prefixed for your domain**
   (the prefix is given in your brief). Lowercase, digits and underscores only.
4. **Judge each technology in isolation.** Each node must be defensible on its
   own: could a competent person, having everything in `pre`, actually build
   this? If the honest answer needs a capability rung (a furnace temperature, a
   machining tolerance, a vacuum level, a purity, a power source, a measurement),
   **put that rung in `pre`**. This is the single most important instruction.
   A node that says "build an aeroplane" with `pre: ["mat_wrought_iron"]` is a
   failure.
5. **Never invent a number you do not have.** Costs and hours are estimates by
   definition; make them proportionate and internally consistent. Set `conf` to
   `C` whenever you are guessing, which will be most of the time.
6. **Anachronism.** Roman *nitrum* is sodium carbonate, NOT saltpetre. Rome has
   no cast iron in the West, no paper, no distilled spirits, no soap as a
   cleanser, no crank and connecting rod before the 3rd century, no zero or
   positional notation. Rome DOES have glassblowing and near-colourless glass,
   hydraulic concrete, water mills, the screw press, force pumps, mercury,
   excellent gear cutting, and superb civil engineering. There is no rubber, no
   gutta percha, no quinine and no New World crop, ever, in any plan.
7. **No em dashes anywhere.** Use commas or plain hyphens.

## Node schema

```json
{
  "id": "tex_spinning_wheel",
  "name": "Spinning wheel",
  "tier": 1,
  "cat": "textiles",
  "pre": ["cap_tol_1mm", "crank_conrod", "mat_wrought_iron"],
  "kb": "",
  "ph": 60,
  "lab": {"carpenter": 300, "artisan": 200},
  "mat": {"timber_m3": 2, "iron_bar_kg": 8},
  "cap": 120,
  "up": 40,
  "yrs": 1.0,
  "risk": 0.15,
  "sus": 0,
  "gov": 1,
  "rev": 400,
  "sch": 0,
  "art": 1,
  "conf": "B",
  "note": "Roughly a threefold gain in yarn output per spinner..."
}
```

| field | meaning |
|---|---|
| `tier` | 0 Rome already has it and it is free, 1 immediate/cheap, 2 industrial foundation, 3 heavy industry, 4 late industrial, 5 modern, 9 UNOBTAINABLE |
| `pre` | prerequisite ids, AND semantics. **Include capability rungs.** |
| `ph` | the founder's own hours. Scarce: he has about 72,000 in a lifetime. Most nodes should be 40 to 400; only things needing his personal insight go above 600. |
| `lab` | hired hours by trade. Allowed trades ONLY: labourer, artisan, master, glassblower, smith, carpenter, miner, scribe, scholar, furnaceman, potter, chemist, machinist |
| `mat` | materials consumed. Allowed keys are listed in PRICED_MATERIALS below. |
| `cap` | one-off capital in denarii beyond labour and materials |
| `up` | annual upkeep in denarii |
| `yrs` | **calendar floor**: curing, growing, seasoning, or a generation of economic diffusion. Money cannot buy this down. Be honest; this is what sets the real timeline. |
| `risk` | 0 to 1, probability an attempt fails outright |
| `sus` | suspicion delta. Rome executes magicians and much of this looks like magic. |
| `gov` | State interest, -3 will actively suppress, +3 will fund and demand. **Use negative values.** Labour-displacing machinery, anything breaking elite information control, and anything that looks like a faction all attract hostility. |
| `rev` | net denarii per year at maturity, 0 if not a product |
| `sch` / `art` | trained scholars and artisans required on staff |
| `conf` | A well attested, B probable, C your estimate |
| `note` | 1 to 4 sentences. State the non-obvious kernel, the honest limitation, and any anachronism trap. This is the most valuable field; write it like you are explaining to someone who has to actually do it. |

## PRICED_MATERIALS (allowed keys for `mat`)

wheat_kg olive_oil_kg wine_common_kg charcoal_kg firewood_kg coal_kg iron_bar_kg
iron_bloom_kg steel_noric_kg copper_kg tin_kg lead_kg brass_kg silver_kg gold_kg
mercury_kg sulfur_kg natron_kg lime_kg alum_kg green_vitriol_kg pyrolusite_kg
calamine_kg galena_kg fluorspar_kg sand_quartz_kg clay_kg glass_raw_kg
linen_rag_kg papyrus_sheet parchment_sheet silk_kg shellac_kg beeswax_kg
tallow_kg emery_kg asbestos_kg bitumen_kg timber_m3 brick_1000 ox mule
slave_unskilled slave_skilled iugerum_land iron_ore_kg copper_ore_kg cinnabar_kg
bauxite_kg manganese_kg wood_ash_kg manure_kg salt_kg blue_vitriol_kg
boric_acid_kg agate_kg antimony_kg cryolite_kg flue_dust_kg graphite_kg
quartz_tube_kg bronze_kg zinc_kg iron_sheet_kg steel_plate_kg nickel_kg
tungsten_kg barium_kg platinum_g gold_g indium_g germanium_g phosphor_bronze_g
sulfuric_acid_kg nitric_acid_kg hydrochloric_acid_kg nitre_kg carbon_kg
hydrogen_m3 oxygen_m3 argon_or_h2_m3 linen_kg leather_kg

If you need a material that is not on this list, use the closest one on the list
and say so in the `note`. Do not invent a key.

## Quality bar

The reader is a competent adult with no specialist training who has been dropped
into 100 AD with this file. Your `note` should tell them something they could not
have worked out. "Spinning wheel: spins thread faster" is worthless. "Spinning
wheel: the flyer, not the wheel, is the invention, because it twists and winds
simultaneously instead of alternately" is worth having.
