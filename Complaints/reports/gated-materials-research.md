# Gated materials: import or unavailable, and physical supply (Complaints 38 and 119)

Scope: research and a staged plan only. No code or data changed; the test suite was not run. Code references are to the branch `structural-dedupe-and-owner-decisions` as of 2026-10-06. Source tags: **[read]** page opened and checked; **[snippet]** only a search summary seen; **[recalled]** author's memory, unverified. Every historical source below is [snippet] (search summaries only, none opened), so all of it is a distribution check to be verified before it is used in a test.

## 1. What happens today

### 1.1 The three price provenances

`sim/engine/prices.py` `priced_goods_table` solves three times and labels each material (`sim/engine/data.py` `goods_provenance`):

- `solved`: made by a technique the civilisation holds.
- `gated`: made only by an unheld technique, priced at the nearest such technique (fewest research steps, `entries_in_reach`) with held techniques for every other input. Crops the climate cannot grow are skipped here.
- `mature`: nothing in reach makes it; priced as if every gate were held. Labelled transitional (CLAUDE.md 4.4), standing for an import "no Roman trader could actually bring".

In every case the material still gets a price, so the engine treats it as buyable. That is the defect: a price is a statement that someone sells at that cost, and for these materials nobody in the world model does.

### 1.2 Measurements

Command (per civilisation, change `c`):

    python3 -c "import sys,collections;sys.path.insert(0,'.');from sim.engine import data;c='rome_100ad';p=data.goods_provenance(frozenset(data.load_civ(c)['starting_techs']),civilization_id=c);print(collections.Counter(p.values()))"

| Measured 2026-10-06 | solved | gated | mature | total priced |
|---|---|---|---|---|
| rome_100ad | 150 | 127 | 22 | 299 |
| han_china_100ad | 153 | 127 | 19 | 299 |
| england_1300 | 149 | 128 | 22 | 299 |
| norse_900ad | 147 | 130 | 22 | 299 |
| mexica_1500 | 126 | 151 | 22 | 299 |

So roughly half of the priced materials are not made by what the civilisation holds, in every scenario. The gate nodes per material come from `requires_node` on the production entries (`sim/engine/prices.py` `all_gate_nodes`); the Rome list (material and its gating node ids) is the output of the same call joined to `prices._default_production_entries()` on `outputs` and `requires_node`. Examples for Rome, gated: `aluminium_kg` (`mat_aluminium`), `silk_kg` (`tx2_sericulture`), `paper_kg` (`prn_hand_papermaking`), `porcelain_kg` (`mat_porcelain`), `steel_plate_kg` and `tool_steel_kg` (`cementation_steel`), `zinc_kg` (`zinc_metal`, `mt2_zinc_by_electrolysis`), `sulfuric_acid_kg` (`sulfuric_retort`, `lead_chamber`). Mature: `nickel_kg` (`mat_nickel`), `cobalt_kg`, `stainless_steel_kg`, `cement_portland_kg`, `silicon_carbide_kg`, `glass_borosilicate_kg`, `pepper_kg` (`fud_pepper_cultivation`, climate), `cacao_kg`, `cassia_kg` (no gate, climate only).

Who in the dataset could supply them (same session, `goods_provenance` for each civilisation, set arithmetic on the `solved` labels):

| Question, Rome as buyer, 2026-10-06 | count |
|---|---|
| Materials Rome does not solve (gated plus mature) | 149 |
| Of those, solved by Han China | 9 |
| Of those, solved by any of the other four civilisations | 14 |
| Of those, solved by none of the five | 135 |

The nine Han supplies are `silk_kg`, `silk_cocoon_kg`, `silkworm_eggs_kg`, `mulberry_leaves_kg`, `ramie_stock_kg`, `cassia_kg`, `cast_iron_kg`, `pig_iron_kg`, `flue_dust_kg`: silk, cassia and cast iron, which is what Rome historically imported from the east [recalled]. Han (the only enabled partner, `data/world/foreign_economies.json`) does not solve `paper_kg` or `porcelain_kg` in the data, which is a data question to check (Han held the paper technique; see section 5).

The other 135 are not made by any civilisation file in the repository. Under the recommendation they are unavailable to a Roman buyer, however cheap their mature price looks.

### 1.3 Which curves read price to infer physical supply

All in `sim/engine/economy_materials.py`:

