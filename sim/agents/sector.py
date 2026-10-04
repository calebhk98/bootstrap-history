"""The body of people an interest group speaks for, and the keys that name it."""


class Sector:
	"""One body of people hurt by the same cause: what it lost, what it lives on, who it is."""

	def __init__(self, kind: str, subject: str, name: str, cause: str, lost_income: float,
				 income_base: float, members: float, scope: float) -> None:
		self.kind = kind
		self.subject = subject
		self.name = name
		self.cause = cause
		self.lost_income = lost_income
		self.income_base = income_base
		self.members = members
		# the share of the state's revenue that comes from the territory the group lives in
		self.scope = scope
		# the share of this loss for which the founder is blamed
		self.blame_share = 1.0

	# the sources of sectors beyond the founder's sales and hiring, reached through this class
	@staticmethod
	def of_strata(strata, world):
		from .group_strata import stratum_sectors
		return stratum_sectors(strata, world)

	@staticmethod
	def remember_welfare(strata):
		from .group_strata import remember_welfare
		remember_welfare(strata)

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
	def reached_by(node_id, nodes, made_by, commodity_of):
		"""The commodities and goods categories a technique touches."""
		from .group_reach import subjects_reached
		return subjects_reached(node_id, nodes, made_by, commodity_of)


CONCESSION_PREFIX = "concession: "


def sector_key(kind: str, subject: str) -> str:
	return kind + ":" + subject

