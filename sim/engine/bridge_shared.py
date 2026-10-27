"""Bridge views more than one module reads: the year, the tree, which nodes are ventures, the acting seat's staff."""
from sim.assembly.api import KEYED, QUOTE

from .bridge import bridge_view
from .units_prose import area_text, mass_per_area_text, mass_rate_text, mass_text


@bridge_view("year")
def year(sim):
	return sim.state.scenario.year


# ---- quantities in sentences: the units the player chose, the civilisation's coin (the reporting module's, when it moves) ----

@bridge_view("mass_text", kind=QUOTE)
def mass_text_view(sim, amount, digits=0, grouped=False, short=False, unit="tonne"):
	return mass_text(amount, sim, digits=digits, grouped=grouped, short=short, unit=unit)


@bridge_view("area_text", kind=QUOTE)
def area_text_view(sim, amount, digits=0, grouped=False, short=False, unit="hectare"):
	return area_text(amount, sim, digits=digits, grouped=grouped, short=short, unit=unit)


@bridge_view("mass_rate_text", kind=QUOTE)
def mass_rate_text_view(sim, amount, digits=0, grouped=False, short=True, unit="tonne"):
	return mass_rate_text(amount, sim, digits=digits, grouped=grouped, short=short, unit=unit)


@bridge_view("mass_per_area_text", kind=QUOTE)
def mass_per_area_text_view(sim, tonnes_per_area, digits=0, area="square_metre"):
	return mass_per_area_text(tonnes_per_area, sim, digits=digits, area=area)
