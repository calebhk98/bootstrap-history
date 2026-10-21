"""Provisional numbers behind the guards and inspectors a state keeps, each awaiting a derivation."""
from sim.constants import declare

PATROL_DAYS_PER_PERSON = declare(
	"PATROL_DAYS_PER_PERSON", 0.02, kind="temporary_heuristic",
	unit="guard-days per person per year", source=None, confidence="D",
	retire="Complaint 660 follow-up: guards sized by the watch a district's crimes ask, not a time per head",
	why="Guard time a state keeps per person of the people it governs for watch, patrol and answering an alarm. "
		"No source found that gives it for a whole pre-modern state. Upper bound only: the capital's standing watch, "
		"vigiles (seven cohorts of 1,000, Wikipedia 'Vigiles') plus urban cohorts (three cohorts of about 500 under "
		"Augustus, Wikipedia 'Cohortes urbanae') for a city of about one million (Wikipedia 'Rome'), is "
		"(7000 + 1500) / 1000000 = 0.0085 staff per person, times 200 working days = 1.7 guard-days per person per "
		"year; a state-wide average sits well below a capital's density, so this value is held under it "
		"(sim/tests/test_order_staffing_sourced.py). Stands in for a model of the watch.")
INSPECTION_DAYS_PER_PERSON = declare(
	"INSPECTION_DAYS_PER_PERSON", 0.005, kind="temporary_heuristic",
	unit="inspector-days per person per year", source=None, confidence="D",
	retire="Complaint 660 follow-up: inspectors sized by the claims and workings on the registry, not a time per head",
	why="Inspector time a state keeps per person of the people it governs for checking claims and workings of "
		"mines against the registry. No source found; stands in for a model of the claims register.")
FORESTER_DAYS_PER_PERSON = declare(
	"FORESTER_DAYS_PER_PERSON", 0.01, kind="temporary_heuristic",
	unit="forester-days per person per year", source=None, confidence="D",
	retire="Complaint 660 follow-up: foresters sized by the woodland a district holds under tenure, not a time per head",
	why="Forester time a state keeps per person of the people it governs for marking boundaries, watching felling "
		"and keeping tenure of coppice. No source found for a pre-modern state; stands in for a model of the woodland "
		"register.")
