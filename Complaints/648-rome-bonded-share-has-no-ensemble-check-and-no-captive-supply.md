# Rome's bonded share has no ensemble check against its sourced range, and captives and imports are not a modelled supply

**Status:** partly - `CAPTIVE_SHARE_OF_DEFEATED_LOSSES` is now a sourced ballpark (confidence C); open: `CAPTIVE_SHARE_OF_CONQUERED_PEOPLE` (labelled, sack frequency unsourced), the age and sex of captives (no constant exists: `AddCaptives` takes a headcount, so it is a mechanism to build), residence shares, a thick market, and people not moving

Found rewriting `rome_slave_stratum` (640). Rome seeds its bonded stratum at its declared share of the people; after two
simulated years the share fell below the low end of the range its source note gives (Scheidel 2005, cited in
`data/civilizations/rome_100ad.json`).

**What was wrong and is fixed.** `BONDED_BIRTH_SHARE`, a labelled heuristic with no source, trimmed bonded births to a
fraction of the ordinary rate. Scheidel 2005 ('Human Mobility in Roman Italy, II: The Slave Population', JRS 95: 64-79, p. 75,
read in the Gwern.net copy) writes: "Bagnall and Frier have found that the average fertility of slave women was similar to
that of all women." The constant is deleted; a bonded stratum has the stratum's own birth rule (rule test in
`sim/tests/test_rome_slave_stratum.py`: a fed bonded stratum grows at the rate a fed free one does). The first-year famine
is fixed too (`true_up_keep`).

**What is built (648).**

1. Captives by campaign. `sim/campaigns/captives.py` (called from `Contest` in `sim/campaigns/contest.py`, 485's orchestration: after a
   decided battle, and in `_take` before the tile changes hands) gives the winner's bonded stratum a share of the beaten side's
   losses (`captives_from_losses`, `CAPTIVE_SHARE_OF_DEFEATED_LOSSES`) and a share of a taken tile's people
   (`captives_from_conquest`, `CAPTIVE_SHARE_OF_CONQUERED_PEOPLE`), both in `sim/agents/bonded_sale.py`; a society with no bonded
   stratum takes none into bondage. Both shares are labelled heuristics (confidence D, `retire` 648): Scheidel 2005 says the
   enslavement of non-combatants after a defeat was a natural outcome of war and women and children more often survived
   defeat than adult men, and gives no share. Tests: `test_bonded_purchase.py` (rules), `test_campaigns_module.py` (the hooks; `test_campaign_scenario.py` is gone).
2. A slave trade by merchants between areas, through the bonded purchase market, not people as goods. Every bonded stratum is on
   offer at its owners' ask (the present value of the person's hours where the owner is, 644 item 1); a short trade buys where ask
   plus carriage (the cheapest way along the migration routes, `carriage_costs` in `sim/labour/market/records.py`; `bonded_worth.cheapest_carriage` is gone) is lowest and under the buyer's bid,
   so people move from where the price is low to where it is high; the owner is paid the ask, the origin country's merchant stratum
   the carriage (`buy_bonded`). Tests: `test_bonded_worth.py`, `test_trade_formation_routes.py`, `test_bonded_purchase.py`.
