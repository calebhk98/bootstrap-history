"""The yearly phases that start projects and supply their materials.

A part of the year's phases (core_step_phases.py); Sim inherits it through StepPhasesMixin."""
from sim.unit_conversions import KILOGRAMS_PER_TONNE
from . import automation_audit, shortage_conditions
from sim.agents.api import edges
from sim.constants import declare
from . import money_units
from .units_prose import area_text, mass_rate_text, money_text


class ProjectStartPhaseMixin:

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

    def _step_start_projects(self):
        # 4b. start new projects
        pool = max(0.0, self.labour.director_pool() - self.labour.director_hours_committed())
        hired_left = self.labour.hired_cap()
        # MANUAL MODE STOPS HERE. This loop is "the optimizer": it walks
        # `order` and starts whatever it judges best, which is exactly the
        # behaviour a free-choice player must NOT get. The old `play` command
        # let you type a node id, but that only did `order.remove/insert(0)`
        # a few lines above this loop's own input; the loop then ran anyway
        # and started other things you never asked for. `self.manual` cuts
        # that off at the root: nothing is ever added to `self.state.projects.active` here,
        # so the only way anything starts is start_project(), called by a
        # human or a script. Everything below this block (materials, staff,
        # money, hazards, the calendar) is untouched by `manual` and keeps
        # running exactly as before.
        if not self.manual and self.state.scenario.year >= self.state.household.credit_frozen_until:
            # More directors means more things in hand at once, and a big trained staff
            # lets routine work proceed without the founder watching it.
            # How many things can be in hand at once: doubling this would let
            # more projects divide the same purse into smaller annual
            # payments, so everything crawls and nothing finishes. Spreading
            # a fixed budget across more work is not more work.
            max_active = int(self.MAX_ACTIVE_PROJECTS_BASE
                             + self.labour.director_pool() / self.MAX_ACTIVE_PROJECTS_PER_DIRECTOR_HOURS
                             + self.state.household.scholars / self.MAX_ACTIVE_PROJECTS_PER_SCHOLAR
                             + self.state.household.artisans / self.MAX_ACTIVE_PROJECTS_PER_ARTISAN)
            # EARN A LIVING FIRST: now that a project must actually be paid
            # for, a founder who arrives with 400 denarii and walks the
            # goal-ordered list starves, so when the surplus is thin, the
            # optimizer has to prefer whatever pays best for what it costs
            # the same way a human player hunting for cheap revenue nodes
            # would; the goal order resumes the moment there is money to
            # pursue it with.
            _upkeep0 = self.upkeep()
            _rev0 = self.revenue()
            fixed0 = _upkeep0 + self.living_cost(_rev=_rev0, _upkeep=_upkeep0) + self.mine_operating_cost()
            candidates = self.order
            if _rev0 - fixed0 < max(400.0, fixed0 * 0.25):
                earners = [node_id for node_id in self.order
                           if self.nodes[node_id]["rev"] - self.nodes[node_id]["up"] > 0]
                earners.sort(key=lambda k: self.project_cost(k)
                             / max(1.0, self.nodes[k]["rev"] - self.nodes[k]["up"]))
                # `set(earners)` HOISTED OUT OF THE COMPREHENSION. Written
                # inline as `if k not in set(earners)`, this rebuilt the set
                # from scratch on every one of the 2,833 iterations of the
                # walk over self.order - one throwaway set per node, an
                # O(|order| x |earners|) rebuild for what a single set
                # covers in O(|order|). Profiling a 300-year single-seed run
                # found this one line costing 0.81s of self time over just
                # 21 calls - a tight-money branch, but each call did the
                # equivalent of an extra multi-hundred-thousand-item pass.
                # See PERFORMANCE.md.
                _earner_set = set(earners)
                candidates = earners + [node_id for node_id in self.order if node_id not in _earner_set]
            # INCREMENTAL COUNT, NOT A SET REBUILT PER ITERATION. Written as
            # `len(self.state.projects.active) - len(self.state.projects.bountied & set(self.state.projects.active))`
            # inside the loop below, this rebuilt `set(self.state.projects.active)` from
            # scratch on every one of the 2,849 iterations of `candidates` -
            # the identical mistake `_earner_set` (above) had already been
            # fixed for, 30 lines earlier in this same function. Unlike
            # `earners`, `self.state.projects.active` IS mutated inside this loop (a normal
            # start at the bottom, or post_bounty() below, which adds to both
            # `self.state.projects.active` and `self.state.projects.bountied` at once), so the fix cannot
            # be "hoist one set outside the loop" - it has to track the two
            # mutations as they happen instead:
            #   - post_bounty(node_id) succeeding adds node_id to self.state.projects.active AND to
            #     self.state.projects.bountied together, so a bountied project never counts
            #     against max_active: _non_bountied_active is left unchanged.
            #   - a normal start only adds node_id to self.state.projects.active, so
            #     _non_bountied_active goes up by one.
            # Nothing else in this loop's body (can_start, project_cost,
            # funding_capacity, committed_spend, bounty_eligible) touches
            # self.state.projects.active or self.state.projects.bountied - checked in projects.py and
            # economy.py - so these two increments are the only places the
            # tracked count can move, and it is computed once up front
            # (O(active), not O(order)) rather than every iteration.
            _non_bountied_active = len(self.state.projects.active) - len(self.state.projects.bountied & set(self.state.projects.active))
            _room = self.funding_capacity() - self.committed_spend()
            _said_blocked = False
            _too_dear = []
            for node_id in candidates:
                if _non_bountied_active >= max_active:
                    automation_audit.record_skip(
                        self, "auto_start", "further projects",
                        "%d projects already active; the cap is %d" % (_non_bountied_active, max_active))
                    break
                if not self.can_start(node_id):
                    # one row a year, for the highest-priority candidate; the rest would flood the trail
                    if not _said_blocked:
                        _said_blocked = True
                        automation_audit.record_skip(
                            self, "auto_start", self.nodes[node_id]["name"],
                            self.start_refusal(node_id) or "cannot start yet")
                    continue
                # do not start something we cannot plausibly fund this decade.
                # material_cost_factor is the geography data's contribution: a
                # located material (mat_gutta_percha and the like) costs more
                # or less to reach depending on how far THIS civ actually is
                # from it, not on Rome's distance to it.
                # Do not begin what you cannot pay for: `room` must reflect
                # what the household can actually fund, net of committed
                # spend, because a project started on unaffordable capacity
                # gets its bill left unpaid - creditors halt everything, and
                # the spend already made is lost.
                #
                # INTEREST IS A FIXED COST here too: leaving it out is how a
                # household already in arrears would compute a surplus that
                # is not really there, commit spend against it, and deepen
                # the arrears it was already in.
                #
                # funding_capacity()/committed_spend() (economy.py), NOT A
                # SECOND COPY OF THIS FORMULA: the player-facing aggregate
                # warning in `start` (protocol.py) answers the identical
                # question by calling the same two functions, so the two
                # cannot drift apart.
                if self.project_cost(node_id) > _room:
                    _too_dear.append((node_id, _room))
                    continue
                _before = self.state.household.capital
                if node_id in self.bounty_set and self.bounty_eligible(node_id) and self.post_bounty(node_id):
                    automation_audit.record(
                        self, "auto_start", "bounty", self.nodes[node_id]["name"],
                        "on the bounty list and eligible, so a bounty was posted instead of starting it", _before)
                    # post_bounty() just added node_id to both self.state.projects.active and
                    # self.state.projects.bountied - the count of NON-bountied active
                    # projects is unchanged.
                    _room = self.funding_capacity() - self.committed_spend()
                    continue
                # lab_left starts full here too, for the same reason
                # start_project (projects.py) sets it at creation rather than
                # leaving lab_year_draw to guess it from ph_left the first
                # time it runs - see the comment there.
                self.initialize_project(node_id)
                _non_bountied_active += 1
                _room = self.funding_capacity() - self.committed_spend()
            if _too_dear:
                # one row a year: the highest-priority candidate and how many more were dearer than their room
                first, room = _too_dear[0]
                automation_audit.record_skip(
                    self, "auto_start", self.nodes[first]["name"],
                    "costs %.0f and the room left to commit is %.0f; %d candidates in all cost more than the room"
                    % (self.project_cost(first), room, len(_too_dear)))
        return pool, hired_left

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
                and (self.state.founder.policy.get("auto_mine", not self.manual)
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
                    and self.state.founder.policy.get("auto_mine", not self.manual)):
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
                # Shafts already sinking count, so a tranche about to
                # commission is not ordered twice.
                want = max(0.0, short - self.mine_capacity.get(self.state.holdings.binding, 0.0)
                           - self.state.holdings.mine_pending.get(self.state.holdings.binding, 0.0))
                _before = self.state.household.capital
                _pending = self.state.holdings.mine_pending.get(self.state.holdings.binding, 0.0)
                _ordered = min(want, self.state.household.capital * 0.25
                               / max(1.0, self._mine_capex(self.state.holdings.binding)))
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
                        _before, order=_order)
                else:
                    automation_audit.record_skip(
                        self, "auto_mine", "mine for %s" % self.state.holdings.binding,
                        "nothing ordered: shortfall %s against %s active and %s pending, "
                        "a quarter of capital buys %s"
                        % (mass_rate_text(short, self),
                           mass_rate_text(self.mine_capacity.get(self.state.holdings.binding, 0.0), self),
                           mass_rate_text(_pending, self),
                           mass_rate_text(self.state.household.capital * 0.25
                                          / max(1.0, self._mine_capex(self.state.holdings.binding)), self)))
                # Iron and the base metals are smelted with charcoal, so the
                # ore is only half the answer.
                if self.state.holdings.binding in ("iron", "copper", "lead"):
                    self.buy_forest(min(200.0, self.state.household.capital / self.AUTO_FOREST_CAPITAL_PER_HA))
            elif (self.state.holdings.binding == "saltpetre"
                    and self.state.founder.policy.get("auto_mine", not self.manual)):
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
                spend = min(self.state.household.capital * 0.05, self.NITRE_BED_SPEND_CEILING)
                self.pay_edge(edges.EDGE_BUILDERS, spend, "nitre beds laid down")
                self.state.holdings.nitre_bed_m2 += spend / self.NITRE_COST_PER_M2
                automation_audit.record(
                    self, "auto_mine", "nitre", "%s of nitre bed" % area_text(spend / self.NITRE_COST_PER_M2, self, unit="square_metre"),
                    "saltpetre is the binding shortage; the yearly spend is capped, not sized to the gap",
                    self.state.household.capital + spend)
                self.state.household.log.append((self.state.scenario.year, "laid down %s of nitre bed "
                                     "for %s (auto_mine)"
                                 % (area_text(spend / self.NITRE_COST_PER_M2, self, unit="square_metre"),
                                    money_text(spend, self))))
        if thr < 0.6 and self.state.holdings.binding:
            # SAY WHAT TO DO ABOUT IT: a bare "SHORT OF SALTPETRE: work at
            # 5% of plan" with no remedy attached reads as the game being
            # stuck rather than as something actionable.
            # One standing condition; the full message only when it is new or has moved materially.
            if shortage_conditions.note_shortage(self, self.state.holdings.binding, thr):
                self.state.household.log.append((self.state.scenario.year, "SHORT OF %s: work running at %d%% of plan. %s"
                                 % (self.state.holdings.binding.upper(), thr * 100,
                                    self.shortage_remedy(self.state.holdings.binding))))
        else:
            shortage_conditions.clear_shortage(self)
