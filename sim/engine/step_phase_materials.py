"""The yearly phase that supplies the materials the economy is short of: woodland, mines and nitre beds.

A part of the year's phases (core_step_phases.py); Sim inherits it through StepPhasesMixin. It ran beside the start
of projects in one step; the start is the projects module's phase now (sim/projects/start_phase.py), and this one
belongs to the resources and materials topics."""
from sim.refusal import LogLine
from sim.unit_conversions import KILOGRAMS_PER_TONNE
from . import automation_audit, shortage_conditions
from .shortage_sizing import automatic_policy_on, auto_mine_affordable_tonnes, auto_mine_order_tonnes, nitre_bed_yearly_spend
from sim.agents.api import edges
from sim.constants import declare
from . import money_units
from .units_prose import area_text, mass_rate_text, money_text


class MaterialsPhaseMixin:

    AUTO_FOREST_CAPITAL_LABOUR_HOURS_PER_HA = declare(
        "AUTO_FOREST_CAPITAL_LABOUR_HOURS_PER_HA", 36300.0, kind="temporary_heuristic",
        unit="labour hours of capital held per hectare bought", source=None, confidence="D",
        why="How much capital the optimizer holds for each hectare of charcoal forest its mining "
            "policy buys alongside an ore shortfall, so the forest never takes the whole purse. "
            "Tuned, not measured.")
    AUTO_FOREST_CAPITAL_PER_HA = money_units.PricedInLabourHours("AUTO_FOREST_CAPITAL_LABOUR_HOURS_PER_HA")
    NITRE_BED_SPEND_CEILING_LABOUR_HOURS = declare(
        "NITRE_BED_SPEND_CEILING_LABOUR_HOURS", 40300.0, kind="temporary_heuristic",
        unit="labour hours per year", source=None, confidence="D",
        why="Yearly ceiling on the optimizer's automatic nitre-bed spending, a flat amount of work "
            "rather than a share of the shortfall that beds cannot close. Tuned, not measured.")
    NITRE_BED_SPEND_CEILING = money_units.PricedInLabourHours("NITRE_BED_SPEND_CEILING_LABOUR_HOURS")

    def _step_materials(self):
        # 4c. materials. Buy the woodland and dig the beds BEFORE the shortage
        #     bites, which is what a competent manager does and what the old
        #     model never had to think about at all.
        self.commission_mines()
        thr = self.resource_throttle()
        # THE GATE WAS THE DEADLOCK. `capital > 3000` was meant to stop this
        # spending a poor household's last coin, and instead it made charcoal
        # a wall nobody in arrears could ever climb: no woodland, so the
        # furnaces run at a fraction, so nothing is built, so no money, so
        # still no woodland. An England run measured 521 charcoal-short years
        # out of 700, ended on 31 technologies with 71 hectares of coppice and
        # -6,332 in hand, and settled its debts twenty-eight times.
        #
        # Coppice is the cheapest thing in the tree and the one that decides
        # whether a furnace runs at all, so what it is really gated on is
        # whether you can raise the price of some, which is what
        # spending_power says. Below that the branch does nothing anyway,
        # because buy_forest refuses what you cannot pay for.
        _can_raise = self.spending_power("buy")
        if (thr < 0.9 and _can_raise > self.FOREST_COST_PER_HA * self.price_index
                and (automatic_policy_on(self.state.founder.policy, "auto_mine", self.manual)
                     or self.state.founder.policy.get("auto_forest", not self.manual))):
            # Charcoal is GROWN, so the answer is woodland. Everything else in
            # this list is DUG, so the answer is a mine, and the old model had
            # no answer at all for coal: the binding constraint fell through
            # both branches and the run simply sat throttled. That is why coal
            # showed 1,669 shortage-years in a 395 year run.
            if self.state.holdings.binding == "charcoal":
                if self.state.founder.policy.get("auto_forest", not self.manual):
                    # SIZED FROM THE SHORTFALL, like the mine branch below,
                    # rather than from a flat share of cash. A tenth of a
                    # denarius of capital bought a ten-thousandth of a hectare
                    # while the demand was measured in hundreds of tonnes.
                    _need_t = (self.annual_material_demand().get("charcoal_kg", 0.0)
                               / KILOGRAMS_PER_TONNE) - self.state.holdings.forest_ha * self.CHARCOAL_PER_HA
                    _want_ha = max(0.0, _need_t) / max(self.CHARCOAL_PER_HA, 1e-9)
                    _afford_ha = (_can_raise * 0.35
                                  / (self.FOREST_COST_PER_HA * self.price_index))
                    _before = self.state.household.capital
                    _hectares_before = self.state.holdings.forest_ha
                    self.buy_forest(min(400.0, _want_ha, _afford_ha))
                    if self.state.holdings.forest_ha > _hectares_before:
                        automation_audit.record(
                            self, "auto_forest", "forest",
                            "%s of coppice" % area_text(self.state.holdings.forest_ha - _hectares_before, self),
                            "charcoal demand exceeds what %s yield by %s"
                            % (area_text(_hectares_before, self),
                               mass_rate_text(max(0.0, _need_t), self, short=False)), _before)
            elif (self.state.holdings.binding in self.MINE_OPEX_MATERIALS
                    and automatic_policy_on(self.state.founder.policy, "auto_mine", self.manual)):
                # Size the mine from ALL the material keys that feed this
                # bucket, not one of them. The throttle counted iron ore AND
                # iron bar against "iron"; the investment response looked only
                # at iron bar. A run needing 10,330 tonnes of ore a year sank a
                # mine sized for the 13 tonnes of bar, stayed throttled for
                # centuries, and ended with its capital untouched.
                dem = self.annual_material_demand()
                # DERIVED FROM MATERIAL_CHECKS, not a second hand-kept copy
                # of it: a separately maintained list would silently drift
                # out of sync whenever a material is added to
                # MATERIAL_CHECKS, raising a KeyError the first year that
                # material happens to bind. Two lists of the same thing is
                # one list too many, and the regression suite cannot catch
                # it unless a check runs a long enough optimizer game to
                # make that material bind.
                # sorted(), because this feeds a float sum.
                keys = tuple(sorted(material for material, (bucket, _tag)
                                    in self.MATERIAL_CHECKS.items()
                                    if bucket == self.state.holdings.binding))
                short = sum(dem.get(material, 0.0) for material in keys)
                # Shafts already sinking count, so a tranche about to commission is not ordered twice.
                _before = self.state.household.capital
                _pending = self.state.holdings.mine_pending.get(self.state.holdings.binding, 0.0)
                _ordered = auto_mine_order_tonnes(short, self.mine_capacity.get(self.state.holdings.binding, 0.0), _pending,
                                                  self.state.household.capital, self._mine_capex(self.state.holdings.binding))
                _order = automation_audit.order_id("auto_mine", self.state.holdings.binding, self.state.scenario.year)
                self.auto_prospect(self.state.holdings.binding)
                self.open_mine(self.state.holdings.binding, _ordered, order=_order)
                if _ordered > 0:
                    automation_audit.record(
                        self, "auto_mine", "mine",
                        "%s of %s ordered" % (mass_rate_text(_ordered, self), self.state.holdings.binding),
                        "demand %s > active %s; pending capacity considered %s"
                        % (mass_rate_text(short, self),
                           mass_rate_text(self.mine_capacity.get(self.state.holdings.binding, 0.0), self),
                           mass_rate_text(_pending, self)),
                        _before, order=_order, reason_kind="mine_ordered", demand=short,
                        active_capacity=self.mine_capacity.get(self.state.holdings.binding, 0.0),
                        pending_capacity=_pending, ordered=_ordered)
                else:
                    automation_audit.record_skip(
                        self, "auto_mine", "mine for %s" % self.state.holdings.binding,
                        "nothing ordered: shortfall %s against %s active and %s pending, "
                        "a quarter of capital buys %s"
                        % (mass_rate_text(short, self),
                           mass_rate_text(self.mine_capacity.get(self.state.holdings.binding, 0.0), self),
                           mass_rate_text(_pending, self),
                           mass_rate_text(auto_mine_affordable_tonnes(
                               self.state.household.capital, self._mine_capex(self.state.holdings.binding)), self)))
                # Iron and the base metals are smelted with charcoal, so the
                # ore is only half the answer.
                if self.state.holdings.binding in ("iron", "copper", "lead"):
                    self.buy_forest(min(200.0, self.state.household.capital / self.AUTO_FOREST_CAPITAL_PER_HA))
            elif (self.state.holdings.binding == "saltpetre"
                    and automatic_policy_on(self.state.founder.policy, "auto_mine", self.manual)):
                # GATED, like every other automatic purchase: ungated, this
                # branch would take five per cent of a manual player's
                # capital every year they were short of nitre, without a
                # line in the log and without anything they typed.
                # A FLAT CEILING, AND IT IS NOT AN OVERSIGHT: sizing this to
                # the measured shortfall, the way the mine branch above does,
                # spends a quarter of capital a year against a shortfall
                # nitre beds cannot close at any affordable scale, which
                # starves everything else and, once the household falls into
                # arrears, pins it there with interest. A fixed yearly amount
                # of work is what leaves the rest of the programme funded.
                #
                # The shortage is real and unresolved; more money is not the
                # answer to it.
                spend = nitre_bed_yearly_spend(self.state.household.capital, self.NITRE_BED_SPEND_CEILING)
                self.pay_edge(edges.EDGE_BUILDERS, spend, "nitre beds laid down")
                self.state.holdings.nitre_bed_m2 += spend / self.NITRE_COST_PER_M2
                automation_audit.record(
                    self, "auto_mine", "nitre", "%s of nitre bed" % area_text(spend / self.NITRE_COST_PER_M2, self, unit="square_metre"),
                    "saltpetre is the binding shortage; the yearly spend is capped, not sized to the gap",
                    self.state.household.capital + spend)
                self.state.household.log.append((self.state.scenario.year, LogLine("nitre_bed_laid", "laid down %s of nitre bed "
                                     "for %s (auto_mine)"
                                 % (area_text(spend / self.NITRE_COST_PER_M2, self, unit="square_metre"),
                                    money_text(spend, self)))))
        slowed = shortage_conditions.slowed_projects(self) if thr < 0.6 and self.state.holdings.binding else []
        if slowed:
            # SAY WHAT TO DO ABOUT IT: a bare "SHORT OF SALTPETRE: work at
            # 5% of plan" with no remedy attached reads as the game being
            # stuck rather than as something actionable.
            # One standing condition; the full message only when it is new or has moved materially.
            # Only said while a running project draws the material: a shortage nothing running needs slows nothing.
            if shortage_conditions.note_shortage(self, self.state.holdings.binding, thr):
                names = ", ".join(self.nodes[node_id]["name"] for node_id in slowed[:3])
                self.state.household.log.append((self.state.scenario.year, LogLine("material_shortage", "SHORT OF %s: %s running at %d%% of plan. %s"
                                 % (shortage_conditions.material_words(self.state.holdings.binding).upper(), names,
                                    thr * 100, self.shortage_remedy(self.state.holdings.binding)))))
        else:
            shortage_conditions.clear_shortage(self)
