"""One-line forwarders from `Sim` to the campaigns module, for callers not yet in a module (the army screens).

Each goes when its last caller reads the view (`sim.view(name)`) or sends the command (`sim.send(command)`) itself."""
from sim.campaigns.api import DisbandArmy, OrderArmy, RaiseArmy, RecallArmy


class ForwardCampaignsMixin:

    def raise_army(self, owner, soldiers, tile=None):
        return self.send(RaiseArmy(owner, soldiers, tile))

    def order_army(self, owner, army_id, tile):
        return self.send(OrderArmy(owner, army_id, tile))

    def recall_army(self, owner, army_id):
        return self.send(RecallArmy(owner, army_id))

    def disband_army(self, owner, army_id):
        return self.send(DisbandArmy(owner, army_id))

    def armies_of(self, owner):
        return self.view("armies")[owner]["armies"]

    def free_soldiers(self, owner):
        return self.view("armies")[owner]["free_soldiers"]
