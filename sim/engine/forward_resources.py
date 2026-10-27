"""One-line forwarders from `Sim` to the resources module, for callers not yet in a module.

Each goes when its last caller reads the view (`sim.view(name)`) or sends the command (`sim.send(command)`) itself.
"""


class ForwardResourcesMixin:

    def _workings_of(self, material):
        return [working for working in self.view("mine_workings")() if working.get("material") == material]
