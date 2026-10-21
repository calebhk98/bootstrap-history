"""The yearly staff phase's rules, on values given: who is let go when the payroll cannot be met, how much room a
household has to hire, what it aims to hold and how it moves toward that."""
import math


def payroll_shortfall(payroll, revenue, other_costs, capital, credit_limit):
    """What of the payroll cannot be paid: the payroll less what is left after every other cost, counting what
    lenders will still advance (the credit limit less the arrears already carried). Nothing when it can be paid."""
    headroom = max(0.0, capital + credit_limit)
    can_pay = revenue - other_costs + headroom
    return payroll - can_pay if payroll > can_pay else 0.0


def shed_for_payroll(short, headcount, annual_wage):
    """[(trade, people let go, people left)] to cover a shortfall of `short`, dearest trade first. Whole people,
    rounded up (cutting the fraction would leave part of a person drawing a wage already found unaffordable); a
    trade with no wage is skipped; a remainder under half a person is let go with the rest."""
    cuts = []
    for trade in sorted(headcount, key=lambda trade_id: -annual_wage(trade_id)):
        if short <= 0:
            break
        wage = annual_wage(trade)
        if wage <= 0:
            continue
        cut = min(headcount[trade], math.ceil(short / wage - 1e-9))
        short -= cut * wage
        left = headcount[trade] - cut
        cuts.append((trade, cut, 0.0 if left < 0.5 else left))
    return cuts


def has_room_to_hire(capital, credit_limit, credit_room_share):
    """Whether a household may take on people: it is in funds, or in arrears by no more than the share of its credit
    line that hiring may draw. Being overdrawn alone is not a bar."""
    return capital >= 0 or -capital <= credit_limit * credit_room_share


def staff_targets(scholars, artisans, scholar_capacity, artisan_capacity, extra_room, extra_scholar_share,
                  literate_ceiling, scholar_approach, artisan_approach, freedmen, slaves, slave_craft_credit):
    """(scholars wanted, generic craftsmen wanted) this year: the headcount moves a fraction of the way toward its
    target. The scholar target is the institutional capacity plus a share of the spare supervision room, never past
    the literacy ceiling; the craftsmen's is the capacity plus the room, less the freed and enslaved already counted."""
    target_scholars = min(scholar_capacity + extra_room * extra_scholar_share, literate_ceiling)
    desired_scholars = scholars + (target_scholars - scholars) * scholar_approach
    target_artisans = artisan_capacity + extra_room
    desired_artisans = artisans + (target_artisans - artisans) * artisan_approach
    craft = max(0.0, desired_artisans - freedmen - slaves * slave_craft_credit)
    return desired_scholars, craft


def hires_needed(have, wanted_whole):
    """Whole people to take on (positive) or release (negative) so `have` reaches `wanted_whole`; changes of less
    than a whole person are not acted on."""
    delta = wanted_whole - have
    if delta >= 1.0:
        return int(delta)
    if delta <= -1.0:
        return -int(-delta)
    return 0


def replacement_shortfall(have, taught, target_headcount, capital, annual_wage_of, affordability_years):
    """People of a trade to replace this year: up to the target headcount for a trade the founder taught, none for
    any other, and only when the household can cover that many years of one person's wage (`annual_wage_of()`, asked
    only when there is a shortfall). A hundredth of a person or less is not replaced."""
    want = max(have, target_headcount if taught else 0.0)
    short = want - have
    return short if short > 0.02 and capital > annual_wage_of() * affordability_years else 0.0