3. The ensemble check. The slow game test is deleted (it read an unsettled whole economy and named no rule). What remains as
   a rule test is `sim/tests/test_rome_bonded_share_sourced_range.py`: the declared bonded share is inside the range the civilisation
   file's own source note gives (8 to 15 per cent). The share after played years is measured by
   `python3 sim/simulator.py baseline-ensemble --civ rome_100ad` (the bonded stratum's share is a `bonded_share` metric of its distributions, from `home_strata_rows`; tabulation test `test_baseline_ensemble.py`). Run it with `python3 sim/simulator.py baseline-ensemble --civ rome_100ad --seeds 3 --years 2` to read the played-years share.

**Measured (seeds 1 to 3, `rome_100ad`, two market years, one seed per run of about two minutes):** the bonded share went from 0.1000 to 0.0995
under every seed (about 63,780 people bought out of the stratum into the employers' hands by vacancies; no captives, no war in a
baseline). The seeds hardly differ because `follow_population` holds the strata in proportion to the people counted and the stratum
has no seeded draws, so the ensemble is a weak test of the share; it would bite once wars (captives) or the stratum's own births and
deaths vary by seed. The test that produced this is deleted; see item 3 for the measuring command.

**What is left.**

- Residence-driven mortality is built: a stratum plan may carry `residence` shares (`urban`, `rural`, `malarial`); `grow` sets the base death rate with `residence_death_rate` (`sim/agents/bonded_residence.py`; the urban premium is `People.urban_mortality_premium`, the demography's town premium per resident; malarial land adds Scheidel 2005, JRS 95, pp. 76-77, 'annual excess mortality of 1 per cent', which he assumes for a tenth to a third of rural slaves). Open: no civilisation file declares residence shares for its bonded (no opened source gives the split; Scheidel says urban slaves lived in their owners' houses), the home stratum's headcount follows the population model (`follow_population`) so the rule bites only where strata grow on their own, and the demography holds no mine mortality figure, so `mine` adds nothing.
- A sourced captive share and the age and sex of captives: searched this session; Scheidel 2005 (read, pp. 70-71 and n. 56) cites ancient authors for the enslavement of non-combatants and women and children and disputes Harris's male-prisoner claim, but gives no share; Wickham (Liverpool thesis) and Abgrall (campaign mapping) were found as abstracts only. Both captive constants stay labelled. Second pass (opened: Scheidel, 'The Roman slave supply', 2007 working paper, pp. 7-9 and the sex-ratio section, https://typeset.io/pdf/the-roman-slave-supply-vhrhub3hsh.pdf; Josephus, Jewish War 6.9.2-3, Whiston, Gutenberg 2850; Caesar, Gallic War 1.29, 2.4, 2.33, Gutenberg 10657; Strabo 4.6.7, Loeb, Penelope): the sources give counts, not a rule. Captives against dead: Jerusalem 97,000 captive and 1,100,000 perished (0.08 of the two), Aduatuci about 4,000 slain and 53,000 sold (0.93), Salassi all 44,000 surviving sold (36,000 others and 8,000 fighting men, so fighting men 0.18 of captives). Age and sex: Scheidel writes that 'ancient sources consistently convey the impression that women and children were over-represented among war captives'; Josephus has the aged and infirm killed, those under seventeen sold, the prime-age men sent to mines and shows, with no counts. Ziolkowski 1986 (PBSR 54: 69-80) was paywalled; Scheidel gives 150,000 for Epirus 167 BC, without the population. The range 0.08 to 0.93 contains the 0.2 value and fixes nothing; the values stay D with the range in their `why`. Piracy and the frontier trade as suppliers are not modelled.
- Purchases fire only where vacancies exist and a route runs; a thick slave market (an auction, a dealer holding stock) is not
  modelled, and the buyers' people count in the economy is working people while a stratum counts all ages.
- People do not move: a purchase moves money (ask to the owner, carriage to the merchants) and lowers the seller's bonded
  stratum, but the held hours are taken from the trade's workers already living at the destination tile
  (`place_held` in `sim/economy/bondage_hours.py`), and no tile's population changes. A bought person should leave the origin tile's people and
  join the destination's.
- Captives convert rather than move: `follow_population` rescales every home stratum to the counted people each year, so
  captives added to the winner's bonded stratum raise its share and lower the others', while the loser's population is not
  reduced by the conquest captives (the tile's people pass to the winner with the tile anyway).

**Research needed.** The supply side of Roman bondage as events the model can generate: captives by campaign (which
campaigns, how many taken, what share sold), and a price-driven trade (prices of slaves by age and skill against the cost of
rearing one, sources for Roman Egypt sale contracts, Scheidel's and Harris's estimates, and how piracy and the frontier
trade supplied the market). The model aims at realism: captives come from the war mechanism (484) and trade from merchants,
not from a typed inflow. See also 644 (the owners' sale rule).

## Sourced (2026-11, ballpark standard)

- `CAPTIVE_SHARE_OF_DEFEATED_LOSSES` 0.2 kept, confidence C, `engineering_estimate`. Wikipedia 'Battle of Cannae' (https://en.wikipedia.org/wiki/Battle_of_Cannae): Livy 19,300 captured of 67,500 lost = 0.29; Polybius 10,000 of 80,000 = 0.125; Plutarch 14,000 of 64,000 = 0.22. Mean 0.21. Besieged people for contrast: Wikipedia 'Atuatuci' (https://en.wikipedia.org/wiki/Atuatuci) 4,000 killed and 53,000 sold = 0.93.
- `CAPTIVE_SHARE_OF_CONQUERED_PEOPLE` 0.02 kept as a labelled heuristic (confidence D). Sacked places: Carthage 50,000 sold of 90,000 to 800,000 (0.06 to 0.56; Wikipedia 'Third Punic War'), Aduatuci 0.93. A surrendering tile loses none. The average needs the share of taken tiles that were sacked; no count of that was found, so 0.02 rests on an assumed one in ten to fifteen.
- Age and sex of captives: no constant in the code; `AddCaptives` adds a headcount to the bonded stratum, so this is a mechanism (typed captives) rather than a number to source. Qualitative anchor already recorded: women and children over-represented (Scheidel).

## Pass (2026-11, any-source bar)

`CAPTIVE_SHARE_OF_CONQUERED_PEOPLE` 0.02 -> 0.09, now confidence C. Opened: Caesar, Gallic War (Gutenberg 10657, books 2, 3, 7, read through a page summariser, so a town may be missed) and Wikipedia 'Gallic Wars'. Places taken or yielded: 9 spared (Noviodunum of the Suessiones, Bratuspantium, Ambiani, the Alpine forts, the Sotiates, Adcantuannus's stronghold, Vellaunodunum, Noviodunum of the Bituriges, Uxellodunum) and 4 sacked (Aduatuci 53,000 sold, Veneti sold, Genabum, Avaricum 40,000 killed and none sold): 4 / 13 = 0.31 sacked. Captured share of a sacked place: Aduatuci 0.93, Carthage about 0.31 (midpoint of 0.06 to 0.56, Wikipedia 'Third Punic War'), Avaricum and Genabum about 0: mean 0.31. 0.31 * 0.31 = 0.095. The old 0.02 was 4.5 times lower. One campaign by one author; the Veneti and Alesia have no count; Thirty Years War and Alexander's sieges were not counted (Wikipedia 'Thirty Years' War', opened, gives no sack counts).
