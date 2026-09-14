# SHARED VOCABULARY for tech-tree branch authors

You may use ONLY these ids as prerequisites outside your own file, plus ids you
define yourself inside your own file. Any other id will be rejected by the merge
validator and your branch will be sent back.

## CAPABILITY RUNGS (use these to say WHY a thing is hard)

| id | means |
|---|---|
| `cap_heat_0700` | Sustained 700 C (pottery kiln) |
| `cap_heat_1100` | Sustained 1100 C (hand-blown charcoal) |
| `cap_heat_1300` | Sustained 1300 C (water-blown continuous blast) |
| `cap_heat_1600` | Sustained 1600 C (regenerative preheat) |
| `cap_heat_2000` | 2000 C localised (oxy-hydrogen blowpipe) |
| `cap_heat_3000` | 3000 C+ (electric arc / resistance) |
| `cap_tol_1mm` | Tolerance 1 mm (skilled hand craft) |
| `cap_tol_100um` | Tolerance 0.1 mm (file, scraper, gauge) |
| `cap_tol_10um` | Tolerance 0.01 mm (slide rest, lead screw, micrometer) |
| `cap_tol_1um` | Tolerance 1 micron (lapping, grinding, optical flats) |
| `cap_tol_100nm` | Tolerance 0.1 micron (interferometric) |
| `cap_vac_1torr` | Rough vacuum, about 1 torr (piston pump) |
| `cap_vac_1e3` | High vacuum, about 1e-3 torr (Sprengel mercury drop) |
| `cap_vac_1e6` | Very high vacuum, 1e-6 torr (diffusion pump plus getters) |
| `cap_vac_1e9` | Ultra high vacuum, 1e-9 torr (bakeable metal systems) |
| `cap_pure_2N` | Purity 99% (careful classical refining) |
| `cap_pure_4N` | Purity 99.99% (electrorefining, fractional crystallisation) |
| `cap_pure_6N` | Purity 99.9999% (fractional distillation of volatile compounds) |
| `cap_pure_9N` | Purity 1 part in 1e9 (zone refining) |
| `cap_power_muscle` | Muscle and animal power |
| `cap_power_water` | Water power, tens of kW on one shaft |
| `cap_power_steam` | Steam power, portable, hundreds of kW |
| `cap_power_electric` | Local electric power, kW scale |
| `cap_power_grid` | Grid electric power, MW scale |
| `cap_measure_len` | Reproducible length standard |
| `cap_measure_mass_mg` | Mass to 1 milligram |
| `cap_measure_temp` | Temperature to a few degrees (liquid in glass) |
| `cap_measure_temp_hi` | High temperature (clay contraction and colour pyrometry) |
| `cap_measure_time_s` | Time to the second (pendulum) |
| `cap_measure_time_ms` | Time to the millisecond (chronograph, tuning fork) |
| `cap_measure_elec` | Absolute electrical units |
| `cap_measure_light` | Interferometric length (wavelengths of light) |
| `cap_gas_o2h2` | Oxygen and hydrogen in quantity |

## MATERIALS

Tier 0 = Rome already has it, free. Tier 9 = UNOBTAINABLE, and if your technology
needs one of those you must say so plainly and give the substitute.

