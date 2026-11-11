"""Titles sold in the year (Complaint 538): on each tile, the holders who would rather have money offer hectares and the
cohorts on the tile with cash to spare bid for them (rules in title_sales.py). A sale moves the title and the money and the
seller stays on the land as the buyer's tenant. The year's prices are kept per tile and, with the rent, give the land yield
the lenders read (lender_ask.land_yield).

A holder sells when it needs money (its cash is under the target it rests at, or it is in arrears on a loan), asking
what the rent is worth at the rate cash costs it; or, with no need, when what the tile's rent earned over its last sale
price is under what its money earns elsewhere. Titles pledged to a loan or let out are not offered.
"""
from typing import Dict, List, Mapping, Optional

from . import titles, titles_ground, title_sales
from .cohort_store import table_of
from .household_time_preference import HOUSEHOLD_TIME_PREFERENCE
from .types import AgentId, Transfer

SALE_PURPOSE = "land_sale"


def _arrears_by_borrower(loans) -> Dict[AgentId, float]:
    owed: Dict[AgentId, float] = {}
    for loan in loans:
        if loan.arrears > 0.0:
            owed[loan.borrower] = owed.get(loan.borrower, 0.0) + loan.arrears
    return owed


def run(setup, record, public_premium: Optional[float], cost_of_cash: Optional[float],
        pledges: Optional[Mapping[tuple, float]] = None) -> List[title_sales.Sale]:
    """Clear each tile's title sales and settle them. `cost_of_cash` is the rate a holder short of money pays for it (the market's
    loan rate, None before one); `pledges` is `titles.pledges_by_title` when the caller has it. Returns the sales made."""
    money = setup.currency_id
    store = table_of(record.cohorts)
    order = store.order()
    ids = [store.ids[row] for row in order.tolist()]
    cash = record.book.balance_by_agent(ids, money)
    target = dict(zip(ids, store.floats("cash_target", order)))
    inflation = dict(zip(ids, store.floats("expected_inflation", order)))
    arrears = _arrears_by_borrower(record.credit.loans)
    pledges = titles.pledges_by_title(record.credit) if pledges is None else pledges
    cohorts_on = {tile: [store.ids[row] for row in store.rows_on_tile(tile).tolist()] for tile in store.tiles_present()}
    rates = {cohort_id: title_sales.discount_rate(HOUSEHOLD_TIME_PREFERENCE, inflation[cohort_id], public_premium) for cohort_id in ids}
    made: List[title_sales.Sale] = []
    year_prices: Dict[str, float] = {}
    year_hectares: Dict[str, float] = {}
    for tile_id in sorted(record.land.titles):
        tile, rent = setup.tiles.get(tile_id), record.land.land_rent.get(tile_id, 0.0)
        if tile is None or rent <= 0.0 or not cohorts_on.get(tile_id):
            continue
        arable = titles_ground.arable_hectares(record, tile_id, tile)
        sellers = _offers(record, tile_id, arable, rent, rates, cash, target, arrears, pledges, cost_of_cash)
        if not sellers:
            continue
        selling = {seller.agent_id for seller in sellers}
        buyers = [bid for bid in (title_sales.bid_for(cohort_id, rent, rates[cohort_id], cash[cohort_id] - target[cohort_id])
                                  for cohort_id in cohorts_on[tile_id] if cohort_id not in selling) if bid is not None]
        sales = title_sales.clear_tile(sellers, buyers)
        done = _settle(record, money, tile_id, arable, sales, cohorts_on[tile_id])
        for sale in done:
            cash[sale.seller] = cash.get(sale.seller, 0.0) + sale.hectares * sale.price_per_hectare
            cash[sale.buyer] = cash.get(sale.buyer, 0.0) - sale.hectares * sale.price_per_hectare
        if done:
            year_prices[tile_id], year_hectares[tile_id] = title_sales.year_price(done), sum(sale.hectares for sale in done)
            record.land.sale_price_by_tile[tile_id] = year_prices[tile_id]
            made.extend(done)
    found = title_sales.market_land_yield(record.land.land_rent, year_prices, year_hectares)
    if found is not None:
        record.credit.set_land_yield(found)
    return made


def _offers(record, tile_id, arable, rent, rates, cash, target, arrears, pledges, cost_of_cash) -> List[title_sales.Seller]:
    """What each cohort that holds a free title on the tile offers."""
    offers = []
    last_price = record.land.sale_price_by_tile.get(tile_id)
    for holder in sorted(titles.shares(record, tile_id)):
        if holder not in rates:
            continue
        free = (titles.free_share(record, holder, tile_id, pledges) - titles.let_out_share(record, tile_id, holder)) * arable
        need = max(0.0, target[holder] - cash[holder], arrears.get(holder, 0.0))
        own_rate = rates[holder]
        if need > 0.0:
            offer = title_sales.asking_offer(holder, free, rent, title_sales.seller_discount_rate(own_rate, cost_of_cash), need)
        elif last_price is not None and rent / last_price < own_rate:      # its land earns it less than its money does elsewhere
            offer = title_sales.asking_offer(holder, free, rent, own_rate)
        else:
            offer = None
        if offer is not None:
            offers.append(offer)
    return offers


def _settle(record, money, tile_id, arable, sales, residents) -> List[title_sales.Sale]:
    """Pass each sale's title and its money; a seller that lives on the tile stays as the buyer's tenant. Returns the sales that went through."""
    done = []
    for sale in sales:
        moved = titles.pass_title(record, tile_id, sale.seller, sale.buyer, sale.hectares / arable)
        if moved <= 0.0:
            continue
        hectares = moved * arable
        record.book.transfer(Transfer(sale.buyer, sale.seller, money, hectares * sale.price_per_hectare, SALE_PURPOSE))
        if sale.seller in residents:
            titles.lease(record, tile_id, sale.seller, sale.buyer, moved)
        done.append(title_sales.Sale(sale.seller, sale.buyer, hectares, sale.price_per_hectare))
    return done
