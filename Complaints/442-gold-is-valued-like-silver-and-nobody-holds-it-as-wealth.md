# Gold is worth no more than silver per kilogram to households, and nobody holds it as wealth

**Status:** open - data (`data/world/needs.json`) and an economy mechanism to design

Measured on the agent economy (scratch driver replaying the deleted `sim/economy_validate.py`,
30 years, seeds 1-3; no command prints it yet, Complaint 445): the median gold-to-silver price ratio
is about 6 in England, far below one in Rome, and in the thousands to tens of thousands in Han,
Mexica and Norse, where gold barely trades; the attested ratio is around 10-15 (see
`Complaints/reports/economy-research-extraction-and-money-metals.md`, weak sources). Gold's price
swings by more than its own value year to year.

Why:
- the only household use of gold is the `ornament` need, whose effectiveness is "equal across the
  bright metals" per kg. Buyers then take gold only when it costs no more per kg than silver: gold
  either sells at or below silver's price (Rome, where the hydraulic route is cheap) or not at all;
- there is no demand to hold precious metal as wealth (plate, hoards, temple treasure). Households save
  only in coin and loans (`households_orders.savings_target`), so a metal's price is set by a year's
  flow against a thin ornament demand, not by willingness to hold the stock, which was dozens of years
  of output;
- goods are not durable in the economy at all (Complaint 443), so an ornament bought is used up.

What it would take:
- data: an ornament effectiveness that is not equal per kg, or better, none needed: a store-of-value
  demand in which prestige follows scarcity, so the ratio emerges;
- economy: households keep part of their savings in durable, non-spoiling goods of high value per kg,
  chosen by those physical properties and the price, not by id; selling from that stock when its price
  is high is what makes the stock, not the flow, set the price.
