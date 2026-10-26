"""Forwarders from the old `Sim` names of the log to the reporting module.

The screens and the step code still say `sim.log`; the line goes when its last reader asks the `event_log` view."""


class ReportingForwardsMixin:

    @property
    def log(self):
        """The acting seat's log: (year, line) pairs in the order they happened."""
        return self.view("event_log")()
