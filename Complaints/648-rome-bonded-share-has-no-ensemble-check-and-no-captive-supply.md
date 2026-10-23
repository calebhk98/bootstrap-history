# Rome's bonded share has no ensemble check against its sourced range, and captives and imports are not a modelled supply

**Status:** partly - the births drift is fixed; captives of battles and conquests and a merchants' trade of bonded people between areas are built; the ensemble check is a rule test on the declared share, the played-years share is measured by `baseline-ensemble`; the share of the defeated taken and the age and sex of captives are labelled heuristics with no sourced figure, and the residence-driven mortality of item 3 is open

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

1. Captives by campaign. `sim/engine/captives.py` (called from two lines of `sim/engine/campaign_year.py`, 485's file: after a
   decided battle, and in `_take` before the tile changes hands) gives the winner's bonded stratum a share of the beaten side's
   losses (`captives_from_losses`, `CAPTIVE_SHARE_OF_DEFEATED_LOSSES`) and a share of a taken tile's people
   (`captives_from_conquest`, `CAPTIVE_SHARE_OF_CONQUERED_PEOPLE`), both in `sim/agents/bonded_sale.py`; a society with no bonded
   stratum takes none into bondage. Both shares are labelled heuristics (confidence D, `retire` 648): Scheidel 2005 says the
   enslavement of non-combatants after a defeat was a natural outcome of war and women and children more often survived
   defeat than adult men, and gives no share. Tests: `test_bonded_purchase.py` (rules), `test_campaign_scenario.py` (the hooks in a
   real two-country game).
2. A slave trade by merchants between areas, through the bonded purchase market, not people as goods. Every bonded stratum is on
   offer at its owners' ask (the present value of the person's hours where the owner is, 644 item 1); a short trade buys where ask
   plus carriage (the cheapest way along the migration routes, `bonded_worth.cheapest_carriage`) is lowest and under the buyer's bid,
   so people move from where the price is low to where it is high; the owner is paid the ask, the origin country's merchant stratum
   the carriage (`buy_bonded`). Tests: `test_bonded_worth.py`, `test_trade_formation_routes.py`, `test_bonded_purchase.py`.
3. The ensemble check. The slow game test is deleted (it read an unsettled whole economy and named no rule). What remains as
   a rule test is `sim/tests/test_rome_bonded_share_sourced_range.py`: the declared bonded share is inside the range the civilisation
   file's own source note gives (8 to 15 per cent). The share after played years is measured by
   `python3 sim/simulator.py baseline-ensemble --civ rome_100ad` (the bonded stratum's share is not in its distributions yet; add it there).

**Measured (seeds 1 to 3, `rome_100ad`, two market years, one seed per run of about two minutes):** the bonded share went from 0.1000 to 0.0995
under every seed (about 63,780 people bought out of the stratum into the employers' hands by vacancies; no captives, no war in a
baseline). The seeds hardly differ because `follow_population` holds the strata in proportion to the people counted and the stratum
has no seeded draws, so the ensemble is a weak test of the share; it would bite once wars (captives) or the stratum's own births and
deaths vary by seed. The test that produced this is deleted; see item 3 for the measuring command.

**What is left.**

- A residence-driven mortality difference (Scheidel pp. 69 and 75): the stratum model does not carry urban or malarial residence.
- A measured captive share and the age and sex of captives; piracy and the frontier trade as suppliers are not modelled.
- Purchases fire only where vacancies exist and a route runs; a thick slave market (an auction, a dealer holding stock) is not
  modelled, and the buyers' people count in the economy is working people while a stratum counts all ages.
- People do not move: a purchase moves money (ask to the owner, carriage to the merchants) and lowers the seller's bonded
  stratum, but the held hours are taken from the trade's workers already living at the destination tile
  (`bondage_hours.place_held`), and no tile's population changes. A bought person should leave the origin tile's people and
  join the destination's.
- Captives convert rather than move: `follow_population` rescales every home stratum to the counted people each year, so
  captives added to the winner's bonded stratum raise its share and lower the others', while the loser's population is not
  reduced by the conquest captives (the tile's people pass to the winner with the tile anyway).

**Research needed.** The supply side of Roman bondage as events the model can generate: captives by campaign (which
campaigns, how many taken, what share sold), and a price-driven trade (prices of slaves by age and skill against the cost of
rearing one, sources for Roman Egypt sale contracts, Scheidel's and Harris's estimates, and how piracy and the frontier
trade supplied the market). The model aims at realism: captives come from the war mechanism (484) and trade from merchants,
not from a typed inflow. See also 644 (the owners' sale rule).