| id | tier | material |
|---|---|---|
| `mat_alum` | 0 | Alum |
| `mat_asbestos` | 0 | Asbestos |
| `mat_beeswax` | 0 | Beeswax |
| `mat_bitumen` | 0 | Bitumen and naphtha seeps |
| `mat_brass` | 0 | Brass (by cementation) |
| `mat_bronze` | 0 | Bronze |
| `mat_calamine` | 0 | Calamine (zinc carbonate/silicate ore) |
| `mat_carbon_black` | 0 | Carbon black and lampblack |
| `mat_charcoal` | 0 | Charcoal |
| `mat_copper` | 0 | Copper (fire refined) |
| `mat_emery` | 0 | Emery (Naxos) |
| `mat_galena` | 0 | Galena (lead sulfide) |
| `mat_glass_soda` | 0 | Soda-lime glass |
| `mat_gold` | 0 | Gold |
| `mat_gypsum` | 0 | Gypsum plaster |
| `mat_lead` | 0 | Lead |
| `mat_leather` | 0 | Leather |
| `mat_lime` | 0 | Quicklime and slaked lime |
| `mat_linen` | 0 | Linen |
| `mat_mercury` | 0 | Mercury |
| `mat_natron` | 0 | Natron (sodium carbonate) |
| `mat_olive_oil` | 0 | Olive oil |
| `mat_papyrus` | 0 | Papyrus |
| `mat_parchment` | 0 | Parchment |
| `mat_pozzolana` | 0 | Pozzolana and hydraulic concrete |
| `mat_pyrolusite` | 0 | Pyrolusite (manganese dioxide) |
| `mat_salt` | 0 | Salt |
| `mat_shellac` | 0 | Shellac (traded) |
| `mat_silk` | 0 | Silk (traded) |
| `mat_silver` | 0 | Silver |
| `mat_sulfur` | 0 | Sulfur |
| `mat_tallow` | 0 | Tallow |
| `mat_tin` | 0 | Tin |
| `mat_vitriols` | 0 | Vitriols (iron and copper sulfates) |
| `mat_wool` | 0 | Wool |
| `mat_wrought_iron` | 0 | Wrought iron (bloomery) |
| `mat_camphor` | 1 | Camphor (traded) |
| `mat_paper` | 1 | Rag paper |
| `mat_blister_steel` | 2 | Blister steel |
| `mat_cast_iron` | 2 | Cast iron |
| `mat_porcelain` | 2 | Porcelain and high-fired stoneware |
| `mat_zinc` | 2 | Zinc metal |
| `mat_crucible_steel` | 3 | Crucible steel |
| `mat_glass_boro` | 3 | Borosilicate glass |
| `mat_glass_lead` | 3 | Lead crystal (flint glass) |
| `mat_glycerol` | 3 | Glycerol |
| `mat_ammonia` | 4 | Ammonia |
| `mat_bulk_steel` | 4 | Bulk steel (converter and open hearth) |
| `mat_celluloid` | 4 | Celluloid (nitrocellulose plastic) |
| `mat_cement_portland` | 4 | Portland cement |
| `mat_chlorine` | 4 | Chlorine and bleach |
| `mat_concrete_reinforced` | 4 | Reinforced concrete |
| `mat_dyes_synthetic` | 4 | Synthetic dyes (aniline) |
| `mat_formaldehyde` | 4 | Formaldehyde |
| `mat_fused_quartz` | 4 | Fused quartz |
| `mat_ice_artificial` | 4 | Artificial ice and mechanical refrigeration |
| `mat_manganese` | 4 | Manganese and ferromanganese |
| `mat_nickel` | 4 | Nickel |
| `mat_nitrocellulose` | 4 | Nitrocellulose |
| `mat_nitroglycerin` | 4 | Nitroglycerin and dynamite |
| `mat_petroleum_refined` | 4 | Refined petroleum fractions |
| `mat_aluminium` | 5 | Aluminium |
| `mat_bakelite` | 5 | Bakelite (phenol formaldehyde) |
| `mat_chromium` | 5 | Chromium |
| `mat_graphite_pure` | 5 | High purity graphite |
| `mat_magnesium` | 5 | Magnesium |
| `mat_stainless` | 5 | Stainless steel |
| `mat_synthetic_rubber` | 5 | Synthetic rubber |
| `mat_tool_steel_hss` | 5 | High speed and alloy tool steel |
| `mat_tungsten` | 5 | Tungsten |
| `mat_chile_nitrate` | 9 | Chile saltpetre |
| `mat_cryolite` | 9 | Cryolite |
| `mat_gutta_percha` | 9 | Gutta percha |
| `mat_natural_rubber` | 9 | Natural rubber (Hevea) |
| `mat_newworld_crops` | 9 | Potato, maize, tomato, cassava, chilli, cocoa, tobacco, vanilla |
| `mat_platinum_bulk` | 9 | Platinum in quantity |
| `mat_quinine` | 9 | Quinine (cinchona) |

## EXISTING TECHNOLOGIES (already in the tree, reuse do not redefine)

