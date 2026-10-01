"""What the staffing rule did this year, in one place the player can read."""


class StaffingReportMixin:

    STAFFING_REMEDIES = (
        "To hold staff: 'keep <id> staffed' hires for that concern each year; "
        "'reserve craftsmen <n>' and 'reserve scholars <n>' with 'policy "
        "reserve_staff on' keep spare hands; 'policy auto_replace_foreman on' "
        "rehires a lost specialist foreman")

    def _staffing_tally(self):
        """This year's closed and reopened counts, started afresh each year."""
        projects = self.state.projects
        year = self.state.scenario.year
        if projects.staffing_tally.get("year") != year:
            projects.staffing_tally = {"year": year, "closed": 0, "reopened": 0, "short": {}}
        return projects.staffing_tally

    def record_staffing_closures(self, count, shortfalls):
        tally = self._staffing_tally()
        tally["closed"] += count
        for resource, amount in shortfalls.items():
            tally["short"][resource] = max(tally["short"].get(resource, 0.0), round(amount, 2))

    def record_staffing_reopenings(self, count):
        self._staffing_tally()["reopened"] += count

    def staffing_shut_count(self):
        """Concerns shut for want of staff right now."""
        return sum(1 for node_id in self.state.projects.closures
                   if self.staff_closure_age(node_id) is not None)

    @staticmethod
    def staffing_shortfall_words(shortfalls):
        """Cause text such as 'craftsmen (short 2.1 full-time)'."""
        return ", ".join("%s (short %.1f full-time)" % (resource, amount)
                         for resource, amount in sorted(shortfalls.items()))

    def staffing_closure_summary(self):
        """One line: closed, reopened and still shut this year, the cause and the remedies.

        None while nothing is shut for staff and nothing closed or reopened
        this year.
        """
        tally = self._staffing_tally()
        still_shut = self.staffing_shut_count()
        if not (tally["closed"] or tally["reopened"] or still_shut):
            return None
        cause = (" Cause: short of %s." % self.staffing_shortfall_words(tally["short"])
                 if tally["short"] else "")
        return ("Staffing this year: closed %d, reopened %d, still shut %d (net %d).%s %s"
                % (tally["closed"], tally["reopened"], still_shut,
                   tally["closed"] - tally["reopened"], cause, self.STAFFING_REMEDIES))