- `_generic_national_output_uncached` (via `_generic_national_output_t_per_yr`): output equals an anchor divided by price raised to an exponent, clamped by a floor and a ceiling (`GENERIC_OUTPUT_ANCHOR_T_PER_YR`, `GENERIC_OUTPUT_PRICE_EXPONENT`, `GENERIC_OUTPUT_FLOOR_T_PER_YR`, `GENERIC_OUTPUT_CEILING_T_PER_YR`). Fitted from three curated commodities (iron, copper, gold).
- `_generic_market_share_uncached` (via `_generic_market_share`): share equals a scale divided by price raised to an exponent, clamped (`GENERIC_MARKET_SHARE_*`).
- Both feed `_national_output_tonnes`, `_society_output_tonnes` and `_material_market_tonnes`, hence `resource_throttle` and `material_price_factor`. Price is read through `_denarii_price_per_kg` and `_material_price_per_kg`, which take the solver's price (the fallback to `commodities.json` `base_price_denarii_per_kg` at `_material_price_per_kg` is authored book money, the third problem).
- Related, not supply: `economy_mining.py` `_mine_capex_opex` returns "not mineable" for any material the solver does not price, so a priced gated material becomes mineable by the founder with generic deposits; `mining_tech` is a physical multiplier and is fine.
- `commodities.json` (nine commodities) is authored book denarii; the ledger path (`_commodity_ledger`, `country_output`) is the curated half and does not infer from price, but its base prices are book money.

