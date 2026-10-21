"""What staff are paid and who leaves: plain functions of the pay, the market's wage and the draws."""


def pay_of(market_wage, keeps_pay_at_market, held_pay):
    """A year's pay of one person on the payroll: the going wage while pay is kept at the market, else the figure
    last settled (the going wage when none was)."""
    return market_wage if keeps_pay_at_market else (market_wage if held_pay is None else held_pay)


def blended_pay(have, held_pay, count, offered_pay):
    """The settled pay of a trade after `count` people are taken on at `offered_pay`, weighted by head."""
    return (have * held_pay + count * offered_pay) / max(have + count, 1e-9)


def settled_pay(held_pay, trades_held, market_wage_of, keeps_pay_at_market):
    """The pay settled for the coming year: trades no longer held are dropped, and with pay kept at the market
    every trade held is settled at the going wage."""
    settled = {trade: pay for trade, pay in held_pay.items() if trade in trades_held}
    if keeps_pay_at_market:
        for trade in trades_held:
            settled[trade] = market_wage_of(trade)
    return settled


def wage_bill_of(heads, pay_of_trade):
    """What the standing staff costs in a year: the head of each trade times its pay."""
    return sum(head * pay_of_trade(trade) for trade, head in heads.items())


def roll_trade(head, offer_rate, death_rate, draw):
    """Roll each of `head` people for the year: one dies below the death rate, else takes a better offer at the
    offer rate. Returns (died, left, survivors) as counts."""
    died = left = 0
    for _ in range(head):
        roll = draw()
        if roll < death_rate:
            died += 1
        elif roll < death_rate + (1.0 - death_rate) * offer_rate:
            left += 1
    return died, left, head - died - left


def wage_for_hours_of(annual_wage, hours_per_person_year, hours, reputation, bonus_cap, bonus_scale):
    """What `hours` of the founder's own work pay: the trade's hourly rate (its yearly wage over the hours in a year) times a
    bonus of reputation over `bonus_scale`, capped at `bonus_cap`; a reputation below nothing earns a smaller rate."""
    rate = annual_wage / hours_per_person_year
    return hours * rate * (1.0 + min(bonus_cap, reputation / bonus_scale))
