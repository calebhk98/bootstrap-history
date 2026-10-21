"""Complaint 315: a state's revenue is what its declared forms yield on the bases the simulation models
(harvest, people, trade, coin held), not a fitted share of labour value. Complaint 640: the forms are assessed over a
stand-in world that answers the bases from numbers built here; the year of a state taking grain in kind is
test_state_revenue_forms_scenario."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check, S

from sim.agents import revenue, revenue_labour
from sim.agents.api import Government
from sim.agents.records import ActorRecord
from sim.engine.agents_port_revenue import RevenueView

from .agents_fake_world import FakeWorld

HARVEST_TONNES = 4.0e6
WHEAT_PRICE = 12.0
LABOUR_YEAR = 900.0
WORKING_AGE = 2.0e6
SOLDIERS = 5.0e4
COIN_VALUE = 3.0e8
IMPORTS, EXPORTS = 6.0e9, 2.0e9

LAND = {"form": "land_tax", "basis": "harvest", "rate": 0.1, "paid_in": "wheat_kg"}
POLL = {"form": "poll_tax", "basis": "adult_labour_years", "rate": 0.02}
IMPORT_DUTY = {"form": "import_duty", "basis": "imports_value", "rate": 0.025}
EXPORT_DUTY = {"form": "export_duty", "basis": "exports_value", "rate": 0.05}
WEALTH = {"form": "wealth_tax", "basis": "coin_stock", "rate": 0.01}


class BasesWorld(FakeWorld):
    """A country that answers each base from a number."""

    def __init__(self, forms):
        super().__init__()
        self.forms = forms
        self.harvest = HARVEST_TONNES
        self.trade = {"in": IMPORTS, "out": EXPORTS}

    def revenue_forms(self):
        return self.forms

    def harvest_tonnes(self):
        return self.harvest

    def material_price(self, material):
        return WHEAT_PRICE

    def national_people(self, trade):
        return WORKING_AGE

    def soldiers_under_arms(self):
        return SOLDIERS

    def pay_per_person_year(self, trade):
        return LABOUR_YEAR

    def trade_value(self, direction):
        return self.trade[direction]

    def coin_stock_value(self):
        return COIN_VALUE

    def revenue_assessments(self):
        return revenue.assess(self)


class StateView(RevenueView):
    """The revenue questions over a stand-in game: its declared forms, its government and the bases of BasesWorld."""

    def __init__(self, civ, forms_world):
        self._sim = SimpleNamespace(civ=civ)
        self._forms_world = forms_world
        self._government = Government("government:home", ActorRecord(kind="government"))

    def government(self):
        return self._government

    def _once(self, key, compute):
        return compute()

    def revenue_assessments(self):
        return revenue.assess(self._forms_world)


# ---- every civilisation declares its forms, each with a rate, a basis and a source ----------------
for civ_id in ("rome_100ad", "han_china_100ad", "norse_900ad", "mexica_1500", "england_1300"):
    forms = S.load_civ(civ_id).get("state_revenue")
    check("%s declares the forms its state raises revenue by" % civ_id, bool(forms), forms)
    check("%s's forms each name a basis the engine models, a rate and where the rate comes from" % civ_id,
          all((form["basis"] in revenue.BASES or form["basis"] == revenue_labour.BASIS) and form["rate"] > 0.0 and form.get("_internal", {}).get("source")
              for form in forms or []), forms)

# ---- revenue is the sum of the forms assessed on their bases --------------------------------------
world = BasesWorld([LAND, POLL, IMPORT_DUTY, EXPORT_DUTY, WEALTH])
expected = {
    "land_tax": 0.1 * HARVEST_TONNES * WHEAT_PRICE,
    "poll_tax": 0.02 * (WORKING_AGE - SOLDIERS) * LABOUR_YEAR,
    "import_duty": 0.025 * IMPORTS,
    "export_duty": 0.05 * EXPORTS,
    "wealth_tax": 0.01 * COIN_VALUE,
}
by_form = {assessed.form: assessed for assessed in revenue.assess(world)}
check("each declared form is assessed once", sorted(by_form) == sorted(expected), sorted(by_form))
for form, money in expected.items():
    check("%s is its rate times the modelled base" % form, abs(by_form[form].money - money) < 1e-6 * money, (form, by_form[form].money, money))
view = StateView({"state_revenue": [LAND, POLL, IMPORT_DUTY, EXPORT_DUTY, WEALTH]}, world)
check("the state's revenue is the sum of the forms",
      abs(view.state_revenue() - sum(expected.values())) < 1e-6 * sum(expected.values()), (view.state_revenue(), sum(expected.values())))

# ---- nothing declared, nothing raised; the old fitted share no longer sets it ----------------------
check("a state that declares no form raises no revenue", StateView({"state_revenue": []}, BasesWorld([])).state_revenue() == 0.0)
check("a state whose file has no revenue section raises none", StateView({}, BasesWorld([])).state_revenue() == 0.0)
plain = StateView({"state_revenue": [POLL]}, BasesWorld([POLL]))
fitted = StateView({"state_revenue": [POLL], "starting_tax_share": 0.9}, BasesWorld([POLL]))
check("the civilisation's fitted tax share does not set the state's revenue",
      abs(fitted.state_revenue() - plain.state_revenue()) < 1e-9 * plain.state_revenue(), (fitted.state_revenue(), plain.state_revenue()))
check("the forms the view reads are the civilisation's declared ones", fitted.revenue_forms() == [POLL], fitted.revenue_forms())

bigger, smaller = BasesWorld([LAND]), BasesWorld([LAND])
bigger.harvest = 2.0 * HARVEST_TONNES
check("a larger harvest yields a larger land tax",
      StateView({}, bigger).state_revenue() > 1.9 * StateView({}, smaller).state_revenue())
quiet = BasesWorld([IMPORT_DUTY, EXPORT_DUTY])
quiet.trade = {"in": 0.0, "out": 0.0}
check("trade duties follow the trade that crossed the border",
      StateView({}, quiet).state_revenue() == 0.0 < StateView({}, BasesWorld([IMPORT_DUTY, EXPORT_DUTY])).state_revenue())

# ---- a lever on a rate (595) moves the form's yield -------------------------------------------------
levered = StateView({"state_revenue": [POLL]}, BasesWorld([POLL]))
levered.government().record.levers["revenue"] = {"poll_tax": {"rate": 0.04}}
forms = levered.revenue_forms()
check("the government's lever sets the rate of a declared form", [form["rate"] for form in forms] == [0.04], forms)

# ---- the revenue by form is recorded, for the audit -------------------------------------------------
state = Government("government:home", ActorRecord(kind="government"))
state.receive_revenue(world)
check("the revenue by form is recorded in money's worth, for the audit",
      all(abs(state.record.revenue_by_form[form] - money) < 1e-6 * money for form, money in expected.items()), state.record.revenue_by_form)
check("a form paid in kind is booked as goods, not as coin taxation",
      abs(state.record.in_kind_received["wheat_kg"] - 0.1 * HARVEST_TONNES) < 1e-6 and
      abs(state.record.income.get("taxation", 0.0) - (sum(expected.values()) - expected["land_tax"])) < 1e-3 * sum(expected.values()),
      (state.record.in_kind_received, state.record.income))
