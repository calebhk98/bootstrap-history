"""One-line forwarders from the old `Sim` methods of project starting to the projects module's views and commands.

Callers outside the module (the screens, fog, the autostart rules, hazards, labour) still say `sim.can_start(node)`;
each line goes when its last caller reads the view or sends the command itself."""
from sim.projects.api import BLOCKER_KINDS, Bribe, PostBounty, StartProject, StopProject, constants


class ProjectsForwardsMixin:

    BLOCKER_KINDS = BLOCKER_KINDS
    # numbers other topics' code still reads off the game (sim/projects/constants.py declares them)
    BOUNTY_PRICE_MULTIPLIER = constants.BOUNTY_PRICE_MULTIPLIER
    PURCHASABLE_SUBSTITUTE_QUALITY_DISCOUNT = constants.PURCHASABLE_SUBSTITUTE_QUALITY_DISCOUNT
    STATE_OPPOSITION_PROTECTION_OVERRIDE = constants.STATE_OPPOSITION_PROTECTION_OVERRIDE

    def start_reason(self, node_id, ignore_trade=False, _memo=None, _why=True):
        return self.view("start_check")(node_id, ignore_trade, _memo, _why)

    def can_start(self, node_id, _memo=None):
        return self.view("start_check")(node_id, False, _memo, False)[0]

    def start_refusal(self, node_id, extra_owed=0.0):
        return self.view("start_refusal")(node_id, extra_owed)

    def start_blockers(self, node_id, extra_owed=0.0):
        return self.view("start_blockers")(node_id, extra_owed)

    def bounty_eligible(self, node_id):
        return self.view("bounty_eligible")(node_id)

    def start_project(self, node_id, precaution=False):
        return self.send(StartProject(node_id, precaution))

    def stop_project(self, node_id):
        return self.send(StopProject(node_id))

    def post_bounty(self, node_id):
        return self.send(PostBounty(node_id))

    def bribe(self, amount):
        return self.send(Bribe(amount))

    def _visible_to_player(self, node_id):
        return self.view("visible_to_player")(node_id)

    @property
    def materials_paid_at_last_start(self):
        return self.view("last_start")()
