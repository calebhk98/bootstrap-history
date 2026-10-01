"""Telling the player their standing `allocate` orders fell short, once per change."""
import re


class AllocationNotesMixin:

    def unused_hours_is_news(self, key, signature):
        """True the first time this order falls short this way, False while it repeats."""
        reported = self.state.household.unused_hours_reported
        if reported.get(key) == signature:
            return False
        reported[key] = signature
        return True

    def clear_unused_hours_report(self, key):
        self.state.household.unused_hours_reported.pop(key, None)

    def report_unused_directed_hours(self, unused):
        """Log each standing project order that could not use its hours.

        `unused` holds (node_id, hours unused, reason). An order that falls
        short the same way as last year (same order, same reason apart from
        its figures) is not repeated; once it recovers or changes it is
        reported afresh.
        """
        household = self.state.household
        for node_id in [key for key in household.unused_hours_reported
                        if key != "work" and key not in {row[0] for row in unused}]:
            self.clear_unused_hours_report(node_id)
        for node_id, hours, why in sorted(unused):
            directed = household.hour_allocations.get(node_id, 0.0)
            signature = [round(directed), re.sub(r"[\d,]+", "#", why)]
            if not self.unused_hours_is_news(node_id, signature):
                continue
            household.log.append((self.state.scenario.year,
                "DIRECTED HOURS UNUSED: you allocated hours to %s this year that it "
                "could not use - %s of them went begging because %s. 'portfolio' "
                "shows the rest; 'allocate %s %s' lowers the standing order to what "
                "it can use, or 'allocate %s 0' clears it. This is said once until "
                "the order or the reason changes."
                % (self.nodes[node_id]["name"], "{:,.0f}".format(hours), why,
                   node_id, "{:,.0f}".format(max(0.0, directed - hours)), node_id)))
