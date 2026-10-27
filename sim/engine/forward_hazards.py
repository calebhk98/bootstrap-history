"""One-line forwarders from the old `Sim` names of hazards to the hazards module, for callers not yet in a module.

The screens, the fog, the epidemic step and the state's demands still say `sim.hazard_figure(kind, hazard)` or
`sim.lose_capital(fraction)`; each line goes when its last caller reads the view or sends the command itself."""
from sim.agents.api import ledger
from sim.hazards.api import LoseCapital, capital_lost, constants, rules
from sim.seats.api import EndRun
from sim.workforce.api import SurviveStaff, rules as workforce_rules


class HazardsForwardsMixin:

    # numbers other topics' code and mods still read off the game (sim/hazards/constants.py declares them)
    STAFF_LOSS_HAZARD_ANNUAL_CHANCE = constants.STAFF_LOSS_HAZARD_ANNUAL_CHANCE
    PLAGUE_CASH_LOSS_SHARE = constants.PLAGUE_CASH_LOSS_SHARE
    SACK_TAKE_STRENGTH = constants.SACK_TAKE_STRENGTH
    REAL_EROSION_CASH_LOSS_SHARE = constants.REAL_EROSION_CASH_LOSS_SHARE
    FIRE_ANNUAL_CHANCE = constants.FIRE_ANNUAL_CHANCE
    FIRE_CAPITAL_LOSS = constants.FIRE_CAPITAL_LOSS
    BANDITRY_ANNUAL_CHANCE = constants.BANDITRY_ANNUAL_CHANCE
    BANDITRY_TAKE_STRENGTH = constants.BANDITRY_TAKE_STRENGTH
    HAZARD_EROSION_OWN_GOLD = constants.HAZARD_EROSION_OWN_GOLD
    HAZARD_EROSION_OWN_SILVER = constants.HAZARD_EROSION_OWN_SILVER

    # ---- the figures ----

    def knowledge_risk(self, advice=True, chronology=True):
        return self.view("knowledge_risk")(advice, chronology)

    def hazard_figure(self, kind, hazard, assume_running=()):
        return self.view("hazard_figure")(kind, hazard, assume_running)

    def hazard_relief_entries(self, kind, beyond_national=False, assume_running=()):
        return self.view("hazard_relief_entries")(kind, beyond_national, assume_running)

    def hazard_relief(self, kind, beyond_national=False, assume_running=()):
        return self.view("hazard_relief")(kind, beyond_national, assume_running)

    def hazard_effect_preview(self, node_id):
        return self.view("hazard_effect_preview")(node_id)

    def hazard_advice(self, kind, hazard=None):
        return self.view("hazard_advice")(kind, hazard)

    def hazard_timeline(self, limit=4):
        return self.view("hazard_timeline")(limit)

    def staff_loss_exposure(self, historical, assume_running=()):
        return self.view("staff_loss_exposure")(historical, assume_running)

    def national_public_health_sources(self, limit=3):
        return self.view("national_public_health_sources")(limit)

    def output_floor(self, hazard_factor, relief):
        return rules.output_floor(hazard_factor, relief)

    # ---- the world ----

    @property
    def output_factor(self):
        return self.view("output_factor")()

    @property
    def disaster_this_year(self):
        return self.view("disaster_this_year")()

    def check_yearly_world(self):
        """The yearly invariants, run in every game of more than one country."""
        from . import invariants
        if len(self.view("countries_in_game")()) > 1:
            invariants.check_yearly_invariants(self)

    # ---- what a hazard does to the acting seat ----

    def lose_capital(self, fraction, cause="losses", taker=None):
        if taker is None:
            return self.send(LoseCapital(fraction, cause))
        lost = capital_lost(self.state.household.capital, fraction)   # taken for the state: its treasury is not a named edge
        if lost <= 0.0:
            return 0.0
        ledger.transfer(self.state.household, taker, lost, cause)
        return lost

    def apply_staff_survival(self, survival_share):
        return self.send(SurviveStaff(survival_share))

    def _surviving_people(self, headcount, survival_share):
        return workforce_rules.surviving_people(self.rng, headcount, survival_share)

    def _catastrophe(self, why):
        return self.send(EndRun(why))
