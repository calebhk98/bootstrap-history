# The price of silver and gold follows the yearly cost of mining, not the stock of metal in circulation and the demand for money

**Status:** open

Measured: the solver prices silver at its marginal deposit's production cost (`python3 sim/solve_prices.py --civ rome_100ad --why silver_kg`, about 378 hours per kg), and the coin is pinned to that, so every nominal wage inherits it. A pre-industrial empire held a stock of silver many times its yearly output (Patterson 1972, about 10,000 t in the mid-2nd century against about 200 t a year; cited, not opened), so the price reflects money demand over the stock, hoarding, plate and ornament, with production cost as the long-run floor. There is no metal stock, no losses or hoarding and no minting demand.

What it would take: a precious-metal stock per economy (opening stock as an initial condition with its basis), flows in from mines and trade and out by loss, hoarding and ornament; the market price from demand for coin and goods against that stock; production cost as the floor below which mines close. Design note first. Source review: `Complaints/reports/silver-mining-and-minting-review.md`. Related: 284, 305, 338, 349.

Update (Complaint 375): the coin metal is held at the mint's standard when converting partner prices and merchant capital (`Sim._coin_metal_price`), so the metal does not follow the goods' price level; its own price still follows its mining cost, not a stock.
