"""Where a bonded person lives changes the yearly death rate (Complaint 648). The stratum model carries no tiles, so a
stratum's plan names the shares of its members by kind of residence and this rule weights what each residence adds."""
from typing import Mapping

from sim.constants import declare

MALARIAL_EXCESS_DEATH_RATE = declare(
	"MALARIAL_EXCESS_DEATH_RATE", 0.01, kind="biological_parameter", unit="extra deaths per member per year",
	source="Scheidel 2005, 'Human Mobility in Roman Italy, II: The Slave Population', JRS 95, pp. 76-77 (Gwern.net copy): "
		   "'annual excess mortality of 1 per cent' for rural slaves who laboured in malarial terrain, an assumption he "
		   "applies to a tenth, a sixth or a third of rural slaves; he does not claim to measure it.",
	confidence="C",
	why="Added to the base death rate for the share of a bonded stratum living and working in malarial country.")


def residence_death_rate(base_death_rate: float, residence_shares: Mapping[str, float],
						 premium_of_residence: Mapping[str, float]) -> float:
	"""The stratum's death rate: the base rate raised, for each residence, by that residence's premium (a share of the
	base rate, from the demography's town premium) or, for malarial land, by the sourced excess rate, each weighted by the
	residence's share of members. Shares are normalised; a residence with no figure adds nothing."""
	total = sum(max(0.0, share) for share in residence_shares.values())
	if total <= 0.0:
		return base_death_rate
	added = 0.0
	for residence, share in residence_shares.items():
		weight = max(0.0, share) / total
		if residence == "malarial":
			added += weight * MALARIAL_EXCESS_DEATH_RATE
		else:
			added += weight * base_death_rate * max(0.0, premium_of_residence.get(residence, 0.0))
	return base_death_rate + added
