# Research: what limits the number and size of firms (Complaint 345)

Scope: replace the labelled fixed entry premium with a derived cost, and remove the limit of one entrant per proven concern per year. No code or data was changed. Tags: **[read]** the abstract or page was returned by a search and checked (full text not opened unless stated), **[snippet]** only a search summary was seen, **[recalled]** the author's recollection of the literature, unverified. No figure below is a simulator measurement; cited figures carry their source.

## 1. What the code does now

- **Premium.** `firm_entry.entry_premium(copy_cost, operators)` returns the copy cost times `ENTRY_PREMIUM_PER_OPERATOR` (a `temporary_heuristic` in `sim/agents/tuning.py`) times the operators already in the market. It is added to the stake in `Registry.consider_entry` (`sim/agents/registry.py`) and in `consider_spinoffs` (`sim/agents/spinoff.py`), then debited from the new firm as `edge:entry premium`. It scales with the copy cost of know-how, which has nothing to do with what a site or a customer base costs, and it is paid once, not every year.
- **Rate limit, agents path.** `consider_entry` is called once a year and loops over `proven_concerns`: each proven concern yields at most one new firm per call. Expected gross comes from `world.entry_gross(node, rivals, waiting + 1)`, which counts entrants already waiting for the same market but not the price effect of the other firms this same loop founds for other concerns in the same goods category. Spinoffs are limited to one per parent per year.
- **Rate limit, economy path.** `entry_plans` (`sim/economy/entry.py`) makes "at most one new maker per market with unmet demand" and sizes it at a share of the gap (`ENTRY_SHARE_OF_UNMET_DEMAND`, `ENTRY_SHARE_OF_TRADED_VOLUME`). Its return already includes land rent (`rent_by_tile` times `land_per_run`), but only for recipes that carry a land requirement; a workshop on a market tile pays nothing for the site. Exit exists (`producers_close.py`, `producer_exit.py`, `firm_exit.py`): a firm leaves at a loss or earning less than its plant would lend for.
- **Land.** `land_market.clear_land` clears arable hectares per tile against demands from producers; `land_lease.posted_rents` lags the clearing rent. Rent is a posted per-hectare figure by tile, available to anything that asks.
- **Labour.** `sim/labour/market/aptitude.py` and `records.py` carry ability bands per person. The scarce input in a firm beyond one person is whoever coordinates it; the labour core has the bands, but no one is yet drawn as the manager.

The complaint's diagnosis stands: costs a firm must carry do not scale with a growing market, so the only thing that stops the count is the rate limit.

## 2. Mechanisms that bound the number and size of firms

For each: the idea, sources, the state that could derive it.

### 2.1 Boundary of the firm: transaction and coordination costs (Coase, Williamson)

