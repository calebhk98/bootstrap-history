"""The seat's log and the automation audit trail: what is recorded, and what a reader may ask for."""
from typing import Any, Dict, List

from . import rules

LOG = "log"
AUDIT = "audit"


class Logging:
    """Needs: year, acting_balance."""

    def slot_of(self, seat_id: Any) -> Any:
        """The state of `seat_id`, or of the acting seat when none is named."""
        return self.seat if seat_id is None or seat_id == self.clock.acting_seat else self.seat_of(seat_id)

    def record_event(self, command: Any) -> None:
        self.slot_of(command.seat).log.append(rules.log_entry(
            self.needs.year() if command.year is None else command.year, command.kind, command.text, command.facts))
        self.bump_seat(LOG, command.seat)

    def discard_events_after(self, command: Any) -> None:
        del self.seat.log[command.kept:]
        self.bump_seat(LOG)

    def event_log(self) -> List[Any]:
        """The acting seat's log: (year, line) pairs in the order they happened."""
        return self.seat.log

    def record_automation(self, command: Any) -> Dict[str, Any]:
        row = rules.audit_row(self.needs.year(), command.policy, command.action, command.what, command.reason,
                              command.capital_before, self.needs.acting_balance(), command.facts)
        self.seat.automation_audit.append(row)
        self.bump_seat(AUDIT)
        return row

    def record_automation_skip(self, command: Any) -> Dict[str, Any]:
        capital = self.needs.acting_balance()
        row = rules.audit_row(self.needs.year(), command.policy, "skipped", command.what, command.reason, capital,
                              capital, command.facts)
        self.seat.automation_audit.append(row)
        self.bump_seat(AUDIT)
        return row

    def trim_audit(self, seat_id: Any = None) -> None:
        """Drop the rows older than the years kept, at the start of a seat's year."""
        self.seat.automation_audit = rules.kept_rows(self.seat.automation_audit, self.needs.year())
        self.bump_seat(AUDIT)

    def automation_rows(self, years: Any = 1) -> List[Dict[str, Any]]:
        """The rows from the latest `years` years that were played, oldest first."""
        return rules.recent_rows(self.seat.automation_audit, self.needs.year(), years)
