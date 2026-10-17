# Main fails three slow topics

**Status:** open

Measured on `origin/main` at f0ff751d with `python3 -m sim.tests --slow --only market_records_ownership,economy_tin_dearer_than_copper,insolvency_whole_game`:

- ~~`market_records_ownership`: "no module outside the market writes a market record" names
  `sim/engine/economy_electricity.py` writing `market_flows`.~~ Fixed: the throttle peek saves and
  restores the flows through `goods_market.snapshot_flows` / `restore_flows`.
- `economy_tin_dearer_than_copper`: tin shows far cheaper against copper than the labour its recipe embodies
  (511). Measured again on the 511 branch: tin is above its cost (about four to seven hours of wage a kilogram
  against about one hour of embodied labour); copper shows six to nine times its smelting cost, so the ratio fails
  on copper's scarcity price, not on unsold tin or gravel asks. Cash, loans, ore and plant do not bind year zero
  (the test's only year): the opening's workforce by trade and seeded `last_runs` do (smith hours in Spain are all
  hired), so a fix belongs with the opening. Later years: starved flux makers never grow (511's third update).
  Open.
- `insolvency_whole_game`: fixed (see 524): a household in arrears now lives within its income, so its debt no
  longer climbs past the credit limit and its cash rises.

A red slow suite on the default branch means every branch's slow run starts red and its own regressions are
read against noise. Each failure needs a fix or, where the subject is an open design issue, a pinned status
with the test kept honest.
- `affordability_and_credit`: fixed (test, not engine). The last section stepped twice and then read a project whose
  calendar floor is two years; on this branch the project (the dearest the founder can start on 30% of its bill) now
  finishes in the second step, on origin/main it was still active (late with arrears). Both are legitimate. The test
  now steps once, so a two-year floor leaves it active, and checks it is part-paid with cost still left.
- `economy_bronze_market_price`: the 502 check on bronze's shown price over its cost fails (worst about 2.4).
  Measured (stepping `rome_100ad` 18 years as the test does; shown bronze over `notional.cheapest_cost` at the shown
  input prices): it PASSES on `origin/main` (worst 1.81 in year 12, `python3 -m sim.tests --slow --only
  economy_bronze_market_price`, 133 s) and fails on this branch (the test's own 18-year run shows the worst
  years 15 to 17 at 4.1, 4.5, 5.6). It is not copper alone: bronze's cost is 90 percent copper at the shown price,
  but on the branch copper falls to 5.4 to 7.5 in years 15 to 17 while bronze stays 22 to 31, so the ask lags a
  falling input (a markdown share a year) and a thin market holds it. With the 550 change (`seller_offers.stands_for_many`,
  aggregate producers keep the price-taking reservation) disabled the late spike goes (years 15 to 17 about 0.96)
  but year 5 still shows 3.07 against the 3.0 bound, from copper halving over years 1 to 4 (12.8 to 6.8) faster than
  bronze's ask follows. So two things: the 550 aggregate pricing makes the late bronze price ratchet (not yet
  explained: why a price-taking reservation reaches 4 to 5 times cost), and any fast fall of copper shows as a
  ratio above 1 because the cost is read at the same year's inputs. Not fixed; the diagnosis is a lead for 550 and 511.
- `economy_bronze_market_price`, bisected on `economy-accounting-and-speed` (helper `bronze_multiples(6)` in the
  test file, one game per commit): years 1 to 6 are inside the bound through the 546 and 558 merges; entry sized
  to unfilled bids (559) briefly pushes year 4 over; food intake above need (513) pushes year 2 over (traded about
  3.1 times cost) through households' demand and labour, not through any bronze rule; the aggregate ask markdown
  (550) adds a lag behind falling copper in years 2 to 6. The late-year spike from 550 is fixed. What is left
  moves with every change elsewhere, as `economy_innovator_pricing` does (553): the early price over cost is a
  scarcity price while supply catches up, and it depends on when entry and expansion arrive. The test topic
  also runs over the time limit. Open; not loosened.
- `real_output` passes on `origin/main` and fails on `economy-accounting-and-speed`: the checks that a new
  entry's producer lowers the posted price, the founder's bill and raises cleared quantity and real output.
  Being bisected.
