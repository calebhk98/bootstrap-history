"""The resources module's labour_hours_per_tonne answers from its own game's deposits: two modules that read different
metals from their maps, asked for the same material under the same effects, give their own answers (Complaint 730)."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.tests import land_views, resources_stand_in


def module_with_metals(metals):
    catalogue = dict(land_views.of(resources_stand_in.rome(), ("deposit_catalogue",))["deposit_catalogue"]())
    catalogue["metals"] = metals
    return resources_stand_in.build(views={"deposit_catalogue": lambda: catalogue})


with_iron = module_with_metals(("iron",))
without_iron = module_with_metals(())
first = with_iron.labour_hours_per_tonne("iron")
second = without_iron.labour_hours_per_tonne("iron")
check("a map without iron deposits works iron as a generic seam, not as the other game's deposits", second != first, (first, second))
check("asking the first game again gives its own answer", with_iron.labour_hours_per_tonne("iron") == first)

from unittest import mock
from types import SimpleNamespace
from sim.resources.deposit_history import historical_rates
from sim.world import deposits as deposit_model

with mock.patch.object(deposit_model, "load_deposits", lambda resource_id: [SimpleNamespace(name="a", quantity_tonnes_per_year=1.0)]):
    before = historical_rates(("iron",), "iron")
with mock.patch.object(deposit_model, "load_deposits", lambda resource_id: [SimpleNamespace(name="b", quantity_tonnes_per_year=2.0)]):
    after = historical_rates(("iron",), "iron")
check("historical rates follow the deposit data loaded now, not the data first loaded", before == {"a": 1.0} and after == {"b": 2.0}, (before, after))
