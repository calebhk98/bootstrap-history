"""What a switch of trade is discounted by, worked out once per year for every destination (`switch_year.switch_all`).

A group weighing a switch pays the income it gives up over the training years and gains the income difference over the career
left after the training. The discount factors depend on the destination's training years and on the group's kind, never on the
area, the source trade or the incomes, so `plan_area` reads them from a table instead of working out three exponentials for
each destination of each group."""
from typing import NamedTuple

import numpy as np

from sim.jit import njit

YOUNG, FULL, RETRAINED = 0, 1, 2   # the rows of the tables: the young train the destination's years, an established worker in another family the same, within the family a share


class Discounts(NamedTuple):
    """`[kind, destination]` tables, kind being YOUNG, FULL or RETRAINED."""
    lost: np.ndarray       # annuity over the training years: multiplied by the income given up
    start: np.ndarray      # discount to the end of the training
    after: np.ndarray      # annuity over the career left after the training
    pays: np.ndarray       # the career outlasts the training (otherwise the gain is nothing)


@njit
def annuity(rate, years):
    """`premium.annuity_factor`."""
    if years <= 0.0:
        return 0.0
    if rate <= 0.0:
        return years
    return (1.0 - np.exp(-rate * years)) / rate


@njit
def career_gain(amount, start, after, pays):
    """`expectations.present_value` of an income difference from the end of the training to the end of the career."""
    if not pays:
        return 0.0
    return amount * start * after


@njit
def _fill_kind(tables, kind, rate, trained, remaining):
    for destination in range(trained.shape[0]):
        tables.lost[kind, destination] = annuity(rate, trained[destination])
        tables.pays[kind, destination] = remaining > trained[destination]
        tables.start[kind, destination] = np.exp(-max(0.0, rate) * trained[destination])
        tables.after[kind, destination] = annuity(rate, remaining - trained[destination])


@njit
def discount_tables(rate, career_years, remaining_share, years, retraining_share):
    """The tables for the year's destinations (`years`: training years of each)."""
    count = years.shape[0]
    tables = Discounts(np.empty((3, count)), np.empty((3, count)), np.empty((3, count)), np.empty((3, count), np.bool_))
    remaining_established = career_years * remaining_share
    _fill_kind(tables, YOUNG, rate, years * 1.0, career_years)
    _fill_kind(tables, FULL, rate, years * 1.0, remaining_established)
    _fill_kind(tables, RETRAINED, rate, years * retraining_share, remaining_established)
    return tables
