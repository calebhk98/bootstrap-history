"""The error raised when a figure is asked of a country the agent economy cannot answer for."""


class NoCountryEconomy(LookupError):
	"""A figure was asked of a country that has no part of the economy (or whose markets cannot answer yet).
	Every declared foreign economy is in the agent economy; there is no home answer to stand in for it."""

	def __init__(self, country: str, figure: str = "economy") -> None:
		super().__init__("country %r has no %s of its own in the agent economy" % (country, figure))
