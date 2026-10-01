# A concern that sells at solved cost earns its staff's wages and nothing above

**Status:** open

Solved prices are cost-based: a good's price repays its inputs, labour, the capital charge the entry states (build bill over service life and capacity) and rent. A node whose revenue is derived from output (`sim/engine/node_revenue.py`) earns that price less what it buys, and since derived upkeep (`sim/engine/node_upkeep.py`) charges its staff at the same wages, revenue less upkeep is only the capital charge less the plant's maintenance. Where the entries state no capital (the data's own judgement that capital is small against labour), the node earns exactly its staff's wages: revenue equals upkeep and the node never pays back what it cost to build. Measure with `python3 sim/node_revenue_report.py` (the line "earning exactly their upkeep" and the net payback distribution), per civilisation with `--civ`.

This is what cost-based prices give a competitive, price-taking producer, so it is not a bug in the derivation. It means the founder's income from these concerns has to come from somewhere else: a margin over cost that the market layer supplies (`Sim.market_price_ratio` above one, scarcity, demand above supply), rent on a deposit or site, a technique cheaper than the one that sets the price (the founder's advantage), or return on capital in the solver (interest in the capital charge, which the capital-markets work owns). Until one of them exists a derived concern is a way to employ staff at no loss, and payback-driven choices between concerns are driven by the few that state capital.

Related: `Complaints/287`, `Complaints/351` (closed), `Complaints/39`.
