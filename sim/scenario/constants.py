"""The declared numbers of the scenario module."""
from sim.constants import declare

FOUNDER_MIN_REMAINING_LIFE_YEARS = declare(
    "FOUNDER_MIN_REMAINING_LIFE_YEARS", 5, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="Floor on the founder's gaussian-drawn remaining lifespan, so "
        "an unlucky draw does not end a run in its first years before "
        "anything is possible. Round guard value, not a mortality "
        "estimate.")

MAX_ACTIVE_PROJECTS_BASE = declare(
    "MAX_ACTIVE_PROJECTS_BASE", 2, kind="temporary_heuristic",
    unit="projects", source=None, confidence="D",
    why="Minimum number of projects a household can hold active at "
        "once, before scholars/artisans/director hours add more. "
        "Round number, not measured.")
MAX_ACTIVE_PROJECTS_PER_DIRECTOR_HOURS = declare(
    "MAX_ACTIVE_PROJECTS_PER_DIRECTOR_HOURS", 2000.0, kind="temporary_heuristic",
    unit="founder-hours per extra active project", source=None,
    confidence="D",
    why="How many director-hours of capacity buy one more active "
        "project slot - see the comment above: doubling this whole "
        "formula was measured to make every civilisation worse (Rome "
        "fell from 33% of runs reaching the transistor to none), "
        "because more projects in hand divide the same purse into "
        "smaller annual payments. Kept at the value that measured "
        "better, not derived from a model of attention or budgeting.")
MAX_ACTIVE_PROJECTS_PER_SCHOLAR = declare(
    "MAX_ACTIVE_PROJECTS_PER_SCHOLAR", 12.0, kind="temporary_heuristic",
    unit="scholars per extra active project", source=None,
    confidence="D",
    why="How many scholars buy one more active project slot. Tuned "
        "alongside MAX_ACTIVE_PROJECTS_PER_DIRECTOR_HOURS and "
        "MAX_ACTIVE_PROJECTS_PER_ARTISAN as one measured formula; not "
        "independently derived.")
MAX_ACTIVE_PROJECTS_PER_ARTISAN = declare(
    "MAX_ACTIVE_PROJECTS_PER_ARTISAN", 25.0, kind="temporary_heuristic",
    unit="artisans per extra active project", source=None,
    confidence="D",
    why="How many artisans buy one more active project slot - see "
        "MAX_ACTIVE_PROJECTS_PER_DIRECTOR_HOURS's own comment for the "
        "measurement this whole formula was tuned and then held "
        "against.")
