"""The one rule for the wage per hour a trade is priced at, wherever a bid, a quote or a crew needs it:
the wage its labour market paid (the memory holds only wages above zero, `labour_state.mirror_wages`, so a wage that
is there is positive), else the wage the economy opened with for the trade scaled to today's money
(`MarketMemory.opening_wage_level`: an opening-year nominal wage is out of date after inflation and after the
spin-up's rebase), else the unskilled wage of the same scope plus the trade's training premium, else the opening
unskilled wage in today's money plus the premium.

The rule answers for every scope, home or partner: the opening unskilled wage exists and is positive by construction
(sim/markets/port_setup.py adds the unskilled trade to the labour trades and refuses an opening with no positive quote
for it), so after the economy opens no trade is without a wage. A trade id the setup does not know is refused.

The unskilled wage is of the scope the caller asks about: one labour area (`wage_in_area`, `wage_in_view`) or the
country's hours-weighted figure (sim/economy/api.py `country_trade_wage`).

Households differ on purpose: a household is a seller, and what it faces in a market with no recorded wage is its own
reservation wage (`faced_wage`), the least it will work for, not the wage an employer would be billed. A tax or land
bid that reads a wage for a cohort prices a trade by the rule above like any other caller. A country in the economy always
answers (`NoCountryEconomy` is raised only for a country with no economy part)."""
from typing import Optional

from sim.labour.api import CAREER_YEARS, wages

from .households_orders import HOUSEHOLD_TIME_PREFERENCE
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
                      opening_wage_level: float) -> float:
    """The wage per hour of `trade` given what its market paid (None if nothing), the unskilled wage of the same
    scope (None if none) and the level the opening wages are scaled by (`MarketMemory.opening_wage_level`). Raises
    KeyError for a trade the setup has no spec for."""
    if trade not in setup.trades:
        raise KeyError(f"unknown trade {trade!r}: the setup's trades are {sorted(setup.trades)}")
    if paid is not None:
        return paid
    opening = setup.opening_wages.get(trade)
    if opening is not None:
        return opening * opening_wage_level
    if unskilled is None:
        unskilled = setup.opening_wages[setup.unskilled_trade] * opening_wage_level
    return unskilled * (1.0 + trade_premium(setup, trade))


def wage_in_area(setup, memory, trade: str, area: str) -> float:
    """The wage per hour of `trade` in a labour area, on the area's unskilled wage and the memory's price level."""
    return priced_trade_wage(setup, trade, memory.wages.get(market_key(trade, area)),
                             memory.wages.get(market_key(setup.unskilled_trade, area)),
                             memory.opening_wage_level(setup.currency_id))


def wage_in_view(setup, view, trade: str, area: str) -> float:
    """`wage_in_area` read through a market view."""
    return priced_trade_wage(setup, trade, view.wage(trade, area), view.wage(setup.unskilled_trade, area),
                             view.opening_wage_level(setup.currency_id))


def faced_wage(recorded: Optional[float], reservation: float) -> float:
    """The wage per hour a household seller faces: the recorded wage of its market, else its reservation wage."""
    return reservation if recorded is None else recorded
