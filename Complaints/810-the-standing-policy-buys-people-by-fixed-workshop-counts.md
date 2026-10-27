# The standing policy buys people by fixed workshop counts

**Status:** open

The optimizer's standing policy on buying people (`auto_buy_people`, `sim/workforce/standing_bondage.py`) stops once the
workshop holds a fixed number of artisans and buys at most a fixed number of people a year
(`ARTISAN_CEILING_FOR_AUTO_BUY`, `MOST_PEOPLE_AUTO_BOUGHT_PER_YEAR` in `sim/workforce/constants.py`). Neither number follows
from the household's work: a household whose concerns need more hands than the ceiling never buys them, and the yearly cap
is the same for a workshop of three and one of three hundred.

They were bare literals in the old money phase and are kept as declared heuristics with this Complaint as their retirement.
The fix sizes the purchase from the hands the household's concerns and projects lack (workforce's shortfall views) and what
the purse can carry after the reserve the two `AUTO_BUY_PEOPLE_*` multiples already declare.
