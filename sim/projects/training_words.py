"""The player's wording of what teaching a trade nobody here can supply costs."""


def training_advice_text(advice):
	"""The train command and its cost, from the facts of teaching one person a trade (`hours_each` and `years` are None
	when no trade here can teach it)."""
	if advice["source_trade"]:
		cost = "about %.0f of your own hours each, %.1f years" % (advice["hours_each"], advice["years"])
	else:
		cost = "no trade here to teach it from"
	return '{"cmd":"train","trade":"%s","n":1} (%s)' % (advice["trade"], cost)
