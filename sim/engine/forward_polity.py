"""One-line forwarders from the old `Sim` names of polity to the polity module, for callers not yet in a module.

The screens, the agents' world, the project completion and the mods still say `sim.state_reach()` or `sim.reputation`; each line
goes when its last caller reads the view or sends the command itself."""
from sim.polity.api import (CarryOutTransfers, SetValueWeights, SettleWithState, WithdrawFromPublicLife, constants)
from . import money_units


class PolityForwardsMixin:

    # numbers other topics' code, the screens and the tests still read off the game (sim/polity/constants.py declares them)
    vars().update({name: value for name, value in vars(constants).items() if name.isupper()})

    @property
    def value_weights(self):
        return self.view("value_weights")()

    def open_value_weights(self):
        """The society starts with its civilisation's value weights."""
        self.send(SetValueWeights(tuple(self.civ["values"].items())))
    STATE_FUNDING_BASE = money_units.PricedInLabourHours("STATE_FUNDING_BASE_LABOUR_HOURS")
    # ---- the seat's figures ----

    @property
    def reputation(self):
        return self.view("standing")()["reputation"]

    @property
    def scandal(self):
        return self.view("standing")()["scandal"]

    @property
    def scandal_last_year(self):
        return self.view("standing")()["scandal_last_year"]

    @property
    def protection(self):
        return self.view("standing")()["protection"]

    @property
    def eminence(self):
        return self.view("eminence")()

    @property
    def familiarity(self):
        return self.view("standing")()["familiarity"]

    def standing_floor(self):
        return self.view("standing_floor")()

    def rep_factor(self):
        return self.view("rep_factor")()

    # ---- what the state notices and asks ----

    def state_trait_weights(self):
        return self.view("state_trait_weights")()

    def state_interest(self, node_record):
        return self.view("state_interest")(node_record)

    def alarm_of(self, node_record):
        return self.view("alarm_of")(node_record)

    def military_leverage(self):
        return self.view("military_leverage")()

    def military_equipment_burden_kg_per_soldier_per_year(self, adoption=None):
        return self.view("military_equipment_burden")(adoption)

    def eminence_report(self):
        return self.view("eminence_report")()

    def household_scale(self):
        return self.view("household_scale")()

    def visible_scale(self, headcount, wealth, eminence, defiance=0.0):
        return self.view("visible_scale")(headcount, wealth, eminence, defiance)

    def state_notice(self):
        return self.view("state_notice")()

    def notice_over(self, scale, capacity=None):
        return self.view("notice_over")(scale, capacity)

    def levy_shares(self, scale, protection=0.0, state=None):
        return self.view("levy_shares")(scale, protection, state)

    def confiscation_status(self):
        return self.view("confiscation_status")()

    def state_pressure_report(self):
        return self.view("state_pressure_report")()

    # ---- how far the state reaches ----

    def state_authority(self):
        return self.view("state_authority")()

    def state_reach(self):
        return self.view("state_reach")()

    def order_reach(self):
        return self.view("order_reach")()

    def inspection_reach(self):
        return self.view("inspection_reach")()

    def forest_reach(self):
        return self.view("forest_reach")()

    # ---- the groups, the transfers and the patron's funding ----

    def interest_groups(self):
        return self.view("interest_groups")()

    def interest_groups_report(self):
        return self.view("interest_groups_report")()

    def state_debt(self):
        return self.view("state_debt")()

    def patron_funding_ask(self):
        return self.view("patron_funding_ask")()

    def patron_clients(self, country):
        return self.view("patron_clients")[country]

    def state_funding(self):
        return self.view("state_funding")()

    def settle_with_state(self, target, amount=None):
        return self.send(SettleWithState(target, amount))

    def withdraw_from_public_life(self):
        return self.send(WithdrawFromPublicLife())

    def carry_out_transfers(self, node_id):
        return self.send(CarryOutTransfers(node_id))
