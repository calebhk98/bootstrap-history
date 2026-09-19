"""The year's phases: what step() calls, in the order it calls them.

These are methods of Sim, living in a mixin (StepPhasesMixin) rather than
directly in core.py's `class Sim(...)`. `Sim.step()` itself stays in
core.py: it is the orchestrator, not one of the phases, and it is short
(42 lines) because it only calls `self._step_apprenticeships()` and the
other named phases this file holds - method resolution walks the whole
MRO, so it does not matter to `step()` that these live on StepPhasesMixin
rather than directly on Sim.

Each phase method below still reads and writes exactly the self.* state it
needs, UNASSIGNED to any one domain mixin's territory: this file groups
the phases by "step() calls them in this order", not by "the labour phase
belongs to labour.py, the money phase belongs to economy.py". Assigning
each phase's state to a specific domain mixin is a distinct, harder job
(see docs/architecture/SIM_DECOMPOSITION_REVISITED.md's staged proposal)
that this file does not attempt - do not assume a phase here can be moved
into a domain file without first working out its self.* footprint.
"""
import math

from .data import trade_family, WAGES
from sim.unit_conversions import KILOGRAMS_PER_TONNE, PERCENT_SCALE


class StepPhasesMixin:
    """Composition point only: every method below is one of the fourteen
    named phases Sim.step() calls, in order. Sim inherits this mixin, so
    step() calls self._step_whatever() exactly as if these methods were
    defined directly on Sim.
    """

    def _step_apprenticeships(self):
        # 0. PEOPLE WHOSE APPRENTICESHIP ENDED, FIRST, BEFORE THE YEAR'S WORK
        #    IS HANDED OUT: a man who finishes his training at the turn of the
        #    year works that year, so a machinist promised "ready in 102" must
        #    be usable in 102, not only from 103.
        # People bought this year are not artisans this year.
        if self.household.training:
            still = []
            for row in self.household.training:
                cap, ready = row[0], row[1]
                trade = row[2] if len(row) > 2 else None
                count = row[3] if len(row) > 3 else 0.0
                if self.year >= ready:
                    if trade:
                        # A trade you taught. They are now yours to pay, and
                        # they are that trade and no other.
                        self.household.employees[trade] = self.household.employees.get(trade, 0.0) + count
                        self.household.log.append((self.year, "%g %s%s finish their training"
                                         % (count, trade, "s" if count != 1 else "")))
                        self._resync_pools()
                    else:
                        # They are trained now, so _resync_pools counts them
                        # from the people you actually hold - see the note
                        # there about why adding to self.household.artisans directly was
                        # thrown away at the next call.
                        self.household.log.append((self.year,
                                         "%g of the people you bought finish "
                                         "learning the work" % round(cap / 0.55, 1)))
                else:
                    still.append(row)
            # BEFORE the resync, not after: _resync_pools counts who is still
            # learning off this very list, so recomputing while the matured row
            # was still on it cost a whole extra year of everybody's time.
            self.household.training = still
            self._resync_pools()

    def _step_staff(self):
        # 1. staff. ATTRITION IS UNCONDITIONAL: people die, are poached and grow
        #    old whatever your policy is. GROWTH IS NOT: growing the staff
        #    automatically, with no command issued, would be the same fault
        #    as buying people without being asked, so it is gated behind
        #    auto_hire.
        #
        #    With auto_hire on (the default for the optimizer, off for a player)
        #    staff smooths toward capacity, which is what the long civilization
        #    runs are calibrated against. With it off, the only things that
        #    change the staff are hire, fire, train, buy and manumit.
        sc_cap, ar_cap, di_cap = self.staff_capacity()
        attrition_rate = self.STAFF_ATTRITION_RATE
        # PEOPLE ARE WHOLE: attrition rolls each actual person on the books
        # individually against self.rng, sorted by trade name so the draws
        # happen in the same order whatever PYTHONHASHSEED the process
        # started with, the same convention every other rng loop over this
        # dict uses (see the "cannot pay" shedding loop below). A death is a
        # discrete thing that either happens to a particular person this
        # year or does not, so no trade's headcount is ever a fraction of a
        # person - never "1.32 artisans" or "0.03 engineers" drawing a
        # fractional wage while supervising nothing. Summed over many people
        # this reproduces the same 3.5%-a-year average ATTRITION targets; no
        # single person is ever a third of a casualty.
        _lost = {}
        for trade_id in sorted(self.household.employees):
            head = int(round(self.household.employees[trade_id]))
            survivors = sum(1 for _ in range(head) if self.rng.random() >= attrition_rate)
            if head - survivors > 0:
                _lost[trade_id] = head - survivors
            if survivors > 0:
                self.household.employees[trade_id] = float(survivors)
            else:
                self.household.employees.pop(trade_id)
        # AND SAY SO: a death is a discrete event that HAPPENED, and a player
        # watching the payroll shrink with nothing in the log or the events
        # to say why cannot tell attrition from a bug - it looks exactly
        # like staff vanishing.
        if _lost:
            self.household.log.append((self.year, "you lose %s to death and to better offers"
                             % ", ".join("%d %s%s" % (count, trade_id, "" if count == 1 else "s")
                                         for trade_id, count in sorted(_lost.items()))))
        self._resync_pools()
        # A HOUSEHOLD THAT CANNOT PAY ITS PEOPLE LETS THEM GO. This is the whole
        # answer to "you built it from nothing, so you must be able to rebuild
        # it": a payroll a household cannot carry and never reduces keeps a
        # ruined run frozen indefinitely, worse than shedding staff, living
        # cheaply and starting again.
        #
        # THE TRIGGER MUST BE "CANNOT PAY AFTER CREDIT", NOT `capital < 0`:
        # being overdrawn is not being unable to pay. A household with credit
        # left borrows and makes payroll; that is what credit is for, and
        # enforce_credit_limit already models the point where it runs out.
        # Letting staff go the first year capital dips a denarius below zero,
        # with the lender still willing, is not what an enterprise does.
        #
        # THE GAP BEING CLOSED MUST EXCLUDE living_cost()'S OWN WAGE BILL:
        # living_cost() INCLUDES the wage bill, so measuring the deficit
        # directly against it would close the payroll PLUS the founder's own
        # food, rent and appearances - firing people cannot buy your own
        # dinner. Whenever base living exceeds revenue, which it does in
        # every early game, that would run the shedding loop off the end of
        # the staff list and empty it.
        #
        # The honest rule is that your people are paid out of what is left after
        # everything else, INCLUDING what somebody will still lend you, and you
        # shed only the part of the payroll that will not cover.
        payroll = self.wage_bill()
        other = (self.upkeep() + (self.living_cost() - payroll)
                 + self.mine_operating_cost())
        # capital is negative in arrears; credit_limit() is how far into arrears
        # anyone will let you go, so this is what you can actually still spend.
        headroom = max(0.0, self.household.capital + self.credit_limit())
        can_pay = self.revenue() - other + headroom
        # NOT GATED BY A POLICY, and this is the one automatic thing that is not.
        # A policy switch is for something the game decides FOR you - who to
        # hire, what to mothball - and every one of those is yours to turn off.
        # People leaving a household that has no money and no credit to pay them
        # is not a decision the game is making on your behalf, it is the world
        # answering one you already made, the same as the arrears bleed below.
        # The `policy` reply says so in as many words.
        if payroll > can_pay and self.household.employees:
            short = payroll - can_pay
            gone = 0.0
            # shed, dearest first, until the wages you are left with fit
            for trade_id in sorted(self.household.employees, key=lambda t: -self.annual_wage(t)):
                if short <= 0:
                    break
                wage = self.annual_wage(trade_id)
                if wage <= 0:
                    continue
                # A WHOLE PERSON, ROUNDED UP. `short / wage` is a quantity of
                # wages, not a quantity of people: cutting that fraction
                # straight would leave "0.3 smiths" still on the books, still
                # drawing 0.3 of a wage that was just found unaffordable.
                # Rounding up sheds one whole person too many at worst,
                # which is the safe direction for a household that genuinely
                # cannot make payroll.
                cut = min(self.household.employees[trade_id], math.ceil(short / wage - 1e-9))
                self.household.employees[trade_id] -= cut
                short -= cut * wage
                gone += cut
                if self.household.employees[trade_id] < 0.5:
                    self.household.employees.pop(trade_id)
            self._resync_pools()
            # ALWAYS, not only when it worked. Losing the staff you paid to hire
            # is more consequential than any of the flavour events that do get
            # logged, and a player who is not told has to notice their own wage
            # bill hit zero to find out.
            if gone > 0.005:
                self.household.log.append((self.year, "you cannot pay everyone: %.1f of your staff "
                                     "leave for work that pays" % gone))
        # NOT `capital > 0`: gating hiring on a strictly positive balance
        # creates a catch-22, where a household in arrears could never take
        # on the people whose work is the only way out of arrears. A run
        # that keeps a project going can carry a balance in the red almost
        # permanently and legitimately - the gate is not "you are ruined",
        # it is "you are building something". The affordability arithmetic
        # below - which already subtracts living cost, upkeep and the wages
        # you are carrying - is what decides how many to hire, and correctly
        # says nobody when there is nothing spare.
        _hire_room = (self.household.capital >= 0
                      or -self.household.capital <= self.credit_limit() * self.AUTO_HIRE_CREDIT_ROOM_SHARE)
        if (self.policy.get("auto_hire", not self.manual) and _hire_room):
            # Scaled by the SAME affordability figure staff_capacity() just
            # used for sc_cap/ar_cap (see the comment there): supervision-room
            # headroom is not a free six people, it is six people you still
            # have to pay for.
            extra = self.supervision_room() * self.household._staff_scale
            # THE SAME WALL hire() AND train() ENFORCE: `target_sc` is capped
            # at `literate_capacity("scholar")`, the wall a player typing
            # `hire scholar N` is refused at, so auto_hire cannot grow the
            # scholar pool past a ceiling a manual hire command could not
            # cross either. See literate_capacity()'s own docstring for the
            # other half of this: widening the wall enough that clamping to
            # it here does not simply strand every long civilisation run
            # short of what the tree actually asks for (the goal wants 25;
            # building the institutions staff_capacity() already credits
            # widens this same wall past that well before the goal is in
            # reach).
            target_sc = min(sc_cap + extra * self.AUTO_HIRE_SCHOLAR_EXTRA_SHARE, self.literate_capacity("scholar"))
            desired_sc = self.household.scholars + (target_sc - self.household.scholars) * self.AUTO_HIRE_SCHOLAR_APPROACH_RATE
            target_ar = ar_cap + extra
            desired_ar = self.household.artisans + (target_ar - self.household.artisans) * self.AUTO_HIRE_ARTISAN_APPROACH_RATE
            # Keep the per-trade books honest about the aggregate: staff taken on
            # for you are generic craftsmen and scribes, and that is all they are.
            craft = max(0.0, desired_ar - self.household.freedmen - self.household.slaves * self.AUTO_HIRE_SLAVE_CRAFT_CREDIT)
            specials = sum(value for trade_id, value in self.household.employees.items()
                           if trade_id not in ("artisan", "scholar") and trade_family(trade_id) == "craft")
            # SPECIALISTS MUST NOT EAT THE GENERALISTS: the generic bucket is
            # the remainder after every taught trade has taken its share,
            # so the top-up must not let specialist trades squeeze the
            # generic artisan count to nothing. Artisans are what supervise
            # a concern; a household of nothing but specialists cannot keep
            # its own doors open.
            #
            # PEOPLE ARE WHOLE: the smoothing above is a continuous approach
            # to a continuous target, by design, so writing that target
            # straight into `employees` would hand a fractional person
            # every single year, forever, never quite arriving.
            # _stochastic_round spends the fractional remainder as this
            # year's chance of the next whole hire, so the long-run average
            # this formula was tuned against is unchanged and every actual
            # year's headcount is an integer (see its own docstring).
            # THROUGH hire(), NOT AROUND IT: a direct write to the pools
            # here instead would mean every rule hire() enforces - the
            # advance, the household room, the literacy wall, the price
            # pressure, the refusals - has to be re-enforced by hand, and
            # any one left out silently diverges from what a player hitting
            # the same wall experiences. Routing through hire() makes that
            # impossible by construction rather than by vigilance: it is
            # whatever hire() says it is, for player and optimizer alike.
            # A refusal here is not an error - it is the same wall a
            # player hits - so it is simply not acted on.
            def _grow_to(trade, want):
                have = self.household.employees.get(trade, 0.0)
                delta = self._stochastic_round(want) - have
                if delta >= 1.0:
                    self.hire(trade, int(delta))
                elif delta <= -1.0:
                    self.fire(trade, int(-delta))
            _grow_to("artisan", max(craft * 0.25, craft - specials))
            if desired_sc > 0:
                _grow_to("scholar", desired_sc)
            # REPLACE THE PEOPLE YOU LOSE, trade by trade: attrition can erode
            # a taught trade toward zero, and nothing replaces it if the
            # top-up only knows about the two generic buckets. A programme
            # that trains the first machinists in the world and then lets
            # them die out has not trained anybody.
            # FROM THE TRADES YOU TAUGHT, not from the keys that happen to
            # be left: a trade falls out of `employees` entirely once the
            # last of them drops below 0.05, so iterating only over
            # `employees`'s own keys would stop replacing a taught trade,
            # permanently, the moment its last person is lost. Iterating
            # trades_created too is what keeps a trade whose last person
            # just died still eligible for replacement.
            for trade_id in sorted(set(self.household.employees) | set(self.household.trades_created)):
                if trade_id in ("artisan", "scholar"):
                    continue
                have = self.household.employees.get(trade_id, 0.0)
                want = max(have, self.TRADE_REPLACEMENT_TARGET_HEADCOUNT if trade_id in self.household.trades_created else 0.0)
                short = want - have
                if short > 0.02 and self.household.capital > self.annual_wage(trade_id) * self.TRADE_REPLACEMENT_AFFORDABILITY_YEARS:
                    self.household.employees[trade_id] = have + short
                    self.household.capital -= short * self.annual_wage(trade_id)
            self._resync_pools()
        # BUY A JOB WHEN A HANDFUL OF HANDS IS THE ONLY THING IN THE WAY:
        # letting contracted craftsmen count toward a project's staff
        # requirement only helps a person who thinks to type `commission`
        # unless the optimizer can call it too. A run that can see the
        # wall, has the money, and has no way to spend it on the wall is
        # the same dead end wearing a different hat.
        if self.policy.get("auto_commission", not self.manual):
            self.auto_commission_for_blocked()
        self.household.directors_extra += (di_cap - self.household.directors_extra) * self.DIRECTORS_EXTRA_APPROACH_RATE - self.household.directors_extra * attrition_rate
        self.household.artisans = max(0.0, self.household.artisans)
        self.household.scholars = max(0.0, self.household.scholars)
        self.household.directors_extra = max(0.0, self.household.directors_extra)
        # SAY IT WHEN IT CROSSES A WHOLE PERSON: the year's hour pool can
        # grow well past the founder's own baseline as institutions add
        # deputies, and the single largest change to the resource the
        # whole game is built on must not go unannounced.
        _whole = int(self.household.directors_extra)
        if _whole > int(getattr(self.household, "_said_deputies", 0)):
            self.household._said_deputies = _whole
            self.household.log.append((self.year, "you now have %d deput%s directing work in "
                                 "your name: your year is %s hours instead of "
                                 "%s. They came with the institutions you built"
                             % (_whole, "y" if _whole == 1 else "ies",
                                "{:,.0f}".format(self.director_pool()),
                                "{:,.0f}".format(self.cfg["founder_hours_per_year"]))))

    def _step_money(self):
        # 2. money
        self.economy = self.economy_index()
        living_cost = self.living_cost()
        # THE YEAR YOU PAID FOR IN ADVANCE IS NOT BILLED AGAIN: `hire` takes
        # a finder's fee and the first year's wages up front, and
        # living_cost() carries the whole payroll, so without netting the
        # advance off here, a smith at 281 a year would cost 566 in his
        # first year - the advance, then the identical year again at the
        # next step.
        prepaid = min(living_cost, self.household.wages_prepaid)
        living_cost -= prepaid
        self.household.wages_prepaid = 0.0
        self.living_cost_paid += living_cost
        mine_cost = self.mine_operating_cost()
        self.household.mine_cost_paid += mine_cost
        self.household.capital += self.revenue() - self.upkeep() - living_cost - mine_cost
        # A mine you cannot pay for is a mine you stop working. Without this the
        # opex accrued for ever against a bankrupt enterprise: the England run
        # sank a large mine, lost its revenue and then ran three centuries at
        # minus four million denarii, unable to afford anything at all, which
        # the log reported as being "blocked" on a treadle lathe.
        if self.household.capital < 0 and self.mine_capacity and self.policy.get("auto_mothball", True):
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
        self.reopen_restaffed_ventures(self.year)
        self.close_unstaffed_ventures(self.year)
        # Open what plainly pays for itself, before the books are struck: a
        # concern you opened this year is a concern that earns this year.
        if self.policy.get("auto_open", not self.manual):
            self.auto_open_ventures()
        self.charge_interest(self.year)
        if self.policy.get("auto_shed", True):
            self.shed_loss_makers(self.year)
        self.warn_near_the_limit(self.year)
        self.enforce_credit_limit(self.year)

        # INSOLVENCY MUST HAVE A CONSEQUENCE: capital sitting deeply negative
        # for years with no event, no block and no attrition would not be a
        # hard game made easy, it would be an accounting fiction that
        # quietly makes every cost in the model optional.
        #
        # The consequence is deliberately the realistic one rather than a
        # dramatic one. Nobody arrests you for debt. What happens is that people
        # you cannot pay stop turning up, and nobody will extend you credit for
        # something new while you are in arrears.
        if self.household.capital < 0:
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
                self.household.insolvent_years = 0
            else:
                self.household.insolvent_years = getattr(self.household, "insolvent_years", 0) + 1
            floor = -max(self.INSOLVENCY_FLOOR_MIN, self.revenue() * self.INSOLVENCY_FLOOR_REVENUE_MULTIPLE)
            if self.household.capital < floor and self.household.insolvent_years >= self.INSOLVENCY_YEARS_BEFORE_BLEED:
                # wages unpaid: freedmen leave first, they are free to
                # A FLOOR: staff must not bleed without limit, or fewer people
                # earn less, which deepens the arrears, which bleeds more
                # people - an unrecoverable doom loop. Insolvency should
                # cost you your expansion, not trap you in a state you can
                # never leave: a household that has shed everything also
                # stops paying for it, and can climb back.
                bleed = min(self.INSOLVENCY_BLEED_CAP, self.INSOLVENCY_BLEED_RATE * self.household.insolvent_years)
                self.household.artisans = max(self.INSOLVENCY_ARTISAN_FLOOR, self.household.artisans * (1.0 - bleed))
                self.household.scholars = max(self.INSOLVENCY_SCHOLAR_FLOOR, self.household.scholars * (1.0 - bleed * self.INSOLVENCY_SCHOLAR_BLEED_DISCOUNT))
                if self.household.insolvent_years in (3, 6, 12, 25):
                    self.household.log.append((self.year, "IN ARREARS for %d years: staff are leaving "
                                         "because you cannot pay them" % self.household.insolvent_years))
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
                if net < 0 and self.policy.get("auto_shed", True):
                    burden = sorted((node_id for node_id in self.household.done
                                     if self.nodes[node_id]["up"] > self.nodes[node_id]["rev"]
                                     and node_id not in self.household.granted
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
                        self.household.operating.discard(node_id)
                        self.household.mothballed.add(node_id)   # you can buy it back
                        shed.append(node_id)
                    if shed:
                        # NAME THEM, for the same reason as shed_loss_makers and
                        # the creditors' seizure below: a bare count does not
                        # tell a player what they lost or why it later
                        # reappeared mothballed rather than gone for good.
                        self.household.log.append((self.year, "ABANDONED %d works you could no longer "
                                             "maintain; they have fallen into disrepair: %s"
                                             % (len(shed), ", ".join(shed))))
        else:
            self.household.insolvent_years = 0
        # A standing workforce policy, and ONLY when the optimizer is playing:
        # buying people automatically in manual mode, with no command issued
        # and no log line, would be lying about the acquisition - the game's
        # own justification for modelling slavery at all is that "a model
        # that hides it lies about the cost of everything", and hiding the
        # acquisition from a player is the worst version of that.
        if self.policy.get("auto_buy_people", False):
            if self.household.capital > 6000 and self.household.artisans < 12 and self.running("workshop_first"):
                got = self.buy_slaves(min(6, int(self.household.capital // 1500)))
                if got:
                    self.household.log.append((self.year, "bought %d people for the workshop" % got))
        if self.policy.get("auto_manumit", not self.manual) and self.household.slaves:
            if self.rng.random() < self.AUTO_MANUMIT_ANNUAL_CHANCE:
                freed = self.manumit(max(1, self.household.slaves // self.AUTO_MANUMIT_SHARE_DIVISOR))
                if freed:
                    self.household.log.append((self.year, "freed %d people" % freed))
        # currency debasement and war damage now come from the civilization's
        # own hazard list, not from Rome's dates baked into the engine
        if self.output_factor < 1.0:
            # A STATE THAT CAN DEFEND ITSELF REBUILDS FASTER: the recovery
            # rate must scale with military_leverage(), or a civilization
            # that built the whole military branch and one that ignored it
            # would recover from the SAME war at the SAME speed regardless of
            # either one's investment. military_leverage() is
            # the same count update_protection() and
            # hazard_relief("output_factor") (society.py) already read off
            # self.household.done; at full leverage the recovery rate doubles, so an
            # armed empire is back to normal trade in roughly half the years
            # an unarmed one takes, not instantly - the war still happened
            # and the years it cost are not given back.
            self.output_factor = min(1.0, self.output_factor
                                     + self.OUTPUT_RECOVERY_RATE * (1.0 + self.military_leverage()))
        # Population and the wage premium it drives recover/build in on their
        # own clock too, and must run before this year's shocks get a chance
        # to add a fresh deficit - see _demographic_recovery for why.
        self._demographic_recovery(self.year)
        # Literacy and taught-trade naturalisation move on the same kind of
        # slow, generational clock as population above - see
        # SocietyMixin.advance_society (society.py) for the mechanism. Run
        # here, before 4a2's auto_train reads literate_capacity() below, so
        # a year's schooling gain is visible to this same year's teaching
        # decisions rather than lagging a full step behind them.
        self.advance_society(self.year)
        # 2c. THRESHOLD GOALS. A node carrying a `win_condition` (see
        # data.py's WIN_CONDITION_LABELS and tech_tree.json's own goals
        # using one) is never built - start_reason refuses it outright -
        # it completes itself the moment a live measurement crosses its
        # target. Checked here, right after the literacy/trade growth this
        # same measurement usually depends on has moved for the year, so a
        # threshold crossed this year is seen this year rather than lagging
        # a full step behind it.
        self._check_win_conditions(self.year)

    def _step_dated_shocks(self):
        # 3. dated shocks
        if self.events:
            self._shocks(self.year)
            if self.dead_reason:
                return True
        return False

    def _step_teach_trades(self):
        # 4a2. TEACH THE TRADES THIS SOCIETY DOES NOT HAVE. The optimizer has to
        #      do this for itself or half the tree is unreachable; a player does
        #      it with `train`, or turns this on.
        if self.policy.get("auto_train", not self.manual):
            want = {}
            # LOCAL, PER-YEAR MEMO for market_supply()/trade_available().
            # Both are pure functions of staff and trades_created, which this
            # whole block only READS - train(), below, adds to trades_created,
            # but that happens once, at the very end, after every use of these
            # memos - so the same handful of distinct trade names (maybe
            # thirty) get recomputed from scratch once per NODE that lists
            # them in `lab`, and hundreds of nodes across the tree share the
            # same absent trade (machinist, engineer, ...). This dict is a
            # plain local, created fresh every call and discarded when the
            # block ends, so it needs no invalidation logic at all: nothing
            # outside this block ever reads it, so it cannot go stale.
            _ms_memo, _ta_memo = {}, {}
            def _market_supply(trade):
                value = _ms_memo.get(trade)
                if value is None:
                    value = _ms_memo[trade] = self.market_supply(trade)
                return value
            def _trade_avail(trade):
                value = _ta_memo.get(trade)
                if value is None:
                    value = _ta_memo[trade] = self.trade_available(trade)
                return value
            # Anything already in hand that has lost its trade comes FIRST: those
            # projects are burning a slot and will be halted if nobody turns up.
            for node_id in self.household.active:
                for trade_id in self.nodes[node_id]["lab"]:
                    if _market_supply(trade_id) <= 0.0:
                        want[trade_id] = want.get(trade_id, 0) + 500
            # WORK THE PLAYER COULD START TODAY, not the whole tree. The old
            # test was "direct prerequisites satisfied", which is not "wanted":
            # it looked past cost, staff, state approval and every OTHER trade
            # a node needs, so it walked deep into the order training engineers,
            # then chemists, machinists and opticians, with no active project
            # asking for any of them. Its own description promises "when a
            # project needs them", and a project three tiers away with money
            # you do not have is not a project you need anything for yet.
            # ignore_trade asks the one question that answers that: if this
            # trade existed, would everything ELSE already let it start?
            # EXISTING IS NOT THE SAME AS ANYBODY BEING LEFT. A trade you
            # taught stays "available" for ever, so once the last machinist
            # had died of old age this loop skipped every node that needed
            # one and nobody was ever taught again. A Rome run built 829
            # technologies, sat on 31.9M denarii, and could not begin
            # precision_three_plate - which gates master_screw, the screw
            # lathe and the entire precision branch, ninety-nine of the
            # hundred and forty-six nodes on the road to the goal. This is
            # the same distinction start_reason learned an hour earlier.
            # Hoisted out of the loop below: it closes only over `self` and
            # the memos above, never over the loop variable `node_id`, so defining
            # it fresh on every one of ~2,800 iterations bought nothing.
            #
            # _is_gone(trade) ITSELF IS NOW MEMOIZED TOO (_gone_memo), for the same
            # reason _market_supply/_trade_avail already are: it reads only
            # _trade_avail(trade), _market_supply(trade) and
            # self._trade_headcount_pending(trade), and the last of those
            # (labour.py) reads only self.household.training and self.household.employees -
            # neither mutated anywhere in this block; train(), at the very
            # end of it, is the only thing that changes either, exactly as
            # the comment above already established for the other two. So
            # _is_gone(trade) is just as pure a function of (staff, trades_created)
            # across this whole block as they are, and is safe to cache the
            # same way.
            #
            # Caching matters here: `order` has ~2,800 nodes, many naming the
            # same handful of distinct trades, so recomputing `_is_gone(trade)` from
            # scratch for every node that names a trade costs one Python
            # function call per node even after the first node already
            # worked out the answer. `_is_gone` below answers the identical
            # question, through the identical `any()` (so a node whose FIRST
            # lab trade is already known gone, or one that fails
            # start_reason() right after, costs exactly what it always
            # did - no extra work done on the strength of a guess that it
            # would be needed), but every trade's verdict is computed once
            # and reused for every later node that names it, rather than
            # recomputed from scratch each time.
            _gone_memo = {}
            def _is_gone(trade):
                value = _gone_memo.get(trade)
                if value is None:
                    value = _gone_memo[trade] = (
                        not _trade_avail(trade)
                        or (_market_supply(trade) <= 0.0
                            and self._trade_headcount_pending(trade) <= 0.0))
                return value
            for node_id in self.order:
                if node_id in self.household.done or node_id in self.household.active:
                    continue
                node = self.nodes[node_id]
                if not any(_is_gone(trade_id) for trade_id in node["lab"]):
                    continue
                if not self.start_reason(node_id, ignore_trade=True)[0]:
                    continue
                for trade_id in node["lab"]:
                    if _is_gone(trade_id):
                        want[trade_id] = want.get(trade_id, 0) + 1
            # NOT EVERY YEAR: teaching two of a trade costs about nine hundred
            # of the founder's two thousand hours plus their keep, so
            # re-teaching a lost trade every single year it qualifies would
            # turn into a teaching treadmill that eats most of a run's
            # output. A trade is worth restoring; it is not worth half of
            # every year for ever.
            _taught = self.household.last_taught
            want = {trade_id: value for trade_id, value in want.items()
                    if self.year - _taught.get(trade_id, -999) >= self.RETEACH_EVERY}
            # AND ONLY IF YOU CAN PAY THEM: train() checks hours, literacy and
            # household room but nothing here about money, so teaching a
            # trade a household cannot actually afford to keep paid turns
            # every year after into a wage bill that eats its whole income.
            # A trade you cannot pay for is not a trade you have; it is a
            # wage bill that stops you building anything.
            #
            # Two standards, because the two cases are not alike. A trade a
            # project ALREADY IN HAND is waiting on (scored 500 above) is worth
            # borrowing against: that work is paid for and stops without it.
            # A trade for something you might start one day has to come out of
            # what you are actually clearing.
            _spare_tr = self.revenue() - self.upkeep() - self.living_cost()
            for trade_id, _score in sorted(want.items(), key=lambda kv: (-kv[1], kv[0]))[:1]:
                _wages = 2.0 * self.annual_wage(trade_id)
                _budget = (max(0.0, _spare_tr) + max(0.0, self.household.capital) * 0.10
                           if _score >= 500 else max(0.0, _spare_tr) * 0.5)
                if _wages > _budget:
                    continue
                _first = trade_id not in self.household.trades_created
                taught, _msg = self.train(trade_id, 2)
                # THE COOLDOWN IS ON TEACHING, NOT ON TRYING. Recording the
                # attempt meant a refusal - no room in the household, no hours
                # left, nobody to teach from - burned the trade's whole
                # twenty-five years, so the run went on needing machinists and
                # never asked again.
                if taught:
                    _taught[trade_id] = self.year
                    self.household.log.append((self.year, "you begin teaching the first %ss this "
                                         "world has ever had" % trade_id if _first else
                                     "the last %ss are gone; you begin teaching "
                                     "more" % trade_id))

    def _step_standing_work_directive(self):
        # 4a(ii). THE STANDING "WORK" DIRECTIVE. `work` (protocol.py) sells
        # hours for wages the moment a player types it; `allocate` lets them
        # say "sell N hours a year this way" ONCE and have it happen every
        # year without retyping it, the same standing-instruction idea as
        # the project directives just below. Run BEFORE `pool` is struck so
        # director_hours_committed() (which counts wage hours already sold
        # this year) sees it, exactly as it would if the player had typed
        # `work` by hand a moment ago.
        #
        # TOPPED UP, NOT DOUBLED. A player who already called `work` by hand
        # earlier this same turn has already sold some of the hours this
        # directive wants; this only sells the remainder, never the whole
        # directive again on top of what was already sold.
        _wd = self.household.hour_allocations.get("work")
        if _wd and _wd > 0 and self.household.work_trade:
            _already = getattr(self.household, "wage_hours_this_year", 0.0)
            _want = max(0.0, _wd - _already)
            if _want > 0.5:
                _room = max(0.0, self.director_pool() - self.director_hours_committed())
                _take = min(_want, _room)
                _got = 0.0
                if _take > 0.5:
                    _pay, _werr = self.work_for_wages(self.household.work_trade, _take)
                    # pay > 0 with an error is a WARNING (a bad trade, or
                    # starving an active project of its last hours), not a
                    # refusal - see work_for_wages's own docstring. The sale
                    # happened either way; only a genuine refusal (pay <= 0)
                    # means none of it landed.
                    if _pay > 0 or not _werr:
                        _got = _take
                # SAY SO, THE SAME WAY AN UNHONOURED PROJECT DIRECTIVE DOES,
                # BELOW. A standing instruction nobody is told failed is the
                # same unfairness either way: the founder-hours it asked for
                # either went unsold or went somewhere the player never
                # chose.
                if _wd - (_already + _got) > 1.0:
                    self.household.log.append((self.year, "DIRECTED HOURS UNUSED: your standing "
                                         "order to sell %s hours a year as a "
                                         "%s only managed %s this year - %s. "
                                         "'allocate' changes or clears it"
                                     % ("{:,.0f}".format(_wd), self.household.work_trade,
                                        "{:,.0f}".format(_already + _got),
                                        "no more of your own hours were left "
                                        "to sell once your projects and "
                                        "training had theirs"
                                        if _room < _want else
                                        "nobody here will pay for that trade "
                                        "any longer" )))

    def _step_start_projects(self):
        # 4b. start new projects
        pool = max(0.0, self.director_pool() - self.director_hours_committed())
        hired_left = self.hired_cap()
        # MANUAL MODE STOPS HERE. This loop is "the optimizer": it walks
        # `order` and starts whatever it judges best, which is exactly the
        # behaviour a free-choice player must NOT get. The old `play` command
        # let you type a node id, but that only did `order.remove/insert(0)`
        # a few lines above this loop's own input; the loop then ran anyway
        # and started other things you never asked for. `self.manual` cuts
        # that off at the root: nothing is ever added to `self.household.active` here,
        # so the only way anything starts is start_project(), called by a
        # human or a script. Everything below this block (materials, staff,
        # money, hazards, the calendar) is untouched by `manual` and keeps
        # running exactly as before.
        if not self.manual and self.year >= self.household.credit_frozen_until:
            # More directors means more things in hand at once, and a big trained staff
            # lets routine work proceed without the founder watching it.
            # How many things can be in hand at once: doubling this would let
            # more projects divide the same purse into smaller annual
            # payments, so everything crawls and nothing finishes. Spreading
            # a fixed budget across more work is not more work.
            max_active = int(self.MAX_ACTIVE_PROJECTS_BASE
                             + self.director_pool() / self.MAX_ACTIVE_PROJECTS_PER_DIRECTOR_HOURS
                             + self.household.scholars / self.MAX_ACTIVE_PROJECTS_PER_SCHOLAR
                             + self.household.artisans / self.MAX_ACTIVE_PROJECTS_PER_ARTISAN)
            # EARN A LIVING FIRST: now that a project must actually be paid
            # for, a founder who arrives with 400 denarii and walks the
            # goal-ordered list starves, so when the surplus is thin, the
            # optimizer has to prefer whatever pays best for what it costs
            # the same way a human player hunting for cheap revenue nodes
            # would; the goal order resumes the moment there is money to
            # pursue it with.
            fixed0 = self.upkeep() + self.living_cost() + self.mine_operating_cost()
            candidates = self.order
            if self.revenue() - fixed0 < max(400.0, fixed0 * 0.25):
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
            # `len(self.household.active) - len(self.household.bountied & set(self.household.active))`
            # inside the loop below, this rebuilt `set(self.household.active)` from
            # scratch on every one of the 2,849 iterations of `candidates` -
            # the identical mistake `_earner_set` (above) had already been
            # fixed for, 30 lines earlier in this same function. Unlike
            # `earners`, `self.household.active` IS mutated inside this loop (a normal
            # start at the bottom, or post_bounty() below, which adds to both
            # `self.household.active` and `self.household.bountied` at once), so the fix cannot
            # be "hoist one set outside the loop" - it has to track the two
            # mutations as they happen instead:
            #   - post_bounty(node_id) succeeding adds node_id to self.household.active AND to
            #     self.household.bountied together, so a bountied project never counts
            #     against max_active: _non_bountied_active is left unchanged.
            #   - a normal start only adds node_id to self.household.active, so
            #     _non_bountied_active goes up by one.
            # Nothing else in this loop's body (can_start, project_cost,
            # funding_capacity, committed_spend, bounty_eligible) touches
            # self.household.active or self.household.bountied - checked in projects.py and
            # economy.py - so these two increments are the only places the
            # tracked count can move, and it is computed once up front
            # (O(active), not O(order)) rather than every iteration.
            _non_bountied_active = len(self.household.active) - len(self.household.bountied & set(self.household.active))
            for node_id in candidates:
                if _non_bountied_active >= max_active:
                    break
                if not self.can_start(node_id):
                    continue
                node = self.nodes[node_id]
                # do not start something we cannot plausibly fund this decade.
                # material_cost_factor is geography.json's contribution: a
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
                room = self.funding_capacity() - self.committed_spend()
                if self.project_cost(node_id) > room:
                    continue
                if node_id in self.bounty_set and self.bounty_eligible(node_id) and self.post_bounty(node_id):
                    # post_bounty() just added node_id to both self.household.active and
                    # self.household.bountied - the count of NON-bountied active
                    # projects is unchanged.
                    continue
                # lab_left starts full here too, for the same reason
                # start_project (projects.py) sets it at creation rather than
                # leaving lab_year_draw to guess it from ph_left the first
                # time it runs - see the comment there.
                self.household.active[node_id] = dict(ph_left=float(node["ph"]), yrs=0.0, spent=0.0,
                                      cost_left=self.project_cost(node_id),
                                      lab_left=dict(node["lab"]))
                _non_bountied_active += 1
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
                and (self.policy.get("auto_mine", not self.manual)
                     or self.policy.get("auto_forest", not self.manual))):
            # Charcoal is GROWN, so the answer is woodland. Everything else in
            # this list is DUG, so the answer is a mine, and the old model had
            # no answer at all for coal: the binding constraint fell through
            # both branches and the run simply sat throttled. That is why coal
            # showed 1,669 shortage-years in a 395 year run.
            if self.household.binding == "charcoal":
                if self.policy.get("auto_forest", not self.manual):
                    # SIZED FROM THE SHORTFALL, like the mine branch below,
                    # rather than from a flat share of cash. A tenth of a
                    # denarius of capital bought a ten-thousandth of a hectare
                    # while the demand was measured in hundreds of tonnes.
                    _need_t = (self.annual_material_demand().get("charcoal_kg", 0.0)
                               / KILOGRAMS_PER_TONNE) - self.household.forest_ha * self.CHARCOAL_PER_HA
                    _want_ha = max(0.0, _need_t) / max(self.CHARCOAL_PER_HA, 1e-9)
                    _afford_ha = (_can_raise * 0.35
                                  / (self.FOREST_COST_PER_HA * self.price_index))
                    self.buy_forest(min(400.0, _want_ha, _afford_ha))
            elif (self.household.binding in self.MINE_CAPEX_PER_T_YR
                    and self.policy.get("auto_mine", not self.manual)):
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
                                    if bucket == self.household.binding))
                short = sum(dem.get(material, 0.0) for material in keys)
                want = max(0.0, short - self.mine_capacity.get(self.household.binding, 0.0))
                self.open_mine(self.household.binding, min(want, self.household.capital * 0.25
                                                 / max(1.0, self.MINE_CAPEX_PER_T_YR[self.household.binding])))
                # Iron and the base metals are smelted with charcoal, so the
                # ore is only half the answer.
                if self.household.binding in ("iron", "copper", "lead"):
                    self.buy_forest(min(200.0, self.household.capital / 1800.0))
            elif (self.household.binding == "saltpetre"
                    and self.policy.get("auto_mine", not self.manual)):
                # GATED, like every other automatic purchase: ungated, this
                # branch would take five per cent of a manual player's
                # capital every year they were short of nitre, without a
                # line in the log and without anything they typed.
                # A FLAT CEILING, AND IT IS NOT AN OVERSIGHT: sizing this to
                # the measured shortfall, the way the mine branch above does,
                # spends a quarter of capital a year against a shortfall
                # nitre beds cannot close at any affordable scale, which
                # starves everything else and, once the household falls into
                # arrears, pins it there with interest. Two thousand denarii
                # a year is what leaves the rest of the programme funded.
                #
                # The shortage is real and unresolved; more money is not the
                # answer to it.
                spend = min(self.household.capital * 0.05, 2000)
                self.household.capital -= spend
                self.household.nitre_bed_m2 += spend / self.NITRE_COST_PER_M2
                self.household.log.append((self.year, "laid down %d square metres of nitre bed "
                                     "for %d denarii (auto_mine)"
                                 % (spend / self.NITRE_COST_PER_M2, spend)))
        if thr < 0.6 and self.household.binding:
            # SAY WHAT TO DO ABOUT IT: a bare "SHORT OF SALTPETRE: work at
            # 5% of plan" with no remedy attached reads as the game being
            # stuck rather than as something actionable.
            self.household.log.append((self.year, "SHORT OF %s: work running at %d%% of plan. %s"
                             % (self.household.binding.upper(), thr * 100,
                                self.shortage_remedy(self.household.binding))))

    def _step_progress_project(self, node_id, pool_rank, pool_total_this_year,
                              pool_active_count_this_year, remaining, hired_left,
                              arrears_hours_lost, directed_hours_unused):
        # One project's share of this year's director hours and money, pulled
        # out of the priority loop in _step_progress() so the loop itself reads
        # as "for each active project, in priority order, give it its turn"
        # rather than burying that in 374 lines of one project's turn. Threads
        # remaining/hired_left through by argument and return, the same shared
        # pool every project in the loop draws from in order; arrears_hours_lost
        # and directed_hours_unused are the two logging lists _step_progress()
        # reports from once, after every project has had its turn, and are
        # appended to here exactly where the original inline code appended to
        # them.
        _pool_rank = pool_rank
        _pool_total_this_year = pool_total_this_year
        _pool_active_count_this_year = pool_active_count_this_year
        _arrears_hours_lost = arrears_hours_lost
        _directed_hours_unused = directed_hours_unused
        project_state = self.household.active[node_id]
        node = self.nodes[node_id]
        project_state["pool_total_this_year"] = _pool_total_this_year
        project_state["pool_active_count_this_year"] = _pool_active_count_this_year
        project_state["pool_rank_this_year"] = _pool_rank
        project_state["pool_remaining_before_this_year"] = round(remaining, 1)
        # A PIPELINE, ONE STAGE PER CONCERN, IN A FIXED ORDER: is there
        # anybody to do the work, how many hours does the project get this
        # year, what labour and bill follow from that, can the household
        # afford the bill, then the bookkeeping and completion check. Split
        # so this method reads as five sentences instead of one project's
        # whole turn in a single block. Every self.rng-touching call these
        # stages make (lab_year_draw is the only one that plausibly draws)
        # runs exactly once, in exactly this order, for exactly this
        # project - the stages are called unconditionally in sequence, and
        # only the two `continue`-turned-early-returns below skip any of
        # them.
        if self._project_progress_trade_gate(node_id, project_state, node):
            return remaining, hired_left, 0.0
        remaining, per, spent_hours, _dir_hours = self._project_progress_offer_hours(
            node_id, project_state, remaining, _pool_total_this_year, _directed_hours_unused)
        _labour = self._project_progress_labour_and_bill(
            node_id, project_state, node, hired_left, per, spent_hours)
        if _labour is None:
            return remaining, hired_left, 0.0
        hired_left, money, refunded = _labour
        money, refunded = self._project_progress_afford_gate(
            node_id, project_state, money, refunded, spent_hours, per, _arrears_hours_lost)
        self._project_progress_finish(
            node_id, project_state, money, refunded, spent_hours, _dir_hours,
            _directed_hours_unused)

        return remaining, hired_left, project_state["hours_effective_this_year"]

    def _project_progress_trade_gate(self, node_id, project_state, node):
        # Stage 1 of _step_progress_project: is there anybody to do the
        # work. Returns True when the project is stalled or just halted
        # this year, in which case the caller returns immediately with no
        # hours or money spent - the first of the two `continue`-turned-
        # early-returns the original loop already had. Returns False, and
        # clears stalled_years, when the project can proceed.
        # IS THERE ANYBODY TO DO THE WORK? If a trade this project needs
        # has vanished since it started (the machinists you taught died
        # out, say), nothing can be done on it this year, and your own
        # hours should go somewhere they are useful rather than into a
        # project that cannot absorb them.
        #
        # This matters more than it sounds. Without it a project whose
        # trade had disappeared sat in `active` for ever: hours went in,
        # no money was spent because no work was done, so the bill was
        # never paid, so it could never complete, so it never released
        # the slot. Four of those deadlocked a run at 98 technologies for
        # two hundred and fifty years.
        #
        # ONLY A TRADE THIS PROJECT STILL OWES SOMETHING TO: checked against
        # `_lab_left` (how much of each trade's hours remain to be drawn),
        # NOT node["lab"]'s ORIGINAL total (`want > 0`), which never goes back
        # to zero no matter how much of that trade's hours the project has
        # already drawn. lab_year_draw and trade_draw_plan both correctly
        # stop asking a trade for more once lab_left hits zero; checking the
        # original total here would keep vetoing the project on a trade it
        # no longer needs anything from - the same question `_waiting_on`
        # (protocol.py) already answers correctly off lab_left, so this
        # makes the stall check agree with the one that draws the hours.
        _lab_left = project_state.get("lab_left")
        if _lab_left is None:
            _lab_left = node["lab"]
        blocked = [trade_id for trade_id, want in node["lab"].items()
                   if want > 0 and _lab_left.get(trade_id, want) > 0
                   and self.market_supply(trade_id) <= 0.0]
        if blocked:
            project_state["stalled_years"] = project_state.get("stalled_years", 0) + 1
            project_state["blocked_on_trades"] = blocked
            if project_state["stalled_years"] >= 4:
                self.household.log.append((self.year, "HALTED %s: there is nobody here who can "
                                     "do this work (%s). What you spent is lost"
                                 % (node_id, ", ".join(blocked[:2]))))
                self.household.active.pop(node_id, None)
                self.household.bountied.discard(node_id)
            else:
                # WARN BEFORE THE MONEY GOES: a countdown to abandonment
                # running silently, with nothing said until everything
                # spent is taken at once, gives no chance to act. Say it
                # each year, with the number of years left and what would
                # fix it.
                _left = 4 - project_state["stalled_years"]
                self.household.log.append((self.year, "%s cannot go on: no %s here. It has "
                                     "%d year%s before it is abandoned and "
                                     "what you spent on it is lost. Teach "
                                     "the trade, or 'stop %s' now and keep "
                                     "your hours"
                                 % (node_id, " or ".join(blocked[:2]), _left,
                                    "" if _left == 1 else "s", node_id)))
                # Nothing happened here this year - say so, rather than
                # leaving last year's hours_offered/effective sitting on
                # the entry looking like they still applied.
                project_state["hours_offered_this_year"] = 0.0
                project_state["hours_effective_this_year"] = 0.0
            return True
        project_state["stalled_years"] = 0
        return False

    def _project_progress_offer_hours(self, node_id, project_state, remaining,
                                     _pool_total_this_year, _directed_hours_unused):
        # Stage 2: how many hours the project gets this year (`per`), what
        # that leaves of the shared pool (`remaining`), and the first of the
        # two places a standing allocation can go unhonoured. Returns the
        # updated remaining, per, spent_hours (for the give-backs later
        # stages compute) and _dir_hours (read again by stage 5's inner-gap
        # check).
        # project_hour_pace (projects.py) is this same formula, read
        # rather than re-derived, so 'work's own pre-sale warning
        # about starving an active project can never disagree with
        # what this loop actually offers it.
        #
        # A STANDING ALLOCATION IS A CEILING, NOT A FLOOR. hour_
        # allocations.get(node_id) is only ever a THIRD candidate in this
        # min() - never a reason to offer MORE than remaining or the
        # project's own pace would otherwise allow - so a directed
        # project can still never outrun the pool it shares with
        # everything else, and never get hours faster than its own
        # calendar floor could ever use. What it changes is ORDER
        # (active_sorted, above) and that an undirected project
        # never crowds this one out of the share the player asked
        # for it to have.
        _dir_hours = self.household.hour_allocations.get(node_id)
        _pace_cap = self.project_hour_pace(node_id)
        _project_throttle = self.project_resource_throttle(node_id)
        if _dir_hours and _dir_hours > 0:
            per = min(remaining, _pace_cap, _dir_hours) * _project_throttle
        else:
            per = min(remaining, _pace_cap) * _project_throttle
        remaining -= per
        # WHAT WAS ACTUALLY TAKEN OFF, which is not the same as what was
        # offered: `per` is allowed to exceed ph_left (the max() above
        # offers a full year's worth even to a project with an hour to
        # run), and the subtraction clamps at zero. A refund computed from
        # `per` instead of from what was truly spent could hand back more
        # than was ever taken - a project with 10 hours left offered 500
        # would have its 10 taken and be handed 200 back, ending the year
        # with twenty times the hours it began with, founder_hours_left
        # larger than founder_hours_total. You cannot be refunded work you
        # never did.
        spent_hours = min(per, project_state["ph_left"])
        project_state["ph_left"] = max(0.0, project_state["ph_left"] - per)
        self.director_hours_spent_founder += per if self.founder_alive else 0
        # Hours OFFERED this year vs hours that actually did anything.
        # `refunded` tracks the difference: hours credited back to
        # ph_left below because a trade or the money to pay for it
        # fell short. This must stay visible to the player: showing only
        # the net hours left, with nothing recording what was offered
        # versus refunded, reads as confusing and artificial when half a
        # year's hours come back with no explanation of why. See
        # hours_this_year in `state`.
        project_state["hours_offered_this_year"] = round(per, 1)
        # WHAT THE PLAYER ACTUALLY ASKED FOR, READ BACK AT THE END OF
        # THE YEAR - `portfolio` and `why` print this field verbatim,
        # same reasoning as pool_total_this_year and its neighbours
        # just above: never recompute a number a player is told,
        # always read the one this loop actually used.
        project_state["hours_directed_this_year"] = (round(_dir_hours, 1)
                                          if _dir_hours else None)
        # SAY SO WHEN THE PROMISE ITSELF WAS NOT KEPT, before any
        # trade or money shortfall even has a chance to bite further
        # in. A directive can be cut short right here, two ways: the
        # POOL had already given the rest away (to a higher-priority
        # directed project, or simply was not big enough for every
        # standing order at once), or this project's OWN pace -
        # what is left to do, or its calendar floor - could not use
        # that many hours even with the whole pool behind it. Either
        # is a real, nameable reason; "it disappeared" is not.
        if _dir_hours and _dir_hours > 0 and _dir_hours - per > 1.0:
            if (_project_throttle < 0.98 and self.household.binding
                    and _pace_cap >= _dir_hours - 0.5):
                _directed_hours_unused.append((node_id, round(_dir_hours - per, 0),
                    "a shortage of %s has every project (this one "
                    "included) running at %d%% of the pace its "
                    "hours alone would allow"
                    % (self.household.binding, round(_project_throttle * 100))))
            elif _pace_cap * _project_throttle < _dir_hours - 0.5:
                _directed_hours_unused.append((node_id, round(_dir_hours - per, 0),
                    "its own pace this year - at most %s hours, set "
                    "by how much of it is left to do or its "
                    "calendar floor, not by your hours - could not "
                    "use the rest" % "{:,.0f}".format(
                        _pace_cap * _project_throttle)))
            else:
                _directed_hours_unused.append((node_id, round(_dir_hours - per, 0),
                    "your other standing allocations and active "
                    "work already claimed the rest of this year's "
                    "%s hours before this one's turn came"
                    % "{:,.0f}".format(_pool_total_this_year)))
        return remaining, per, spent_hours, _dir_hours

    def _project_progress_labour_and_bill(self, node_id, project_state, node,
                                          hired_left, per, spent_hours):
        # Stage 3: the labour this project can actually hire this year and
        # the bill that follows from it. Returns None when the project was
        # abandoned this year - the second of the two `continue`-turned-
        # early-returns - in which case the caller returns immediately.
        # Otherwise returns the updated hired_left, money and refunded.
        refunded = 0.0
        project_state["yrs"] += 1
        frac = min(1.0, 1.0 / max(1.0, node["yrs"]))
        # Diagnostic callers can construct active-project dictionaries
        # directly, so initialise an omitted bill defensively.
        if project_state.get("cost_left") is None:
            project_state["cost_left"] = max(0.0, self.project_cost(node_id) - project_state["spent"])
        # LABOUR BY TRADE. The old model pooled every trade into one
        # bucket of hired hours, so 450 hours of engineer and 450 hours
        # of labourer were the same resource. They are not, and the wage
        # table has said so all along. What binds now is the scarcest
        # trade this project actually needs.
        #
        # HOURS ARE A TOTAL AND A CEILING NOW, NOT A FIXED ANNUAL TOLL.
        # See ProjectsMixin.lab_year_draw (projects.py) for the finding
        # that forced this and the reasoning behind the new shape; this
        # call site only has to act on what it returns.
        hired_hours, worst, frac, _abandon = self.lab_year_draw(node_id, project_state, frac, hired_left)
        if _abandon:
            self.household.log.append((self.year, "ABANDONED %s: %s" % (node_id, _abandon)))
            self.household.active.pop(node_id, None)
            self.household.bountied.discard(node_id)
            return None
        if worst < 1.0:
            # NEVER ALL OF IT: the refund says "hours offered but not
            # usable, because the trade was booked", and with no floor
            # under it could hand back every hour that had actually gone
            # in - leaving a project's founder-hours sit unchanged forever
            # whenever its scarcest trade stays short, the bill fully paid,
            # making no progress at all while holding an entire trade's
            # pool and freezing other projects behind it.
            #
            # If a fraction `worst` of the work could be done, then a
            # fraction `worst` of it WAS done, and that much can never
            # be given back. Progress is strictly positive whenever
            # anybody at all can be found.
            give_back = min(spent_hours - refunded,
                            per * 0.4 * (1.0 - worst),
                            spent_hours * (1.0 - worst))
            project_state["ph_left"] += max(0.0, give_back)
            refunded += max(0.0, give_back)
            # Remember it: `waiting_on` reporting "money" for a project
            # whose real block is a fully booked trade, not an actual spend
            # cap, is a misleading label even though the underlying
            # mechanic is correct - a player watching a large balance sit
            # unspent against "money" owed can reasonably conclude the
            # spend cap itself is broken. (short_of_trade itself is set
            # inside lab_year_draw, against the same pace this comment
            # describes.)
        if hired_hours > hired_left:
            frac *= hired_left / max(hired_hours, 1e-9)
            hired_hours = hired_left
        # THE INSTALMENT IS WHAT A CONSTRAINED YEAR CAN DO; THE BILL IS
        # WHAT IS LEFT: working from the already-scaled `frac`, applied
        # directly to `cost_left`, means a shortage sets how FAST a
        # project can be paid off and never stops the last payment
        # landing. Working the payment out first and then multiplying it
        # by each shortage in turn would instead pay a FRACTION OF WHAT
        # WAS LEFT every year, forever, once the remaining balance is
        # smaller than a year's instalment - a geometric decay that
        # approaches zero and never reaches it, while completion needs the
        # bill down to half a denarius.
        money = min(project_state["cost_left"], self.project_cost(node_id) * frac)
        hired_left -= hired_hours
        return hired_left, money, refunded

    def _project_progress_afford_gate(self, node_id, project_state, money, refunded,
                                     spent_hours, per, _arrears_hours_lost):
        # Stage 4: can the household actually afford this year's bill.
        # Returns the updated money and refunded.
        # You may spend into debt, up to what someone will lend you, and
        # no further. Beyond that the work simply does not get paid for
        # this year, and a year nobody was paid for is a year of little
        # progress. What must NOT happen is the bill being forgiven.
        #
        # The margin is deliberate. Spending to the last denarius of your
        # credit means next year's rent breaches the limit and the
        # creditors halt every project you have, which turns "I was
        # ambitious" into "everything I had in hand was destroyed". A
        # lender who will advance you a thousand will not let you draw
        # the last two hundred of it against a half-built balloon.
        # Reserve next year's fixed costs AND most of the credit line.
        # Drawing the line to its last denarius risks destroying everything
        # else in hand: the limit itself falls as reputation and revenue
        # fall, so a balance exactly at the limit this year is over it next
        # year, and over the line every project in progress is halted at
        # once.
        # Reserve only the SHORTFALL, not the whole running cost: this
        # year's rent and wages have already been taken out of capital at
        # the top of step(), so reserving them again would leave a
        # household whose income comfortably covers its costs unable to
        # spend a single denarius on its own projects.
        fixed = self.living_cost() + self.upkeep() + self.mine_operating_cost()
        reserve = max(0.0, fixed - self.revenue())
        purse = self.household.capital + self.credit_limit() * 0.6 - reserve
        # NOTHING OWED IS NOT THE SAME AS NOTHING AFFORDABLE: a project
        # with cost_left already at zero asks for money=0 this year, and
        # the money>purse test must not fire just because purse itself has
        # gone negative from deep arrears unrelated to this project's own
        # bill - a fully paid project, needing not one more denarius, must
        # still be free to make purely calendar-waiting progress. The gate
        # is on the household's purse only when this project actually
        # needs something from it.
        if money > 0 and money > purse:
            # PROPORTIONAL, not a flat half: the refund must scale by how
            # underfunded the purse actually is (`funded_frac`), the same
            # way the trade-shortage case two blocks up already scales its
            # refund by how much of the need went unmet (worst). A flat
            # per*0.5 refund whenever the purse falls short AT ALL, whether
            # by one denarius or by the whole bill, would give a project
            # funded to 95% of what it needed the same fixed half-progress
            # loss as one funded to 5%.
            funded_frac = 0.0 if money <= 0 else max(0.0, min(1.0, purse / money))
            money = max(0.0, purse)
            # Capped at what was actually taken off, and at what has not
            # already been handed back by the trade-shortage refund
            # above. See spent_hours: you cannot be refunded work you
            # never did, and you cannot be refunded the same hour twice.
            give_back = min(spent_hours - refunded, per * (1.0 - funded_frac))
            project_state["ph_left"] += max(0.0, give_back)
            refunded += max(0.0, give_back)
            project_state["underfunded_this_year"] = True
            # WHY, not just that: hours reported as "offered" with none
            # "effective" is meaningless without a reason. Arrears are the
            # reason: the purse a project may draw on is what you hold
            # plus part of your credit, less what your fixed costs need,
            # and in arrears that is nothing at all.
            project_state["why_underfunded"] = (
                "in arrears: after fixed costs there is nothing left to "
                "draw on, so the hours offered this year did almost "
                "nothing" if self.household.capital < 0 else
                "this year's instalment is more than the purse will bear")
            # SAY IT NOW, NOT ONLY WHEN ASKED. `why_underfunded` sits on
            # the project and answers the question if a player thinks
            # to check `why` or `portfolio` - but the founder-hours lost
            # here never come back, whatever the player does next, and
            # nothing prompted them to look. Recorded here (only the
            # arrears case, only if it actually cost real hours) and
            # logged once below, after the loop.
            if self.household.capital < 0 and give_back > 1.0:
                _arrears_hours_lost.append((node_id, round(give_back, 0)))
        else:
            project_state.pop("underfunded_this_year", None)
            project_state.pop("why_underfunded", None)
        return money, refunded

    def _project_progress_finish(self, node_id, project_state, money, refunded,
                                spent_hours, _dir_hours, _directed_hours_unused):
        # Stage 5: spend the money, record the hours actually done, the
        # second place a standing allocation can go unhonoured, and the
        # completion check. Nothing to return - project_state carries every
        # result the caller (and the rest of the game) reads back.
        self.household.capital -= money
        self.household.total_spend += money
        project_state["spent"] += money
        project_state["cost_left"] = max(0.0, project_state["cost_left"] - money)
        # spent_hours, NOT per. `per` is what was OFFERED, and it is
        # allowed to exceed the hours the project actually had left; the
        # refunds above are capped at spent_hours for exactly that
        # reason, and this line was left uncapped. A sweep of the
        # playtest notes found a project reporting 387.2 effective hours
        # a year for four consecutive years while founder_hours_left sat
        # unchanged at 112.8 - work reported that provably did not
        # happen, about the one resource the whole game is built on.
        project_state["hours_effective_this_year"] = round(max(0.0, spent_hours - refunded), 1)
        # Accumulated into hours_effective_total by the caller, _step_progress,
        # which sums this project's own returned effective hours into the
        # year's running total - see the return at the end of this method.
        # THE SECOND WAY A DIRECTIVE GOES UNHONOURED: OFFERED, THEN
        # HANDED BACK. Unlike the check above this one, it must NOT
        # fire just because spent_hours fell short of `per` - a
        # project a few hours from finished is offered a whole
        # year's pace and only needs a sliver of it, which is not a
        # shortage of anything, it is the project ending. Gated on
        # why_underfunded/short_of_trade actually being SET this
        # year - fields only the money and trade-shortage branches
        # above ever write - so this can only ever name a real
        # shortfall, never mistake "it finished" for one.
        if _dir_hours and _dir_hours > 0:
            _inner_gap = project_state["hours_offered_this_year"] - project_state["hours_effective_this_year"]
            # DEEP ARREARS ALREADY GETS ITS OWN LINE, BELOW - "IN
            # ARREARS: ... did almost nothing this year" - and it is
            # the sharper warning of the two. Saying the same
            # shortfall twice in two different voices is not
            # clearer, it is just noise; this fires only for the
            # money-short case arrears does NOT already cover (the
            # purse-can-only-absorb-so-much-a-year pace, which is
            # real money trouble without capital actually being
            # negative).
            if _inner_gap > 1.0 and project_state.get("why_underfunded") and self.household.capital >= 0:
                _directed_hours_unused.append(
                    (node_id, round(_inner_gap, 0), project_state["why_underfunded"]))
            elif _inner_gap > 1.0 and project_state.get("short_of_trade"):
                _directed_hours_unused.append((node_id, round(_inner_gap, 0),
                    "trade hours already booked: " + ", ".join(
                        sorted(project_state["short_of_trade"])[:2])))
        # Count it HERE, after the hired-hours scaling and the
        # affordability clamp, not before them: accumulating the notional
        # figure instead would make project_spend_last_year disagree with
        # the actual capital movement.
        self.household._spend_this_year = self.household._spend_this_year + money
        # calendar_floor(node_id), NOT a second copy of this formula -
        # expected_calendar_years (projects.py) needs the identical
        # figure to project retries honestly, and a rule living in
        # two places is how this kind of arithmetic drifts apart.
        floor = self.calendar_floor(node_id)
        # THE BILL HAS TO BE PAID. Hours done and years elapsed are not
        # enough; if the money never arrived, the thing was never built.
        # HALF AN HOUR IS NOTHING LEFT TO DO: the give-back hands back a
        # fraction of what was offered, so on a throttled project ph_left
        # decays geometrically towards zero and never exactly reaches it -
        # a project could otherwise sit at some vanishingly small residual,
        # bill paid, complete in every practical sense except an exact
        # comparison. The bill already has this exact fix and this exact
        # reason (see `money` just above, and cost_left <= 0.5 on the same
        # line); hours need it too.
        if project_state["ph_left"] < 0.5:
            project_state["ph_left"] = 0.0
        if project_state["ph_left"] <= 0 and project_state["yrs"] >= floor and project_state["cost_left"] <= 0.5:
            self._complete(node_id)
        elif project_state["ph_left"] <= 0 and project_state["yrs"] >= floor and project_state["cost_left"] > 0.5:
            project_state["waiting_on_money"] = True

    def _step_progress(self, pool, hired_left):
        # 5. progress. Director hours go to the HIGHEST-PRIORITY active projects
        #    first, not spread evenly: a director who gives every project equal
        #    attention finishes nothing, which is a real failure mode but not the
        #    one we are trying to model here.
        #
        # ONLY THE HANDFUL OF KEYS active_sorted ACTUALLY NEEDS, NOT EVERY
        # NODE IN THE TREE: a bare `{k: i for i, k in enumerate(self.order)}`
        # would build a fresh 2,849-entry dict from scratch every single
        # year to answer `rank.get(k, 9999)` for the at most a few dozen
        # keys in self.household.active. Nothing below reads `rank` for any
        # node NOT in self.household.active (checked: its only other use is
        # the `_pool_rank` loop variable a few lines further down, an
        # unrelated name), so recording a position for every other one of
        # the ~2,849 nodes would be pure waste.
        # This still walks self.order and cannot skip any of it in the
        # worst case (an active key can be anywhere in `order`), so it is
        # not a complexity win - but it stops paying for ~2,849 dict
        # insertions when only a few dozen are ever read, and exits the
        # walk the moment every active key's position has been found
        # (start_project, in projects.py, moves a project to the FRONT of
        # `order` the instant a human starts it by hand, so active keys
        # skew early there in practice, though the automated 4b loop above
        # does not reorder `order` and gives no such guarantee - the early
        # exit is a bonus, not a requirement of correctness). Recomputed
        # fresh every call: no cache, no staleness risk.
        _active_left = set(self.household.active)
        rank = {}
        if _active_left:
            for i, node_id in enumerate(self.order):
                if node_id in _active_left:
                    rank[node_id] = i
                    _active_left.discard(node_id)
                    if not _active_left:
                        break
        # A STANDING ALLOCATION IS A PROMISE, NOT A PRIORITY BID. Without
        # this, a project the player explicitly told `allocate` to give 500
        # hours a year could still be starved by three higher-`order`
        # undirected projects taking the whole pool first - the exact
        # opposite of what asking for an explicit split means. Every project
        # the player has put a standing instruction on is moved to the
        # FRONT of the queue (still ordered among themselves by the usual
        # priority, so two directed projects do not disagree about which of
        # them goes first); everything without one shares whatever is left
        # exactly as it always has, by the same `order`-based priority. A
        # player who never calls `allocate` has an empty hour_allocations,
        # every project sorts into the same single undirected bucket it
        # always did, and this line changes nothing for them.
        active_sorted = sorted(
            self.household.active,
            key=lambda k: (0 if self.household.hour_allocations.get(k, 0.0) > 0 else 1,
                           rank.get(k, 9999)))
        remaining = pool
        self.household.trade_hours_used = {}
        # Summed as the loop runs, not re-read from self.household.active afterwards,
        # because a project that completes THIS year is popped from
        # self.household.active before we would get to it. See the hours_this_year
        # summary this feeds, below the loop.
        hours_effective_total = 0.0
        # NAMED, NOT JUST STORED ON THE PROJECT: `why_underfunded` (set below,
        # in the arrears branch) answers "why is this stalled" only when a
        # player thinks to ask `why` or `portfolio`, which is not the same
        # as announcing it. Founder-hours are the one resource that never
        # banks: a year of them lost to arrears and never
        # announced is the least fair thing a status screen can leave out.
        # Collected here and logged once, after the loop, so a step that
        # starves three projects at once gets one clear line, not three.
        _arrears_hours_lost = []
        # AN ALLOCATION THE PLAYER EXPLICITLY ASKED FOR, AND DID NOT GET.
        # hour_allocations is a promise the player made about their OWN one
        # resource that never banks; silently handing back less than it
        # asked for - because the project's own pace, its trade, or its
        # money was the real ceiling, not the founder's hours - is the same
        # unfairness the arrears line above exists to stop, aimed at a
        # player who took the extra step of directing their hours on
        # purpose. Collected here, per project, and logged once below.
        _directed_hours_unused = []
        # WHY A PROJECT IS GETTING THE SHARE IT IS GETTING, STORED HERE AND
        # NOWHERE ELSE: the only honest way to explain a project's share of
        # this year's directed hours is to read the numbers this loop
        # actually used, never to guess at them again from outside.
        # pool_total/active_count
        # are the same for every project processed this step; rank and
        # remaining_before are this project's own position in the queue and
        # what was left of the pool when its own turn came. _agent_state and
        # `portfolio` (protocol.py) read these fields back verbatim - they do
        # not, and must not, recompute a share that could then disagree with
        # what this loop actually handed out.
        _pool_total_this_year = pool
        _pool_active_count_this_year = len(active_sorted)
        for _pool_rank, node_id in enumerate(active_sorted, start=1):
            remaining, hired_left, _effective = self._step_progress_project(
                node_id, _pool_rank, _pool_total_this_year, _pool_active_count_this_year,
                remaining, hired_left, _arrears_hours_lost, _directed_hours_unused)
            hours_effective_total += _effective
        # ARREARS COSTS YOU THE YEAR'S HOURS, NOT JUST THE MONEY - SAY SO:
        # a project sitting at "did almost nothing" with no explanation on
        # the turn itself leaves founder-hours lost to arrears
        # undiscoverable except by several turns of confusion. Founder-hours
        # are the one resource in this whole model that never banks (see step 5b and
        # `state`'s free_hours_going_unused): a year of them lost silently is
        # worse than a year of money lost, because money can be earned back
        # on the same footing next year and this cannot be earned back at
        # all. Named per project, so 'why <id>' and this line never disagree
        # about which project or how much.
        if _arrears_hours_lost:
            _total_lost = sum(hours for _, hours in _arrears_hours_lost)
            _names = ", ".join("%s (%s hr)" % (node_id, "{:,.0f}".format(hours))
                                for node_id, hours in _arrears_hours_lost)
            self.household.log.append((self.year, "IN ARREARS: %s founder-hours meant for %s did "
                                 "almost nothing this year, on top of the money "
                                 "- that time does not come back, arrears or not. "
                                 "'work' sells idle hours for wages instead of "
                                 "losing them here; clearing the arrears is what "
                                 "stops it happening again"
                             % ("{:,.0f}".format(_total_lost), _names)))

        # A STANDING ALLOCATION THE PLAYER GAVE, AND DID NOT GET - SAID, NOT
        # LEFT FOR THEM TO NOTICE. `allocate` is a promise about the one
        # resource that never banks; silently falling short of it is the
        # same unfairness the arrears line above exists to stop, aimed at a
        # player who took the extra step of directing their hours on
        # purpose rather than leaving the split to priority order. Sorted
        # by id for a deterministic order across runs with the same seed -
        # several projects can be cut short in the same year.
        if _directed_hours_unused:
            for _node_id, _hr, _why in sorted(_directed_hours_unused):
                self.household.log.append((self.year, "DIRECTED HOURS UNUSED: you allocated hours "
                                     "to %s this year that it could not use - "
                                     "%s of them went begging because %s. "
                                     "'portfolio' shows the rest; 'allocate' "
                                     "changes or clears the standing order"
                                 % (self.nodes[_node_id]["name"],
                                    "{:,.0f}".format(_hr), _why)))

        # Snapshot BEFORE 5b spends more of `remaining` on wage work: otherwise
        # offered_to_projects below double-counts wage hours as though they had
        # been offered to projects too, since 5b draws from the same pool.
        remaining_after_projects = remaining
        return remaining, remaining_after_projects, hours_effective_total

    def _step_wage_fallback(self, remaining):
        # 5b. IF THERE IS NO WORK AND NO MONEY, TAKE A JOB. A man who arrives
        #     with four hundred denarii and a lens does not sit watching his
        #     savings run out; he teaches, or writes, or sets bones for money. It
        #     is in the protocol as `work` for a player and the optimizer had no
        #     equivalent, so a single bad year in the opening decade could end a
        #     run: one Rome seed earned four technologies in five hundred years
        #     because a fire in 103 took a fifth of everything it had.
        if (not self.manual and remaining > self.WAGE_FALLBACK_MIN_HOURS
                and (self.household.capital < self.living_cost() * self.WAGE_FALLBACK_LIVING_COST_YEARS
                     or not self.household.active)):
            trade = ("scholar" if self.effective_scholars() >= 1 else "scribe")
            hours = min(remaining, self.WAGE_FALLBACK_MAX_HOURS)
            # ONLY IF IT PAYS BETTER THAN THE PRACTICE IT DISPLACES. Wage hours
            # now cost you the share of your practice they were sold out of
            # (see practice_attention), and without this check the optimizer
            # went on taking a scribe's wage at the price of a physician's fee
            # and lost Rome a sixth of its runs. A man with a practice does not
            # go and copy documents for less than the practice earns; that is
            # the whole reason `work` is the thing you do BEFORE you have one.
            # NOT `pool`: that name already holds the year's project budget,
            # computed at 4b. Reusing it here would overwrite it, so
            # hours_this_year would then report "offered_to_projects"
            # against the WHOLE year instead of against the project budget,
            # letting a year's hours add up to more than what was actually
            # available.
            year_hours = max(1.0, self.director_pool())
            practice_lost = self.revenue() * (hours / year_hours) * (
                1.0 if self.practice_attention() > 0 else 0.0)
            rate = (self.annual_wage(trade) / self.HOURS_PER_PERSON_YEAR
                    * (1.0 + min(self.WAGE_REPUTATION_BONUS_CAP,
                                 self.household.reputation / self.WAGE_REPUTATION_BONUS_SCALE)))
            if hours * rate > practice_lost:
                _, err = self.work_for_wages(trade, hours)
                # Kept in step with `remaining` so hours_this_year (below) does
                # not count hours sold for wages here as still unused.
                if err is None:
                    remaining -= hours
        return remaining

    def _step_reputation(self, pool, remaining, remaining_after_projects, hours_effective_total):
        # 6. reputation, familiarity, protection, scandal
        #
        # Reputation DECAYS TOWARD WHAT YOU ARE ACTUALLY KNOWN FOR, not toward
        # zero: a physician with a practice, a school and a written corpus
        # does not become a man nobody has heard of because thirty quiet
        # years passed. What fades is novelty; what remains is the work.
        floor = self.standing_floor()
        self.household.reputation = floor + (self.household.reputation - floor) * self.REPUTATION_DECAY_TOWARD_FLOOR
        # ADAPTATION. Every year the world has known you, and every visible thing
        # you have already done, makes the next one less astonishing.
        pub = sum(1 for node_id in self.household.done
                  if set(self.nodes[node_id].get("traits", [])) & {"spectacle", "inexplicable"})
        self.household.familiarity = min(
            self.FAMILIARITY_CEILING,
            1.0 - math.exp(-self.value_weights["adaptation_rate"]
                           * (self.FAMILIARITY_PUBLICATION_WEIGHT * pub
                              + self.FAMILIARITY_TENURE_WEIGHT * (self.year - 100))))
        # WHERE THE YEAR'S HOURS WENT: captured here, before the tallies
        # below reset for the next year, the same way spend_last_year
        # already captures the year's spending, so a player can see the
        # breakdown as `hours_this_year` in `state` rather than only a
        # final hours-left figure with no way to tell where the rest went.
        self.hours_this_year = {
            "available": round(self.director_pool(), 1),
            "wage_work": round(getattr(self.household, "wage_hours_this_year", 0.0), 1),
            "teaching": round(self.household.teaching_hours_this_year, 1),
            "offered_to_projects": round(max(0.0, pool - remaining_after_projects), 1),
            # OFFERED is what projects were given a shot at; EFFECTIVE is what
            # actually reduced their founder_hours_left. The gap between the
            # two is hours that went in and came straight back out again
            # because a trade or the money to pay for it fell short that year
            # - see hours_offered_this_year / hours_effective_this_year on
            # each project in `active`, and underfunded_this_year.
            "effective_on_projects": round(hours_effective_total, 1),
            "unused": round(max(0.0, remaining), 1),
        }
        # Reset AFTER the progress pass above, which is where the hours you sold
        # are subtracted from the hours you have left to direct.
        self.household.wage_hours_this_year = 0.0
        # Contracted work is bought for a year and expires with it: hours you
        # paid a shop for in 142 are not still sitting there in 143.
        self.household.contract_hours = {}
        self.household.teaching_hours_this_year = 0.0
        self.household.spend_last_year = self.household._spend_this_year
        self.household._spend_this_year = 0.0
        # Sellers restock, so the pressure your buying put on the market fades.
        self.household.market_pressure = max(0.0, self.household.market_pressure * self.MARKET_PRESSURE_DECAY - self.MARKET_PRESSURE_ANNUAL_FADE)
        # WARN BEFORE IT KILLS YOU: eminence can end the run outright on a
        # roll with no escalation and nothing in the log ever mentioning
        # it beforehand. It is the one hazard that cannot be bribed away,
        # so the player must be told it is closing in.
        _danger = self.cfg["eminence_danger"]
        if self.household.eminence > _danger * 0.75:
            _said = self.household._said_eminence
            _band = int(self.household.eminence / max(1.0, _danger * 0.15))
            if _band > _said:
                self.household._said_eminence = _band
                self.household.log.append((self.year, "YOU ARE BECOMING CONSPICUOUS: eminence %.0f "
                                     "against a danger line of %.0f. This is the "
                                     "one thing no patron and no bribe protects "
                                     "you from, and it grows with reputation and "
                                     "visible wealth. A wide, dispersed "
                                     "institution is what survives you"
                                 % (self.household.eminence, _danger)))
        self.update_protection()
        # THE STATE NOTICES YOU. Requisition, the pressed office, a demand
        # for military supply, and the tail confiscation risk at the top of
        # the same scale - see SocietyMixin's own "THE STATE NOTICES YOU"
        # section (society.py) for the whole mechanic. Run after
        # update_protection() so this year's patronage and office standing
        # are what requisition/confiscation actually bargain against, and
        # before scandal/eminence below so a confiscation this mechanic
        # causes and the eminence-driven one further down are never
        # resolved in the same breath as two unrelated draws on the same
        # stale numbers.
        self._state_pressure(self.year)
        self.household.scandal *= self.SCANDAL_DECAY_RATE
        # Eminence accumulates in a SEPARATE pool, because bribery does not
        # touch it. You can buy a magistrate, an accuser and a jury. You cannot
        # buy an emperor's judgement that you have grown too large, and the
        # attempt is itself evidence against you.
        self.household.eminence = self.household.eminence * self.EMINENCE_DECAY_RATE + self.prominence_hazard()
        # you can buy your way out of trouble, and a sane player does
        if (self.household.scandal > self.AUTO_BRIBE_SCANDAL_THRESHOLD
                and self.household.capital > self.AUTO_BRIBE_CAPITAL_THRESHOLD
                and self.policy.get("auto_bribe", not self.manual)):
            spend = min(self.household.capital * self.AUTO_BRIBE_CAPITAL_SHARE,
                        self.household.scandal * self.AUTO_BRIBE_COST_PER_SCANDAL_POINT)
            self.household.capital -= spend
            self.household.bribes_ytd = self.BRIBES_YTD_DECAY * self.household.bribes_ytd + spend
            self.household.scandal -= (spend / self.BRIBE_SCANDAL_REDUCTION_SCALE
                                       * self.value_weights["bribability"])
        else:
            self.household.bribes_ytd *= self.BRIBES_YTD_DECAY
        self.household.scandal = max(0.0, self.household.scandal)
        # WARN, THE WAY EMINENCE DOES: denunciation ends the run outright,
        # and a scandal figure with no threshold, no probability and no
        # note is not legible the way eminence's own warning already is.
        # Two hazards of the same shape must both be legible.
        _sd = self.cfg["suspicion_danger"]
        if self.household.scandal > _sd * 0.75:
            _band = int(self.household.scandal / max(1.0, _sd * 0.15))
            if _band > int(getattr(self.household, "_said_scandal", 0)):
                self.household._said_scandal = _band
                self.household.log.append((self.year, "YOU ARE BEING TALKED ABOUT: scandal %.0f "
                                     "against a line of %.0f. Past it you may be "
                                     "denounced, and that ends the run - about "
                                     "%.0f%% a year at this level. 'bribe' buys "
                                     "advocacy and piety; it falls a tenth a "
                                     "year on its own"
                                 % (self.household.scandal, _sd,
                                    PERCENT_SCALE * max(0.0, (self.household.scandal - _sd) / self.SCANDAL_HAZARD_SCALE))))
        elif self.household.scandal < _sd * 0.5:
            self.household._said_scandal = 0
        if self.events and self.household.scandal > self.cfg["suspicion_danger"]:
            probability = (self.household.scandal - self.cfg["suspicion_danger"]) / self.SCANDAL_HAZARD_SCALE
            if self.rng.random() < probability:
                self._catastrophe("denounced: %s" % ("as a sorcerer"
                                  if self.value_weights["w_magic_fear"] > 0.5
                                                     else "as a subversive"))
        # The eminence hazard is separate and unbribable. Its usual outcome is a
        # bad year rather than a death: a confiscation, a patron destroyed in
        # someone else's quarrel, a forced withdrawal from public life.
        if self.events and self.household.eminence > self.cfg["eminence_danger"]:
            probability = (self.household.eminence - self.cfg["eminence_danger"]) / self.EMINENCE_HAZARD_SCALE
            if self.rng.random() < probability:
                roll = self.rng.random()
                if roll < self.EMINENCE_OUTCOME_CONFISCATION_SHARE:
                    take = self.household.capital * self.EMINENCE_CONFISCATION_CAPITAL_LOSS
                    self.household.capital -= take
                    self.household.reputation = max(0.0, self.household.reputation - self.EMINENCE_CONFISCATION_REPUTATION_LOSS)
                    self.household.eminence *= self.EMINENCE_CONFISCATION_RETENTION
                    self.household.log.append((self.year, "PROMINENCE: property confiscated, %d den lost, "
                                         "and you withdraw from public life for a while" % take))
                elif roll < (self.EMINENCE_OUTCOME_CONFISCATION_SHARE + self.EMINENCE_OUTCOME_PATRON_LOST_SHARE):
                    for pat in ("patron_imperial", "patron_senatorial"):
                        if pat in self.household.done:
                            self.household.done.discard(pat)
                            self._done_changed()
                            self.household.log.append((self.year, "PROMINENCE: your patron is destroyed in "
                                                 "someone else's quarrel and you lose %s" % pat))
                            break
                    self.household.eminence *= self.EMINENCE_PATRON_LOSS_RETENTION
                    self.household.reputation = max(0.0, self.household.reputation - self.EMINENCE_PATRON_LOSS_REPUTATION_LOSS)
                else:
                    self._catastrophe("too eminent: brought down not for what you built "
                                      "but for how large you had become")

    def _step_bondage(self):
        # 6b. serving out a debt. The hours you owe go to the creditor and the
        #     debt falls; when it is done you are free, and you keep everything
        #     you know.
        if self.household.bondage_years_left > 0:
            self.household.bondage_years_left -= 1
            paid = self.cfg["founder_hours_per_year"] * self.BONDAGE_LABOUR_SHARE *\
                (WAGES.get("labourer", self.BONDAGE_LABOURER_WAGE_DEFAULT) * self.BONDAGE_WAGE_MARKUP) * self.wage_index * self.price_index
            self.household.bondage_debt = max(0.0, self.household.bondage_debt - paid)
            if self.household.bondage_debt <= 0 and self.household.bondage_years_left > 0:
                self.household.bondage_years_left = 0     # paid early
            if self.household.bondage_years_left <= 0:
                self.household.bondage_years_left = 0.0
                self.household.bondage_debt = 0.0
                self.household.log.append((self.year, "your term is served and the debt is discharged; "
                                     "you are your own man again"))

    def _step_founder_mortality(self):
        # 7. founder mortality
        if self.founder_alive:
            self.life_left -= 1
            if self.running("sanitation_antisepsis"):
                self.life_left += self.SANITATION_LIFE_EXTENSION_YEARS      # you at least do not die of a septic cut
            if self.life_left <= 0:
                self.founder_alive = False
                # SAY WHAT IT MEANS, not only that it happened: the engine is
                # not in fact silent about the consequence of the founder's
                # death - deputies carry the work, and with none the
                # programme dissolves over twelve years - but that has to
                # be said here, in the same line, not left for the player
                # to work out on their own.
                _dep = self.household.directors_extra
                self.household.log.append((self.year, "THE FOUNDER DIES, aged about %d. %s"
                                 % (self.cfg["founder_arrival_age"] + self.year
                                    - self.cfg["start_year"],
                                    ("Your %.1f deputies direct the work in your "
                                     "name and the programme goes on without you: "
                                     "that is what training them was for."
                                     % _dep) if _dep >= 0.5 else
                                    "You trained no deputy, so there is nobody to "
                                    "direct anything. Nothing that needs your "
                                    "hours can ever be begun again, and what you "
                                    "built will be forgotten over the next twelve "
                                    "years unless a deputy appears. This run is "
                                    "effectively over; 'state' shows how far you "
                                    "got.")))
        # a programme with no director is not paused, it is dissolving
        if not self.founder_alive and self.household.directors_extra < 0.5:
            self.household.stalled += 1
            if self.household.stalled >= self.DISSOLUTION_YEARS_BEFORE_FORGETTING:
                losable = sorted(node_id for node_id in self.household.done if node_id not in self.household.granted)
                # sorted() matters: self.household.done is a SET, and a set iterates in an
                # order that depends on PYTHONHASHSEED, so feeding it unsorted to
                # rng.sample made the same --seed give a different answer on every
                # invocation. Every figure this project has reported was, strictly,
                # unreproducible.
                if losable:
                    for node_id in self.rng.sample(losable, max(1, len(losable) // self.DISSOLUTION_FORGET_FRACTION_DIVISOR)):
                        self.household.operating.discard(node_id)
                        self.household.done.discard(node_id)
                        self._done_changed()
            # COUNT IT DOWN WHERE THE PLAYER CAN SEE IT: twelve years of a
            # dissolving programme passing with nothing said but the
            # shedding itself would read as merely unlucky rather than as
            # the run actually being finished.
            if self.household.stalled in (3, 6, 9, 11):
                self.household.log.append((self.year, "THE PROGRAMME IS DISSOLVING: %d year(s) "
                                     "since the founder died with no deputy to "
                                     "take over. What you built is being "
                                     "forgotten. The run ends at twelve."
                                 % self.household.stalled))
            if self.household.stalled >= self.DISSOLUTION_YEARS_UNTIL_END:
                self._catastrophe("the founder died without training successors; "
                                  "the school dispersed and the work was forgotten")
        else:
            self.household.stalled = 0
