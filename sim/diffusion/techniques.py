"""Which techniques a concern can copy from the producers that run them, and when it first saw them run.

Needs: techniques_in_use, techniques_granted, tree, year. A reader sends `NoteFirstRuns` with the techniques in use
before it asks for `techniques_spread`, so a technique is stamped with the year it was first seen."""
from typing import Any, FrozenSet

from . import technique_spread


class Techniques:

    def note_first_runs(self, command: Any) -> None:
        """Stamp each technique in use that has no first-run year yet. The opening's techniques were copied before the
        game began and are stamped long before."""
        in_use, year, world = command.in_use, self.needs.year(), self.world
        noted = self._noted
        if noted is not None and noted[0] is in_use and noted[1] == year and world.technique_record_started:
            return    # the same techniques seen in the same year: nothing new to note
        technique_spread.note_first_run(world.technique_first_run, in_use, year, not world.technique_record_started)
        world.technique_record_started = True
        self._noted = (in_use, year)

    def techniques_spread(self) -> FrozenSet[str]:
        """The techniques in use that concerns in the same line of business have had time to copy."""
        in_use = self.needs.techniques_in_use()
        year = self.needs.year()
        first_run = self.world.technique_first_run
        granted = frozenset(self.needs.techniques_granted())
        stamp = (year, granted, len(first_run), self.world.technique_record_started)
        cached = self._spread
        if cached is not None and cached[0] is in_use and cached[1] is first_run and cached[2] == stamp:
            return cached[3]
        tree = self.needs.tree
        spread = technique_spread.spread_techniques(in_use, granted, first_run, lambda node_id: tree[node_id], year)
        self._spread = (in_use, first_run, stamp, spread)
        return spread