| id | name |
|---|---|
| `academy_network` | Three geographically separated academies |
| `algebra_symbolic` | Symbolic algebra and equation notation |
| `analytical_chemistry` | Gravimetric and volumetric analysis |
| `arc_furnace_ferroalloys` | Electric arc furnace, carbides and ferroalloys |
| `arc_light_lamp` | Arc lighting and incandescent lamps |
| `arithmetic_positional` | Decimal positional notation, zero, negative numbers, decimal fractions |
| `arrival_orientation` | Six months of doing nothing but listening |
| `atomic_theory` | Atoms, elements, atomic weights, stoichiometry, the periodic table |
| `balance_analytical` | Analytical balance reading to 1 milligram |
| `barometer` | Mercury barometer, and the first hard vacuum |
| `bellows_water_blown` | Water-driven double-acting bellows |
| `bessemer_openhearth` | Bulk steel: converter and open hearth |
| `blast_furnace` | Tall shaft blast furnace and cast iron |
| `boring_mill` | Cylinder boring mill |
| `calculus` | Differential and integral calculus |
| `camera_obscura` | Camera obscura with lens |
| `case_hardening` | Systematic case hardening, quenching and tempering |
| `cementation_steel` | Blister steel by cementation |
| `charcoal_industrial` | Coppiced charcoal at industrial scale |
| `citizenship` | Roman citizenship by grant |
| `clock_pendulum` | Pendulum clock and later the balance spring |
| `coal_coke` | Coal, and coking it |
| `collegium_licensed` | Licensed collegium of physicians and teachers |
| `copper_fire_refined` | Fire-refined copper stock |
| `copper_refining` | High-purity copper and insulated wire |
| `corpus_dispersed` | Print and disperse hundreds of copies across three continents |
| `corpus_written` | Write the corpus: everything you know, in plain quantitative Greek and Latin |
| `crank_conrod` | Crank, connecting rod, flywheel, cam and trip hammer |
| `crop_rotation` | Legume rotation, heavy plough, marling, selective breeding |
| `crucible_steel` | Crucible steel |
| `crude_cell` | Copper-iron brine cell |
| `daniell_cell` | Daniell cell and reliable current sources |
| `destructive_distillation` | Destructive distillation of wood and coal |
| `diffusion_pump` | Rotary and mercury diffusion pumps |
| `discharge_xray` | Discharge tubes, cathode rays, X-rays, the electron |
| `distillation_alcohol` | Worm condenser, distilled spirits, essential oils |
| `drawplate_wire` | The drawplate and drawn wire |
| `dynamo` | Dynamo with self-excitation |
| `electrolysis_industrial` | Chlor-alkali, aluminium and industrial electrochemistry |
| `electromagnet` | Electromagnet, relay, and the Wheatstone bridge |
| `electroplating` | Electroplating and electro-refining |
| `electrostatics` | Friction machine, Leyden jar, electroscope |
| `em_theory` | Electromagnetic theory |
| `endowment_land` | Endow the institute in land, not coin |
| `finery_puddling` | Finery forge and the puddling furnace |
| `freedman_staff` | Buy, train and manumit a technical staff |
| `fused_quartz` | Fused silica working |
| `galena_detector` | Galena cat's whisker point-contact rectifier |
| `galvanometer` | Tangent galvanometer and electrical metrology |
| `ge_reduction` | Reduction of germanium dioxide to metal under hydrogen |
| `gecl4_purification` | Germanium tetrachloride fractional distillation |
| `geometry_analytic` | Coordinate geometry and trigonometric tables |
| `germ_theory` | Germ theory of disease |
| `germanium_extraction` | Germanium concentrate from flue dust and coal ash |
| `glass_bead_microscope` | Single-bead microscope |
| `glass_borosilicate` | Borosilicate glass |
| `glass_clear` | Deliberately water-clear soda-lime glass to specification |
| `glass_labware` | Retorts, flasks, condensers, tubing, graduated vessels |
| `gunpowder` | Corned gunpowder |
| `high_temp_furnace` | Regenerative and forced-draught furnaces to 1600 C+ |
| `horse_collar` | Rigid padded horse collar, whippletree, nailed horseshoe |
| `hot_air_balloon` | Hot air balloon for observation |
| `hydrochloric_acid` | Hydrochloric acid and aqua regia |
| `hydrofluoric_acid` | Hydrofluoric acid |
| `identity_cover` | Establish the Alexandrian physician-philosopher persona |
| `industrial_gases` | Oxygen and hydrogen in quantity |
| `interchangeable_parts` | Tolerances, jigs, fixtures and interchangeable manufacture |
| `junction_transistor` | Grown and alloy junction transistors |
| `lab_apparatus` | A working laboratory: retorts, baths, lutes, crucibles, fume management |
| `lead_chamber` | Lead chamber sulfuric acid at industrial scale |
| `lead_metallurgy` | Lead sheet, pipe, litharge and cupellation control |
| `lens_grinding` | Ground and polished spherical lenses |
| `logarithms` | Logarithms and computed tables |
| `master_screw` | The first accurate screw, and thread standards |
| `mercury_supply` | Secure mercury supply |
| `micrometer_gauges` | Micrometer, verniers, gauge blocks, go/no-go gauges |
| `microscope_compound` | Compound microscope with achromatic objective |
| `mining_concession` | Mineral concessions and access to imperial mines |
| `mirror_amalgam` | Tin-mercury amalgam plate mirrors |
| `motor_transformer_ac` | Motors, transformers, alternating current |
| `newtonian_mechanics` | Newtonian mechanics and gravitation |
| `nitre_beds` | Nitre beds and potassium nitrate |
| `nitric_acid` | Nitric acid |
| `patron_imperial` | Imperial patronage |
| `patron_local` | Secure a town patron |
| `patron_senatorial` | Senatorial patronage |
| `photography` | Silver halide photography on glass |
| `plague_preparedness` | Quarantine, clean water, sanitation and variolation programme |
| `point_contact_transistor` | Point-contact transistor |
| `potash_soda` | Potash, caustic potash, soda and caustic soda |
| `power_grid` | Central generation and distribution |
| `precision_three_plate` | True plane surfaces by the three-plate method |
| `printing_press` | Movable type and the screw press |
| `quantum_solidstate_theory` | Band theory, doping, carriers, the p-n junction |
| `radio` | Radio: spark, crystal set, then valve transmitters |
| `rag_paper` | Rag paper from linen |
| `railway` | Iron rail, locomotive and permanent way |
| `refractory_fireclay` | Fireclay, grog and silica refractories |
| `sanitation_antisepsis` | Boiled water, handwashing, wound irrigation, quarantine |
| `school_founded` | Found the school (the Museum) |
| `scientific_method` | Controlled experiment, hypothesis, replication, publication |
| `screw_lathe` | Screw-cutting lathe with lead screw and slide rest |
| `semaphore_telegraph` | Optical semaphore chain |
| `semiconductor_metrology` | Four-point probe, Hall effect, carrier measurement |
| `silicon_path` | Silicon: trichlorosilane purification and high-temperature crystal growth |
| `single_crystal` | Czochralski single crystal growth and controlled doping |
| `soap_hard` | Hard soap from oil and causticised lye |
| `soda_leblanc` | Leblanc and later Solvay soda |
| `spectroscope` | Prism and grating spectroscope |
| `statistics_basic` | Averages, error, sampling, controlled comparison |
| `steam_atmospheric` | Newcomen atmospheric engine |
| `steam_high_pressure` | High pressure steam and adequate boilers |
| `steam_watt` | Separate condenser and rotative engines |
| `sulfuric_retort` | Oil of vitriol by dry distillation of green vitriol |
| `telegraph_electric` | Electric telegraph |
| `telescope` | Refracting telescope |
| `thermodynamics_theory` | Heat, energy, entropy, the gas laws |
| `thermometer` | Sealed liquid-in-glass thermometer with fixed points |
| `units_standards` | Define and publish standard length, mass, time and temperature |
| `vacuum_pumps` | Sprengel mercury pump and high vacuum |
| `vacuum_tube` | Diode, triode, and the first amplifier |
| `voltaic_pile` | Voltaic pile |
| `water_power_scale` | Overshot wheels, millponds, leats, line shafting |
| `workshop_first` | First workshop and laboratory |
| `world_map` | Publish an accurate world map and sailing directions |
| `zinc_industry_scale` | Zinc smelting at industrial scale, with flue dust collection |
| `zinc_metal` | Zinc metal by downward distillation |
| `zone_refining` | Zone refining to one part in 1e9 |
