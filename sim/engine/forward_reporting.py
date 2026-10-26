"""Forwarders from the old `Sim` names of the log and the indicators to the reporting module.

The screens, the step code and the other mixins still say `sim.log` or `self.real_output_per_head()`; each line goes
when its last reader asks the view itself."""


class ReportingForwardsMixin:

    @property
    def log(self):
        """The acting seat's log: (year, line) pairs in the order they happened."""
        return self.view("event_log")()

    @property
    def money_real(self):
        """What one coin buys over what it bought at the start; falls as the coin is debased."""
        return self.view("money_real")()

    def real_output_per_head(self):
        return self.view("real_output_per_head")()

    def real_output_hours(self, measure=None):
        return self.view("real_output_hours")(measure)

    def last_market_price_ratio(self, material):
        return self.view("last_market_price_ratio")[material]
