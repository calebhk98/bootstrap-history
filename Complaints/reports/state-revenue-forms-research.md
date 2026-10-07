# State revenue forms: research for Complaint 315

Scope: which forms of state revenue each of the five civilisations used at its start date, what each falls on in terms the simulator models, how it was collected, and what the schema can and cannot declare today. No code or data was changed. Rates appear only where a source states them; none was derived to reach a revenue total (CLAUDE.md 4.1, 4.5). Amounts must emerge.

Source tags: **read** = page fetched and read in this session; **snippet** = a web search result summary only, not opened; **recalled** = from memory of the literature, not re-checked, treat as a lead.

## What the engine can express today

Read in `sim/agents/revenue.py`, `sim/agents/revenue_bases.py`, `data/civilizations/_SCHEMA.md` [read]. A form is `{form, basis, rate, paid_in?, from_strata?, _internal}` with `revenue = rate * base`. Bases: `harvest` (money value and tonnes, so it can be paid in kind), `adult_labour_years` (working age less soldiers, valued at the unskilled wage), `imports_value`, `exports_value`, `coin_stock`, `stratum_income` (earned income of the country's strata since last assessed, optional `from_strata`, taken from purses by `ledger.transfer`). Note: the schema table row for `state_revenue` lists five bases and omits `stratum_income` and `from_strata`; the schema text should be brought level with the code.

Standing lines today (`sim/agents/budget_lines.py`, `budget.py`) [read]: army, officials, roads (from road length, paid in labourers), public buildings (masons, from urban population), court, dole (grain, from urban population), navy (from coast length). None carries a stock that persists between years; each is recomputed from a world quantity.

## Rome, about 100 AD

Context: the early Principate. Scholars agree the mix differed from Han: Scheidel's comparison has Rome drawing a larger share from domains, mining and trade levies and spending more on the army and on agents drawn from the upper class [snippet: Scheidel comparative work, via search summary]. A consensus of about a billion sesterces a year of outlay in the second century is reported by Duncan-Jones, Wolters, Scheidel, with the military the largest share, put at 80 percent in about 150 by one estimate and not under 60 percent by others [snippet: Economics of the Roman army, https://en.wikipedia.org/wiki/Economics_of_the_Roman_army]. Those are cited outcomes for comparison only, never targets.

| Form | Base in simulator terms | Collection and cost | Sourced rate | Schema mapping |
|---|---|---|---|---|
| Land tax (tributum soli), provinces; Italy exempt [recalled] | Land output | Assessed on a census; collected through city councils and magistrates, with the fiscus keeping accounts [read: https://en.wikipedia.org/wiki/Taxation_in_ancient_Rome]. Grain in kind in grain provinces, coin elsewhere [recalled] | No single rate known. The file's one tenth rests on the Sicilian decuma (Cicero, Verrines) [recalled; already in data file] | `harvest`, `paid_in: wheat_kg` (declared) |
| Poll or property tax (tributum capitis) | Households by head or by property | As above; census-based [read] | No general rate stated in the List of Roman taxes page [read: https://en.wikipedia.org/wiki/List_of_Roman_taxes]. Egyptian laographia is the best-known case [recalled] | `adult_labour_years` (declared, rate low confidence). Property-based forms would want `stratum_income` or a wealth base |
| Customs (portoria) | Trade volume at district borders | Tax farmers (publicani) early; imperial procurators took over in most provinces by the Flavian and Trajanic period, apart from Syria, Egypt and Judea [read: Taxation in ancient Rome] | 2.5 percent [read: List of Roman taxes] | `imports_value`, `exports_value` (declared) |
| Inheritance tax (vicesima hereditatium), citizens only [recalled for the citizen limit] | Estates passing at death | Public officials after Augustus | 5 percent [read: List of Roman taxes] | Not expressible (see list below) |
| Manumission tax (vicesima libertatis) | Value of slaves freed | Public officials | 5 percent of the slave's value [read: List of Roman taxes] | Not expressible |
| Sales tax on auctions (centesima rerum venalium) | Goods sold at auction | Auction houses report | 1 percent under Augustus, 0.5 percent under Tiberius [read: List of Roman taxes] | Not expressible; no domestic trade-volume base |
| Tax on sale of slaves (quinta et vicesima) | Slave sales | Sellers or buyers | 4 percent [read: List of Roman taxes] | Not expressible |
| Imperial estates, mines and quarries | Mine output, rent of state land | Procurators; leased to conductores [recalled] | None stated | Not expressible (no state-owned production or rent) |
| Mint profit (seigniorage, debasement) | Coin struck | Imperial mints | None stated | Partly: `government_coinage.py` exists but no declared form |
| Fines, confiscations, unclaimed property, gold crown payments | Windfall | Courts, procurators | None stated | Not expressible, and arguably should stay emergent |

Collection: a mixed system of tax farming for indirect taxes early, procurators later, and city elites collecting direct taxes locally, so officials' cost is partly paid by the collecting cities, not the fiscus [read: Taxation in ancient Rome]. Historians disagree on burden: some argue taxation drove rural depopulation, others find little archaeological sign of an impoverished countryside [read: same page]. Scheidel's model stresses inefficient collection of tributum [snippet].

Spending lines: army pay (stipendium and donativa) and supply (annona), administration, public works, and the capital's grain dole [read: Taxation in ancient Rome; snippet: Economics of the Roman army]. Military pay was in coin; supply often in kind [snippet].

## Han China, about 100 AD (Eastern Han)

| Form | Base | Collection and cost | Sourced rate | Schema mapping |
|---|---|---|---|---|
| Land tax | Crop yield | Commandery and county officials; grain in kind [recalled] | One thirtieth of yield, reinstated 156 BC; Eastern Han began at one tenth and cut to one thirtieth in 30 AD [read: https://en.wikipedia.org/wiki/Economy_of_the_Han_dynasty]. Early dates conflict with the data file's wording only in emphasis; the file's one thirtieth matches | `harvest`, `paid_in: wheat_kg` (declared) |
| Poll tax (suanfu), adults | Adult households by head | County registers; paid in cash | 120 coins an adult, double for merchants, 20 coins for children 3 to 14 [read: Economy of the Han dynasty] | `adult_labour_years` (declared as a share of wage; the merchant doubling and child rate are not expressible without strata or age bases) |
| Property tax on merchants | Merchants' property | County officials | In 119 BC, 120 coins per 2,000 coins of property, raised from per 10,000 [read: Economy of the Han dynasty]. Whether still in force at 100 AD is not stated there | `stratum_income` with `from_strata` for a merchant stratum, if one exists |
| Corvee labour (gengfu) and conscription | Adult male labour time | Registers; Eastern Han allowed commutation by payment [read: Economy of the Han dynasty] | One month a year in Western Han [read: same] | Not expressible (labour owed in time, not money or goods) |
| Salt, iron and liquor monopolies | Production and sale of salt, iron | Government workshops under Emperor Wu | Abolished or returned to commanderies and private hands in Eastern Han, coinage kept [read: https://en.wikipedia.org/wiki/Taxation_in_premodern_China; Economy of the Han dynasty] | Not expressible, and by this date largely not in force |
| Mint | Coin struck | State mints; coinage monopoly retained | None stated | See Rome |
| Pass and market dues | Trade | Local officials | None stated; the Taxation page says no commercial taxes in Eastern Han [read: Taxation in premodern China] | `imports_value`, `exports_value` declared as D heuristics. Historians' view conflicts with the file's claim that dues are attested; flag the file for review |
| Ever-normal granaries | Grain bought cheap and sold dear | Officials; established 110 BC [read: Economy of the Han dynasty] | n/a | A line with a stock, see below |

Historians disagree on the state's character: the Taxation page frames Eastern Han as low-tax and laissez-faire against the Western Han late period [read]. Late in the dynasty the land tax was cut while poll and property rates rose [read: Economy of the Han dynasty]; the start date matters.

Spending lines: frontier army and garrisons, roads, walls and canals built with conscript labour, granaries, administration [read: Economy of the Han dynasty].

## England, 1300

| Form | Base | Collection and cost | Sourced rate | Schema mapping |
|---|---|---|---|---|
| Royal demesne rents and farms of boroughs | Rent of crown land, town farms | Sheriffs and bailiffs, accounted twice a year at the Exchequer; boroughs farmed for a fixed sum [read: https://en.wikipedia.org/wiki/History_of_the_English_fiscal_system] | None stated | Not expressible (no land rent base) |
| Feudal incidents (reliefs, wardships, aids, escheats, scutage) | Tenures of the crown's tenants | Exchequer, escheators [read: same] | None stated | Not expressible |
| Lay subsidy on movables | Taxpayers' moveable goods | Locally assessed by taxers, voted by Parliament, irregular [read: same; snippet: https://ehs.org.uk/article/the-lay-subsidies-and-the-distribution-of-wealth-in-medieval-england-1275-1334/] | Fifteenth in the country, tenth in towns [recalled; the data file cites this] | `coin_stock` stands in (declared, D). `stratum_income` on a property-owning stratum is closer |
| Wool custom (the "ancient custom", 1275) | Wool exports | Collected by Italian merchant bankers (Riccardi) before 1294, then others [snippet: https://voxeu.org/article/credit-crunch-1294-causes-consequences-and-aftermath] | 6s 8d a sack [snippet: Brainscape custom duties card; Ormrod, recalled]. Receipts reported near ten thousand pounds a year from 1275 under the Riccardi [snippet, cited outcome only] | `exports_value` (declared) |
| Alien imports duty (carta mercatoria 1303) and prisage on wine | Imports | Customs collectors | Additional 3d in the pound on aliens' imports [recalled; in data file] | `imports_value` (declared) |
| Judicial profits (fines, fees, writs) | Litigation | Courts and sheriffs [read: History of the English fiscal system] | None stated | Not expressible; arguably tied to a justice line |
| Vacant bishoprics and abbeys | Church revenue in the crown's hands | Escheators | None stated | Not expressible |
| Taxation of Jews | Moneylenders | Arbitrary tallage; expelled 1290 [read: same] | None | Moot at 1300 |
| Purveyance and prise | Provisions taken from locals for army and household | Royal purveyors, paid in tallies, often not repaid [snippet: Prise page, Edward I expanded it for the Scottish war] | None stated | `paid_in` gets close: a levy in kind on `harvest`, but it is not a share of output, it is a demand set by the army's need |
| Mint, borrowing from banker consortia | Coin, credit | Moneyers; Riccardi lent at about 15 percent before 1294 [snippet] | | `government_coinage.py` and the capital market already cover loans |

Spending lines: Welsh and Scottish campaigns and castles, the household, administration and justice; armies were raised for a campaign by array and indenture, not kept [read in data file: Prestwich cited there]. Historians do not agree how much of royal income counted as the king "living of his own" against taxation, contemporaries counting all of it as his own [snippet: Camden series article].

## Norse, about 900 AD

Evidence is thin. A revenue "form" often has no source for its rate. The file is honest that most of its rates are placeholders.

| Form | Base | Collection and cost | Sourced rate | Schema mapping |
|---|---|---|---|---|
| Royal feasting circuit (veizla) | Food and lodging from farmers on the king's progress | The king and household travel; no officials [recalled] | None | `harvest` in kind is an approximation; the real base is an obligation tied to the king's presence, not a share |
| Ship-levy and service (leidang) | Ship, crew and provisions per district, about one ship per some farms; free farmers outfit it for two or three summer months [read: https://en.wikipedia.org/wiki/Leidang]. First attested in the late tenth century, so dating at 900 is uncertain [snippet and read] | Local organisation by district; no money moves | Conversion into a tax came in the twelfth and thirteenth centuries [read: Leidang] | Not expressible (service in ships and time) |
| Tolls and market dues at trading towns (Hedeby, Kaupang) | Trade passing the town | Local ruler's agents | None known | `imports_value`, `exports_value` (declared, D) |
| Tribute from the Sami (finnskatt) and from subject lands | Furs, skins from a named people | Royal officials on tribute expeditions; a central revenue in the early Middle Ages [snippet: https://snl.no/finnskatten] | None known | Not expressible: tribute from outside the modelled strata |
| Fines and compensation at the thing | Disputes | Thing assembly [recalled] | None | Not expressible |
| Mint | Hedeby struck coin from the ninth century [snippet: Bundesbank money of the Vikings] | | | `government_coinage.py` |
| Booty and silver tribute (Danegeld taken abroad) | Foreign wealth | Raiding | | Not a revenue form; a foreign action |

Spending lines: retinues (hird), ship building and upkeep, feasts and gifts to followers, fortresses where present. Historians disagree whether a Norse king in 900 held a state revenue at all rather than personal wealth and followers; on that view the whole concept of a state budget is anachronistic and the file's "state" is a ruler's household.

## Mexica, about 1500

| Form | Base | Collection and cost | Sourced rate | Schema mapping |
|---|---|---|---|---|
| Tribute from conquered provinces (goods: maize, beans, cloth, warrior costumes, feathers) | The province's produce and crafts, set in a list not a share | Calpixque stewards, with two per province under Moctezuma I, one in the province and one in Tenochtitlan; a central head of tribute (petlacalcatl) above them [read: https://en.wikipedia.org/wiki/Aztec_Empire]. Ledgers: Matricula de Tributos and Codex Mendoza [read: Codex Mendoza page; snippet] | Quantities of goods per province, not rates. No share of harvest is stated | Mapping is poor. The file's `harvest` share is a placeholder (D). Fixed quantities per province would need a new kind of form |
| Commoner tribute (macehualtin) to the ruler and the nobility, in goods and labour | Households | Calpulli leaders, local lords [read: Aztec Empire] | None | `adult_labour_years` for labour in cash terms; `harvest` for goods; labour in time is not expressible |
| Market dues | Market trade | Market judges and officials [recalled]. Pochteca merchants acted as spies and administrators [read: Aztec Empire] | None known | `imports_value` (declared, D) |
| Labour on public works (causeways, aqueducts, temples) | Adult male time | Rotating levies [recalled] | None | Not expressible (corvee) |
| Storehouses of tribute | Stock | Calpixque keep storage in Tenochtitlan and provinces [read: Aztec Empire] | | A stock line |

Collection cost is dominated by transport: with no draught animals, grain stored at regional collection centres, days or weeks away, needed large numbers of porters (Hassig, 1985) [snippet]. That cost belongs to the freight model, not a tax rate. Spending: army supply (porters, storehouses), feasts, temples, causeways, aqueducts [read: Aztec Empire]. Disagreement: authors differ on how far the tribute province quantities reflected real flows versus a ledger of nominal entitlement [recalled, to verify].

## Forms the schema cannot express yet

| Form | What field would express it |
|---|---|
| Tax on a flow of a domestic good's sales (centesima, market dues on internal trade, excise) | New basis `domestic_trade_value` (sales by the home country's actors, optionally by `material`) |
| Tax on estates at death, on manumission, on slave sales | New basis `estate_value_at_death` and `slave_sales_value` from the household and bondage models; or a general basis `transfers_of_kind` keyed by event type |
| Corvee, labour tribute, ship service | New `paid_in_labour: {trade, days_per_person}` on a form, based on `adult_labour_years` people; the labour appears as a line's workforce at no wage and reduces the payers' own time |
| Fixed tribute lists (quantity per province, per household) | `quantity` instead of `rate`, with `per: household | stratum | province`, so a form need not be a share |
| Per-head amounts that differ by stratum (merchant double, child rate) | `from_strata` plus a per-stratum `rate_by_stratum`, or `stratum_income` with distinct forms per stratum, which the current schema already allows for rates |
| Rent on state land, mines, quarries, estates | State ownership of land and deposits as actors' holdings, with the form based on `land_rent_value` or `state_mine_output`. Needs a land value (complaint 315 names its absence) |
| Monopolies (salt, iron, coinage) | A state-owned firm whose profit is revenue; or a form based on `output_value` of a named `material` produced by a state firm. Needs a state firm kind |
| Mint profit | Basis `coin_struck_value` less metal value, from `government_coinage.py` |
| Fines, fees, judicial profits | A justice line with fees; or leave emergent |
| Purveyance and requisition at a set price | `forced_purchase` form: goods taken at a stated price below the market, the gap being the tax. Base is the state's own need |
| Tribute received from outside (finnskatt, conquered provinces, Danegeld) | A foreign-actor flow booked as `edge:tribute` or a transfer from a named other country's government; belongs to foreign relations, not the home revenue forms |
| Revenue farmed out or tax farming with a collector's margin | `collector: farmer | official` with a `collection_cost_share`; the cost then falls on the payers or on the state as an outlay |
| Feudal incidents, reliefs, wardship | A tenure and landholding model; none exists |

A general change worth one design note: `rate` is currently a share of a base. Taxes stated as a fixed sum per head, per plough, per sack, or per ship are common in the sources and cannot be written without converting them to shares against a wage that is itself a model output. A `rate_kind` of `share` or `per_unit` would remove that conversion.

## Spending lines with their own stock

Today each line is recomputed from a world quantity each year, so a year of underspending leaves nothing behind. Candidates where a stock would carry between years:

| Line | Stock it would hold | How it accrues and decays | What it feeds |
|---|---|---|---|
| Army | Standing force, arms, horses, and a supply depot | Men in service by recruiting; equipment wears out; depot fills from in-kind revenue and draws down on campaign | Pay and rations from the depot first, coin second. Existing `standing_army` is the opening headcount (initial condition) |
| Granaries | Grain in public stores (Han ever-normal granaries, the Mexica storehouses, the Roman annona stores, the English royal purveyance stocks) | In-kind revenue and purchases when price is low; spoilage rate by storage technology; sales or dole when price is high | Dole, army supply, price stabilisation. `government_stores.py` already holds in-kind revenue; the missing parts are a named store per purpose, spoilage, and a rule to buy and sell by price |
| Roads | Kilometres of road with a condition per segment | Built by labour and materials; condition decays unless maintained; `territory().road_km` is a count today | Freight cost and army march speed (feeds the geography package through its `api.py`), so decay has an effect |
| Public buildings, aqueducts, walls | Floor area or length with condition | Same pattern as roads; today a steady upkeep proportional to town population | Urban capacity, health |
| Navy | Ships with age | Built and decays; crews in service | Coast defence, transport |
| Mint | Metal stock and coin issued | Metal bought or mined; coin struck | Pay and coin supply |
| Arsenal and castles (England, Han garrisons) | Fortification and weapon stock | As above | Campaign capacity |

Pattern: a stock is a record on the government with `quantity`, `condition`, and a `decay` coming from the material and the technology, built from the world's production data, not from this document. Each line then spends to hold or grow the stock and the stock supplies the effect. Any number here belongs in the data, not in these notes.

## Open questions

1. At 100 AD, did the Eastern Han court collect any commercial tax? The Taxation in premodern China page says no; the data file states dues are attested. The file should be checked against a primary or specialist source before more weight is put on the Han duty rows.
2. Rome: how large was the share of revenue from the land and poll taxes against customs, mines and estates, and how did it differ between Italy, the provinces and Egypt? Italy's exemption makes a single empire-wide poll rate misleading; the simulator has one home country per civilisation. Is it right to model the provinces as part of the home economy?
3. Norse 900: is a state revenue meaningful at all? If the ruler's household is the actor, then feasting circuits and the retinue are consumption, not a budget.
4. Mexica: are tribute quantities in the Codex Mendoza a record of annual flows or of nominal entitlement? Whether the tribute is a share of harvest can only be answered with a model that has provinces.
5. England 1300: what part of lay-subsidy revenue fell on the poor and what on the rich (the lay subsidy had an exemption threshold)? This decides if the `stratum_income` basis on a named stratum is the right stand-in.
6. How should conquered or tributary provinces appear: as a second country the home state taxes, or as strata of the home country? The choice decides whether tribute is `edge:` income or a transfer between governments.
7. How should a collection cost appear: as the state paying officials (a line), as the farmer's margin (a payer's loss), or both? Sources show all three, by period and by form.
8. Rates for the Roman poll tax, Han pass dues, Norse tolls and the Mexica market dues remain without a source in this pass. A targeted search of specialist literature (de Laet, Hopkins, Scheidel and Friesen for Rome; Loewe, Bielenstein and Hsu for Han; Sawyer for Norse; Berdan and Smith for Mexica) is needed before any rate moves out of confidence D. Those names are recalled and unverified here.
9. What measurable ensemble should these forms be validated against? CLAUDE.md 4.2 says distributions and relationships, not dated outcomes. The cited outcomes in this note (Roman military share, wool custom receipts) are useful as ranges to test the emergent budget against, not as targets.
