"""The body of people an interest group speaks for, and the keys that name it."""


class Sector:
	"""One body of people hurt by the same cause: what it lost, what it lives on, who it is."""

	def __init__(self, kind: str, subject: str, name: str, cause: str, lost_income: float,
				 income_base: float, members: float, scope: float, technique: str = "") -> None:
		self.kind = kind
		self.subject = subject
		self.name = name
		self.cause = cause
		self.lost_income = lost_income
		self.income_base = income_base
		self.members = members
		# the share of the state's revenue that comes from the territory the group lives in
		self.scope = scope
		# the technique said to have taken the members' living, when one can be told
		self.technique = technique
		# the share of this loss for which the founder is blamed
		self.blame_share = 1.0

	# the sources of sectors beyond the founder's sales and hiring, reached through this class
	@staticmethod
	def of_strata(strata, world):
		from .group_strata import stratum_sectors
		return stratum_sectors(strata, world)

	@staticmethod
	def remember_welfare(strata, world=None):
		from .group_strata import remember_welfare
		remember_welfare(strata, world)

	@staticmethod
	def of_firms(firms, world):
		from .group_firms import firm_owner_sectors
		return firm_owner_sectors(firms)

	@staticmethod
	def remember_margins(firms):
		from .group_firms import remember_margins
		remember_margins(firms)

	@staticmethod
	def displacing_technique(trade, running, nodes):
		"""The running technique that most recently began doing a category's work with fewer hands of a trade."""
		from .group_jobs import displacing_technique
		return displacing_technique(trade, running, nodes)

	@staticmethod
	def of_foundations(foundations):
		from .foundation import foundation_sectors
		return foundation_sectors(foundations)

	@staticmethod
	def remember_foundations(foundations):
		from .foundation import remember_collections
		remember_collections(foundations)

	@staticmethod
	def of_servants(government, world):
		from .group_servants import servant_sectors
		return servant_sectors(government, world)

	@staticmethod
	def remember_servants(government, world):
		from .group_servants import remember_servants
		remember_servants(government, world)

	@staticmethod
	def of_goods(strata, categories, world):
		from .group_goods import goods_sectors
		return goods_sectors(strata, categories, world)

	@staticmethod
	def protection_needed(group_strength, opposition_line):
		"""The protection that lets the founder build despite a prohibition a group of this pull obtained."""
		from .group import protection_needed
		return protection_needed(group_strength, opposition_line)

	@staticmethod
	def reached_by(node_id, nodes, made_by, commodity_of, substitutes_of=None):
		"""The commodities and goods categories a technique touches, and (given `substitutes_of`) those of the
		goods that serve the same needs as what it makes."""
		from .group_reach import subjects_reached
		return subjects_reached(node_id, nodes, made_by, commodity_of, substitutes_of)


CONCESSION_PREFIX = "concession: "


def sector_key(kind: str, subject: str) -> str:
	return kind + ":" + subject

