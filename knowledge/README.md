# knowledge/ - the how-to library

**This file is generated. Do not edit it.** Run `python3 rome/sim/build_index.py`.

A tech tree that says *microscope requires glass* is useless to someone who does
not already know that one melted bead of glass gives 250x. The tree in
`../data/tech_tree.json` says WHAT and IN WHAT ORDER. These modules say HOW, at a
level of detail a competent non-specialist can act on: masses, ratios,
temperatures with Roman-observable proxies, vessel materials, how to tell it
worked, how it fails, what it costs, and what it will do to you.

## Start here

**[`00_NONOBVIOUS_TRICKS.md`](00_NONOBVIOUS_TRICKS.md)** is the index of specific
physical tricks: the glass-bead microscope, the three-plate method, downward zinc
distillation, the Sprengel pump, zone refining, and the rest. If you read one file
in this directory, read that one.

## Modules

| Module | Subject | Entries | Tree nodes it documents |
|---|---|---:|---:|
| [`00_NONOBVIOUS_TRICKS.md`](00_NONOBVIOUS_TRICKS.md) | The tricks that make everything else buildable. READ FIRST. | 11 | 0 |
| [`03_SOCIAL_POLITICS.md`](03_SOCIAL_POLITICS.md) |  | 10 | 0 |
| [`10_metallurgy.md`](10_metallurgy.md) | Metallurgy, fuel and refractories | 19 | 182 |
| [`20_chemistry.md`](20_chemistry.md) | Chemistry, acids, alkalis and energetics | 16 | 190 |
| [`30_glass_optics.md`](30_glass_optics.md) | Glass, optics and scientific instruments | 17 | 168 |
| [`40_power_precision.md`](40_power_precision.md) | Prime movers, machine tools and precision | 21 | 223 |
| [`50_electricity.md`](50_electricity.md) | Electricity, magnetism and electrical machines | 15 | 194 |
| [`55_semiconductors.md`](55_semiconductors.md) | Vacuum, high purity and semiconductors | 13 | 17 |
| [`60_mathematics_method.md`](60_mathematics_method.md) | Mathematics, physics and the scientific method | 13 | 71 |
| [`70_medicine_biology.md`](70_medicine_biology.md) | Medicine, public health and biology | 13 | 153 |
| [`75_agriculture_food.md`](75_agriculture_food.md) | Agriculture, food and surplus | 12 | 58 |
| [`76_farming_food_deep.md`](76_farming_food_deep.md) |  | 115 | 112 |
| [`80_information_printing.md`](80_information_printing.md) | Paper, printing and the survival of knowledge | 11 | 59 |
| [`85_transport_civil.md`](85_transport_civil.md) | Transport, mining and civil engineering | 12 | 189 |
| [`86_transport_deep.md`](86_transport_deep.md) |  | 211 | 192 |
| [`87_construction.md`](87_construction.md) |  | 101 | 94 |
| [`88_media_signals.md`](88_media_signals.md) |  | 100 | 80 |
| [`89_remaining_arts.md`](89_remaining_arts.md) |  | 227 | 197 |
| [`90_textiles.md`](90_textiles.md) |  | 20 | 198 |
| [`91_household.md`](91_household.md) |  | 27 | 67 |
| [`92_vehicles_flight.md`](92_vehicles_flight.md) |  | 29 | 0 |
| [`93_energy.md`](93_energy.md) |  | 27 | 0 |
| [`94_computing.md`](94_computing.md) |  | 22 | 0 |
| [`95_expeditions.md`](95_expeditions.md) |  | 11 | 12 |
| [`96_finance.md`](96_finance.md) |  | 34 | 86 |
| [`97_military.md`](97_military.md) |  | 29 | 109 |
| [`98_power_plants.md`](98_power_plants.md) |  | 115 | 94 |
| [`99_AUDIT.md`](99_AUDIT.md) | Adversarial audit of the technical modules | 0 | 0 |

### Nodes documented in the top-level prose files

These are institutional, political and economic nodes. Their 'how to' is a
strategy, not a procedure, so it lives outside the recipe library.

| Node | Tier | Your hours | Documented in |
|---|---:|---:|---|
| `arrival_orientation` | 0 | 900.0 | [`00_BRIEFING.md`](../00_BRIEFING.md) |
| `citizenship` | 0 | 250.0 | [`03_SOCIAL_POLITICS.md`](../03_SOCIAL_POLITICS.md) |
| `identity_cover` | 0 | 500.0 | [`03_SOCIAL_POLITICS.md`](../03_SOCIAL_POLITICS.md) |
| `patron_local` | 0 | 400.0 | [`03_SOCIAL_POLITICS.md`](../03_SOCIAL_POLITICS.md) |
| `collegium_licensed` | 1 | 350.0 | [`03_SOCIAL_POLITICS.md`](../03_SOCIAL_POLITICS.md) |
| `freedman_staff` | 1 | 900.0 | [`03_SOCIAL_POLITICS.md`](../03_SOCIAL_POLITICS.md) |
| `patron_senatorial` | 1 | 600.0 | [`03_SOCIAL_POLITICS.md`](../03_SOCIAL_POLITICS.md) |
| `school_founded` | 1 | 2,000.0 | [`03_SOCIAL_POLITICS.md`](../03_SOCIAL_POLITICS.md) |
| `workshop_first` | 1 | 500.0 | [`00_BRIEFING.md`](../00_BRIEFING.md) |
| `endowment_land` | 2 | 500.0 | [`03_SOCIAL_POLITICS.md`](../03_SOCIAL_POLITICS.md) |
| `mining_concession` | 2 | 400.0 | [`01_WORLD_STATE_100AD.md`](../01_WORLD_STATE_100AD.md) |
| `patron_imperial` | 2 | 900.0 | [`03_SOCIAL_POLITICS.md`](../03_SOCIAL_POLITICS.md) |
| `academy_network` | 3 | 2,500.0 | [`03_SOCIAL_POLITICS.md`](../03_SOCIAL_POLITICS.md) |

## Every tech-tree node, and where its recipe lives

Sorted by module. Migrated modules are sorted by node id; sections still
awaiting migration retain their legacy tier ordering for a stable partial diff.

### 10_metallurgy.md

| Node | Your hours | Recipe |
|---|---:|---|
| `arc_furnace_ferroalloys` | 600.0 | [`alloy_steels_ferroalloys`](10_metallurgy.md#alloy_steels_ferroalloys---ferromanganese-ferrosilicon-tungsten-and-chrome-steels) |
| `bellows_water_blown` | 300.0 | [`bellows_water_blown`](10_metallurgy.md#bellows_water_blown---water-driven-double-bellows-and-the-trompe) |
| `blast_furnace` | 900.0 | [`blast_furnace_cast_iron`](10_metallurgy.md#blast_furnace_cast_iron---the-tall-shaft-furnace-and-cast-iron) |
| `case_hardening` | 300.0 | [`case_hardening`](10_metallurgy.md#case_hardening---surface-hardening-a-finished-tool-ferrum-indurare) |
| `cementation_steel` | 400.0 | [`cementation_steel`](10_metallurgy.md#cementation_steel---blister-steel) |
| `charcoal_industrial` | 250.0 | [`charcoal_industrial`](10_metallurgy.md#charcoal_industrial---charcoal-at-scale-carbo) |
| `coal_coke` | 350.0 | [`coal_and_coke`](10_metallurgy.md#coal_and_coke---sea-coal-and-coking-carbo-fossilis) |
| `crucible_steel` | 600.0 | [`crucible_steel`](10_metallurgy.md#crucible_steel---melted-homogeneous-steel-huntsman-process) |
| `drawplate_wire` | 180.0 | [`wire_drawing`](10_metallurgy.md#wire_drawing---the-drawplate) |
| `finery_puddling` | 500.0 | [`finery_forge`](10_metallurgy.md#finery_forge---converting-pig-iron-to-wrought-iron-fining) |
| `high_temp_furnace` | 800.0 | [`high_temp_furnace`](10_metallurgy.md#high_temp_furnace---pushing-past-1500-c) |
| `lead_metallurgy` | 200.0 | [`lead_silver_cupellation`](10_metallurgy.md#lead_silver_cupellation---refining-silver-from-lead-ore-cupellatio) |
| `mat_bulk_steel` | 900.0 | [`alloy_steels_ferroalloys`](10_metallurgy.md#alloy_steels_ferroalloys---ferromanganese-ferrosilicon-tungsten-and-chrome-steels) |
| `mat_copper` | 200.0 | [`copper_refining`](10_metallurgy.md#copper_refining---fire-refining-copper-aes) |
| `mercury_supply` | 150.0 | [`mercury`](10_metallurgy.md#mercury---retorting-cinnabar-hydrargyrum) |
| `met_acetylene_supply` | 200.0 | _(module has no anchor)_ |
| `met_annealing_recrystallization` | 100.0 | _(module has no anchor)_ |
| `met_basic_lining_phosphorus` | 240.0 | _(module has no anchor)_ |
| `met_black_powder_blasting` | 120.0 | _(module has no anchor)_ |
| `met_bloomery_bog_iron` | 100.0 | [`bloomery_iron`](10_metallurgy.md#bloomery_iron) **BROKEN** |
| `met_chill_casting` | 100.0 | _(module has no anchor)_ |
| `met_continuous_casting` | 140.0 | _(module has no anchor)_ |
| `met_converter_furnace` | 180.0 | _(module has no anchor)_ |
| `met_cupola_furnace` | 150.0 | _(module has no anchor)_ |
| `met_deep_drawing` | 350.0 | _(module has no anchor)_ |
| `met_deep_shaft_sinking` | 240.0 | _(module has no anchor)_ |
| `met_die_casting` | 180.0 | _(module has no anchor)_ |
| `met_drawn_tube` | 100.0 | _(module has no anchor)_ |
| `met_drop_hammer` | 280.0 | _(module has no anchor)_ |
| `met_dry_sand_mold` | 120.0 | _(module has no anchor)_ |
| `met_dynamite_blasting` | 100.0 | _(module has no anchor)_ |
| `met_electro_refining` | 100.0 | _(module has no anchor)_ |
| `met_extrusion_press` | 450.0 | _(module has no anchor)_ |
| `met_fire_assay` | 60.0 | _(module has no anchor)_ |
| `met_froth_flotation` | 300.0 | _(module has no anchor)_ |
| `met_galvanizing` | 120.0 | _(module has no anchor)_ |
| `met_green_sand_mold` | 80.0 | _(module has no anchor)_ |
| `met_hardenability_alloys` | 280.0 | _(module has no anchor)_ |
| `met_hydraulic_press` | 350.0 | _(module has no anchor)_ |
| `met_investment_casting` | 100.0 | _(module has no anchor)_ |
| `met_jigging_gravity` | 80.0 | _(module has no anchor)_ |
| `met_mine_pumping` | 180.0 | _(module has no anchor)_ |
| `met_normalizing` | 100.0 | _(module has no anchor)_ |
| `met_open_hearth_furnace` | 220.0 | _(module has no anchor)_ |
| `met_ore_crushing_sorting` | 20.0 | _(module has no anchor)_ |
| `met_pneumatic_drill` | 180.0 | _(module has no anchor)_ |
| `met_powder_metallurgy` | 260.0 | _(module has no anchor)_ |
| `met_quenching_media` | 140.0 | _(module has no anchor)_ |
| `met_rail_mill` | 180.0 | _(module has no anchor)_ |
| `met_reverberatory` | 200.0 | _(module has no anchor)_ |
| `met_reversing_mill` | 240.0 | _(module has no anchor)_ |
| `met_roasting_calcining` | 60.0 | _(module has no anchor)_ |
| `met_safety_lamps_ventilation` | 140.0 | _(module has no anchor)_ |
| `met_section_mill` | 200.0 | _(module has no anchor)_ |
| `met_steam_hammer` | 180.0 | _(module has no anchor)_ |
| `met_tempering_color` | 120.0 | _(module has no anchor)_ |
| `met_three_high_mill` | 200.0 | _(module has no anchor)_ |
| `met_tin_plate` | 100.0 | _(module has no anchor)_ |
| `met_trip_hammer` | 80.0 | _(module has no anchor)_ |
| `met_tube_mill_seamless` | 220.0 | _(module has no anchor)_ |
| `met_two_high_mill` | 280.0 | _(module has no anchor)_ |
| `met_water_ore_stamp` | 120.0 | _(module has no anchor)_ |
| `met_winding_engine` | 200.0 | _(module has no anchor)_ |
| `met_wire_rod_rolling` | 160.0 | _(module has no anchor)_ |
| `mt2_age_hardening_aluminum` | 280.0 | _(module has no anchor)_ |
| `mt2_alumina_ceramic` | 200.0 | _(module has no anchor)_ |
| `mt2_aluminum_alloy_series` | 280.0 | _(module has no anchor)_ |
| `mt2_amalgamation` | 80.0 | _(module has no anchor)_ |
| `mt2_annealing` | 100.0 | _(module has no anchor)_ |
| `mt2_austenitizing` | 120.0 | _(module has no anchor)_ |
| `mt2_babbitt_metal` | 130.0 | _(module has no anchor)_ |
| `mt2_ball_mill_grinding` | 140.0 | _(module has no anchor)_ |
| `mt2_basic_converter` | 160.0 | _(module has no anchor)_ |
| `mt2_bell_metal` | 120.0 | _(module has no anchor)_ |
| `mt2_bone_china` | 140.0 | _(module has no anchor)_ |
| `mt2_brinell_hardness` | 130.0 | _(module has no anchor)_ |
| `mt2_britannia_metal` | 120.0 | _(module has no anchor)_ |
| `mt2_carborundum_ceramic` | 220.0 | _(module has no anchor)_ |
| `mt2_carburising` | 140.0 | _(module has no anchor)_ |
| `mt2_cement_varieties` | 160.0 | _(module has no anchor)_ |
| `mt2_charpy_impact_test` | 180.0 | _(module has no anchor)_ |
| `mt2_chromite_refractory` | 170.0 | _(module has no anchor)_ |
| `mt2_chromium_extraction` | 220.0 | _(module has no anchor)_ |
| `mt2_classifier_size_separation` | 110.0 | _(module has no anchor)_ |
| `mt2_cobalt_extraction` | 150.0 | _(module has no anchor)_ |
| `mt2_constantan_alloy` | 160.0 | _(module has no anchor)_ |
| `mt2_copper_converter` | 180.0 | _(module has no anchor)_ |
| `mt2_copper_electrowinning` | 220.0 | _(module has no anchor)_ |
| `mt2_copper_reverberatory` | 120.0 | _(module has no anchor)_ |
| `mt2_creep_testing` | 210.0 | _(module has no anchor)_ |
| `mt2_crusher_grinding` | 120.0 | _(module has no anchor)_ |
| `mt2_cyanidation` | 220.0 | _(module has no anchor)_ |
| `mt2_dredging_mining` | 150.0 | _(module has no anchor)_ |
| `mt2_drifting_horizontal` | 110.0 | _(module has no anchor)_ |
| `mt2_ductile_cast_iron` | 200.0 | _(module has no anchor)_ |
| `mt2_duralumin_alloy` | 250.0 | _(module has no anchor)_ |
| `mt2_dye_penetrant_inspection` | 160.0 | _(module has no anchor)_ |
| `mt2_earthenware` | 60.0 | _(module has no anchor)_ |
| `mt2_electrorefining` | 200.0 | _(module has no anchor)_ |
| `mt2_elinvar_alloy` | 220.0 | _(module has no anchor)_ |
| `mt2_german_silver` | 140.0 | _(module has no anchor)_ |
| `mt2_glass_fibre_insulation` | 220.0 | _(module has no anchor)_ |
| `mt2_grain_size_control` | 200.0 | _(module has no anchor)_ |
| `mt2_grey_cast_iron` | 100.0 | _(module has no anchor)_ |
| `mt2_gunmetal_alloy` | 80.0 | _(module has no anchor)_ |
| `mt2_hadfield_manganese_steel` | 210.0 | _(module has no anchor)_ |
| `mt2_high_speed_steel` | 250.0 | _(module has no anchor)_ |
| `mt2_hydraulic_mining` | 120.0 | _(module has no anchor)_ |
| `mt2_induction_furnace` | 250.0 | _(module has no anchor)_ |
| `mt2_induction_hardening` | 250.0 | _(module has no anchor)_ |
| `mt2_invar_nickel_steel` | 200.0 | _(module has no anchor)_ |
| `mt2_izod_impact_test` | 160.0 | _(module has no anchor)_ |
| `mt2_jackhammer_portable` | 130.0 | _(module has no anchor)_ |
| `mt2_laminated_glass_safety` | 180.0 | _(module has no anchor)_ |
| `mt2_leaching_chemical` | 140.0 | _(module has no anchor)_ |
| `mt2_lead_glass_flint` | 180.0 | _(module has no anchor)_ |
| `mt2_magnesite_refractory` | 140.0 | _(module has no anchor)_ |
| `mt2_magnesium_alloys` | 220.0 | _(module has no anchor)_ |
| `mt2_magnesium_extraction` | 250.0 | _(module has no anchor)_ |
| `mt2_magnetic_particle_inspection` | 180.0 | _(module has no anchor)_ |
| `mt2_malleable_cast_iron` | 150.0 | _(module has no anchor)_ |
| `mt2_manganese_extraction` | 180.0 | _(module has no anchor)_ |
| `mt2_manganin_resistance` | 170.0 | _(module has no anchor)_ |
| `mt2_metallography_etching` | 140.0 | _(module has no anchor)_ |
| `mt2_molybdenum_extraction` | 200.0 | _(module has no anchor)_ |
| `mt2_monel_metal` | 180.0 | _(module has no anchor)_ |
| `mt2_nichrome_alloy` | 200.0 | _(module has no anchor)_ |
| `mt2_nickel_extraction` | 200.0 | _(module has no anchor)_ |
| `mt2_nitriding` | 180.0 | _(module has no anchor)_ |
| `mt2_normalising` | 120.0 | _(module has no anchor)_ |
| `mt2_opencast_mining` | 130.0 | _(module has no anchor)_ |
| `mt2_optical_glass_development` | 250.0 | _(module has no anchor)_ |
| `mt2_parkes_process` | 140.0 | _(module has no anchor)_ |
| `mt2_pelletising` | 110.0 | _(module has no anchor)_ |
| `mt2_pewter_alloy` | 100.0 | _(module has no anchor)_ |
| `mt2_platinum_group_metals` | 300.0 | _(module has no anchor)_ |
| `mt2_precipitation_recovery` | 130.0 | _(module has no anchor)_ |
| `mt2_quenching_brine` | 100.0 | _(module has no anchor)_ |
| `mt2_quenching_oil` | 130.0 | _(module has no anchor)_ |
| `mt2_quenching_water` | 100.0 | _(module has no anchor)_ |
| `mt2_radiography_industrial` | 250.0 | _(module has no anchor)_ |
| `mt2_rare_earths_separation` | 400.0 | _(module has no anchor)_ |
| `mt2_recrystallisation` | 140.0 | _(module has no anchor)_ |
| `mt2_rock_drill_pneumatic` | 140.0 | _(module has no anchor)_ |
| `mt2_rockwell_hardness` | 160.0 | _(module has no anchor)_ |
| `mt2_safety_lamp_mining` | 130.0 | _(module has no anchor)_ |
| `mt2_shaft_sinking_mining` | 120.0 | _(module has no anchor)_ |
| `mt2_shot_firer_blasting` | 140.0 | _(module has no anchor)_ |
| `mt2_silica_brick_refractory` | 110.0 | _(module has no anchor)_ |
| `mt2_silicon_steel_transformer` | 200.0 | _(module has no anchor)_ |
| `mt2_sintering_process` | 130.0 | _(module has no anchor)_ |
| `mt2_solder_lead_tin` | 100.0 | _(module has no anchor)_ |
| `mt2_spring_steel` | 160.0 | _(module has no anchor)_ |
| `mt2_stainless_austenitic` | 220.0 | _(module has no anchor)_ |
| `mt2_stainless_ferritic` | 180.0 | _(module has no anchor)_ |
| `mt2_stainless_martensitic` | 200.0 | _(module has no anchor)_ |
| `mt2_stellite_cobalt_alloy` | 220.0 | _(module has no anchor)_ |
| `mt2_stoneware` | 80.0 | _(module has no anchor)_ |
| `mt2_stoping_ore_extraction` | 100.0 | _(module has no anchor)_ |
| `mt2_tempered_glass_safety` | 200.0 | _(module has no anchor)_ |
| `mt2_tempering` | 100.0 | _(module has no anchor)_ |
| `mt2_tensile_test` | 240.0 | _(module has no anchor)_ |
| `mt2_thickener_clarifier` | 110.0 | _(module has no anchor)_ |
| `mt2_timbering_safety` | 80.0 | _(module has no anchor)_ |
| `mt2_titanium_alloys` | 300.0 | _(module has no anchor)_ |
| `mt2_titanium_extraction` | 300.0 | _(module has no anchor)_ |
| `mt2_tungsten_extraction` | 250.0 | _(module has no anchor)_ |
| `mt2_type_metal` | 110.0 | _(module has no anchor)_ |
| `mt2_ultrasonic_testing` | 240.0 | _(module has no anchor)_ |
| `mt2_uranium_thorium_extraction` | 280.0 | _(module has no anchor)_ |
| `mt2_vacuum_melting` | 280.0 | _(module has no anchor)_ |
| `mt2_vanadium_extraction` | 220.0 | _(module has no anchor)_ |
| `mt2_ventilation_mining` | 110.0 | _(module has no anchor)_ |
| `mt2_vickers_hardness` | 170.0 | _(module has no anchor)_ |
| `mt2_white_cast_iron` | 110.0 | _(module has no anchor)_ |
| `mt2_work_hardening` | 130.0 | _(module has no anchor)_ |
| `mt2_xray_diffraction` | 280.0 | _(module has no anchor)_ |
| `mt2_zinc_by_electrolysis` | 200.0 | _(module has no anchor)_ |
| `mt2_zinc_by_retort` | 150.0 | _(module has no anchor)_ |
| `phosphor_bronze_alloy` | 40.0 | [`phosphor_bronze_alloy`](10_metallurgy.md#phosphor_bronze_alloy) **BROKEN** |
| `refractory_fireclay` | 350.0 | [`refractory_fireclay`](10_metallurgy.md#refractory_fireclay---furnace-lining-and-crucible-clay-argilla-refractaria) |
| `zinc_metal` | 700.0 | [`zinc_metal`](10_metallurgy.md#zinc_metal---distilling-metallic-zinc-per-descensum) |

### 20_chemistry.md

| Node | Your hours | Recipe |
|---|---:|---|
| `analytical_chemistry` | 900.0 | [`analytical_chemistry`](20_chemistry.md#analytical_chemistry---analytical-chemistry-and-the-assay-bench) |
| `cap_gas_o2h2` | 450.0 | [`industrial_gases`](20_chemistry.md#industrial_gases---industrial-gases-oxygen-and-hydrogen-without) |
| `ch2_analysis_colorimetry` | 75.0 | _(module has no anchor)_ |
| `ch2_analysis_combustion` | 125.0 | _(module has no anchor)_ |
| `ch2_analysis_complexometric` | 100.0 | _(module has no anchor)_ |
| `ch2_analysis_conductometry` | 85.0 | _(module has no anchor)_ |
| `ch2_analysis_flame_photometry` | 130.0 | _(module has no anchor)_ |
| `ch2_analysis_glass_ph_electrode` | 150.0 | _(module has no anchor)_ |
| `ch2_analysis_gravimetric` | 50.0 | _(module has no anchor)_ |
| `ch2_analysis_indicator_dyes` | 95.0 | _(module has no anchor)_ |
| `ch2_analysis_kjeldahl` | 110.0 | _(module has no anchor)_ |
| `ch2_analysis_melting_point` | 40.0 | _(module has no anchor)_ |
| `ch2_analysis_polarography` | 155.0 | _(module has no anchor)_ |
| `ch2_analysis_redox_titration` | 80.0 | _(module has no anchor)_ |
| `ch2_analysis_refractometry` | 90.0 | _(module has no anchor)_ |
| `ch2_analysis_spectrophotometry` | 140.0 | _(module has no anchor)_ |
| `ch2_analysis_titrimetry` | 60.0 | _(module has no anchor)_ |
| `ch2_lab_azeotropic_distillation` | 85.0 | _(module has no anchor)_ |
| `ch2_lab_centrifugation` | 95.0 | _(module has no anchor)_ |
| `ch2_lab_column_chromatography` | 90.0 | _(module has no anchor)_ |
| `ch2_lab_dialysis` | 45.0 | _(module has no anchor)_ |
| `ch2_lab_electrophoresis` | 110.0 | _(module has no anchor)_ |
| `ch2_lab_fractional_crystallisation` | 70.0 | _(module has no anchor)_ |
| `ch2_lab_freeze_drying` | 140.0 | _(module has no anchor)_ |
| `ch2_lab_gas_chromatography` | 150.0 | _(module has no anchor)_ |
| `ch2_lab_ion_exchange` | 130.0 | _(module has no anchor)_ |
| `ch2_lab_paper_chromatography` | 60.0 | _(module has no anchor)_ |
| `ch2_lab_recrystallisation` | 45.0 | _(module has no anchor)_ |
| `ch2_lab_reflux` | 40.0 | _(module has no anchor)_ |
| `ch2_lab_solvent_extraction` | 45.0 | _(module has no anchor)_ |
| `ch2_lab_soxhlet` | 90.0 | _(module has no anchor)_ |
| `ch2_lab_steam_distillation` | 50.0 | _(module has no anchor)_ |
| `ch2_lab_sublimation` | 60.0 | _(module has no anchor)_ |
| `ch2_lab_vacuum_distillation` | 110.0 | _(module has no anchor)_ |
| `ch2_phys_anodising` | 120.0 | _(module has no anchor)_ |
| `ch2_phys_colligative` | 85.0 | _(module has no anchor)_ |
| `ch2_phys_electrochemical_series` | 85.0 | _(module has no anchor)_ |
| `ch2_phys_equilibrium` | 70.0 | _(module has no anchor)_ |
| `ch2_phys_kinetics` | 100.0 | _(module has no anchor)_ |
| `ch2_phys_le_chatelier` | 65.0 | _(module has no anchor)_ |
| `ch2_phys_mole` | 65.0 | _(module has no anchor)_ |
| `ch2_phys_nernst_equation` | 100.0 | _(module has no anchor)_ |
| `ch2_phys_overpotential` | 110.0 | _(module has no anchor)_ |
| `ch2_phys_phase_rule` | 100.0 | _(module has no anchor)_ |
| `ch2_phys_thermochemistry` | 90.0 | _(module has no anchor)_ |
| `ch2_polymer_bakelite` | 135.0 | _(module has no anchor)_ |
| `ch2_polymer_buna` | 130.0 | _(module has no anchor)_ |
| `ch2_polymer_celluloid` | 110.0 | _(module has no anchor)_ |
| `ch2_polymer_cellulose_acetate` | 120.0 | _(module has no anchor)_ |
| `ch2_polymer_neoprene` | 130.0 | _(module has no anchor)_ |
| `ch2_polymer_nylon` | 140.0 | _(module has no anchor)_ |
| `ch2_polymer_pmma` | 125.0 | _(module has no anchor)_ |
| `ch2_polymer_polyester` | 135.0 | _(module has no anchor)_ |
| `ch2_polymer_polyethylene` | 120.0 | _(module has no anchor)_ |
| `ch2_polymer_polystyrene` | 110.0 | _(module has no anchor)_ |
| `ch2_polymer_pvc` | 200.0 | _(module has no anchor)_ |
| `ch2_polymer_silicone` | 145.0 | _(module has no anchor)_ |
| `ch2_polymer_urea_formaldehyde` | 125.0 | _(module has no anchor)_ |
| `ch2_polymer_viscose` | 130.0 | _(module has no anchor)_ |
| `ch2_process_alkylation` | 115.0 | _(module has no anchor)_ |
| `ch2_process_bayer` | 130.0 | _(module has no anchor)_ |
| `ch2_process_bergius` | 150.0 | _(module has no anchor)_ |
| `ch2_process_birkeland_eyde` | 120.0 | _(module has no anchor)_ |
| `ch2_process_castner_kellner` | 140.0 | _(module has no anchor)_ |
| `ch2_process_catalytic_cracking` | 135.0 | _(module has no anchor)_ |
| `ch2_process_claus` | 125.0 | _(module has no anchor)_ |
| `ch2_process_contact` | 120.0 | _(module has no anchor)_ |
| `ch2_process_cyanamide` | 115.0 | _(module has no anchor)_ |
| `ch2_process_deacon` | 110.0 | _(module has no anchor)_ |
| `ch2_process_fischer_tropsch` | 145.0 | _(module has no anchor)_ |
| `ch2_process_frasch` | 150.0 | _(module has no anchor)_ |
| `ch2_process_kraft_pulping` | 130.0 | _(module has no anchor)_ |
| `ch2_process_ostwald` | 125.0 | _(module has no anchor)_ |
| `ch2_process_reforming` | 140.0 | _(module has no anchor)_ |
| `ch2_process_sulfite_pulping` | 120.0 | _(module has no anchor)_ |
| `ch2_process_thermal_cracking` | 150.0 | _(module has no anchor)_ |
| `ch2_prod_acetic_acid` | 70.0 | _(module has no anchor)_ |
| `ch2_prod_acetone` | 95.0 | _(module has no anchor)_ |
| `ch2_prod_aniline` | 75.0 | _(module has no anchor)_ |
| `ch2_prod_carbon_tetrachloride` | 95.0 | _(module has no anchor)_ |
| `ch2_prod_chloroform` | 85.0 | _(module has no anchor)_ |
| `ch2_prod_citric_acid` | 100.0 | _(module has no anchor)_ |
| `ch2_prod_ether` | 60.0 | _(module has no anchor)_ |
| `ch2_prod_formaldehyde` | 90.0 | _(module has no anchor)_ |
| `ch2_prod_glycerol` | 60.0 | _(module has no anchor)_ |
| `ch2_prod_methanol` | 125.0 | _(module has no anchor)_ |
| `ch2_prod_phenol` | 110.0 | _(module has no anchor)_ |
| `ch2_prod_urea` | 95.0 | _(module has no anchor)_ |
| `ch2_prod_xylene` | 90.0 | _(module has no anchor)_ |
| `ch2_rxn_addition_polymerisation` | 110.0 | _(module has no anchor)_ |
| `ch2_rxn_aldol` | 105.0 | _(module has no anchor)_ |
| `ch2_rxn_bechamp_reduction` | 75.0 | _(module has no anchor)_ |
| `ch2_rxn_catalytic_hydrogenation` | 100.0 | _(module has no anchor)_ |
| `ch2_rxn_condensation_polymerisation` | 120.0 | _(module has no anchor)_ |
| `ch2_rxn_diazotisation` | 120.0 | _(module has no anchor)_ |
| `ch2_rxn_dichromate_oxidation` | 70.0 | _(module has no anchor)_ |
| `ch2_rxn_esterification` | 55.0 | _(module has no anchor)_ |
| `ch2_rxn_friedel_crafts` | 100.0 | _(module has no anchor)_ |
| `ch2_rxn_grignard` | 110.0 | _(module has no anchor)_ |
| `ch2_rxn_halogenation` | 90.0 | _(module has no anchor)_ |
| `ch2_rxn_nitration` | 95.0 | _(module has no anchor)_ |
| `ch2_rxn_permanganate_oxidation` | 65.0 | _(module has no anchor)_ |
| `ch2_rxn_saponification` | 65.0 | _(module has no anchor)_ |
| `ch2_rxn_sulfonation` | 85.0 | _(module has no anchor)_ |
| `ch2_rxn_vulcanisation` | 85.0 | _(module has no anchor)_ |
| `chm_activated_carbon` | 100.0 | _(module has no anchor)_ |
| `chm_alizarin` | 200.0 | _(module has no anchor)_ |
| `chm_alkali_waste` | 150.0 | _(module has no anchor)_ |
| `chm_ammonia_recovery` | 100.0 | _(module has no anchor)_ |
| `chm_aniline` | 180.0 | _(module has no anchor)_ |
| `chm_anthracene` | 100.0 | _(module has no anchor)_ |
| `chm_aspirin` | 60.0 | _(module has no anchor)_ |
| `chm_azo_dyes` | 150.0 | _(module has no anchor)_ |
| `chm_bakelite` | 150.0 | _(module has no anchor)_ |
| `chm_benzene` | 80.0 | _(module has no anchor)_ |
| `chm_black_powder` | 0.0 | _(module has no anchor)_ |
| `chm_blasting_cap` | 100.0 | _(module has no anchor)_ |
| `chm_bleaching_powder` | 80.0 | _(module has no anchor)_ |
| `chm_casein` | 100.0 | _(module has no anchor)_ |
| `chm_catalyst_concept` | 120.0 | _(module has no anchor)_ |
| `chm_caustic_soda` | 100.0 | _(module has no anchor)_ |
| `chm_centrifuge` | 200.0 | _(module has no anchor)_ |
| `chm_chlor_alkali_diaphragm` | 250.0 | _(module has no anchor)_ |
| `chm_chlor_alkali_mercury` | 300.0 | _(module has no anchor)_ |
| `chm_chromatography` | 100.0 | _(module has no anchor)_ |
| `chm_coal_tar_distillation` | 250.0 | _(module has no anchor)_ |
| `chm_contact_sulfuric` | 300.0 | _(module has no anchor)_ |
| `chm_contact_vanadium` | 150.0 | _(module has no anchor)_ |
| `chm_continuous_batch` | 100.0 | _(module has no anchor)_ |
| `chm_corrosion_glass_lined` | 150.0 | _(module has no anchor)_ |
| `chm_corrosion_lead` | 80.0 | _(module has no anchor)_ |
| `chm_corrosion_stainless` | 80.0 | _(module has no anchor)_ |
| `chm_corrosion_stoneware` | 100.0 | _(module has no anchor)_ |
| `chm_crystallisation` | 60.0 | _(module has no anchor)_ |
| `chm_cyanamide_fixation` | 200.0 | _(module has no anchor)_ |
| `chm_deacon_process` | 150.0 | _(module has no anchor)_ |
| `chm_detergent_synthetic` | 150.0 | _(module has no anchor)_ |
| `chm_dynamite` | 100.0 | _(module has no anchor)_ |
| `chm_electric_arc_nitrogen` | 150.0 | _(module has no anchor)_ |
| `chm_evaporator_surface` | 120.0 | _(module has no anchor)_ |
| `chm_filter_press` | 150.0 | _(module has no anchor)_ |
| `chm_formaldehyde_synthesis` | 100.0 | _(module has no anchor)_ |
| `chm_fractionating_column` | 200.0 | _(module has no anchor)_ |
| `chm_fulminate` | 80.0 | _(module has no anchor)_ |
| `chm_gelignite` | 100.0 | _(module has no anchor)_ |
| `chm_glycerol` | 100.0 | _(module has no anchor)_ |
| `chm_guncotton` | 120.0 | _(module has no anchor)_ |
| `chm_haber_bosch` | 400.0 | _(module has no anchor)_ |
| `chm_indigo_synthesis` | 220.0 | _(module has no anchor)_ |
| `chm_industrial_hygiene` | 200.0 | _(module has no anchor)_ |
| `chm_ion_exchange` | 200.0 | _(module has no anchor)_ |
| `chm_matches` | 100.0 | _(module has no anchor)_ |
| `chm_naphthalene` | 100.0 | _(module has no anchor)_ |
| `chm_nylon` | 300.0 | _(module has no anchor)_ |
| `chm_oleum` | 120.0 | _(module has no anchor)_ |
| `chm_ostwald_ammonia_oxidation` | 250.0 | _(module has no anchor)_ |
| `chm_phenol` | 120.0 | _(module has no anchor)_ |
| `chm_phosphorus_extraction` | 120.0 | _(module has no anchor)_ |
| `chm_picric_acid` | 100.0 | _(module has no anchor)_ |
| `chm_polyethylene` | 250.0 | _(module has no anchor)_ |
| `chm_potash_mining` | 150.0 | _(module has no anchor)_ |
| `chm_pressure_gauge` | 100.0 | _(module has no anchor)_ |
| `chm_pressure_vessel` | 200.0 | _(module has no anchor)_ |
| `chm_refrigerant_ammonia` | 100.0 | _(module has no anchor)_ |
| `chm_saccharin` | 120.0 | _(module has no anchor)_ |
| `chm_salicylic_acid` | 100.0 | _(module has no anchor)_ |
| `chm_solvay_process` | 250.0 | _(module has no anchor)_ |
| `chm_sulfonamides` | 150.0 | _(module has no anchor)_ |
| `chm_superphosphate` | 100.0 | _(module has no anchor)_ |
| `chm_tnt` | 150.0 | _(module has no anchor)_ |
| `chm_toluene` | 80.0 | _(module has no anchor)_ |
| `chm_water_chlorination` | 80.0 | _(module has no anchor)_ |
| `chm_water_coagulation` | 60.0 | _(module has no anchor)_ |
| `chm_water_filtration` | 60.0 | _(module has no anchor)_ |
| `chm_weldon_process` | 100.0 | _(module has no anchor)_ |
| `destructive_distillation` | 600.0 | [`destructive_distillation`](20_chemistry.md#destructive_distillation---destructive-distillation-of-wood-and-coal) |
| `distillation_alcohol` | 450.0 | [`distillation_fractional`](20_chemistry.md#distillation_fractional---fractional-distillation-and-the-worm-still) |
| `gunpowder` | 300.0 | [`gunpowder`](20_chemistry.md#gunpowder---gunpowder-pulvis-pyrius-a-later-coinage-no-roman) |
| `hydrochloric_acid` | 300.0 | [`hydrochloric_acid`](20_chemistry.md#hydrochloric_acid---spirit-of-salt-muriatic-acid) |
| `hydrofluoric_acid` | 400.0 | [`hydrofluoric_acid`](20_chemistry.md#hydrofluoric_acid---hydrofluoric-acid-no-established-roman-name) |
| `lab_apparatus` | 600.0 | [`lab_apparatus`](20_chemistry.md#lab_apparatus---laboratory-apparatus-vasa-chymica) |
| `lead_chamber` | 900.0 | [`lead_chamber`](20_chemistry.md#lead_chamber---the-lead-chamber-process) |
| `mat_celluloid` | 150.0 | _(module has no anchor)_ |
| `mat_nitroglycerin` | 150.0 | _(module has no anchor)_ |
| `nitre_beds` | 350.0 | [`saltpetre_nitre_beds`](20_chemistry.md#saltpetre_nitre_beds---saltpetre-nitre-beds-no-roman-name-this) |
| `nitric_acid` | 400.0 | [`nitric_acid`](20_chemistry.md#nitric_acid---nitric-acid-aqua-fortis) |
| `potash_soda` | 200.0 | [`potash_and_soda`](20_chemistry.md#potash_and_soda---potash-and-soda-ash-soda-overlaps-with-roman) |
| `soap_hard` | 250.0 | [`potash_and_soda`](20_chemistry.md#potash_and_soda---potash-and-soda-ash-soda-overlaps-with-roman) |
| `soda_leblanc` | 600.0 | [`potash_and_soda`](20_chemistry.md#potash_and_soda---potash-and-soda-ash-soda-overlaps-with-roman) |
| `sulfuric_retort` | 800.0 | [`sulfuric_acid_retort`](20_chemistry.md#sulfuric_acid_retort---oil-of-vitriol-by-dry-distillation) |

### 30_glass_optics.md

| Node | Your hours | Recipe |
|---|---:|---|
| `balance_analytical` | 700.0 | [`balance_analytical`](30_glass_optics.md#balance_analytical---analytical-balance-milligram-precision) |
| `barometer` | 200.0 | [`thermometer`](30_glass_optics.md#thermometer---sealed-liquid-in-glass-thermometer) |
| `camera_obscura` | 120.0 | [`camera_obscura_photography`](30_glass_optics.md#camera_obscura_photography---camera-obscura-and-silver-halide-photography) |
| `fused_quartz` | 700.0 | [`fused_quartz`](30_glass_optics.md#fused_quartz---fused-silica-pure-quartz-glass) |
| `glass_bead_microscope` | 300.0 | [`glass_bead_microscope`](30_glass_optics.md#glass_bead_microscope---bead-microscope) |
| `glass_borosilicate` | 500.0 | [`glass_borosilicate`](30_glass_optics.md#glass_borosilicate---boron-glass-no-roman-name-propose-vitrum-larderellianum) |
| `glass_clear` | 400.0 | [`glass_clear_cristallo`](30_glass_optics.md#glass_clear_cristallo---clear-glass-vitrum) |
| `glass_labware` | 500.0 | [`glass_lab_ware`](30_glass_optics.md#glass_lab_ware---laboratory-glassware) |
| `in2_adiabatic_demagnetization` | 150.0 | _(module has no anchor)_ |
| `in2_aerial_camera_mount` | 130.0 | _(module has no anchor)_ |
| `in2_alidade_ruler` | 45.0 | _(module has no anchor)_ |
| `in2_antireflection_coating` | 90.0 | _(module has no anchor)_ |
| `in2_artificial_horizon_bubble` | 40.0 | _(module has no anchor)_ |
| `in2_baseline_measurement_apparatus` | 90.0 | _(module has no anchor)_ |
| `in2_beam_splitter` | 70.0 | _(module has no anchor)_ |
| `in2_bolometer_thermal_detector` | 80.0 | _(module has no anchor)_ |
| `in2_cassegrain_reflector` | 100.0 | _(module has no anchor)_ |
| `in2_chain_surveyor` | 30.0 | _(module has no anchor)_ |
| `in2_chronometer_rate_check` | 60.0 | _(module has no anchor)_ |
| `in2_claude_cycle_air_liquefaction` | 130.0 | _(module has no anchor)_ |
| `in2_cloud_chamber_wilson` | 140.0 | _(module has no anchor)_ |
| `in2_condenser_substage` | 45.0 | _(module has no anchor)_ |
| `in2_cooke_triplet_photography` | 100.0 | _(module has no anchor)_ |
| `in2_creep_furnace` | 130.0 | _(module has no anchor)_ |
| `in2_cryostat_dewar_flask` | 90.0 | _(module has no anchor)_ |
| `in2_cyclotron` | 250.0 | _(module has no anchor)_ |
| `in2_dark_field_condenser` | 70.0 | _(module has no anchor)_ |
| `in2_doublet_lens` | 180.0 | _(module has no anchor)_ |
| `in2_echo_sounder_acoustic` | 140.0 | _(module has no anchor)_ |
| `in2_electron_diffraction_camera` | 140.0 | _(module has no anchor)_ |
| `in2_electron_microscope_column` | 200.0 | _(module has no anchor)_ |
| `in2_electron_source_cathode` | 100.0 | _(module has no anchor)_ |
| `in2_electroscope_gold_leaf` | 45.0 | _(module has no anchor)_ |
| `in2_eyepiece_erfle` | 90.0 | _(module has no anchor)_ |
| `in2_eyepiece_huygens` | 40.0 | _(module has no anchor)_ |
| `in2_eyepiece_kellner` | 50.0 | _(module has no anchor)_ |
| `in2_eyepiece_orthoscopic` | 70.0 | _(module has no anchor)_ |
| `in2_eyepiece_ramsden` | 40.0 | _(module has no anchor)_ |
| `in2_fatigue_machine` | 100.0 | _(module has no anchor)_ |
| `in2_geiger_counter` | 110.0 | _(module has no anchor)_ |
| `in2_geodetic_apparatus` | 130.0 | _(module has no anchor)_ |
| `in2_gravimeter_spring_balance` | 100.0 | _(module has no anchor)_ |
| `in2_gyro_horizon_artificial` | 120.0 | _(module has no anchor)_ |
| `in2_gyrocompass` | 160.0 | _(module has no anchor)_ |
| `in2_high_pressure_cell` | 150.0 | _(module has no anchor)_ |
| `in2_immersion_objective_oil` | 80.0 | _(module has no anchor)_ |
| `in2_interference_filter` | 110.0 | _(module has no anchor)_ |
| `in2_interferometer_fabry_perot` | 130.0 | _(module has no anchor)_ |
| `in2_ionisation_chamber` | 85.0 | _(module has no anchor)_ |
| `in2_joule_thomson_valve` | 80.0 | _(module has no anchor)_ |
| `in2_linde_cycle_expansion_engine` | 120.0 | _(module has no anchor)_ |
| `in2_magnetometer_compass` | 75.0 | _(module has no anchor)_ |
| `in2_marine_chronometer` | 250.0 | _(module has no anchor)_ |
| `in2_mass_spectrograph` | 180.0 | _(module has no anchor)_ |
| `in2_microtome_rotary` | 80.0 | _(module has no anchor)_ |
| `in2_microtome_sliding` | 60.0 | _(module has no anchor)_ |
| `in2_newtonian_reflector` | 80.0 | _(module has no anchor)_ |
| `in2_oscilloscope_crt` | 160.0 | _(module has no anchor)_ |
| `in2_petzval_portrait_lens` | 90.0 | _(module has no anchor)_ |
| `in2_ph_meter_potentiometer` | 120.0 | _(module has no anchor)_ |
| `in2_phase_contrast_objective` | 120.0 | _(module has no anchor)_ |
| `in2_photocell_vacuum_photoelectric` | 90.0 | _(module has no anchor)_ |
| `in2_photogrammetry_stereoscope` | 100.0 | _(module has no anchor)_ |
| `in2_photographic_emulsion` | 70.0 | _(module has no anchor)_ |
| `in2_photometer_visual_comparison` | 50.0 | _(module has no anchor)_ |
| `in2_photomultiplier_cascade_amplifier` | 120.0 | _(module has no anchor)_ |
| `in2_plane_table` | 100.0 | _(module has no anchor)_ |
| `in2_polariser_crystal` | 85.0 | _(module has no anchor)_ |
| `in2_precise_levelling_rod` | 80.0 | _(module has no anchor)_ |
| `in2_primary_mirror` | 140.0 | _(module has no anchor)_ |
| `in2_prism_amici` | 80.0 | _(module has no anchor)_ |
| `in2_prism_porro` | 75.0 | _(module has no anchor)_ |
| `in2_radio_direction_finder` | 110.0 | _(module has no anchor)_ |
| `in2_reticle_crosshair` | 30.0 | _(module has no anchor)_ |
| `in2_ruling_engine` | 400.0 | _(module has no anchor)_ |
| `in2_schmidt_corrector_plate` | 120.0 | _(module has no anchor)_ |
| `in2_scintillation_detector` | 120.0 | _(module has no anchor)_ |
| `in2_shock_tube` | 180.0 | _(module has no anchor)_ |
| `in2_simple_lens` | 60.0 | _(module has no anchor)_ |
| `in2_sounding_machine_lead_line` | 35.0 | _(module has no anchor)_ |
| `in2_spectral_radiometer` | 130.0 | _(module has no anchor)_ |
| `in2_spectrograph_grating` | 110.0 | _(module has no anchor)_ |
| `in2_spectrograph_prism` | 85.0 | _(module has no anchor)_ |
| `in2_spirit_level` | 50.0 | _(module has no anchor)_ |
| `in2_strain_gauge_bridge` | 120.0 | _(module has no anchor)_ |
| `in2_strain_gauge_electric` | 80.0 | _(module has no anchor)_ |
| `in2_tacheometer` | 80.0 | _(module has no anchor)_ |
| `in2_tape_measure_steel` | 40.0 | _(module has no anchor)_ |
| `in2_telephoto_design` | 85.0 | _(module has no anchor)_ |
| `in2_tessar_lens` | 110.0 | _(module has no anchor)_ |
| `in2_theodolite` | 200.0 | _(module has no anchor)_ |
| `in2_towing_tank` | 140.0 | _(module has no anchor)_ |
| `in2_triangulation_tripod_station` | 40.0 | _(module has no anchor)_ |
| `in2_triplet_lens` | 180.0 | _(module has no anchor)_ |
| `in2_ultracentrifuge` | 180.0 | _(module has no anchor)_ |
| `in2_ultramicroscope` | 150.0 | _(module has no anchor)_ |
| `in2_van_de_graaff_generator` | 200.0 | _(module has no anchor)_ |
| `in2_vibration_table` | 110.0 | _(module has no anchor)_ |
| `in2_waveplate_mica` | 70.0 | _(module has no anchor)_ |
| `in2_wide_angle_lens` | 130.0 | _(module has no anchor)_ |
| `in2_wind_tunnel_subsonic` | 150.0 | _(module has no anchor)_ |
| `in2_xray_diffraction_camera` | 130.0 | _(module has no anchor)_ |
| `lens_grinding` | 600.0 | [`lens_grinding`](30_glass_optics.md#lens_grinding---grinding-and-polishing-lenses) |
| `microscope_compound` | 600.0 | [`microscope_compound`](30_glass_optics.md#microscope_compound---compound-microscope) |
| `mirror_amalgam` | 350.0 | [`mirrors_amalgam`](30_glass_optics.md#mirrors_amalgam---tin-mercury-amalgam-mirror-later-venetian-mirror) |
| `opt_abbe_condenser` | 120.0 | _(module has no anchor)_ |
| `opt_anemometer` | 60.0 | _(module has no anchor)_ |
| `opt_aneroid_barometer` | 140.0 | _(module has no anchor)_ |
| `opt_apochromat` | 250.0 | _(module has no anchor)_ |
| `opt_ballistic_galvanometer` | 160.0 | _(module has no anchor)_ |
| `opt_bolometer` | 200.0 | _(module has no anchor)_ |
| `opt_bourdon_gauge` | 120.0 | _(module has no anchor)_ |
| `opt_burning_glass` | 0.0 | _(module has no anchor)_ |
| `opt_calorimeter` | 100.0 | _(module has no anchor)_ |
| `opt_chronograph` | 160.0 | _(module has no anchor)_ |
| `opt_clock_drive` | 160.0 | _(module has no anchor)_ |
| `opt_diffraction_grating` | 150.0 | _(module has no anchor)_ |
| `opt_dioptra` | 0.0 | _(module has no anchor)_ |
| `opt_electrometer` | 120.0 | _(module has no anchor)_ |
| `opt_electron_microscope` | 400.0 | _(module has no anchor)_ |
| `opt_equatorial_mount` | 180.0 | _(module has no anchor)_ |
| `opt_flame_spark_spectra` | 80.0 | _(module has no anchor)_ |
| `opt_focal_length_measurement` | 50.0 | _(module has no anchor)_ |
| `opt_fraunhofer_lines` | 200.0 | _(module has no anchor)_ |
| `opt_geared_mechanisms` | 0.0 | _(module has no anchor)_ |
| `opt_gravimeter` | 220.0 | _(module has no anchor)_ |
| `opt_groma` | 0.0 | _(module has no anchor)_ |
| `opt_high_speed_camera` | 280.0 | _(module has no anchor)_ |
| `opt_hygrometer` | 70.0 | _(module has no anchor)_ |
| `opt_level` | 80.0 | _(module has no anchor)_ |
| `opt_magnetometer` | 140.0 | _(module has no anchor)_ |
| `opt_manometer` | 60.0 | _(module has no anchor)_ |
| `opt_metal_mirror_polished` | 0.0 | _(module has no anchor)_ |
| `opt_michelson_interferometer` | 250.0 | _(module has no anchor)_ |
| `opt_newton_rings` | 80.0 | _(module has no anchor)_ |
| `opt_nicol_prism` | 100.0 | _(module has no anchor)_ |
| `opt_oil_immersion_objective` | 130.0 | _(module has no anchor)_ |
| `opt_oscilloscope` | 300.0 | _(module has no anchor)_ |
| `opt_phase_contrast` | 200.0 | _(module has no anchor)_ |
| `opt_photocell` | 180.0 | _(module has no anchor)_ |
| `opt_photometry` | 100.0 | _(module has no anchor)_ |
| `opt_plano_convex_lens` | 40.0 | _(module has no anchor)_ |
| `opt_polarimeter` | 120.0 | _(module has no anchor)_ |
| `opt_pyrometer_contraction` | 80.0 | _(module has no anchor)_ |
| `opt_pyrometer_optical` | 120.0 | _(module has no anchor)_ |
| `opt_pyrometer_radiation` | 180.0 | _(module has no anchor)_ |
| `opt_pyrometer_thermoelectric` | 150.0 | _(module has no anchor)_ |
| `opt_reflecting_telescope` | 200.0 | _(module has no anchor)_ |
| `opt_refractometer` | 140.0 | _(module has no anchor)_ |
| `opt_seismograph` | 200.0 | _(module has no anchor)_ |
| `opt_sextant` | 150.0 | _(module has no anchor)_ |
| `opt_spectroheliograph` | 250.0 | _(module has no anchor)_ |
| `opt_spectroscopy_absorption` | 120.0 | _(module has no anchor)_ |
| `opt_spectroscopy_emission` | 100.0 | _(module has no anchor)_ |
| `opt_speculum_metal` | 150.0 | _(module has no anchor)_ |
| `opt_spherometer` | 80.0 | _(module has no anchor)_ |
| `opt_standards_laboratory` | 500.0 | _(module has no anchor)_ |
| `opt_steelyards` | 0.0 | _(module has no anchor)_ |
| `opt_stellar_parallax` | 150.0 | _(module has no anchor)_ |
| `opt_stroboscope` | 140.0 | _(module has no anchor)_ |
| `opt_sundial` | 0.0 | _(module has no anchor)_ |
| `opt_transit_instrument` | 200.0 | _(module has no anchor)_ |
| `opt_water_clock` | 0.0 | _(module has no anchor)_ |
| `opt_water_globe_magnifier` | 0.0 | _(module has no anchor)_ |
| `photography` | 800.0 | [`camera_obscura_photography`](30_glass_optics.md#camera_obscura_photography---camera-obscura-and-silver-halide-photography) |
| `spectroscope` | 500.0 | [`spectroscope`](30_glass_optics.md#spectroscope---prism-spectroscope) |
| `telescope` | 350.0 | [`telescope`](30_glass_optics.md#telescope---refracting-telescope) |
| `thermometer` | 400.0 | [`thermometer`](30_glass_optics.md#thermometer---sealed-liquid-in-glass-thermometer) |

### 40_power_precision.md

| Node | Your hours | Recipe |
|---|---:|---|
| `boring_mill` | 600.0 | [`boring_mill`](40_power_precision.md#boring_mill---the-cylinder-boring-machine-no-latin-term) |
| `clock_pendulum` | 500.0 | [`clockwork_escapement`](40_power_precision.md#clockwork_escapement---verge-and-foliot-pendulum-and-balance) |
| `crank_conrod` | 300.0 | [`crank_connecting_rod`](40_power_precision.md#crank_connecting_rod---the-crank-and-connecting-rod-no-attested) |
| `en_battery_lead_acid` | 250.0 | _(module has no anchor)_ |
| `en_boiler_cornish` | 250.0 | _(module has no anchor)_ |
| `en_boiler_haystack` | 180.0 | _(module has no anchor)_ |
| `en_boiler_lancashire` | 250.0 | _(module has no anchor)_ |
| `en_boiler_wagon` | 200.0 | _(module has no anchor)_ |
| `en_boiler_water_tube` | 300.0 | _(module has no anchor)_ |
| `en_flywheel_storage` | 200.0 | _(module has no anchor)_ |
| `en_hydroelectric_station` | 400.0 | _(module has no anchor)_ |
| `en_post_mill` | 250.0 | _(module has no anchor)_ |
| `en_pumped_storage` | 400.0 | _(module has no anchor)_ |
| `en_tide_mill` | 200.0 | _(module has no anchor)_ |
| `en_tower_mill` | 300.0 | _(module has no anchor)_ |
| `en_transformer` | 250.0 | _(module has no anchor)_ |
| `interchangeable_parts` | 800.0 | [`interchangeable_parts`](40_power_precision.md#interchangeable_parts---gono-go-gauges-tolerance-jigs-and) |
| `master_screw` | 700.0 | [`screw_cutting_lathe`](40_power_precision.md#screw_cutting_lathe---the-lead-screw-slide-rest-and-change-gears) |
| `mfg_adhesive_bond` | 140.0 | _(module has no anchor)_ |
| `mfg_air_gauge` | 250.0 | _(module has no anchor)_ |
| `mfg_anodising` | 160.0 | _(module has no anchor)_ |
| `mfg_arbor` | 100.0 | _(module has no anchor)_ |
| `mfg_arc_weld_bare` | 160.0 | _(module has no anchor)_ |
| `mfg_arc_weld_coated` | 140.0 | _(module has no anchor)_ |
| `mfg_automatic_screw` | 500.0 | _(module has no anchor)_ |
| `mfg_brazed_tip` | 100.0 | _(module has no anchor)_ |
| `mfg_brazing` | 120.0 | _(module has no anchor)_ |
| `mfg_broaching_machine` | 350.0 | _(module has no anchor)_ |
| `mfg_buffing` | 130.0 | _(module has no anchor)_ |
| `mfg_cam_lobe` | 300.0 | _(module has no anchor)_ |
| `mfg_carbon_steel_tool` | 100.0 | _(module has no anchor)_ |
| `mfg_cemented_carbide` | 200.0 | _(module has no anchor)_ |
| `mfg_centreless_grinder` | 400.0 | _(module has no anchor)_ |
| `mfg_chip_formation` | 120.0 | _(module has no anchor)_ |
| `mfg_cold_riveting` | 100.0 | _(module has no anchor)_ |
| `mfg_collet` | 120.0 | _(module has no anchor)_ |
| `mfg_comparator` | 200.0 | _(module has no anchor)_ |
| `mfg_compound_die` | 250.0 | _(module has no anchor)_ |
| `mfg_control_chart` | 200.0 | _(module has no anchor)_ |
| `mfg_core_box` | 180.0 | _(module has no anchor)_ |
| `mfg_cutting_fluid` | 40.0 | _(module has no anchor)_ |
| `mfg_cutting_speed` | 100.0 | _(module has no anchor)_ |
| `mfg_cylindrical_grinder` | 300.0 | _(module has no anchor)_ |
| `mfg_dial_indicator` | 180.0 | _(module has no anchor)_ |
| `mfg_die_set` | 180.0 | _(module has no anchor)_ |
| `mfg_dividing_engine` | 350.0 | _(module has no anchor)_ |
| `mfg_enamelling` | 120.0 | _(module has no anchor)_ |
| `mfg_engine_lathe` | 300.0 | _(module has no anchor)_ |
| `mfg_escapement_lever` | 240.0 | _(module has no anchor)_ |
| `mfg_flash_butt` | 200.0 | _(module has no anchor)_ |
| `mfg_flux` | 60.0 | _(module has no anchor)_ |
| `mfg_forge_weld` | 100.0 | _(module has no anchor)_ |
| `mfg_forging_press` | 300.0 | _(module has no anchor)_ |
| `mfg_four_jaw_chuck` | 140.0 | _(module has no anchor)_ |
| `mfg_galvanising` | 130.0 | _(module has no anchor)_ |
| `mfg_gear_grinder` | 400.0 | _(module has no anchor)_ |
| `mfg_gear_hobber` | 450.0 | _(module has no anchor)_ |
| `mfg_gear_shaper` | 400.0 | _(module has no anchor)_ |
| `mfg_go_gauge` | 100.0 | _(module has no anchor)_ |
| `mfg_height_gauge` | 160.0 | _(module has no anchor)_ |
| `mfg_honing` | 280.0 | _(module has no anchor)_ |
| `mfg_horizontal_jig_borer` | 350.0 | _(module has no anchor)_ |
| `mfg_horizontal_mill` | 350.0 | _(module has no anchor)_ |
| `mfg_hot_riveting` | 80.0 | _(module has no anchor)_ |
| `mfg_hss_development` | 400.0 | _(module has no anchor)_ |
| `mfg_hss_production` | 80.0 | _(module has no anchor)_ |
| `mfg_indexable_insert` | 150.0 | _(module has no anchor)_ |
| `mfg_indexing_head` | 250.0 | _(module has no anchor)_ |
| `mfg_internal_grinder` | 350.0 | _(module has no anchor)_ |
| `mfg_japanning` | 110.0 | _(module has no anchor)_ |
| `mfg_lapping` | 300.0 | _(module has no anchor)_ |
| `mfg_magnetic_chuck` | 200.0 | _(module has no anchor)_ |
| `mfg_mandrel` | 80.0 | _(module has no anchor)_ |
| `mfg_mould` | 120.0 | _(module has no anchor)_ |
| `mfg_multi_spindle` | 600.0 | _(module has no anchor)_ |
| `mfg_mushet_steel` | 150.0 | _(module has no anchor)_ |
| `mfg_optical_comparator` | 300.0 | _(module has no anchor)_ |
| `mfg_oxy_acetylene` | 180.0 | _(module has no anchor)_ |
| `mfg_painting` | 80.0 | _(module has no anchor)_ |
| `mfg_pattern` | 150.0 | _(module has no anchor)_ |
| `mfg_phosphating` | 100.0 | _(module has no anchor)_ |
| `mfg_pickling` | 100.0 | _(module has no anchor)_ |
| `mfg_planer` | 350.0 | _(module has no anchor)_ |
| `mfg_plug_gauge` | 120.0 | _(module has no anchor)_ |
| `mfg_press_brake` | 280.0 | _(module has no anchor)_ |
| `mfg_profile_mill` | 450.0 | _(module has no anchor)_ |
| `mfg_progressive_die` | 280.0 | _(module has no anchor)_ |
| `mfg_punch_press` | 300.0 | _(module has no anchor)_ |
| `mfg_radial_drill` | 300.0 | _(module has no anchor)_ |
| `mfg_rake_clearance` | 80.0 | _(module has no anchor)_ |
| `mfg_resistance_seam` | 220.0 | _(module has no anchor)_ |
| `mfg_resistance_spot` | 200.0 | _(module has no anchor)_ |
| `mfg_ring_gauge` | 120.0 | _(module has no anchor)_ |
| `mfg_roll_former` | 350.0 | _(module has no anchor)_ |
| `mfg_rotary_table` | 220.0 | _(module has no anchor)_ |
| `mfg_sampling_plan` | 180.0 | _(module has no anchor)_ |
| `mfg_sand_blasting` | 100.0 | _(module has no anchor)_ |
| `mfg_sawing_machine` | 250.0 | _(module has no anchor)_ |
| `mfg_shaper` | 300.0 | _(module has no anchor)_ |
| `mfg_shearing_machine` | 280.0 | _(module has no anchor)_ |
| `mfg_shot_blasting` | 120.0 | _(module has no anchor)_ |
| `mfg_silver_solder` | 100.0 | _(module has no anchor)_ |
| `mfg_sine_bar` | 150.0 | _(module has no anchor)_ |
| `mfg_slotter` | 250.0 | _(module has no anchor)_ |
| `mfg_snap_gauge` | 110.0 | _(module has no anchor)_ |
| `mfg_soft_solder` | 80.0 | _(module has no anchor)_ |
| `mfg_spinning_lathe` | 250.0 | _(module has no anchor)_ |
| `mfg_stellite_tool` | 120.0 | _(module has no anchor)_ |
| `mfg_submerged_arc` | 250.0 | _(module has no anchor)_ |
| `mfg_superfinishing` | 350.0 | _(module has no anchor)_ |
| `mfg_thread_gauge` | 140.0 | _(module has no anchor)_ |
| `mfg_three_jaw_chuck` | 150.0 | _(module has no anchor)_ |
| `mfg_tolerance_limit` | 140.0 | _(module has no anchor)_ |
| `mfg_tool_grinder` | 300.0 | _(module has no anchor)_ |
| `mfg_tumbling` | 110.0 | _(module has no anchor)_ |
| `mfg_turret_lathe` | 400.0 | _(module has no anchor)_ |
| `mfg_universal_mill` | 400.0 | _(module has no anchor)_ |
| `mfg_upsetter` | 400.0 | _(module has no anchor)_ |
| `mfg_vertical_jig_borer` | 400.0 | _(module has no anchor)_ |
| `mfg_vertical_mill` | 350.0 | _(module has no anchor)_ |
| `mfg_wire_drawing` | 280.0 | _(module has no anchor)_ |
| `micrometer_gauges` | 500.0 | [`micrometer_gauge_blocks`](40_power_precision.md#micrometer_gauge_blocks---screw-micrometer-vernier-scale-and-end) |
| `prc_arbor_press` | 40.0 | _(module has no anchor)_ |
| `prc_autocollimator` | 110.0 | _(module has no anchor)_ |
| `prc_automatic_screw_machine` | 200.0 | _(module has no anchor)_ |
| `prc_back_gear` | 60.0 | _(module has no anchor)_ |
| `prc_ball_roller_bearing` | 140.0 | _(module has no anchor)_ |
| `prc_ballscrew` | 130.0 | _(module has no anchor)_ |
| `prc_broach_machine` | 110.0 | _(module has no anchor)_ |
| `prc_capstan_turret_lathe` | 150.0 | _(module has no anchor)_ |
| `prc_change_gears_quadrant` | 80.0 | _(module has no anchor)_ |
| `prc_comparator_optical` | 100.0 | _(module has no anchor)_ |
| `prc_compound_slide_rest` | 120.0 | _(module has no anchor)_ |
| `prc_coolant_cutting_fluid` | 50.0 | _(module has no anchor)_ |
| `prc_cylindrical_square` | 60.0 | _(module has no anchor)_ |
| `prc_depth_gauge` | 40.0 | _(module has no anchor)_ |
| `prc_die_sinker` | 110.0 | _(module has no anchor)_ |
| `prc_dividing_head` | 100.0 | _(module has no anchor)_ |
| `prc_drill_press` | 70.0 | _(module has no anchor)_ |
| `prc_fly_cutter` | 50.0 | _(module has no anchor)_ |
| `prc_gauge_blocks_johansson` | 120.0 | _(module has no anchor)_ |
| `prc_go_nogo_gauge` | 60.0 | _(module has no anchor)_ |
| `prc_honing_machine` | 100.0 | _(module has no anchor)_ |
| `prc_jig_and_fixture` | 120.0 | _(module has no anchor)_ |
| `prc_jig_boring_machine` | 150.0 | _(module has no anchor)_ |
| `prc_lapping_plate` | 60.0 | _(module has no anchor)_ |
| `prc_lathe_faceplate` | 40.0 | _(module has no anchor)_ |
| `prc_lead_screw_error_cam` | 100.0 | _(module has no anchor)_ |
| `prc_machine_frame_cast_iron` | 120.0 | _(module has no anchor)_ |
| `prc_mandrel_chuck` | 60.0 | _(module has no anchor)_ |
| `prc_metrology_room_20c` | 200.0 | _(module has no anchor)_ |
| `prc_milling_machine` | 160.0 | _(module has no anchor)_ |
| `prc_optical_flat` | 100.0 | _(module has no anchor)_ |
| `prc_pantograph_copying` | 80.0 | _(module has no anchor)_ |
| `prc_planer_machine` | 140.0 | _(module has no anchor)_ |
| `prc_profile_projector` | 110.0 | _(module has no anchor)_ |
| `prc_reamer_hand_flute` | 40.0 | _(module has no anchor)_ |
| `prc_roundness_measurement` | 100.0 | _(module has no anchor)_ |
| `prc_scraped_surface_plate` | 200.0 | _(module has no anchor)_ |
| `prc_shaper_machine` | 100.0 | _(module has no anchor)_ |
| `prc_slide_rest_simple` | 100.0 | _(module has no anchor)_ |
| `prc_slotter_machine` | 70.0 | _(module has no anchor)_ |
| `prc_square_reference` | 50.0 | _(module has no anchor)_ |
| `prc_standard_meter_wavelength` | 150.0 | _(module has no anchor)_ |
| `prc_straightedge` | 30.0 | _(module has no anchor)_ |
| `prc_surface_grinder` | 300.0 | _(module has no anchor)_ |
| `prc_tailstock_deadcentre` | 50.0 | _(module has no anchor)_ |
| `prc_tap_die` | 80.0 | _(module has no anchor)_ |
| `prc_three_wire_thread_measure` | 70.0 | _(module has no anchor)_ |
| `prc_tool_cutter_grinder` | 120.0 | _(module has no anchor)_ |
| `prc_tool_steel_hss_carbide` | 100.0 | _(module has no anchor)_ |
| `prc_toolmaker_microscope` | 130.0 | _(module has no anchor)_ |
| `prc_tracer_lathe` | 140.0 | _(module has no anchor)_ |
| `prc_treadle_lathe_flywheel` | 80.0 | _(module has no anchor)_ |
| `prc_twist_drill` | 50.0 | _(module has no anchor)_ |
| `prc_universal_milling_machine` | 180.0 | _(module has no anchor)_ |
| `prc_vernier_caliper` | 60.0 | _(module has no anchor)_ |
| `prc_vibration_and_chatter` | 100.0 | _(module has no anchor)_ |
| `precision_three_plate` | 500.0 | [`precision_three_plate`](40_power_precision.md#precision_three_plate---whitworths-three-plate-method-no-latin) |
| `pwr_animal_treadmill` | 0.0 | _(module has no anchor)_ |
| `pwr_cable_tool_drilling` | 300.0 | _(module has no anchor)_ |
| `pwr_coal_gas` | 300.0 | _(module has no anchor)_ |
| `pwr_coal_seam` | 150.0 | _(module has no anchor)_ |
| `pwr_coking` | 200.0 | _(module has no anchor)_ |
| `pwr_condenser` | 200.0 | _(module has no anchor)_ |
| `pwr_electric_motor_industry` | 300.0 | _(module has no anchor)_ |
| `pwr_feedwater_heating` | 200.0 | _(module has no anchor)_ |
| `pwr_flywheel_governor` | 150.0 | _(module has no anchor)_ |
| `pwr_force_pump` | 0.0 | _(module has no anchor)_ |
| `pwr_fuel_cell` | 300.0 | _(module has no anchor)_ |
| `pwr_fuel_oil` | 150.0 | _(module has no anchor)_ |
| `pwr_gas_main` | 250.0 | _(module has no anchor)_ |
| `pwr_gas_meter` | 180.0 | _(module has no anchor)_ |
| `pwr_high_voltage_transmission` | 300.0 | _(module has no anchor)_ |
| `pwr_indicator_diagram` | 200.0 | _(module has no anchor)_ |
| `pwr_leat_and_weir` | 200.0 | _(module has no anchor)_ |
| `pwr_load_factor_economics` | 200.0 | _(module has no anchor)_ |
| `pwr_millpond` | 150.0 | _(module has no anchor)_ |
| `pwr_norse_waterwheel` | 120.0 | _(module has no anchor)_ |
| `pwr_nuclear_fission` | 500.0 | _(module has no anchor)_ |
| `pwr_oil_refinery` | 300.0 | _(module has no anchor)_ |
| `pwr_oil_shale` | 80.0 | _(module has no anchor)_ |
| `pwr_peat` | 100.0 | _(module has no anchor)_ |
| `pwr_petroleum_seeps` | 100.0 | _(module has no anchor)_ |
| `pwr_pipeline` | 250.0 | _(module has no anchor)_ |
| `pwr_rotary_drilling` | 350.0 | _(module has no anchor)_ |
| `pwr_screw_press_power` | 0.0 | _(module has no anchor)_ |
| `pwr_selenium_cell` | 150.0 | _(module has no anchor)_ |
| `pwr_selenium_metal` | 200.0 | _(module has no anchor)_ |
| `pwr_selenium_photovoltaic` | 200.0 | _(module has no anchor)_ |
| `pwr_ship_sail` | 0.0 | _(module has no anchor)_ |
| `pwr_smeaton_efficiency` | 200.0 | _(module has no anchor)_ |
| `pwr_thermoelectric_couple` | 200.0 | _(module has no anchor)_ |
| `pwr_thermopile` | 150.0 | _(module has no anchor)_ |
| `pwr_three_phase_ac` | 250.0 | _(module has no anchor)_ |
| `pwr_trompe` | 180.0 | _(module has no anchor)_ |
| `pwr_water_turbine_fourneyron` | 300.0 | _(module has no anchor)_ |
| `screw_lathe` | 900.0 | [`screw_cutting_lathe`](40_power_precision.md#screw_cutting_lathe---the-lead-screw-slide-rest-and-change-gears) |
| `steam_atmospheric` | 900.0 | [`steam_atmospheric`](40_power_precision.md#steam_atmospheric---the-newcomen-atmospheric-engine-no-latin-term) |
| `steam_high_pressure` | 700.0 | [`steam_high_pressure`](40_power_precision.md#steam_high_pressure---high-pressure-non-condensing-steam-no-latin) |
| `steam_watt` | 800.0 | [`steam_watt`](40_power_precision.md#steam_watt---watts-separate-condenser-no-latin-term) |
| `units_standards` | 300.0 | [`micrometer_gauge_blocks`](40_power_precision.md#micrometer_gauge_blocks---screw-micrometer-vernier-scale-and-end) |
| `water_power_scale` | 450.0 | [`water_power_scaleup`](40_power_precision.md#water_power_scaleup---scaling-up-the-water-wheel-rota-aquaria) |

### 50_electricity.md

| Node | Your hours | Recipe |
|---|---:|---|
| `arc_light_lamp` | 500.0 | [`incandescent_lamp`](50_electricity.md#incandescent_lamp---filament-lamp-carbon-then-tungsten) |
| `com_accumulator` | 130.0 | _(module has no anchor)_ |
| `com_analytical_engine` | 250.0 | _(module has no anchor)_ |
| `com_antenna_ground` | 60.0 | _(module has no anchor)_ |
| `com_arithmometer` | 120.0 | _(module has no anchor)_ |
| `com_baudot_code` | 60.0 | _(module has no anchor)_ |
| `com_binary_arithmetic` | 100.0 | _(module has no anchor)_ |
| `com_boolean_algebra` | 120.0 | _(module has no anchor)_ |
| `com_broadcasting_institution` | 200.0 | _(module has no anchor)_ |
| `com_compiler_and_language` | 300.0 | _(module has no anchor)_ |
| `com_continuous_wave` | 120.0 | _(module has no anchor)_ |
| `com_cryptography_substitution` | 80.0 | _(module has no anchor)_ |
| `com_crystal_set` | 80.0 | _(module has no anchor)_ |
| `com_difference_engine` | 200.0 | _(module has no anchor)_ |
| `com_duplex_telegraph` | 120.0 | _(module has no anchor)_ |
| `com_error_detecting_code` | 140.0 | _(module has no anchor)_ |
| `com_flip_flop` | 100.0 | _(module has no anchor)_ |
| `com_heliograph` | 80.0 | _(module has no anchor)_ |
| `com_hollerith_tabulation` | 180.0 | _(module has no anchor)_ |
| `com_information_theory` | 160.0 | _(module has no anchor)_ |
| `com_integrated_circuit` | 220.0 | _(module has no anchor)_ |
| `com_jacquard_loom` | 250.0 | _(module has no anchor)_ |
| `com_loading_coil` | 120.0 | _(module has no anchor)_ |
| `com_logic_gate` | 100.0 | _(module has no anchor)_ |
| `com_magnetic_core_memory` | 140.0 | _(module has no anchor)_ |
| `com_magnetic_drum_storage` | 110.0 | _(module has no anchor)_ |
| `com_magnetic_tape_storage` | 120.0 | _(module has no anchor)_ |
| `com_magnetic_wire_storage` | 100.0 | _(module has no anchor)_ |
| `com_mechanical_calculator` | 150.0 | _(module has no anchor)_ |
| `com_morse_code` | 60.0 | _(module has no anchor)_ |
| `com_morse_register` | 100.0 | _(module has no anchor)_ |
| `com_morse_sounder` | 80.0 | _(module has no anchor)_ |
| `com_multiplexing` | 120.0 | _(module has no anchor)_ |
| `com_napiers_bones` | 100.0 | _(module has no anchor)_ |
| `com_one_time_pad` | 100.0 | _(module has no anchor)_ |
| `com_optical_codebook` | 100.0 | _(module has no anchor)_ |
| `com_optical_tower` | 120.0 | _(module has no anchor)_ |
| `com_photolithography` | 180.0 | _(module has no anchor)_ |
| `com_public_key_cryptography` | 200.0 | _(module has no anchor)_ |
| `com_quadruplex_telegraph` | 140.0 | _(module has no anchor)_ |
| `com_radar_magnetron` | 160.0 | _(module has no anchor)_ |
| `com_radio_spark_transmitter` | 120.0 | _(module has no anchor)_ |
| `com_register_computing` | 120.0 | _(module has no anchor)_ |
| `com_relay` | 100.0 | _(module has no anchor)_ |
| `com_relay_computer` | 300.0 | _(module has no anchor)_ |
| `com_ring_counter` | 110.0 | _(module has no anchor)_ |
| `com_rotor_machine` | 160.0 | _(module has no anchor)_ |
| `com_semiconductor_diode` | 100.0 | _(module has no anchor)_ |
| `com_signal_flags` | 40.0 | _(module has no anchor)_ |
| `com_stepped_drum` | 80.0 | _(module has no anchor)_ |
| `com_stock_ticker` | 100.0 | _(module has no anchor)_ |
| `com_stored_program_concept` | 180.0 | _(module has no anchor)_ |
| `com_submarine_cable` | 200.0 | _(module has no anchor)_ |
| `com_telegraph_battery` | 60.0 | _(module has no anchor)_ |
| `com_telephone_carbon_mic` | 100.0 | _(module has no anchor)_ |
| `com_telephone_diaphragm` | 80.0 | _(module has no anchor)_ |
| `com_telephone_manual_exchange` | 150.0 | _(module has no anchor)_ |
| `com_teleprinter` | 140.0 | _(module has no anchor)_ |
| `com_trunk_lines` | 100.0 | _(module has no anchor)_ |
| `com_tv_electronic_camera` | 160.0 | _(module has no anchor)_ |
| `com_tv_mechanical_scanning` | 140.0 | _(module has no anchor)_ |
| `com_tv_raster_sync` | 120.0 | _(module has no anchor)_ |
| `com_vacuum_tube_computer` | 400.0 | _(module has no anchor)_ |
| `com_vacuum_tube_pentode` | 110.0 | _(module has no anchor)_ |
| `com_vacuum_tube_tetrode` | 100.0 | _(module has no anchor)_ |
| `com_waveguide` | 80.0 | _(module has no anchor)_ |
| `copper_refining` | 400.0 | [`wire_insulation`](50_electricity.md#wire_insulation---insulated-wire-varnish-and-cable) |
| `crude_cell` | 120.0 | [`crude_cell`](50_electricity.md#crude_cell---iron-and-copper-brine-cell) |
| `daniell_cell` | 250.0 | [`daniell_cell`](50_electricity.md#daniell_cell---two-fluid-cell-daniell-no-latin-name) |
| `dynamo` | 800.0 | [`dynamo_motor`](50_electricity.md#dynamo_motor---faraday-disc-ring-and-drum-armatures-self-excitation) |
| `el2_alternator_rotating_field` | 120.0 | _(module has no anchor)_ |
| `el2_amplifier_gain_voltage_current` | 80.0 | _(module has no anchor)_ |
| `el2_antenna_patterns_radiation_efficiency` | 110.0 | _(module has no anchor)_ |
| `el2_arc_welding_carbon_metal_electrode` | 120.0 | _(module has no anchor)_ |
| `el2_bandpass_filter_notch_filter` | 70.0 | _(module has no anchor)_ |
| `el2_beam_tetrode_output_tube` | 130.0 | _(module has no anchor)_ |
| `el2_bridge_resistance_AC_impedance` | 120.0 | _(module has no anchor)_ |
| `el2_capacitor_electrolytic` | 120.0 | _(module has no anchor)_ |
| `el2_capacitor_fixed_mica` | 50.0 | _(module has no anchor)_ |
| `el2_capacitor_fixed_paper` | 60.0 | _(module has no anchor)_ |
| `el2_capacitor_variable_air` | 70.0 | _(module has no anchor)_ |
| `el2_cathode_ray_tube_oscilloscope` | 150.0 | _(module has no anchor)_ |
| `el2_circuit_breaker_magnetic` | 70.0 | _(module has no anchor)_ |
| `el2_circuit_breaker_thermal` | 60.0 | _(module has no anchor)_ |
| `el2_contactor_industrial` | 80.0 | _(module has no anchor)_ |
| `el2_counter_frequency_scaling_binary` | 100.0 | _(module has no anchor)_ |
| `el2_detector_demodulation_envelope_product` | 75.0 | _(module has no anchor)_ |
| `el2_dielectric_heating_capacitor_coupling` | 120.0 | _(module has no anchor)_ |
| `el2_diode_thermionic_rectifying_tube` | 70.0 | _(module has no anchor)_ |
| `el2_discriminator_FM_demodulator` | 100.0 | _(module has no anchor)_ |
| `el2_dynamo_compound_wound` | 100.0 | _(module has no anchor)_ |
| `el2_dynamo_series_wound` | 75.0 | _(module has no anchor)_ |
| `el2_dynamo_shunt_wound` | 80.0 | _(module has no anchor)_ |
| `el2_earthing_grounding_system` | 80.0 | _(module has no anchor)_ |
| `el2_electric_drill_handheld_motor` | 100.0 | _(module has no anchor)_ |
| `el2_electric_lift_motor_gear_reduction` | 130.0 | _(module has no anchor)_ |
| `el2_electric_locomotive_traction_motor` | 150.0 | _(module has no anchor)_ |
| `el2_electron_microscope_electromagnetic_lens` | 200.0 | _(module has no anchor)_ |
| `el2_electroplating_and_electrorefining` | 80.0 | _(module has no anchor)_ |
| `el2_electropolishing_etching_surface_finish` | 100.0 | _(module has no anchor)_ |
| `el2_electrostatic_precipitation_dust_collection` | 130.0 | _(module has no anchor)_ |
| `el2_flip_flop_binary_latch_memory` | 120.0 | _(module has no anchor)_ |
| `el2_galvanometer_ballistic_impulse` | 110.0 | _(module has no anchor)_ |
| `el2_impedance_matching_transformer_network` | 70.0 | _(module has no anchor)_ |
| `el2_induction_heating_inductor_coupling` | 100.0 | _(module has no anchor)_ |
| `el2_induction_motor_squirrel_cage` | 100.0 | _(module has no anchor)_ |
| `el2_induction_motor_wound_rotor` | 120.0 | _(module has no anchor)_ |
| `el2_inductor_air_core` | 30.0 | _(module has no anchor)_ |
| `el2_inductor_ferrite_core` | 80.0 | _(module has no anchor)_ |
| `el2_inductor_iron_core` | 60.0 | _(module has no anchor)_ |
| `el2_insulator_bushing` | 60.0 | _(module has no anchor)_ |
| `el2_insulator_pin_porcelain` | 40.0 | _(module has no anchor)_ |
| `el2_klystron_microwave_amplifier` | 150.0 | _(module has no anchor)_ |
| `el2_lightning_arrestor_gap` | 50.0 | _(module has no anchor)_ |
| `el2_load_dispatch_and_scheduling` | 150.0 | _(module has no anchor)_ |
| `el2_loudspeaker_moving_coil_magnetic` | 110.0 | _(module has no anchor)_ |
| `el2_low_pass_filter_high_pass_filter` | 50.0 | _(module has no anchor)_ |
| `el2_magnetron_microwave_oscillator` | 160.0 | _(module has no anchor)_ |
| `el2_megger_resistance_tester` | 90.0 | _(module has no anchor)_ |
| `el2_meter_electrodynamometer_wattmeter` | 100.0 | _(module has no anchor)_ |
| `el2_meter_energy_kWh_meter` | 110.0 | _(module has no anchor)_ |
| `el2_meter_moving_coil_galvanometer` | 70.0 | _(module has no anchor)_ |
| `el2_meter_moving_iron_attraction` | 60.0 | _(module has no anchor)_ |
| `el2_microphone_carbon_contact` | 70.0 | _(module has no anchor)_ |
| `el2_microphone_condenser_electrostatic` | 130.0 | _(module has no anchor)_ |
| `el2_microphone_dynamic_moving_coil` | 100.0 | _(module has no anchor)_ |
| `el2_microphone_ribbon_velocity` | 110.0 | _(module has no anchor)_ |
| `el2_mixer_frequency_translation` | 80.0 | _(module has no anchor)_ |
| `el2_modulator_amplitude_frequency_phase` | 90.0 | _(module has no anchor)_ |
| `el2_multivibrator_binary_oscillator` | 110.0 | _(module has no anchor)_ |
| `el2_negative_feedback_stability_gain` | 100.0 | _(module has no anchor)_ |
| `el2_oscillator_feedback_frequency_generation` | 90.0 | _(module has no anchor)_ |
| `el2_oscillograph_string_recorder` | 130.0 | _(module has no anchor)_ |
| `el2_pentode_five_electrode_tube` | 120.0 | _(module has no anchor)_ |
| `el2_photocell_vacuum_gas_photoelectric` | 100.0 | _(module has no anchor)_ |
| `el2_photodiode_photocell_selenium` | 80.0 | _(module has no anchor)_ |
| `el2_photomultiplier_single_photon` | 140.0 | _(module has no anchor)_ |
| `el2_plug_socket_portable` | 70.0 | _(module has no anchor)_ |
| `el2_potentiometer` | 180.0 | _(module has no anchor)_ |
| `el2_potentiometer_method_measurement` | 100.0 | _(module has no anchor)_ |
| `el2_power_factor_correction_capacitor` | 100.0 | _(module has no anchor)_ |
| `el2_power_supply_rectification_filtering` | 80.0 | _(module has no anchor)_ |
| `el2_printed_circuit_board` | 100.0 | _(module has no anchor)_ |
| `el2_protective_relaying_differential` | 110.0 | _(module has no anchor)_ |
| `el2_quartz_crystal` | 100.0 | _(module has no anchor)_ |
| `el2_radar_pulse_modulation_detection` | 200.0 | _(module has no anchor)_ |
| `el2_rectifier_mercury_arc` | 100.0 | _(module has no anchor)_ |
| `el2_rectifier_metal_layer` | 80.0 | _(module has no anchor)_ |
| `el2_relay_electromagnetic` | 50.0 | _(module has no anchor)_ |
| `el2_resistance_welding_spot_seam` | 110.0 | _(module has no anchor)_ |
| `el2_resistor_carbon` | 60.0 | _(module has no anchor)_ |
| `el2_resistor_wirewound` | 40.0 | _(module has no anchor)_ |
| `el2_resonance_frequency_selectivity` | 70.0 | _(module has no anchor)_ |
| `el2_rheostat` | 80.0 | _(module has no anchor)_ |
| `el2_ring_main_distribution` | 130.0 | _(module has no anchor)_ |
| `el2_servo_motor_feedback` | 120.0 | _(module has no anchor)_ |
| `el2_sonar_acoustic_detection_ranging` | 180.0 | _(module has no anchor)_ |
| `el2_standard_cell_weston_saturated` | 100.0 | _(module has no anchor)_ |
| `el2_standard_resistor_manganin` | 80.0 | _(module has no anchor)_ |
| `el2_standardised_frequency_nominal` | 180.0 | _(module has no anchor)_ |
| `el2_standardised_voltage_nominal` | 200.0 | _(module has no anchor)_ |
| `el2_stepper_motor_PM` | 100.0 | _(module has no anchor)_ |
| `el2_substation_voltage_regulation` | 140.0 | _(module has no anchor)_ |
| `el2_switch_knife` | 20.0 | _(module has no anchor)_ |
| `el2_synchronous_motor` | 110.0 | _(module has no anchor)_ |
| `el2_synchroscope_phase_angle_indicator` | 80.0 | _(module has no anchor)_ |
| `el2_tap_changer_load_compensator` | 100.0 | _(module has no anchor)_ |
| `el2_telephone_exchange_switching_network` | 200.0 | _(module has no anchor)_ |
| `el2_tetrode_four_electrode_tube` | 110.0 | _(module has no anchor)_ |
| `el2_thermistor_thermally_sensitive_resistor` | 100.0 | _(module has no anchor)_ |
| `el2_three_wire_distribution_system` | 120.0 | _(module has no anchor)_ |
| `el2_thyratron_gas_filled_switching_tube` | 100.0 | _(module has no anchor)_ |
| `el2_transformer_core_air` | 40.0 | _(module has no anchor)_ |
| `el2_transmission_line_coaxial_cable` | 100.0 | _(module has no anchor)_ |
| `el2_travelling_wave_tube_linear_amplifier` | 170.0 | _(module has no anchor)_ |
| `el2_triode_amplifying_tube` | 100.0 | _(module has no anchor)_ |
| `el2_trolleybus_catenary_power` | 120.0 | _(module has no anchor)_ |
| `el2_tuned_circuit_resonance_tank` | 100.0 | _(module has no anchor)_ |
| `el2_universal_motor_AC_DC` | 90.0 | _(module has no anchor)_ |
| `el2_valve_voltmeter_high_impedance` | 120.0 | _(module has no anchor)_ |
| `el2_varistor_voltage_dependent_resistor` | 90.0 | _(module has no anchor)_ |
| `el2_voltage_regulation_series_shunt` | 100.0 | _(module has no anchor)_ |
| `el2_waveguide_rectangular_propagation` | 130.0 | _(module has no anchor)_ |
| `el2_xray_tube_high_voltage_cathode_rays` | 150.0 | _(module has no anchor)_ |
| `electrolysis_industrial` | 700.0 | [`electrolysis_industrial`](50_electricity.md#electrolysis_industrial---electroplating-electro-refining-chlor-alkali-aluminium) |
| `electromagnet` | 350.0 | [`electromagnet`](50_electricity.md#electromagnet---iron-core-electromagnet-and-relay) |
| `electroplating` | 350.0 | [`electrolysis_industrial`](50_electricity.md#electrolysis_industrial---electroplating-electro-refining-chlor-alkali-aluminium) |
| `electrostatics` | 350.0 | [`electrostatics`](50_electricity.md#electrostatics---static-machines-and-the-leyden-jar-electrum-vis-electrica) |
| `em_theory` | 800.0 | _(module has no anchor)_ |
| `galvanometer` | 400.0 | [`galvanometer`](50_electricity.md#galvanometer---tangent-galvanometer-and-the-absolute-measurement-bootstrap) |
| `motor_transformer_ac` | 700.0 | [`transformer_ac`](50_electricity.md#transformer_ac---ac-generation-transformers-lamination-three-phase) |
| `power_grid` | 900.0 | [`transformer_ac`](50_electricity.md#transformer_ac---ac-generation-transformers-lamination-three-phase) |
| `telegraph_electric` | 700.0 | [`telegraph`](50_electricity.md#telegraph---electric-line-telegraph) |
| `voltaic_pile` | 300.0 | [`voltaic_pile`](50_electricity.md#voltaic_pile---zinc-and-copper-disc-pile) |

### 55_semiconductors.md

| Node | Your hours | Recipe |
|---|---:|---|
| `diffusion_pump` | 600.0 | [`vacuum_pumps`](55_semiconductors.md#vacuum_pumps---pumps-and-gauges-for-empty-space-antlia-pneumatica) |
| `discharge_xray` | 700.0 | [`crookes_xray_electron`](55_semiconductors.md#crookes_xray_electron---discharge-tubes-x-rays-and-the-electron-tubus-vacuus-electricus) |
| `galena_detector` | 150.0 | [`galena_detector`](55_semiconductors.md#galena_detector---the-cats-whisker-rectifier-plumbago-fulminans-informal) |
| `ge_reduction` | 600.0 | [`germanium_sourcing`](55_semiconductors.md#germanium_sourcing---finding-germanium-at-all-plumbum-cinereum-informal) |
| `gecl4_purification` | 900.0 | [`germanium_sourcing`](55_semiconductors.md#germanium_sourcing---finding-germanium-at-all-plumbum-cinereum-informal) |
| `germanium_extraction` | 900.0 | [`germanium_sourcing`](55_semiconductors.md#germanium_sourcing---finding-germanium-at-all-plumbum-cinereum-informal) |
| `junction_transistor` | 800.0 | [`junction_transistor`](55_semiconductors.md#junction_transistor---grown-and-alloy-junctions-iunctio-amplificans-informal) |
| `point_contact_transistor` | 900.0 | [`point_contact_transistor`](55_semiconductors.md#point_contact_transistor---the-first-transistor-punctum-amplificans-informal) |
| `quantum_solidstate_theory` | 1,800.0 | [`semiconductor_theory`](55_semiconductors.md#semiconductor_theory---what-to-write-down-before-you-can-test-any-of-it-doctrina-de-semiconductoribus) |
| `radio` | 700.0 | [`radio_spark_to_valve`](55_semiconductors.md#radio_spark_to_valve---from-spark-transmitter-to-the-crystal-set-and-the-valve-radio-telegraphia-sine-filo) |
| `semiconductor_metrology` | 800.0 | [`semiconductor_metrology`](55_semiconductors.md#semiconductor_metrology---measuring-what-you-have-made-mensura-resistentiae-informal) |
| `silicon_path` | 1,000.0 | [`silicon_path`](55_semiconductors.md#silicon_path---the-alternative-substrate-and-why-to-defer-it-silex-amplificans-informal) |
| `single_crystal` | 1,000.0 | [`single_crystal_growth`](55_semiconductors.md#single_crystal_growth---pulling-a-single-crystal-from-the-melt-cristallus-tractus-informal) |
| `vacuum_pumps` | 500.0 | [`vacuum_pumps`](55_semiconductors.md#vacuum_pumps---pumps-and-gauges-for-empty-space-antlia-pneumatica) |
| `vacuum_tube` | 900.0 | [`vacuum_tube`](55_semiconductors.md#vacuum_tube---the-diode-and-triode-lampas-electrica) |
| `zinc_industry_scale` | 600.0 | [`germanium_sourcing`](55_semiconductors.md#germanium_sourcing---finding-germanium-at-all-plumbum-cinereum-informal) |
| `zone_refining` | 1,200.0 | [`zone_refining`](55_semiconductors.md#zone_refining---pfanns-travelling-molten-zone-purgatio-per-zonam-informal) |

### 60_mathematics_method.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `algebra_symbolic` | 0 | 500.0 | _(module has no anchor)_ |
| `arithmetic_positional` | 0 | 450.0 | _(module has no anchor)_ |
| `atomic_theory` | 0 | 1,000.0 | _(module has no anchor)_ |
| `calculus` | 0 | 800.0 | _(module has no anchor)_ |
| `geometry_analytic` | 0 | 350.0 | _(module has no anchor)_ |
| `logarithms` | 0 | 400.0 | _(module has no anchor)_ |
| `newtonian_mechanics` | 0 | 600.0 | _(module has no anchor)_ |
| `sc2_notation_positional` | 0 | 0.0 | _(module has no anchor)_ |
| `scientific_method` | 0 | 350.0 | _(module has no anchor)_ |
| `statistics_basic` | 0 | 300.0 | _(module has no anchor)_ |
| `thermodynamics_theory` | 0 | 700.0 | _(module has no anchor)_ |
| `world_map` | 0 | 250.0 | _(module has no anchor)_ |
| `sc2_algebra_logarithm` | 1 | 70.0 | _(module has no anchor)_ |
| `sc2_algebra_quadratic` | 1 | 80.0 | _(module has no anchor)_ |
| `sc2_geometry_coordinate` | 1 | 80.0 | _(module has no anchor)_ |
| `sc2_geometry_trigonometry` | 1 | 100.0 | _(module has no anchor)_ |
| `sc2_notation_decimal_fraction` | 1 | 45.0 | _(module has no anchor)_ |
| `sc2_notation_decimal_point` | 1 | 20.0 | _(module has no anchor)_ |
| `sc2_notation_equals_sign` | 1 | 30.0 | _(module has no anchor)_ |
| `sc2_notation_exponents` | 1 | 45.0 | _(module has no anchor)_ |
| `sc2_notation_negative` | 1 | 50.0 | _(module has no anchor)_ |
| `sc2_notation_operator_symbols` | 1 | 35.0 | _(module has no anchor)_ |
| `sc2_notation_roots` | 1 | 40.0 | _(module has no anchor)_ |
| `sc2_notation_zero` | 1 | 40.0 | _(module has no anchor)_ |
| `sc2_probability_axioms` | 1 | 100.0 | _(module has no anchor)_ |
| `sc2_probability_combinatorics` | 1 | 80.0 | _(module has no anchor)_ |
| `sc2_statistics_mean_variance` | 1 | 60.0 | _(module has no anchor)_ |
| `sc2_algebra_binomial` | 2 | 90.0 | _(module has no anchor)_ |
| `sc2_algebra_complex_numbers` | 2 | 110.0 | _(module has no anchor)_ |
| `sc2_algebra_determinant` | 2 | 110.0 | _(module has no anchor)_ |
| `sc2_algebra_infinite_series` | 2 | 110.0 | _(module has no anchor)_ |
| `sc2_algebra_interpolation` | 2 | 100.0 | _(module has no anchor)_ |
| `sc2_algebra_least_squares` | 2 | 110.0 | _(module has no anchor)_ |
| `sc2_algebra_matrix` | 2 | 130.0 | _(module has no anchor)_ |
| `sc2_algebra_numerical_methods` | 2 | 120.0 | _(module has no anchor)_ |
| `sc2_algebra_polynomial` | 2 | 100.0 | _(module has no anchor)_ |
| `sc2_algebra_vector` | 2 | 120.0 | _(module has no anchor)_ |
| `sc2_calculus_derivative` | 2 | 140.0 | _(module has no anchor)_ |
| `sc2_calculus_fundamental_theorem` | 2 | 100.0 | _(module has no anchor)_ |
| `sc2_calculus_integral` | 2 | 150.0 | _(module has no anchor)_ |
| `sc2_calculus_limit` | 2 | 120.0 | _(module has no anchor)_ |
| `sc2_geometry_conics` | 2 | 100.0 | _(module has no anchor)_ |
| `sc2_geometry_descriptive` | 2 | 130.0 | _(module has no anchor)_ |
| `sc2_geometry_spherical_trig` | 2 | 120.0 | _(module has no anchor)_ |
| `sc2_notation_dimension` | 2 | 70.0 | _(module has no anchor)_ |
| `sc2_notation_metric_unit` | 2 | 80.0 | _(module has no anchor)_ |
| `sc2_notation_scientific` | 2 | 60.0 | _(module has no anchor)_ |
| `sc2_notation_significant_figures` | 2 | 90.0 | _(module has no anchor)_ |
| `sc2_probability_central_limit` | 2 | 120.0 | _(module has no anchor)_ |
| `sc2_probability_normal_distribution` | 2 | 110.0 | _(module has no anchor)_ |
| `sc2_statistics_blinding` | 2 | 90.0 | _(module has no anchor)_ |
| `sc2_statistics_blocking` | 2 | 100.0 | _(module has no anchor)_ |
| `sc2_statistics_confidence_interval` | 2 | 100.0 | _(module has no anchor)_ |
| `sc2_statistics_control_chart` | 2 | 110.0 | _(module has no anchor)_ |
| `sc2_statistics_control_group` | 2 | 70.0 | _(module has no anchor)_ |
| `sc2_statistics_correlation` | 2 | 100.0 | _(module has no anchor)_ |
| `sc2_statistics_mortality_table` | 2 | 100.0 | _(module has no anchor)_ |
| `sc2_statistics_randomisation` | 2 | 80.0 | _(module has no anchor)_ |
| `sc2_statistics_regression` | 2 | 110.0 | _(module has no anchor)_ |
| `sc2_statistics_sampling_theory` | 2 | 110.0 | _(module has no anchor)_ |
| `sc2_statistics_significance_test` | 2 | 120.0 | _(module has no anchor)_ |
| `sc2_statistics_t_test` | 2 | 120.0 | _(module has no anchor)_ |
| `sc2_algebra_tensor` | 3 | 180.0 | _(module has no anchor)_ |
| `sc2_calculus_fourier_series` | 3 | 160.0 | _(module has no anchor)_ |
| `sc2_calculus_fourier_transform` | 3 | 170.0 | _(module has no anchor)_ |
| `sc2_calculus_ode` | 3 | 150.0 | _(module has no anchor)_ |
| `sc2_calculus_pde` | 3 | 200.0 | _(module has no anchor)_ |
| `sc2_geometry_differential` | 3 | 170.0 | _(module has no anchor)_ |
| `sc2_geometry_non_euclidean` | 3 | 150.0 | _(module has no anchor)_ |
| `sc2_notation_error_propagation` | 3 | 120.0 | _(module has no anchor)_ |
| `sc2_statistics_anova` | 3 | 140.0 | _(module has no anchor)_ |

### 70_medicine_biology.md

| Node | Your hours | Recipe |
|---|---:|---|
| `germ_theory` | 350.0 | [`germ_theory`](70_medicine_biology.md#germ_theory---germ-theory-of-disease-no-roman-term-the-closest-existing-idea-is-varros-semina-morbi-seeds-of-disease) |
| `goal_public_health` | 0.0 | [`public_health`](70_medicine_biology.md#public_health) **BROKEN** |
| `md2_activated_sludge` | 250.0 | _(module has no anchor)_ |
| `md2_adrenaline` | 140.0 | _(module has no anchor)_ |
| `md2_anaesthetic_machine` | 250.0 | _(module has no anchor)_ |
| `md2_antitoxin` | 150.0 | _(module has no anchor)_ |
| `md2_appendicectomy` | 150.0 | _(module has no anchor)_ |
| `md2_auscultation` | 100.0 | _(module has no anchor)_ |
| `md2_autoclave` | 120.0 | _(module has no anchor)_ |
| `md2_barbiturates` | 160.0 | _(module has no anchor)_ |
| `md2_basal_metabolic_rate` | 100.0 | _(module has no anchor)_ |
| `md2_biopsy` | 100.0 | _(module has no anchor)_ |
| `md2_blood_bank` | 180.0 | _(module has no anchor)_ |
| `md2_blood_sugar_test` | 100.0 | _(module has no anchor)_ |
| `md2_blood_transfusion` | 120.0 | _(module has no anchor)_ |
| `md2_blood_typing` | 100.0 | _(module has no anchor)_ |
| `md2_caesarean_section` | 180.0 | _(module has no anchor)_ |
| `md2_cataract_extraction` | 160.0 | _(module has no anchor)_ |
| `md2_catgut_suture` | 100.0 | _(module has no anchor)_ |
| `md2_child_clinic` | 110.0 | _(module has no anchor)_ |
| `md2_chlorination` | 120.0 | _(module has no anchor)_ |
| `md2_citrate_anticoagulation` | 80.0 | _(module has no anchor)_ |
| `md2_clinical_thermometer` | 80.0 | _(module has no anchor)_ |
| `md2_contact_tracing` | 120.0 | _(module has no anchor)_ |
| `md2_contrast_media` | 120.0 | _(module has no anchor)_ |
| `md2_cystoscope` | 120.0 | _(module has no anchor)_ |
| `md2_differential_count` | 80.0 | _(module has no anchor)_ |
| `md2_digitalis` | 140.0 | _(module has no anchor)_ |
| `md2_ecg` | 250.0 | _(module has no anchor)_ |
| `md2_eeg` | 300.0 | _(module has no anchor)_ |
| `md2_electrocautery` | 200.0 | _(module has no anchor)_ |
| `md2_endoscope` | 200.0 | _(module has no anchor)_ |
| `md2_endotracheal_intubation` | 150.0 | _(module has no anchor)_ |
| `md2_fluoroscopy` | 250.0 | _(module has no anchor)_ |
| `md2_food_adulteration_law` | 80.0 | _(module has no anchor)_ |
| `md2_frozen_section` | 150.0 | _(module has no anchor)_ |
| `md2_gastrectomy` | 200.0 | _(module has no anchor)_ |
| `md2_haemocytometer` | 100.0 | _(module has no anchor)_ |
| `md2_haemostat` | 80.0 | _(module has no anchor)_ |
| `md2_hernia_repair` | 120.0 | _(module has no anchor)_ |
| `md2_hospital_infection_control` | 150.0 | _(module has no anchor)_ |
| `md2_insulin` | 200.0 | _(module has no anchor)_ |
| `md2_iodised_salt` | 100.0 | _(module has no anchor)_ |
| `md2_isolation_hospital` | 180.0 | _(module has no anchor)_ |
| `md2_iv_saline` | 80.0 | _(module has no anchor)_ |
| `md2_laryngoscope` | 100.0 | _(module has no anchor)_ |
| `md2_light_source` | 120.0 | _(module has no anchor)_ |
| `md2_local_anaesthesia` | 80.0 | _(module has no anchor)_ |
| `md2_maternal_clinic` | 120.0 | _(module has no anchor)_ |
| `md2_meat_inspection` | 100.0 | _(module has no anchor)_ |
| `md2_milk_pasteurisation` | 120.0 | _(module has no anchor)_ |
| `md2_morphine` | 120.0 | _(module has no anchor)_ |
| `md2_mosquito_net` | 40.0 | _(module has no anchor)_ |
| `md2_notifiable_disease` | 100.0 | _(module has no anchor)_ |
| `md2_oral_rehydration` | 90.0 | _(module has no anchor)_ |
| `md2_orthopaedic_fixation` | 180.0 | _(module has no anchor)_ |
| `md2_otoscope` | 80.0 | _(module has no anchor)_ |
| `md2_penicillin_fermentation` | 300.0 | _(module has no anchor)_ |
| `md2_penicillin_freeze_dry` | 220.0 | _(module has no anchor)_ |
| `md2_penicillin_production` | 200.0 | _(module has no anchor)_ |
| `md2_percussion` | 40.0 | _(module has no anchor)_ |
| `md2_pit_latrine` | 80.0 | _(module has no anchor)_ |
| `md2_plant_chemistry` | 100.0 | _(module has no anchor)_ |
| `md2_plaster_cast` | 100.0 | _(module has no anchor)_ |
| `md2_retractor` | 120.0 | _(module has no anchor)_ |
| `md2_salicylate` | 130.0 | _(module has no anchor)_ |
| `md2_sand_filtration` | 150.0 | _(module has no anchor)_ |
| `md2_sewage_separation` | 180.0 | _(module has no anchor)_ |
| `md2_skin_graft` | 150.0 | _(module has no anchor)_ |
| `md2_sphygmomanometer` | 120.0 | _(module has no anchor)_ |
| `md2_spinal_anaesthesia` | 120.0 | _(module has no anchor)_ |
| `md2_spirometer` | 100.0 | _(module has no anchor)_ |
| `md2_staining_methylene` | 80.0 | _(module has no anchor)_ |
| `md2_stethoscope` | 60.0 | _(module has no anchor)_ |
| `md2_streptomycin` | 200.0 | _(module has no anchor)_ |
| `md2_sulphonamides` | 180.0 | _(module has no anchor)_ |
| `md2_surgical_drape` | 80.0 | _(module has no anchor)_ |
| `md2_surgical_glove` | 80.0 | _(module has no anchor)_ |
| `md2_surgical_gown` | 70.0 | _(module has no anchor)_ |
| `md2_surgical_mask` | 60.0 | _(module has no anchor)_ |
| `md2_synthetic_suture` | 150.0 | _(module has no anchor)_ |
| `md2_thyroid_extract` | 120.0 | _(module has no anchor)_ |
| `md2_thyroidectomy` | 170.0 | _(module has no anchor)_ |
| `md2_tourniquet` | 80.0 | _(module has no anchor)_ |
| `md2_traction` | 120.0 | _(module has no anchor)_ |
| `md2_urinalysis` | 60.0 | _(module has no anchor)_ |
| `md2_vaccine_cholera` | 130.0 | _(module has no anchor)_ |
| `md2_vaccine_diphtheria` | 160.0 | _(module has no anchor)_ |
| `md2_vaccine_pertussis` | 140.0 | _(module has no anchor)_ |
| `md2_vaccine_plague` | 150.0 | _(module has no anchor)_ |
| `md2_vaccine_rabies` | 180.0 | _(module has no anchor)_ |
| `md2_vaccine_smallpox` | 120.0 | _(module has no anchor)_ |
| `md2_vaccine_tetanus` | 150.0 | _(module has no anchor)_ |
| `md2_vaccine_typhoid` | 140.0 | _(module has no anchor)_ |
| `md2_vaccine_yellow_fever` | 180.0 | _(module has no anchor)_ |
| `md2_vector_control` | 100.0 | _(module has no anchor)_ |
| `md2_vitamin_a` | 110.0 | _(module has no anchor)_ |
| `md2_vitamin_b1` | 100.0 | _(module has no anchor)_ |
| `md2_vitamin_b12` | 160.0 | _(module has no anchor)_ |
| `md2_vitamin_c` | 110.0 | _(module has no anchor)_ |
| `md2_vitamin_d` | 120.0 | _(module has no anchor)_ |
| `md2_wassermann_test` | 120.0 | _(module has no anchor)_ |
| `md2_xray_plate` | 200.0 | _(module has no anchor)_ |
| `med_amputation` | 0.0 | _(module has no anchor)_ |
| `med_aqueducts_latrines` | 0.0 | _(module has no anchor)_ |
| `med_asepsis_antisepsis` | 120.0 | _(module has no anchor)_ |
| `med_aspirin` | 80.0 | _(module has no anchor)_ |
| `med_autoclave` | 150.0 | _(module has no anchor)_ |
| `med_blood_groups` | 150.0 | _(module has no anchor)_ |
| `med_bone_setting` | 0.0 | _(module has no anchor)_ |
| `med_cataract_couching` | 0.0 | _(module has no anchor)_ |
| `med_clinical_trials` | 200.0 | _(module has no anchor)_ |
| `med_coca_alkaloid` | 60.0 | _(module has no anchor)_ |
| `med_dentistry` | 120.0 | _(module has no anchor)_ |
| `med_electrocardiogram` | 200.0 | _(module has no anchor)_ |
| `med_endoscope` | 200.0 | _(module has no anchor)_ |
| `med_epidemiology_statistics` | 150.0 | _(module has no anchor)_ |
| `med_ether_anaesthesia` | 120.0 | _(module has no anchor)_ |
| `med_forensic_medicine` | 120.0 | _(module has no anchor)_ |
| `med_gram_stain_culture` | 100.0 | _(module has no anchor)_ |
| `med_handwashing_semmelweis` | 80.0 | _(module has no anchor)_ |
| `med_herbal_pharmacy` | 100.0 | _(module has no anchor)_ |
| `med_hospital_institution` | 200.0 | _(module has no anchor)_ |
| `med_hypodermic_syringe` | 100.0 | _(module has no anchor)_ |
| `med_insulin` | 200.0 | _(module has no anchor)_ |
| `med_legal_physician` | 0.0 | _(module has no anchor)_ |
| `med_ligature_haemostasis` | 60.0 | _(module has no anchor)_ |
| `med_medical_education` | 200.0 | _(module has no anchor)_ |
| `med_microscopy_pathology` | 120.0 | _(module has no anchor)_ |
| `med_nursing_profession` | 150.0 | _(module has no anchor)_ |
| `med_nutrition_vitamins` | 120.0 | _(module has no anchor)_ |
| `med_obstetric_antisepsis` | 120.0 | _(module has no anchor)_ |
| `med_obstetric_practice` | 0.0 | _(module has no anchor)_ |
| `med_ophthalmoscope` | 150.0 | _(module has no anchor)_ |
| `med_opium_mandrake` | 0.0 | _(module has no anchor)_ |
| `med_penicillin` | 250.0 | _(module has no anchor)_ |
| `med_quarantine_sanitation` | 150.0 | _(module has no anchor)_ |
| `med_saline_resuscitation` | 60.0 | _(module has no anchor)_ |
| `med_spectacles_refraction` | 60.0 | _(module has no anchor)_ |
| `med_sphygmomanometer` | 100.0 | _(module has no anchor)_ |
| `med_sterile_technique` | 100.0 | _(module has no anchor)_ |
| `med_stethoscope_percussion` | 60.0 | _(module has no anchor)_ |
| `med_sulfonamides` | 150.0 | _(module has no anchor)_ |
| `med_surgical_gloves_mask` | 40.0 | _(module has no anchor)_ |
| `med_surgical_kit_good` | 0.0 | _(module has no anchor)_ |
| `med_trepanation` | 0.0 | _(module has no anchor)_ |
| `med_vaccination_progression` | 150.0 | _(module has no anchor)_ |
| `med_valetudinaria` | 200.0 | _(module has no anchor)_ |
| `med_vector_control` | 100.0 | _(module has no anchor)_ |
| `med_wound_suturing` | 0.0 | _(module has no anchor)_ |
| `med_xray_imaging` | 200.0 | _(module has no anchor)_ |
| `plague_preparedness` | 700.0 | [`quarantine_publichealth`](70_medicine_biology.md#quarantine_publichealth---quarantine-clean-water-sewage-separation-and-food-inspection-custodia-cura-aquarum-no-single-roman-term-covers-the-whole-programme) |
| `sanitation_antisepsis` | 300.0 | [`sanitation_antisepsis`](70_medicine_biology.md#sanitation_antisepsis---boiled-water-handwashing-wound-irrigation-quarantine-aqua-fervens-manus-lotae-no-single-roman-term-covers-the-practice) |

### 75_agriculture_food.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `crop_rotation` | 1 | 450.0 | [`crop_rotation`](75_agriculture_food.md#crop_rotation---three-course-rotation-with-a-legume-break) |
| `fud_alfalfa` | 1 | 100.0 | _(module has no anchor)_ |
| `fud_bone_meal_fertilizer` | 1 | 100.0 | _(module has no anchor)_ |
| `fud_bottling_sealed_cork` | 1 | 80.0 | _(module has no anchor)_ |
| `fud_brewing_with_hops` | 1 | 120.0 | _(module has no anchor)_ |
| `fud_clover_winter_fodder` | 1 | 80.0 | _(module has no anchor)_ |
| `fud_coffee_trade_import` | 1 | 60.0 | _(module has no anchor)_ |
| `fud_dairy_butter_production` | 1 | 120.0 | _(module has no anchor)_ |
| `fud_dairy_cheese_aging` | 1 | 100.0 | _(module has no anchor)_ |
| `fud_distillation_spirits` | 1 | 150.0 | _(module has no anchor)_ |
| `fud_enclosure_of_common_land` | 1 | 150.0 | _(module has no anchor)_ |
| `fud_farm_as_capital_enterprise` | 1 | 200.0 | _(module has no anchor)_ |
| `fud_fish_curing_and_smoking` | 1 | 120.0 | _(module has no anchor)_ |
| `fud_guano_import_trade` | 1 | 80.0 | _(module has no anchor)_ |
| `fud_hay_making_storage` | 1 | 100.0 | _(module has no anchor)_ |
| `fud_ice_harvesting_and_cutting` | 1 | 100.0 | _(module has no anchor)_ |
| `fud_ice_house_construction` | 1 | 150.0 | _(module has no anchor)_ |
| `fud_liming_acid_soils` | 1 | 100.0 | _(module has no anchor)_ |
| `fud_livestock_selective_cattle` | 1 | 200.0 | _(module has no anchor)_ |
| `fud_livestock_selective_sheep` | 1 | 180.0 | _(module has no anchor)_ |
| `fud_malt_production` | 1 | 120.0 | _(module has no anchor)_ |
| `fud_nitrogen_fixing_understanding` | 1 | 80.0 | _(module has no anchor)_ |
| `fud_rice_cultivation` | 1 | 120.0 | _(module has no anchor)_ |
| `fud_root_cellar_storage` | 1 | 120.0 | _(module has no anchor)_ |
| `fud_seed_drill` | 1 | 180.0 | _(module has no anchor)_ |
| `fud_selective_breeding_pedigree` | 1 | 200.0 | _(module has no anchor)_ |
| `fud_sourdough_starter` | 1 | 100.0 | _(module has no anchor)_ |
| `fud_sugar_cane_cultivation` | 1 | 100.0 | _(module has no anchor)_ |
| `fud_tea_trade_import` | 1 | 60.0 | _(module has no anchor)_ |
| `fud_three_field_rotation` | 1 | 120.0 | _(module has no anchor)_ |
| `fud_turnips_winter_fodder` | 1 | 100.0 | _(module has no anchor)_ |
| `fud_vegetable_oil_extraction` | 1 | 100.0 | _(module has no anchor)_ |
| `fud_vinegar_production` | 1 | 80.0 | _(module has no anchor)_ |
| `horse_collar` | 1 | 200.0 | [`horse_collar_harness`](75_agriculture_food.md#horse_collar_harness---see-module-40-for-construction-agronomic-case-here) |
| `fud_beet_sugar_processing` | 2 | 200.0 | _(module has no anchor)_ |
| `fud_canning_appert_method` | 2 | 200.0 | _(module has no anchor)_ |
| `fud_drying_evaporated_milk` | 2 | 150.0 | _(module has no anchor)_ |
| `fud_grain_storage_silos` | 2 | 200.0 | _(module has no anchor)_ |
| `fud_heavy_mouldboard_plough_coulter` | 2 | 200.0 | _(module has no anchor)_ |
| `fud_ice_trade_logistics` | 2 | 120.0 | _(module has no anchor)_ |
| `fud_mechanical_reaper` | 2 | 300.0 | _(module has no anchor)_ |
| `fud_roller_mill` | 2 | 250.0 | _(module has no anchor)_ |
| `fud_roller_milled_white_flour` | 2 | 150.0 | _(module has no anchor)_ |
| `fud_silage_fermentation` | 2 | 150.0 | _(module has no anchor)_ |
| `fud_whaling_industry` | 2 | 300.0 | _(module has no anchor)_ |
| `fud_winnowing_machine` | 2 | 150.0 | _(module has no anchor)_ |
| `fud_yeast_pure_culture` | 2 | 200.0 | _(module has no anchor)_ |
| `fud_can_opener` | 3 | 100.0 | _(module has no anchor)_ |
| `fud_margarine_synthesis` | 3 | 200.0 | _(module has no anchor)_ |
| `fud_mechanical_refrigeration` | 3 | 300.0 | _(module has no anchor)_ |
| `fud_superphosphate_fertilizer` | 3 | 200.0 | _(module has no anchor)_ |
| `fud_tin_plate_cans` | 3 | 200.0 | _(module has no anchor)_ |
| `fud_cacao` | 4 | 60.0 | _(module has no anchor)_ |
| `fud_cold_chain_refrigerated_shipping` | 4 | 200.0 | _(module has no anchor)_ |
| `fud_freezing_with_mechanical_cold` | 4 | 150.0 | _(module has no anchor)_ |
| `fud_maize` | 4 | 60.0 | _(module has no anchor)_ |
| `fud_potato` | 4 | 60.0 | _(module has no anchor)_ |
| `fud_haber_process_synthetic_nitrogen` | 5 | 600.0 | _(module has no anchor)_ |

### 76_farming_food_deep.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `ag2_bottling` | 0 | 60.0 | [`ag2_bottling`](76_farming_food_deep.md#ag2_bottling-ag2_crown_cork---sealing-liquids-for-storage-and-transport) |
| `ag2_budding` | 0 | 45.0 | [`ag2_grafting`](76_farming_food_deep.md#ag2_grafting-ag2_budding-ag2_layering-ag2_rootstocks---vegetative-propagation-as-knowledge) |
| `ag2_butter` | 0 | 50.0 | [`ag2_butter`](76_farming_food_deep.md#ag2_butter-ag2_cheese_families-ag2_condensed_milk-ag2_evaporated_milk---dairy-processing-and-preservation) |
| `ag2_chaff_cutter` | 0 | 50.0 | [`ag2_winnower`](76_farming_food_deep.md#ag2_winnower-ag2_fanning_mill-ag2_chaff_cutter-ag2_baler---cleaning-sizing-and-packing-bulk) |
| `ag2_cheese_families` | 0 | 80.0 | [`ag2_butter`](76_farming_food_deep.md#ag2_butter-ag2_cheese_families-ag2_condensed_milk-ag2_evaporated_milk---dairy-processing-and-preservation) |
| `ag2_composting` | 0 | 40.0 | [`ag2_norfolk_course`](76_farming_food_deep.md#ag2_norfolk_course---four-course-rotation-without-fallow) |
| `ag2_coulter` | 0 | 40.0 | [`ag2_seed_drill`](76_farming_food_deep.md#ag2_seed_drill-ag2_horse_hoe-ag2_coulter---rows-instead-of-broadcast) |
| `ag2_grafting` | 0 | 50.0 | [`ag2_grafting`](76_farming_food_deep.md#ag2_grafting-ag2_budding-ag2_layering-ag2_rootstocks---vegetative-propagation-as-knowledge) |
| `ag2_harrow` | 0 | 45.0 | [`ag2_cultivator`](76_farming_food_deep.md#ag2_cultivator-ag2_subsoiler-ag2_harrow-ag2_roller---working-ground-between-sowing-and-harvest) |
| `ag2_hopping` | 0 | 40.0 | [`ag2_malting`](76_farming_food_deep.md#ag2_malting-ag2_mashing-ag2_hopping-ag2_hydrometer-ag2_pot_still-ag2_column_still---brewing-and-distilling-as-controlled-process) |
| `ag2_hydrometer` | 0 | 50.0 | [`ag2_malting`](76_farming_food_deep.md#ag2_malting-ag2_mashing-ag2_hopping-ag2_hydrometer-ag2_pot_still-ag2_column_still---brewing-and-distilling-as-controlled-process) |
| `ag2_layering` | 0 | 40.0 | [`ag2_grafting`](76_farming_food_deep.md#ag2_grafting-ag2_budding-ag2_layering-ag2_rootstocks---vegetative-propagation-as-knowledge) |
| `ag2_liming` | 0 | 30.0 | [`ag2_liming`](76_farming_food_deep.md#ag2_liming-ag2_marling-ag2_soil_testing---reading-and-fixing-soil-chemistry) |
| `ag2_malting` | 0 | 60.0 | [`ag2_malting`](76_farming_food_deep.md#ag2_malting-ag2_mashing-ag2_hopping-ag2_hydrometer-ag2_pot_still-ag2_column_still---brewing-and-distilling-as-controlled-process) |
| `ag2_marling` | 0 | 25.0 | [`ag2_liming`](76_farming_food_deep.md#ag2_liming-ag2_marling-ag2_soil_testing---reading-and-fixing-soil-chemistry) |
| `ag2_mashing` | 0 | 50.0 | [`ag2_malting`](76_farming_food_deep.md#ag2_malting-ag2_mashing-ag2_hopping-ag2_hydrometer-ag2_pot_still-ag2_column_still---brewing-and-distilling-as-controlled-process) |
| `ag2_nicotine_pesticide` | 0 | 60.0 | [`ag2_bordeaux_mixture`](76_farming_food_deep.md#ag2_bordeaux_mixture-ag2_lime_sulphur-ag2_lead_arsenate-ag2_nicotine_pesticide-ag2_pyrethrum-ag2_ddt---pest-chemicals-oldest-to-most-dangerous) |
| `ag2_oil_pressing` | 0 | 60.0 | [`ag2_oil_pressing`](76_farming_food_deep.md#ag2_oil_pressing-ag2_fat_hydrogenation---extracting-and-modifying-fats) |
| `ag2_pot_still` | 0 | 60.0 | [`ag2_malting`](76_farming_food_deep.md#ag2_malting-ag2_mashing-ag2_hopping-ag2_hydrometer-ag2_pot_still-ag2_column_still---brewing-and-distilling-as-controlled-process) |
| `ag2_potash` | 0 | 40.0 | [`ag2_potash`](76_farming_food_deep.md#ag2_potash---wood-ash-as-fertiliser) |
| `ag2_roller` | 0 | 40.0 | [`ag2_cultivator`](76_farming_food_deep.md#ag2_cultivator-ag2_subsoiler-ag2_harrow-ag2_roller---working-ground-between-sowing-and-harvest) |
| `ag2_root_cutter` | 0 | 60.0 | [`ag2_ridging_plough`](76_farming_food_deep.md#ag2_ridging_plough-ag2_root_cutter-ag2_potato_lifter---handling-root-crops) |
| `ag2_sheep_dip` | 0 | 70.0 | [`ag2_tuberculin_test`](76_farming_food_deep.md#ag2_tuberculin_test-ag2_veterinary_vaccination-ag2_sheep_dip---disease-control-in-livestock) |
| `ag2_terracing` | 0 | 50.0 | [`ag2_erosion_control`](76_farming_food_deep.md#ag2_erosion_control-ag2_terracing-ag2_contour_ploughing---keeping-soil-in-place) |
| `ag2_adulteration_law` | 1 | 110.0 | [`ag2_adulteration_law`](76_farming_food_deep.md#ag2_adulteration_law-ag2_food_laboratory---regulation-and-the-means-to-enforce-it) |
| `ag2_balanced_ration` | 1 | 110.0 | [`ag2_progeny_testing`](76_farming_food_deep.md#ag2_progeny_testing-ag2_herd_book-ag2_artificial_insemination-ag2_balanced_ration---livestock-breeding-and-feeding-as-bookkeeping) |
| `ag2_bone_meal` | 1 | 70.0 | [`ag2_guano`](76_farming_food_deep.md#ag2_guano-ag2_bone_meal-ag2_basic_slag---imported-and-recycled-phosphate) |
| `ag2_bordeaux_mixture` | 1 | 80.0 | [`ag2_bordeaux_mixture`](76_farming_food_deep.md#ag2_bordeaux_mixture-ag2_lime_sulphur-ag2_lead_arsenate-ag2_nicotine_pesticide-ag2_pyrethrum-ag2_ddt---pest-chemicals-oldest-to-most-dangerous) |
| `ag2_botanic_garden` | 1 | 110.0 | [`ag2_botanic_garden`](76_farming_food_deep.md#ag2_botanic_garden-ag2_wardian_case-ag2_plant_quarantine---moving-living-plants-across-oceans) |
| `ag2_canning` | 1 | 100.0 | [`ag2_canning`](76_farming_food_deep.md#ag2_canning-ag2_retort-ag2_double_seam_can---preservation-that-worked-before-anyone-knew-why) |
| `ag2_cold_store` | 1 | 110.0 | [`ag2_refrigeration_ice`](76_farming_food_deep.md#ag2_refrigeration_ice-ag2_refrigerated_ship-ag2_cold_store---the-cold-chain) |
| `ag2_column_still` | 1 | 120.0 | [`ag2_malting`](76_farming_food_deep.md#ag2_malting-ag2_mashing-ag2_hopping-ag2_hydrometer-ag2_pot_still-ag2_column_still---brewing-and-distilling-as-controlled-process) |
| `ag2_condensed_milk` | 1 | 100.0 | [`ag2_butter`](76_farming_food_deep.md#ag2_butter-ag2_cheese_families-ag2_condensed_milk-ag2_evaporated_milk---dairy-processing-and-preservation) |
| `ag2_contour_ploughing` | 1 | 70.0 | [`ag2_erosion_control`](76_farming_food_deep.md#ag2_erosion_control-ag2_terracing-ag2_contour_ploughing---keeping-soil-in-place) |
| `ag2_controlled_pollination` | 1 | 150.0 | [`ag2_record_keeping_breeding`](76_farming_food_deep.md#ag2_record_keeping_breeding-ag2_pure_line_selection-ag2_hybridisation-ag2_hybrid_maize-ag2_controlled_pollination---selection-and-breeding-as-bookkeeping) |
| `ag2_cream_separator` | 1 | 100.0 | [`ag2_milking_machine`](76_farming_food_deep.md#ag2_milking_machine-ag2_cream_separator-ag2_battery_poultry-ag2_silage_silo---dairy-poultry-and-fodder-at-scale) |
| `ag2_cultivator` | 1 | 70.0 | [`ag2_cultivator`](76_farming_food_deep.md#ag2_cultivator-ag2_subsoiler-ag2_harrow-ag2_roller---working-ground-between-sowing-and-harvest) |
| `ag2_erosion_control` | 1 | 60.0 | [`ag2_erosion_control`](76_farming_food_deep.md#ag2_erosion_control-ag2_terracing-ag2_contour_ploughing---keeping-soil-in-place) |
| `ag2_evaporated_milk` | 1 | 95.0 | [`ag2_butter`](76_farming_food_deep.md#ag2_butter-ag2_cheese_families-ag2_condensed_milk-ag2_evaporated_milk---dairy-processing-and-preservation) |
| `ag2_fanning_mill` | 1 | 110.0 | [`ag2_winnower`](76_farming_food_deep.md#ag2_winnower-ag2_fanning_mill-ag2_chaff_cutter-ag2_baler---cleaning-sizing-and-packing-bulk) |
| `ag2_fermentation_control` | 1 | 100.0 | [`ag2_yeast_culture`](76_farming_food_deep.md#ag2_yeast_culture-ag2_fermentation_control---controlling-fermentation-deliberately) |
| `ag2_gravity_irrigation` | 1 | 110.0 | [`ag2_tile_drainage`](76_farming_food_deep.md#ag2_tile_drainage-ag2_gravity_irrigation---moving-water-off-and-onto-fields) |
| `ag2_green_manure` | 1 | 50.0 | [`ag2_norfolk_course`](76_farming_food_deep.md#ag2_norfolk_course---four-course-rotation-without-fallow) |
| `ag2_guano` | 1 | 30.0 | [`ag2_guano`](76_farming_food_deep.md#ag2_guano-ag2_bone_meal-ag2_basic_slag---imported-and-recycled-phosphate) |
| `ag2_herd_book` | 1 | 100.0 | [`ag2_progeny_testing`](76_farming_food_deep.md#ag2_progeny_testing-ag2_herd_book-ag2_artificial_insemination-ag2_balanced_ration---livestock-breeding-and-feeding-as-bookkeeping) |
| `ag2_horse_hoe` | 1 | 120.0 | [`ag2_seed_drill`](76_farming_food_deep.md#ag2_seed_drill-ag2_horse_hoe-ag2_coulter---rows-instead-of-broadcast) |
| `ag2_lime_sulphur` | 1 | 90.0 | [`ag2_bordeaux_mixture`](76_farming_food_deep.md#ag2_bordeaux_mixture-ag2_lime_sulphur-ag2_lead_arsenate-ag2_nicotine_pesticide-ag2_pyrethrum-ag2_ddt---pest-chemicals-oldest-to-most-dangerous) |
| `ag2_mower` | 1 | 95.0 | [`ag2_reaper`](76_farming_food_deep.md#ag2_reaper-ag2_reaper_binder-ag2_mower-ag2_tedder---cutting-and-handling-grain-and-hay) |
| `ag2_nitrite_curing` | 1 | 100.0 | [`ag2_pasteurisation`](76_farming_food_deep.md#ag2_pasteurisation-ag2_nitrite_curing---milder-preservation-with-narrower-margins) |
| `ag2_nitrogen_cycle` | 1 | 120.0 | [`ag2_rhizobia`](76_farming_food_deep.md#ag2_rhizobia---legume-root-nodules-and-the-nitrogen-cycle-attributed) |
| `ag2_norfolk_course` | 1 | 60.0 | [`ag2_norfolk_course`](76_farming_food_deep.md#ag2_norfolk_course---four-course-rotation-without-fallow) |
| `ag2_pasteurisation` | 1 | 180.0 | [`ag2_pasteurisation`](76_farming_food_deep.md#ag2_pasteurisation-ag2_nitrite_curing---milder-preservation-with-narrower-margins) |
| `ag2_plant_quarantine` | 1 | 90.0 | [`ag2_botanic_garden`](76_farming_food_deep.md#ag2_botanic_garden-ag2_wardian_case-ag2_plant_quarantine---moving-living-plants-across-oceans) |
| `ag2_potato_lifter` | 1 | 65.0 | [`ag2_ridging_plough`](76_farming_food_deep.md#ag2_ridging_plough-ag2_root_cutter-ag2_potato_lifter---handling-root-crops) |
| `ag2_progeny_testing` | 1 | 110.0 | [`ag2_progeny_testing`](76_farming_food_deep.md#ag2_progeny_testing-ag2_herd_book-ag2_artificial_insemination-ag2_balanced_ration---livestock-breeding-and-feeding-as-bookkeeping) |
| `ag2_pure_line_selection` | 1 | 110.0 | [`ag2_record_keeping_breeding`](76_farming_food_deep.md#ag2_record_keeping_breeding-ag2_pure_line_selection-ag2_hybridisation-ag2_hybrid_maize-ag2_controlled_pollination---selection-and-breeding-as-bookkeeping) |
| `ag2_purifier` | 1 | 100.0 | [`ag2_roller_mill`](76_farming_food_deep.md#ag2_roller_mill-ag2_purifier-ag2_white_flour_loss---milling-wheat-and-the-cost-it-hides) |
| `ag2_pyrethrum` | 1 | 70.0 | [`ag2_bordeaux_mixture`](76_farming_food_deep.md#ag2_bordeaux_mixture-ag2_lime_sulphur-ag2_lead_arsenate-ag2_nicotine_pesticide-ag2_pyrethrum-ag2_ddt---pest-chemicals-oldest-to-most-dangerous) |
| `ag2_reaper` | 1 | 110.0 | [`ag2_reaper`](76_farming_food_deep.md#ag2_reaper-ag2_reaper_binder-ag2_mower-ag2_tedder---cutting-and-handling-grain-and-hay) |
| `ag2_record_keeping_breeding` | 1 | 90.0 | [`ag2_record_keeping_breeding`](76_farming_food_deep.md#ag2_record_keeping_breeding-ag2_pure_line_selection-ag2_hybridisation-ag2_hybrid_maize-ag2_controlled_pollination---selection-and-breeding-as-bookkeeping) |
| `ag2_refrigeration_ice` | 1 | 70.0 | [`ag2_refrigeration_ice`](76_farming_food_deep.md#ag2_refrigeration_ice-ag2_refrigerated_ship-ag2_cold_store---the-cold-chain) |
| `ag2_retort` | 1 | 110.0 | [`ag2_canning`](76_farming_food_deep.md#ag2_canning-ag2_retort-ag2_double_seam_can---preservation-that-worked-before-anyone-knew-why) |
| `ag2_ridging_plough` | 1 | 60.0 | [`ag2_ridging_plough`](76_farming_food_deep.md#ag2_ridging_plough-ag2_root_cutter-ag2_potato_lifter---handling-root-crops) |
| `ag2_rootstocks` | 1 | 100.0 | [`ag2_grafting`](76_farming_food_deep.md#ag2_grafting-ag2_budding-ag2_layering-ag2_rootstocks---vegetative-propagation-as-knowledge) |
| `ag2_seed_trade` | 1 | 80.0 | [`ag2_seed_certification`](76_farming_food_deep.md#ag2_seed_certification-ag2_seed_trade---guaranteeing-what-is-in-the-sack) |
| `ag2_silage_silo` | 1 | 100.0 | [`ag2_milking_machine`](76_farming_food_deep.md#ag2_milking_machine-ag2_cream_separator-ag2_battery_poultry-ag2_silage_silo---dairy-poultry-and-fodder-at-scale) |
| `ag2_sprayer` | 1 | 95.0 | [`ag2_sprayer`](76_farming_food_deep.md#ag2_sprayer-ag2_biological_control-ag2_resistant_variety---applying-and-avoiding-chemicals) |
| `ag2_subsoiler` | 1 | 55.0 | [`ag2_cultivator`](76_farming_food_deep.md#ag2_cultivator-ag2_subsoiler-ag2_harrow-ag2_roller---working-ground-between-sowing-and-harvest) |
| `ag2_sugar_refining` | 1 | 110.0 | [`ag2_centrifugal_sugar`](76_farming_food_deep.md#ag2_centrifugal_sugar-ag2_vacuum_pan-ag2_sugar_refining---turning-cane-or-beet-juice-into-refined-sugar) |
| `ag2_tedder` | 1 | 65.0 | [`ag2_reaper`](76_farming_food_deep.md#ag2_reaper-ag2_reaper_binder-ag2_mower-ag2_tedder---cutting-and-handling-grain-and-hay) |
| `ag2_threshing_machine` | 1 | 250.0 | [`ag2_threshing_machine`](76_farming_food_deep.md#ag2_threshing_machine-ag2_combine_harvester---separating-grain-from-straw-by-machine) |
| `ag2_tile_drainage` | 1 | 80.0 | [`ag2_tile_drainage`](76_farming_food_deep.md#ag2_tile_drainage-ag2_gravity_irrigation---moving-water-off-and-onto-fields) |
| `ag2_tuberculin_test` | 1 | 90.0 | [`ag2_tuberculin_test`](76_farming_food_deep.md#ag2_tuberculin_test-ag2_veterinary_vaccination-ag2_sheep_dip---disease-control-in-livestock) |
| `ag2_vacuum_pan` | 1 | 100.0 | [`ag2_centrifugal_sugar`](76_farming_food_deep.md#ag2_centrifugal_sugar-ag2_vacuum_pan-ag2_sugar_refining---turning-cane-or-beet-juice-into-refined-sugar) |
| `ag2_wardian_case` | 1 | 100.0 | [`ag2_botanic_garden`](76_farming_food_deep.md#ag2_botanic_garden-ag2_wardian_case-ag2_plant_quarantine---moving-living-plants-across-oceans) |
| `ag2_white_flour_loss` | 1 | 90.0 | [`ag2_roller_mill`](76_farming_food_deep.md#ag2_roller_mill-ag2_purifier-ag2_white_flour_loss---milling-wheat-and-the-cost-it-hides) |
| `ag2_winnower` | 1 | 80.0 | [`ag2_winnower`](76_farming_food_deep.md#ag2_winnower-ag2_fanning_mill-ag2_chaff_cutter-ag2_baler---cleaning-sizing-and-packing-bulk) |
| `ag2_yeast_culture` | 1 | 110.0 | [`ag2_yeast_culture`](76_farming_food_deep.md#ag2_yeast_culture-ag2_fermentation_control---controlling-fermentation-deliberately) |
| `ag2_artificial_insemination` | 2 | 140.0 | [`ag2_progeny_testing`](76_farming_food_deep.md#ag2_progeny_testing-ag2_herd_book-ag2_artificial_insemination-ag2_balanced_ration---livestock-breeding-and-feeding-as-bookkeeping) |
| `ag2_baler` | 2 | 150.0 | [`ag2_winnower`](76_farming_food_deep.md#ag2_winnower-ag2_fanning_mill-ag2_chaff_cutter-ag2_baler---cleaning-sizing-and-packing-bulk) |
| `ag2_basic_slag` | 2 | 50.0 | [`ag2_guano`](76_farming_food_deep.md#ag2_guano-ag2_bone_meal-ag2_basic_slag---imported-and-recycled-phosphate) |
| `ag2_battery_poultry` | 2 | 110.0 | [`ag2_milking_machine`](76_farming_food_deep.md#ag2_milking_machine-ag2_cream_separator-ag2_battery_poultry-ag2_silage_silo---dairy-poultry-and-fodder-at-scale) |
| `ag2_biological_control` | 2 | 110.0 | [`ag2_sprayer`](76_farming_food_deep.md#ag2_sprayer-ag2_biological_control-ag2_resistant_variety---applying-and-avoiding-chemicals) |
| `ag2_centrifugal_sugar` | 2 | 95.0 | [`ag2_centrifugal_sugar`](76_farming_food_deep.md#ag2_centrifugal_sugar-ag2_vacuum_pan-ag2_sugar_refining---turning-cane-or-beet-juice-into-refined-sugar) |
| `ag2_coffee_voyage` | 2 | 90.0 | [`ag2_sugar_voyage`](76_farming_food_deep.md#ag2_sugar_voyage-ag2_coffee_voyage-ag2_tea_voyage---cash-crops-needing-ongoing-trade-not-one-trip) |
| `ag2_crown_cork` | 2 | 90.0 | [`ag2_bottling`](76_farming_food_deep.md#ag2_bottling-ag2_crown_cork---sealing-liquids-for-storage-and-transport) |
| `ag2_double_seam_can` | 2 | 100.0 | [`ag2_canning`](76_farming_food_deep.md#ag2_canning-ag2_retort-ag2_double_seam_can---preservation-that-worked-before-anyone-knew-why) |
| `ag2_fat_hydrogenation` | 2 | 120.0 | [`ag2_oil_pressing`](76_farming_food_deep.md#ag2_oil_pressing-ag2_fat_hydrogenation---extracting-and-modifying-fats) |
| `ag2_food_laboratory` | 2 | 120.0 | [`ag2_adulteration_law`](76_farming_food_deep.md#ag2_adulteration_law-ag2_food_laboratory---regulation-and-the-means-to-enforce-it) |
| `ag2_gasworks_ammonia` | 2 | 80.0 | [`ag2_gasworks_ammonia`](76_farming_food_deep.md#ag2_gasworks_ammonia-ag2_urea---synthetic-nitrogen) |
| `ag2_hybrid_maize` | 2 | 150.0 | [`ag2_record_keeping_breeding`](76_farming_food_deep.md#ag2_record_keeping_breeding-ag2_pure_line_selection-ag2_hybridisation-ag2_hybrid_maize-ag2_controlled_pollination---selection-and-breeding-as-bookkeeping) |
| `ag2_hybridisation` | 2 | 120.0 | [`ag2_record_keeping_breeding`](76_farming_food_deep.md#ag2_record_keeping_breeding-ag2_pure_line_selection-ag2_hybridisation-ag2_hybrid_maize-ag2_controlled_pollination---selection-and-breeding-as-bookkeeping) |
| `ag2_lead_arsenate` | 2 | 100.0 | [`ag2_bordeaux_mixture`](76_farming_food_deep.md#ag2_bordeaux_mixture-ag2_lime_sulphur-ag2_lead_arsenate-ag2_nicotine_pesticide-ag2_pyrethrum-ag2_ddt---pest-chemicals-oldest-to-most-dangerous) |
| `ag2_maize_newworld` | 2 | 65.0 | [`ag2_potato_newworld`](76_farming_food_deep.md#ag2_potato_newworld-ag2_maize_newworld---staple-crops-locked-behind-one-voyage) |
| `ag2_milking_machine` | 2 | 130.0 | [`ag2_milking_machine`](76_farming_food_deep.md#ag2_milking_machine-ag2_cream_separator-ag2_battery_poultry-ag2_silage_silo---dairy-poultry-and-fodder-at-scale) |
| `ag2_potato_newworld` | 2 | 70.0 | [`ag2_potato_newworld`](76_farming_food_deep.md#ag2_potato_newworld-ag2_maize_newworld---staple-crops-locked-behind-one-voyage) |
| `ag2_power_take_off` | 2 | 100.0 | [`ag2_tractor_steam`](76_farming_food_deep.md#ag2_tractor_steam-ag2_three_point_linkage-ag2_power_take_off-ag2_caterpillar_track---mechanising-traction) |
| `ag2_reaper_binder` | 2 | 180.0 | [`ag2_reaper`](76_farming_food_deep.md#ag2_reaper-ag2_reaper_binder-ag2_mower-ag2_tedder---cutting-and-handling-grain-and-hay) |
| `ag2_refrigerated_ship` | 2 | 140.0 | [`ag2_refrigeration_ice`](76_farming_food_deep.md#ag2_refrigeration_ice-ag2_refrigerated_ship-ag2_cold_store---the-cold-chain) |
| `ag2_resistant_variety` | 2 | 120.0 | [`ag2_sprayer`](76_farming_food_deep.md#ag2_sprayer-ag2_biological_control-ag2_resistant_variety---applying-and-avoiding-chemicals) |
| `ag2_rhizobia` | 2 | 150.0 | [`ag2_rhizobia`](76_farming_food_deep.md#ag2_rhizobia---legume-root-nodules-and-the-nitrogen-cycle-attributed) |
| `ag2_seed_certification` | 2 | 100.0 | [`ag2_seed_certification`](76_farming_food_deep.md#ag2_seed_certification-ag2_seed_trade---guaranteeing-what-is-in-the-sack) |
| `ag2_soil_testing` | 2 | 100.0 | [`ag2_liming`](76_farming_food_deep.md#ag2_liming-ag2_marling-ag2_soil_testing---reading-and-fixing-soil-chemistry) |
| `ag2_sugar_voyage` | 2 | 80.0 | [`ag2_sugar_voyage`](76_farming_food_deep.md#ag2_sugar_voyage-ag2_coffee_voyage-ag2_tea_voyage---cash-crops-needing-ongoing-trade-not-one-trip) |
| `ag2_tea_voyage` | 2 | 120.0 | [`ag2_sugar_voyage`](76_farming_food_deep.md#ag2_sugar_voyage-ag2_coffee_voyage-ag2_tea_voyage---cash-crops-needing-ongoing-trade-not-one-trip) |
| `ag2_three_point_linkage` | 2 | 90.0 | [`ag2_tractor_steam`](76_farming_food_deep.md#ag2_tractor_steam-ag2_three_point_linkage-ag2_power_take_off-ag2_caterpillar_track---mechanising-traction) |
| `ag2_tractor_steam` | 2 | 160.0 | [`ag2_tractor_steam`](76_farming_food_deep.md#ag2_tractor_steam-ag2_three_point_linkage-ag2_power_take_off-ag2_caterpillar_track---mechanising-traction) |
| `ag2_veterinary_vaccination` | 2 | 120.0 | [`ag2_tuberculin_test`](76_farming_food_deep.md#ag2_tuberculin_test-ag2_veterinary_vaccination-ag2_sheep_dip---disease-control-in-livestock) |
| `ag2_combine_harvester` | 3 | 400.0 | [`ag2_threshing_machine`](76_farming_food_deep.md#ag2_threshing_machine-ag2_combine_harvester---separating-grain-from-straw-by-machine) |
| `ag2_ddt` | 3 | 140.0 | [`ag2_bordeaux_mixture`](76_farming_food_deep.md#ag2_bordeaux_mixture-ag2_lime_sulphur-ag2_lead_arsenate-ag2_nicotine_pesticide-ag2_pyrethrum-ag2_ddt---pest-chemicals-oldest-to-most-dangerous) |
| `ag2_urea` | 3 | 60.0 | [`ag2_gasworks_ammonia`](76_farming_food_deep.md#ag2_gasworks_ammonia-ag2_urea---synthetic-nitrogen) |
| `fud_chinampa` | 4 | 120.0 | [`ag2_terracing`](76_farming_food_deep.md#ag2_erosion_control-ag2_terracing-ag2_contour_ploughing---keeping-soil-in-place) |

### 80_information_printing.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `prn_carbon_ink` | 0 | 0.0 | _(module has no anchor)_ |
| `prn_codex_bound` | 0 | 0.0 | _(module has no anchor)_ |
| `prn_mosaic_fresco` | 0 | 0.0 | _(module has no anchor)_ |
| `prn_papyrus_sheets` | 0 | 0.0 | _(module has no anchor)_ |
| `prn_parchment_sheets` | 0 | 0.0 | _(module has no anchor)_ |
| `prn_scribal_copying` | 0 | 0.0 | _(module has no anchor)_ |
| `prn_sculpture` | 0 | 0.0 | _(module has no anchor)_ |
| `prn_seals_stamps` | 0 | 0.0 | _(module has no anchor)_ |
| `prn_theatre_pantomime` | 0 | 0.0 | _(module has no anchor)_ |
| `prn_wax_tablets` | 0 | 0.0 | _(module has no anchor)_ |
| `corpus_written` | 1 | 6,000.0 | _(module has no anchor)_ |
| `if_daguerreotype` | 1 | 200.0 | _(module has no anchor)_ |
| `if_printing_ink` | 1 | 100.0 | _(module has no anchor)_ |
| `printing_press` | 1 | 900.0 | _(module has no anchor)_ |
| `prn_hand_papermaking` | 1 | 80.0 | _(module has no anchor)_ |
| `prn_magic_lantern` | 1 | 120.0 | _(module has no anchor)_ |
| `prn_pulp_stamper` | 1 | 100.0 | _(module has no anchor)_ |
| `prn_relief_printing` | 1 | 60.0 | _(module has no anchor)_ |
| `prn_sizing_surface` | 1 | 50.0 | _(module has no anchor)_ |
| `prn_wire_mould_deckle` | 1 | 150.0 | _(module has no anchor)_ |
| `prn_woodblock_carving` | 1 | 120.0 | _(module has no anchor)_ |
| `rag_paper` | 1 | 400.0 | _(module has no anchor)_ |
| `semaphore_telegraph` | 1 | 700.0 | _(module has no anchor)_ |
| `corpus_dispersed` | 2 | 800.0 | _(module has no anchor)_ |
| `goal_literacy_common` | 2 | 0.0 | [`literacy`](80_information_printing.md#literacy) **BROKEN** |
| `if_lithography` | 2 | 200.0 | _(module has no anchor)_ |
| `if_typewriter` | 2 | 300.0 | _(module has no anchor)_ |
| `prn_calotype_process` | 2 | 250.0 | _(module has no anchor)_ |
| `prn_cinema_projection` | 2 | 120.0 | _(module has no anchor)_ |
| `prn_cinema_shutter` | 2 | 100.0 | _(module has no anchor)_ |
| `prn_enlarger` | 2 | 150.0 | _(module has no anchor)_ |
| `prn_etching_technique` | 2 | 200.0 | _(module has no anchor)_ |
| `prn_film_studio` | 2 | 300.0 | _(module has no anchor)_ |
| `prn_hand_mould_adjustable` | 2 | 80.0 | _(module has no anchor)_ |
| `prn_intaglio_engraving` | 2 | 300.0 | _(module has no anchor)_ |
| `prn_intermittent_motion` | 2 | 180.0 | _(module has no anchor)_ |
| `prn_loudspeaker` | 2 | 120.0 | _(module has no anchor)_ |
| `prn_newspaper_institution` | 2 | 400.0 | _(module has no anchor)_ |
| `prn_nitrate_film_safety` | 2 | 100.0 | _(module has no anchor)_ |
| `prn_phonograph_cylinder` | 2 | 250.0 | _(module has no anchor)_ |
| `prn_platen_press` | 2 | 200.0 | _(module has no anchor)_ |
| `prn_stereotype_plate` | 2 | 120.0 | _(module has no anchor)_ |
| `prn_type_matrix` | 2 | 60.0 | _(module has no anchor)_ |
| `prn_type_metal_alloy` | 2 | 100.0 | _(module has no anchor)_ |
| `prn_type_punch` | 2 | 200.0 | _(module has no anchor)_ |
| `prn_wet_collodion_plate` | 2 | 200.0 | _(module has no anchor)_ |
| `prn_wood_pulp` | 2 | 120.0 | _(module has no anchor)_ |
| `if_cylinder_press` | 3 | 250.0 | _(module has no anchor)_ |
| `if_electrotype` | 3 | 150.0 | _(module has no anchor)_ |
| `if_rotary_press` | 3 | 300.0 | _(module has no anchor)_ |
| `prn_colour_photography` | 3 | 250.0 | _(module has no anchor)_ |
| `prn_electrical_recording` | 3 | 200.0 | _(module has no anchor)_ |
| `prn_four_colour_separation` | 3 | 200.0 | _(module has no anchor)_ |
| `prn_fourdrinier_machine` | 3 | 400.0 | _(module has no anchor)_ |
| `prn_offset_lithography` | 3 | 250.0 | _(module has no anchor)_ |
| `prn_radio_broadcasting` | 3 | 300.0 | _(module has no anchor)_ |
| `if_linotype_machine` | 4 | 600.0 | _(module has no anchor)_ |
| `prn_monotype_machine` | 4 | 500.0 | _(module has no anchor)_ |
| `goal_literate_nation` | 5 | 0.0 | [`literacy`](80_information_printing.md#literacy) **BROKEN** |

### 85_transport_civil.md

| Node | Your hours | Recipe |
|---|---:|---|
| `air_aerial_bombing` | 150.0 | _(module has no anchor)_ |
| `air_aerial_photography` | 120.0 | _(module has no anchor)_ |
| `air_aerodrome` | 100.0 | _(module has no anchor)_ |
| `air_aerofoil_section` | 200.0 | _(module has no anchor)_ |
| `air_aileron` | 140.0 | _(module has no anchor)_ |
| `air_airspeed_indicator` | 100.0 | _(module has no anchor)_ |
| `air_altimeter` | 120.0 | _(module has no anchor)_ |
| `air_artificial_horizon` | 250.0 | _(module has no anchor)_ |
| `air_autogyro` | 200.0 | _(module has no anchor)_ |
| `air_balloon_ballast` | 20.0 | _(module has no anchor)_ |
| `air_balloon_valve` | 60.0 | _(module has no anchor)_ |
| `air_biplane` | 140.0 | _(module has no anchor)_ |
| `air_cayley_forces` | 250.0 | _(module has no anchor)_ |
| `air_coal_gas_generation` | 180.0 | _(module has no anchor)_ |
| `air_compass_magnetic` | 30.0 | _(module has no anchor)_ |
| `air_dirigible_engine_mount` | 200.0 | _(module has no anchor)_ |
| `air_elevator_pitch` | 50.0 | _(module has no anchor)_ |
| `air_elongated_envelope` | 120.0 | _(module has no anchor)_ |
| `air_flying_boat` | 220.0 | _(module has no anchor)_ |
| `air_glider_simple` | 160.0 | _(module has no anchor)_ |
| `air_goldbeater_skin` | 200.0 | _(module has no anchor)_ |
| `air_helicopter_rotor` | 280.0 | _(module has no anchor)_ |
| `air_hydrogen_danger` | 100.0 | _(module has no anchor)_ |
| `air_hydrogen_generation_charcoal` | 100.0 | _(module has no anchor)_ |
| `air_jet_engine_build` | 350.0 | _(module has no anchor)_ |
| `air_jet_engine_concept` | 200.0 | _(module has no anchor)_ |
| `air_kite_basic` | 20.0 | _(module has no anchor)_ |
| `air_light_petrol_engine` | 250.0 | _(module has no anchor)_ |
| `air_monoplane_structure` | 200.0 | _(module has no anchor)_ |
| `air_observation_balloon_tethered` | 120.0 | _(module has no anchor)_ |
| `air_parachute` | 80.0 | _(module has no anchor)_ |
| `air_pitot_tube` | 80.0 | _(module has no anchor)_ |
| `air_power_to_weight` | 150.0 | _(module has no anchor)_ |
| `air_powered_aeroplane` | 300.0 | _(module has no anchor)_ |
| `air_propeller_wing` | 180.0 | _(module has no anchor)_ |
| `air_radial_engine` | 200.0 | _(module has no anchor)_ |
| `air_rigid_airship_frame` | 300.0 | _(module has no anchor)_ |
| `air_rotary_engine` | 220.0 | _(module has no anchor)_ |
| `air_rudder_vertical` | 60.0 | _(module has no anchor)_ |
| `air_stressed_skin_fuselage` | 180.0 | _(module has no anchor)_ |
| `air_three_axis_control` | 200.0 | _(module has no anchor)_ |
| `air_varnished_silk_envelope` | 150.0 | _(module has no anchor)_ |
| `air_wind_tunnel` | 150.0 | _(module has no anchor)_ |
| `air_wing_warping` | 120.0 | _(module has no anchor)_ |
| `civ_amphitheatre` | 0.0 | _(module has no anchor)_ |
| `civ_aqueduct_roman` | 300.0 | _(module has no anchor)_ |
| `civ_arch_roman` | 60.0 | _(module has no anchor)_ |
| `civ_brick_tile` | 40.0 | _(module has no anchor)_ |
| `civ_bridge_cantilever` | 250.0 | _(module has no anchor)_ |
| `civ_bridge_cast_iron` | 150.0 | _(module has no anchor)_ |
| `civ_bridge_suspension` | 300.0 | _(module has no anchor)_ |
| `civ_bridge_timber_truss` | 200.0 | _(module has no anchor)_ |
| `civ_bridge_wrought_iron_truss` | 200.0 | _(module has no anchor)_ |
| `civ_building_code` | 200.0 | _(module has no anchor)_ |
| `civ_caisson_compressed_air` | 200.0 | _(module has no anchor)_ |
| `civ_canal_pound_lock` | 150.0 | _(module has no anchor)_ |
| `civ_chorobates` | 25.0 | _(module has no anchor)_ |
| `civ_cofferdam` | 60.0 | _(module has no anchor)_ |
| `civ_dam_arch` | 250.0 | _(module has no anchor)_ |
| `civ_dam_earth_fill` | 150.0 | _(module has no anchor)_ |
| `civ_dam_gravity` | 200.0 | _(module has no anchor)_ |
| `civ_dome_roman` | 250.0 | _(module has no anchor)_ |
| `civ_dredging` | 200.0 | _(module has no anchor)_ |
| `civ_elevator_otis` | 250.0 | _(module has no anchor)_ |
| `civ_fireproofing` | 150.0 | _(module has no anchor)_ |
| `civ_foundation_piles` | 100.0 | _(module has no anchor)_ |
| `civ_foundation_spread` | 80.0 | _(module has no anchor)_ |
| `civ_gate_sluice` | 100.0 | _(module has no anchor)_ |
| `civ_glass_plate` | 100.0 | _(module has no anchor)_ |
| `civ_glass_windows` | 0.0 | _(module has no anchor)_ |
| `civ_harbour_dock` | 200.0 | _(module has no anchor)_ |
| `civ_insula` | 200.0 | _(module has no anchor)_ |
| `civ_iron_wrought` | 0.0 | _(module has no anchor)_ |
| `civ_lightning_conductor` | 80.0 | _(module has no anchor)_ |
| `civ_marble_facing` | 0.0 | _(module has no anchor)_ |
| `civ_precise_levelling` | 120.0 | _(module has no anchor)_ |
| `civ_pumping_station` | 150.0 | _(module has no anchor)_ |
| `civ_road_paved` | 150.0 | _(module has no anchor)_ |
| `civ_roof_king_post` | 80.0 | _(module has no anchor)_ |
| `civ_sewage_treatment` | 200.0 | _(module has no anchor)_ |
| `civ_sewer_roman` | 220.0 | _(module has no anchor)_ |
| `civ_sewer_separate` | 120.0 | _(module has no anchor)_ |
| `civ_steel_frame` | 300.0 | _(module has no anchor)_ |
| `civ_street_lighting` | 120.0 | _(module has no anchor)_ |
| `civ_street_paved` | 80.0 | _(module has no anchor)_ |
| `civ_surveying_groma` | 20.0 | _(module has no anchor)_ |
| `civ_town_planning` | 180.0 | _(module has no anchor)_ |
| `civ_truss_triangulated` | 120.0 | _(module has no anchor)_ |
| `civ_tunnel_rock_drill` | 180.0 | _(module has no anchor)_ |
| `civ_vault_barrel` | 0.0 | _(module has no anchor)_ |
| `civ_water_tower` | 100.0 | _(module has no anchor)_ |
| `civ_water_treatment` | 200.0 | _(module has no anchor)_ |
| `civ_wire_drawn` | 100.0 | _(module has no anchor)_ |
| `cn_arch_bridge_steel` | 250.0 | _(module has no anchor)_ |
| `cn_crane_treadwheel` | 55.0 | _(module has no anchor)_ |
| `cn_queen_post` | 100.0 | _(module has no anchor)_ |
| `hot_air_balloon` | 400.0 | _(module has no anchor)_ |
| `lnd_air_brake` | 250.0 | _(module has no anchor)_ |
| `lnd_assembly_line` | 600.0 | _(module has no anchor)_ |
| `lnd_automobile` | 500.0 | _(module has no anchor)_ |
| `lnd_axle_pivot_front` | 0.0 | _(module has no anchor)_ |
| `lnd_block_system` | 150.0 | _(module has no anchor)_ |
| `lnd_boneshaker` | 80.0 | _(module has no anchor)_ |
| `lnd_bridge` | 0.0 | _(module has no anchor)_ |
| `lnd_chain_drive_bicycle` | 100.0 | _(module has no anchor)_ |
| `lnd_coach` | 200.0 | _(module has no anchor)_ |
| `lnd_coal_tar_gas` | 80.0 | _(module has no anchor)_ |
| `lnd_cursus_publicus` | 0.0 | _(module has no anchor)_ |
| `lnd_diesel_cycle` | 400.0 | _(module has no anchor)_ |
| `lnd_diesel_supply` | 180.0 | _(module has no anchor)_ |
| `lnd_flanged_wheel` | 80.0 | _(module has no anchor)_ |
| `lnd_four_wheel_cart` | 0.0 | _(module has no anchor)_ |
| `lnd_gas_engine_atmospheric` | 250.0 | _(module has no anchor)_ |
| `lnd_gearbox_clutch` | 200.0 | _(module has no anchor)_ |
| `lnd_harness_throat_girth` | 0.0 | _(module has no anchor)_ |
| `lnd_hobby_horse` | 40.0 | _(module has no anchor)_ |
| `lnd_horse_saddle_basic` | 0.0 | _(module has no anchor)_ |
| `lnd_iron_edge_rail` | 80.0 | _(module has no anchor)_ |
| `lnd_litter` | 0.0 | _(module has no anchor)_ |
| `lnd_macadam` | 140.0 | _(module has no anchor)_ |
| `lnd_magneto` | 150.0 | _(module has no anchor)_ |
| `lnd_milestone` | 0.0 | _(module has no anchor)_ |
| `lnd_motor_road_network` | 250.0 | _(module has no anchor)_ |
| `lnd_mule_transport` | 0.0 | _(module has no anchor)_ |
| `lnd_otto_cycle_four_stroke` | 350.0 | _(module has no anchor)_ |
| `lnd_ox_transport` | 0.0 | _(module has no anchor)_ |
| `lnd_paved_road_network` | 0.0 | _(module has no anchor)_ |
| `lnd_point_switch` | 120.0 | _(module has no anchor)_ |
| `lnd_signal_railway` | 80.0 | _(module has no anchor)_ |
| `lnd_spring_leaf` | 80.0 | _(module has no anchor)_ |
| `lnd_stagecoach` | 250.0 | _(module has no anchor)_ |
| `lnd_standard_gauge` | 200.0 | _(module has no anchor)_ |
| `lnd_steam_locomotive` | 400.0 | _(module has no anchor)_ |
| `lnd_steering_geometry` | 100.0 | _(module has no anchor)_ |
| `lnd_tarmacadam` | 150.0 | _(module has no anchor)_ |
| `lnd_tender` | 120.0 | _(module has no anchor)_ |
| `lnd_truck` | 300.0 | _(module has no anchor)_ |
| `lnd_turnpike` | 50.0 | _(module has no anchor)_ |
| `lnd_two_wheel_cart` | 0.0 | _(module has no anchor)_ |
| `lnd_tyre_iron` | 0.0 | _(module has no anchor)_ |
| `lnd_wheel_spoked` | 0.0 | _(module has no anchor)_ |
| `lnd_wheelbarrow` | 30.0 | _(module has no anchor)_ |
| `railway` | 800.0 | _(module has no anchor)_ |
| `sea_anchor` | 0.0 | _(module has no anchor)_ |
| `sea_astronomical_tables` | 400.0 | _(module has no anchor)_ |
| `sea_backstaff` | 100.0 | _(module has no anchor)_ |
| `sea_bowsprit` | 60.0 | _(module has no anchor)_ |
| `sea_buoy` | 60.0 | _(module has no anchor)_ |
| `sea_charts_navigation` | 200.0 | _(module has no anchor)_ |
| `sea_coastal_pilotage` | 0.0 | _(module has no anchor)_ |
| `sea_compartmented_hull` | 150.0 | _(module has no anchor)_ |
| `sea_cross_staff` | 80.0 | _(module has no anchor)_ |
| `sea_diesel_engine` | 250.0 | _(module has no anchor)_ |
| `sea_diving_bell` | 120.0 | _(module has no anchor)_ |
| `sea_diving_suit` | 180.0 | _(module has no anchor)_ |
| `sea_dry_compass_card` | 60.0 | _(module has no anchor)_ |
| `sea_drydock` | 300.0 | _(module has no anchor)_ |
| `sea_electromagnetic_wave_theory` | 200.0 | _(module has no anchor)_ |
| `sea_fresnel_lens` | 180.0 | _(module has no anchor)_ |
| `sea_fuel_oil_burner` | 140.0 | _(module has no anchor)_ |
| `sea_harbours_pozzolana` | 0.0 | _(module has no anchor)_ |
| `sea_iron_hull` | 250.0 | _(module has no anchor)_ |
| `sea_jib` | 40.0 | _(module has no anchor)_ |
| `sea_lead_line_hydro` | 120.0 | _(module has no anchor)_ |
| `sea_lead_sheathing` | 0.0 | _(module has no anchor)_ |
| `sea_lodestone` | 20.0 | _(module has no anchor)_ |
| `sea_log_line` | 30.0 | _(module has no anchor)_ |
| `sea_lunar_distances` | 200.0 | _(module has no anchor)_ |
| `sea_magnetic_compass` | 80.0 | _(module has no anchor)_ |
| `sea_mercator_projection` | 180.0 | _(module has no anchor)_ |
| `sea_merchant_ships_large` | 0.0 | _(module has no anchor)_ |
| `sea_monsoon_route` | 0.0 | _(module has no anchor)_ |
| `sea_mortise_tenon` | 0.0 | _(module has no anchor)_ |
| `sea_multiple_masts` | 150.0 | _(module has no anchor)_ |
| `sea_pharos_lighthouse` | 0.0 | _(module has no anchor)_ |
| `sea_skeleton_first` | 250.0 | _(module has no anchor)_ |
| `sea_sonar` | 250.0 | _(module has no anchor)_ |
| `sea_sounding_lines` | 0.0 | _(module has no anchor)_ |
| `sea_spritsail` | 0.0 | _(module has no anchor)_ |
| `sea_square_sail` | 0.0 | _(module has no anchor)_ |
| `sea_steam_turbine` | 280.0 | _(module has no anchor)_ |
| `sea_steering_oars` | 0.0 | _(module has no anchor)_ |
| `sea_sternpost_rudder` | 120.0 | _(module has no anchor)_ |
| `sea_submarine` | 300.0 | _(module has no anchor)_ |
| `sea_traverse_board` | 40.0 | _(module has no anchor)_ |
| `tl_horseshoe` | 40.0 | _(module has no anchor)_ |
| `tr_fore_aft_rig` | 100.0 | _(module has no anchor)_ |
| `tr_lateen_sail` | 80.0 | _(module has no anchor)_ |
| `tr_screw_propeller` | 220.0 | _(module has no anchor)_ |

### 86_transport_deep.md

| Node | Your hours | Recipe |
|---|---:|---|
| `sea_clinker_hull` | 150.0 | [`tr_clinker_planking`](86_transport_deep.md#tr_carvel_planking---hull-planking-framing-and-caulking) |
| `sea_keel_deep` | 100.0 | [`tr_frame_first_construction`](86_transport_deep.md#tr_carvel_planking---hull-planking-framing-and-caulking) |
| `tl_air_filter` | 60.0 | [`tl_carburettor`](86_transport_deep.md#tl_carburettor---carburettor-fuel-atomiser) |
| `tl_anti_siphon_valve` | 50.0 | [`tl_carburettor`](86_transport_deep.md#tl_carburettor---carburettor-fuel-atomiser) |
| `tl_articulated_trailer` | 170.0 | [`tl_motor_lorry`](86_transport_deep.md#tl_motor_lorry---motor-lorry-and-heavy-road-vehicles) |
| `tl_automatic_transmission` | 200.0 | [`tl_plate_clutch`](86_transport_deep.md#tl_plate_clutch---plate-clutch-and-gearbox) |
| `tl_ball_bearing` | 150.0 | [`tl_ball_bearing`](86_transport_deep.md#tl_ball_bearing---ball-roller-and-taper-bearings) |
| `tl_brake_shoe` | 70.0 | [`tl_brake_shoe`](86_transport_deep.md#tl_brake_shoe---brake-shoe-on-a-drum) |
| `tl_caliper_brake` | 100.0 | [`tl_chain_drive`](86_transport_deep.md#tl_chain_drive---chain-drive-freewheel-and-gearing) |
| `tl_cam_follower` | 120.0 | [`tl_engine_block`](86_transport_deep.md#tl_engine_block---cast-engine-block) |
| `tl_cambered_drainage` | 80.0 | [`tl_macadam_road`](86_transport_deep.md#tl_macadam_road---macadam-and-bound-road-surfaces) |
| `tl_carbide_lamp` | 100.0 | [`tl_headlamp`](86_transport_deep.md#tl_headlamp---headlamp-and-signal-lighting) |
| `tl_carburettor` | 150.0 | [`tl_carburettor`](86_transport_deep.md#tl_carburettor---carburettor-fuel-atomiser) |
| `tl_caterpillar_track` | 200.0 | [`tl_motor_lorry`](86_transport_deep.md#tl_motor_lorry---motor-lorry-and-heavy-road-vehicles) |
| `tl_chain_drive` | 120.0 | [`tl_chain_drive`](86_transport_deep.md#tl_chain_drive---chain-drive-freewheel-and-gearing) |
| `tl_coil_ignition` | 140.0 | [`tl_magneto_ignition`](86_transport_deep.md#tl_magneto_ignition---magneto-ignition) |
| `tl_coil_spring` | 110.0 | [`tl_leaf_spring`](86_transport_deep.md#tl_leaf_spring---leaf-spring-suspension) |
| `tl_concrete_roadway` | 200.0 | [`tl_macadam_road`](86_transport_deep.md#tl_macadam_road---macadam-and-bound-road-surfaces) |
| `tl_cone_clutch` | 120.0 | [`tl_plate_clutch`](86_transport_deep.md#tl_plate_clutch---plate-clutch-and-gearbox) |
| `tl_connecting_rod` | 150.0 | [`tl_engine_block`](86_transport_deep.md#tl_engine_block---cast-engine-block) |
| `tl_cooling_fan` | 100.0 | [`tl_radiator`](86_transport_deep.md#tl_radiator---radiator-water-cooling) |
| `tl_dead_axle` | 60.0 | [`tl_differential`](86_transport_deep.md#tl_differential---differential-bevel-gears) |
| `tl_derailleur` | 140.0 | [`tl_chain_drive`](86_transport_deep.md#tl_chain_drive---chain-drive-freewheel-and-gearing) |
| `tl_differential` | 150.0 | [`tl_differential`](86_transport_deep.md#tl_differential---differential-bevel-gears) |
| `tl_disc_brake` | 150.0 | [`tl_brake_shoe`](86_transport_deep.md#tl_brake_shoe---brake-shoe-on-a-drum) |
| `tl_distributor` | 130.0 | [`tl_magneto_ignition`](86_transport_deep.md#tl_magneto_ignition---magneto-ignition) |
| `tl_drum_brake` | 120.0 | [`tl_brake_shoe`](86_transport_deep.md#tl_brake_shoe---brake-shoe-on-a-drum) |
| `tl_electric_starter` | 170.0 | [`tl_dynamo`](86_transport_deep.md#tl_dynamo---dynamo-and-electric-starting) |
| `tl_electric_tram` | 200.0 | [`tl_omnibus`](86_transport_deep.md#tl_omnibus---omnibus-and-public-transit) |
| `tl_elliptic_spring` | 120.0 | [`tl_leaf_spring`](86_transport_deep.md#tl_leaf_spring---leaf-spring-suspension) |
| `tl_engine_block` | 170.0 | [`tl_engine_block`](86_transport_deep.md#tl_engine_block---cast-engine-block) |
| `tl_epicyclic_gearbox` | 170.0 | [`tl_plate_clutch`](86_transport_deep.md#tl_plate_clutch---plate-clutch-and-gearbox) |
| `tl_exhaust_valve` | 150.0 | [`tl_intake_valve`](86_transport_deep.md#tl_intake_valve---poppet-valve-with-cam-and-spring) |
| `tl_fan_belt` | 100.0 | [`tl_radiator`](86_transport_deep.md#tl_radiator---radiator-water-cooling) |
| `tl_fifth_wheel` | 130.0 | [`tl_ackermann_steering`](86_transport_deep.md#tl_ackermann_steering---ackermann-steering-geometry) |
| `tl_freewheel` | 100.0 | [`tl_chain_drive`](86_transport_deep.md#tl_chain_drive---chain-drive-freewheel-and-gearing) |
| `tl_friction_damper` | 90.0 | [`tl_leaf_spring`](86_transport_deep.md#tl_leaf_spring---leaf-spring-suspension) |
| `tl_fuel_pump` | 100.0 | [`tl_carburettor`](86_transport_deep.md#tl_carburettor---carburettor-fuel-atomiser) |
| `tl_grease_cup` | 50.0 | [`tl_ball_bearing`](86_transport_deep.md#tl_ball_bearing---ball-roller-and-taper-bearings) |
| `tl_handbrake` | 70.0 | [`tl_brake_shoe`](86_transport_deep.md#tl_brake_shoe---brake-shoe-on-a-drum) |
| `tl_headlamp` | 120.0 | [`tl_headlamp`](86_transport_deep.md#tl_headlamp---headlamp-and-signal-lighting) |
| `tl_horse_tram` | 180.0 | [`tl_omnibus`](86_transport_deep.md#tl_omnibus---omnibus-and-public-transit) |
| `tl_hub_gear` | 160.0 | [`tl_chain_drive`](86_transport_deep.md#tl_chain_drive---chain-drive-freewheel-and-gearing) |
| `tl_hydraulic_brake_line` | 130.0 | [`tl_brake_shoe`](86_transport_deep.md#tl_brake_shoe---brake-shoe-on-a-drum) |
| `tl_hydraulic_shock` | 160.0 | [`tl_leaf_spring`](86_transport_deep.md#tl_leaf_spring---leaf-spring-suspension) |
| `tl_ignition_timing` | 110.0 | [`tl_magneto_ignition`](86_transport_deep.md#tl_magneto_ignition---magneto-ignition) |
| `tl_indicator` | 70.0 | [`tl_headlamp`](86_transport_deep.md#tl_headlamp---headlamp-and-signal-lighting) |
| `tl_inner_tube` | 120.0 | [`tl_pneumatic_tyre`](86_transport_deep.md#tl_pneumatic_tyre---pneumatic-tyre) |
| `tl_intake_valve` | 140.0 | [`tl_intake_valve`](86_transport_deep.md#tl_intake_valve---poppet-valve-with-cam-and-spring) |
| `tl_iron_tyre` | 100.0 | [`tl_spoked_wheel`](86_transport_deep.md#tl_spoked_wheel---improved-spoked-and-wire-spoke-wheel) |
| `tl_kerbing` | 60.0 | [`tl_macadam_road`](86_transport_deep.md#tl_macadam_road---macadam-and-bound-road-surfaces) |
| `tl_kingpin` | 80.0 | [`tl_ackermann_steering`](86_transport_deep.md#tl_ackermann_steering---ackermann-steering-geometry) |
| `tl_leaf_spring` | 100.0 | [`tl_leaf_spring`](86_transport_deep.md#tl_leaf_spring---leaf-spring-suspension) |
| `tl_level_crossing` | 120.0 | [`tl_road_roller`](86_transport_deep.md#tl_road_roller---steam-road-roller-and-level-crossings) |
| `tl_live_axle` | 120.0 | [`tl_differential`](86_transport_deep.md#tl_differential---differential-bevel-gears) |
| `tl_magneto_ignition` | 160.0 | [`tl_magneto_ignition`](86_transport_deep.md#tl_magneto_ignition---magneto-ignition) |
| `tl_motor_dc` | 140.0 | [`tl_dynamo`](86_transport_deep.md#tl_dynamo---dynamo-and-electric-starting) |
| `tl_motor_lorry` | 240.0 | [`tl_motor_lorry`](86_transport_deep.md#tl_motor_lorry---motor-lorry-and-heavy-road-vehicles) |
| `tl_motorcycle` | 180.0 | [`tl_omnibus`](86_transport_deep.md#tl_omnibus---omnibus-and-public-transit) |
| `tl_muffler` | 80.0 | [`tl_muffler`](86_transport_deep.md#tl_muffler---muffler-and-windscreen-wiper) |
| `tl_oil_bath` | 80.0 | [`tl_ball_bearing`](86_transport_deep.md#tl_ball_bearing---ball-roller-and-taper-bearings) |
| `tl_oil_pump` | 120.0 | [`tl_oil_pump`](86_transport_deep.md#tl_oil_pump---pressure-oil-pump) |
| `tl_omnibus` | 250.0 | [`tl_omnibus`](86_transport_deep.md#tl_omnibus---omnibus-and-public-transit) |
| `tl_penny_farthing` | 110.0 | [`tl_safety_bicycle`](86_transport_deep.md#tl_safety_bicycle---safety-bicycle-and-its-ancestors) |
| `tl_piston_assembly` | 160.0 | [`tl_engine_block`](86_transport_deep.md#tl_engine_block---cast-engine-block) |
| `tl_plain_bearing` | 70.0 | [`tl_ball_bearing`](86_transport_deep.md#tl_ball_bearing---ball-roller-and-taper-bearings) |
| `tl_plate_clutch` | 130.0 | [`tl_plate_clutch`](86_transport_deep.md#tl_plate_clutch---plate-clutch-and-gearbox) |
| `tl_pneumatic_tyre` | 160.0 | [`tl_pneumatic_tyre`](86_transport_deep.md#tl_pneumatic_tyre---pneumatic-tyre) |
| `tl_pressure_relief_valve` | 90.0 | [`tl_oil_pump`](86_transport_deep.md#tl_oil_pump---pressure-oil-pump) |
| `tl_propshaft` | 100.0 | [`tl_differential`](86_transport_deep.md#tl_differential---differential-bevel-gears) |
| `tl_radiator` | 140.0 | [`tl_radiator`](86_transport_deep.md#tl_radiator---radiator-water-cooling) |
| `tl_road_roller` | 160.0 | [`tl_road_roller`](86_transport_deep.md#tl_road_roller---steam-road-roller-and-level-crossings) |
| `tl_roller_bearing` | 120.0 | [`tl_ball_bearing`](86_transport_deep.md#tl_ball_bearing---ball-roller-and-taper-bearings) |
| `tl_safety_bicycle` | 130.0 | [`tl_safety_bicycle`](86_transport_deep.md#tl_safety_bicycle---safety-bicycle-and-its-ancestors) |
| `tl_shrink_fit` | 120.0 | [`tl_spoked_wheel`](86_transport_deep.md#tl_spoked_wheel---improved-spoked-and-wire-spoke-wheel) |
| `tl_sliding_gearbox` | 140.0 | [`tl_plate_clutch`](86_transport_deep.md#tl_plate_clutch---plate-clutch-and-gearbox) |
| `tl_snow_plough` | 150.0 | [`tl_motor_lorry`](86_transport_deep.md#tl_motor_lorry---motor-lorry-and-heavy-road-vehicles) |
| `tl_solid_rubber_tyre` | 100.0 | [`tl_pneumatic_tyre`](86_transport_deep.md#tl_pneumatic_tyre---pneumatic-tyre) |
| `tl_spark_plug` | 120.0 | [`tl_magneto_ignition`](86_transport_deep.md#tl_magneto_ignition---magneto-ignition) |
| `tl_spoked_wheel` | 80.0 | [`tl_spoked_wheel`](86_transport_deep.md#tl_spoked_wheel---improved-spoked-and-wire-spoke-wheel) |
| `tl_steam_tram` | 220.0 | [`tl_omnibus`](86_transport_deep.md#tl_omnibus---omnibus-and-public-transit) |
| `tl_stirrup` | 60.0 | [`tl_horse_collar`](86_transport_deep.md#tl_horse_collar---horse-collar-horseshoe-stirrup-and-harness) |
| `tl_synchromesh` | 160.0 | [`tl_plate_clutch`](86_transport_deep.md#tl_plate_clutch---plate-clutch-and-gearbox) |
| `tl_tandem_harness` | 70.0 | [`tl_horse_collar`](86_transport_deep.md#tl_horse_collar---horse-collar-horseshoe-stirrup-and-harness) |
| `tl_taper_roller_bearing` | 180.0 | [`tl_ball_bearing`](86_transport_deep.md#tl_ball_bearing---ball-roller-and-taper-bearings) |
| `tl_thermostat` | 90.0 | [`tl_radiator`](86_transport_deep.md#tl_radiator---radiator-water-cooling) |
| `tl_throttle` | 80.0 | [`tl_carburettor`](86_transport_deep.md#tl_carburettor---carburettor-fuel-atomiser) |
| `tl_tractor` | 350.0 | [`tl_motor_lorry`](86_transport_deep.md#tl_motor_lorry---motor-lorry-and-heavy-road-vehicles) |
| `tl_transmission_lubrication` | 70.0 | [`tl_oil_pump`](86_transport_deep.md#tl_oil_pump---pressure-oil-pump) |
| `tl_trolleybus` | 210.0 | [`tl_omnibus`](86_transport_deep.md#tl_omnibus---omnibus-and-public-transit) |
| `tl_tyre_bead` | 100.0 | [`tl_pneumatic_tyre`](86_transport_deep.md#tl_pneumatic_tyre---pneumatic-tyre) |
| `tl_tyre_tread` | 110.0 | [`tl_pneumatic_tyre`](86_transport_deep.md#tl_pneumatic_tyre---pneumatic-tyre) |
| `tl_universal_joint` | 110.0 | [`tl_differential`](86_transport_deep.md#tl_differential---differential-bevel-gears) |
| `tl_velocipede` | 100.0 | [`tl_safety_bicycle`](86_transport_deep.md#tl_safety_bicycle---safety-bicycle-and-its-ancestors) |
| `tl_vulcanized_rubber` | 140.0 | [`tl_pneumatic_tyre`](86_transport_deep.md#tl_pneumatic_tyre---pneumatic-tyre) |
| `tl_water_pump` | 110.0 | [`tl_radiator`](86_transport_deep.md#tl_radiator---radiator-water-cooling) |
| `tl_whippletree` | 60.0 | [`tl_horse_collar`](86_transport_deep.md#tl_horse_collar---horse-collar-horseshoe-stirrup-and-harness) |
| `tl_windscreen_wiper` | 100.0 | [`tl_muffler`](86_transport_deep.md#tl_muffler---muffler-and-windscreen-wiper) |
| `tl_wire_rope_brake` | 60.0 | [`tl_brake_shoe`](86_transport_deep.md#tl_brake_shoe---brake-shoe-on-a-drum) |
| `tl_wire_spoke_wheel` | 120.0 | [`tl_spoked_wheel`](86_transport_deep.md#tl_spoked_wheel---improved-spoked-and-wire-spoke-wheel) |
| `tr_articulated_locomotive` | 200.0 | [`tr_slide_valve`](86_transport_deep.md#tr_slide_valve---slide-valve-piston-valve-and-valve-gear) |
| `tr_automatic_train_stop` | 200.0 | [`tr_semaphore_signal`](86_transport_deep.md#tr_semaphore_signal---semaphore-block-and-interlocking-signalling) |
| `tr_axle_bearing_box` | 60.0 | [`tr_flanged_wheel`](86_transport_deep.md#tr_flanged_wheel---flanged-wheel-axle-box-and-bogie) |
| `tr_ballast_tank` | 120.0 | [`tr_windlass`](86_transport_deep.md#tr_windlass---deck-machinery-windlass-capstan-anchor-chain-bilge-pump-ballast-block-and-tackle) |
| `tr_bilge_pump` | 50.0 | [`tr_windlass`](86_transport_deep.md#tr_windlass---deck-machinery-windlass-capstan-anchor-chain-bilge-pump-ballast-block-and-tackle) |
| `tr_blastpipe` | 50.0 | [`tr_locomotive_boiler`](86_transport_deep.md#tr_locomotive_boiler---locomotive-boiler-smokebox-blastpipe-superheater-injector) |
| `tr_block_signalling` | 100.0 | [`tr_semaphore_signal`](86_transport_deep.md#tr_semaphore_signal---semaphore-block-and-interlocking-signalling) |
| `tr_block_tackle` | 40.0 | [`tr_windlass`](86_transport_deep.md#tr_windlass---deck-machinery-windlass-capstan-anchor-chain-bilge-pump-ballast-block-and-tackle) |
| `tr_bogie_truck` | 120.0 | [`tr_flanged_wheel`](86_transport_deep.md#tr_flanged_wheel---flanged-wheel-axle-box-and-bogie) |
| `tr_bullhead_rail` | 70.0 | [`tr_edge_rail`](86_transport_deep.md#tr_edge_rail---edge-rail-bullhead-and-flat-bottom-profiles) |
| `tr_canal_lift` | 250.0 | [`tr_canal_lock`](86_transport_deep.md#tr_canal_lock---canal-lock-and-canal-lift) |
| `tr_canal_lock` | 250.0 | [`tr_canal_lock`](86_transport_deep.md#tr_canal_lock---canal-lock-and-canal-lift) |
| `tr_capstan` | 80.0 | [`tr_windlass`](86_transport_deep.md#tr_windlass---deck-machinery-windlass-capstan-anchor-chain-bilge-pump-ballast-block-and-tackle) |
| `tr_carvel_planking` | 200.0 | [`tr_carvel_planking`](86_transport_deep.md#tr_carvel_planking---hull-planking-framing-and-caulking) |
| `tr_catenary_overhead` | 150.0 | [`tr_electric_locomotive`](86_transport_deep.md#tr_electric_locomotive---electric-and-diesel-electric-traction) |
| `tr_caulking_oakum` | 60.0 | [`tr_carvel_planking`](86_transport_deep.md#tr_carvel_planking---hull-planking-framing-and-caulking) |
| `tr_chain_cable` | 80.0 | [`tr_windlass`](86_transport_deep.md#tr_windlass---deck-machinery-windlass-capstan-anchor-chain-bilge-pump-ballast-block-and-tackle) |
| `tr_chair_key` | 50.0 | [`tr_edge_rail`](86_transport_deep.md#tr_edge_rail---edge-rail-bullhead-and-flat-bottom-profiles) |
| `tr_clinker_planking` | 100.0 | [`tr_carvel_planking`](86_transport_deep.md#tr_carvel_planking---hull-planking-framing-and-caulking) |
| `tr_compound_expansion` | 300.0 | [`tr_slide_valve`](86_transport_deep.md#tr_slide_valve---slide-valve-piston-valve-and-valve-gear) |
| `tr_copper_sheathing` | 180.0 | [`tr_carvel_planking`](86_transport_deep.md#tr_carvel_planking---hull-planking-framing-and-caulking) |
| `tr_diesel_electric` | 250.0 | [`tr_electric_locomotive`](86_transport_deep.md#tr_electric_locomotive---electric-and-diesel-electric-traction) |
| `tr_double_bottom` | 150.0 | [`tr_iron_hull`](86_transport_deep.md#tr_iron_hull---iron-and-steel-hull-plating-and-bulkheads) |
| `tr_dredger` | 200.0 | [`tr_dry_dock`](86_transport_deep.md#tr_dry_dock---shipyard-infrastructure-dry-dock-slipway-tugs-dredging) |
| `tr_dry_dock` | 200.0 | [`tr_dry_dock`](86_transport_deep.md#tr_dry_dock---shipyard-infrastructure-dry-dock-slipway-tugs-dredging) |
| `tr_electric_locomotive` | 200.0 | [`tr_electric_locomotive`](86_transport_deep.md#tr_electric_locomotive---electric-and-diesel-electric-traction) |
| `tr_fishplate` | 50.0 | [`tr_edge_rail`](86_transport_deep.md#tr_edge_rail---edge-rail-bullhead-and-flat-bottom-profiles) |
| `tr_flatbottom_rail` | 90.0 | [`tr_edge_rail`](86_transport_deep.md#tr_edge_rail---edge-rail-bullhead-and-flat-bottom-profiles) |
| `tr_fore_and_aft_rigging` | 100.0 | [`tr_square_rig`](86_transport_deep.md#tr_square_rig---sail-plans-square-lateen-fore-and-aft-jib-staysail-reefing) |
| `tr_frame_first_construction` | 80.0 | [`tr_carvel_planking`](86_transport_deep.md#tr_carvel_planking---hull-planking-framing-and-caulking) |
| `tr_grade_crossing` | 80.0 | [`tr_points_frog`](86_transport_deep.md#tr_points_frog---points-frog-turntable-and-yard-switching) |
| `tr_gyrocompass_repeater` | 150.0 | [`tr_marine_chronometer`](86_transport_deep.md#tr_marine_chronometer---navigation-instruments-chronometer-sextant-gyrocompass-log-lighthouse-ship-telegraph) |
| `tr_hopper_wagon` | 50.0 | [`tr_hopper_wagon`](86_transport_deep.md#tr_hopper_wagon---specialised-wagons-hopper-tank-refrigerated-sleeping-car) |
| `tr_hull_sheathing_wood` | 100.0 | [`tr_carvel_planking`](86_transport_deep.md#tr_carvel_planking---hull-planking-framing-and-caulking) |
| `tr_injector_feedwater` | 100.0 | [`tr_locomotive_boiler`](86_transport_deep.md#tr_locomotive_boiler---locomotive-boiler-smokebox-blastpipe-superheater-injector) |
| `tr_interlocking_signal` | 180.0 | [`tr_semaphore_signal`](86_transport_deep.md#tr_semaphore_signal---semaphore-block-and-interlocking-signalling) |
| `tr_jib` | 30.0 | [`tr_square_rig`](86_transport_deep.md#tr_square_rig---sail-plans-square-lateen-fore-and-aft-jib-staysail-reefing) |
| `tr_keelson` | 80.0 | [`tr_carvel_planking`](86_transport_deep.md#tr_carvel_planking---hull-planking-framing-and-caulking) |
| `tr_knuckle_coupler` | 150.0 | [`tr_screw_coupling`](86_transport_deep.md#tr_screw_coupling---screw-coupling-buffer-and-knuckle-coupler) |
| `tr_leading_truck` | 80.0 | [`tr_flanged_wheel`](86_transport_deep.md#tr_flanged_wheel---flanged-wheel-axle-box-and-bogie) |
| `tr_lifeboat` | 100.0 | [`tr_lifeboat`](86_transport_deep.md#tr_lifeboat---lifeboat-submarine-hull-and-periscope) |
| `tr_locomotive_boiler` | 150.0 | [`tr_locomotive_boiler`](86_transport_deep.md#tr_locomotive_boiler---locomotive-boiler-smokebox-blastpipe-superheater-injector) |
| `tr_log_sounding` | 50.0 | [`tr_marine_chronometer`](86_transport_deep.md#tr_marine_chronometer---navigation-instruments-chronometer-sextant-gyrocompass-log-lighthouse-ship-telegraph) |
| `tr_marine_diesel` | 200.0 | [`tr_marine_engine`](86_transport_deep.md#tr_marine_engine---marine-steam-and-diesel-propulsion-machinery) |
| `tr_marine_engine` | 180.0 | [`tr_marine_engine`](86_transport_deep.md#tr_marine_engine---marine-steam-and-diesel-propulsion-machinery) |
| `tr_marine_turbine` | 250.0 | [`tr_marine_engine`](86_transport_deep.md#tr_marine_engine---marine-steam-and-diesel-propulsion-machinery) |
| `tr_marshalling_hump` | 100.0 | [`tr_points_frog`](86_transport_deep.md#tr_points_frog---points-frog-turntable-and-yard-switching) |
| `tr_mast_stepping` | 80.0 | [`tr_bowsprit`](86_transport_deep.md#tr_bowsprit---bowsprit-mast-stepping-and-rigging-hardware) |
| `tr_paddle_wheel` | 200.0 | [`tr_sternpost_rudder`](86_transport_deep.md#tr_sternpost_rudder---propulsion-rudder-propeller-and-shafting) |
| `tr_pantograph` | 100.0 | [`tr_electric_locomotive`](86_transport_deep.md#tr_electric_locomotive---electric-and-diesel-electric-traction) |
| `tr_piston_valve` | 100.0 | [`tr_slide_valve`](86_transport_deep.md#tr_slide_valve---slide-valve-piston-valve-and-valve-gear) |
| `tr_points_frog` | 120.0 | [`tr_points_frog`](86_transport_deep.md#tr_points_frog---points-frog-turntable-and-yard-switching) |
| `tr_rail_gauge_standardization` | 40.0 | [`tr_sleeper_ballast`](86_transport_deep.md#tr_sleeper_ballast---sleeper-ballast-and-track-gauge) |
| `tr_rail_rolling` | 120.0 | [`tr_edge_rail`](86_transport_deep.md#tr_edge_rail---edge-rail-bullhead-and-flat-bottom-profiles) |
| `tr_rail_welding` | 150.0 | [`tr_edge_rail`](86_transport_deep.md#tr_edge_rail---edge-rail-bullhead-and-flat-bottom-profiles) |
| `tr_reduction_gearing` | 200.0 | [`tr_sternpost_rudder`](86_transport_deep.md#tr_sternpost_rudder---propulsion-rudder-propeller-and-shafting) |
| `tr_reefing` | 50.0 | [`tr_square_rig`](86_transport_deep.md#tr_square_rig---sail-plans-square-lateen-fore-and-aft-jib-staysail-reefing) |
| `tr_refrigerated_wagon` | 80.0 | [`tr_hopper_wagon`](86_transport_deep.md#tr_hopper_wagon---specialised-wagons-hopper-tank-refrigerated-sleeping-car) |
| `tr_rigging_block_lashing` | 60.0 | [`tr_bowsprit`](86_transport_deep.md#tr_bowsprit---bowsprit-mast-stepping-and-rigging-hardware) |
| `tr_riveted_plating` | 150.0 | [`tr_iron_hull`](86_transport_deep.md#tr_iron_hull---iron-and-steel-hull-plating-and-bulkheads) |
| `tr_screw_coupling` | 40.0 | [`tr_screw_coupling`](86_transport_deep.md#tr_screw_coupling---screw-coupling-buffer-and-knuckle-coupler) |
| `tr_semaphore_signal` | 40.0 | [`tr_semaphore_signal`](86_transport_deep.md#tr_semaphore_signal---semaphore-block-and-interlocking-signalling) |
| `tr_sextant_navigation` | 110.0 | [`tr_marine_chronometer`](86_transport_deep.md#tr_marine_chronometer---navigation-instruments-chronometer-sextant-gyrocompass-log-lighthouse-ship-telegraph) |
| `tr_ship_telegraph` | 60.0 | [`tr_marine_chronometer`](86_transport_deep.md#tr_marine_chronometer---navigation-instruments-chronometer-sextant-gyrocompass-log-lighthouse-ship-telegraph) |
| `tr_sleeper_ballast` | 30.0 | [`tr_sleeper_ballast`](86_transport_deep.md#tr_sleeper_ballast---sleeper-ballast-and-track-gauge) |
| `tr_sleeping_car` | 60.0 | [`tr_hopper_wagon`](86_transport_deep.md#tr_hopper_wagon---specialised-wagons-hopper-tank-refrigerated-sleeping-car) |
| `tr_slide_valve` | 70.0 | [`tr_slide_valve`](86_transport_deep.md#tr_slide_valve---slide-valve-piston-valve-and-valve-gear) |
| `tr_slipway_launch` | 80.0 | [`tr_dry_dock`](86_transport_deep.md#tr_dry_dock---shipyard-infrastructure-dry-dock-slipway-tugs-dredging) |
| `tr_smoke_box` | 70.0 | [`tr_locomotive_boiler`](86_transport_deep.md#tr_locomotive_boiler---locomotive-boiler-smokebox-blastpipe-superheater-injector) |
| `tr_sprung_buffer` | 50.0 | [`tr_screw_coupling`](86_transport_deep.md#tr_screw_coupling---screw-coupling-buffer-and-knuckle-coupler) |
| `tr_square_rig` | 40.0 | [`tr_square_rig`](86_transport_deep.md#tr_square_rig---sail-plans-square-lateen-fore-and-aft-jib-staysail-reefing) |
| `tr_staysail` | 40.0 | [`tr_square_rig`](86_transport_deep.md#tr_square_rig---sail-plans-square-lateen-fore-and-aft-jib-staysail-reefing) |
| `tr_steel_hull` | 250.0 | [`tr_iron_hull`](86_transport_deep.md#tr_iron_hull---iron-and-steel-hull-plating-and-bulkheads) |
| `tr_stephenson_linkmotion` | 120.0 | [`tr_slide_valve`](86_transport_deep.md#tr_slide_valve---slide-valve-piston-valve-and-valve-gear) |
| `tr_stern_tube` | 100.0 | [`tr_sternpost_rudder`](86_transport_deep.md#tr_sternpost_rudder---propulsion-rudder-propeller-and-shafting) |
| `tr_stockless_anchor` | 100.0 | [`tr_windlass`](86_transport_deep.md#tr_windlass---deck-machinery-windlass-capstan-anchor-chain-bilge-pump-ballast-block-and-tackle) |
| `tr_submarine_hull` | 250.0 | [`tr_lifeboat`](86_transport_deep.md#tr_lifeboat---lifeboat-submarine-hull-and-periscope) |
| `tr_superheater` | 200.0 | [`tr_locomotive_boiler`](86_transport_deep.md#tr_locomotive_boiler---locomotive-boiler-smokebox-blastpipe-superheater-injector) |
| `tr_tank_wagon` | 100.0 | [`tr_hopper_wagon`](86_transport_deep.md#tr_hopper_wagon---specialised-wagons-hopper-tank-refrigerated-sleeping-car) |
| `tr_third_rail` | 80.0 | [`tr_electric_locomotive`](86_transport_deep.md#tr_electric_locomotive---electric-and-diesel-electric-traction) |
| `tr_track_circuit` | 120.0 | [`tr_semaphore_signal`](86_transport_deep.md#tr_semaphore_signal---semaphore-block-and-interlocking-signalling) |
| `tr_triple_expansion` | 200.0 | [`tr_marine_engine`](86_transport_deep.md#tr_marine_engine---marine-steam-and-diesel-propulsion-machinery) |
| `tr_tug` | 100.0 | [`tr_dry_dock`](86_transport_deep.md#tr_dry_dock---shipyard-infrastructure-dry-dock-slipway-tugs-dredging) |
| `tr_turntable` | 100.0 | [`tr_points_frog`](86_transport_deep.md#tr_points_frog---points-frog-turntable-and-yard-switching) |
| `tr_vacuum_brake` | 100.0 | [`tr_brake_shoe`](86_transport_deep.md#tr_brake_shoe---rail-brake-shoe-vacuum-and-westinghouse-air-brake) |
| `tr_variable_pitch_propeller` | 180.0 | [`tr_sternpost_rudder`](86_transport_deep.md#tr_sternpost_rudder---propulsion-rudder-propeller-and-shafting) |
| `tr_walschaerts_valve` | 140.0 | [`tr_slide_valve`](86_transport_deep.md#tr_slide_valve---slide-valve-piston-valve-and-valve-gear) |
| `tr_watertight_bulkhead` | 70.0 | [`tr_iron_hull`](86_transport_deep.md#tr_iron_hull---iron-and-steel-hull-plating-and-bulkheads) |
| `tr_welded_hull` | 200.0 | [`tr_iron_hull`](86_transport_deep.md#tr_iron_hull---iron-and-steel-hull-plating-and-bulkheads) |
| `tr_westinghouse_brake` | 180.0 | [`tr_brake_shoe`](86_transport_deep.md#tr_brake_shoe---rail-brake-shoe-vacuum-and-westinghouse-air-brake) |
| `tr_windlass` | 100.0 | [`tr_windlass`](86_transport_deep.md#tr_windlass---deck-machinery-windlass-capstan-anchor-chain-bilge-pump-ballast-block-and-tackle) |
| `tr_wooden_waggonway` | 40.0 | [`tr_sleeper_ballast`](86_transport_deep.md#tr_sleeper_ballast---sleeper-ballast-and-track-gauge) |

### 87_construction.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `cn_aqueduct` | 0 | 110.0 | [`cn_aqueduct`](87_construction.md#cn_aqueduct---masonry-aqueduct-arch-bridge-aqua-ducta) |
| `cn_block_tackle_hoist` | 0 | 30.0 | [`cn_crane_treadwheel`](87_construction.md#cn_crane_treadwheel---treadwheel-crane-polyspastos) |
| `cn_damp_proof_course` | 0 | 50.0 | [`cn_cavity_wall`](87_construction.md#cn_cavity_wall---cavity-wall-damp-proof-course-insulation) |
| `cn_gypsum_plaster` | 0 | 35.0 | [`cn_portland_cement`](87_construction.md#cn_portland_cement---portland-cement-powder) |
| `cn_mortar` | 0 | 80.0 | [`cn_pozzolana_concrete`](87_construction.md#cn_pozzolana_concrete---pozzolana-hydraulic-concrete-opus-caementicium) |
| `cn_pile_driving` | 0 | 40.0 | [`cn_pile_driving`](87_construction.md#cn_pile_driving---pile-driving-screw-piles-soil-compaction) |
| `cn_post_lintel` | 0 | 25.0 | [`cn_post_lintel`](87_construction.md#cn_post_lintel---post-and-lintel-the-theory-of-the-beam) |
| `cn_quarrying_wedge` | 0 | 20.0 | [`cn_quarrying_wedge`](87_construction.md#cn_quarrying_wedge---stone-quarrying-with-wedges) |
| `cn_retaining_wall` | 0 | 80.0 | [`cn_gravity_dam`](87_construction.md#cn_gravity_dam---gravity-dam-arch-dam-earth-dam-spillway-retaining-wall) |
| `cn_scaffolding` | 0 | 50.0 | [`cn_scaffolding`](87_construction.md#cn_scaffolding---timber-scaffolding-system) |
| `cn_stone_polish` | 0 | 30.0 | [`cn_quarrying_wedge`](87_construction.md#cn_quarrying_wedge---stone-quarrying-with-wedges) |
| `cn_stone_saw` | 0 | 40.0 | [`cn_quarrying_wedge`](87_construction.md#cn_quarrying_wedge---stone-quarrying-with-wedges) |
| `cn_timber_truss` | 0 | 45.0 | [`cn_king_post`](87_construction.md#cn_king_post---king-post-roof-truss) |
| `cn_true_arch` | 0 | 35.0 | [`cn_true_arch`](87_construction.md#cn_true_arch---true-arch-in-stone-fornix) |
| `mat_pozzolana` | 0 | 50.0 | [`cn_pozzolana_concrete`](87_construction.md#cn_pozzolana_concrete---pozzolana-hydraulic-concrete-opus-caementicium) |
| `civ_monumental_stone` | 1 | 150.0 | [`cn_quarry_wedge`](87_construction.md#cn_quarry_wedge) **BROKEN** |
| `cn_artificial_stone` | 1 | 70.0 | [`cn_portland_cement`](87_construction.md#cn_portland_cement---portland-cement-powder) |
| `cn_caisson` | 1 | 150.0 | [`cn_caisson`](87_construction.md#cn_caisson---caisson-pneumatic-caisson-underpinning) |
| `cn_cavity_wall` | 1 | 75.0 | [`cn_cavity_wall`](87_construction.md#cn_cavity_wall---cavity-wall-damp-proof-course-insulation) |
| `cn_crane_derrick` | 1 | 75.0 | [`cn_crane_derrick`](87_construction.md#cn_crane_derrick---derrick-and-tower-cranes-elevator-safety-brake) |
| `cn_dewatering` | 1 | 85.0 | [`cn_cofferdam`](87_construction.md#cn_cofferdam---cofferdam-dewatering-diaphragm-wall-sheet-piling) |
| `cn_earth_dam` | 1 | 100.0 | [`cn_gravity_dam`](87_construction.md#cn_gravity_dam---gravity-dam-arch-dam-earth-dam-spillway-retaining-wall) |
| `cn_expansion_joint` | 1 | 75.0 | [`cn_concrete_mixer`](87_construction.md#cn_concrete_mixer---concrete-mixing-and-placing-at-scale) |
| `cn_fire_escape` | 1 | 75.0 | [`cn_fire_escape`](87_construction.md#cn_fire_escape---fire-escape-and-automatic-sprinklers) |
| `cn_flying_buttress` | 1 | 90.0 | [`cn_true_arch`](87_construction.md#cn_true_arch---true-arch-in-stone-fornix) |
| `cn_formwork_shuttering` | 1 | 95.0 | [`cn_concrete_mixer`](87_construction.md#cn_concrete_mixer---concrete-mixing-and-placing-at-scale) |
| `cn_gang_saw` | 1 | 80.0 | [`cn_quarrying_wedge`](87_construction.md#cn_quarrying_wedge---stone-quarrying-with-wedges) |
| `cn_gravity_dam` | 1 | 120.0 | [`cn_gravity_dam`](87_construction.md#cn_gravity_dam---gravity-dam-arch-dam-earth-dam-spillway-retaining-wall) |
| `cn_groin_vault` | 1 | 100.0 | [`cn_true_arch`](87_construction.md#cn_true_arch---true-arch-in-stone-fornix) |
| `cn_gusset_plate` | 1 | 60.0 | [`cn_riveted_connection`](87_construction.md#cn_riveted_connection---riveted-bolted-gusseted-and-welded-joints) |
| `cn_iron_column` | 1 | 65.0 | [`cn_cast_iron_beam`](87_construction.md#cn_cast_iron_beam---cast-iron-beam) |
| `cn_lattice_truss` | 1 | 70.0 | [`cn_pratt_truss`](87_construction.md#cn_wrought_iron_girder---wrought-iron-girder-and-later-steel) |
| `cn_plumbing_stack` | 1 | 80.0 | [`cn_plumbing_stack`](87_construction.md#cn_plumbing_stack---plumbing-stack-and-trapped-drains) |
| `cn_pontoon_bridge` | 1 | 85.0 | [`cn_bascule_bridge`](87_construction.md#cn_bascule_bridge---bascule-swing-and-pontoon-bridges) |
| `cn_ribbed_vault` | 1 | 120.0 | [`cn_true_arch`](87_construction.md#cn_true_arch---true-arch-in-stone-fornix) |
| `cn_riveted_connection` | 1 | 70.0 | [`cn_riveted_connection`](87_construction.md#cn_riveted_connection---riveted-bolted-gusseted-and-welded-joints) |
| `cn_sash_window` | 1 | 85.0 | [`cn_curtain_wall`](87_construction.md#cn_curtain_wall---curtain-wall-plate-glass-sash-window-asphalt-roofing-corrugated-roof) |
| `cn_sewer_system` | 1 | 100.0 | [`cn_aqueduct`](87_construction.md#cn_aqueduct---masonry-aqueduct-arch-bridge-aqua-ducta) |
| `cn_sheet_piling` | 1 | 100.0 | [`cn_cofferdam`](87_construction.md#cn_cofferdam---cofferdam-dewatering-diaphragm-wall-sheet-piling) |
| `cn_siphon` | 1 | 75.0 | [`cn_aqueduct`](87_construction.md#cn_aqueduct---masonry-aqueduct-arch-bridge-aqua-ducta) |
| `cn_soil_compaction` | 1 | 70.0 | [`cn_pile_driving`](87_construction.md#cn_pile_driving---pile-driving-screw-piles-soil-compaction) |
| `cn_spillway` | 1 | 150.0 | [`cn_gravity_dam`](87_construction.md#cn_gravity_dam---gravity-dam-arch-dam-earth-dam-spillway-retaining-wall) |
| `cn_swing_bridge` | 1 | 110.0 | [`cn_bascule_bridge`](87_construction.md#cn_bascule_bridge---bascule-swing-and-pontoon-bridges) |
| `cn_terrazzo` | 1 | 60.0 | [`cn_terrazzo`](87_construction.md#cn_portland_cement---portland-cement-powder) |
| `cn_trapped_drain` | 1 | 60.0 | [`cn_plumbing_stack`](87_construction.md#cn_plumbing_stack---plumbing-stack-and-trapped-drains) |
| `cn_trussed_arch` | 1 | 100.0 | [`cn_king_post`](87_construction.md#cn_king_post---king-post-roof-truss) |
| `cn_tunnel_cut_cover` | 1 | 105.0 | [`cn_drill_blast`](87_construction.md#cn_drill_blast---tunnelling-by-drill-and-blast) |
| `cn_tunnel_lining` | 1 | 95.0 | [`cn_tunnel_shield`](87_construction.md#cn_tunnel_shield---tunnel-shield-method-and-tunnel-lining) |
| `cn_ventilation_shaft` | 1 | 85.0 | [`cn_drill_blast`](87_construction.md#cn_drill_blast---tunnelling-by-drill-and-blast) |
| `cn_water_main` | 1 | 85.0 | [`cn_aqueduct`](87_construction.md#cn_aqueduct---masonry-aqueduct-arch-bridge-aqua-ducta) |
| `cn_wrought_iron_girder` | 1 | 95.0 | [`cn_wrought_iron_girder`](87_construction.md#cn_wrought_iron_girder---wrought-iron-girder-and-later-steel) |
| `cn_arch_dam` | 2 | 140.0 | [`cn_gravity_dam`](87_construction.md#cn_gravity_dam---gravity-dam-arch-dam-earth-dam-spillway-retaining-wall) |
| `cn_asphalt_roofing` | 2 | 80.0 | [`cn_curtain_wall`](87_construction.md#cn_curtain_wall---curtain-wall-plate-glass-sash-window-asphalt-roofing-corrugated-roof) |
| `cn_bascule_bridge` | 2 | 140.0 | [`cn_bascule_bridge`](87_construction.md#cn_bascule_bridge---bascule-swing-and-pontoon-bridges) |
| `cn_bolted_connection` | 2 | 85.0 | [`cn_riveted_connection`](87_construction.md#cn_riveted_connection---riveted-bolted-gusseted-and-welded-joints) |
| `cn_box_girder` | 2 | 120.0 | [`cn_wrought_iron_girder`](87_construction.md#cn_wrought_iron_girder---wrought-iron-girder-and-later-steel) |
| `cn_cable_anchorage` | 2 | 95.0 | [`cn_suspension_bridge`](87_construction.md#cn_suspension_bridge---suspension-bridge-system) |
| `cn_cantilever` | 2 | 85.0 | [`cn_post_lintel`](87_construction.md#cn_post_lintel---post-and-lintel-the-theory-of-the-beam) |
| `cn_cast_iron_beam` | 2 | 80.0 | [`cn_cast_iron_beam`](87_construction.md#cn_cast_iron_beam---cast-iron-beam) |
| `cn_cement_clinker_grinding` | 2 | 110.0 | [`cn_portland_cement`](87_construction.md#cn_portland_cement---portland-cement-powder) |
| `cn_central_heating` | 2 | 180.0 | [`cn_central_heating`](87_construction.md#cn_central_heating---central-heating-radiators-forced-ventilation) |
| `cn_concrete_mixer` | 2 | 100.0 | [`cn_concrete_mixer`](87_construction.md#cn_concrete_mixer---concrete-mixing-and-placing-at-scale) |
| `cn_crane_tower` | 2 | 130.0 | [`cn_crane_derrick`](87_construction.md#cn_crane_derrick---derrick-and-tower-cranes-elevator-safety-brake) |
| `cn_deformed_rebar` | 2 | 85.0 | [`cn_reinforced_concrete`](87_construction.md#cn_reinforced_concrete---reinforced-concrete-slab-and-beam) |
| `cn_drill_blast` | 2 | 125.0 | [`cn_drill_blast`](87_construction.md#cn_drill_blast---tunnelling-by-drill-and-blast) |
| `cn_forced_ventilation` | 2 | 100.0 | [`cn_central_heating`](87_construction.md#cn_central_heating---central-heating-radiators-forced-ventilation) |
| `cn_insulation` | 2 | 90.0 | [`cn_cavity_wall`](87_construction.md#cn_cavity_wall---cavity-wall-damp-proof-course-insulation) |
| `cn_plate_girder` | 2 | 105.0 | [`cn_wrought_iron_girder`](87_construction.md#cn_wrought_iron_girder---wrought-iron-girder-and-later-steel) |
| `cn_plate_glass_window` | 2 | 120.0 | [`cn_curtain_wall`](87_construction.md#cn_curtain_wall---curtain-wall-plate-glass-sash-window-asphalt-roofing-corrugated-roof) |
| `cn_pneumatic_caisson` | 2 | 140.0 | [`cn_caisson`](87_construction.md#cn_caisson---caisson-pneumatic-caisson-underpinning) |
| `cn_portland_cement` | 2 | 120.0 | [`cn_portland_cement`](87_construction.md#cn_portland_cement---portland-cement-powder) |
| `cn_pratt_truss` | 2 | 90.0 | [`cn_pratt_truss`](87_construction.md#cn_wrought_iron_girder---wrought-iron-girder-and-later-steel) |
| `cn_precast_panel` | 2 | 110.0 | [`cn_reinforced_concrete`](87_construction.md#cn_reinforced_concrete---reinforced-concrete-slab-and-beam) |
| `cn_reinforced_concrete` | 2 | 200.0 | [`cn_reinforced_concrete`](87_construction.md#cn_reinforced_concrete---reinforced-concrete-slab-and-beam) |
| `cn_rolled_I_beam` | 2 | 110.0 | [`cn_wrought_iron_girder`](87_construction.md#cn_wrought_iron_girder---wrought-iron-girder-and-later-steel) |
| `cn_roof_truss_corrugated` | 2 | 95.0 | [`cn_curtain_wall`](87_construction.md#cn_curtain_wall---curtain-wall-plate-glass-sash-window-asphalt-roofing-corrugated-roof) |
| `cn_screw_pile` | 2 | 95.0 | [`cn_pile_driving`](87_construction.md#cn_pile_driving---pile-driving-screw-piles-soil-compaction) |
| `cn_shotcrete` | 2 | 110.0 | [`cn_concrete_mixer`](87_construction.md#cn_concrete_mixer---concrete-mixing-and-placing-at-scale) |
| `cn_sprinkler` | 2 | 110.0 | [`cn_fire_escape`](87_construction.md#cn_fire_escape---fire-escape-and-automatic-sprinklers) |
| `cn_stiffening_truss` | 2 | 100.0 | [`cn_suspension_bridge`](87_construction.md#cn_suspension_bridge---suspension-bridge-system) |
| `cn_tunnel_shield` | 2 | 250.0 | [`cn_tunnel_shield`](87_construction.md#cn_tunnel_shield---tunnel-shield-method-and-tunnel-lining) |
| `cn_underpinning` | 2 | 130.0 | [`cn_caisson`](87_construction.md#cn_caisson---caisson-pneumatic-caisson-underpinning) |
| `cn_vibratory_compaction` | 2 | 85.0 | [`cn_concrete_mixer`](87_construction.md#cn_concrete_mixer---concrete-mixing-and-placing-at-scale) |
| `cn_warren_truss` | 2 | 85.0 | [`cn_pratt_truss`](87_construction.md#cn_wrought_iron_girder---wrought-iron-girder-and-later-steel) |
| `cn_wire_cable_spinning` | 2 | 110.0 | [`cn_suspension_bridge`](87_construction.md#cn_suspension_bridge---suspension-bridge-system) |
| `cn_curtain_wall` | 3 | 150.0 | [`cn_curtain_wall`](87_construction.md#cn_curtain_wall---curtain-wall-plate-glass-sash-window-asphalt-roofing-corrugated-roof) |
| `cn_diaphragm_wall` | 3 | 160.0 | [`cn_cofferdam`](87_construction.md#cn_cofferdam---cofferdam-dewatering-diaphragm-wall-sheet-piling) |
| `cn_post_tensioning` | 3 | 135.0 | [`cn_prestressed_concrete`](87_construction.md#cn_reinforced_concrete---reinforced-concrete-slab-and-beam) |
| `cn_prestressed_concrete` | 3 | 180.0 | [`cn_prestressed_concrete`](87_construction.md#cn_reinforced_concrete---reinforced-concrete-slab-and-beam) |
| `cn_rotary_cement_kiln` | 3 | 160.0 | [`cn_portland_cement`](87_construction.md#cn_portland_cement---portland-cement-powder) |
| `cn_slipform` | 3 | 160.0 | [`cn_concrete_mixer`](87_construction.md#cn_concrete_mixer---concrete-mixing-and-placing-at-scale) |
| `cn_space_frame` | 3 | 150.0 | [`cn_pratt_truss`](87_construction.md#cn_wrought_iron_girder---wrought-iron-girder-and-later-steel) |
| `cn_suspension_bridge` | 3 | 200.0 | [`cn_suspension_bridge`](87_construction.md#cn_suspension_bridge---suspension-bridge-system) |
| `cn_welded_connection` | 3 | 125.0 | [`cn_riveted_connection`](87_construction.md#cn_riveted_connection---riveted-bolted-gusseted-and-welded-joints) |

### 88_media_signals.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `if_dewey_classification` | 0 | 80.0 | [`if_index_card_system`](88_media_signals.md#if_index_card_system---index-card-and-filing-system) |
| `if_index_card_system` | 0 | 70.0 | [`if_index_card_system`](88_media_signals.md#if_index_card_system---index-card-and-filing-system) |
| `if_iron_gall_ink` | 0 | 40.0 | [`if_quill`](88_media_signals.md#if_quill---quill-pen-penna) |
| `if_quill` | 0 | 15.0 | [`if_quill`](88_media_signals.md#if_quill---quill-pen-penna) |
| `mat_papyrus` | 0 | 20.0 | [`if_papyrus`](88_media_signals.md#if_papyrus---papyrus-sheet-papyrus-biblus) |
| `mat_parchment` | 0 | 30.0 | [`if_papyrus`](88_media_signals.md#if_papyrus---papyrus-sheet-papyrus-biblus) |
| `if_acoustic_horn_recording` | 1 | 90.0 | [`if_disc_record`](88_media_signals.md#if_disc_record---disc-record) |
| `if_adding_machine` | 1 | 120.0 | [`if_adding_machine`](88_media_signals.md#if_adding_machine---adding-machine) |
| `if_antenna_dipole` | 1 | 80.0 | [`if_tuned_circuit`](88_media_signals.md#if_tuned_circuit---tuned-lc-circuit) |
| `if_bookbinding_case` | 1 | 120.0 | [`if_papyrus`](88_media_signals.md#if_papyrus---papyrus-sheet-papyrus-biblus) |
| `if_camera_lucida` | 1 | 90.0 | [`if_camera_obscura_lens`](88_media_signals.md#if_camera_obscura_lens---camera-obscura-with-lens) |
| `if_chase_and_forme` | 1 | 80.0 | [`if_printing_ink`](88_media_signals.md#if_printing_ink---printing-ink-oil-based) |
| `if_coherer` | 1 | 100.0 | [`if_spark_transmitter`](88_media_signals.md#if_spark_transmitter---spark-transmitter) |
| `if_composing_stick` | 1 | 60.0 | [`if_printing_ink`](88_media_signals.md#if_printing_ink---printing-ink-oil-based) |
| `if_gramophone_motor` | 1 | 100.0 | [`if_disc_record`](88_media_signals.md#if_disc_record---disc-record) |
| `if_jacquard_chain` | 1 | 120.0 | [`if_punched_card`](88_media_signals.md#if_punched_card---punched-card) |
| `if_morse_key_and_sounder` | 1 | 100.0 | [`if_electric_telegraph`](88_media_signals.md#if_electric_telegraph---electric-telegraph) |
| `if_phonautograph` | 1 | 110.0 | [`if_phonautograph`](88_media_signals.md#if_phonautograph---phonautograph) |
| `if_punched_card` | 1 | 80.0 | [`if_punched_card`](88_media_signals.md#if_punched_card---punched-card) |
| `if_silver_halide_sensitivity` | 1 | 120.0 | [`if_silver_halide_sensitivity`](88_media_signals.md#if_silver_halide_sensitivity---silver-halide-photographic-sensitivity) |
| `if_slide_rule` | 1 | 100.0 | [`if_adding_machine`](88_media_signals.md#if_adding_machine---adding-machine) |
| `if_spark_transmitter` | 1 | 130.0 | [`if_spark_transmitter`](88_media_signals.md#if_spark_transmitter---spark-transmitter) |
| `if_steel_pen_nib` | 1 | 80.0 | [`if_quill`](88_media_signals.md#if_quill---quill-pen-penna) |
| `if_telegraph_relay` | 1 | 90.0 | [`if_electric_telegraph`](88_media_signals.md#if_electric_telegraph---electric-telegraph) |
| `if_telephone_receiver` | 1 | 80.0 | [`if_telephone_transmitter`](88_media_signals.md#if_telephone_transmitter---telephone-transmitter) |
| `if_tin_foil_phonograph` | 1 | 130.0 | [`if_phonautograph`](88_media_signals.md#if_phonautograph---phonautograph) |
| `if_woodblock_printing` | 1 | 150.0 | [`if_printing_ink`](88_media_signals.md#if_printing_ink---printing-ink-oil-based) |
| `if_amplitude_modulation` | 2 | 120.0 | [`if_triode_oscillator`](88_media_signals.md#if_triode_oscillator---triode-oscillator) |
| `if_cable_repeater` | 2 | 140.0 | [`if_submarine_cable_gutta_percha`](88_media_signals.md#if_submarine_cable_gutta_percha---submarine-cable-with-gutta-percha) |
| `if_calotype` | 2 | 130.0 | [`if_calotype`](88_media_signals.md#if_calotype---calotype-paper-negative) |
| `if_carbon_microphone` | 2 | 110.0 | [`if_carbon_microphone`](88_media_signals.md#if_carbon_microphone---carbon-microphone) |
| `if_card_sorter` | 2 | 140.0 | [`if_card_sorter`](88_media_signals.md#if_card_sorter---card-sorter) |
| `if_cash_register` | 2 | 140.0 | [`if_adding_machine`](88_media_signals.md#if_adding_machine---adding-machine) |
| `if_comptometer` | 2 | 160.0 | [`if_adding_machine`](88_media_signals.md#if_adding_machine---adding-machine) |
| `if_continuous_wave_transmitter` | 2 | 150.0 | [`if_triode_oscillator`](88_media_signals.md#if_triode_oscillator---triode-oscillator) |
| `if_crystal_detector` | 2 | 110.0 | [`if_spark_transmitter`](88_media_signals.md#if_spark_transmitter---spark-transmitter) |
| `if_disc_cutting_lathe` | 2 | 150.0 | [`if_disc_record`](88_media_signals.md#if_disc_record---disc-record) |
| `if_disc_record` | 2 | 150.0 | [`if_disc_record`](88_media_signals.md#if_disc_record---disc-record) |
| `if_dry_gelatin_plate` | 2 | 160.0 | [`if_calotype`](88_media_signals.md#if_calotype---calotype-paper-negative) |
| `if_film_projector` | 2 | 140.0 | [`if_cine_camera`](88_media_signals.md#if_cine_camera---cine-camera) |
| `if_flash_powder` | 2 | 100.0 | [`if_flash_powder`](88_media_signals.md#if_flash_powder---flash-powder) |
| `if_focal_plane_shutter` | 2 | 130.0 | [`if_focal_plane_shutter`](88_media_signals.md#if_focal_plane_shutter---focal-plane-shutter) |
| `if_hollerith_tabulator` | 2 | 150.0 | [`if_card_sorter`](88_media_signals.md#if_card_sorter---card-sorter) |
| `if_iron_hand_press` | 2 | 140.0 | [`if_screw_press`](88_media_signals.md#if_screw_press---screw-press-for-printing) |
| `if_keypunch` | 2 | 130.0 | [`if_punched_card`](88_media_signals.md#if_punched_card---punched-card) |
| `if_leaf_shutter` | 2 | 140.0 | [`if_focal_plane_shutter`](88_media_signals.md#if_focal_plane_shutter---focal-plane-shutter) |
| `if_movable_type` | 2 | 200.0 | [`if_movable_type`](88_media_signals.md#if_movable_type---movable-type-cast-metal-typi-mobiles) |
| `if_moving_coil_loudspeaker` | 2 | 130.0 | [`if_carbon_microphone`](88_media_signals.md#if_carbon_microphone---carbon-microphone) |
| `if_pencil_graphite` | 2 | 100.0 | [`if_fountain_pen`](88_media_signals.md#if_fountain_pen---fountain-pen) |
| `if_punch_and_matrix` | 2 | 180.0 | [`if_movable_type`](88_media_signals.md#if_movable_type---movable-type-cast-metal-typi-mobiles) |
| `if_radio_direction_finding` | 2 | 130.0 | [`if_superheterodyne_receiver`](88_media_signals.md#if_superheterodyne_receiver---superheterodyne-receiver) |
| `if_recording_bias` | 2 | 120.0 | [`if_magnetic_tape`](88_media_signals.md#if_magnetic_tape---magnetic-tape-recording) |
| `if_screw_press` | 2 | 160.0 | [`if_screw_press`](88_media_signals.md#if_screw_press---screw-press-for-printing) |
| `if_shift_key_mechanism` | 2 | 100.0 | [`if_typewriter`](88_media_signals.md#if_typewriter---typewriter) |
| `if_stencil_duplicator` | 2 | 140.0 | [`if_mimeograph`](88_media_signals.md#if_mimeograph---mimeograph) |
| `if_telephone_exchange` | 2 | 150.0 | [`if_telephone_exchange`](88_media_signals.md#if_telephone_exchange---telephone-exchange-and-switchboard) |
| `if_telephone_transmitter` | 2 | 110.0 | [`if_telephone_transmitter`](88_media_signals.md#if_telephone_transmitter---telephone-transmitter) |
| `if_television_mechanical` | 2 | 160.0 | [`if_cathode_ray_tube`](88_media_signals.md#if_cathode_ray_tube---cathode-ray-tube) |
| `if_type_mould` | 2 | 140.0 | [`if_movable_type`](88_media_signals.md#if_movable_type---movable-type-cast-metal-typi-mobiles) |
| `if_video_scanning_standard` | 2 | 100.0 | [`if_cathode_ray_tube`](88_media_signals.md#if_cathode_ray_tube---cathode-ray-tube) |
| `if_wax_cylinder` | 2 | 140.0 | [`if_phonautograph`](88_media_signals.md#if_phonautograph---phonautograph) |
| `if_autochrome_plate` | 3 | 180.0 | [`if_celluloid_roll_film`](88_media_signals.md#if_celluloid_roll_film---celluloid-roll-film) |
| `if_carbon_paper` | 3 | 70.0 | [`if_fountain_pen`](88_media_signals.md#if_fountain_pen---fountain-pen) |
| `if_cathode_ray_tube` | 3 | 200.0 | [`if_cathode_ray_tube`](88_media_signals.md#if_cathode_ray_tube---cathode-ray-tube) |
| `if_celluloid_roll_film` | 3 | 200.0 | [`if_celluloid_roll_film`](88_media_signals.md#if_celluloid_roll_film---celluloid-roll-film) |
| `if_chromolithography` | 3 | 200.0 | [`if_lithography`](88_media_signals.md#if_lithography---lithography) |
| `if_cine_camera` | 3 | 180.0 | [`if_cine_camera`](88_media_signals.md#if_cine_camera---cine-camera) |
| `if_facsimile_transmission` | 3 | 170.0 | [`if_superheterodyne_receiver`](88_media_signals.md#if_superheterodyne_receiver---superheterodyne-receiver) |
| `if_flashbulb` | 3 | 150.0 | [`if_flash_powder`](88_media_signals.md#if_flash_powder---flash-powder) |
| `if_frequency_modulation` | 3 | 180.0 | [`if_triode_oscillator`](88_media_signals.md#if_triode_oscillator---triode-oscillator) |
| `if_halftone_screen` | 3 | 150.0 | [`if_halftone_screen`](88_media_signals.md#if_halftone_screen---halftone-screen-and-dot-matrix) |
| `if_iconoscope` | 3 | 200.0 | [`if_cathode_ray_tube`](88_media_signals.md#if_cathode_ray_tube---cathode-ray-tube) |
| `if_magnetic_tape` | 3 | 250.0 | [`if_magnetic_tape`](88_media_signals.md#if_magnetic_tape---magnetic-tape-recording) |
| `if_mimeograph` | 3 | 160.0 | [`if_mimeograph`](88_media_signals.md#if_mimeograph---mimeograph) |
| `if_panchromatic_emulsion` | 3 | 140.0 | [`if_celluloid_roll_film`](88_media_signals.md#if_celluloid_roll_film---celluloid-roll-film) |
| `if_photoengraving` | 3 | 130.0 | [`if_halftone_screen`](88_media_signals.md#if_halftone_screen---halftone-screen-and-dot-matrix) |
| `if_strowger_exchange` | 3 | 180.0 | [`if_telephone_exchange`](88_media_signals.md#if_telephone_exchange---telephone-exchange-and-switchboard) |
| `if_superheterodyne_receiver` | 3 | 170.0 | [`if_superheterodyne_receiver`](88_media_signals.md#if_superheterodyne_receiver---superheterodyne-receiver) |
| `if_triode_oscillator` | 3 | 160.0 | [`if_triode_oscillator`](88_media_signals.md#if_triode_oscillator---triode-oscillator) |
| `if_submarine_cable_gutta_percha` | 5 | 200.0 | [`if_submarine_cable_gutta_percha`](88_media_signals.md#if_submarine_cable_gutta_percha---submarine-cable-with-gutta-percha) |

### 89_remaining_arts.md

| Node | Your hours | Recipe |
|---|---:|---|
| `civ_bending_moment` | 200.0 | [`civ_bending_moment`](89_remaining_arts.md#civ_bending_moment---bending-moment-shear-neutral-axis-elasticity-buckling) |
| `civ_elasticity_theory` | 300.0 | [`civ_bending_moment`](89_remaining_arts.md#civ_bending_moment---bending-moment-shear-neutral-axis-elasticity-buckling) |
| `civ_euler_buckling` | 180.0 | [`civ_bending_moment`](89_remaining_arts.md#civ_bending_moment---bending-moment-shear-neutral-axis-elasticity-buckling) |
| `civ_factor_safety` | 100.0 | [`civ_materials_testing`](89_remaining_arts.md#civ_materials_testing---materials-testing-safety-factor-soil-mechanics) |
| `civ_materials_testing` | 150.0 | [`civ_materials_testing`](89_remaining_arts.md#civ_materials_testing---materials-testing-safety-factor-soil-mechanics) |
| `civ_method_joints` | 150.0 | [`civ_statics`](89_remaining_arts.md#civ_statics---statics-forces-and-moments-in-balance) |
| `civ_neutral_axis` | 120.0 | [`civ_bending_moment`](89_remaining_arts.md#civ_bending_moment---bending-moment-shear-neutral-axis-elasticity-buckling) |
| `civ_soil_mechanics` | 250.0 | [`civ_materials_testing`](89_remaining_arts.md#civ_materials_testing---materials-testing-safety-factor-soil-mechanics) |
| `civ_statics` | 200.0 | [`civ_statics`](89_remaining_arts.md#civ_statics---statics-forces-and-moments-in-balance) |
| `ctl_bode_plot_margins` | 160.0 | [`ctl_nyquist_stability_criterion`](89_remaining_arts.md#ctl_nyquist_stability_criterion---nyquist-criterion-bode-plot-and-margins-root-locus) |
| `ctl_governor_stability_theory` | 150.0 | [`ctl_governor_stability_theory`](89_remaining_arts.md#ctl_governor_stability_theory---stability-theory-maxwells-governor-equations-routh-and-hurwitz-criteria-nyquist-bode-root-locus) |
| `ctl_hurwitz_criterion` | 170.0 | [`ctl_governor_stability_theory`](89_remaining_arts.md#ctl_governor_stability_theory---stability-theory-maxwells-governor-equations-routh-and-hurwitz-criteria-nyquist-bode-root-locus) |
| `ctl_minorsky_pid_law` | 200.0 | [`ctl_minorsky_pid_law`](89_remaining_arts.md#ctl_minorsky_pid_law---the-designed-process-controller-three-term-pid-control-the-pneumatic-controller-ziegler-nichols-tuning) |
| `ctl_nyquist_stability_criterion` | 220.0 | [`ctl_nyquist_stability_criterion`](89_remaining_arts.md#ctl_nyquist_stability_criterion---nyquist-criterion-bode-plot-and-margins-root-locus) |
| `ctl_pneumatic_process_controller` | 260.0 | [`ctl_minorsky_pid_law`](89_remaining_arts.md#ctl_minorsky_pid_law---the-designed-process-controller-three-term-pid-control-the-pneumatic-controller-ziegler-nichols-tuning) |
| `ctl_root_locus` | 170.0 | [`ctl_nyquist_stability_criterion`](89_remaining_arts.md#ctl_nyquist_stability_criterion---nyquist-criterion-bode-plot-and-margins-root-locus) |
| `ctl_routh_criterion` | 170.0 | [`ctl_governor_stability_theory`](89_remaining_arts.md#ctl_governor_stability_theory---stability-theory-maxwells-governor-equations-routh-and-hurwitz-criteria-nyquist-bode-root-locus) |
| `ctl_ziegler_nichols_tuning` | 140.0 | [`ctl_minorsky_pid_law`](89_remaining_arts.md#ctl_minorsky_pid_law---the-designed-process-controller-three-term-pid-control-the-pneumatic-controller-ziegler-nichols-tuning) |
| `fin_assay_office` | 180.0 | [`fin_standard_weights`](89_remaining_arts.md#fin_standard_weights---standard-weights-assay-office-customs-house) |
| `fin_census` | 200.0 | [`fin_census`](89_remaining_arts.md#fin_census---census-survey-statistics-office-mortality-table) |
| `fin_civil_service_exam` | 180.0 | [`fin_government`](89_remaining_arts.md#fin_government---standing-bureaucracy-post-office-civil-service-exam) |
| `fin_collegium` | 120.0 | [`fin_societas`](89_remaining_arts.md#fin_societas---business-organisation-partnership-to-joint-stock-exchange-guilds-unions-totalisator) |
| `fin_commodity_exchange` | 180.0 | [`fin_societas`](89_remaining_arts.md#fin_societas---business-organisation-partnership-to-joint-stock-exchange-guilds-unions-totalisator) |
| `fin_customs_house` | 120.0 | [`fin_standard_weights`](89_remaining_arts.md#fin_standard_weights---standard-weights-assay-office-customs-house) |
| `fin_endowed_chair` | 150.0 | [`fin_university`](89_remaining_arts.md#fin_university---academic-and-research-institutions) |
| `fin_government` | 0.0 | [`fin_government`](89_remaining_arts.md#fin_government---standing-bureaucracy-post-office-civil-service-exam) |
| `fin_guild` | 100.0 | [`fin_societas`](89_remaining_arts.md#fin_societas---business-organisation-partnership-to-joint-stock-exchange-guilds-unions-totalisator) |
| `fin_joint_stock` | 250.0 | [`fin_societas`](89_remaining_arts.md#fin_societas---business-organisation-partnership-to-joint-stock-exchange-guilds-unions-totalisator) |
| `fin_learned_society` | 200.0 | [`fin_university`](89_remaining_arts.md#fin_university---academic-and-research-institutions) |
| `fin_mortality_table` | 250.0 | [`fin_census`](89_remaining_arts.md#fin_census---census-survey-statistics-office-mortality-table) |
| `fin_museum` | 180.0 | [`fin_university`](89_remaining_arts.md#fin_university---academic-and-research-institutions) |
| `fin_patent_office` | 200.0 | [`fin_professional_exam`](89_remaining_arts.md#fin_professional_exam---professional-licensing-and-patent-office) |
| `fin_post_office` | 150.0 | [`fin_government`](89_remaining_arts.md#fin_government---standing-bureaucracy-post-office-civil-service-exam) |
| `fin_professional_exam` | 150.0 | [`fin_professional_exam`](89_remaining_arts.md#fin_professional_exam---professional-licensing-and-patent-office) |
| `fin_research_institute` | 250.0 | [`fin_university`](89_remaining_arts.md#fin_university---academic-and-research-institutions) |
| `fin_societas` | 40.0 | [`fin_societas`](89_remaining_arts.md#fin_societas---business-organisation-partnership-to-joint-stock-exchange-guilds-unions-totalisator) |
| `fin_standard_weights` | 150.0 | [`fin_standard_weights`](89_remaining_arts.md#fin_standard_weights---standard-weights-assay-office-customs-house) |
| `fin_statistical_office` | 220.0 | [`fin_census`](89_remaining_arts.md#fin_census---census-survey-statistics-office-mortality-table) |
| `fin_survey_map` | 250.0 | [`fin_census`](89_remaining_arts.md#fin_census---census-survey-statistics-office-mortality-table) |
| `fin_totalisator` | 200.0 | [`fin_societas`](89_remaining_arts.md#fin_societas---business-organisation-partnership-to-joint-stock-exchange-guilds-unions-totalisator) |
| `fin_trade_union` | 120.0 | [`fin_societas`](89_remaining_arts.md#fin_societas---business-organisation-partnership-to-joint-stock-exchange-guilds-unions-totalisator) |
| `fin_university` | 200.0 | [`fin_university`](89_remaining_arts.md#fin_university---academic-and-research-institutions) |
| `fud_agricultural_treatises` | 300.0 | [`fud_agricultural_treatises`](89_remaining_arts.md#fud_agricultural_treatises---written-treatises-and-soil-testing) |
| `fud_soil_composition_analysis` | 200.0 | [`fud_agricultural_treatises`](89_remaining_arts.md#fud_agricultural_treatises---written-treatises-and-soil-testing) |
| `gp_carbon_brushes` | 50.0 | [`gp_carbon_brushes`](89_remaining_arts.md#gp_carbon_brushes---carbon-and-graphite-brush-contacts) |
| `gp_controlled_atmosphere_chamber` | 180.0 | [`gp_controlled_atmosphere_chamber`](89_remaining_arts.md#gp_controlled_atmosphere_chamber---controlled-atmosphere-furnace-chamber) |
| `gp_czochralski_puller` | 200.0 | [`gp_czochralski_puller`](89_remaining_arts.md#gp_czochralski_puller---seed-and-pull-crystal-grower) |
| `gp_exhaust_pinchoff` | 100.0 | [`gp_exhaust_pinchoff`](89_remaining_arts.md#gp_exhaust_pinchoff---exhaust-and-pinch-off-technique) |
| `gp_getter` | 130.0 | [`gp_getter`](89_remaining_arts.md#gp_getter---chemical-getter) |
| `gp_glass_metal_seal` | 150.0 | [`gp_glass_metal_seal`](89_remaining_arts.md#gp_glass_metal_seal---glass-to-metal-vacuum-seal) |
| `gp_laminated_core` | 90.0 | [`gp_laminated_core`](89_remaining_arts.md#gp_laminated_core---laminated-iron-core) |
| `gp_magnet_wire_enamelled` | 120.0 | [`gp_magnet_wire_enamelled`](89_remaining_arts.md#gp_magnet_wire_enamelled---enamelled-magnet-wire) |
| `gp_whisker_forming` | 200.0 | [`gp_whisker_forming`](89_remaining_arts.md#gp_whisker_forming---point-contact-whisker-forming) |
| `in2_analytical_balance` | 50.0 | [`in2_analytical_balance`](89_remaining_arts.md#in2_analytical_balance---precision-balances-equal-arm-torsion-quartz-microbalance) |
| `in2_aneroid_capsule` | 70.0 | [`in2_bourdon_pressure_gauge`](89_remaining_arts.md#in2_bourdon_pressure_gauge---pressure-and-vacuum-gauges) |
| `in2_balance_spring_watch` | 100.0 | [`in2_quartz_resonator_frequency`](89_remaining_arts.md#in2_quartz_resonator_frequency---frequency-standards-quartz-tuning-fork-hairspring) |
| `in2_gas_thermometry_absolute` | 140.0 | [`in2_thermocouple`](89_remaining_arts.md#in2_thermocouple---temperature-measurement-thermocouple-rtd-gas-thermometry) |
| `in2_mcleod_vacuum_gauge` | 85.0 | [`in2_bourdon_pressure_gauge`](89_remaining_arts.md#in2_bourdon_pressure_gauge---pressure-and-vacuum-gauges) |
| `in2_mercury_barometer` | 45.0 | [`in2_bourdon_pressure_gauge`](89_remaining_arts.md#in2_bourdon_pressure_gauge---pressure-and-vacuum-gauges) |
| `in2_microbalance_quartz` | 100.0 | [`in2_analytical_balance`](89_remaining_arts.md#in2_analytical_balance---precision-balances-equal-arm-torsion-quartz-microbalance) |
| `in2_orifice_flow_meter` | 50.0 | [`in2_pitot_tube`](89_remaining_arts.md#in2_pitot_tube---flow-measurement-pitot-venturi-orifice) |
| `in2_quartz_resonator_frequency` | 110.0 | [`in2_quartz_resonator_frequency`](89_remaining_arts.md#in2_quartz_resonator_frequency---frequency-standards-quartz-tuning-fork-hairspring) |
| `in2_resistance_thermometer_RTD` | 80.0 | [`in2_thermocouple`](89_remaining_arts.md#in2_thermocouple---temperature-measurement-thermocouple-rtd-gas-thermometry) |
| `in2_thermocouple` | 45.0 | [`in2_thermocouple`](89_remaining_arts.md#in2_thermocouple---temperature-measurement-thermocouple-rtd-gas-thermometry) |
| `in2_torsion_balance` | 85.0 | [`in2_analytical_balance`](89_remaining_arts.md#in2_analytical_balance---precision-balances-equal-arm-torsion-quartz-microbalance) |
| `in2_travelling_microscope` | 80.0 | [`in2_optical_comparator`](89_remaining_arts.md#in2_optical_comparator---optical-length-measurement-comparator-and-travelling-microscope) |
| `in2_tuning_fork_oscillator` | 60.0 | [`in2_quartz_resonator_frequency`](89_remaining_arts.md#in2_quartz_resonator_frequency---frequency-standards-quartz-tuning-fork-hairspring) |
| `in2_venturi_flow_meter` | 70.0 | [`in2_pitot_tube`](89_remaining_arts.md#in2_pitot_tube---flow-measurement-pitot-venturi-orifice) |
| `mat_chile_nitrate` | 60.0 | [`mat_natural_rubber`](89_remaining_arts.md#mat_natural_rubber---distant-materials-that-are-reachable-not-exotic) |
| `mat_cryolite` | 200.0 | [`mat_natural_rubber`](89_remaining_arts.md#mat_natural_rubber---distant-materials-that-are-reachable-not-exotic) |
| `mat_gutta_percha` | 120.0 | [`mat_natural_rubber`](89_remaining_arts.md#mat_natural_rubber---distant-materials-that-are-reachable-not-exotic) |
| `mat_natural_rubber` | 60.0 | [`mat_natural_rubber`](89_remaining_arts.md#mat_natural_rubber---distant-materials-that-are-reachable-not-exotic) |
| `mat_newworld_crops` | 60.0 | [`mat_natural_rubber`](89_remaining_arts.md#mat_natural_rubber---distant-materials-that-are-reachable-not-exotic) |
| `mat_platinum_bulk` | 60.0 | [`mat_natural_rubber`](89_remaining_arts.md#mat_natural_rubber---distant-materials-that-are-reachable-not-exotic) |
| `mat_quinine` | 150.0 | [`mat_natural_rubber`](89_remaining_arts.md#mat_natural_rubber---distant-materials-that-are-reachable-not-exotic) |
| `mat_rubber_coagulated` | 150.0 | [`mat_rubber_coagulated`](89_remaining_arts.md#mat_rubber_coagulated) **BROKEN** |
| `md2_agar_media` | 100.0 | [`md2_agar_media`](89_remaining_arts.md#md2_agar_media---laboratory-and-anatomical-method-agar-culture-microbiology-bioassay-drug-standardisation-cadaver-dissection) |
| `md2_bioassay` | 140.0 | [`md2_agar_media`](89_remaining_arts.md#md2_agar_media---laboratory-and-anatomical-method-agar-culture-microbiology-bioassay-drug-standardisation-cadaver-dissection) |
| `md2_blinding` | 100.0 | [`md2_case_series`](89_remaining_arts.md#md2_case_series---clinical-study-design-case-series-to-randomised-controlled-trial) |
| `md2_cadaver_dissection` | 100.0 | [`md2_agar_media`](89_remaining_arts.md#md2_agar_media---laboratory-and-anatomical-method-agar-culture-microbiology-bioassay-drug-standardisation-cadaver-dissection) |
| `md2_case_control_study` | 160.0 | [`md2_case_series`](89_remaining_arts.md#md2_case_series---clinical-study-design-case-series-to-randomised-controlled-trial) |
| `md2_case_record` | 80.0 | [`md2_case_record`](89_remaining_arts.md#md2_case_record---medical-practice-institutions-case-records-journals-licensing-nursing-pharmacopoeia) |
| `md2_case_series` | 100.0 | [`md2_case_series`](89_remaining_arts.md#md2_case_series---clinical-study-design-case-series-to-randomised-controlled-trial) |
| `md2_cell_theory` | 100.0 | [`md2_cell_theory`](89_remaining_arts.md#md2_cell_theory---cell-theory-and-heredity-chromosomes-genes-dna-mendelian-ratios) |
| `md2_chromosome` | 120.0 | [`md2_cell_theory`](89_remaining_arts.md#md2_cell_theory---cell-theory-and-heredity-chromosomes-genes-dna-mendelian-ratios) |
| `md2_circulation` | 150.0 | [`md2_circulation`](89_remaining_arts.md#md2_circulation---core-physiology-circulation-digestion-respiration-kidney-nerves-hormones-immunity) |
| `md2_cohort_study` | 180.0 | [`md2_case_series`](89_remaining_arts.md#md2_case_series---clinical-study-design-case-series-to-randomised-controlled-trial) |
| `md2_digestion` | 140.0 | [`md2_circulation`](89_remaining_arts.md#md2_circulation---core-physiology-circulation-digestion-respiration-kidney-nerves-hormones-immunity) |
| `md2_dna` | 150.0 | [`md2_cell_theory`](89_remaining_arts.md#md2_cell_theory---cell-theory-and-heredity-chromosomes-genes-dna-mendelian-ratios) |
| `md2_drug_standardisation` | 150.0 | [`md2_agar_media`](89_remaining_arts.md#md2_agar_media---laboratory-and-anatomical-method-agar-culture-microbiology-bioassay-drug-standardisation-cadaver-dissection) |
| `md2_endocrine_system` | 180.0 | [`md2_circulation`](89_remaining_arts.md#md2_circulation---core-physiology-circulation-digestion-respiration-kidney-nerves-hormones-immunity) |
| `md2_gas_exchange` | 120.0 | [`md2_circulation`](89_remaining_arts.md#md2_circulation---core-physiology-circulation-digestion-respiration-kidney-nerves-hormones-immunity) |
| `md2_gene` | 100.0 | [`md2_cell_theory`](89_remaining_arts.md#md2_cell_theory---cell-theory-and-heredity-chromosomes-genes-dna-mendelian-ratios) |
| `md2_immunity` | 200.0 | [`md2_circulation`](89_remaining_arts.md#md2_circulation---core-physiology-circulation-digestion-respiration-kidney-nerves-hormones-immunity) |
| `md2_kidney` | 130.0 | [`md2_circulation`](89_remaining_arts.md#md2_circulation---core-physiology-circulation-digestion-respiration-kidney-nerves-hormones-immunity) |
| `md2_medical_journal` | 120.0 | [`md2_case_record`](89_remaining_arts.md#md2_case_record---medical-practice-institutions-case-records-journals-licensing-nursing-pharmacopoeia) |
| `md2_medical_licensing` | 100.0 | [`md2_case_record`](89_remaining_arts.md#md2_case_record---medical-practice-institutions-case-records-journals-licensing-nursing-pharmacopoeia) |
| `md2_medical_statistics` | 140.0 | [`md2_medical_statistics`](89_remaining_arts.md#md2_medical_statistics---medical-statistics-and-vital-registration) |
| `md2_mendelian_inheritance` | 80.0 | [`md2_cell_theory`](89_remaining_arts.md#md2_cell_theory---cell-theory-and-heredity-chromosomes-genes-dna-mendelian-ratios) |
| `md2_microbiology_culture` | 140.0 | [`md2_agar_media`](89_remaining_arts.md#md2_agar_media---laboratory-and-anatomical-method-agar-culture-microbiology-bioassay-drug-standardisation-cadaver-dissection) |
| `md2_nervous_system` | 160.0 | [`md2_circulation`](89_remaining_arts.md#md2_circulation---core-physiology-circulation-digestion-respiration-kidney-nerves-hormones-immunity) |
| `md2_nursing_profession` | 150.0 | [`md2_case_record`](89_remaining_arts.md#md2_case_record---medical-practice-institutions-case-records-journals-licensing-nursing-pharmacopoeia) |
| `md2_pharmacopoeia` | 180.0 | [`md2_case_record`](89_remaining_arts.md#md2_case_record---medical-practice-institutions-case-records-journals-licensing-nursing-pharmacopoeia) |
| `md2_placebo` | 100.0 | [`md2_case_series`](89_remaining_arts.md#md2_case_series---clinical-study-design-case-series-to-randomised-controlled-trial) |
| `md2_randomised_controlled_trial` | 250.0 | [`md2_case_series`](89_remaining_arts.md#md2_case_series---clinical-study-design-case-series-to-randomised-controlled-trial) |
| `md2_vital_registration` | 100.0 | [`md2_medical_statistics`](89_remaining_arts.md#md2_medical_statistics---medical-statistics-and-vital-registration) |
| `met_fatigue_testing` | 280.0 | [`met_tensile_test`](89_remaining_arts.md#met_tensile_test---mechanical-testing-tensile-hardness-fatigue) |
| `met_hardness_test` | 140.0 | [`met_tensile_test`](89_remaining_arts.md#met_tensile_test---mechanical-testing-tensile-hardness-fatigue) |
| `met_mannesmann_piercing` | 300.0 | [`met_mannesmann_piercing`](89_remaining_arts.md#met_mannesmann_piercing---mannesmann-piercing-for-seamless-tube) |
| `met_metallography` | 200.0 | [`met_metallography`](89_remaining_arts.md#met_metallography---metal-structure-analysis-metallography-phase-diagrams-spectroscopy) |
| `met_phase_diagram_knowledge` | 300.0 | [`met_metallography`](89_remaining_arts.md#met_metallography---metal-structure-analysis-metallography-phase-diagrams-spectroscopy) |
| `met_spectroscopic_assay` | 160.0 | [`met_metallography`](89_remaining_arts.md#met_metallography---metal-structure-analysis-metallography-phase-diagrams-spectroscopy) |
| `mfg_bill_materials` | 140.0 | [`mfg_drawing_office`](89_remaining_arts.md#mfg_drawing_office---engineering-drawing-and-documentation) |
| `mfg_blueprint` | 140.0 | [`mfg_drawing_office`](89_remaining_arts.md#mfg_drawing_office---engineering-drawing-and-documentation) |
| `mfg_change_order` | 120.0 | [`mfg_drawing_office`](89_remaining_arts.md#mfg_drawing_office---engineering-drawing-and-documentation) |
| `mfg_critical_path_method` | 220.0 | [`mfg_queueing_theory`](89_remaining_arts.md#mfg_queueing_theory---operations-research-queueing-theory-linear-programming-and-the-simplex-method-gantt-charts-the-critical-path-method) |
| `mfg_dimensioning` | 160.0 | [`mfg_drawing_office`](89_remaining_arts.md#mfg_drawing_office---engineering-drawing-and-documentation) |
| `mfg_drawing_office` | 150.0 | [`mfg_drawing_office`](89_remaining_arts.md#mfg_drawing_office---engineering-drawing-and-documentation) |
| `mfg_gantt_chart` | 100.0 | [`mfg_queueing_theory`](89_remaining_arts.md#mfg_queueing_theory---operations-research-queueing-theory-linear-programming-and-the-simplex-method-gantt-charts-the-critical-path-method) |
| `mfg_inventory_mgmt` | 120.0 | [`mfg_production_schedule`](89_remaining_arts.md#mfg_production_schedule---production-planning-and-control) |
| `mfg_linear_programming_simplex` | 250.0 | [`mfg_queueing_theory`](89_remaining_arts.md#mfg_queueing_theory---operations-research-queueing-theory-linear-programming-and-the-simplex-method-gantt-charts-the-critical-path-method) |
| `mfg_maintenance` | 130.0 | [`mfg_production_schedule`](89_remaining_arts.md#mfg_production_schedule---production-planning-and-control) |
| `mfg_orthographic` | 130.0 | [`mfg_drawing_office`](89_remaining_arts.md#mfg_drawing_office---engineering-drawing-and-documentation) |
| `mfg_piece_rate` | 100.0 | [`mfg_time_study`](89_remaining_arts.md#mfg_time_study---scientific-management-time-study-work-study-standard-hour-piece-rate-assembly-line) |
| `mfg_production_schedule` | 130.0 | [`mfg_production_schedule`](89_remaining_arts.md#mfg_production_schedule---production-planning-and-control) |
| `mfg_quality_dept` | 160.0 | [`mfg_production_schedule`](89_remaining_arts.md#mfg_production_schedule---production-planning-and-control) |
| `mfg_queueing_theory` | 150.0 | [`mfg_queueing_theory`](89_remaining_arts.md#mfg_queueing_theory---operations-research-queueing-theory-linear-programming-and-the-simplex-method-gantt-charts-the-critical-path-method) |
| `mfg_standard_hour` | 120.0 | [`mfg_time_study`](89_remaining_arts.md#mfg_time_study---scientific-management-time-study-work-study-standard-hour-piece-rate-assembly-line) |
| `mfg_time_study` | 140.0 | [`mfg_time_study`](89_remaining_arts.md#mfg_time_study---scientific-management-time-study-work-study-standard-hour-piece-rate-assembly-line) |
| `mfg_tool_room` | 140.0 | [`mfg_production_schedule`](89_remaining_arts.md#mfg_production_schedule---production-planning-and-control) |
| `mfg_work_study` | 200.0 | [`mfg_time_study`](89_remaining_arts.md#mfg_time_study---scientific-management-time-study-work-study-standard-hour-piece-rate-assembly-line) |
| `mil_ammunition_standardisation` | 80.0 | [`mil_conscription_reserve`](89_remaining_arts.md#mil_conscription_reserve---mass-mobilisation-conscription-railways-logistics-arsenal-manufacture) |
| `mil_arsenal_manufacturing` | 110.0 | [`mil_conscription_reserve`](89_remaining_arts.md#mil_conscription_reserve---mass-mobilisation-conscription-railways-logistics-arsenal-manufacture) |
| `mil_conscription_reserve` | 60.0 | [`mil_conscription_reserve`](89_remaining_arts.md#mil_conscription_reserve---mass-mobilisation-conscription-railways-logistics-arsenal-manufacture) |
| `mil_cryptanalysis` | 110.0 | [`mil_cryptanalysis`](89_remaining_arts.md#mil_cryptanalysis---signals-intelligence-cryptanalysis-operational-research) |
| `mil_general_staff` | 100.0 | [`mil_general_staff`](89_remaining_arts.md#mil_general_staff---professional-military-planning-general-staff-and-war-college) |
| `mil_logistics_discipline` | 90.0 | [`mil_conscription_reserve`](89_remaining_arts.md#mil_conscription_reserve---mass-mobilisation-conscription-railways-logistics-arsenal-manufacture) |
| `mil_operational_research` | 120.0 | [`mil_cryptanalysis`](89_remaining_arts.md#mil_cryptanalysis---signals-intelligence-cryptanalysis-operational-research) |
| `mil_railway_mobilisation` | 100.0 | [`mil_conscription_reserve`](89_remaining_arts.md#mil_conscription_reserve---mass-mobilisation-conscription-railways-logistics-arsenal-manufacture) |
| `mil_signals_intelligence` | 80.0 | [`mil_cryptanalysis`](89_remaining_arts.md#mil_cryptanalysis---signals-intelligence-cryptanalysis-operational-research) |
| `mil_war_college` | 100.0 | [`mil_general_staff`](89_remaining_arts.md#mil_general_staff---professional-military-planning-general-staff-and-war-college) |
| `prc_apprentice_system` | 150.0 | [`prc_apprentice_system`](89_remaining_arts.md#prc_apprentice_system---apprentice-system-and-toolroom-institution) |
| `prc_toolroom_institution` | 100.0 | [`prc_apprentice_system`](89_remaining_arts.md#prc_apprentice_system---apprentice-system-and-toolroom-institution) |
| `prn_cataloguing_system` | 200.0 | [`prn_library_archive`](89_remaining_arts.md#prn_library_archive---library-archive-cataloguing-indexing-copyright-economics) |
| `prn_copyright_economics` | 150.0 | [`prn_library_archive`](89_remaining_arts.md#prn_library_archive---library-archive-cataloguing-indexing-copyright-economics) |
| `prn_index_concordance` | 300.0 | [`prn_library_archive`](89_remaining_arts.md#prn_library_archive---library-archive-cataloguing-indexing-copyright-economics) |
| `prn_library_archive` | 0.0 | [`prn_library_archive`](89_remaining_arts.md#prn_library_archive---library-archive-cataloguing-indexing-copyright-economics) |
| `sc2_institution_citation` | 80.0 | [`sc2_institution_journal`](89_remaining_arts.md#sc2_institution_journal---scientific-publication-journal-learned-society-citation-peer-review) |
| `sc2_institution_curriculum` | 120.0 | [`sc2_institution_curriculum`](89_remaining_arts.md#sc2_institution_curriculum---academic-teaching-institutions-curriculum-textbook-examination-doctorate) |
| `sc2_institution_doctorate` | 150.0 | [`sc2_institution_curriculum`](89_remaining_arts.md#sc2_institution_curriculum---academic-teaching-institutions-curriculum-textbook-examination-doctorate) |
| `sc2_institution_examination` | 80.0 | [`sc2_institution_curriculum`](89_remaining_arts.md#sc2_institution_curriculum---academic-teaching-institutions-curriculum-textbook-examination-doctorate) |
| `sc2_institution_funded_programme` | 120.0 | [`sc2_institution_funded_programme`](89_remaining_arts.md#sc2_institution_funded_programme---research-funding-and-management) |
| `sc2_institution_journal` | 110.0 | [`sc2_institution_journal`](89_remaining_arts.md#sc2_institution_journal---scientific-publication-journal-learned-society-citation-peer-review) |
| `sc2_institution_learned_society` | 100.0 | [`sc2_institution_journal`](89_remaining_arts.md#sc2_institution_journal---scientific-publication-journal-learned-society-citation-peer-review) |
| `sc2_institution_patent_disclosure` | 100.0 | [`sc2_institution_funded_programme`](89_remaining_arts.md#sc2_institution_funded_programme---research-funding-and-management) |
| `sc2_institution_referee` | 100.0 | [`sc2_institution_journal`](89_remaining_arts.md#sc2_institution_journal---scientific-publication-journal-learned-society-citation-peer-review) |
| `sc2_institution_research_group` | 100.0 | [`sc2_institution_funded_programme`](89_remaining_arts.md#sc2_institution_funded_programme---research-funding-and-management) |
| `sc2_institution_textbook` | 200.0 | [`sc2_institution_curriculum`](89_remaining_arts.md#sc2_institution_curriculum---academic-teaching-institutions-curriculum-textbook-examination-doctorate) |
| `sc2_method_controlled_experiment` | 100.0 | [`sc2_method_hypothesis`](89_remaining_arts.md#sc2_method_hypothesis---hypothesis-controlled-experiment-lab-notebook-replication-peer-criticism-negative-results) |
| `sc2_method_hypothesis` | 90.0 | [`sc2_method_hypothesis`](89_remaining_arts.md#sc2_method_hypothesis---hypothesis-controlled-experiment-lab-notebook-replication-peer-criticism-negative-results) |
| `sc2_method_lab_notebook` | 70.0 | [`sc2_method_hypothesis`](89_remaining_arts.md#sc2_method_hypothesis---hypothesis-controlled-experiment-lab-notebook-replication-peer-criticism-negative-results) |
| `sc2_method_negative_result` | 90.0 | [`sc2_method_hypothesis`](89_remaining_arts.md#sc2_method_hypothesis---hypothesis-controlled-experiment-lab-notebook-replication-peer-criticism-negative-results) |
| `sc2_method_peer_criticism` | 100.0 | [`sc2_method_hypothesis`](89_remaining_arts.md#sc2_method_hypothesis---hypothesis-controlled-experiment-lab-notebook-replication-peer-criticism-negative-results) |
| `sc2_method_replication` | 80.0 | [`sc2_method_hypothesis`](89_remaining_arts.md#sc2_method_hypothesis---hypothesis-controlled-experiment-lab-notebook-replication-peer-criticism-negative-results) |
| `sc2_physics_acoustics` | 120.0 | [`sc2_physics_elasticity`](89_remaining_arts.md#sc2_physics_elasticity---elasticity-wave-motion-acoustics-aerodynamic-lift) |
| `sc2_physics_aerodynamic_lift` | 130.0 | [`sc2_physics_elasticity`](89_remaining_arts.md#sc2_physics_elasticity---elasticity-wave-motion-acoustics-aerodynamic-lift) |
| `sc2_physics_blackbody_radiation` | 140.0 | [`sc2_physics_kinetic_theory`](89_remaining_arts.md#sc2_physics_kinetic_theory---kinetic-theory-and-statistical-mechanics) |
| `sc2_physics_boltzmann_distribution` | 120.0 | [`sc2_physics_kinetic_theory`](89_remaining_arts.md#sc2_physics_kinetic_theory---kinetic-theory-and-statistical-mechanics) |
| `sc2_physics_diffraction` | 120.0 | [`sc2_physics_geometric_optics`](89_remaining_arts.md#sc2_physics_geometric_optics---optics-geometric-rays-diffraction-speed-of-light) |
| `sc2_physics_elasticity` | 110.0 | [`sc2_physics_elasticity`](89_remaining_arts.md#sc2_physics_elasticity---elasticity-wave-motion-acoustics-aerodynamic-lift) |
| `sc2_physics_electrostatics` | 100.0 | [`sc2_physics_electrostatics`](89_remaining_arts.md#sc2_physics_electrostatics---electromagnetism-electrostatics-magnetostatics-maxwells-equations-em-waves-spectrum) |
| `sc2_physics_em_wave` | 120.0 | [`sc2_physics_electrostatics`](89_remaining_arts.md#sc2_physics_electrostatics---electromagnetism-electrostatics-magnetostatics-maxwells-equations-em-waves-spectrum) |
| `sc2_physics_energy` | 110.0 | [`sc2_physics_newtons_laws`](89_remaining_arts.md#sc2_physics_newtons_laws---classical-mechanics-newtons-laws-kinematics-momentum-energy-work-gravitation) |
| `sc2_physics_fluid_statics` | 80.0 | [`sc2_physics_fluid_statics`](89_remaining_arts.md#sc2_physics_fluid_statics---fluid-mechanics-statics-bernoulli-viscosity-reynolds-number) |
| `sc2_physics_geometric_optics` | 100.0 | [`sc2_physics_geometric_optics`](89_remaining_arts.md#sc2_physics_geometric_optics---optics-geometric-rays-diffraction-speed-of-light) |
| `sc2_physics_gravitation` | 100.0 | [`sc2_physics_newtons_laws`](89_remaining_arts.md#sc2_physics_newtons_laws---classical-mechanics-newtons-laws-kinematics-momentum-energy-work-gravitation) |
| `sc2_physics_hydrodynamics` | 130.0 | [`sc2_physics_fluid_statics`](89_remaining_arts.md#sc2_physics_fluid_statics---fluid-mechanics-statics-bernoulli-viscosity-reynolds-number) |
| `sc2_physics_kinematics` | 90.0 | [`sc2_physics_newtons_laws`](89_remaining_arts.md#sc2_physics_newtons_laws---classical-mechanics-newtons-laws-kinematics-momentum-energy-work-gravitation) |
| `sc2_physics_kinetic_theory` | 130.0 | [`sc2_physics_kinetic_theory`](89_remaining_arts.md#sc2_physics_kinetic_theory---kinetic-theory-and-statistical-mechanics) |
| `sc2_physics_magnetostatics` | 100.0 | [`sc2_physics_electrostatics`](89_remaining_arts.md#sc2_physics_electrostatics---electromagnetism-electrostatics-magnetostatics-maxwells-equations-em-waves-spectrum) |
| `sc2_physics_maxwell_equations` | 140.0 | [`sc2_physics_electrostatics`](89_remaining_arts.md#sc2_physics_electrostatics---electromagnetism-electrostatics-magnetostatics-maxwells-equations-em-waves-spectrum) |
| `sc2_physics_momentum` | 80.0 | [`sc2_physics_newtons_laws`](89_remaining_arts.md#sc2_physics_newtons_laws---classical-mechanics-newtons-laws-kinematics-momentum-energy-work-gravitation) |
| `sc2_physics_neutron_discovery` | 110.0 | [`sc2_physics_quantum_photon`](89_remaining_arts.md#sc2_physics_quantum_photon---quantum-and-nuclear-physics-photon-photoelectric-effect-uncertainty-wave-mechanics-nucleus-neutron-fission) |
| `sc2_physics_newtons_laws` | 100.0 | [`sc2_physics_newtons_laws`](89_remaining_arts.md#sc2_physics_newtons_laws---classical-mechanics-newtons-laws-kinematics-momentum-energy-work-gravitation) |
| `sc2_physics_nuclear_fission` | 140.0 | [`sc2_physics_quantum_photon`](89_remaining_arts.md#sc2_physics_quantum_photon---quantum-and-nuclear-physics-photon-photoelectric-effect-uncertainty-wave-mechanics-nucleus-neutron-fission) |
| `sc2_physics_nucleus_discovery` | 120.0 | [`sc2_physics_quantum_photon`](89_remaining_arts.md#sc2_physics_quantum_photon---quantum-and-nuclear-physics-photon-photoelectric-effect-uncertainty-wave-mechanics-nucleus-neutron-fission) |
| `sc2_physics_photoelectric_effect` | 110.0 | [`sc2_physics_quantum_photon`](89_remaining_arts.md#sc2_physics_quantum_photon---quantum-and-nuclear-physics-photon-photoelectric-effect-uncertainty-wave-mechanics-nucleus-neutron-fission) |
| `sc2_physics_quantum_photon` | 120.0 | [`sc2_physics_quantum_photon`](89_remaining_arts.md#sc2_physics_quantum_photon---quantum-and-nuclear-physics-photon-photoelectric-effect-uncertainty-wave-mechanics-nucleus-neutron-fission) |
| `sc2_physics_reynolds_number` | 110.0 | [`sc2_physics_fluid_statics`](89_remaining_arts.md#sc2_physics_fluid_statics---fluid-mechanics-statics-bernoulli-viscosity-reynolds-number) |
| `sc2_physics_spectrum` | 100.0 | [`sc2_physics_electrostatics`](89_remaining_arts.md#sc2_physics_electrostatics---electromagnetism-electrostatics-magnetostatics-maxwells-equations-em-waves-spectrum) |
| `sc2_physics_speed_of_light` | 100.0 | [`sc2_physics_geometric_optics`](89_remaining_arts.md#sc2_physics_geometric_optics---optics-geometric-rays-diffraction-speed-of-light) |
| `sc2_physics_statistical_mechanics` | 160.0 | [`sc2_physics_kinetic_theory`](89_remaining_arts.md#sc2_physics_kinetic_theory---kinetic-theory-and-statistical-mechanics) |
| `sc2_physics_uncertainty_principle` | 120.0 | [`sc2_physics_quantum_photon`](89_remaining_arts.md#sc2_physics_quantum_photon---quantum-and-nuclear-physics-photon-photoelectric-effect-uncertainty-wave-mechanics-nucleus-neutron-fission) |
| `sc2_physics_viscosity` | 120.0 | [`sc2_physics_fluid_statics`](89_remaining_arts.md#sc2_physics_fluid_statics---fluid-mechanics-statics-bernoulli-viscosity-reynolds-number) |
| `sc2_physics_wave_mechanics` | 180.0 | [`sc2_physics_quantum_photon`](89_remaining_arts.md#sc2_physics_quantum_photon---quantum-and-nuclear-physics-photon-photoelectric-effect-uncertainty-wave-mechanics-nucleus-neutron-fission) |
| `sc2_physics_wave_motion` | 130.0 | [`sc2_physics_elasticity`](89_remaining_arts.md#sc2_physics_elasticity---elasticity-wave-motion-acoustics-aerodynamic-lift) |
| `sc2_physics_work_power` | 100.0 | [`sc2_physics_newtons_laws`](89_remaining_arts.md#sc2_physics_newtons_laws---classical-mechanics-newtons-laws-kinematics-momentum-energy-work-gravitation) |

### 90_textiles.md

| Node | Your hours | Recipe |
|---|---:|---|
| `mat_dyes_synthetic` | 200.0 | _(module has no anchor)_ |
| `mat_linen` | 0.0 | _(module has no anchor)_ |
| `tex_buttons_buttonholes` | 50.0 | _(module has no anchor)_ |
| `tex_calico_printing` | 140.0 | _(module has no anchor)_ |
| `tex_canvas` | 40.0 | _(module has no anchor)_ |
| `tex_chlorine_bleaching` | 120.0 | _(module has no anchor)_ |
| `tex_chrome_tanning` | 140.0 | _(module has no anchor)_ |
| `tex_cotton_gin` | 80.0 | _(module has no anchor)_ |
| `tex_cotton_trade` | 0.0 | _(module has no anchor)_ |
| `tex_drop_spindle` | 0.0 | _(module has no anchor)_ |
| `tex_dye_madder` | 0.0 | _(module has no anchor)_ |
| `tex_dye_murex` | 0.0 | _(module has no anchor)_ |
| `tex_dye_woad` | 0.0 | _(module has no anchor)_ |
| `tex_felting` | 0.0 | _(module has no anchor)_ |
| `tex_field_bleaching` | 50.0 | _(module has no anchor)_ |
| `tex_fitted_garment` | 50.0 | _(module has no anchor)_ |
| `tex_flying_shuttle` | 120.0 | _(module has no anchor)_ |
| `tex_fulling_water` | 120.0 | _(module has no anchor)_ |
| `tex_hand_ginning` | 30.0 | _(module has no anchor)_ |
| `tex_horizontal_loom` | 80.0 | _(module has no anchor)_ |
| `tex_hosiery` | 70.0 | _(module has no anchor)_ |
| `tex_indigo` | 60.0 | _(module has no anchor)_ |
| `tex_knitting_frame` | 150.0 | _(module has no anchor)_ |
| `tex_mercerisation` | 100.0 | _(module has no anchor)_ |
| `tex_mordanting` | 40.0 | _(module has no anchor)_ |
| `tex_pattern_cutting` | 80.0 | _(module has no anchor)_ |
| `tex_power_loom` | 250.0 | _(module has no anchor)_ |
| `tex_rayon_nitro` | 180.0 | _(module has no anchor)_ |
| `tex_rayon_viscose` | 200.0 | _(module has no anchor)_ |
| `tex_roller_printing` | 180.0 | _(module has no anchor)_ |
| `tex_rope_walk` | 70.0 | _(module has no anchor)_ |
| `tex_sailcloth` | 0.0 | _(module has no anchor)_ |
| `tex_sewing_machine` | 160.0 | _(module has no anchor)_ |
| `tex_shoddy` | 40.0 | _(module has no anchor)_ |
| `tex_silk_trade` | 0.0 | _(module has no anchor)_ |
| `tex_spinning_jenny` | 100.0 | _(module has no anchor)_ |
| `tex_spinning_mule` | 200.0 | _(module has no anchor)_ |
| `tex_spinning_wheel` | 100.0 | _(module has no anchor)_ |
| `tex_tape_measure` | 40.0 | _(module has no anchor)_ |
| `tex_textile_factory` | 300.0 | _(module has no anchor)_ |
| `tex_treadle_loom` | 90.0 | _(module has no anchor)_ |
| `tex_two_beam_loom` | 0.0 | _(module has no anchor)_ |
| `tex_vegetable_tanning` | 100.0 | _(module has no anchor)_ |
| `tex_warp_weighted_loom` | 0.0 | _(module has no anchor)_ |
| `tex_water_frame` | 280.0 | _(module has no anchor)_ |
| `tex_wool` | 0.0 | _(module has no anchor)_ |
| `tex_wool_combing_machinery` | 180.0 | _(module has no anchor)_ |
| `tx2_acrylic` | 170.0 | _(module has no anchor)_ |
| `tx2_alum_tanning` | 60.0 | _(module has no anchor)_ |
| `tx2_asbestos_cloth` | 80.0 | _(module has no anchor)_ |
| `tx2_automatic_bobbin_changer` | 140.0 | _(module has no anchor)_ |
| `tx2_automatic_loom` | 180.0 | _(module has no anchor)_ |
| `tx2_ballpoint_pen` | 120.0 | _(module has no anchor)_ |
| `tx2_band_knife` | 100.0 | _(module has no anchor)_ |
| `tx2_beam` | 40.0 | _(module has no anchor)_ |
| `tx2_bicycle_consumer` | 140.0 | _(module has no anchor)_ |
| `tx2_bleaching_chlorine` | 80.0 | _(module has no anchor)_ |
| `tx2_bleaching_peroxide` | 90.0 | _(module has no anchor)_ |
| `tx2_bleaching_sun` | 30.0 | _(module has no anchor)_ |
| `tx2_board_game` | 100.0 | _(module has no anchor)_ |
| `tx2_bobbin_and_flyer` | 50.0 | _(module has no anchor)_ |
| `tx2_bottle` | 60.0 | _(module has no anchor)_ |
| `tx2_brassiere` | 100.0 | _(module has no anchor)_ |
| `tx2_button_bone` | 40.0 | _(module has no anchor)_ |
| `tx2_button_horn` | 40.0 | _(module has no anchor)_ |
| `tx2_button_plastic` | 70.0 | _(module has no anchor)_ |
| `tx2_button_shell` | 50.0 | _(module has no anchor)_ |
| `tx2_buttonhole_machine` | 120.0 | _(module has no anchor)_ |
| `tx2_calendering` | 80.0 | _(module has no anchor)_ |
| `tx2_camera_consumer` | 130.0 | _(module has no anchor)_ |
| `tx2_cap_frame` | 80.0 | _(module has no anchor)_ |
| `tx2_cardboard_box` | 70.0 | _(module has no anchor)_ |
| `tx2_carding` | 60.0 | _(module has no anchor)_ |
| `tx2_cashmere` | 50.0 | _(module has no anchor)_ |
| `tx2_chain_stitch` | 90.0 | _(module has no anchor)_ |
| `tx2_circular_knitting` | 120.0 | _(module has no anchor)_ |
| `tx2_clockwork_toy` | 110.0 | _(module has no anchor)_ |
| `tx2_comb` | 50.0 | _(module has no anchor)_ |
| `tx2_combing` | 50.0 | _(module has no anchor)_ |
| `tx2_cordage_paperboard` | 50.0 | _(module has no anchor)_ |
| `tx2_corrugated_box` | 100.0 | _(module has no anchor)_ |
| `tx2_corset` | 100.0 | _(module has no anchor)_ |
| `tx2_cotton_ginning` | 120.0 | _(module has no anchor)_ |
| `tx2_count_standard` | 40.0 | _(module has no anchor)_ |
| `tx2_cropping` | 90.0 | _(module has no anchor)_ |
| `tx2_currying` | 60.0 | _(module has no anchor)_ |
| `tx2_cutting_table` | 60.0 | _(module has no anchor)_ |
| `tx2_desizing` | 50.0 | _(module has no anchor)_ |
| `tx2_discharge_printing` | 100.0 | _(module has no anchor)_ |
| `tx2_dobby` | 140.0 | _(module has no anchor)_ |
| `tx2_doll` | 80.0 | _(module has no anchor)_ |
| `tx2_doubling_frame` | 70.0 | _(module has no anchor)_ |
| `tx2_drawing` | 50.0 | _(module has no anchor)_ |
| `tx2_drawing_pin` | 50.0 | _(module has no anchor)_ |
| `tx2_dyeing_fibre` | 60.0 | _(module has no anchor)_ |
| `tx2_dyeing_garment` | 90.0 | _(module has no anchor)_ |
| `tx2_dyeing_piece` | 80.0 | _(module has no anchor)_ |
| `tx2_dyeing_yarn` | 70.0 | _(module has no anchor)_ |
| `tx2_elastic` | 90.0 | _(module has no anchor)_ |
| `tx2_embossing` | 80.0 | _(module has no anchor)_ |
| `tx2_envelope_flap` | 60.0 | _(module has no anchor)_ |
| `tx2_envelope_gummed` | 60.0 | _(module has no anchor)_ |
| `tx2_eraser` | 70.0 | _(module has no anchor)_ |
| `tx2_eye_pointed_needle` | 50.0 | _(module has no anchor)_ |
| `tx2_flameproofing` | 100.0 | _(module has no anchor)_ |
| `tx2_flax_fibre` | 40.0 | _(module has no anchor)_ |
| `tx2_flyer` | 70.0 | _(module has no anchor)_ |
| `tx2_friction_match` | 80.0 | _(module has no anchor)_ |
| `tx2_fulling` | 60.0 | _(module has no anchor)_ |
| `tx2_gilling` | 40.0 | _(module has no anchor)_ |
| `tx2_glass_fibre` | 130.0 | _(module has no anchor)_ |
| `tx2_gramophone` | 140.0 | _(module has no anchor)_ |
| `tx2_hackling` | 40.0 | _(module has no anchor)_ |
| `tx2_heddle` | 40.0 | _(module has no anchor)_ |
| `tx2_hemp_fibre` | 40.0 | _(module has no anchor)_ |
| `tx2_hook_and_eye` | 50.0 | _(module has no anchor)_ |
| `tx2_jacquard_cards` | 80.0 | _(module has no anchor)_ |
| `tx2_jacquard_head` | 200.0 | _(module has no anchor)_ |
| `tx2_jute_fibre` | 50.0 | _(module has no anchor)_ |
| `tx2_lasting_machine` | 120.0 | _(module has no anchor)_ |
| `tx2_latch_needle` | 90.0 | _(module has no anchor)_ |
| `tx2_let_off_motion` | 60.0 | _(module has no anchor)_ |
| `tx2_lockstitch` | 100.0 | _(module has no anchor)_ |
| `tx2_mass_soap` | 80.0 | _(module has no anchor)_ |
| `tx2_mercerising` | 100.0 | _(module has no anchor)_ |
| `tx2_milling` | 40.0 | _(module has no anchor)_ |
| `tx2_mirror` | 70.0 | _(module has no anchor)_ |
| `tx2_mohair` | 50.0 | _(module has no anchor)_ |
| `tx2_mothproofing` | 90.0 | _(module has no anchor)_ |
| `tx2_mule_jenny` | 160.0 | _(module has no anchor)_ |
| `tx2_needle` | 40.0 | _(module has no anchor)_ |
| `tx2_nylon_6_6` | 180.0 | _(module has no anchor)_ |
| `tx2_overlock_stitch` | 110.0 | _(module has no anchor)_ |
| `tx2_paper_bag` | 60.0 | _(module has no anchor)_ |
| `tx2_paper_pattern` | 100.0 | _(module has no anchor)_ |
| `tx2_paperclip` | 50.0 | _(module has no anchor)_ |
| `tx2_pattern_grading` | 80.0 | _(module has no anchor)_ |
| `tx2_permanent_press` | 120.0 | _(module has no anchor)_ |
| `tx2_picking_mechanism` | 100.0 | _(module has no anchor)_ |
| `tx2_pin` | 40.0 | _(module has no anchor)_ |
| `tx2_playing_card` | 100.0 | _(module has no anchor)_ |
| `tx2_polyester` | 180.0 | _(module has no anchor)_ |
| `tx2_postcard` | 70.0 | _(module has no anchor)_ |
| `tx2_press_stud` | 80.0 | _(module has no anchor)_ |
| `tx2_printing_block` | 100.0 | _(module has no anchor)_ |
| `tx2_printing_roller` | 160.0 | _(module has no anchor)_ |
| `tx2_printing_screen` | 120.0 | _(module has no anchor)_ |
| `tx2_radio_set` | 150.0 | _(module has no anchor)_ |
| `tx2_raising` | 80.0 | _(module has no anchor)_ |
| `tx2_ramie_fibre` | 50.0 | _(module has no anchor)_ |
| `tx2_rayon_acetate` | 140.0 | _(module has no anchor)_ |
| `tx2_rayon_cupro` | 150.0 | _(module has no anchor)_ |
| `tx2_razor_blade` | 100.0 | _(module has no anchor)_ |
| `tx2_ready_to_wear` | 120.0 | _(module has no anchor)_ |
| `tx2_resist_dyeing` | 70.0 | _(module has no anchor)_ |
| `tx2_retting` | 30.0 | _(module has no anchor)_ |
| `tx2_ring_frame` | 120.0 | _(module has no anchor)_ |
| `tx2_rope_lay` | 40.0 | _(module has no anchor)_ |
| `tx2_ropemaking_machine` | 110.0 | _(module has no anchor)_ |
| `tx2_roving_frame` | 60.0 | _(module has no anchor)_ |
| `tx2_rubber_soles` | 100.0 | _(module has no anchor)_ |
| `tx2_safety_match` | 100.0 | _(module has no anchor)_ |
| `tx2_scouring` | 40.0 | _(module has no anchor)_ |
| `tx2_screw_cap` | 80.0 | _(module has no anchor)_ |
| `tx2_scutching` | 50.0 | _(module has no anchor)_ |
| `tx2_selvedge` | 40.0 | _(module has no anchor)_ |
| `tx2_sericulture` | 80.0 | _(module has no anchor)_ |
| `tx2_sewing_machine_domestic` | 140.0 | _(module has no anchor)_ |
| `tx2_sewing_machine_industrial` | 150.0 | _(module has no anchor)_ |
| `tx2_shaft` | 50.0 | _(module has no anchor)_ |
| `tx2_shampoo` | 100.0 | _(module has no anchor)_ |
| `tx2_shearing` | 70.0 | _(module has no anchor)_ |
| `tx2_shed` | 30.0 | _(module has no anchor)_ |
| `tx2_shoemaking_mechanised` | 150.0 | _(module has no anchor)_ |
| `tx2_shuttle` | 50.0 | _(module has no anchor)_ |
| `tx2_silk_fibre` | 40.0 | _(module has no anchor)_ |
| `tx2_singeing` | 60.0 | _(module has no anchor)_ |
| `tx2_sizing_systems` | 100.0 | _(module has no anchor)_ |
| `tx2_sliver_preparation` | 40.0 | _(module has no anchor)_ |
| `tx2_spectacle_frame` | 60.0 | _(module has no anchor)_ |
| `tx2_splitting` | 70.0 | _(module has no anchor)_ |
| `tx2_stapler` | 100.0 | _(module has no anchor)_ |
| `tx2_stocking_frame` | 140.0 | _(module has no anchor)_ |
| `tx2_take_up_motion` | 60.0 | _(module has no anchor)_ |
| `tx2_temple` | 40.0 | _(module has no anchor)_ |
| `tx2_throstle_frame` | 100.0 | _(module has no anchor)_ |
| `tx2_tin_can` | 80.0 | _(module has no anchor)_ |
| `tx2_tin_toy` | 90.0 | _(module has no anchor)_ |
| `tx2_toothpaste_tube` | 100.0 | _(module has no anchor)_ |
| `tx2_twist_insertion` | 50.0 | _(module has no anchor)_ |
| `tx2_warp_knitting` | 130.0 | _(module has no anchor)_ |
| `tx2_warp_sizing` | 50.0 | _(module has no anchor)_ |
| `tx2_warping_mill` | 60.0 | _(module has no anchor)_ |
| `tx2_watch_case` | 80.0 | _(module has no anchor)_ |
| `tx2_waterproofing` | 80.0 | _(module has no anchor)_ |
| `tx2_wild_silk` | 70.0 | _(module has no anchor)_ |
| `tx2_wool_fibre` | 40.0 | _(module has no anchor)_ |
| `tx2_worsted` | 60.0 | _(module has no anchor)_ |

### 91_household.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `hom_board_games` | 0 | 0.0 | _(module has no anchor)_ |
| `hom_candle_beeswax` | 0 | 0.0 | _(module has no anchor)_ |
| `hom_candle_tallow` | 0 | 0.0 | _(module has no anchor)_ |
| `hom_cosmetics_roman` | 0 | 20.0 | _(module has no anchor)_ |
| `hom_flush_latrine_simple` | 0 | 0.0 | _(module has no anchor)_ |
| `hom_furniture_wooden` | 0 | 0.0 | _(module has no anchor)_ |
| `hom_hypocaust` | 0 | 0.0 | _(module has no anchor)_ |
| `hom_lead_plumbing` | 0 | 0.0 | _(module has no anchor)_ |
| `hom_locks_keys` | 0 | 0.0 | _(module has no anchor)_ |
| `hom_mirror_bronze_polished` | 0 | 0.0 | _(module has no anchor)_ |
| `hom_musical_instruments` | 0 | 0.0 | _(module has no anchor)_ |
| `hom_oil_lamp_simple` | 0 | 0.0 | _(module has no anchor)_ |
| `hom_perfume_enfleurage` | 0 | 0.0 | _(module has no anchor)_ |
| `hom_public_bath` | 0 | 0.0 | _(module has no anchor)_ |
| `hom_button` | 1 | 40.0 | _(module has no anchor)_ |
| `hom_eraser_breadcrumb` | 1 | 30.0 | _(module has no anchor)_ |
| `hom_fireplace_chimney` | 1 | 120.0 | _(module has no anchor)_ |
| `hom_flush_toilet_trap` | 1 | 80.0 | _(module has no anchor)_ |
| `hom_jigsaw_puzzle` | 1 | 100.0 | _(module has no anchor)_ |
| `hom_latrine_water_trap` | 1 | 60.0 | _(module has no anchor)_ |
| `hom_mirror_silvered_glass` | 1 | 150.0 | _(module has no anchor)_ |
| `hom_pencil` | 1 | 80.0 | _(module has no anchor)_ |
| `hom_playing_cards_printed` | 1 | 60.0 | _(module has no anchor)_ |
| `hom_punkah_ceiling` | 1 | 50.0 | _(module has no anchor)_ |
| `hom_safety_pin` | 1 | 40.0 | _(module has no anchor)_ |
| `hom_spectacles` | 1 | 90.0 | _(module has no anchor)_ |
| `hom_toothbrush` | 1 | 60.0 | _(module has no anchor)_ |
| `hom_umbrella` | 1 | 80.0 | _(module has no anchor)_ |
| `hom_kitchen_range` | 2 | 130.0 | _(module has no anchor)_ |
| `hom_lamp_argand` | 2 | 100.0 | _(module has no anchor)_ |
| `hom_lamp_kerosene` | 2 | 90.0 | _(module has no anchor)_ |
| `hom_mangle_wringer` | 2 | 100.0 | _(module has no anchor)_ |
| `hom_matches_friction` | 2 | 60.0 | _(module has no anchor)_ |
| `hom_mechanical_clock_home` | 2 | 180.0 | _(module has no anchor)_ |
| `hom_metronome` | 2 | 110.0 | _(module has no anchor)_ |
| `hom_perfume_distilled` | 2 | 140.0 | _(module has no anchor)_ |
| `hom_piano` | 2 | 250.0 | _(module has no anchor)_ |
| `hom_pocket_watch` | 2 | 200.0 | _(module has no anchor)_ |
| `hom_pressure_cooker` | 2 | 150.0 | _(module has no anchor)_ |
| `hom_printed_books` | 2 | 160.0 | _(module has no anchor)_ |
| `hom_sewing_machine_hand` | 2 | 180.0 | _(module has no anchor)_ |
| `hom_sprung_mattress` | 2 | 120.0 | _(module has no anchor)_ |
| `hom_stove_enclosed` | 2 | 100.0 | _(module has no anchor)_ |
| `hom_toys_dolls` | 2 | 60.0 | _(module has no anchor)_ |
| `hom_washing_machine_hand` | 2 | 140.0 | _(module has no anchor)_ |
| `if_fountain_pen` | 2 | 130.0 | _(module has no anchor)_ |
| `hom_attar_roses` | 3 | 150.0 | _(module has no anchor)_ |
| `hom_bath_piped_hot_water` | 3 | 140.0 | _(module has no anchor)_ |
| `hom_carpet_sweeper` | 3 | 100.0 | _(module has no anchor)_ |
| `hom_deodorant` | 3 | 70.0 | _(module has no anchor)_ |
| `hom_doll_fashion` | 3 | 110.0 | _(module has no anchor)_ |
| `hom_double_glazing` | 3 | 120.0 | _(module has no anchor)_ |
| `hom_gas_lamp` | 3 | 140.0 | _(module has no anchor)_ |
| `hom_safety_razor` | 3 | 120.0 | _(module has no anchor)_ |
| `hom_sewer_stormwater_separation` | 3 | 180.0 | _(module has no anchor)_ |
| `hom_shampoo_soap_based` | 3 | 80.0 | _(module has no anchor)_ |
| `hom_toothpaste_commercial` | 3 | 90.0 | _(module has no anchor)_ |
| `hom_vacuum_flask` | 3 | 120.0 | _(module has no anchor)_ |
| `hom_zip_fastener` | 3 | 180.0 | _(module has no anchor)_ |
| `hom_cosmetics_modern_warning` | 4 | 100.0 | _(module has no anchor)_ |
| `hom_dishwasher` | 4 | 200.0 | _(module has no anchor)_ |
| `hom_electric_fan` | 4 | 100.0 | _(module has no anchor)_ |
| `hom_electric_lighting` | 4 | 150.0 | _(module has no anchor)_ |
| `hom_refrigerator_home_electric` | 4 | 200.0 | _(module has no anchor)_ |
| `hom_vacuum_cleaner` | 4 | 140.0 | _(module has no anchor)_ |
| `hom_washing_machine_electric` | 4 | 160.0 | _(module has no anchor)_ |
| `mat_ice_artificial` | 4 | 200.0 | _(module has no anchor)_ |

### 95_expeditions.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `exp_provisioning_scurvy` | 1 | 200.0 | _(module has no anchor)_ |
| `exp_trade_route_extend` | 1 | 250.0 | _(module has no anchor)_ |
| `exp_coastal_africa` | 2 | 350.0 | _(module has no anchor)_ |
| `exp_oceangoing_hull` | 2 | 250.0 | _(module has no anchor)_ |
| `exp_openocean_navigation` | 2 | 300.0 | _(module has no anchor)_ |
| `exp_africa_circumnavigation` | 3 | 400.0 | _(module has no anchor)_ |
| `exp_atlantic_crossing` | 3 | 400.0 | _(module has no anchor)_ |
| `exp_colony_administration` | 3 | 400.0 | _(module has no anchor)_ |
| `exp_import_draught_animals` | 3 | 300.0 | [`transplant_botany`](95_expeditions.md#transplant_botany---moving-the-garden) |
| `exp_transplant_botany` | 3 | 350.0 | _(module has no anchor)_ |
| `exp_americas_factory` | 4 | 500.0 | _(module has no anchor)_ |
| `exp_conquest_resource` | 4 | 300.0 | _(module has no anchor)_ |

### 96_finance.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `fin_annona` | 0 | 600.0 | _(module has no anchor)_ |
| `fin_argentarii` | 0 | 150.0 | _(module has no anchor)_ |
| `fin_auction` | 0 | 0.0 | _(module has no anchor)_ |
| `fin_coined_money` | 0 | 0.0 | _(module has no anchor)_ |
| `fin_contract_law` | 0 | 0.0 | _(module has no anchor)_ |
| `fin_maritime_loan` | 0 | 0.0 | _(module has no anchor)_ |
| `fin_market` | 0 | 0.0 | _(module has no anchor)_ |
| `fin_tax_farming` | 0 | 0.0 | _(module has no anchor)_ |
| `fin_testament` | 0 | 0.0 | _(module has no anchor)_ |
| `fin_wage` | 0 | 0.0 | _(module has no anchor)_ |
| `fin_apprenticeship` | 1 | 80.0 | _(module has no anchor)_ |
| `fin_arabic_numerals` | 1 | 120.0 | _(module has no anchor)_ |
| `fin_employment_contract` | 1 | 60.0 | _(module has no anchor)_ |
| `fin_ferry` | 1 | 100.0 | _(module has no anchor)_ |
| `fin_gambling_house` | 1 | 100.0 | _(module has no anchor)_ |
| `fin_hotel` | 1 | 120.0 | _(module has no anchor)_ |
| `fin_inn` | 1 | 100.0 | _(module has no anchor)_ |
| `fin_pawnshop` | 1 | 60.0 | _(module has no anchor)_ |
| `fin_trading_post` | 1 | 100.0 | _(module has no anchor)_ |
| `fin_almanac` | 2 | 150.0 | _(module has no anchor)_ |
| `fin_arbitrage` | 2 | 80.0 | _(module has no anchor)_ |
| `fin_bankruptcy` | 2 | 120.0 | _(module has no anchor)_ |
| `fin_bill_exchange` | 2 | 150.0 | _(module has no anchor)_ |
| `fin_bimetallism` | 2 | 100.0 | _(module has no anchor)_ |
| `fin_brand` | 2 | 100.0 | _(module has no anchor)_ |
| `fin_cartel` | 2 | 100.0 | _(module has no anchor)_ |
| `fin_cheque` | 2 | 100.0 | _(module has no anchor)_ |
| `fin_coffeehouse` | 2 | 120.0 | _(module has no anchor)_ |
| `fin_deposit_bank` | 2 | 200.0 | _(module has no anchor)_ |
| `fin_discounting` | 2 | 120.0 | _(module has no anchor)_ |
| `fin_double_entry` | 2 | 200.0 | _(module has no anchor)_ |
| `fin_endorsement` | 2 | 100.0 | _(module has no anchor)_ |
| `fin_factory` | 2 | 180.0 | _(module has no anchor)_ |
| `fin_fractional_reserve` | 2 | 150.0 | _(module has no anchor)_ |
| `fin_ledger` | 2 | 100.0 | _(module has no anchor)_ |
| `fin_lending_library` | 2 | 140.0 | _(module has no anchor)_ |
| `fin_lottery` | 2 | 150.0 | _(module has no anchor)_ |
| `fin_monopoly` | 2 | 80.0 | _(module has no anchor)_ |
| `fin_mortgage` | 2 | 120.0 | _(module has no anchor)_ |
| `fin_plantation` | 2 | 200.0 | _(module has no anchor)_ |
| `fin_postal_service` | 2 | 180.0 | _(module has no anchor)_ |
| `fin_professional_sport` | 2 | 140.0 | _(module has no anchor)_ |
| `fin_promissory_note` | 2 | 80.0 | _(module has no anchor)_ |
| `fin_racecourse` | 2 | 130.0 | _(module has no anchor)_ |
| `fin_restaurant` | 2 | 120.0 | _(module has no anchor)_ |
| `fin_seigniorage` | 2 | 80.0 | _(module has no anchor)_ |
| `fin_tariff` | 2 | 100.0 | _(module has no anchor)_ |
| `fin_theatre_business` | 2 | 150.0 | _(module has no anchor)_ |
| `fin_toll_bridge` | 2 | 150.0 | _(module has no anchor)_ |
| `fin_trademark` | 2 | 80.0 | _(module has no anchor)_ |
| `fin_trial_balance` | 2 | 80.0 | _(module has no anchor)_ |
| `fin_usury_evasion` | 2 | 80.0 | _(module has no anchor)_ |
| `fin_usury_law` | 2 | 100.0 | _(module has no anchor)_ |
| `fin_advertising` | 3 | 160.0 | _(module has no anchor)_ |
| `fin_annuity` | 3 | 140.0 | _(module has no anchor)_ |
| `fin_bond` | 3 | 120.0 | _(module has no anchor)_ |
| `fin_canal_company` | 3 | 250.0 | _(module has no anchor)_ |
| `fin_central_bank` | 3 | 250.0 | _(module has no anchor)_ |
| `fin_chain_store` | 3 | 200.0 | _(module has no anchor)_ |
| `fin_classified_ad` | 3 | 100.0 | _(module has no anchor)_ |
| `fin_clearing_house` | 3 | 180.0 | _(module has no anchor)_ |
| `fin_company_town` | 3 | 150.0 | _(module has no anchor)_ |
| `fin_copyright` | 3 | 120.0 | _(module has no anchor)_ |
| `fin_department_store` | 3 | 180.0 | _(module has no anchor)_ |
| `fin_directory` | 3 | 140.0 | _(module has no anchor)_ |
| `fin_fire_insurance` | 3 | 180.0 | _(module has no anchor)_ |
| `fin_futures` | 3 | 140.0 | _(module has no anchor)_ |
| `fin_life_insurance` | 3 | 200.0 | _(module has no anchor)_ |
| `fin_limited_liability` | 3 | 200.0 | _(module has no anchor)_ |
| `fin_mail_order` | 3 | 200.0 | _(module has no anchor)_ |
| `fin_marine_insurance` | 3 | 200.0 | _(module has no anchor)_ |
| `fin_news_agency` | 3 | 180.0 | _(module has no anchor)_ |
| `fin_newspaper_business` | 3 | 200.0 | _(module has no anchor)_ |
| `fin_paper_money` | 3 | 200.0 | _(module has no anchor)_ |
| `fin_patent` | 3 | 140.0 | _(module has no anchor)_ |
| `fin_pension` | 3 | 180.0 | _(module has no anchor)_ |
| `fin_public_debt` | 3 | 150.0 | _(module has no anchor)_ |
| `fin_railway_company` | 3 | 300.0 | _(module has no anchor)_ |
| `fin_reinsurance` | 3 | 150.0 | _(module has no anchor)_ |
| `fin_savings_bank` | 3 | 160.0 | _(module has no anchor)_ |
| `fin_share` | 3 | 100.0 | _(module has no anchor)_ |
| `fin_stamp` | 3 | 120.0 | _(module has no anchor)_ |
| `fin_stock_exchange` | 3 | 180.0 | _(module has no anchor)_ |
| `fin_telegraph_business` | 3 | 200.0 | _(module has no anchor)_ |
| `fin_tramway` | 3 | 200.0 | _(module has no anchor)_ |
| `fin_turnpike_trust` | 3 | 200.0 | _(module has no anchor)_ |

### 97_military.md

| Node | Tier | Your hours | Recipe |
|---|---:|---:|---|
| `mil_artillery_carriage` | 1 | 120.0 | _(module has no anchor)_ |
| `mil_artillery_piece` | 1 | 140.0 | _(module has no anchor)_ |
| `mil_bastion` | 1 | 90.0 | _(module has no anchor)_ |
| `mil_fuse_slow_match` | 1 | 30.0 | _(module has no anchor)_ |
| `mil_glacis` | 1 | 60.0 | _(module has no anchor)_ |
| `mil_incorporating_mill` | 1 | 140.0 | _(module has no anchor)_ |
| `mil_powder_mill` | 1 | 120.0 | _(module has no anchor)_ |
| `mil_ravelin` | 1 | 75.0 | _(module has no anchor)_ |
| `mil_serpentine_powder` | 1 | 40.0 | _(module has no anchor)_ |
| `mil_trunnion` | 1 | 80.0 | _(module has no anchor)_ |
| `mil_anti_tank_ditch` | 2 | 50.0 | _(module has no anchor)_ |
| `mil_artillery_shell` | 2 | 60.0 | _(module has no anchor)_ |
| `mil_barbed_wire` | 2 | 50.0 | _(module has no anchor)_ |
| `mil_bomb_general_purpose` | 2 | 70.0 | _(module has no anchor)_ |
| `mil_breech_block` | 2 | 95.0 | _(module has no anchor)_ |
| `mil_breech_loader` | 2 | 95.0 | _(module has no anchor)_ |
| `mil_cartridge_paper` | 2 | 35.0 | _(module has no anchor)_ |
| `mil_casemate` | 2 | 85.0 | _(module has no anchor)_ |
| `mil_chemical_chlorine` | 2 | 60.0 | _(module has no anchor)_ |
| `mil_concrete_fortification` | 2 | 95.0 | _(module has no anchor)_ |
| `mil_flamethrower` | 2 | 75.0 | _(module has no anchor)_ |
| `mil_flintlock` | 2 | 100.0 | _(module has no anchor)_ |
| `mil_fuse_quick_match` | 2 | 40.0 | _(module has no anchor)_ |
| `mil_fuse_types` | 2 | 70.0 | _(module has no anchor)_ |
| `mil_gas_mask` | 2 | 60.0 | _(module has no anchor)_ |
| `mil_high_explosive_shell` | 2 | 100.0 | _(module has no anchor)_ |
| `mil_howitzer` | 2 | 110.0 | _(module has no anchor)_ |
| `mil_incendiary_bomb` | 2 | 70.0 | _(module has no anchor)_ |
| `mil_ironclad` | 2 | 140.0 | _(module has no anchor)_ |
| `mil_lever_action` | 2 | 85.0 | _(module has no anchor)_ |
| `mil_magazine` | 2 | 65.0 | _(module has no anchor)_ |
| `mil_matchlock` | 2 | 60.0 | _(module has no anchor)_ |
| `mil_minie_ball` | 2 | 50.0 | _(module has no anchor)_ |
| `mil_naval_mine` | 2 | 70.0 | _(module has no anchor)_ |
| `mil_observation_balloon` | 2 | 60.0 | _(module has no anchor)_ |
| `mil_percussion_cap` | 2 | 90.0 | _(module has no anchor)_ |
| `mil_pillbox` | 2 | 70.0 | _(module has no anchor)_ |
| `mil_plate_armour_firearms` | 2 | 70.0 | _(module has no anchor)_ |
| `mil_rifling` | 2 | 70.0 | _(module has no anchor)_ |
| `mil_shrapnel_shell` | 2 | 85.0 | _(module has no anchor)_ |
| `mil_torpedo` | 2 | 180.0 | _(module has no anchor)_ |
| `mil_torpedo_boat` | 2 | 100.0 | _(module has no anchor)_ |
| `mil_torpedo_tube` | 2 | 90.0 | _(module has no anchor)_ |
| `mil_trace_italienne` | 2 | 100.0 | _(module has no anchor)_ |
| `mil_wheel_lock` | 2 | 80.0 | _(module has no anchor)_ |
| `tr_periscope` | 2 | 100.0 | _(module has no anchor)_ |
| `mil_aerial_camera` | 3 | 95.0 | _(module has no anchor)_ |
| `mil_aerial_reconnaissance` | 3 | 100.0 | _(module has no anchor)_ |
| `mil_aircraft_catapult` | 3 | 120.0 | _(module has no anchor)_ |
| `mil_anti_aircraft_gun` | 3 | 115.0 | _(module has no anchor)_ |
| `mil_armoured_car` | 3 | 120.0 | _(module has no anchor)_ |
| `mil_armoured_cruiser` | 3 | 150.0 | _(module has no anchor)_ |
| `mil_armoured_cupola` | 3 | 110.0 | _(module has no anchor)_ |
| `mil_arrester_wire` | 3 | 85.0 | _(module has no anchor)_ |
| `mil_battlecruiser` | 3 | 160.0 | _(module has no anchor)_ |
| `mil_belt_feed` | 3 | 100.0 | _(module has no anchor)_ |
| `mil_bolt_action` | 3 | 120.0 | _(module has no anchor)_ |
| `mil_bomb_sight` | 3 | 110.0 | _(module has no anchor)_ |
| `mil_cartridge_metallic` | 3 | 110.0 | _(module has no anchor)_ |
| `mil_centrefire_primer` | 3 | 85.0 | _(module has no anchor)_ |
| `mil_chemical_phosgene` | 3 | 80.0 | _(module has no anchor)_ |
| `mil_cordite` | 3 | 100.0 | _(module has no anchor)_ |
| `mil_depth_charge` | 3 | 100.0 | _(module has no anchor)_ |
| `mil_destroyer` | 3 | 130.0 | _(module has no anchor)_ |
| `mil_dreadnought` | 3 | 180.0 | _(module has no anchor)_ |
| `mil_face_hardened_armour` | 3 | 110.0 | _(module has no anchor)_ |
| `mil_field_telephone` | 3 | 80.0 | _(module has no anchor)_ |
| `mil_forward_observer` | 3 | 70.0 | _(module has no anchor)_ |
| `mil_gun_synchroniser` | 3 | 120.0 | _(module has no anchor)_ |
| `mil_gunpowder_base` | 3 | 10.0 | _(module has no anchor)_ |
| `mil_indirect_fire` | 3 | 80.0 | _(module has no anchor)_ |
| `mil_machine_gun_gas` | 3 | 150.0 | _(module has no anchor)_ |
| `mil_machine_gun_recoil` | 3 | 160.0 | _(module has no anchor)_ |
| `mil_minesweeper` | 3 | 110.0 | _(module has no anchor)_ |
| `mil_range_table` | 3 | 100.0 | _(module has no anchor)_ |
| `mil_rangefinder` | 3 | 105.0 | _(module has no anchor)_ |
| `mil_recoil_mechanism` | 3 | 130.0 | _(module has no anchor)_ |
| `mil_revolver` | 3 | 110.0 | _(module has no anchor)_ |
| `mil_sloped_armour` | 3 | 85.0 | _(module has no anchor)_ |
| `mil_smokeless_powder` | 3 | 180.0 | _(module has no anchor)_ |
| `mil_sponson` | 3 | 85.0 | _(module has no anchor)_ |
| `mil_tank_turret` | 3 | 110.0 | _(module has no anchor)_ |
| `mil_track` | 3 | 120.0 | _(module has no anchor)_ |
| `mil_turret_traverse` | 3 | 100.0 | _(module has no anchor)_ |
| `mil_water_jacket` | 3 | 90.0 | _(module has no anchor)_ |
| `mil_wireless_set` | 3 | 100.0 | _(module has no anchor)_ |
| `tl_half_track` | 3 | 220.0 | _(module has no anchor)_ |
| `mil_aircraft_carrier` | 4 | 170.0 | _(module has no anchor)_ |
| `mil_asdic` | 4 | 140.0 | _(module has no anchor)_ |
| `mil_atomic_bomb` | 4 | 200.0 | _(module has no anchor)_ |
| `mil_ballistic_rocket` | 4 | 150.0 | _(module has no anchor)_ |
| `mil_bomber_aircraft` | 4 | 150.0 | _(module has no anchor)_ |
| `mil_chain_home` | 4 | 140.0 | _(module has no anchor)_ |
| `mil_dive_bomber` | 4 | 130.0 | _(module has no anchor)_ |
| `mil_fighter_aircraft` | 4 | 140.0 | _(module has no anchor)_ |
| `mil_fire_control_computing` | 4 | 120.0 | _(module has no anchor)_ |
| `mil_fire_control_director` | 4 | 140.0 | _(module has no anchor)_ |
| `mil_guided_bomb` | 4 | 140.0 | _(module has no anchor)_ |
| `mil_iff_system` | 4 | 120.0 | _(module has no anchor)_ |
| `mil_jet_fighter` | 4 | 160.0 | _(module has no anchor)_ |
| `mil_napalm` | 4 | 100.0 | _(module has no anchor)_ |
| `mil_proximity_fuse` | 4 | 150.0 | _(module has no anchor)_ |
| `mil_radar` | 4 | 250.0 | _(module has no anchor)_ |
| `mil_self_loading_pistol` | 4 | 140.0 | _(module has no anchor)_ |
| `mil_self_propelled_gun` | 4 | 150.0 | _(module has no anchor)_ |
| `mil_tank` | 4 | 160.0 | _(module has no anchor)_ |
| `mil_trench` | 4 | 40.0 | _(module has no anchor)_ |
| `mil_chemical_mustard` | 5 | 85.0 | _(module has no anchor)_ |
| `mil_machine_gun_nest` | 5 | 60.0 | _(module has no anchor)_ |

### 98_power_plants.md

| Node | Your hours | Recipe |
|---|---:|---|
| `en_alternator` | 130.0 | [`en_alternator`](98_power_plants.md#en_alternator---alternator-ac-generator) |
| `en_battery_charging` | 110.0 | [`en_battery_charging`](98_power_plants.md#en_battery_charging---battery-charging-system) |
| `en_battery_nickel_iron` | 300.0 | [`en_battery_lead_acid`](98_power_plants.md#en_battery_lead_acid---lead-acid-storage-battery) |
| `en_boiler_babcock` | 140.0 | [`en_boiler_water_tube`](98_power_plants.md#en_boiler_water_tube---water-tube-boiler) |
| `en_boiler_locomotive` | 120.0 | [`en_boiler_cornish`](98_power_plants.md#en_boiler_cornish---cornish-boiler) |
| `en_boiler_stirling` | 150.0 | [`en_boiler_water_tube`](98_power_plants.md#en_boiler_water_tube---water-tube-boiler) |
| `en_breastshot_wheel` | 180.0 | [`en_overshot_wheel`](98_power_plants.md#en_overshot_wheel---overshot-water-wheel) |
| `en_carburetted_engine` | 110.0 | [`en_hot_bulb_engine`](98_power_plants.md#en_hot_bulb_engine---hot-bulb-engine) |
| `en_centrifugal_governor` | 120.0 | [`en_water_wheel_governor`](98_power_plants.md#en_water_wheel_governor---governor-for-water-wheel) |
| `en_charcoal_burning` | 60.0 | [`en_charcoal_burning`](98_power_plants.md#en_charcoal_burning---charcoal-production-by-burning) |
| `en_circuit_breaker` | 140.0 | [`en_switchgear`](98_power_plants.md#en_switchgear---switchgear-high-voltage-switch) |
| `en_coal_mining_washing` | 100.0 | [`en_charcoal_burning`](98_power_plants.md#en_charcoal_burning---charcoal-production-by-burning) |
| `en_coke_oven` | 120.0 | [`en_coke_oven`](98_power_plants.md#en_coke_oven---coke-oven-beehive-or-by-product) |
| `en_commutator` | 90.0 | [`en_alternator`](98_power_plants.md#en_alternator---alternator-ac-generator) |
| `en_compound_engine` | 180.0 | [`en_high_pressure_engine`](98_power_plants.md#en_high_pressure_engine---high-pressure-steam-engine) |
| `en_compressed_air_engine` | 100.0 | [`en_stirling_engine`](98_power_plants.md#en_stirling_engine---stirling-hot-air-engine) |
| `en_condenser_jet` | 70.0 | [`en_separate_condenser`](98_power_plants.md#en_separate_condenser---separate-condenser-watt) |
| `en_condenser_surface` | 100.0 | [`en_separate_condenser`](98_power_plants.md#en_separate_condenser---separate-condenser-watt) |
| `en_corliss_valve` | 150.0 | [`en_expansive_working`](98_power_plants.md#en_expansive_working---expansive-working-cutoff) |
| `en_cutoff_valve` | 90.0 | [`en_expansive_working`](98_power_plants.md#en_expansive_working---expansive-working-cutoff) |
| `en_double_acting` | 160.0 | [`en_atmospheric_engine`](98_power_plants.md#en_atmospheric_engine---atmospheric-engine-newcomen) |
| `en_draft_tube` | 80.0 | [`en_penstock`](98_power_plants.md#en_penstock---penstock-and-flume) |
| `en_economiser` | 100.0 | [`en_economiser`](98_power_plants.md#en_economiser---economiser) |
| `en_exciter` | 100.0 | [`en_alternator`](98_power_plants.md#en_alternator---alternator-ac-generator) |
| `en_expansive_working` | 110.0 | [`en_expansive_working`](98_power_plants.md#en_expansive_working---expansive-working-cutoff) |
| `en_feedwater_heater` | 90.0 | [`en_economiser`](98_power_plants.md#en_economiser---economiser) |
| `en_fourneyron_turbine` | 200.0 | [`en_fourneyron_turbine`](98_power_plants.md#en_fourneyron_turbine---fourneyron-turbine) |
| `en_francis_turbine` | 220.0 | [`en_fourneyron_turbine`](98_power_plants.md#en_fourneyron_turbine---fourneyron-turbine) |
| `en_frequency_standardisation` | 150.0 | [`en_substation`](98_power_plants.md#en_substation---substation-transformer-station) |
| `en_fuel_injection` | 150.0 | [`en_poppet_valve`](98_power_plants.md#en_poppet_valve---poppet-valve-and-camshaft) |
| `en_fuse` | 70.0 | [`en_switchgear`](98_power_plants.md#en_switchgear---switchgear-high-voltage-switch) |
| `en_gas_engine` | 350.0 | [`en_four_stroke_cycle`](98_power_plants.md#en_four_stroke_cycle---four-stroke-cycle-otto) |
| `en_gas_holder` | 110.0 | [`en_coke_oven`](98_power_plants.md#en_coke_oven---coke-oven-beehive-or-by-product) |
| `en_gas_producer` | 130.0 | [`en_coke_oven`](98_power_plants.md#en_coke_oven---coke-oven-beehive-or-by-product) |
| `en_gas_turbine` | 250.0 | [`en_gas_turbine`](98_power_plants.md#en_gas_turbine---gas-turbine-brayton-cycle) |
| `en_grid_interconnection` | 180.0 | [`en_substation`](98_power_plants.md#en_substation---substation-transformer-station) |
| `en_high_pressure_engine` | 180.0 | [`en_high_pressure_engine`](98_power_plants.md#en_high_pressure_engine---high-pressure-steam-engine) |
| `en_horse_gin` | 30.0 | [`en_undershot_wheel`](98_power_plants.md#en_undershot_wheel---undershot-water-wheel) |
| `en_hot_bulb_engine` | 120.0 | [`en_hot_bulb_engine`](98_power_plants.md#en_hot_bulb_engine---hot-bulb-engine) |
| `en_hydraulic_accumulator` | 100.0 | [`en_hydraulic_accumulator`](98_power_plants.md#en_hydraulic_accumulator---hydraulic-accumulator) |
| `en_hydraulic_power_main` | 140.0 | [`en_hydraulic_accumulator`](98_power_plants.md#en_hydraulic_accumulator---hydraulic-accumulator) |
| `en_insulator` | 100.0 | [`en_transmission_line`](98_power_plants.md#en_transmission_line---transmission-line-high-voltage-power-cable) |
| `en_jet_engine` | 300.0 | [`en_gas_turbine`](98_power_plants.md#en_gas_turbine---gas-turbine-brayton-cycle) |
| `en_kaplan_turbine` | 250.0 | [`en_fourneyron_turbine`](98_power_plants.md#en_fourneyron_turbine---fourneyron-turbine) |
| `en_kerosene` | 100.0 | [`en_petrol`](98_power_plants.md#en_petrol---petrol-gasoline-production) |
| `en_lightning_arrester` | 90.0 | [`en_switchgear`](98_power_plants.md#en_switchgear---switchgear-high-voltage-switch) |
| `en_liquid_propellant` | 180.0 | [`en_gas_turbine`](98_power_plants.md#en_gas_turbine---gas-turbine-brayton-cycle) |
| `en_load_factor_diversity` | 120.0 | [`en_substation`](98_power_plants.md#en_substation---substation-transformer-station) |
| `en_lubricating_oil` | 100.0 | [`en_petrol`](98_power_plants.md#en_petrol---petrol-gasoline-production) |
| `en_oil_drilling` | 130.0 | [`en_oil_drilling`](98_power_plants.md#en_oil_drilling---oil-drilling-and-production) |
| `en_oil_refining_distillation` | 140.0 | [`en_oil_drilling`](98_power_plants.md#en_oil_drilling---oil-drilling-and-production) |
| `en_oil_shale_retorting` | 130.0 | [`en_oil_drilling`](98_power_plants.md#en_oil_drilling---oil-drilling-and-production) |
| `en_overshot_wheel` | 80.0 | [`en_overshot_wheel`](98_power_plants.md#en_overshot_wheel---overshot-water-wheel) |
| `en_parallel_motion` | 100.0 | [`en_parallel_motion`](98_power_plants.md#en_parallel_motion---parallel-motion-linkage-watt) |
| `en_patent_sail` | 110.0 | [`en_patent_sail`](98_power_plants.md#en_patent_sail---patent-sail) |
| `en_peat_fuel` | 70.0 | [`en_charcoal_burning`](98_power_plants.md#en_charcoal_burning---charcoal-production-by-burning) |
| `en_pelton_wheel` | 250.0 | [`en_fourneyron_turbine`](98_power_plants.md#en_fourneyron_turbine---fourneyron-turbine) |
| `en_penstock` | 50.0 | [`en_penstock`](98_power_plants.md#en_penstock---penstock-and-flume) |
| `en_petrol` | 90.0 | [`en_petrol`](98_power_plants.md#en_petrol---petrol-gasoline-production) |
| `en_poncelet_wheel` | 100.0 | [`en_overshot_wheel`](98_power_plants.md#en_overshot_wheel---overshot-water-wheel) |
| `en_poppet_valve` | 100.0 | [`en_poppet_valve`](98_power_plants.md#en_poppet_valve---poppet-valve-and-camshaft) |
| `en_power_factor_correction` | 120.0 | [`en_substation`](98_power_plants.md#en_substation---substation-transformer-station) |
| `en_reduction_gear` | 120.0 | [`en_parallel_motion`](98_power_plants.md#en_parallel_motion---parallel-motion-linkage-watt) |
| `en_rocket_motor` | 200.0 | [`en_gas_turbine`](98_power_plants.md#en_gas_turbine---gas-turbine-brayton-cycle) |
| `en_rotary_converter` | 150.0 | [`en_battery_charging`](98_power_plants.md#en_battery_charging---battery-charging-system) |
| `en_safety_valve` | 150.0 | [`en_safety_valve`](98_power_plants.md#en_safety_valve---safety-valve-pop-off) |
| `en_separate_condenser` | 200.0 | [`en_separate_condenser`](98_power_plants.md#en_separate_condenser---separate-condenser-watt) |
| `en_sleeve_valve` | 120.0 | [`en_poppet_valve`](98_power_plants.md#en_poppet_valve---poppet-valve-and-camshaft) |
| `en_spring_motor` | 80.0 | [`en_stirling_engine`](98_power_plants.md#en_stirling_engine---stirling-hot-air-engine) |
| `en_spring_sail` | 100.0 | [`en_patent_sail`](98_power_plants.md#en_patent_sail---patent-sail) |
| `en_steam_trap` | 80.0 | [`en_safety_valve`](98_power_plants.md#en_safety_valve---safety-valve-pop-off) |
| `en_steam_turbine_curtis` | 210.0 | [`en_steam_turbine_impulse`](98_power_plants.md#en_steam_turbine_impulse---impulse-steam-turbine-de-laval) |
| `en_steam_turbine_impulse` | 200.0 | [`en_steam_turbine_impulse`](98_power_plants.md#en_steam_turbine_impulse---impulse-steam-turbine-de-laval) |
| `en_steam_turbine_reaction` | 400.0 | [`en_steam_turbine_impulse`](98_power_plants.md#en_steam_turbine_impulse---impulse-steam-turbine-de-laval) |
| `en_stirling_engine` | 300.0 | [`en_stirling_engine`](98_power_plants.md#en_stirling_engine---stirling-hot-air-engine) |
| `en_substation` | 300.0 | [`en_substation`](98_power_plants.md#en_substation---substation-transformer-station) |
| `en_sun_planet_gear` | 100.0 | [`en_parallel_motion`](98_power_plants.md#en_parallel_motion---parallel-motion-linkage-watt) |
| `en_supercharger` | 140.0 | [`en_supercharger`](98_power_plants.md#en_supercharger---supercharger-mechanically-driven) |
| `en_switchgear` | 120.0 | [`en_switchgear`](98_power_plants.md#en_switchgear---switchgear-high-voltage-switch) |
| `en_thermal_station` | 220.0 | [`en_hydroelectric_station`](98_power_plants.md#en_hydroelectric_station---hydroelectric-power-station) |
| `en_three_phase_gen` | 110.0 | [`en_alternator`](98_power_plants.md#en_alternator---alternator-ac-generator) |
| `en_town_gas_retort` | 140.0 | [`en_coke_oven`](98_power_plants.md#en_coke_oven---coke-oven-beehive-or-by-product) |
| `en_transmission_line` | 140.0 | [`en_transmission_line`](98_power_plants.md#en_transmission_line---transmission-line-high-voltage-power-cable) |
| `en_treadwheel` | 20.0 | [`en_undershot_wheel`](98_power_plants.md#en_undershot_wheel---undershot-water-wheel) |
| `en_turbine_blading` | 150.0 | [`en_turbine_blading`](98_power_plants.md#en_turbine_blading---turbine-blade-design-and-profile) |
| `en_turbine_condenser_vacuum` | 160.0 | [`en_turbine_blading`](98_power_plants.md#en_turbine_blading---turbine-blade-design-and-profile) |
| `en_turbocharger` | 160.0 | [`en_supercharger`](98_power_plants.md#en_supercharger---supercharger-mechanically-driven) |
| `en_two_stroke_cycle` | 90.0 | [`en_four_stroke_cycle`](98_power_plants.md#en_four_stroke_cycle---four-stroke-cycle-otto) |
| `en_undershot_wheel` | 60.0 | [`en_undershot_wheel`](98_power_plants.md#en_undershot_wheel---undershot-water-wheel) |
| `en_uniflow_engine` | 160.0 | [`en_high_pressure_engine`](98_power_plants.md#en_high_pressure_engine---high-pressure-steam-engine) |
| `en_water_wheel_governor` | 100.0 | [`en_water_wheel_governor`](98_power_plants.md#en_water_wheel_governor---governor-for-water-wheel) |
| `en_wind_electric` | 180.0 | [`en_wind_pump`](98_power_plants.md#en_wind_pump---wind-pump) |
| `en_wind_pump` | 120.0 | [`en_wind_pump`](98_power_plants.md#en_wind_pump---wind-pump) |
| `en_windmill_fantail` | 200.0 | [`en_patent_sail`](98_power_plants.md#en_patent_sail---patent-sail) |

## Documentation coverage

| status | nodes |
|---|---:|
| linked to a specific recipe entry | 871 |
| linked to a domain module, no specific entry | 1874 |
| documented in a top-level prose file | 13 |
| no link BY DESIGN (capability rungs, materials, unobtainables) | 88 |
| **undocumented, a real gap** | **3** |

The undocumented nodes, listed so the gap is visible rather than hidden:

`com_led`, `hom_clothes_dryer_electric`, `hom_freezer_domestic`

## Broken links

- `civ_monumental_stone` points at `87_construction.md#cn_quarry_wedge`, but that module has no such `###` entry
- `met_bloomery_bog_iron` points at `10_metallurgy.md#bloomery_iron`, but that module has no such `###` entry
- `mat_rubber_coagulated` points at `89_remaining_arts.md#mat_rubber_coagulated`, but that module has no such `###` entry
- `phosphor_bronze_alloy` points at `10_metallurgy.md#phosphor_bronze_alloy`, but that module has no such `###` entry
- `goal_literacy_common` points at `80_information_printing.md#literacy`, but that module has no such `###` entry
- `goal_literate_nation` points at `80_information_printing.md#literacy`, but that module has no such `###` entry
- `goal_public_health` points at `70_medicine_biology.md#public_health`, but that module has no such `###` entry

