"""What a state's own take does to the money it raises, through the unrest it arms (Complaint 657), for the fiscal menu.

A take above the one people are used to is their grievance (`unrest.grievance`, the same rule the stability phase reads); the
share of the people it makes discontented is `unrest.unrest`, and the discontented do not pay the part of the take that raised
the grievance. So an option that raises `extra` money from taxpayers with `taxpayer_income` yields only what the rest pay:

    unrest_added   = unrest(grievance(extra, 0, 0, taxpayer_income), no hunger, no burden)
    net_of_unrest  = extra * (1 - unrest_added)

The take people have grown used to adds nothing (`unrest.adapted`), so only the extra is counted."""
from . import unrest


def unrest_added(extra_take: float, taxpayer_income: float) -> float:
	"""Share of the taxpayers made discontented by taking `extra_take` more than they are used to; none where no income is
	visible to take it from."""
	return unrest.unrest(unrest.grievance(max(0.0, extra_take), 0.0, 0.0, taxpayer_income), None, 0.0)


def net_of_unrest(extra_take: float, taxpayer_income: float) -> float:
	"""Money of `extra_take` that the taxpayers who are not made discontented by it pay."""
	return max(0.0, extra_take) * (1.0 - unrest_added(extra_take, taxpayer_income))


def lost_per_money_kept(extra_take: float, taxpayer_income: float) -> float:
	"""Money lost to unrest for each money the option brings in after it; zero where nothing comes in."""
	kept = net_of_unrest(extra_take, taxpayer_income)
	return (max(0.0, extra_take) - kept) / kept if kept > 0.0 else 0.0
