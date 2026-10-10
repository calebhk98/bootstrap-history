"""Provisional numbers behind how actors answer the state's demands, each awaiting a derivation."""
from sim.constants import declare

DEMAND_STANDING_DISCOUNT = declare(
	"DEMAND_STANDING_DISCOUNT", 0.55, kind="temporary_heuristic",
	unit="share of enforcement turned aside at full standing", source=None, confidence="D",
	why="How much of a state's reach over a refusal a fully protected actor turns aside; the same "
		"share the requisition rate is bargained down by. Stands in for a model of patronage "
		"and who the state can afford to offend.")
REFUSAL_PENALTY_MULTIPLE = declare(
	"REFUSAL_PENALTY_MULTIPLE", 1.0, kind="temporary_heuristic",
	unit="demands, at full state capacity", source=None, confidence="D",
	why="What an enforced refusal adds to the demand itself, in demands, for a state of full "
		"capacity; scaled down by the capacity. Stands in for fines, seizure of the goods "
		"withheld and the cost of the officers sent to collect.")
NEGOTIATE_OFFER_SHARE = declare(
	"NEGOTIATE_OFFER_SHARE", 0.5, kind="temporary_heuristic",
	unit="share of the demand offered in money", source=None, confidence="D",
	why="The share of a demand an actor that negotiates offers in money. Stands in for a model of "
		"what each side knows of the other's walk-away price.")
STATE_SERVICE_VALUE_SHARE = declare(
	"STATE_SERVICE_VALUE_SHARE", 0.8, kind="temporary_heuristic",
	unit="share of the service's cost to the actor", source=None, confidence="D",
	why="How much of what a service costs the actor who renders it the state counts against a demand; "
		"the rest is lost in the state having to organise and use it.")
CONCEALED_SHARE_OF_WEALTH = declare(
	"CONCEALED_SHARE_OF_WEALTH", 0.5, kind="temporary_heuristic",
	unit="share of wealth", source=None, confidence="D",
	why="The share of its wealth an actor that conceals holds where the state cannot count it. "
		"Stands in for a model of which holdings can be moved out of sight.")
CONCEALMENT_COST_RATE = declare(
	"CONCEALMENT_COST_RATE", 0.05, kind="temporary_heuristic",
	unit="share of the concealed wealth a year", source=None, confidence="D",
	why="What hiding wealth costs a year (guards, go-betweens, wealth held idle where it earns "
		"nothing). Stands in for a model of the price of secrecy.")
CONCEALMENT_DETECTION_SHARE = declare(
	"CONCEALMENT_DETECTION_SHARE", 0.5, kind="temporary_heuristic",
	unit="share of the state's enforcement chance", source=None, confidence="D",
	why="How much of its reach over a refusal a state turns to finding hidden wealth; finding it is "
		"harder than collecting what is in plain view.")
REFUSAL_DEFIANCE = declare(
	"REFUSAL_DEFIANCE", 0.4, kind="temporary_heuristic",
	unit="defiance points a refusal adds (0..1)", source=None, confidence="D",
	why="How far one refused demand marks the actor in the state's eyes. Stands in for a model of "
		"how a state remembers who defied it.")
DEFIANCE_MEMORY = declare(
	"DEFIANCE_MEMORY", 0.7, kind="temporary_heuristic",
	unit="share of defiance kept a year", source=None, confidence="D",
	why="How much of the state's memory of a refusal is still there a year on.")
DEFIANCE_NOTICE_WEIGHT = declare(
	"DEFIANCE_NOTICE_WEIGHT", 0.3, kind="temporary_heuristic",
	unit="visible scale added at full defiance", source=None, confidence="D",
	why="How much more visible to the state an actor that has defied it is: the state looks harder "
		"at whoever has shown it will not pay.")
REFUSAL_BLAME_POINTS = declare(
	"REFUSAL_BLAME_POINTS", 2.0, kind="temporary_heuristic",
	unit="scandal points per refused demand", source=None, confidence="D",
	why="Public blame a refusal puts on the one who refused, on the same scale as the alarm points a "
		"technology raises when it is finished.")
