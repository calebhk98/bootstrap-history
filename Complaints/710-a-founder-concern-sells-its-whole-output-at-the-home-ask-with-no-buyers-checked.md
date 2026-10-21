# A founder concern sells its whole physical output at the home ask with no buyers checked

**Status:** open

Found reading a playtest (`Complaints/reports/playtest-rome-seed11-agent-to-221.md`, "lead_chamber/sulfuric_retort acid sales
~4M/yr ... labourer wage 37/yr"). The report called it "legit production, unrealistic scale". The scale is not an
artefact of the report; it follows from how an open concern's takings are made:

- `node_output.output_baskets` / `plant_figures.yearly_baskets` size the yearly output from the concern's staff and the
  recipe's labour hours (`sim/engine/node_revenue.py` `_apply_output`). Nothing in that sizing asks how much of the good
  anyone wants.
- `venture_real_earnings` (`sim/engine/projects_venture_quotes.py`) multiplies that output's long-run value by
  `node_output_market_factor` (`sim/engine/economy_production.py`), which is `basket_market_factor`
  (`sim/engine/node_revenue_market.py`): this year's net over long-run net, with each material at
  `goods_market.home_unit_price`, the price the home sellers ASK (`sim/engine/goods_market_offers.py`), not a price
  anything traded at. The factor does not take the quantity, so a thin market's ask multiplies a full plant's output.
- The founder's tonnes are not offered into the goods market and cleared against buyers; the only demand limit is the one
  aggregate saturating ceiling in `_compute_revenue_uncached` (`REVENUE_CEILING_LABOUR_HOURS_PER_POP_SCALE`, a
  `temporary_heuristic`), which cuts every concern by the same share whatever the good.
- Sulfuric acid is an intermediate: its buyers are other chemical works, almost none of which exist at a Rome opening
  (`grep -n sulfuric_acid_kg data/production/*.json` lists the consumers). A good with no buyers still pays the full ask.

It is the same shape as 576 (iron) and sits beside 642 (a price nobody traded at, partly fixed: the quote kind is carried
on `MarketView`, but this reader of `home_unit_price` does not read it) and 643 (the ask band). It breaks 4.3: the
founder's output should propagate through the normal market rules, as any firm's does (`business_books.operate` pays
firms only from the book when the year's market clears, `sells_on_book`).

Pinned by `sim/tests/test_node_revenue_market_no_demand_check.py`: the factor is ask over cost whatever the quantity, and
takings are linear in tonnes with no buyer limit. Rewrite that test when this is fixed.

What it would take: a founder concern's output enters the year's goods market as a seller and is paid what clears
(a founder is one more actor, 4.3), so a good with no buyers sells nothing and a thin one sells at the price it clears
at. The quote shown by `ventures`/`why` then reads a cleared price or says it is a quote (`quote_kind`, 642). The
aggregate ceiling is then a candidate for retirement. A test calls the clearing with built books: a concern's tonnes
against a book with no bid take no money. This touches `sim/economy/` (the clearing), which another session is editing,
so it is filed, not fixed.
