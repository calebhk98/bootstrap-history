"""Provisional numbers behind awareness and staged adoption, each awaiting a measured carrier or a fitted curve."""
from sim.constants import declare

AWARENESS_RATE_PER_CONTACT = declare(
	"AWARENESS_RATE_PER_CONTACT", 0.5, kind="temporary_heuristic",
	unit="per unit of contact volume per year", source=None, confidence="D",
	retire="contact volume measured from carried tonnes, migrants and routes (sim/agents/awareness.py contact_volume)",
	why="Chance per year, per unit of contact volume with a holder, that an actor learns a technique exists: "
		"hazard = 1 - exp(-rate * volume). Stands in for a rate fitted to how fast news travels along a trade link.")
CONTACT_FADE_PER_YEAR = declare(
	"CONTACT_FADE_PER_YEAR", 0.5, kind="temporary_heuristic",
	unit="share kept each year", source=None, confidence="D",
	retire="contact volume measured from carried tonnes, migrants and routes (sim/agents/awareness.py contact_volume)",
	why="How much of a one-off contact (a new route, a conquest, a migration) still counts a year later.")
DEMONSTRATION_VOLUME = declare(
	"DEMONSTRATION_VOLUME", 1.0, kind="temporary_heuristic",
	unit="contact volume at full exposure", source=None, confidence="D",
	retire="contact volume measured from carried tonnes, migrants and routes (sim/agents/awareness.py contact_volume)",
	why="Contact volume a founder's working demonstration gives an onlooker who sees all of it.")
TRADE_TONNES_FOR_UNIT_CONTACT = declare(
	"TRADE_TONNES_FOR_UNIT_CONTACT", 1000.0, kind="temporary_heuristic",
	unit="tonnes a year", source=None, confidence="D",
	retire="contact volume measured from carried tonnes, migrants and routes (sim/agents/awareness.py contact_volume)",
	why="Tonnes carried a year between two places that count as one unit of contact between their people.")
PILOT_SHARE = declare(
	"PILOT_SHARE", 0.02, kind="temporary_heuristic",
	unit="share of the actor's production", source=None, confidence="D",
	retire="a pilot plant built through the ordinary plant path with its own staffing (Complaints/491 remainder, plant-level stages)",
	why="Share of its production an actor puts on a technique while it tries it: a pilot plant or a few hands.")
TRIAL_YEARS = declare(
	"TRIAL_YEARS", 2, kind="temporary_heuristic",
	unit="years", source=None, confidence="D",
	retire="a trial judged when the pilot plant's own books have a full cycle",
	why="Years an actor tries a technique before judging its realised margin.")
ADOPTION_SPEED_PER_MARGIN_GAP = declare(
	"ADOPTION_SPEED_PER_MARGIN_GAP", 1.0, kind="temporary_heuristic",
	unit="logistic slope per year per unit of relative margin gap", source=None, confidence="D",
	retire="slope fitted to observed diffusion curves by technique class (Griliches 1957 fits slope to profitability)",
	why="Slope of the logistic adoption curve, share' = speed * gap * share * (1 - share): the form is "
		"Griliches's, the proportionality of slope to profitability is his finding, the constant is not fitted.")
