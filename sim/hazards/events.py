"""The world event log and the world's output factor: the state hazards owns, its commands and the views of it.

The log is dated records of what changed in the world and why, shared by every seat, saved with the game, keeping the last
`event_log_years_kept` years (data/world/world_hazards.json). A record is {year, kind, actors, tiles, cause, facts}.

Needs: year, military_leverage."""
from typing import Any, Dict, List, Optional

from . import constants, rules, world_data
from .commands import RecordWorldEvent, RecoverOutput
from .state import OUTPUT, WORLD_EVENTS
from .window import kinds_in_progress


class Events:

	def record_world_event(self, command: RecordWorldEvent) -> Dict[str, Any]:
		"""Append one record dated to the game's current year; answers it."""
		entry = rules.world_event_entry(self.needs.year(), command.kind, command.actors, command.tiles, command.cause, command.facts)
		kept = self.world.world_events
		kept.append(entry)
		rules.trim_world_events(kept, world_data.years_kept())
		self.bump(WORLD_EVENTS)
		return entry

	def world_events(self, kind: Optional[str] = None, since_year: Optional[int] = None, actor: Optional[str] = None) -> List[Dict[str, Any]]:
		"""The records, oldest first, optionally of one kind, from a year on, or involving one actor."""
		return rules.world_event_rows(self.world.world_events, kind, since_year, actor)

	def output_factor(self) -> float:
		"""Share of its normal real output the economy keeps: war and plague crush it, a recovering state restores it."""
		return self.world.output_factor

	def recover_output(self, command: RecoverOutput) -> None:
		"""The year's recovery toward 1.0: the base rate, doubled at full military leverage."""
		if self.world.output_factor < 1.0:
			self.world.output_factor = rules.recovered_output_factor(
				self.world.output_factor, constants.OUTPUT_RECOVERY_RATE, self.needs.military_leverage())
			self.bump(OUTPUT)

	def live_hazard_kinds(self, year_now: int) -> set:
		"""The kinds of hazard in progress in `year_now`."""
		return kinds_in_progress(self.needs.civilisation(), year_now)

	def disaster(self) -> Optional[Dict[str, Any]]:
		"""This year's dated hazards by name, and what the acting seat's log said of them; None when none struck."""
		return self.disaster_this_year
