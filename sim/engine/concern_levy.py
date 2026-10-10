"""A state's share of what one kind of concern earns: licensed gambling, a state lottery, a salt farm.

A node declares `mechanics.state_levy = {"share": s}`; while it is open, the state is paid `s` of its revenue each
year, on top of what the state takes from the household's income as a whole.
"""
from .units_prose import money_text


class ConcernLevyMixin:

    def concern_levy_due(self):
        """{node id: sum the state takes from it this year} for the open concerns that declare `state_levy`."""
        due = {}
        operating = self.state.projects.operating
        for node_id in self.running_with_mechanic("state_levy"):
            if node_id not in operating:
                continue   # a trade the society already has is not the household's concern to levy
            share = self.mechanic(node_id, "state_levy")["share"]
            takings = self.concern_revenue(node_id) * self.state.economy.output_factor
            if share > 0.0 and takings > 0.0:
                due[node_id] = share * takings
        return due

    def pay_concern_levies(self, year):
        """Pay the state its share of each levied concern's takings; the household's loss is the treasury's gain.
        The log says so the first year only."""
        said = self.state.scenario._said_condition
        for node_id, owed in sorted(self.concern_levy_due().items()):
            self.pay_state(owed, "levy on " + node_id)
            if "levy:" + node_id not in said:
                said.add("levy:" + node_id)
                self.state.household.log.append((year, "the state takes its share of %s: %s this year, and so on each year it is open"
                                                 % (self.nodes[node_id]["name"], money_text(owed, self, grouped=True))))
