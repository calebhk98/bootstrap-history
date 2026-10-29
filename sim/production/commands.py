"""Commands to the owner of what runs and the experience it builds."""
from dataclasses import dataclass

from sim.assembly.api import Command


@dataclass(frozen=True)
class AccrueExperience(Command):
	"""Fade every trade's tenure, then add this year's worker-years of running each technique to the industry's experience."""


@dataclass(frozen=True)
class LearnFromFailure(Command):
	"""A diagnosed failure at `node_id`: the worker-years its attempt spent stay in the industry's experience."""
	node_id: str


@dataclass(frozen=True)
class RefreshDoneCaches(Command):
	"""What the acting seat holds has changed, so every figure derived from it (revenue, upkeep, capability, material demand)
	is stale."""


@dataclass(frozen=True)
class RefreshOperatingCaches(Command):
	"""What the acting seat has open has changed, so the capability factor and every figure keyed on what is operating is stale."""


@dataclass(frozen=True)
class ForgetRevenueCaches(Command):
	"""Drop every seat's memos over what is done and operating (a load and a seat switch need them rebuilt)."""


@dataclass(frozen=True)
class BumpHouseholdVersion(Command):
	"""Count one change of what the acting seat's household has done (`done`) or has open (`operating`), for the caches keyed on it."""
	counter: str
