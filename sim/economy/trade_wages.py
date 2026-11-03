"""The one rule for the wage per hour a trade is priced at, wherever a bid, a quote or a crew needs it:
1. the wage the labour core recorded for the trade in the scope (the memory holds only wages above zero,
   `labour_state.mirror_wages`, so one that is there is positive; the core clears a (trade, area) only when it has workers
   or bids, so a trade nobody works or hires in an area has no recorded wage there);
2. else, only for a trade the memory holds no wage for in any area (before the economy's first clearing, or a trade the opening gave
   a wage that the memory holds nowhere), the wage the economy opened with for the trade scaled to today's money (`MarketMemory.opening_wage_level`: an
   opening-year nominal wage is out of date after inflation and after the spin-up's rebase);
3. else, for a trade the memory holds a wage for elsewhere or the opening gave none (one only a late entry uses), the scope's unskilled wage plus the trade's training premium,
   or, where the scope has no unskilled wage, the opening unskilled wage in today's money plus the premium.
A trade that is hired somewhere and not here is therefore priced from here, on this area's unskilled wage, never on a frozen
opening wage.

The rule answers for every scope, home or partner: the opening unskilled wage exists and is positive by construction
(sim/markets/port_setup.py adds the unskilled trade to the labour trades and refuses an opening with no positive quote
for it), so after the economy opens no trade is without a wage. A trade id the setup does not know is refused.

The unskilled wage is of the scope the caller asks about: one labour area (`wage_in_area`, `wage_in_view`) or the
country's figure (sim/economy/api.py `country_trade_wage`): the mean of the core's area wages over the country's areas,
weighted by hours hired there last year, else (a trade nobody hired in the country) by the people working it in each area,
else plainly. A trade with no recorded wage in the country is priced by rule 2 or 3 on the country's unskilled wage; the
opening wage never overrides a wage the memory holds for the trade anywhere.

Households differ on purpose: a household is a seller, and what it faces in a market with no recorded wage is its own
reservation wage (`faced_wage`), the least it will work for, not the wage an employer would be billed. A tax or land
bid that reads a wage for a cohort prices a trade by the rule above like any other caller. A country in the economy always
answers (`NoCountryEconomy` is raised only for a country with no economy part)."""
from typing import Optional

from sim.labour.api import CAREER_YEARS, wages

from .household_time_preference import HOUSEHOLD_TIME_PREFERENCE
from .market_memory import market_key


def premium_for_training_years(training_years: float) -> float:
    """What training years add to the pay a worker asks, as a share over the unskilled wage: the core's training
    premium (a multiple, labour/market/premium.py) less one, at the family's own time preference, since the family
    pays for training by going without, not by borrowing. The clearing reads the same multiple at the same rate
    (`labour_context`)."""
    if training_years <= 0.0:
        return 0.0
    return wages.training_premium(training_years, HOUSEHOLD_TIME_PREFERENCE, CAREER_YEARS) - 1.0


def trade_premium(setup, trade) -> float:
    """`premium_for_training_years` for a trade of the setup (a trade the setup has no spec for is a KeyError)."""
    return premium_for_training_years(setup.trades[trade].training_years)


def priced_trade_wage(setup, trade: str, paid: Optional[float], unskilled: Optional[float],
                      opening_wage_level: float, held_anywhere: bool) -> float:
    """The wage per hour of `trade` given what its market paid (None if nothing), the unskilled wage of the same
    scope (None if none), the level the opening wages are scaled by (`MarketMemory.opening_wage_level`) and whether the
    memory holds a wage for the trade in any area. Raises KeyError for a trade the setup has no spec for."""
    if trade not in setup.trades:
        raise KeyError(f"unknown trade {trade!r}: the setup's trades are {sorted(setup.trades)}")
    if paid is not None:
        return paid
    opening = setup.opening_wages.get(trade)
    if opening is not None and not held_anywhere:
        return opening * opening_wage_level
    if unskilled is None:
        unskilled = setup.opening_wages[setup.unskilled_trade] * opening_wage_level
    return unskilled * (1.0 + trade_premium(setup, trade))


def wage_in_area(setup, memory, trade: str, area: str) -> float:
    """The wage per hour of `trade` in a labour area, on the area's unskilled wage and the memory's price level."""
    return priced_trade_wage(setup, trade, memory.wages.get(market_key(trade, area)),
                             memory.wages.get(market_key(setup.unskilled_trade, area)),
                             memory.opening_wage_level(setup.currency_id), memory.holds_wage_for(trade))


def wage_in_view(setup, view, trade: str, area: str) -> float:
    """`wage_in_area` read through a market view."""
    return priced_trade_wage(setup, trade, view.wage(trade, area), view.wage(setup.unskilled_trade, area),
                             view.opening_wage_level(setup.currency_id), view.wage_held_anywhere(trade))


def faced_wage(recorded: Optional[float], reservation: float) -> float:
    """The wage per hour a household seller faces: the recorded wage of its market, else its reservation wage."""
    return reservation if recorded is None else recorded
