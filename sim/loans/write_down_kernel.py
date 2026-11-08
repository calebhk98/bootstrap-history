"""A write-off of loans: each named loan loses a share of its principal and arrears (Eurace@Unibi, Firm_bankruptcy_rescale_loans)."""
import numpy

from sim.jit import njit


@njit
def write_down(loans, rows, ratios, floor, lost, remains):
    """Row `rows[i]` of the loan table loses `ratios[i]` of its principal, arrears and interest arrears, in place. `lost[i]` is
    the ratio of what was owed (principal plus arrears); `remains[i]` is whether any principal or arrears above `floor` is left."""
    for place in range(len(rows)):
        row = rows[place]
        ratio = ratios[place]
        keep = 1.0 - ratio
        lost[place] = ratio * (loans.principal[row] + loans.arrears[row])
        loans.principal[row] = keep * loans.principal[row]
        loans.arrears[row] = keep * loans.arrears[row]
        loans.arrears_interest[row] = keep * loans.arrears_interest[row]
        remains[place] = loans.principal[row] > floor or loans.arrears[row] > floor


def new_outputs(count: int):
    return numpy.zeros(count), numpy.zeros(count, dtype=numpy.bool_)
