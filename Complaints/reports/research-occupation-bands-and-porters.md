# Research: occupation bands (Complaint 619) and porter and longshore figures (Complaint 613)

Sourcing key: **OPENED** = full text read this session; **SNIPPET ONLY** = a search result or abstract, not the work;
**NO SOURCE FOUND** = searched, nothing usable. Bands are validation targets, never fitted to the model.

## 1. Occupation shares (619)

### Findings

| Figure | Source | Status |
|---|---|---|
| England 1381, share of the labour force: agriculture 57.2 %, industry 19.2 %, services 23.6 % (males 67.0 / 15.2 / 17.8; females 34.5 / 28.4 / 37.1) | Broadberry, Campbell, van Leeuwen, "When did Britain industrialise?", Explorations in Economic History 50 (2013) 16-27, Table 1. Industry includes mining and building; females assumed 30 % of employment; weights urban 10 / semi-rural 10 / rural 80 % | OPENED (accepted manuscript, QUB repository) |
| England 1522: agriculture 58.1, industry 22.7, services 19.2 (males 68.2 / 20.2 / 11.6) | same, Table 2 | OPENED |
| England 1381 agriculture, Clark's alternative: 56 to 59 % total | same, Table 9 part C | OPENED |
| England 1300 agricultural share of population 0.76 (3.82m of 5.0m); Italy 1300 0.63 (6.97m of 11.0m); England 1500 0.74, Italy 1500 0.62 | Allen, European Review of Economic History 4 (2000), Tables 2 and 4 | OPENED (Oxford ORA version of record). The rural non-farm share is a stipulation (0.8 of rural people farm in 1500 and earlier), so these are assumption-driven population shares, not occupational counts |
| Roman Empire: subsistence farmers "the overwhelming majority"; a town share of 15 % used only as an illustration | Scheidel and Friesen, JRS 99 (2009) 61-91, section on the non-elite income distribution (page not shown by the text extract) | OPENED (piketty.pse.ens.fr/files/Scheidel2009.pdf). It gives no occupational shares |
| Roman world: "about 80 per cent ... in agriculture, leaving only 20 per cent for all other sectors", a commonplace, "generally about right" | Erdkamp, The Grain Market in the Roman Empire (2005), ch. 1 | SNIPPET ONLY (Cambridge Core summary, page not shown) |
| Roman peasants often combined farming with other work | a Classical Quarterly abstract found by search | SNIPPET ONLY |
| Han China about 90 % farmers | a world-history textbook (unsourced) | SNIPPET ONLY; not usable as a band edge |
| Textile, building, food-processing shares for Rome or England | Broadberry et al. 2015 book, Bairoch 1988, Wilson 2002 | NO SOURCE FOUND. The book and Bairoch were not opened; Wilson 2002 (abstract only) is about water power and gives no shares |
| Rome or England split of industry into crafts | none | NO SOURCE FOUND |
| DeLaine-style construction labour share | none | NO SOURCE FOUND |

Findings that change the repo: the old `wilson_2002` entry was cited for textile, building, food and transport bands, but
the work gives no shares. The old agriculture and services edges were "recalled". Two flags: the model's services group
(soldier, scribe, merchant, scholar, master, servant) is narrower than the Wrigley services class, which probably
also holds transport and retail; Wrigley's scheme was not opened, so the transport placement is unchecked.

### Proposed bands

| Group | Band | Edge sources | Confidence |
|---|---|---|---|
| agriculture | 0.55 to 0.90 | low: England 1381 57.2 %, Clark 56 % (BCvL Tables 1, 9). High: Roman 80 % commonplace (Erdkamp, snippet), widened to 90 for the poorest case; no opened source gives 90 | medium low edge, low high edge |
| services_state (with transport, together) | 0.01 to 0.20 | high: England services 23.6 % (1381), 19.2 % (1522) (BCvL Tables 1, 2), shared with transport. Low: no source found | low |
| industry as a whole (textiles + building + food + other crafts) | 0.10 to 0.30 | England 19.2 % (1381), 22.7 % (1522) (BCvL), widened for the weighting assumptions and the absence of any Roman figure | low to medium; Roman edge NO SOURCE FOUND |
| textiles, building, food_processing, other_crafts, transport singly | unchanged, labelled "recalled" | NO SOURCE FOUND | none |
| unattributed | 0 to 0.10 | a cap, not a literature figure | n/a |

Sources do not support the ordering rule "textiles or building is the largest non-farm group" either; it is unsourced.

## 2. Porters and longshore work (613)

| Figure | Source | Status |
|---|---|---|
| Tlameme load about 23 kg; day's carry 21 to 25 km before relief | Wikipedia "Tlamemeh" (cites León-Portilla; ties neither figure to a page) | OPENED (secondary) |
| Tlameme about 50 lb (about 23 kg) over 5 leagues before relay, attributed to Hassig 1985 pp. 32-33 | a blog post quoting Hassig | SNIPPET ONLY; Hassig not opened |
| Central Africa: porters carried on average no more than about 20 kg, loads cut to about 20 kg units, journeys at most about 25 km a day | Leiden African Studies Centre working paper (fetch failed with 503) | SNIPPET ONLY |
| Precolonial Kano: loads 50 to 90 lb (23 to 41 kg), 15 to 20 miles a day | M. Yusuf Umar, Transportation and Trade in Precolonial Kano | SNIPPET ONLY |
| Modern Inca Trail legal limit 20 kg | news pages | not historical; not used |
| Roman saccarii at Ostia: grain handled by guilds (receivers, helpers, loaders); figurines exist; stevedores "by the thousands" | museum and site pages | SNIPPET ONLY, no throughput |
| Hours of dock handling per tonne, Roman or medieval | none | NO SOURCE FOUND |
| Andean (Inca) bearer loads and distances, historical | none | NO SOURCE FOUND |

The foot mode's 27 kg and 22 km a day sit inside the spread of the snippets (20 to 41 kg; 15 to 25 km); no opened primary
source fixes either, so `modes.json` is unchanged. The Kano load is heavier than the model's. `PORT_HANDLING_HOURS_PER_TONNE`
stays a labelled heuristic with its `retire`. Next steps for a real source: open Hassig 1985 pp. 32-35, Rickman, The Corn
Supply of Ancient Rome, and Genoese Padri del Comune porter tariffs.

## 3. Data changed

`data/world/occupation_groups.json`: agriculture high edge 0.92 to 0.90; services_state high edge 0.10 to 0.20; every
group gains `band_status` and `band_source`; sources rewritten with OPENED or SNIPPET status; new `industry_total`
entry (no test reads it yet). `simulator.py validate` is clean; the two `GroupData` tests pass. The whole-game
`occupational_distribution` topic is slow and was not run.
