"""Provisional numbers behind interest groups, each awaiting a derivation."""
from sim.constants import declare

GROUP_ORGANISING_WEIGHT = declare(
	"GROUP_ORGANISING_WEIGHT", 2.0e-4, kind="temporary_heuristic",
	unit="share of the revenue of the territory the group lives in", source=None,
	confidence="D",
	why="Income lost, as a share of the state's revenue from the group's own territory, at which "
		"those who lost it organise to act on the state. Stands in for a model of collective "
		"action (who knows whom, what a petition costs).")
GROUP_DISBANDING_SHARE = declare(
	"GROUP_DISBANDING_SHARE", 0.5, kind="temporary_heuristic",
	unit="share of the organising weight", source=None, confidence="D",
	why="A group stays organised until its lost income falls below this share of the level at "
		"which it formed, so a grievance on the line does not flicker in and out of existence.")
GRIEVANCE_RETENTION = declare(
	"GRIEVANCE_RETENTION", 0.85, kind="temporary_heuristic",
	unit="share kept per year", source=None, confidence="D",
	why="How much of last year's lost income a group still counts when the cause has eased; "
		"stands in for memory and for losses that outlast their cause (stranded tools, "
		"unlearned trades).")
GROUP_PULL_SCALE = declare(
	"GROUP_PULL_SCALE", 0.01, kind="temporary_heuristic",
	unit="share of the territory's revenue", source=None, confidence="D",
	why="Lost income, as a share of the territory's revenue, at which a group commands about "
		"six tenths of the state's attention. Stands in for a model of how a state weighs "
		"competing petitions.")
GROUP_BAN_PULL = declare(
	"GROUP_BAN_PULL", 0.25, kind="temporary_heuristic",
	unit="pull times state capacity (dimensionless)", source=None, confidence="D",
	why="The attention a group must command, as the state can act on it, before the state "
		"will forbid a technique outright rather than only compensate. Stands in for a model "
		"of what a prohibition costs the state in enforcement and in forgone gains.")
SCANDAL_PER_PETITION = declare(
	"SCANDAL_PER_PETITION", 3.0, kind="temporary_heuristic",
	unit="scandal points a year at full pull and full state capacity", source=None,
	confidence="D",
	why="Public blame a group's petitions put on the founder, on the same scale as the alarm "
		"points a technology raises when it is finished.")
GROUP_LOG_INTERVAL_YEARS = declare(
	"GROUP_LOG_INTERVAL_YEARS", 10, kind="temporary_heuristic",
	unit="years", source=None, confidence="D",
	why="Years between repeated log lines about the same group, so a standing grievance is "
		"reported without filling the log.")
