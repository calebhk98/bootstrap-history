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
STRATUM_WELFARE_MEMORY_RATE = declare(
	"STRATUM_WELFARE_MEMORY_RATE", 0.2, kind="temporary_heuristic",
	unit="share of the gap closed per year", source=None, confidence="D",
	why="How fast a body of people comes to expect the welfare it now has, so that a fall in "
		"income is a grievance only until it becomes the new normal. Stands in for a model of "
		"reference points in what people feel they are owed.")
REACH_REFINEMENT_DEPTH = declare(
	"REACH_REFINEMENT_DEPTH", 8, kind="temporary_heuristic",
	unit="steps of prerequisite", source=None, confidence="D",
	why="How many prerequisite steps back a technique is still taken to refine the line of a "
		"technique that makes a commodity, for the reach of a prohibition. Stands in for a "
		"model of which techniques a state can tell apart.")
STRATUM_GRIEVANCE_THRESHOLD = declare(
	"STRATUM_GRIEVANCE_THRESHOLD", 0.05, kind="temporary_heuristic",
	unit="share of expected welfare", source=None, confidence="D",
	why="How far below what it has come to expect a body of people's welfare must fall before "
		"it counts as a grievance rather than the year's ordinary swing in income.")
GROUP_CLAIM_CEILING_SHARE = declare(
	"GROUP_CLAIM_CEILING_SHARE", 0.25, kind="temporary_heuristic",
	unit="share of the territory's revenue", source=None, confidence="D",
	why="The most a state undertakes to make good to one group in a year, as a share of its "
		"revenue from the group's territory, however large the loss. Stands in for a model of "
		"what a state can raise and what it must keep for its other charges.")
