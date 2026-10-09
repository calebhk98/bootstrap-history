"""The yearly money phase: the founder's takings and costs, credit, insolvency, then society and the actors' year.

A part of the year's phases (core_step_phases.py); Sim inherits it through StepPhasesMixin."""
from . import automation_audit
from sim.constants import declare
from sim.agents.api import edges


class MoneyPhaseMixin:

    AUTO_BUY_PEOPLE_CAPITAL_FLOOR_IN_PRICES = declare(
        "AUTO_BUY_PEOPLE_CAPITAL_FLOOR_IN_PRICES", 20.0, kind="temporary_heuristic",
        unit="base prices of one person", source=None, confidence="D",
        why="Capital the optimizer must hold, as a number of what one person costs to buy, before its "
            "standing policy buys people. A price multiple, so it follows the cost of a person in any coin. "
            "Tuned, not measured.")
    AUTO_BUY_PEOPLE_CAPITAL_PER_PERSON_IN_PRICES = declare(
        "AUTO_BUY_PEOPLE_CAPITAL_PER_PERSON_IN_PRICES", 5.0, kind="temporary_heuristic",
        unit="base prices of one person", source=None, confidence="D",
        why="Capital kept in reserve per person the optimizer's standing policy buys, as a multiple of "
            "one person's base price, so a purchase never spends the purse down to the price. "
            "Tuned, not measured.")

    def _step_money(self):
        # 2. money
        living_cost = self.living_cost()
        # THE YEAR YOU PAID FOR IN ADVANCE IS NOT BILLED AGAIN: `hire` takes
        # a finder's fee and the first year's wages up front, and
        # living_cost() carries the whole payroll, so without netting the
        # advance off here, a smith at 281 a year would cost 566 in his
        # first year - the advance, then the identical year again at the
        # next step.
        prepaid = min(living_cost, self.state.household.wages_prepaid)
        living_cost -= prepaid
        self.state.household.wages_prepaid = 0.0
        self.state.founder.living_cost_paid += living_cost
        mine_cost = self.mine_operating_cost()
        self.state.holdings.mine_cost_paid += mine_cost
        revenue, upkeep = self.revenue(), self.upkeep()
        # The guard is paid from what the purse and the credit line can bear, like any other spending.
        room = max(0.0, self.state.household.capital + self.credit_limit() + revenue - upkeep - living_cost - mine_cost)
        keeping_owed = self.coin_hoard()["keeping_cost_per_year"]
        keeping = min(keeping_owed, room)
        self.receive_from_edge(edges.EDGE_CUSTOMERS, revenue, "venture revenue")
        self.pay_edge(edges.EDGE_SUPPLIERS, upkeep, "running costs of concerns")
        self.pay_wages(living_cost, "living costs")
        self.pay_edge(edges.EDGE_SUPPLIERS, mine_cost, "mine running costs")
        self.pay_edge(edges.EDGE_COIN_GUARDS, keeping, "keeping coin under guard")
        self.charge_founder_for_theft(keeping, keeping_owed)
        # A mine you cannot pay for is a mine you stop working. Without this the
        # opex accrued for ever against a bankrupt enterprise: the England run
        # sank a large mine, lost its revenue and then ran three centuries at
        # minus four million denarii, unable to afford anything at all, which
        # the log reported as being "blocked" on a treadle lathe.
        if self.state.household.capital < 0 and self.mine_capacity and self.state.founder.policy.get("auto_mothball", True):
            self.mothball_mines()
        # A CONCERN NEEDS SOMEBODY WATCHING IT EVERY YEAR, not only on the day
        # you open it: `open` refusing without supervisors is not enough if
        # nothing ever checks again afterward, or a concern can keep
        # earning with nobody employed at all, straight through any
        # attrition or hazard that empties the payroll.
        # THE OTHER HALF OF THE SAME RULE, and applied FIRST: staff hired or
        # taught this same year (the block just above) should get first claim
        # on reclaiming what attrition shut, before anything is judged still
        # short and closed again. See reopen_restaffed_ventures's own
        # docstring for why this is not gated by auto_open.
        _before = self.state.household.capital
        _reopened = self.reopen_restaffed_ventures(self.state.scenario.year)
        if _reopened:
            automation_audit.record(
                self, "reopen (always on, not a policy)", "reopen", ", ".join(_reopened),
                "a staffing closure, and the people to watch it are free again", _before,
                ids=list(_reopened))
        self.close_lapsed_dependents(self.state.scenario.year)
        self.close_unstaffed_ventures(self.state.scenario.year)
        # Open what plainly pays for itself, before the books are struck: a
        # concern you opened this year is a concern that earns this year.
        if self.state.founder.policy.get("auto_open", not self.manual):
            _before = self.state.household.capital
            _opened = self.auto_open_ventures()
            if _opened:
                automation_audit.record(
                    self, "auto_open", "open", ", ".join(_opened),
                    "net-positive concerns already built, within the staff and money available",
                    _before, ids=list(_opened))
        self.charge_interest(self.state.scenario.year)
        if self.state.founder.policy.get("auto_shed", True):
            self.shed_loss_makers(self.state.scenario.year)
        self.warn_near_the_limit(self.state.scenario.year)
        self.enforce_credit_limit(self.state.scenario.year)

        # INSOLVENCY MUST HAVE A CONSEQUENCE: capital sitting deeply negative
        # for years with no event, no block and no attrition would not be a
        # hard game made easy, it would be an accounting fiction that
        # quietly makes every cost in the model optional.
        #
        # The consequence is deliberately the realistic one rather than a
        # dramatic one. Nobody arrests you for debt. What happens is that people
        # you cannot pay stop turning up, and nobody will extend you credit for
        # something new while you are in arrears.
        if self.state.household.capital < 0:
            # BEING IN DEBT IS NOT THE SAME AS BEING INSOLVENT: counting a
            # year of arrears for every year capital is below zero,
            # regardless of what the household is earning, would keep a
            # household running a surplus and paying its debt down
            # classified as insolvent and refused permission to start
            # anything - which is exactly what would keep it from ever
            # climbing out. A household running a surplus is paying its
            # creditors, and nobody calls that insolvency; the counter is
            # for a household whose income does not cover its costs.
            _net = (self.revenue() - self.upkeep() - self.living_cost()
                    - self.mine_operating_cost())
            if _net > 0:
                self.state.household.insolvent_years = 0
            else:
                self.state.household.insolvent_years = self.state.household.insolvent_years + 1
            floor = -max(self.INSOLVENCY_FLOOR_MIN, self.revenue() * self.INSOLVENCY_FLOOR_REVENUE_MULTIPLE)
            if self.state.household.capital < floor and self.state.household.insolvent_years >= self.INSOLVENCY_YEARS_BEFORE_BLEED:
                # wages unpaid: freedmen leave first, they are free to
                # A FLOOR: staff must not bleed without limit, or fewer people
                # earn less, which deepens the arrears, which bleeds more
                # people - an unrecoverable doom loop. Insolvency should
                # cost you your expansion, not trap you in a state you can
                # never leave: a household that has shed everything also
                # stops paying for it, and can climb back.
                bleed = min(self.INSOLVENCY_BLEED_CAP, self.INSOLVENCY_BLEED_RATE * self.state.household.insolvent_years)
                self.state.household.artisans = max(self.INSOLVENCY_ARTISAN_FLOOR, self.state.household.artisans * (1.0 - bleed))
                self.state.household.scholars = max(self.INSOLVENCY_SCHOLAR_FLOOR, self.state.household.scholars * (1.0 - bleed * self.INSOLVENCY_SCHOLAR_BLEED_DISCOUNT))
                if self.state.household.insolvent_years in (3, 6, 12, 25):
                    self.state.household.log.append((self.state.scenario.year, "IN ARREARS for %d years: staff are leaving "
                                         "because you cannot pay them" % self.state.household.insolvent_years))
                # ABANDONMENT, and this is what makes insolvency survivable: a
                # permanently underwater household must not simply sit
                # floored, simulating centuries of nothing and reporting it
                # as "ran out of horizon". An enterprise that cannot
                # maintain its works does not pay for them for five
                # centuries. It lets them go, and the buildings fall down.
                # You lose what they gave you and can rebuild later, which
                # is a real cost and a real way out.
                net = (self.revenue() - self.upkeep() - self.living_cost()
                       - self.mine_operating_cost())
                # ONLY WORKS THAT COST MORE THAN THEY RETURN, and only if you
                # let it happen at all: a loop that runs until the books
                # balance, rather than until shedding stops helping, would
                # go on destroying profitable works once the genuine
                # loss-makers are gone, each one making the deficit worse
                # for ever - and it must respect the auto_shed switch, in a
                # game whose own help says "every one of them is a switch
                # you control".
                if net < 0 and self.state.founder.policy.get("auto_shed", True):
                    burden = sorted((node_id for node_id in self.state.projects.done
                                     if self.nodes[node_id]["up"] > self.nodes[node_id]["rev"]
                                     and node_id not in self.state.projects.granted
                                     and not self.never_abandon(node_id)),
                                    key=lambda k: (self.nodes[k]["rev"] - self.nodes[k]["up"]))
                    shed = []
                    for node_id in burden:
                        if net >= 0:
                            break
                        node = self.nodes[node_id]
                        net += node["up"] - node["rev"]
                        # CLOSE IT, DO NOT UNLEARN IT - and above all do not do
                        # both: discarding from `done` while adding to
                        # `mothballed` produces a state no verb can clear -
                        # `start` sends to `restore`, `restore` says the
                        # trade is no longer known, `open` says it was
                        # never built and `mothball` says there is nothing
                        # to shut. If that node gates a whole branch,
                        # `available` reads "0 startable now" indefinitely.
                        self.close_work(node_id, self.CLOSED_LOSS_MAKING)
                        shed.append(node_id)
                    if shed:
                        # NAME THEM, for the same reason as shed_loss_makers and
                        # the creditors' seizure below: a bare count does not
                        # tell a player what they lost or why it later
                        # reappeared mothballed rather than gone for good.
                        self.state.household.log.append((self.state.scenario.year, "ABANDONED %d works you could no longer "
                                             "maintain; they have fallen into disrepair: %s"
                                             % (len(shed), ", ".join(shed))))
        else:
            self.state.household.insolvent_years = 0
        # A standing workforce policy, and ONLY when the optimizer is playing:
        # buying people automatically in manual mode, with no command issued
        # and no log line, would be lying about the acquisition - the game's
        # own justification for modelling slavery at all is that "a model
        # that hides it lies about the cost of everything", and hiding the
        # acquisition from a player is the worst version of that.
        if self.state.founder.policy.get("auto_buy_people", False):
            if self.state.household.capital > self.AUTO_BUY_PEOPLE_CAPITAL_FLOOR_IN_PRICES * self.labour.SLAVE_BASE_PRICE and self.state.household.artisans < 12 and self.running_with_mechanic("hosts_bought_people"):
                got = self.labour.buy_slaves(min(6, int(self.state.household.capital // (self.AUTO_BUY_PEOPLE_CAPITAL_PER_PERSON_IN_PRICES * self.labour.SLAVE_BASE_PRICE))))
                if got:
                    self.state.household.log.append((self.state.scenario.year, "bought %d people for the workshop" % got))
        if self.state.founder.policy.get("auto_manumit", not self.manual) and self.state.household.slaves:
            if self.rng.random() < self.AUTO_MANUMIT_ANNUAL_CHANCE:
                freed = self.labour.manumit(max(1, self.state.household.slaves // self.AUTO_MANUMIT_SHARE_DIVISOR))
                if freed:
                    self.state.household.log.append((self.state.scenario.year, "freed %d people" % freed))
        # currency debasement and war damage now come from the civilization's
        # own hazard list, not from Rome's dates baked into the engine
        if self.state.economy.output_factor < 1.0:
            # A STATE THAT CAN DEFEND ITSELF REBUILDS FASTER: the recovery
            # rate must scale with military_leverage(), or a civilization
            # that built the whole military branch and one that ignored it
            # would recover from the SAME war at the SAME speed regardless of
            # either one's investment. military_leverage() is
            # the same count update_protection() and
            # hazard_relief("output_factor") (society.py) already read off
            # self.state.projects.done; at full leverage the recovery rate doubles, so an
            # armed empire is back to normal trade in roughly half the years
            # an unarmed one takes, not instantly - the war still happened
            # and the years it cost are not given back.
            self.state.economy.output_factor = min(1.0, self.state.economy.output_factor
                                     + self.OUTPUT_RECOVERY_RATE * (1.0 + self.military_leverage()))
        # Population and the wage premium it drives recover/build in on their
        # own clock too, and must run before this year's shocks get a chance
        # to add a fresh deficit - see _demographic_recovery for why.
        self._demographic_recovery(self.state.scenario.year)
        # Literacy and taught-trade naturalisation move on the same kind of
        # slow, generational clock as population above - see
        # SocietyMixin.advance_society (society.py) for the mechanism. Run
        # here, before 4a2's auto_train reads literate_capacity() below, so
        # a year's schooling gain is visible to this same year's teaching
        # decisions rather than lagging a full step behind them.
        self.advance_society(self.state.scenario.year)
        self.advance_actors(self.state.scenario.year)
        # 2c. THRESHOLD GOALS. A node carrying a `win_condition` (see
        # data.py's WIN_CONDITION_LABELS and the tree's own goals
        # using one) is never built - start_reason refuses it outright -
        # it completes itself the moment a live measurement crosses its
        # target. Checked here, right after the literacy/trade growth this
        # same measurement usually depends on has moved for the year, so a
        # threshold crossed this year is seen this year rather than lagging
        # a full step behind it.
        self._check_win_conditions(self.state.scenario.year)
