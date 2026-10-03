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


CONCESSION_PREFIX = "concession: "


def sector_key(kind: str, subject: str) -> str:
	return kind + ":" + subject
