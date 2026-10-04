# Research brief: commodity money, cacao, and how much of a money commodity gets monetised

Two research agents in economy round four. Labels: **[read]**, **[snippet]**, **[memory]**
(unverified). The trigger was Mexica's hunger: cacao is both the money and a food. A mint that buys up
to a whole money stock's worth of beans a year at parity let cacao take land from food on the
tropical tiles.

## History
- **Where cacao grew.**
  - Cacao was climate-limited to a few wet lowland provinces: Soconusco, and the Chiapas to
    El Salvador coast [snippet: export.com.gt, encyclopedia.com].
  - Ahuitzotl conquered Xoconochco for its cacao, which came to the highlands as tribute and
    through pochteca trade [snippet].
- **Food where it grew.** The cacao regions also farmed maize and used forest products [snippet:
  csudh.edu Soconusco ethnoecology]. No evidence was found of famine caused by cacao planting before
  1521 [memory].
- **Cacao as money.**
  - Beans were small change. Mantles and copper axes covered larger sums [snippet: balagan.info,
    Cornell].
  - Tlaxcala 1545 prices: a turkey hen 100 beans, an avocado 1 [snippet].
  - Beans were counterfeited and graded by quality [snippet].
  - Their value against goods moved with supply [snippet and memory].
- **Tobacco money in Virginia** is the closest analogue.
  - Overplanting crashed tobacco's price (the 1727 glut), and the colony had to require food crops
    [snippet: NPS].
  - The answer was inspection, burning trash tobacco and warehouse notes (the 1730 Act [read:
    Wikipedia]), not a fixed purchase at parity.

## Theory [memory unless marked]
- **The money stock is set by demand** (Barro 1979 [citation snippet]; Friedman; Smith on the cost of
  commodity money). The monetary use of the commodity is real money demand over the commodity's
  relative price.
- **The steady flow into money** is the growth of money demand plus wear and loss.
- **When making money pays too well,** the price level rises, and so the commodity's relative price
  falls, until making it pays no more than other uses.
- **An unbounded mint bid** is right only if the price level answers within the period. In an annual
  model with slow prices it soaks up production.
- **Agent-based models** (Kiyotaki-Wright; Marimon, McGrattan and Sargent) keep the money stock
  exogenous. Games add bullion as an exogenous flow.

## What follows for the model
- **Natural, and kept:** cacao taking the scarce tropical land; cacao regions buying food; local food
  prices rising.
- **A modelling failure, fixed:** monetising without limit at parity. A commodity money now takes into
  circulation only what holders want to add to their cash, plus what spoils
  (`sim/economy/mint.yearly_monetisation`). Struck coin and weighed metal keep the mint capacity: there
  the metal is the money, and a silver strike can still raise prices.
- **Still to consider:** subsistence maize on cacao growers' own plots; quality and counterfeiting as
  costs of using commodity money.