Coase 1937 names the costs of using the price mechanism (finding prices, negotiating contracts) as the reason firms exist, and "decreasing returns to the entrepreneur function" (rising overhead, more mistakes in allocating resources) as the reason a firm does not absorb everything. Size settles where the cost of organising one more transaction inside the firm equals the cost of doing it through the market. [snippet: https://acawiki.org/The_nature_of_the_firm ; https://adambrown.info/p/notes/coase_the_nature_of_the_firm]. Williamson's asset specificity argument (the more a relationship needs a specific investment, the more it moves inside the firm; the cost inside is bureaucratic loss) is [recalled].
- Simulator state: this is a boundary between "buy the input" and "make it", which the agent economy already decides per recipe through the goods market. The part that bounds size is the coordination cost of a wider span, covered in 2.2.

### 2.2 Span of control and managerial talent (Lucas 1978)

Each person has a managerial talent that multiplies the output of the capital and labour under them, with decreasing returns in the span of control. People choose to be workers or managers by talent; a more able manager runs a larger firm, and the distribution of talent maps into the distribution of firm size. [snippet: https://www.cirje.e.u-tokyo.ac.jp/research/workshops/micro/micropaper14/micro1001.pdf ; original Bell Journal of Economics 9, 508 to 523, recalled]. Implications: (a) a firm's size is bounded by the talent of its manager, not by a fixed number of people; (b) a higher wage rate raises the talent threshold for becoming a manager, so there are fewer firms and the survivors are larger [recalled]; (c) the marginal manager is indifferent between a wage and running a firm, so profit net of the manager's own opportunity wage is zero at the margin.
- Simulator state: the labour core's ability bands. The manager is one worker whose ability sets a span: the staff at which the coordination loss equals the gain. Complaint 331's span-of-control exponent on the wage bill is the labelled stand-in. The manager's opportunity cost is the wage the labour market offers that ability band (`market_wage_per_hour`; Complaint 354 notes pay following output is still off by default).

### 2.3 Selection and learning (Jovanovic 1982)

Firms do not know their efficiency at entry and learn it by operating; the efficient grow and survive, the inefficient decline and fail, so small and young firms grow faster and fail more often. [read, abstract: https://www.econometricsociety.org/publications/econometrica/1982/05/01/selection-and-evolution-industry]. Implication: a flood of entrants in one year is followed by a wave of exits; entrants should be sized small and grow on evidence.
- Simulator state: already present as the trial share (`ENTRY_SHARE_OF_UNTRADED_DEMAND`), expansion rules and `producers_to_close`. What is missing is that an entrant's efficiency differs and is unknown to it; a spread in owner ability (2.2) would give selection something to work on.

### 2.4 Entry, exit and a fixed cost in a stationary equilibrium (Hopenhayn 1992)

A competitive industry with an entry cost, a per-period fixed cost, and firm productivity shocks has a stationary distribution of firm sizes; the free-entry condition sets expected discounted profit equal to the entry cost, which pins the number of firms given demand. [read, abstract: https://econometricsociety.org/publications/econometrica/1992/09/01/entry-exit-and-firm-dynamics-long-run-equilibrium]. The free-entry condition and the exit cutoff are [recalled].
- Simulator state: the free-entry condition is what `consider_entry` already tests (`worth > copy + premium`), except that the expected profit of an entrant ignores the price its own entry causes (4.2) and the cost carried is a one-time premium, not a per-period fixed cost.

### 2.5 Fixed operating costs and the productivity cutoff (Melitz 2003)

In a heterogeneous-firm model with a fixed production cost, only firms above a productivity cutoff survive; more exposure to a larger market raises the cutoff and reallocates share to the more productive. [snippet: https://tesnewdev.econometricsociety.org/publications/econometrica/2003/11/01/impact-trade-intra‐industry-reallocations-and-aggregate ; model details recalled]. A fixed operating cost per period, paid whatever the output, makes a market of a given size support a bounded number of firms.
- Simulator state: the per-period fixed cost has to be derived (2.6, 2.2), not declared.

### 2.6 Site rent: von Thunen and Alonso

Alonso (1964, from his 1960 dissertation) extended von Thunen's agricultural rent to urban land: users bid for land near the centre in proportion to the profit that proximity gives them, and rent per hectare falls with distance. Firms near the centre use land more intensively and pay higher rent. [snippet: https://en.wikipedia.org/wiki/Bid_rent_theory ; https://www.sjsu.edu/faculty/watkins/alonso.htm]. For a market tile, the rent a workshop pays follows from the competing uses of that tile.
- Simulator state: `land_market.clear_land` already gives a clearing rent per hectare by tile; `entry_plans` already multiplies it by `land_per_run`. A site for a workshop or shop is an occupied area per unit of capacity. The land per run for a non-agricultural recipe is not authored; it would come from plant goods and staff count (floor area per worker, a physical figure), a new input in `data/production/_SCHEMA.md`. Where markets are crowded, more operators on a tile raise its clearing rent, which is the effect the current premium stands in for ("rises with the operators crowding the market").

### 2.7 Winning customers: search and switching costs

With costly search (Stigler 1961, Diamond 1971, recalled) buyers do not see every seller, and a new seller must reach them; with switching costs (Klemperer 1987) a rival's customers are locked in, so an entrant's residual demand is less than its capacity share. Klemperer 1987 is [read, abstract] in the pricing report (`Complaints/reports/innovator-pricing-research.md`, citing https://ideas.repec.org/a/oup/qjecon/v102y1987i2p375-394..html). Implication: the demand an entrant can win in its first years is its residual demand, a share of the market that grows with its reach and its price advantage.
- Simulator state: the goods market clears at one uniform price per (good, area), so every seller sells at the crossing and no one has to be found. The pricing report's Stage 1 (observable residual demand) is where a seller's own demand curve appears. A reach cost per firm would be derived from how many buyers a seller is visible to per unit of its expense, which is not modelled. Until buyers have a seller-specific state, residual demand is the usable proxy.

## 3. Evidence on pre-industrial and early industrial workshop sizes

All of the below tell a similar shape: most units are small, sizes cluster around what one skilled owner can watch, and the large sites are either many small units sharing a facility or a state or estate operation.

- **Pompeii bakeries.** About 35 bakeries are known in the city, each combining mill and oven, the larger ones with their own mills (donkey or horse driven). [snippet: https://halshs.archives-ouvertes.fr/halshs-01287449 and search summary; the Mayeske 1972 synthesis is recalled]. A lumpy plant (oven, mill) set a minimum efficient scale, and one owner-baker coordinated a handful of staff.
- **Roman potteries, La Graufesenque.** More than six hundred workshops are known there, a few dozen prominent; kilns held tens of thousands of vessels per firing. [snippet: https://en.wikipedia.org/wiki/La_Graufesenque]. The kiln-load graffiti show potters shared kilns (recalled from the literature on the graffiti), so many small workshops pooled a large lumpy plant. A shared plant decouples firm size from plant size; the simulator would need a plant-renting actor to reproduce that.
- **Jingdezhen.** Under the Ming and Qing production was divided among thousands of workers and workshops (throwing, trimming, glazing, painting, firing), with workshop types ranging from small cooperation to site-wide specialisation. [snippet: https://www.cambridge.org/core/books/city-of-blue-and-white/city-of-blue-and-white-visualizing-space-in-ming-jingdezhen-15001600/23AD8002AC2C03D7CA50AD57F3583E86 ; https://etheses.durham.ac.uk/id/eprint/16284]. Specialised firms linked by market, each stage supported by a market large enough for it: the division of labour limited by the extent of the market (Smith, recalled).
- **English cloth putting-out.** Merchant-clothiers distributed wool and collected cloth from household spinners and weavers, so a merchant's size was limited by the cost of supervising dispersed work (embezzlement, quality), and the workshop stayed household-sized until the factory made supervision cheaper (Pollard, Landes) [recalled, not searched]. The span limit is a supervision cost that depends on the technology of monitoring, not a constant.
- **Han and medieval.** Han state ironworks and salt works were large government units while private workshops were small [recalled]. Medieval guild regulation capped journeymen and apprentices per master in many towns [recalled]. Both point to institutions as a size limit; the model has a state and licences (`sim/agents/licence.py`) where this could be authored as rules.

None of these gives a number the model should reproduce (CLAUDE.md 4.1, 4.2): they give shapes to check, such as many small units in a market of a given size and the presence of shared plants.

## 4. Recommended replacement for the fixed premium

### 4.1 Three derived costs, none declared per good

The premium is replaced by what an operator must carry each year, entered in the entrant's expected margin (so it is a running cost that also drives exit), not paid once from the stake:

1. **Site rent.** The rent per hectare of the market tile (from `land_market` through the posted rents) times the area the concern occupies at its capacity. Area is derived from physical features of the recipe (plant goods and staff), not from a price. Crowding then bites through the land market: more operators on a tile raise its clearing rent, which is what the premium per operator stood in for, and rent differs by place (central markets cost more), as Alonso predicts.
2. **Management cost.** The wage of a manager of a given ability band, with the span fixed by Lucas: the manager is one worker, paid the market wage for that band (his opportunity cost), who supports a staff up to a span set by ability. When the concern outgrows one manager it hires another at a higher coordination loss, or the extra size is not worth it. This replaces Complaint 331's exponent on the wage bill and gives a fixed cost per firm that does not scale with output.
3. **Cost of reaching buyers, through residual demand.** An entrant's expected sales are its residual demand at the price it expects after it enters, not the category's takings divided by operators. Until a seller-specific buyer state exists this is where the winning-customers cost shows up: an entrant starts below its capacity share and grows with its reach.

The entry test becomes the Hopenhayn free-entry condition: expected discounted profit, net of rent and the manager's wage at the post-entry price, beats the capital tied up at the market rate. `entry_premium`, `ENTRY_PREMIUM_PER_OPERATOR` and the `edge:entry premium` debit are deleted (CLAUDE.md 4.4; the burndown count falls).

### 4.2 Why the one-entrant-per-year limit can go, and what prevents a flood

The limit now stands in for a missing expectation: an entrant that does not see its own effect on price sees a margin that does not shrink as others join, so only a rate cap stops the count. Once expected profit is computed at the price after entry, entry stops where the next entrant's expected profit is zero. Within a year the loop is written so each founded firm is added to expected supply before the next candidate is evaluated (a sequential, marginal test, as the existing `waiting` count does for one concern, extended to the whole goods category and to the economy path), so one year cannot found more firms than the market will bear. This is the pricing report's Stage 3 (capacity against expected own impact) applied to entry: expectations of post-entry price prevent the flood and no rate constant is needed. Jovanovic says the cost of overshoot is a wave of exits, so tests must also look across years (5.1).

Two residual risks, to be tested not asserted: (a) all candidates see the same stale book and found at once; the sequential count handles one year, and entrants under construction (`pending`) must count as coming supply in later years; (b) entry decisions are deterministic, so a market at the margin may oscillate; the spread in founders' capital (`founder_candidates`) and in copy chance gives some spread, but a spread in owner ability is the proper source and does not exist yet.

## 5. Staged build plan

Each stage starts with a failing regression test (CLAUDE.md section 6) and ends with `python3 sim/simulator.py validate` if data changed and a fingerprint check where behaviour should be unchanged.

**Stage 0. Measure.** A fixed-market scenario that counts firms by year and average size against market size, with today's code. Adds the relationship tests below as expected-fail until Stage 4.

**Stage 1. Marginal entry test.** Evaluate each candidate in a year in sequence, adding each founded firm to the expected supply of its goods category (agents path) and each planned maker to the market's expected supply (economy path) before testing the next. Keep the rate limit. Test: with two proven concerns in the same category the second is judged at the price after the first; the total founded in a year does not exceed what the gap can bear.

**Stage 2. Derived site rent for every concern.** Give recipes a physical occupied area (from plant and staff), apply posted rent on the market tile in `entry_plans` for all recipes and in `world.upkeep` for agent concerns. Tests: a firm on a dearer tile earns less and is founded less often, all else equal; raising the clearing rent on a tile lowers its firm count.

**Stage 3. Management as a scarce input.** Draw a manager from the labour core's ability bands for each firm; cost is that band's wage, span set by ability. Replace the Complaint 331 exponent. Tests: average firm size rises with the ability of the available managers; raising the wage rate lowers the number of firms and raises average size among survivors; no firm is founded where no manager above the margin exists.

**Stage 4. Remove the premium and the rate limits.** Delete `entry_premium`, `ENTRY_PREMIUM_PER_OPERATOR`, the debit, and the per-concern, per-parent and per-market limits. Test across seeds that entry settles rather than floods, and that exits in the year after an entry wave come from entrants that were unprofitable.

**Stage 5. Residual demand and reach.** Use the pricing report's Stages 1 and 2 so an entrant's expected sales are its residual demand; add a reach cost only if Stage 4 leaves firms too small for their market.

**Stage 6 (optional). Shared plant and institutions.** A renter of lumpy plant (kilns, mills) so many small workshops share one, and licence or guild rules as authored state data. Needed only to reproduce the La Graufesenque and guild shapes.

### 5.1 Relationship tests (ensembles of seeds; never dated outcomes, CLAUDE.md 4.2)

- The number of firms in a goods category rises with market size (population, income) and settles.
- The number of firms falls with site rent on the market tile.
- Average firm size rises with the managerial ability of the available talent.
- A higher manager wage relative to output per worker gives fewer, larger firms.
- Firm count per market rises less than in proportion to market size.
- Entrants founded in a year never exceed the number at which the last one's expected profit is zero.
- Firm count does not climb without bound while the output factor rises (Complaint 345's driver: `actors.active_firms()` on Rome seed 1 with seeded founder concerns).
- Fingerprint unchanged for runs with the agent economy off.

## 6. Open questions

1. **Who is the manager.** A member of the owner's stratum (the founder), a hired worker of the top band, or a separate slot? Lucas has the manager outside the labour force with an opportunity cost equal to the best wage. The labour core's bands do not yet mark who coordinates; the choice decides whether firm count is bounded by talent supply in a stratum or by a wage.
2. **Occupied area of non-farming concerns.** Floor area per worker and per plant good is physical but not authored. Derive it from the knowledge base, or start with staff only, labelled as a heuristic?
3. **Shared plants.** If kilns, mills and ovens are rented, does the plant owner count as a firm, or as a landlord-like actor with its own rent?
4. **Customers.** Is the uniform-price call auction enough, or must a stable buyer-seller relationship exist before the number of firms is believable? The pricing report leaves this as its Stage 6.
5. **Supervision technology.** Putting-out shows span depends on monitoring cost (literacy, accounts, transport). Should span be a function of known techniques, and which tree nodes does it read without naming them (CLAUDE.md 4.7)?
6. **Deterministic entry.** Does the labour core's draw per person give the spread in ability that entry needs, and is it seeded per actor?
7. **Institutions.** Guild and licence caps on staff or entrants can be state rules; whose state data holds them, and does the founder's civilisation start with any?
8. **Owner decision of 2026-10-02** (the complaint may be game balance rather than realism): the Lucas and Hopenhayn structure is chosen because it serves any actor without a game-balance constant; confirm before Stage 3.

## 7. Sources

- Coase 1937 summary: https://acawiki.org/The_nature_of_the_firm ; https://adambrown.info/p/notes/coase_the_nature_of_the_firm [snippet]
- Williamson (asset specificity) [recalled]; Smith on the division of labour [recalled]
- Lucas 1978: summary https://www.cirje.e.u-tokyo.ac.jp/research/workshops/micro/micropaper14/micro1001.pdf [snippet]; Bell Journal 9, 508 to 523 [recalled]
- Jovanovic 1982: https://www.econometricsociety.org/publications/econometrica/1982/05/01/selection-and-evolution-industry [read, abstract]
- Hopenhayn 1992: https://econometricsociety.org/publications/econometrica/1992/09/01/entry-exit-and-firm-dynamics-long-run-equilibrium [read, abstract]
- Melitz 2003: https://tesnewdev.econometricsociety.org/publications/econometrica/2003/11/01/impact-trade-intra‐industry-reallocations-and-aggregate [snippet]
- Bid rent (von Thunen, Alonso): https://en.wikipedia.org/wiki/Bid_rent_theory ; https://www.sjsu.edu/faculty/watkins/alonso.htm [snippet]
- Stigler 1961, Diamond 1971 [recalled]; Klemperer 1987 [read, abstract, via the pricing report]
- Pompeii bakeries: https://halshs.archives-ouvertes.fr/halshs-01287449 [snippet]; Mayeske 1972 [recalled]
- La Graufesenque: https://en.wikipedia.org/wiki/La_Graufesenque [snippet]
- Jingdezhen: https://www.cambridge.org/core/books/city-of-blue-and-white/city-of-blue-and-white-visualizing-space-in-ming-jingdezhen-15001600/23AD8002AC2C03D7CA50AD57F3583E86 ; https://etheses.durham.ac.uk/id/eprint/16284 [snippet]
- English putting-out (Pollard, Landes), Han state works, medieval guild limits [recalled]
- In the repository (read): Complaint 345, `Complaints/reports/innovator-pricing-research.md`, `sim/agents/firm_entry.py`, `registry.py` (`consider_entry`), `spinoff.py`, `sim/agents/tuning.py`, `sim/economy/entry.py`, `entry_sizing.py`, `producers_close.py`, `land_lease.py`. `land_market.py` and the labour ability modules were located and skimmed by name only.
