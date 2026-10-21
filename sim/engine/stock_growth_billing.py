"""Whose head a year's herd growth is raised at the expense of."""


def founder_billed_growth(grown, held, society_head):
    """The part of `grown` (units of increase on `held` units) that is the founder's to pay for: the society's own head
    (`society_head`, kept by its producers' recipes) is raised at their expense, only head beyond it is the founder's."""
    society = min(held, society_head)
    return grown * (held - society) / held
