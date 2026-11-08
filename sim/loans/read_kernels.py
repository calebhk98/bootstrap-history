"""Whole-table reads of the loans: per-agent totals added in row order, the way a Python loop over the loan list added them.

The sums here are plain left-to-right additions into one slot per agent (`totals[agent] += value`), as the dict loops they replace did;
a sum that Python took with `sum()` over floats is not one of them (it is compensated: see `python_sum` in `sim/economy/year_close_sums.py`)."""
import numpy

from sim.jit import njit


@njit
def claim_value(principal, arrears, arrears_share):
    """What a lender expects to collect on a loan: the principal and the arrears less the share it doubts, which rises with the
    arrears until `arrears_share` of the principal, where they are worth nothing (credit_claims.claim_value)."""
    if principal <= 0.0:
        return max(0.0, arrears)
    doubt = min(1.0, arrears / (arrears_share * principal))
    return principal + arrears * (1.0 - doubt)


@njit
def total_by_agent(agents, values, selected, count, start):
    """(totals, first_row): for each agent number `start` plus the `values` of its selected rows added in row order, and the first
    selected row it appears in (-1 for an agent with none), so a caller can list the agents in order of first appearance."""
    totals = start.copy()
    first_row = numpy.full(len(start), -1, dtype=numpy.int64)
    for row in range(count):
        if selected[row]:
            agent = agents[row]
            totals[agent] += values[row]
            if first_row[agent] < 0:
                first_row[agent] = row
    return totals, first_row


@njit
def claim_values(principal, arrears, count, arrears_share):
    """`claim_value` for each of the first `count` rows."""
    claims = numpy.empty(count)
    for row in range(count):
        claims[row] = claim_value(principal[row], arrears[row], arrears_share)
    return claims


@njit
def debt_total_by_agent(agents, principal, arrears, selected, count, agent_count):
    """For each agent number the sum of principal plus arrears over its selected rows, added as `(total + principal) + arrears`
    row by row (the order the loan loops added them); also the first selected row of each agent (-1 for none)."""
    totals = numpy.zeros(agent_count)
    first_row = numpy.full(agent_count, -1, dtype=numpy.int64)
    for row in range(count):
        if selected[row]:
            agent = agents[row]
            totals[agent] = totals[agent] + principal[row] + arrears[row]
            if first_row[agent] < 0:
                first_row[agent] = row
    return totals, first_row