Evidence the curve invents markets (relationship, same session, Rome, formula applied to the solved price in `calculated_goods_prices`; price ratio to wheat is measured, tonnage is the curve's own output):

| Material (Rome, provenance) | price over wheat price | curve's national output, tonnes a year |
|---|---|---|
| aluminium_kg (gated) | 360 | 118 |
| silk_kg (gated) | 492 | 84 |
| paper_kg (gated) | 101 | 477 |
| porcelain_kg (gated) | 9 | 6852 |
| steel_plate_kg (gated) | 10 | 6048 |
| pepper_kg (mature) | 17 | 3452 |
| cassia_kg (mature) | 5 | 12108 |
| nickel_kg (mature) | 2 | 31551 |

Command: the formula in `economy_materials.py` evaluated on `data.calculated_goods_prices(held, civilization_id='rome_100ad')`, divided by its `wheat_kg` entry. Two corrections to the complaint's wording. First, under the in-reach price aluminium is dear for Rome (the route needs electrolysis inputs priced through Roman techniques), so its fitted market is small; the "enormous market for a cheap gated material" bites where the mature or in-reach price is low: nickel, cassia, porcelain and steel plate get thousands of tonnes a year from a curve that knows nothing about whether a nickel mine, a porcelain kiln or any Roman supplier exists. Second, as a civilisation's held set grows (electricity held, aluminium route cheap) the same curve for aluminium climbs towards its ceiling, so the defect is latent for later scenarios. The curve returns the same tonnage whether a partner makes the good, nobody does, or a deposit exists, which is the root problem: price is an output of supply and cannot also be its input without circularity.

## 2. Recommendation

A material is in exactly one of three states for a buyer, decided by physical facts, never by a price:

1. **Made at home** (`solved`): supply is physical capacity at home (section 2.1), price is the solved cost.
2. **Imported**: no home technique, but at least one partner in reach holds a technique, has the resource access and the inputs, and a merchant carries it. Delivered price is the partner's own production cost, plus freight over the route, plus the merchant's margin and the partner's own export policy; quantity is bounded by the partner's capacity above its own demand and the carriers' lift.
3. **Unavailable**: nobody in reach can make it. No price, no supply, no market. The founder can unlock it by learning the technique (a home route then exists and the material becomes `solved` or the nearest-technique `gated` price applies as a plan cost for the founder's own build), not by buying it.

This removes `mature`. `gated` survives as a different thing: a planning cost for a technique the actor is considering (what would it cost to make X at the nearest technique), never a market price. Callers that need "can I buy it now" ask availability, not price.

### 2.1 Physical capacity replaces the fitted curves

- Mined and quarried materials: capacity from deposits and regions the territory holds (`sim/world/deposits.py`, `sim/world/mineral_shares.py`, `geography.mineral_scale`, which already exists and is used in `_material_market_tonnes`), worked at the held mining technique (`mining_tech`) and the labour the region's population can allocate. A material with no deposit in reach has zero capacity.
- Made and grown materials: capacity follows from the stock of the plant or land that makes it (kilns, furnaces, hectares) and the inputs and labour it draws, as `sim/engine/foreign_capacity.py` already does for partners ("a made or grown one follows its demand when the economy holds a technique for every step of the chain and every ore deposit on that chain lies in its regions; anything else has no capacity and is only bought"). The home society should use the same rule, so the code that sizes a partner's supply is the code that sizes the home market's; `economy_materials.py` then stops carrying its own estimate.
- The ledger's curated nine (`commodities.json`, `MARKET_SHARE_*`) keep their authored shares only until their output comes from capacity; their base prices must come from the solver (Complaint 119 remains).
- Market share (what an ordinary buyer can reach) is a standing and competition question (the buyer's share of the clearing market, `market_standing`), not a function of price. After capacity exists, the share becomes the buyer's fraction of demand in the clearing, with no price-fitted curve.

### 2.2 What must exist for each state

| State | Needs | Exists today | Missing |
|---|---|---|---|
| Home | Capacity from plant, land, deposits, labour | Deposits, mineral scale, mining tech, solved prices | A home capacity model for made goods and a bound on mining by deposit; the fitted curves removed |
| Import | Partner economy with its own recipes, techniques, wage, coin and capacity; route and freight; merchants carrying goods; margin; the partner's export policy | `sim/engine/foreign_economies.py` (partner solved prices, `_foreign_solved_materials`, `partner_refusal`), `foreign_capacity.py`, `foreign_routes.py`, `foreign_traders.py`, `foreign_payments.py`, `sim/world/trade_between.py`, `data/world/foreign_economies.json` | Only one partner enabled; partners are market books, not agents (MULTI_ACTOR_STATE_PLAN section 3.1); merchant margin and wait are heuristics (merchant-terms report); `not_traded_materials` only lists land; the home price table does not consult it |
| Unavailable | A boolean the price table and callers can read | Provenance labels | `mature` and `gated` still return a price; callers (`goods_market_api.py`, `economy_freight.py`, `economy_mining.py`, project costs) assume a price exists |

The central design point: the home price table must not hold a price for an import until the foreign market book clears. Today the home table is the price the founder pays everywhere; under this design an imported good's price is the clearing price of the foreign-and-home book, so it falls when the partner's technique improves or freight falls, as the engine's `trade_between` already allows for the goods it carries.

### 2.3 Historical distribution checks

Use these as relationships (an import premium over a home good is large, varies by good and distance, and shrinks with competition and shorter routes), never as targets. All are [snippet]; none was opened.

- Silk. Diocletian's edict of 301 gives a top price of 150,000 denarii for one pound of purple silk (Edict on Maximum Prices; also "What things cost in Ancient Rome") [snippet: https://en.wikipedia.org/wiki/Edict_on_Maximum_Prices, https://constantinethegreatcoins.com/edict/]. Relationship: the highest-priced non-human goods in the edict are imported textiles and dyes, many times grain per kilogram. Check: Rome's silk price over wheat is large and rises with route length.
- Indian Ocean trade. Pliny's complaint that Indian wares sold in the empire at about a hundred times their prime cost [snippet: https://en.wikipedia.org/wiki/Indo-Roman_relations, Pliny quoted via a search summary]. A rhetorical, tax-and-risk-laden figure; use only the relationship that the delivered price of a long-route luxury exceeds source cost by a multiple far above merchant interest, falling when routes shorten. Expect lower in a competitive, multi-merchant model.
- Spices. Pepper was worth about its weight in silver at Malabar, and in fifteenth-century England a pound of pepper cost more than two days of a skilled craftsman's wage, a pound of cloves nearly five, saffron a month [snippet: https://brewminate.com/the-medieval-spice-trade/]. Duties at Alexandria reached a third of value at times, with Venice stacking its own margin [snippet, same page]. Relationship: markup is a stack of tolls, freight and margins per leg, and each added leg adds to it. Two detailed pepper-price papers surfaced and are the better sources to open: https://resolve.cambridge.org/core/journals/journal-of-economic-history/article/pepper-prices-before-da-gama/6C850DB458DB453869EB8F41791F02BF [snippet] and https://resolve.cambridge.org/core/journals/journal-of-the-royal-asiatic-society/article/spice-prices-in-the-near-east-in-the-15th-century/91D05F45BE0AF9F1D3AAB50EAE3D449E [snippet].
- Steel. Wootz from South India was exported to Arabia and Persia and worked into Damascus blades in Khorasan and Isfahan [snippet: https://en.wikipedia.org/wiki/Wootz_steel]. Relationship: a technique-held-only-by-one-region good is traded as a finished or semi-finished good, and the importer's price follows the exporter's production cost plus carriage; no price figure found.
- Tin. British tin was traded as far as the southern Levant by about 1300 BCE, up to 4,000 km [snippet: https://dur.ac.uk/news-events/latest-news/2025/05/britains-long-distance-tin-trade-transformed-the-bronze-age/]; Pytheas describes it passing from an island to the Rhone mouth in about a month. Relationship: a material tied to one deposit region, needed by every bronze-making society, is imported over very long routes, and the importer's bronze costs depend on that route, which is the case a deposit-bound `unavailable-or-imported` rule must reproduce (no deposit in reach, so import or nothing).
- Counter-evidence for the model: Muziris papyrus cargo value, Geniza and Venetian profit rates (the merchant-terms report already holds these: venture profits moderate in competitive trade, very high under charter monopoly) bound the margin component separately from the premium that is mostly freight and duty.

Not found: any figure for the price ratio of imported to home iron, or pre-industrial steel imports to Europe. Leave those as open data checks.

## 3. Staged plan

Each stage opens with a failing regression test (CLAUDE.md 6) and a fingerprint record, because the price table feeds the whole simulation. Counts to track: the table in section 1.2 (how many materials are `mature`, `gated` and priced without a supplier) and `python3 sim/constants.py --burndown` for the `GENERIC_*` constants.

**Stage 0: availability as data, no behaviour change.** Add an availability function next to `goods_provenance` that returns `home`, `import`, `unavailable` for a buyer civilisation given the set of partner civilisations in reach (all enabled foreign economies; `data/world/foreign_economies.json`). Import means some partner's `solved` set contains the material and the partner does not refuse it (`exports_refused`) and the material is not in `not_traded_materials`. Files: `sim/engine/data.py` (or a new small `sim/engine/availability.py`), reading `foreign_economies.py`. Tests: the table in 1.2 is reproduced; a material no partner makes is `unavailable`; adding a partner that holds the technique turns it into `import`; a refused material stays `unavailable`.

**Stage 1: unavailable means no price.** The price table drops `mature` entries for materials classified `unavailable` and returns no price for them; callers handle absence. Files: `sim/engine/prices.py` (`priced_goods_table`), `sim/engine/data.py`, callers that assume a price (`goods_market_api.py`, `economy_freight.py`, `economy_mining.py`, `foreign_routes.py`, `project_materials.py`, node cost derivation in `data.py`). `gated` is kept as a "plan cost" table under another name, used only for the founder's own route costs and `node_revenue`. Tests: a material nobody in reach makes has no market and no quote (the `material_trade_quote` is absent), buying it fails with a reason naming the missing technique; a node that needs it reports why it cannot be built; learning the technique makes it `solved` and gives a price.

**Stage 2: imports priced through the foreign market book.** The home price of an `import` material is the clearing price of the book in `foreign_economies.py` (partner price in home money, plus `_route_freight_per_tonne`, plus the merchant's margin), not the in-reach solve. Files: `sim/engine/foreign_economies.py`, `foreign_capacity.py`, `foreign_routes.py`, `foreign_traders.py`, `sim/engine/incumbent_prices.py` (`_material_prices`), `sim/world/trade_between.py`. Tests: an imported price rises with freight and falls when freight falls; it falls when the partner's solved cost falls (partner technique improves); it is at least the partner's own cost plus carriage; quantity is bounded by partner capacity above its own demand and by lift; a refusing partner halts the import; the import premium over the partner's price grows with route length and shrinks with the number of merchants (merchant-terms stage 1 relationship). Dependency: the merchant margin stays the labelled heuristic until the merchant-terms stages land.

**Stage 3: physical capacity replaces the fitted curves.** Home supply of any material comes from the capacity model of `foreign_capacity.py` applied to the home society plus mining capacity from deposits; delete `_generic_national_output_uncached`, `_generic_market_share_uncached` and the `GENERIC_*` constants. Files: `sim/engine/economy_materials.py`, `foreign_capacity.py` (shared function), `sim/world/deposits.py`, `sim/world/mineral_shares.py`, `sim/constants.py` registry through `declare`. Tests: a material with no deposit and no held technique has zero home capacity; adding a deposit raises capacity without any price change; capacity is independent of price (the same plant at a doubled price gives the same tonnage); no module imports `GENERIC_OUTPUT_*`. Needs an owner decision on the home share for the curated nine (section 5).

**Stage 4: `commodities.json` prices from the solver, the book labourer wage derived.** Replace `base_price_denarii_per_kg` with solved prices and remove `BOOK_LABOURER_WAGE_DENARII_PER_HOUR` (Complaint 119 remains). Files: `data/world/commodities.json`, `sim/engine/commodity_ledger*.py`, `sim/engine/money_units.py`. Tests: removing the field leaves the ledger working; no book denominated constant remains (`rg` per Complaint 119's definition of done).

**Stage 5: partner economies as agents.** Real partner producers, cohorts and merchants rather than market books, per `MULTI_ACTOR_STATE_PLAN.md` stages G and H. It makes stage 2's partner capacity and margin emerge from partner firms rather than a formula. Not a prerequisite for stages 0 to 3; those can run on today's market books.

Relationship tests across stages: a material no partner in reach makes has no market; an imported price falls when a partner's technique improves or freight falls; an imported price always exceeds the partner's own cost; an import quantity never exceeds partner capacity less its own demand; removing a partner removes the materials only it makes; a buyer's availability is independent of any price table.

### Dependencies and in-flight work

- `MULTI_ACTOR_STATE_PLAN.md`: stages 0 to 3 need none of A to I and only touch engine files named above. Stage 5 here is stages G and H there. Stage C of that plan edits goods market files that stage 1 above also touches (`goods_market_api.py`): sequence after C or coordinate file ownership.
- `Complaints/reports/merchant-terms-research.md`: stage 2's margin, wait and staffing are its stages 1 to 3; until they land the margin is the labelled heuristic. Its open question 1 (one merchant implementation) decides which module the import margin lives in.
- `Complaints/reports/innovator-pricing-research.md`: sellers choosing prices from the book; imported-price formation at stage 2 should use the same residual-demand function it proposes, so pricing stage 1 of that report should land first or be consumed through a stub.
- Complaints 302 and 309: `gated` in-reach pricing is built there and is reused as the plan cost; the by-product floor question in 309 is unaffected.
- Complaints 382 step 1 (counterparties) edits founder postings in engine files stages 1 and 2 touch; sequence after it merges.
- Complaint 324 and 350 (sourced output per region) provide the partner deposit and output data that stage 3 and 5 need.

## 4. Why not keep a price and add a flag

A flag on a still-priced material leaves every caller free to ignore it; the failure found in the complaint (a Roman market for nickel) comes from callers trusting a price. Making absence the representation of unavailability forces each caller to decide what to do. This follows CLAUDE.md 4.3 (interventions propagate through normal rules: a founder who learns the technique gets the material by the same recipe path any actor uses) and 4.5 (a price is calculated from a producer's cost or a clearing, never from an assumption that someone makes it).

## 5. Open questions

1. Partner coverage. Only one partner is enabled (Han China), so for a Roman buyer most gated materials are unavailable, and that is also true for Han as a buyer. Is that the intended scenario (other civilisation files switched on as partners where dates overlap), or is a generic "rest of world" partner wanted for materials such as tin, amber, incense and the mature-price set? A rest-of-world partner would be a labelled heuristic again.
2. Data check: Han held paper and a porcelain-like technique in the historical record [recalled], but the data does not make `paper_kg` or `porcelain_kg` solved for Han. Is that a starting-techs gap?
3. Does the founder count as a possible importer's supplier, so a partner can buy from the founder's own firms? The plan assumes yes (general actors), which stage 2 should not preclude.
4. Plan cost versus unavailable: should the founder see a "what it would cost to make X" estimate for an unavailable material? This report says yes for planning, under a different name from the market price.
5. Quantity of non-traded goods: `not_traded_materials` lists only land; should bulky goods (gravel, bricks, timber over land) be bound by freight alone or listed?
6. Where margin for a merchant monopoly (charter, as Venice's galleys) comes from; the merchant-terms report's question 5.
7. Which pepper and silk price papers will be opened and verified as the distribution checks (section 2.3 lists candidates, none read).
