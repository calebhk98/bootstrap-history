"""One-line forwarders from `Sim` to the resources module, for callers not yet in a module.

Each goes when its last caller reads the view (`sim.view(name)`) or sends the command (`sim.send(command)`) itself.
`_running_kept` is engine infrastructure the materials topic still calls; it keeps tables that hold while what is built,
granted and operating does not change, and goes with materials."""
from sim.resources.api import DrawDeposit, MothballMines, base_mine_catalog_hint


class ForwardResourcesMixin:

    @property
    def mine_capacity(self):
        """Rated capacity of the acting seat's workings, summed by material."""
        return self.view("mine_capacity")()

    @property
    def MINE_OPEX_MATERIALS(self):
        """Materials whose mine running cost comes from the deposits' physical works, from the map's catalogue."""
        return self.view("mine_works_materials")()

    @staticmethod
    def base_mine_catalog_hint():
        """The mine catalogue hint on the base map, for help text written before any game exists."""
        return base_mine_catalog_hint()

    def mine_operating_cost(self):
        return self.view("mine_operating_cost")()

    def mine_operating_cost_for(self, working):
        return self.view("mine_working_cost")(working)

    def _workings_of(self, material):
        return [working for working in self.view("mine_workings")() if working.get("material") == material]

    def mothball_mines(self):
        self.send(MothballMines())

    def found_deposits(self, material):
        return self.view("found_deposits")[material]

    def partner_deposits(self, material, tile_ids):
        return self.view("partner_deposits")(material, tile_ids)

    def draw_deposit(self, deposit_id, tonnes):
        return self.send(DrawDeposit(deposit_id, tonnes))

    def mine_depletion_factor(self, material):
        return self.view("mine_depletion")[material]

    def shortage_remedy(self, binding, shortfall_t=None):
        """One sentence on what would end this shortage, in things you can type."""
        return self.shortage_remedy_plan(binding, shortfall_t)["text"]

    def shortage_remedy_plan(self, binding, shortfall_t=None):
        return self.view("shortage_remedy_plan")(binding, shortfall_t)

    def _running_kept_stamp(self):
        """(the projects record, counts and versions of what is built, granted and operating, the tree)."""
        projects = self.state.projects
        return (projects, (self.household.done_version, self.household.operating_version,
                           len(projects.done), len(projects.granted), len(projects.operating)), self.nodes)

    def _running_kept(self, name):
        """A dict for derived values that depend only on which nodes are built, granted and operating (what `running`
        reads); it starts empty whenever that changes."""
        projects, stamp, nodes = self._running_kept_stamp()
        kept = self.__dict__.get("_running_kept_tables")
        if kept is None or kept[0] is not projects or kept[1] != stamp or kept[2] is not nodes:
            kept = self.__dict__["_running_kept_tables"] = (projects, stamp, nodes, {})
        return kept[3].setdefault(name, {})
