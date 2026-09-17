"""Money, materials, and the works that consume both.

Split out of simulator.py, which had grown to 5,600 lines. These are
methods of Sim; they are a mixin only so that they can live in a file of
their own. Behaviour is unchanged and verified byte-identical.
"""
import collections, json, math, os, random
from collections import defaultdict

from .data import *          # the shared tables and loaders
from .data import (ANNUAL_WAGE, WAGES, hard_pre, trade_family)
from . import commodities as _commod


class _InvalidatingSet(set):
    """A set that calls `on_change` after every mutation, with no exceptions.

    Backs `Sim.operating` (see the `operating` property on `EconomyMixin`
    below) so that a cache keyed off operating's exact membership -
    `capability_factor()`'s - cannot go stale, no matter which of the nine
    call sites across core.py/projects.py/economy.py/society.py adds to or
    discards from it, and without asking any of them to remember a second
    line. The `done`/`_done_changed()` convention this project already has
    relies on every one of ITS mutation sites remembering to call
    `_done_changed()` by hand; that is a real convention and it has held,
    but a second one just like it - one more rule written down at every call
    site instead of enforced at one - is exactly the shape that has already
    produced three drifted-apart bugs elsewhere in this codebase today. This
    set makes the equivalent mistake impossible for `operating` specifically:
    there is only one `.add`, only one `.discard`, and they are these. It is
    the same reasoning that made `revealed` (engine/fog.py) a property rather
    than a plain attribute, extended to a set instead of a ratchet.

    Every mutating method a plain `set` exposes is overridden so that
    swapping this in for `set()` changes nothing observable except that
    `on_change` now fires. Non-mutating methods (`copy`, `union`, membership
    tests, iteration, `len`) are inherited unchanged.
    """

    def __init__(self, iterable=(), on_change=None):
        set.__init__(self, iterable)
        self._on_change = on_change

    def _fire(self):
        if self._on_change is not None:
            self._on_change()

    def add(self, item):
        if item not in self:
            set.add(self, item)
            self._fire()

    def discard(self, item):
        if item in self:
            set.discard(self, item)
            self._fire()

    def remove(self, item):
        set.remove(self, item)      # raises KeyError, same as a plain set
        self._fire()

    def pop(self):
        item = set.pop(self)
        self._fire()
        return item

    def clear(self):
        if self:
            set.clear(self)
            self._fire()

    def update(self, *others):
        before = len(self)
        set.update(self, *others)
        if len(self) != before:
            self._fire()

    def difference_update(self, *others):
        before = len(self)
        set.difference_update(self, *others)
        if len(self) != before:
            self._fire()

    def intersection_update(self, *others):
        before = len(self)
        set.intersection_update(self, *others)
        if len(self) != before:
            self._fire()

    def symmetric_difference_update(self, other):
        before = frozenset(self)
        set.symmetric_difference_update(self, other)
        if frozenset(self) != before:
            self._fire()

    def __ior__(self, other):
        before = len(self)
        result = set.__ior__(self, other)
        if len(self) != before:
            self._fire()
        return result

    def __iand__(self, other):
        before = len(self)
        result = set.__iand__(self, other)
        if len(self) != before:
            self._fire()
        return result

    def __isub__(self, other):
        before = len(self)
        result = set.__isub__(self, other)
        if len(self) != before:
            self._fire()
        return result

    def __ixor__(self, other):
        before = frozenset(self)
        result = set.__ixor__(self, other)
        if frozenset(self) != before:
            self._fire()
        return result


class EconomyMixin:
    def standing_floor(self):
        """The reputation you keep for what you have built, whatever else happens.

        Novelty fades. A corpus in three libraries, a school with students and a
        senator who will receive you do not.
        """
        earned = len(self.done) - len(self.granted)
        f = 0.5 + 0.55 * math.sqrt(max(0, earned))
        if self.running("corpus_written"):     f += 3.0
        if self.running("corpus_dispersed"):   f += 6.0
        # SQRT, NOT LINEAR. A third schoolhouse does not make you three times
        # as well known as the first one did - the standing a school buys is
        # mostly in having founded one at all, not in its size - so further
        # units add less each time, the same curve `earned` above already
        # uses for the same reason.
        if self.running("school_founded"):
            f += 4.0 * self.institution_units("school_founded") ** 0.5
        if self.running("academy_network"):
            f += 10.0 * self.institution_units("academy_network") ** 0.5
        if self.running("patron_senatorial"):  f += 3.0
        if self.running("patron_imperial"):    f += 8.0
        if self.running("identity_cover"):     f += 1.0
        # Scandal is the one thing that eats into standing rather than sitting
        # alongside it: being notorious is not the same as being unknown.
        return max(0.0, f - 0.5 * self.scandal)

    def rep_factor(self):
        """How much easier reputation makes everything. 1.0 at zero reputation."""
        return 1.0 + self.reputation / 120.0

    def economy_index(self):
        """Diffused technology enriches the whole Empire, not only your workshop.

        Britain's industrialisation paid for itself. So does yours: each heavy
        technology that spreads raises output everywhere, which raises what the
        State and the market can pay you. Without this term the model says an
        industrial revolution is unaffordable, which is false, and the reason it
        is false is that the revolution funds itself.
        """
        diffused = len(self.done - self.granted)
        e = 1.0 + 0.055 * diffused
        if not self.running("corpus_dispersed"):
            e = 1.0 + 0.030 * diffused      # knowledge locked in one workshop spreads slowly
        return e

    def state_funding(self):
        if not self.running("patron_imperial"):
            return 0.0
        return (2500.0 * self.economy * self.state_capacity * self.pop_scale ** 0.4
                * (1.0 + max(0.0, self.gov) / 25.0) * self.rep_factor())

    def credit_limit(self, _rev=None, _upkeep=None):
        """How far into arrears anyone will actually let you go.

        Unbounded debt is an accounting fiction, and it produced the single worst
        outcome in the playtests: testers sat at minus 200,000 denarii for two
        and three CENTURIES, making no progress, with the clock running. That is
        not a hard game, it is a game that has stopped and not said so.

        In reality credit stops long before that, and the moment it stops you are
        merely poor. Poor is recoverable: you climbed out of it the first time
        starting from 400 denarii and a physician's practice, and nothing has
        taken that practice away from you.

        What you can borrow depends on who will stand behind you, which is the
        same currency as everything else in this model.

        `_rev`/`_upkeep`: forwarded to living_cost() unchanged - see ITS
        docstring for what they mean and why passing them is safe. `earning`
        just below still always calls revenue_capacity() itself, because
        that is a genuinely different figure (this year's actual
        wage-selling zeroed out - see revenue_capacity's own docstring),
        never the same call `_rev` would have been computed with.
        """
        # What a STRANGER can borrow is almost nothing, which is the reviewer's
        # question and the right answer. You have walked into a town with no
        # name, no land and no one to vouch for you. The old floor of 2,000
        # denarii handed a newcomer roughly two years of living expenses on
        # nothing but arrival. Credit here is what someone will advance against
        # your income and the people who will stand behind you.
        # WHAT YOU NORMALLY EARN, not what this particular year came to. A
        # lender looks at your practice and your concerns; he does not cut your
        # line because you spent this year working for somebody else. Without
        # that, `work scholar 2000` - which sells the founder's whole year and
        # so takes the practice's income to nothing for it - collapsed the
        # credit line from 1,397 to 210 in the middle of a step, and the
        # project spending already committed against the old line breached the
        # new one. A break tester cleared their debt in full with exactly that
        # command and was answered, the very next year, with "INSOLVENCY
        # SETTLED ... reputation -6.6": owing 628 was safe and owing nothing
        # was ruin.
        earning = self.revenue_capacity()
        base = earning * 0.5
        if self.running("identity_cover"):     base += 400.0
        if self.running("patron_local"):       base += 3000.0
        if self.running("patron_senatorial"):  base += 15000.0
        if self.running("patron_imperial"):    base += 60000.0
        # LINEAR, NOT SQRT: a licensed collegium's credit is collateral, not
        # fame, and three of them really do stand behind three times the
        # borrowing the first one did.
        if self.running("collegium_licensed"):
            base += 4000.0 * self.institution_units("collegium_licensed")
        if self.running("endowment_land"):     base += 30000.0      # real collateral
        base += max(0.0, self.reputation) * 250.0
        base += self.forest_ha * 120.0                           # also collateral
        # A FLOOR of one year's running costs, because everyone everywhere has
        # always been able to run a tab. The baker, the landlord and the smith
        # all carry you for a season; what they will not do is advance you cash.
        # Without this floor a household whose rent exceeded its credit line by
        # a few denarii was declared insolvent, settled, and then declared
        # insolvent again the next year, for ever.
        # ONE upkeep() CALL, NOT TWO (and _rev, if the caller already had
        # one, is reused rather than making living_cost() take its own
        # third). Nothing between here and living_cost()'s own return
        # assigns to self - revenue_capacity() just above already restored
        # wage_hours_this_year before returning (see its own try/finally) -
        # so upkeep()/revenue() cannot answer differently a second time, and
        # living_cost() takes both as `_upkeep`/`_rev` to skip its own copy
        # of the same calls rather than silently repeating them. See
        # living_cost's own docstring on why those arguments exist.
        up = self.upkeep() if _upkeep is None else _upkeep
        floor = self.living_cost(_rev=_rev, _upkeep=up) + up * 0.5
        # AND BOUNDED BY WHAT YOU CAN SERVICE. A senatorial patron adds fifteen
        # thousand to the line whoever you are, so a household with 1,800 of
        # revenue could owe 23,000 - about 1,500 a year in interest against
        # 1,800 of income. That is not a credit line, it is a trap with a
        # patron's name on it, and every Rome run walked into it: five hundred
        # years in arrears, the debt compounding faster than the practice could
        # ever repay, with the optimizer and the player equally helpless.
        #
        # A patron will stand behind you; no lender advances more than your
        # income can carry, however grand your friends. Five years of turnover
        # on top of the running tab everyone gets - turnover and not margin,
        # because much of what this model calls living costs is discretionary
        # display a ruined man stops paying, and a lender knows it. Five is
        # chosen to leave the OPENING where it was: a founder with a practice
        # and nothing else could always just reach a respectable cover
        # identity, and that is the first real decision in the game.
        serviceable = floor + max(0.0, earning) * 5.0
        return max(min(base, serviceable), floor) * self.price_index

    def committed_spend(self):
        """What is still owed, in total, across every project in hand at once.

        Not any one project's own remaining bill - the SUM across all of
        `active`, because they all draw on the same purse and the same
        credit line. Half of the answer to "can I afford this", the other
        half being funding_capacity() just below: a project's own `why`/
        `start` forecast (protocol.py's "on_credit" block) already answers
        whether THAT ONE project can be financed, honestly and correctly,
        in isolation. It says nothing about what else is already in hand,
        and every playtest of this opening found the same trap: two or
        three foundation techs, each individually affordable and each
        correctly priced on its own screen, stacked into a debt spiral
        that nothing added up until the interest was already compounding.
        """
        return sum(st.get("cost_left") or 0.0 for st in self.active.values())

    def funding_capacity(self):
        """What you can actually expect to have to spend on projects.

        Cash in hand, half the credit line (the rest stays in reserve
        against ordinary running costs, the same half `spending_power`
        holds back for anything that is not itself a `start`), and about
        five years of whatever surplus the standing income can add once
        fixed costs and today's arrears interest are paid. See
        committed_spend() for what this is compared against: the aggregate
        question is committed_spend() <= funding_capacity(), not any
        single project's own cost against this number alone.

        This formula already existed, doing this exact job, for the
        un-manual director's own start heuristic (see step(), core.py) -
        added there because the naive "three times capital plus six years
        of gross revenue" heuristic let the optimizer commit to more than
        a household could ever fund, the same mistake every human
        playtester made once at the keyboard. Factored out here so the
        player-facing aggregate warning (protocol.py's `start` handler)
        uses the identical number rather than a second formula that could
        quietly drift from it - one rule in two places is how a game like
        this accumulates its worst bugs.

        revenue()/upkeep() computed ONCE, here, and handed to both
        living_cost() and credit_limit() (which itself forwards them to its
        own living_cost() call) as `_rev`/`_upkeep`, rather than the five
        further calls between them this used to make for the same two
        numbers - see living_cost's own docstring for why reusing them is
        safe: nothing in this whole call graph assigns to self anywhere.
        """
        rev = self.revenue()
        up = self.upkeep()
        fixed = (up + self.living_cost(_rev=rev, _upkeep=up)
                 + self.mine_operating_cost()
                 + max(0.0, -self.capital) * self.debt_interest_rate())
        return (max(0.0, self.capital)
                + self.credit_limit(_rev=rev, _upkeep=up) * 0.5
                + max(0.0, rev - fixed) * 5.0)

    def shed_loss_makers(self, yr):
        """In arrears, stop maintaining anything that costs more than it returns.

        This is what finally answers the reviewer's objection, which was the right
        one: if you can build an enterprise starting from 400 denarii and a
        physician's practice, you must be able to rebuild after ruin, and an
        immortal founder should never spend two centuries making no progress.

        The earlier fixes bounded the DEBT but not the BLEEDING. A ruined run
        still held works whose upkeep exceeded their revenue, so net income sat
        near zero for ever and the recovery took centuries. Nobody does that. You
        let the loss-makers go the same year you notice, and then your income is
        your practice again, which is what you started with and is enough.
        """
        if self.capital >= 0:
            return
        shed = []
        while True:
            net = (self.revenue() - self.upkeep() - self.living_cost()
                   - self.mine_operating_cost())
            if net >= 0:
                break
            worst = None
            # THE SCHOOL AND THE PATRON GO LAST. Every one of these loses money
            # by construction - a school takes 2,500 a year and returns 800 -
            # and every one of them is what your scholars, your household
            # places and your credit are gated on, so shedding by margin alone
            # picked them FIRST and closed the institution that was paying for
            # everything else. In real ruin you do close the school; you close
            # it after you have closed everything else. Two passes: ordinary
            # loss-makers, then, only if that was not enough, these.
            for _pass in (0, 1):
                # WHAT YOU ARE ACTUALLY PAYING FOR, which since knowing and
                # running became two states is `operating`, not `done`. This
                # scanned every completed node, so in a bad year it would pick
                # a loss-maker that was already shut, unlearn it, and save
                # nothing at all: upkeep follows `operating` and a closed
                # concern was already costing nothing. The player lost the
                # knowledge and kept the deficit.
                for k in sorted(self.operating):
                    n = self.nodes[k]
                    if (n["up"] <= n["rev"] or k in self.granted
                            or self.never_abandon(k)):
                        continue
                    if (k in self.CAPABILITY_INSTITUTIONS) != bool(_pass):
                        continue
                    if worst is None or (n["rev"] - n["up"]) < (self.nodes[worst]["rev"]
                                                               - self.nodes[worst]["up"]):
                        worst = k
                if worst is not None:
                    break
            if worst is None:
                break
            # CLOSE IT, do not unlearn it. Shedding a loss-maker in ruin is
            # shutting the doors, and what that saves is its running cost. The
            # knowledge stays: you cannot forget how a thing works because you
            # could not pay for it this year. (This used to discard it from
            # `done` two lines under a comment saying it did not.)
            self.operating.discard(worst)
            # MOTHBALLED, not merely discarded: this is the plant falling into
            # disrepair, exactly like a deliberate `mothball`, and it must show
            # up the same way - in `state.mothballed`, and NOT back in
            # `available` looking like research you have never done. Before
            # this it was a bare discard, so a repossessed work reappeared
            # indistinguishable from something you had never built, and
            # `restore` (a fraction of the cost) was never offered.
            self.mothballed.add(worst)
            shed.append(worst)
        if shed:
            # NAME THEM. "stopped maintaining 1 works" told a player nothing:
            # not which one, not how to get it back. A tester asked the fair
            # question - how do you understand what you lost, or why an option
            # reappeared, if you were never told its name?
            self.log.append((yr, "in arrears, so closed %d concern%s that cost more "
                                 "than they returned: %s. You still know how; "
                                 "'restore' reopens one when you can pay for it"
                             % (len(shed), "" if len(shed) == 1 else "s",
                                ", ".join(shed))))

    def debt_interest_rate(self):
        """What arrears cost you a year.

        Roman lending was expensive and the legal ceiling of twelve per cent was
        a ceiling on the RESPECTABLE end of it; maritime loans ran far higher
        because the risk was real. A man with no standing borrows from whoever
        will have him and pays for it. Standing is what makes money cheap, which
        is the same rule as everything else in this model: patronage is the
        currency underneath the currency.
        """
        r = 0.12
        if self.running("patron_local"):        r -= 0.015
        if self.running("patron_senatorial"):   r -= 0.03
        if self.running("patron_imperial"):     r -= 0.03
        if self.running("endowment_land"):      r -= 0.02          # secured, not personal
        if self.running("fin_argentarii"):      r -= 0.01          # a banker you know
        r -= min(0.03, max(0.0, self.reputation) / 3000.0)
        return max(0.0, r)

    def charge_interest(self, yr):
        """Arrears accrue. They did not before, which made debt free money."""
        if self.capital >= 0:
            return 0.0
        rate = self.debt_interest_rate()
        owed = -self.capital * rate
        self.capital -= owed
        self.interest_paid = getattr(self, "interest_paid", 0.0) + owed
        if owed > 0 and (getattr(self, "insolvent_years", 0) in (1, 5, 15)):
            self.log.append((yr, "interest on %0.f denarii of arrears at %.1f%% a year"
                                 % (-self.capital, rate * 100)))
        return owed

    def warn_near_the_limit(self, yr):
        """Say it BEFORE the creditors do, while there is still a decision left.

        A play tester watched a recoverable-looking cash dip turn into "CREDIT
        EXHAUSTED: 4 projects halted" and a forty-year dead run, and wrote:
        "`money` shows a credit limit but nothing shows how close to insolvency
        you are." A limit you can only discover by crossing it is not a limit,
        it is an ambush - and everything that would have saved them (stop a
        project, close a loss-maker, let somebody go) was still available the
        year before.
        """
        limit = self.credit_limit()
        if limit <= 0 or self.capital >= 0:
            self._said_near_limit = False
            return
        used = -self.capital / limit
        # PAST IT IS NOT "CLOSE TO" IT, and past it the halting has already
        # happened: a break tester read "CLOSE TO THE LIMIT ... (103%) ... every
        # project in hand is halted" in a year when nothing was halted, because
        # enforce_credit_limit runs immediately after this and had already dealt
        # with it. Warn about what is still ahead of you, not about what has
        # just been done.
        if used >= 1.0:
            self._said_near_limit = True
            return
        if used < 0.7:
            self._said_near_limit = False
            return
        if getattr(self, "_said_near_limit", False):
            return
        self._said_near_limit = True
        self.log.append((yr, "CLOSE TO THE LIMIT: you owe %s of the %s anyone "
                             "here will advance you (%d%%). Past it every "
                             "project in hand is halted unfinished and nobody "
                             "funds new work for some years. 'stop' a project, "
                             "'mothball' a loss-maker or 'fire' somebody while "
                             "it is still your choice"
                         % ("{:,.0f}".format(-self.capital),
                            "{:,.0f}".format(limit), used * 100)))

    def enforce_credit_limit(self, yr):
        """Nobody lends past the limit, so past the limit you simply stop.

        The order matters and is the realistic one: first you stop paying for new
        work, then you let go of what you cannot maintain, and only then, if it is
        still hopeless, your creditors write the rest off and take everything
        that was not nailed down. You are left poor rather than impossibly
        indebted, which is a position you can work out of.
        """
        limit = self.credit_limit()
        if self.capital >= -limit:
            return
        # stop everything in progress: you cannot fund it
        if self.active:
            dropped = sorted(self.active)
            # WHAT YOU PAID IS NOT BURNED. "Halted" means paused to a reader
            # and meant deleted here: a break tester watched 795 denarii and
            # about 800 founder-hours vanish, with scientific_method dying 115
            # denarii short of done and every hour already spent. A half-built
            # thing is still half built when the money runs out; the site does
            # not un-dig itself. What you paid stands to your credit and comes
            # off the bill when you begin again.
            _paid = getattr(self, "paid_towards", None)
            if _paid is None:
                _paid = self.paid_towards = {}
            _kept = 0.0
            for k in dropped:
                st = self.active.pop(k, None)
                if st:
                    _paid[k] = _paid.get(k, 0.0) + max(0.0, st.get("spent", 0.0))
                    _kept += max(0.0, st.get("spent", 0.0))
                self.bountied.discard(k)
            self.credit_frozen_until = yr + 5
            self.log.append((yr, "CREDIT EXHAUSTED: %d project%s stopped, "
                                 "unfinished: %s. The %s denarii already paid "
                                 "stands to your credit and comes off the "
                                 "bill if you begin again. Nobody will fund new "
                                 "work here until %d"
                             % (len(dropped), "" if len(dropped) == 1 else "s",
                                ", ".join(dropped[:4])
                                + (" and others" if len(dropped) > 4 else ""),
                                "{:,.0f}".format(_kept), yr + 5)))
        # let go of what you cannot maintain
        if self.capital < -limit:
            self.mothball_mines()
        if self.capital < -limit:
            # From what you are RUNNING: a creditor cannot seize a thing you
            # merely know how to do, and closing something that was not open
            # saves nobody anything.
            burden = sorted((k for k in self.operating
                             if self.nodes[k]["up"] > self.nodes[k]["rev"]
                             and k not in self.granted
                             and not self.never_abandon(k)),
                            key=lambda k: (self.nodes[k]["rev"] - self.nodes[k]["up"]))
            taken = []
            for k in burden:
                if self.capital >= -limit:
                    break
                # THEY TAKE THE CONCERN, NOT YOUR MEMORY OF HOW IT WORKED.
                # This discarded the node from `done` and left it in
                # `operating`, so afterwards it was simultaneously forgotten
                # and running: `state` said the concern was running, `ventures`
                # billed 200 a year for it, `money` charged nothing, and all
                # four verbs refused it on mutually contradictory grounds -
                # `start` said restore it, `restore` said start it, `open` said
                # you do not know it, `mothball` said you never built it. A
                # weird-play tester reached that state in seven years from a
                # fresh start and could never clear the entry.
                #
                # Closing it is both the fix and the more honest event: what a
                # creditor can carry away is the shop.
                self.operating.discard(k)
                self.capital += self.nodes[k]["up"] * 2.0
                # MOTHBALLED, not merely discarded - see the identical comment
                # in shed_loss_makers. Without this a work creditors took stood
                # indistinguishable from research never begun, and `restore`
                # (a fraction of the cost) was never offered for it.
                self.mothballed.add(k)
                taken.append(k)
            # Only say it if it happened. This line used to fire every year
            # whether or not there was anything left to take, so a run with
            # nothing to lose logged creditors seizing it over and over.
            # NAME THEM, for the same reason shed_loss_makers now does: a
            # player cannot understand what they lost, or why it reappeared
            # mothballed rather than gone, from a bare count.
            if taken:
                self.log.append((yr, "creditors took what they could: %d concerns "
                                     "closed and sold up: %s. You keep the "
                                     "knowledge; reopening means paying for the "
                                     "premises again"
                                     % (len(taken), ", ".join(taken))))
        # And the household goes. This was the missing piece: a tester's run sat
        # pinned at the credit floor making no progress for a century because the
        # upkeep of a household they could no longer feed consumed every denarius
        # of income forever. Nobody keeps four hundred dependants they cannot
        # feed. People are sold or freed and they leave, and the point of modelling
        # it is that shedding them is how you become solvent again.
        if self.capital < -limit and (self.slaves or self.freedmen):
            freed = self.slaves + self.freedmen
            self.manumit(self.slaves)          # you do not sell them on
            self.freedmen = 0
            self.artisans = max(3.0, self.artisans * 0.4)
            self.log.append((yr, "the household disperses: %d people leave, because "
                                 "you can no longer feed them" % freed))

        # DEBT BONDAGE, where the society had it, and worked off, because that is
        # what it mostly was. A tester asked me to reconsider having refused it:
        # "I know a lot of slave debt was also something you worked off, so it
        # wouldn't necessarily be a dead end." That is right, and the general
        # case matters more than the Roman one: Han debt servitude, the Norse
        # debt-thrall and Mexica tlacotin were all terms of service that ended,
        # were redeemable, and in the Mexica case were not heritable. Rome is the
        # exception, not the rule, because nexum was abolished in 326 BC, so Rome
        # carries debt_bondage false and goes straight to the write-off below.
        #
        # In bondage your hours are not your own. That is the whole penalty, and
        # it is a heavy one in a game whose scarcest resource is your hours; but
        # it ends, and it ends sooner if the work is worth something.
        if (self.capital < -limit and self.civ.get("debt_bondage")
                and not self.bondage_years_left):
            term = float(self.civ.get("bondage_years", 10))
            self.bondage_years_left = term
            self.bondage_debt = -self.capital
            self.capital = 0.0
            self.log.append((yr, "BONDAGE: you cannot pay, and you enter service for "
                                 "your debt. For about %d years most of your hours "
                                 "belong to someone else. It is not the end: it is "
                                 "worked off, and then you are free again" % term))
            return

        # and the rest is written off. You keep your standing, your knowledge and
        # your practice, which is exactly what you started with.
        #
        # ONCE A DECADE AT MOST. The first version settled whenever the balance
        # sat a denarius past the line, so a household whose rent slightly
        # exceeded its credit was "settled" every single year, logging the same
        # dramatic event five hundred times. A write-off is a once-in-a-life
        # humiliation, not an annual accounting entry, and between them you are
        # simply in arrears, which already has consequences of its own.
        if self.capital < -limit and yr - getattr(self, "last_settlement", -999) >= 10:
            self.last_settlement = yr
            self.capital = -limit * 0.35
            # THE NUMBER ANNOUNCED HAS TO BE THE NUMBER APPLIED. Two settlements
            # each said "reputation -12" against a reputation of 4.9, and the
            # second did nothing at all - a break tester checked, and was right
            # that a penalty which cannot be paid should not be quoted.
            _rep_hit = min(12.0, max(0.0, self.reputation))
            self.reputation = max(0.0, self.reputation - 12)
            # AND NOBODY LENDS TO YOU FOR A WHILE. Without this, walking away
            # from a debt cost a little standing and nothing else, and standing
            # grows back. A person who has just been written off does not get
            # a fresh line of credit the following morning.
            _frozen_before = getattr(self, "credit_frozen_until", 0)
            self.credit_frozen_until = max(_frozen_before, yr + 12)
            # SAY WHAT ACTUALLY HAPPENED. "The debt is written off" while
            # leaving the player owing a third of their credit line is a
            # sentence that contradicts the number on the next line, and a
            # weird-play tester watched it fire eight times and concluded it
            # did nothing at all. Most of it goes; what is left, and what it
            # cost your name, is the part worth reading.
            #
            # AND SAY IF THE UNLOCK DATE JUST MOVED. A second settlement
            # while the first freeze had not yet lifted pushes it from yr+5
            # or yr+12 out to a fresh yr+12 with nothing said about it - an
            # England playtester watched their own credit-freeze date move
            # silently three times (1313, then 1320, then 1330) with no
            # event naming the change. A deadline that quietly slides is
            # worse than a longer fixed one would have been.
            # A FREEZE HAS TO HAVE BEEN ACTUALLY IN FORCE to "move" - the
            # default _frozen_before of 0 is "never frozen", not a freeze
            # that this settlement then extended, and comparing only the
            # before/after VALUES said a date had moved on every first-ever
            # settlement (0 -> yr+12 is a bigger number, by that test, same
            # as a real extension).
            _moved = (_frozen_before > yr
                     and self.credit_frozen_until > _frozen_before)
            self.log.append((yr, "INSOLVENCY SETTLED: most of the debt is written "
                                 "off and you still owe about %s denarii. Your "
                                 "name is worth less for it (reputation %s), and "
                                 "you keep your knowledge and your practice%s"
                                 % ("{:,.0f}".format(limit * 0.35),
                                    "-%.1f" % _rep_hit if _rep_hit > 0.05
                                    else "already at nothing, so no further",
                                    (". Settling again while still frozen out "
                                     "pushes the date nobody will fund you "
                                     "again until from %d out to %d - it moves "
                                     "with every settlement, not just the first"
                                     % (_frozen_before, self.credit_frozen_until))
                                    if _moved else "")))

    def stall_diagnosis(self):
        """None if the run is going somewhere; otherwise what is wrong and what
        would actually change it.

        A weird-play tester called this the most important finding of their
        session: "a player who makes one bad purchase early can be locked out
        of the goal for the rest of the game, with the game continuing to
        accept commands and give the impression of an ongoing playthrough for
        470+ more years, and the only feedback being the same static 'in
        arrears' message every time." Their run sat at exactly -924.5 denarii
        for fifty years, completing nothing, while INSOLVENCY SETTLED fired
        once a decade for ever.

        The arithmetic was not wrong and the state was not even a dead end -
        they got out of it themselves with forty rounds of working for wages.
        What was wrong is that nothing told them any of that. A game that has
        effectively stopped has to say so, and say what would restart it,
        because the alternative is a player spending an hour discovering it by
        experiment.
        """
        if self.capital >= 0 or getattr(self, "insolvent_years", 0) < 8:
            return None
        # THE SAME NET THE LEDGER PRINTS. This left out the interest on the
        # arrears, which is the one cost that exists BECAUSE you are in
        # arrears: a break tester read "you lose 46 denarii a year" directly
        # above "Net/yr: -159.5" and reported the banner as quoting a loss that
        # is not the loss.
        interest = max(0.0, -self.capital) * self.debt_interest_rate()
        # revenue_capacity(), to actually BE "the same net the ledger
        # prints" above, now that the ledger's own net_per_year reads it
        # too - both were reading plain revenue() and calling themselves
        # the standing figure, which is exactly what revenue_capacity()
        # exists to be instead.
        standing_revenue = self.revenue_capacity()
        standing_upkeep = self.upkeep()
        standing_living = self.living_cost(
            _rev=standing_revenue, _upkeep=standing_upkeep)
        net = (standing_revenue - standing_upkeep - standing_living
               - self.mine_operating_cost() - interest)
        if net >= 0:
            return None
        ways = []
        pool = self.director_pool() - getattr(self, "wage_hours_this_year", 0.0)
        if pool > 100:
            # ONLY IF IT WOULD ACTUALLY GAIN. Selling your hours takes them out
            # of your own practice, so with a practice to lose this is often
            # the losing move - and `work` says so to your face when you take
            # it. A break tester followed the banner's advice and was answered
            # "you earned 125, and the practice those hours were running was
            # worth 175 a year - so this cost you 50", which is the game
            # recommending a mistake and then naming it as one.
            # NAME THE TRADE, and pick the one that actually pays best here.
            # A break tester followed "work for wages" as a labourer, the
            # cheapest trade in the table, and `work` answered "you earned 125,
            # and the practice those hours were running was worth 175 a year -
            # so this cost you 50". Advice that does not say which job to take
            # is advice that can be followed into a loss.
            trades = [t for t in WAGES if self.trade_available(t)]
            best_t = max(trades, key=lambda t: ANNUAL_WAGE.get(t, 375.0),
                         default=None)
            if best_t:
                rate = ANNUAL_WAGE[best_t] / self.HOURS_PER_PERSON_YEAR
                would_earn = (pool * rate * self.price_index * self.wage_index
                              * (1.0 + min(0.5, self.reputation / 200.0)))
                # What those same hours are already earning in the practice.
                practice = sum(self.nodes[k]["rev"] for k in self._practice_set())
                would_cost = (practice * self.PRACTICE_SHARE
                              * (pool / max(1.0, self.director_pool())))
                if would_earn > would_cost:
                    ways.append("work as a %s: %.0f of your own hours are left "
                                "this year and would bring in about %s against "
                                "the %s of practice they come out of, so you are "
                                "up %s. Nobody has to lend you anything for that"
                                % (best_t, pool,
                                   "{:,.0f}".format(would_earn),
                                   "{:,.0f}".format(would_cost),
                                   "{:,.0f}".format(would_earn - would_cost)))
        losers = sorted((k for k in self.operating
                         if self.nodes[k]["up"] > self.nodes[k]["rev"]),
                        key=lambda k: self.nodes[k]["rev"] - self.nodes[k]["up"])
        if losers:
            ways.append("close what costs more than it brings in: %s"
                        % ", ".join("%s (%+.0f a year)"
                                    % (k, self.nodes[k]["rev"] - self.nodes[k]["up"])
                                    for k in losers[:3]))
        if self.wage_bill() > 0:
            ways.append("let people go: your payroll is %s a year"
                        % "{:,.0f}".format(self.wage_bill()))
        if self.mine_operating_cost() > 0:
            ways.append("close a mine: they cost %s a year whether you use them "
                        "or not" % "{:,.0f}".format(self.mine_operating_cost()))
        if not ways:
            ways.append("there is nothing left to cut; your living costs alone "
                        "exceed what you earn, and only new income will move it")
        if interest > 0.5:
            ways.append("%s of that %s is interest on the arrears themselves, "
                        "which is the one cost that goes away as the balance "
                        "comes back up"
                        % ("{:,.0f}".format(interest), "{:,.0f}".format(-net)))
        return {"you_are_stuck": ("you have been in arrears %d years and you "
                                  "lose %s denarii a year, so nothing you start "
                                  "will ever be paid for"
                                  % (self.insolvent_years,
                                     "{:,.0f}".format(-net))),
                "this_is_not_the_end_of_the_run": ("it is escapable, and none of "
                                                   "these need anybody to lend "
                                                   "you a denarius"),
                "what_would_change_it": ways}

    # THREE ANSWERS TO "CAN I AFFORD THIS" is two too many. A break tester
    # collected them: `quote` counted cash alone, `available afford` and `hire`
    # counted cash plus half the credit line, and `start` counted cash plus the
    # whole of it. Two of those are a real distinction and one was an
    # oversight, so the distinction is named here and used everywhere.
    #
    # A lender advances against WORK - there is something half-built to point
    # at - and will not advance against a payroll or a purchase, where the
    # money is gone the moment it is spent. That is why `start` may draw the
    # whole line and `hire` and `buy` may draw half of it. `quote` counted
    # neither, which was simply wrong: it is the command whose entire job is
    # to tell you what you can pay for.
    def spending_power(self, kind="buy"):
        """What you could actually raise, by what you mean to spend it on."""
        share = 1.0 if kind == "start" else 0.5
        # THE DEBT YOU ALREADY CARRY COUNTS AGAINST YOU. This read
        # max(0.0, self.capital) + credit_limit() * share, which floored the
        # capital term and so ignored arrears entirely: a household 500 into
        # a 210-denarii credit line was told it could still raise 105. It
        # cannot. credit_limit() is "how far into arrears anyone will let you
        # go" - an absolute floor on capital, which is exactly how
        # enforce_credit_limit() reads it (`if self.capital >= -limit`), not
        # headroom to be added on top of a debt.
        #
        # The floor belongs on the ANSWER, not on the capital term: you can
        # raise nothing when you are past the line, never a negative amount.
        # hire(), train() and commission() had this right all along and
        # computed it inline; the screens that quote a figure to the player
        # called this function and so quoted one too high.
        if kind == "open":
            # THE ONE CASE WHERE THE HOLE DOES NOT COUNT, and it is not an
            # oversight. Opening a door on a concern you have ALREADY built
            # and which ALREADY earns is not a wage or a commission: it buys
            # its own fee back, often in weeks. Counting the arrears against
            # it is how a household gets locked out of the very thing that
            # would dig it out.
            #
            # Two traced runs are in the suite for this. A tester at -1,608
            # against a 3,684 line left seven finished concerns worth 1,713 a
            # year shut, believing they could not open them; and a Rome run
            # built exp_trade_route_extend (net +1,700 a year) by year 117 and
            # sat on it, unopened, for about 850 years. See the checks named
            # "a completed concern that pays for its own door within months
            # opens even while deep in arrears" and its slow-payback sibling,
            # which holds the line the other way: a concern that takes YEARS
            # to clear its own capex still does not open on this.
            return max(0.0, self.capital) + self.credit_limit() * share
        return max(0.0, self.capital + self.credit_limit() * share)

    def cost_money_factor(self):
        """What a denarius of QUOTED cost means, for spending purposes.

        This exists because money_real was being multiplied into every price,
        and money_real FALLS as the currency is debased. So the worse the money
        got, the cheaper everything became: a naive tester found a pawnshop
        quoted at 5 denarii in 278 AD that had cost 1,025 when they built one in
        160, and correctly said debasement should push nominal prices UP, not
        collapse them by two orders of magnitude. They guessed the cause exactly:
        a multiplier tending to zero being multiplied in rather than divided.

        The model is in REAL terms. Debasement destroys the value of CASH, which
        is already handled by taking a haircut off capital when it fires. Real
        prices do not fall, so nothing here tracks money_real; it survives only
        as something to report. Applying both would have been a double count in
        opposite directions.
        """
        return float(self.price_index)

    def opposition_factor(self, k):
        """Opposed work costs more: bribes, delay, a provincial site, a front man."""
        return 1.0 + 0.25 * max(0.0, -self.state_interest(self.nodes[k]))

    def project_cost(self, k):
        """What this project will actually cost in money, all factors applied.

        This is the number `why` quotes and the number the project must have
        actually PAID before it can complete. It used not to exist, and that was
        the single worst bug in the economy: step() charged what you could afford
        each year, clamped at your balance, and then completed the project on
        hours and calendar alone. A tester started a 4,361 denarius balloon with
        400 denarii, finished it in four years having paid about 984, and the
        remainder was simply forgiven. Money was decorative; only hours were real.
        """
        n = self.nodes[k]
        return (n["_total_cost"] * self.cost_money_factor() * self.opposition_factor(k)
                * self.civ_cost_factor(k) * self.material_cost_factor(k)
                * self.material_market_factor(k))

    def _done_changed(self):
        """Call after anything adds to or removes from self.done.

        Also invalidates capability_factor()'s cache: that walk filters
        done_in_order() by self.granted too, and every site that adds to
        self.granted does so in the same breath as adding to self.done (see
        the comments on capability_factor), so no separate granted-changed
        signal exists or is needed.
        """
        self._done_seq = None
        self._cap_factor = None

    def _operating_changed(self):
        """Call after anything adds to or removes from self.operating.

        The `_InvalidatingSet` self.operating is built from (see that
        class's comment, just above EconomyMixin) calls this on every
        mutation automatically - every `.add`/`.discard`/`.update`/... from
        any of the nine-odd call sites across core.py/projects.py/
        economy.py/society.py, and any future one, with nothing for any of
        them to remember. See capability_factor(), its only reader so far.

        A property (`self.operating` intercepting every READ, the way
        `revealed` in engine/fog.py intercepts every WRITE) was tried first
        and measured worse, not better: self.operating is read in the
        hottest loop in the engine - `_goods_category_state` and
        `goods_market_factor` alone read it roughly sixteen million times
        in the 300-year profile this fix was measured against - so a
        property's per-access overhead, paid on every one of those reads to
        protect a few thousand writes, cost far more than capability_factor
        saved; a 300-year profiled run got SLOWER (22.1s -> 27.5s). An
        `_InvalidatingSet` intercepts only mutation, which is what actually
        needs intercepting, at none of that cost: plain attribute reads
        (`in`, `for`, `sorted(...)`, truthiness) are exactly as fast as a
        plain set, unmeasurably so, because they are a plain set's own
        C-level methods, inherited unchanged.

        The gap a property would have closed is whole-object replacement -
        `s.operating = X`, which only two places in this codebase do: a
        fresh Sim's own __init__ (core.py), where there is nothing yet to
        invalidate, and load_state's generic `setattr` loop (protocol.py),
        which is NOT always acting on a freshly-constructed Sim - `load`
        issued mid-session through the agent/play JSON protocol loads into
        the SAME long-lived object a player goes on playing in, and every
        open/close/mothball after that load mutates .operating directly.
        Left alone, that setattr would silently downgrade self.operating to
        a plain, non-invalidating set for the rest of that process's life.
        load_state calls _reset_operating() (below) once, right after its
        generic loop, to close that one specific gap explicitly instead of
        taxing sixteen million reads to close a gap with exactly one door.

        ALSO bumps `_operating_ver`, a plain monotonic counter with the same
        reach as this hook (every one of the same nine-odd call sites, and
        no others - it is set here and nowhere else). `_goods_category_state`
        and `_revenue_upkeep_candidates` below both key a cache on this
        counter instead of re-deriving their own answer from `operating`'s
        contents on every call, for the same reason `_cap_factor` already
        does: those two are read from the hottest loops in the engine (see
        _goods_category_state's own comment - 75,748 calls in a 150-year
        profile, more than any other function in this file) and their
        actual inputs (self.year plus this set) change far less often than
        they are read. It carries the exact same one known gap this
        docstring already describes for `_cap_factor` - a caller that
        replaces `self.operating` with a plain `set()` rather than going
        through `_reset_operating()` (test_regressions.py's ROUND 8 close-
        order test does this once, deliberately, to build a fixture) stops
        this counter advancing for the rest of that object's life, same as
        it already stops `_cap_factor` invalidating. Not a new risk this
        change introduces: the existing cache already lives with it, on the
        same object, for the same reason, and no reference run in
        perf_fingerprint.py's suite ever does this to a live Sim - only that
        one hand-built test fixture does, and it never asks for a goods
        price, an income factor, or a revenue/upkeep total afterward.
        """
        self._cap_factor = None
        self._operating_ver = getattr(self, "_operating_ver", 0) + 1

    def _reset_operating(self):
        """Re-wrap self.operating in a fresh `_InvalidatingSet` and
        invalidate once. See the long comment on _operating_changed() for
        why this exists and why it is not a property instead: this is the
        one call site (load_state, protocol.py) that replaces
        self.operating wholesale on a Sim that may go on being mutated
        afterward in the same process."""
        self.operating = _InvalidatingSet(self.operating, on_change=self._operating_changed)
        self._operating_changed()

    def venture_ramp(self, k):
        """How much of its full takings a concern is making, 0..1.

        FROM THE YEAR YOU OPENED IT, not the year you worked out how. This read
        done_year, so a concern built in 100 and opened in 130 was at full
        takings the day its doors opened - which made delaying `open` strictly
        better than opening promptly, and made the ledger's own sentence ("a
        concern you open reaches its full figure over 3 years") false in the
        one case a break tester checked. Custom takes time to find whoever owns
        the shop.
        """
        started = (getattr(self, "opened_year", None) or {}).get(k)
        if started is None:
            started = self.done_year.get(k, self.year)
        age = self.year - started
        return min(1.0, (age + 1) / self.cfg["revenue_ramp_years"])

    # ---- goods-producing concerns: a market, not a fixed number --------------
    #
    # Every OTHER concern in this file pays the tree's flat `rev` for ever,
    # scaled only by the ramp above and this society's prices. A playtester's
    # question was exactly the case that breaks: an automated loom should make
    # an enormous margin the day it opens, because handlooms are everywhere and
    # power looms are not, and that margin has to erode as the rest of the
    # world catches up, cushioned by the fact that cheaper cloth pulls in
    # buyers who could not afford cloth before. `commodities.py` already has a
    # bounded, elastic price built for exactly this worked example (see
    # COMMODITIES.md section 4.2), but it is a standalone module Sim has never
    # imported - its own header says so - because it reasons in tonnes against
    # a national output table and has no notion of "years since you personally
    # opened this," or "how rich a population you can reach": Sim already has
    # both (opened_year, pop_scale, self.economy). This reuses commodities.py's
    # IDEAS - a bounded, elastic price, and the loom's own twenty-times figure
    # - natively, rather than bolting a tonnage model onto a system that has
    # never tracked a single tonne of anything. Wiring commodities.py itself
    # into Sim is the larger integration COMMODITIES.md section 11 describes
    # and explicitly defers.
    #
    # SCOPE IS DELIBERATELY NARROW. Only categories that are a tangible good
    # sold to a broad population get this: cloth (`textiles`), preserved food
    # and drink (`processing`), books and print matter (`printing`), cameras
    # and film (`photography`). Mining, instruments, transport and every
    # institution keep the flat figure - a mine's output already has its own
    # supply-and-price machinery below (MARKET_SHARE, material_price_factor)
    # answering a different question (what it costs YOU to buy ore, not what
    # a workshop earns selling a finished good), and a school or a patron is
    # exactly what the brief asked to leave alone.
    #
    # NUMBERS AND WHERE THEY CAME FROM, per category:
    #   eta (price elasticity of demand: how much buying responds to price):
    #     textiles 0.65 - apparel-demand studies typically put clothing's
    #       own-price elasticity in the 0.6-1.0 range, moderately elastic,
    #       neither a staple nor a luxury; picked at the inelastic end of that
    #       range so the early erosion the brief asks for is actually visible
    #       - at exactly 1.0 (unit elastic) revenue would sit dead flat as
    #       price moved, which demonstrates nothing. [C]
    #     processing 0.35 - agricultural-economics estimates for food-at-home
    #       demand (the USDA's Economic Research Service puts most packaged
    #       food categories around 0.2-0.6) cluster low: people keep eating
    #       whether or not canned milk or refined sugar gets cheaper. [C]
    #     printing 0.80 - discretionary but not a luxury in the pre-mass-media
    #       world these nodes describe; picked close to, but under, unit
    #       elastic. [C]
    #     photography 1.60 - camera and film equipment is squarely a luxury
    #       good throughout the period this applies to; luxury-goods demand
    #       studies commonly cite elasticities above 1.5 (fine goods and
    #       jewellery studies often land in the 1.5-2.5 range). [C]
    #   floor (price never falls below this fraction of the tree's own
    #     figure, however saturated the market): textiles and printing start
    #     from the bound already chosen for cloth (the one tracked commodity
    #     textiles maps to) in commodities.json, 0.35, nudged up to 0.40;
    #     processing starts tighter still, 0.45, because preserved food has a
    #     harder cost floor (a tin and the heat to seal it cost what they
    #     cost) and a harder ceiling on how much cheaper it can get before
    #     people just use raw ingredients instead, nudged up to 0.55;
    #     photography starts from coffee's bound in commodities.json, the one
    #     other luxury good that file prices, 0.5, nudged up to 0.55. Every
    #     nudge is the SAME finding: measuring this against the 700-year
    #     Monte Carlo runs (see the change's own report) showed a civilization
    #     already winning on the earlier, harsher floors on the edge of the
    #     700-year horizon (han_china_100ad, 2 of 10 seeds) losing every one
    #     of them once a goods concern's long-run earnings fell as far as the
    #     first pass had them fall. A model that turns a marginal win into a
    #     loss is not "more realistic," it is miscalibrated against a game
    #     this game already plays close to the edge of - so every floor here
    #     moved up by 0.05-0.1 from its first-pass figure, softening how much
    #     of the day-one margin is eventually given up, while leaving the
    #     shape of the curve (an early, visible decline) untouched.
    #   tau (years for the market to visibly respond to a new supply):
    #     textiles 35 - Britain's handloom weavers went from the dominant
    #       technology to a shrinking minority over roughly thirty to forty
    #       years, the 1810s to the 1850s; that is the number used for how
    #       long a cloth market takes to re-equilibrate around a new loom, at
    #       the slower end of that range for the same reason the floors moved
    #       - see above. Processing, printing and photography use a longer 40
    #       [C]: no equally specific diffusion-speed citation exists for
    #       those, so a longer, explicitly illustrative period stands in for
    #       one, and the same 700-year-horizon finding argued for slower
    #       rather than faster.
    #
    # EXTENDED, data/review/COMMODITY_DYNAMISM.md's second and third
    # findings. Two gaps in the original four categories, both measured
    # directly against a live Sim:
    #
    # (a) ZERO CROSS-ELASTICITY. "One loom at age 20 earns factor 0.7840.
    #     With a second identical loom running: 0.7840. With ten: 0.7840."
    #     goods_market_factor() used each concern's OWN age as a private
    #     clock standing in for "how saturated is the market" - a real
    #     number for a lone producer, but a fiction once a second producer
    #     (yours, or - per this file's existing goods_reach_factor comment
    #     - the rest of the world's) exists, because nothing summed what
    #     they were jointly supplying. Fixed below by pricing off the
    #     CATEGORY's total supply (every concern you operate in it, not one
    #     node's private clock) rather than one node's own age in isolation.
    #
    # (b) NO REAL CONSUMER ECONOMY. The brief's own richest idea: "when the
    #     public has less money, they buy less. So if the price of food
    #     goes down, the price people would be willing to pay for diamonds
    #     or records would go up." That is an ordinary income effect
    #     (cheaper necessities free up spending on everything else, the
    #     same logic behind Engel's law) and this file had no channel for
    #     it at all - `processing` (food) and, say, `photography` (a
    #     luxury) moved on completely independent clocks. The brief also
    #     named the actual businesses this should cover - "alcohol, or
    #     wine... food like pizza... gambling, casinos... books, card
    #     games, movies, phonographs, record players, newspapers" - and
    #     grepping the tree for them turns up real, revenue-bearing nodes
    #     (fud_distillation_spirits, fin_gambling_house, fin_racecourse,
    #     fin_theatre_business, hom_printed_books, hom_playing_cards_printed,
    #     if_tin_foil_phonograph, prn_radio_broadcasting,
    #     fin_newspaper_business...) that were earning the tree's flat
    #     figure for ever, the same as an aqueduct. `essential` below marks
    #     which categories are necessities (only `processing`, food, so
    #     far - the one the brief's own worked example is about) and
    #     income_factor()/essential_price_ratio() below implement the
    #     effect: a discretionary category earns more as the player's own
    #     essential-goods concerns get cheaper, and is neutral (no effect,
    #     not a penalty) when the player runs none. See those methods' own
    #     comments for the mechanism and its honest scope limit.
    #
    # NEW CATEGORY NUMBERS, same [C] estimation method as the original
    # four (see the class comment above for how those were reasoned):
    #   fermentation (alcohol - brewing, distilling, vinegar) 0.55/0.45/35:
    #     alcohol demand studies commonly cite elasticities of roughly
    #     0.3-0.9 (a consumption habit, not a nutritional necessity, but
    #     also not as freely substitutable as a camera); floor and tau
    #     follow processing's "real cost floor" and textiles' diffusion
    #     pace respectively, as the closest existing anchors.
    #   leisure (toys, games, puzzles, books, instruments) 1.10/0.45/35:
    #     hobby and entertainment goods are usually cited above unit
    #     elasticity but below photography's fine-goods range.
    #   sound (phonograph, gramophone, radio broadcasting) 1.30/0.50/35:
    #     a luxury technology good, the same reasoning as photography but
    #     slightly less extreme - audio reached a mass market somewhat
    #     faster, historically, than the camera did.
    #   media (newspapers, advertising, lending library, telegraph
    #     business) 0.85/0.40/35: an information good, close to printing's
    #     own 0.80.
    #   commerce (inns, hotels, restaurants, department stores, trading
    #     posts, coffeehouses) 1.00/0.45/30: unit-elastic hospitality and
    #     retail demand (commonly cited 0.8-1.3); a shorter tau because a
    #     service business's custom is understood to shift faster than a
    #     manufacturing good's.
    #   entertainment (gambling, lotteries, theatre, professional sport,
    #     racecourses - cat values "luxury", "spectacle" and "law" in the
    #     tree, which is where fin_gambling_house, fin_lottery,
    #     fin_theatre_business, fin_racecourse and fin_professional_sport
    #     actually live) 1.80/0.50/35: the single most discretionary
    #     bucket here, above photography, matching how elastic gambling
    #     and spectator-entertainment demand is usually cited to be.
    #   personal (perfume, cosmetics, toiletries) 1.10/0.45/35: ordinary
    #     personal-luxury demand, the same order as leisure.
    # `essential` is omitted (defaults False, i.e. discretionary) on every
    # category except processing; textiles is left discretionary too,
    # deliberately - clothing is not modelled as a nutritional necessity
    # here, only food is, matching the brief's own worked example exactly.
    GOODS_CATEGORIES = {
        "textiles":      {"eta": 0.65, "floor": 0.40, "tau": 35.0},
        "processing":    {"eta": 0.35, "floor": 0.55, "tau": 40.0, "essential": True},
        "printing":      {"eta": 0.80, "floor": 0.40, "tau": 40.0},
        "photography":   {"eta": 1.60, "floor": 0.55, "tau": 40.0},
        "fermentation":  {"eta": 0.55, "floor": 0.45, "tau": 35.0},
        "leisure":       {"eta": 1.10, "floor": 0.45, "tau": 35.0},
        "sound":         {"eta": 1.30, "floor": 0.50, "tau": 35.0},
        "media":         {"eta": 0.85, "floor": 0.40, "tau": 35.0},
        "commerce":      {"eta": 1.00, "floor": 0.45, "tau": 30.0},
        "luxury":        {"eta": 1.80, "floor": 0.50, "tau": 35.0},
        "spectacle":     {"eta": 1.80, "floor": 0.50, "tau": 35.0},
        "law":           {"eta": 1.80, "floor": 0.50, "tau": 35.0},
        "personal":      {"eta": 1.10, "floor": 0.45, "tau": 35.0},
    }
    # Which of the categories above are necessities, for income_factor()
    # below. Kept as its own set rather than scattering an `essential`
    # check across every reader, matching the class's own convention of
    # naming a scope decision once rather than repeating the condition.
    ESSENTIAL_CATEGORIES = frozenset(
        cat for cat, cfg in GOODS_CATEGORIES.items() if cfg.get("essential"))

    def goods_reach_factor(self):
        """How much further than a purely local market your goods can travel,
        and so how fast you saturate the market you can reach.

        The brief asks for this explicitly: market size "should depend on...
        how far your goods can travel." Reuses the exact signals
        _material_market_tonnes() already uses for the OPPOSITE direction (how
        far your BUYING reach extends) - a patron's name, citizenship, a
        standing trade route, a railway, a telegraph - because a network that
        gets you more iron also gets your cloth to more buyers; it would be an
        odd model that widened one side of the ledger with these flags and not
        the other. Capped, like every other compounding multiplier in this
        file (MARKET_SHARE, material_price_factor), so five flags together do
        not multiply into an implausible number.
        """
        r = 1.0
        if self.has("citizenship"):                r *= 1.15
        if self.running("patron_senatorial"):      r *= 1.3
        if self.running("patron_imperial"):        r *= 1.6
        if self.running("exp_trade_route_extend"): r *= 1.3
        if self.running("railway"):                r *= 1.35
        if self.running("telegraph_electric"):      r *= 1.15
        return min(r, 3.0)

    def _goods_category_state(self, cat):
        """(n_active, world_age, cfg) for a goods category: every one of
        YOUR OWN concerns currently operating in it, and how long the
        oldest of them has been open. None if this is not a goods category
        at all, or you operate nothing in it.

        THE FIX FOR ZERO CROSS-ELASTICITY. COMMODITY_DYNAMISM.md measured
        it directly: two identical looms, same age, both showed a revenue
        factor of 0.7840 - "bit-for-bit identical... neither affected the
        other at all," because the old formula's only inputs were one
        node's own age and the civilization-wide scalars, with no shared
        state for "how much of this is already being made." n_active below
        is that shared state: every concern in the category counts toward
        the SAME total supply, so a second loom genuinely competes with
        the first rather than each independently pretending to have the
        market alone. world_age uses the OLDEST still-operating concern
        (max, not min, over each member's own age) so a lone producer's
        day-one factor is unchanged (see goods_market_factor's own
        docstring for why that identity matters): with one concern, this
        is exactly the age that concern's own private clock always used;
        with several, it is when this player's presence in the category
        began, which is the right reference point for "how long has
        outside diffusion had to work on this market."
        """
        cfg = self.GOODS_CATEGORIES.get(cat)
        if not cfg:
            return None
        # RESULT CACHED PER (cat, self.year, operating's version), because
        # the walk below is still called far more often than its answer can
        # possibly change. A 150-year rome_100ad profile of 150 optimizer
        # steps found this called 75,748 times - 505 times per simulated
        # year - for the same reason the comment below already explains
        # (goods_market_factor() once per operating concern, income_factor()
        # again for the essential category, from every one of those calls):
        # nothing that changes what this function returns happens between
        # most of those calls in the same year.
        #
        # WHY THIS KEY IS SAFE, exhaustively:
        #   self.year only ever changes at one place in the whole engine
        #   (core.py's step(), `self.year += 1`, once per step) - so it is
        #   constant for the entire year's worth of calls this is trying to
        #   collapse, and a NEW year always gets a different key, never a
        #   stale hit.
        #   self.operating's membership is the other input read below (the
        #   `for m in ...: if m not in self.operating` test); `_operating_ver`
        #   is a plain counter bumped by _operating_changed(), which the
        #   _InvalidatingSet backing self.operating (see that class's own
        #   comment, top of file) fires on EVERY .add/.discard/.update/...
        #   from any of the nine-odd call sites across core.py/projects.py/
        #   economy.py/society.py - the exact mechanism _cap_factor's own
        #   cache already trusts for the same set, and it carries the same
        #   one accepted gap that one already has (see _operating_changed's
        #   own docstring): a caller that replaces self.operating with a
        #   bare set() rather than going through _reset_operating() stops
        #   this counter, same as it already stops _cap_factor. Not a new
        #   risk.
        #   `opened_year` (read below via `started`) is never mutated
        #   anywhere except projects.py's open_venture, and there only ever
        #   in the same call, immediately after, as `self.operating.add(k)`
        #   - grep the engine for "opened_year" and it is the only
        #   assignment site outside __init__'s empty {} and load_state's
        #   generic setattr (which itself calls _reset_operating(), and so
        #   _operating_changed(), right after setting it - see that
        #   function's own comment on why that ordering matters). So
        #   `_operating_ver` changing is a SUPERSET of every way
        #   `opened_year` can change: it cannot go stale on its own.
        #   `done_year` is read here only as a fallback for a member of
        #   `operating` whose opened_year entry is somehow still missing -
        #   which the paragraph above shows never happens along either real
        #   path into `operating` (open_venture always sets it in the same
        #   breath; restore() requires the node to already be mothballed,
        #   which means it went through open_venture earlier). The one place
        #   this fallback is actually reachable is a test fixture that adds
        #   directly to `operating` without ever opening anything - and that
        #   still bumps `_operating_ver` through the identical hook, so even
        #   there this cache is not stale, only (like the code before this
        #   change) reading done_year's default of self.year for a node that
        #   was never truly opened.
        key = (self.year, getattr(self, "_operating_ver", 0))
        cache = getattr(self, "_goods_cat_state_cache", None)
        if cache is None or cache[0] != key:
            cache = (key, {})
            self._goods_cat_state_cache = cache
        bucket = cache[1]
        if cat in bucket:
            return bucket[cat]
        ages = []
        # WHICH NODES CAN EVER BE IN THIS CATEGORY IS FIXED AT LOAD TIME,
        # so walk that (small, cached-once) list and test membership in
        # `operating` instead of sorting and filtering the whole operating
        # set on every single call. `cat` never changes after the tree is
        # loaded, so this cache needs no invalidation. Profiling a 300-year
        # single-seed run found this function alone (the `sorted(self.
        # operating)` scan) costing more self time than any other in the
        # engine - 7.1s of 34.4s total, called 1.5 million times because
        # goods_market_factor() calls it once per operating concern, and
        # income_factor() (reached from the SAME call, for every
        # non-essential concern) calls it again for the essential
        # category. Only max() and len() are taken from `ages` below, both
        # order-independent, so dropping the sort changes no result. See
        # PERFORMANCE.md.
        for m in self._nodes_in_cat(cat):
            if m not in self.operating:
                continue
            started = (getattr(self, "opened_year", None) or {}).get(m)
            if started is None:
                started = self.done_year.get(m, self.year)
            ages.append(max(0.0, self.year - started))
        if not ages:
            bucket[cat] = None
            return None
        result = (len(ages), max(ages), cfg)
        bucket[cat] = result
        return result

    def _nodes_in_cat(self, cat):
        """Every node key that carries this goods category, in the tree's
        own (stable, insertion) order - independent of PYTHONHASHSEED and
        never changing after load, so this is built once per run and
        reused. See _goods_category_state's own comment for why this
        exists."""
        cache = getattr(self, "_nodes_by_cat_cache", None)
        if cache is None:
            cache = {}
            for k, n in self.nodes.items():
                c = n.get("cat")
                if c:
                    cache.setdefault(c, []).append(k)
            self._nodes_by_cat_cache = cache
        return cache.get(cat, ())

    def _goods_category_ratios(self, cat, extra=0):
        """(price_ratio, qty_ratio, n_active) for a whole category, shared
        by every concern that sells into it - the actual mechanism
        goods_market_factor() and goods_category_price_ratio() both read,
        so the two cannot drift apart. None if nothing of this player's is
        currently operating in the category AND `extra` is 0.

        `extra`: how many MORE concerns to price in as already sharing this
        category's total supply, beyond what you currently operate - 0 for
        every caller before this, 1 for goods_market_factor_if_opened()'s
        "what would a NEW one earn on its own day one, given the ones
        already running" question. Kept as a parameter on the one function
        that already owns this formula, rather than a second copy of it that
        could drift from this one, per this file's own convention elsewhere
        (see goods_market_factor's docstring on why goods_category_price_
        ratio() reads this same function instead of reimplementing it)."""
        st = self._goods_category_state(cat)
        if st is None:
            if extra <= 0:
                return None
            # NOTHING OF YOURS IS RUNNING YET, so there is no world_age to
            # inherit - the honest answer for "day one of the first concern
            # in a category" is the tree's own figure, exactly what
            # goods_market_factor() already returns for that case. Do not
            # invent a supply/age pair out of nothing to answer `extra` here;
            # let the caller's own bare 1.0 fallback (goods_market_factor_
            # if_opened) handle it, the same way goods_market_factor() does.
            return None
        n_active, world_age, cfg = st
        n_active += extra
        reach = self.goods_reach_factor()
        tau = max(1.0, cfg["tau"] * (self.pop_scale ** 0.5)
                  * (self.economy ** 0.25) / reach)
        world_supply = 1.0 + world_age / tau
        total_supply = world_supply * n_active
        eta = cfg["eta"]
        price_ratio = max(cfg["floor"], min(1.0, total_supply ** (-1.0 / eta)))
        qty_ratio = min(total_supply, price_ratio ** (-eta))
        return price_ratio, qty_ratio, n_active

    def goods_category_price_ratio(self, cat):
        """The price this category's market currently pays, as a fraction
        of its day-one figure (1.0 = day one; falls toward the category's
        own floor as supply catches up). None if you operate nothing in
        it - "we do not know," not "assume 1.0" - see essential_price_ratio
        for the caller that turns that None into a neutral default.
        Independent of any one node, unlike goods_market_factor(k): this
        is the market-wide number income_factor() below needs, since a
        player's disposable income depends on what food costs in general,
        not on one specific cannery."""
        r = self._goods_category_ratios(cat)
        return None if r is None else r[0]

    def essential_price_ratio(self):
        """A stand-in for 'the cost of living', averaged over every
        ESSENTIAL category (today: just `processing`, food) the player
        currently operates a concern in. 1.0 (neutral) if none - this
        model only ever learns food got cheaper because the player's own
        preserving/processing capacity made it so; it has no independent
        notion of a national food price. That is a real scope limit
        (COMMODITY_DYNAMISM.md's own finding about population elsewhere in
        this file: "this is a solo-player economic simulation... not a
        multi-agent market"), stated rather than hidden behind a default
        that looks like data.
        """
        ratios = [self.goods_category_price_ratio(c)
                  for c in sorted(self.ESSENTIAL_CATEGORIES)]
        ratios = [r for r in ratios if r is not None]
        market_ratio = sum(ratios) / len(ratios) if ratios else 1.0
        # Household-backed farms supply staples even before a processing
        # concern exists. Diminishing returns reach the same 0.55 floor as the
        # established food market rather than making subsistence free.
        farm_ha = max(0.0, getattr(self, "farm_hectares", 0.0))
        farm_ratio = max(0.55, 1.0 / (1.0 + farm_ha / 120.0))
        return min(market_ratio, farm_ratio)

    FARM_COST_PER_HA = 75.0
    HOUSING_COST_PER_PLACE = 600.0
    TRADE_SCHOOL_COST_PER_SEAT = 1200.0

    def invest_farm(self, hectares):
        """Buy productive farmland that lowers the household staple price."""
        hectares = float(hectares)
        cost = hectares * self.FARM_COST_PER_HA * self.price_index
        if hectares <= 0 or cost > self.capital:
            return 0.0
        self.capital -= cost
        self.farm_hectares = getattr(self, "farm_hectares", 0.0) + hectares
        return hectares

    def build_worker_housing(self, places):
        """Add durable worker housing and relieve household crowding."""
        places = float(places)
        cost = places * self.HOUSING_COST_PER_PLACE * self.price_index
        if places <= 0 or cost > self.capital:
            return 0.0
        self.capital -= cost
        self.worker_housing_places = getattr(self, "worker_housing_places", 0.0) + places
        return places

    # How much a fully-saturated essential's cheapness (price_ratio at its
    # own floor) can move discretionary spending. 1.0 means "as much extra
    # spending power as the essential's own price drop, one-for-one" -
    # deliberately modest (not the >1 multiplier a strict income-effect
    # model of Engel curves would license) because this model can only see
    # ONE essential category's price moving, not a whole household budget,
    # and overstating it would let a single cannery understate how much
    # this simplification is worth trusting. [C]
    INCOME_ELASTICITY = 1.0

    def income_factor(self):
        """How much extra (or, in principle, less) a population has to
        spend on everything that is NOT a staple, from how cheap staples
        currently are.

        The brief's own framing, almost verbatim: "when the public has
        less money, they buy less. So if the price of food goes down, the
        price people would be willing to pay for diamonds or records would
        go up." That is a real, textbook mechanism (an income effect: money
        freed up by a cheaper necessity gets spent on everything else) and
        this is the one channel this model can see it through - see
        essential_price_ratio()'s own comment for the honest scope limit.
        Neutral (1.0, no effect either way) whenever the player runs no
        essential concern, so a run that never touches food processing
        behaves exactly as it did before this pass - see the class comment
        on GOODS_CATEGORIES for why that identity matters to the test
        suite. Clamped defensively in case ESSENTIAL_CATEGORIES ever grows
        to more than one category and their ratios compound oddly; with
        today's single essential category (processing, floor 0.55) the
        clamp never actually binds (1.0 + 1.0*(1-0.55) = 1.45).
        """
        ratio = self.essential_price_ratio()
        return max(0.7, min(1.8, 1.0 + self.INCOME_ELASTICITY * (1.0 - ratio)))

    def goods_market_factor(self, k):
        """How a goods-producing concern's revenue has moved, relative to
        the day it opened, as the market it sells into fills up - shared
        with every OTHER concern selling the same kind of good, and lifted
        or dampened by how cheap the essentials market has made staples if
        this good is a discretionary one. See _goods_category_state's own
        comment for the cross-elasticity fix and income_factor's for the
        income effect; this function's job is only to turn those into one
        node's own revenue multiplier.

        Exactly 1.0 for a LONE concern on the day it opens, by
        construction (n_active=1, world_age=0, no essential concern
        running -> income_factor=1.0), so a player who opens one loom
        still earns the tree's own figure on the first turn, unchanged
        from before this pass - the brief's own original requirement.
        A SECOND concern in the same category, though, does not reset to
        1.0 even on ITS day one if the first is already mature: it is
        entering a market that already has supply in it, which is
        precisely what "compete" has to mean.

        Price then moves along an ordinary constant-elasticity demand
        curve against the category's SHARED total supply (see
        _goods_category_ratios): quantity sold varies as price ** (-eta),
        so solving for the price that clears exactly `total_supply` gives
        price_ratio = total_supply ** (-1/eta), clamped at the floor;
        quantity sold is the smaller of what supply can make and what
        that price will move. Revenue is price times quantity, both
        relative to day one - but quantity is now a SHARED total, split
        evenly across every concern currently selling into the category
        (`/ n_active`), because that total is what the whole category's
        combined capacity finds buyers for, not what any one concern
        alone would.
        """
        cat = self.nodes[k].get("cat")
        if k not in self.operating:
            return 1.0
        r = self._goods_category_ratios(cat)
        if r is None:
            return 1.0
        price_ratio, qty_ratio, n_active = r
        factor = price_ratio * qty_ratio / n_active
        if cat not in self.ESSENTIAL_CATEGORIES:
            factor *= self.income_factor()
        return factor

    def goods_market_factor_if_opened(self, k):
        """What goods_market_factor(k) would read on the day you actually
        opened k, if you opened it today - unlike goods_market_factor(k)
        itself, which answers a flat 1.0 for anything not yet `operating`
        because it has no day-one to measure yet, and every screen that
        lists a not-yet-opened concern (`ventures`'s "you know how but have
        not opened", `why`) reads that 1.0 as "the tree's own figure is what
        this would earn." For the FIRST concern in a category that is true.
        For a SECOND one it has never been true - see goods_market_factor's
        own docstring, which already says a second concern "does not reset
        to 1.0... it is entering a market that already has supply in it" -
        and nothing before this function let a player see that BEFORE
        opening it and finding out the hard way, which is exactly what two
        independent playtesters (Han, England) reported: revenue quietly
        far below what they had been shown, with no warning at the moment
        the decision to open was actually made.

        None for anything not a goods category. 1.0 - the honest, unhedged
        answer - when nothing of yours operates in this category yet: a
        real first mover really does get the tree's own figure, the same
        identity goods_market_factor() itself preserves.
        """
        cat = self.nodes[k].get("cat")
        cfg = self.GOODS_CATEGORIES.get(cat)
        if not cfg:
            return None
        if k in self.operating:
            return self.goods_market_factor(k)
        r = self._goods_category_ratios(cat, extra=1)
        if r is None:
            return 1.0
        price_ratio, qty_ratio, n_active = r
        factor = price_ratio * qty_ratio / n_active
        if cat not in self.ESSENTIAL_CATEGORIES:
            factor *= self.income_factor()
        return factor

    def goods_market_note(self, k):
        """One sentence on why THIS concern's earnings have moved (or, for
        one not yet opened, WOULD move) from the tree's own figure - so a
        player sees why a concern that opened at 400 a year now earns 280,
        instead of being left to notice the number changed and guess why
        (the brief's own example, in the brief's own words). Also says when
        competition, not just time, is the reason - the brief's own second
        question ("do two looms compete") answered on the one screen a
        player actually reads.

        WORKS BEFORE YOU OPEN IT, not only after. It used to return None for
        anything not yet `operating`, which meant the one moment a player
        could still choose differently - before committing capital to a
        second concern in an already-saturated category - was the one moment
        this said nothing at all. Two playtesters (Han, England) each
        reported market saturation eating a large, unexplained share of
        gross revenue; neither had anything on screen, before or after
        opening, that named it. See goods_market_factor_if_opened's own
        comment for the mechanism this now surfaces early.
        """
        cat = self.nodes[k].get("cat")
        cfg = self.GOODS_CATEGORIES.get(cat)
        if not cfg:
            return None
        opened = k in self.operating
        factor = (self.goods_market_factor(k) if opened
                  else self.goods_market_factor_if_opened(k))
        if factor is None or abs(factor - 1.0) < 0.01:
            return None
        n = self.nodes[k]
        quoted = n["rev"] * (self.venture_ramp(k) if opened else 1.0) * self.price_index
        now = quoted * factor
        floor_factor = cfg["floor"] ** (1.0 - cfg["eta"])
        direction = ("fallen, because supply of it - yours and everyone "
                     "else's - has grown faster than demand"
                     if factor < 1.0 else
                     "risen, because the cheaper it got the more buyers it "
                     "found")
        st = self._goods_category_state(cat)
        n_active = (st[0] if st else 0) + (0 if opened else 1)
        n_active = max(1, n_active)
        if opened:
            bits = ["the tree quotes %s a year for this; it actually earns "
                    "about %s now. The price this market pays has %s since "
                    "you opened it. It will settle at roughly %s a year "
                    "once that market saturation runs its course, not at "
                    "nothing - there is always a floor price and a floor of "
                    "buyers this kind of good keeps"
                    % ("{:,.0f}".format(quoted), "{:,.0f}".format(now), direction,
                       "{:,.0f}".format(quoted * floor_factor / n_active))]
        else:
            # THE WARNING BEFORE THE DECISION, not the postmortem after it.
            # `quoted` here is the tree's own figure exactly as `ventures`
            # and `why` already show it for anything not yet opened, so a
            # player reading this alongside that figure sees the same number
            # this note is about to tell them not to expect.
            bits = ["the tree quotes %s a year for this, and 'ventures'/'why' "
                    "show that same figure - but %d of yours already sell "
                    "into this market, so this would open already reduced by "
                    "market saturation, at about %s a year, not %s"
                    % ("{:,.0f}".format(quoted), n_active - 1,
                       "{:,.0f}".format(now), "{:,.0f}".format(quoted))]
        if n_active > 1:
            bits.append("%d concern%s of yours %s selling into this same "
                        "market at once and share what it will pay - each "
                        "one takes home a smaller slice than it would alone"
                        % (n_active, "" if n_active == 1 else "s",
                           "would be" if not opened else "are"))
        if cfg.get("essential"):
            bits.append("this is a necessity: people keep buying it "
                        "whatever it costs, which is why it barely moves "
                        "with price")
        elif self.essential_price_ratio() < 0.99:
            bits.append("food has gotten cheaper in your hands, which "
                        "leaves people more to spend on a good like this "
                        "one")
        if factor < 1.0:
            # THE WAY OUT, not only the diagnosis. This is a shared-total
            # mechanism scoped to ONE category (GOODS_CATEGORIES/
            # _goods_category_state): a concern in a different category is
            # not competing for the same buyers at all and keeps the tree's
            # own figure, which is the honest answer to "what do I do about
            # this" and was missing from every screen this appears on.
            bits.append("a concern in a DIFFERENT goods category is not "
                        "competing for these same buyers and is not reduced "
                        "by this at all")
        return ". ".join(bits)

    def goods_market_summary(self):
        """Every operating goods concern whose earnings have moved from the
        tree's own figure, worst first - the aggregate version of
        goods_market_note(), for `money` rather than one concern at a time.

        ALSO THE TOTAL, not only the worst row. Two playtesters (Han,
        England) each watched market saturation eat a large share of gross
        revenue by measuring it themselves against a total they had to
        reconstruct on their own - this screen told them which single
        concern was worst hit and never added the pieces up, so "the market
        is taking some of what I earn" never became a number a player could
        actually read against their own revenue. This is not a new
        mechanism and not a bug in the existing one: goods_market_factor()'s
        floors are exactly what GOODS_CATEGORIES documents, and several
        concerns competing in the same category is exactly the situation
        this file's cross-elasticity fix (see _goods_category_state) was
        written to represent honestly. It is a real, intended effect that
        simply had no total attached to it anywhere a player would read.
        """
        rows = []
        quoted_total = actual_total = 0.0
        for k in sorted(self.operating):
            cfg = self.GOODS_CATEGORIES.get(self.nodes[k].get("cat"))
            if not cfg:
                continue
            f = self.goods_market_factor(k)
            n = self.nodes[k]
            quoted = n["rev"] * self.venture_ramp(k) * self.price_index
            quoted_total += quoted
            actual_total += quoted * f
            if abs(f - 1.0) > 0.01:
                rows.append((k, f))
        if not rows:
            return None
        rows.sort(key=lambda kv: kv[1])
        worst = rows[0]
        cats_sharing = sorted({self.nodes[k].get("cat") for k, _f in rows
                               if (self._goods_category_state(self.nodes[k].get("cat")) or (1,))[0] > 1})
        note = ("%d concern%s selling into a market that has moved since it "
                "opened: %s is at %d%% of the tree's own figure, because "
                "supply of what it makes has grown since it opened. "
                "'ventures' says the same thing for each one"
                % (len(rows), "" if len(rows) == 1 else "s",
                   worst[0], round(worst[1] * 100)))
        if cats_sharing:
            note += (". You are running more than one concern selling into "
                     "the same market in: %s - they are competing with each "
                     "other, not just with time" % ", ".join(cats_sharing))
        # THE NUMBER THAT WAS MISSING: total denarii a year, and what share
        # of these concerns' own quoted figures that is - the "47% of gross
        # revenue" a player has to be able to read directly, not infer.
        gap = quoted_total - actual_total
        if quoted_total > 0.5 and abs(gap) > 0.5:
            pct = round(100.0 * abs(gap) / quoted_total)
            if gap > 0:
                note += (". Altogether, market saturation is taking about %s "
                         "a year from these concerns - %d%% of what their own "
                         "quoted figures add up to. It does not recover on "
                         "its own: opening ANOTHER concern in a category you "
                         "are already saturating makes this worse, not "
                         "better, while a concern in a category you do not "
                         "yet run keeps the tree's own figure"
                         % ("{:,.0f}".format(gap), pct))
            else:
                note += (". Altogether, these concerns are earning about %s "
                         "a year MORE than their own quoted figures add up "
                         "to (%d%%) - cheap, saturated essentials have left "
                         "buyers with more to spend on the rest"
                         % ("{:,.0f}".format(-gap), pct))
        return note

    def done_in_order(self):
        """Everything you have finished, in a FIXED order.

        `self.done` is a set of strings, and a set of strings iterates in an
        order that depends on PYTHONHASHSEED, which Python randomises per
        process. Three places summed floats over it - revenue, upkeep and
        material demand - and floating point addition is not associative, so
        the totals differed in their last bits between one process and the
        next. Over five hundred years those last bits decide which side of a
        threshold you land on, and the same --seed gave two different answers
        on alternate invocations. Three other sites were fixed for this before
        by sorting; these were missed because nothing here touches the RNG, and
        the arithmetic looked innocent.

        `self.order` is a list, and a list is a list.
        """
        # CACHED, because this is O(nodes) and revenue() calls it. Uncached it
        # was 2.2 seconds of a 3.5 second `can_start` once something else began
        # calling revenue() thousands of times: correct, and quadratic. The
        # cache is invalidated by hand at the twelve places that add to or
        # remove from `done`, rather than by a length check, because a year that
        # abandons one work and completes another leaves the length identical
        # and the contents different.
        seq = getattr(self, "_done_seq", None)
        if seq is None:
            seq = self._done_seq = [k for k in self.order if k in self.done]
        return seq

    # WHAT ONE PERSON'S PRACTICE IS WORTH, against what the tree quotes for the
    # trade as a going concern. A physician working alone, out of a rented room,
    # with no partners and no staff, does not take what an organised practice
    # takes; a third is the figure the whole opening is calibrated around.
    #
    # This number was already in the game and was reached by accident. A granted
    # skill has no entry in done_year, so its "age" was zero every year for ever
    # and the revenue ramp - meant to say a NEW business takes three years to
    # find its custom - pinned it at the first step of three and never moved it.
    # The arithmetic came out right and the meaning came out wrong: a break
    # tester read `why` at 500 a year, saw 166.7 in the ledger, and could find
    # nothing anywhere that explained the difference or said whether it would
    # ever close. It will not. It is not a ramp; it is the size of your practice.
    PRACTICE_SHARE = 1.0 / 3.0

    def practice_attention(self):
        """How much of your practice you are actually there to run.

        The income from practising medicine is your own two hands: it is the
        cover identity the guide tells you to adopt, and a weird-play tester
        found you could sell every one of your 2,400 hours as a labourer and
        still collect the full fee from a surgery you were demonstrably not in.
        That is the same hours sold twice, which is an accounting error rather
        than a balance choice.

        Only hours sold for WAGES count against it. Hours that go into your own
        projects do not: a physician who spends his evenings grinding lenses is
        still a physician in the morning, and the whole model assumes you build
        while your practice runs. Whether THAT should compete too is a real
        question and a much larger one; this is the half that is simply wrong.
        """
        # A DEAD PHYSICIAN HAS NO PRACTICE. This is your own two hands, and a
        # break tester watched the surgery go on taking fees for eleven years
        # after the founder was buried. What you built outlives you; what you
        # personally did does not.
        if not self.founder_alive:
            return 0.0
        pool = self.director_pool()
        if pool <= 0:
            return 1.0
        sold = min(pool, getattr(self, "wage_hours_this_year", 0.0))
        return max(0.0, 1.0 - sold / pool)

    def revenue_capacity(self):
        """What you would earn in an ordinary year, with your own hands on your
        own work. Used where a swing in ONE year should not count - a lender
        does not cut your line because you took a job this year."""
        _sold = getattr(self, "wage_hours_this_year", 0.0)
        self.wage_hours_this_year = 0.0
        try:
            return self.revenue()
        finally:
            self.wage_hours_this_year = _sold

    def revenue(self):
        r = 0.0
        attention = self.practice_attention()
        practice_set = self._practice_set()
        granted = self.granted
        operating = self.operating
        # SCAN ONLY WHAT COULD POSSIBLY PAY. Every node this loop's own body
        # goes on to skip - not operating and not practised - was already
        # true of the whole rest of `done`, which only grows; see
        # _revenue_upkeep_candidates' own docstring for why this is safe.
        for k in self._revenue_upkeep_candidates():
            practice = k in practice_set
            if k in granted and not practice:
                continue          # the society's, not yours
            # KNOWING HOW IS NOT THE SAME AS RUNNING IT. A node pays when it is
            # open, and not for having been worked out. See is_venture and
            # open_venture in projects.py for why: the tree already described
            # these as concerns with a yearly running cost, and the only thing
            # missing was the decision to open the doors.
            if not practice and k not in operating:
                continue
            n = self.nodes[k]
            if n["rev"]:
                # AT THIS SOCIETY'S PRICES, like everything else it charges you.
                # The tree's revenue figures are Rome 100 AD denarii and this
                # was the one flow that never converted them, so a physician's
                # practice paid exactly 233.5 in Tenochtitlan, in Luoyang and
                # in Scandinavia while the cost of building anything differed
                # by up to 1.4x. See living_cost for the other half.
                if practice:
                    r += n["rev"] * self.PRACTICE_SHARE * attention * self.price_index
                else:
                    # A SCHOOL YOU FOUNDED THREE OF EARNS THREE SCHOOLS' WORTH.
                    # institution_units is 1.0 for everything that was never
                    # expanded - the whole rest of the tree, and a single
                    # ordinary founding of the five that CAN be - so this
                    # changes nothing for a run that never asks `open` for a
                    # second one. See ProjectsMixin.institution_units.
                    _units = (self.institution_units(k)
                              if k in self.SCALABLE_INSTITUTIONS else 1.0)
                    # goods_market_factor() is 1.0 for anything outside
                    # GOODS_CATEGORIES, so this changes nothing for the
                    # services, institutions and patronage the brief asked to
                    # leave alone - see that method's own comment for why.
                    r += (n["rev"] * _units * self.venture_ramp(k) * self.price_index
                          * self.goods_market_factor(k))
        # THERE IS ONLY SO MUCH MARKET. Uncapped, this compounds: every venture
        # pays back inside two years, so its income buys the next one, and a run
        # ended holding three billion denarii against an empire whose entire
        # annual product was perhaps five billion. Testers saw the near end of
        # it and said so plainly: "I have far more capital than I have good
        # places to put it". You cannot sell more inns than the town wants, and
        # a saturating curve says that without ever making a venture worthless.
        # WHAT YOUR OWN WORKSHOP SELLS. Charging wages explicitly without
        # crediting the work was half an accounting change: in the old model a
        # trained staff was free and its output was folded invisibly into node
        # revenue, so adding a payroll of 12,000 a year and no corresponding
        # output made every civilization except Rome unable to finish. Thirty
        # craftsmen in a workshop do not sit there costing money. They make
        # things, and the things are sold.
        #
        # It is deliberately less than a 2x markup on wages and it needs somewhere
        # to work: a staff with no workshop is an expense, which is exactly why
        # workshop_first matters and why it is cheap.
        r += self.workshop_output()
        gross = r * (self.economy ** 0.75)
        ceiling = 900000.0 * self.pop_scale * (self.economy ** 0.75) * self.price_index
        gross = gross / (1.0 + gross / max(1.0, ceiling))
        return (gross + self.state_funding()) * self.output_factor

    def workshop_output(self):
        """What your standing staff produces and sells, over and above projects."""
        if not (self.running("workshop_first") or self.running("school_founded")):
            return 0.0
        craft = sum(n for t, n in self.employees.items() if trade_family(t) == "craft")
        craft += self.freedmen + self.slaves * 0.7
        wage = 0.0
        for t, n in self.employees.items():
            if trade_family(t) == "craft":
                wage += n * ANNUAL_WAGE.get(t, 375.0)
        wage += (self.freedmen + self.slaves * 0.7) * ANNUAL_WAGE.get("artisan", 250.0)
        mark = 1.55
        if self.running("interchangeable_parts"):  mark += 0.35
        if self.running("power_grid"):             mark += 0.45
        # AND EVERYTHING YOU KNOW HOW TO DO, which is where the value of a
        # capability actually shows up.
        #
        # Making revenue follow what you RUN was right, and it left a hole:
        # 1,337 nodes carried revenue and most of them are not businesses at
        # all. A better furnace, a tighter tolerance, a purer reagent - nobody
        # opens those as a going concern, so under the new rule they paid
        # nothing whatever, and the economy came out far poorer than every
        # number in this file was calibrated against. A Rome run ended at year
        # 800 with 270 technologies, one open concern and no craftsmen at all.
        #
        # The honest place for that value is here. Knowing how to do a thing
        # earns you nothing on its own - which was the whole point - but it
        # makes the workshop you actually staff and pay for more productive,
        # which is how method has always paid. It needs a workshop and it needs
        # people; with neither, it is still worth nothing.
        return (wage * mark * self.capability_factor()
                * self.wage_index * self.price_index)

    def capability_factor(self):
        """How much better your methods make the same pair of hands.

        Tier-weighted, over what you have built and are NOT separately running
        as a concern - a concern already pays you directly and must not be
        counted twice. Saturating, because the tenth improvement to a workshop
        is worth less than the first, and because an unbounded product of 1,300
        technologies is how you get a run holding more method than the empire.

        CACHED. A 300-year profile called this ~17,000 times, every one of
        them walking the full done list - self.done/self.operating change far
        less often than that (done_in_order() itself was fixed the same way,
        earlier, for the same reason). The cache holds the FINISHED RESULT of
        exactly this walk, recomputed from scratch - same order, same
        arithmetic, nothing added or removed piecemeal - whenever it is
        invalidated, so it is bit-identical to calling this uncached every
        time: see _done_changed() and _operating_changed(), the only two
        places that clear it. An incremental version that added and
        subtracted a node's weight as it entered or left self.done/
        self.operating was considered and rejected: float addition is not
        associative, and the order nodes enter or leave at runtime is not the
        order done_in_order() walks them in, so an incremental running total
        would drift from a full recompute in its last bits over a long run -
        a real behaviour change, not just a speed one. Recomputing the whole
        thing on invalidation has none of that risk and still turns ~17,000
        calls into however many times done/operating actually change in a
        run (a few hundred), not however many times this is asked.
        """
        cached = getattr(self, "_cap_factor", None)
        if cached is not None:
            return cached
        weight = 0.0
        for k in self.done_in_order():
            if k in self.granted or k in self.operating:
                continue
            n = self.nodes[k]
            if n["rev"] <= 0:
                continue
            weight += n["rev"]
        # 40,000 of tier-weighted method roughly doubles what a workshop makes.
        result = 1.0 + 2.0 * (weight / (weight + 40000.0))
        self._cap_factor = result
        return result

    def revenue_sources(self):
        """Where the money actually comes from, itemised.

        Testers asked this three separate times and could not answer it: "there
        is no visible in-fiction source for it", "a player who never issues a
        single start still gets richer every year". Both were looking at the
        income from practising medicine, which is the cover identity the game
        tells you to adopt, and neither had any way to find that out.
        """
        rows = {}
        for k in self.done_in_order():
            practice = k in self.granted and self._practisable(k)
            if k in self.granted and not practice:
                continue
            if not practice and k not in self.operating:
                continue
            n = self.nodes[k]
            if not n["rev"]:
                continue
            if practice:
                ramp = self.PRACTICE_SHARE
            else:
                ramp = self.venture_ramp(k)
            amt = (n["rev"] * ramp * (self.economy ** 0.75) * self.output_factor
                   * self.price_index)
            if practice:
                amt *= self.practice_attention()
            else:
                # SAME FACTOR revenue() APPLIES, so this row and the total it
                # is supposed to add up to do not silently disagree - see the
                # "the ledger's parts add up to the revenue it states" check.
                amt *= self.goods_market_factor(k)
            if amt > 0.5:
                rows[k] = round(amt, 1)
        # ALL OF IT, OR SAY WHAT IS MISSING. This returned the fifteen largest
        # rows and nothing else, so a break tester summed what the ledger
        # listed, got 7,101.9 against a stated revenue of 6,738, and correctly
        # reported that the accounts do not add up - two running earners were
        # simply not shown, and the workshop's own output and the saturation
        # that caps the whole figure were never rows at all.
        ranked = sorted(rows.items(), key=lambda kv: -kv[1])
        out = dict(ranked[:15])
        rest = sum(v for _k, v in ranked[15:])
        if rest > 0.5:
            out["_and_%d_smaller_concerns" % len(ranked[15:])] = round(rest, 1)
        wo = self.workshop_output() * (self.economy ** 0.75) * self.output_factor
        if wo > 0.5:
            out["_what_your_own_workshop_sells"] = round(wo, 1)
        if self.state_funding() > 0.5:
            out["_state_funding"] = round(self.state_funding() * self.output_factor, 1)
        # And the difference between the parts and the whole, which is the
        # market saturating: you cannot sell more inns than the town wants.
        gap = round(self.revenue() - sum(out.values()), 1)
        if abs(gap) > 1.0:
            out["_what_the_market_will_not_absorb"] = gap
        else:
            # ROUNDING IS NOT A ROW. Every entry is rounded to a tenth so it
            # can be read, and a ledger that says "these add up to the revenue
            # above" has to survive being added up: a break tester summed two
            # rows, got 166.7 + 66.7 = 233.4 under a stated 233.5, and filed
            # the claim as false in one line. Push the residue into the largest
            # row, which is the one place a tenth cannot be noticed.
            # AT ONE DECIMAL, like every other row. Pushing the raw residue in
            # wrote 166.8394 onto a line the player reads; the rows and the
            # total both live at a tenth, so the correction has to as well.
            resid = round(round(self.revenue(), 1) - sum(out.values()), 1)
            if out and abs(resid) > 0.049:
                # sorted(): a tie in max() over a dict falls back to insertion
                # order, which came from a set.
                big = max(sorted(out), key=lambda k: abs(out[k]))
                out[big] = round(out[big] + resid, 1)
        return out

    # Of the auto-granted nodes that carry revenue, seven are medicine and two
    # are shipping, and the difference decides who gets paid. Cataract couching
    # is a skill a single trained person practises with their own hands, and
    # practising it is exactly the cover the guide tells you to adopt. A fleet
    # of large merchant ships is owned by other people and you are not entitled
    # to its freight. Removing the revenue from BOTH, which is what I did first,
    # was too blunt: it left every civilization with no way to earn a living at
    # all, and the Norse, who are poorer and pay a 1.4 price index, could then
    # never accumulate the 1,580 denarii for identity_cover. They failed 100% of
    # runs, blocked on the first node in the game.
    PRACTISABLE_CATS = {"surgery", "obstetrics", "pharmacology", "medicine",
                        "diagnosis", "dentistry"}

    def _practisable(self, k):
        """Is this granted node a skill YOU can practise for a fee?"""
        return self.nodes[k].get("cat") in self.PRACTISABLE_CATS

    def still_ramping(self):
        """Earners that are not yet paying their full figure, and how far along.

        Every earner ramps over revenue_ramp_years, so on the day you open one
        it pays a third of what the tree quotes for it. A break tester read
        `why` at 500 a year, opened it, saw 166.7 in the ledger, and had
        nothing anywhere to tell them whether the ledger was wrong, the quote
        was wrong, or they were being charged for something. It is none of
        those: it is year one of three. Kept OUT of revenue_sources, whose
        every value is a number that has to sum to the revenue above it.
        """
        young = []
        for k in sorted(self.operating):
            n = self.nodes.get(k)
            if not n or not n["rev"] or k in self.granted:
                continue
            ramp = self.venture_ramp(k)
            if ramp < 0.999:
                young.append((k, ramp))
        if not young:
            return None
        young.sort(key=lambda kv: kv[1])
        return ("%s%s at %d%% of full takings. A concern you open reaches its "
                "full figure over %g years, so what the ledger shows is not "
                "what it will be."
                % (", ".join(k for k, _r in young[:6]),
                   " and %d more" % (len(young) - 6) if len(young) > 6 else "",
                   young[0][1] * 100, self.cfg["revenue_ramp_years"]))

    def practice_note(self):
        """Why the practice pays less than the tree quotes, said once, plainly."""
        # ONLY WHAT THE LEDGER ACTUALLY SHOWS. Naming rows that were dropped
        # for being under half a denarius invites the reader to look for them.
        scale = (self.PRACTICE_SHARE * self.practice_attention()
                 * (self.economy ** 0.75) * self.output_factor)
        prac = sorted(k for k in self._practice_set()
                      if self.nodes[k]["rev"] * scale > 0.5)
        if not prac:
            return None
        return ("%s %s your own practice, and %s about a third of what the tree "
                "quotes for the trade: the difference between one person in a "
                "rented room and an organised concern. That gap does not close "
                "with time. Selling your hours for wages takes another bite out "
                "of it, because you cannot be in two places."
                % (", ".join(prac[:4]),
                   "is" if len(prac) == 1 else "are",
                   "it pays" if len(prac) == 1 else "they pay"))

    def _practice_set(self):
        """The granted skills you actually practise, as a set, computed once.

        revenue() called _practisable once per done node per call, and
        start_reason calls revenue() - so a 45-year fogged Mexica run made
        SIXTY-ONE MILLION of those calls and spent 38 seconds inside revenue().
        The answer never changes unless the granted set does, which happens at
        setup and never again.
        """
        cache = getattr(self, "_practice_cache", None)
        if cache is None or cache[0] != len(self.granted):
            cache = (len(self.granted),
                     frozenset(k for k in self.granted if self._practisable(k)))
            self._practice_cache = cache
        return cache[1]

    def _revenue_upkeep_candidates(self):
        """Every node in `done` that revenue() or upkeep() could possibly
        charge or pay for - i.e. that is operating, or in your practice
        set - in done_in_order()'s own tree order. Neither function can do
        anything with a node that is neither, so both used to scan the
        WHOLE of `done` (every technology ever finished, which is most of
        the tree by the late game) just to throw almost all of it away
        again on that same test; this is the small subset that survives it,
        computed once and handed to both.

        A 150-year rome_100ad profile of 150 optimizer steps found revenue()
        alone at 9,037 calls and 1.428s cumulative, and upkeep() at 4,293
        calls (upkeep's own summing genexpr showing up separately at
        120,922 calls) - both walking done_in_order() start to finish on
        every one of those, when `operating` and the practice set together
        are typically a handful of concerns against a `done` list that only
        grows. This is exactly the O(active) vs O(done) gap done_in_order()
        itself was already added to close for a DIFFERENT quadratic blowup
        (see its own docstring); the list is short but the SCAN was still
        long.

        CACHED, on the same three signals _goods_category_state's own cache
        (above) already trusts for this reason:
          - the identity of done_in_order()'s own cached list - a NEW list
            object exactly when `done` changes, because _done_changed()
            (below) sets `_done_seq` to None and done_in_order() rebuilds it
            from scratch. A length check is not safe here for the same
            reason done_in_order's docstring already gives: a year that
            finishes one thing and abandons another leaves the length
            unchanged and the contents different.
          - `operating`'s version counter, `_operating_ver`, bumped once per
            mutation by _operating_changed() - see that method's own
            docstring for the exhaustive case-by-case proof, which applies
            unchanged here since this reads exactly the same `operating`.
          - the identity of _practice_set()'s own cached frozenset, which
            THAT method already rebuilds (a new object, new identity) the
            moment len(self.granted) changes - see its own docstring. Since
            self.granted is only ever grown (grep the engine: every mutation
            site is `.add`, never `.discard`/`.remove`/`&=`/`-=`), a length
            check is sound there in a way it would not be for `done`, and
            this cache inherits that same soundness by keying on the
            resulting object's identity rather than re-deriving it.
        Three signals already relied on elsewhere in this file, not a new
        one - and this cache's OWN staleness, if any one of them were wrong,
        would show up as a wrong revenue or upkeep total, which
        perf_fingerprint.py's byte-for-byte, per-year state hash across nine
        reference runs (five civilisations, several seeds, fog on and off,
        events on and off) is built to catch.
        """
        seq = self.done_in_order()
        practice_set = self._practice_set()
        # STRONG REFERENCES AND `is`, NOT BARE id() INTEGERS, for the reason
        # _cached_demand_by_tag() below now spells out at length: a freed
        # object's address is handed straight to the next same-sized
        # allocation, so two different objects compare equal by id() often
        # enough to matter, and the cache replays a stale answer under a fresh
        # one. That is what made this simulation non-deterministic, in the
        # sibling cache rather than this one.
        #
        # This one had not been shown to be firing. It had been PROBED and
        # come back clean - 0 stale answers in 64,157 calls - and that probe
        # was worthless, because it allocated a comparison list on every call
        # and allocation is precisely what decides whether an address gets
        # recycled. It suppressed the effect it was measuring. The same false
        # negative cleared the cache that turned out to be guilty.
        #
        # So this is not a fix for an observed bug. It is the removal of a
        # hazard that cannot be cheaply observed, in the one shape known to
        # have already cost this project a day, by the defence
        # sim/engine/proto/nodes.py chose for the identical reason. Holding
        # seq and practice_set alive for as long as the entry may be compared
        # against them makes the collision structurally impossible rather than
        # merely unmeasured.
        operating_version = getattr(self, "_operating_ver", 0)
        cached = getattr(self, "_rev_up_candidates_cache", None)
        if (cached is not None and cached[0] is seq
                and cached[1] is practice_set and cached[2] == operating_version):
            return cached[3]
        operating = self.operating
        cands = [k for k in seq if k in operating or k in practice_set]
        self._rev_up_candidates_cache = (seq, practice_set, operating_version, cands)
        return cands

    def upkeep(self):
        # Symmetrically, you do not pay to maintain what you do not own, but you
        # do bear the small standing cost of the practice you actually run - and
        # you do not pay the running costs of a concern you have not opened.
        # Both halves of that follow `operating`, so closing something really
        # does stop the bleeding, and knowing how to do something costs nothing
        # to know.
        practice_set = self._practice_set()
        return sum(self.institution_upkeep(k)
                   for k in self._revenue_upkeep_candidates()
                   if k in self.operating or k in practice_set)

    # What a school costs on the day you found it, as a share of what it costs
    # once it is full: the building, the lease, and one teacher.
    INSTITUTION_FLOOR = 0.20

    def institution_upkeep(self, k):
        """What this concern actually costs to keep open THIS year.

        For almost everything, its upkeep. For an establishment whose purpose is
        to support PEOPLE - a school, an academy, a workshop, a licensed
        collegium, a freedman staff - it scales with how much of that support you
        are using, because a school with three scholars in it does not cost what
        a school with forty does. Endowed schools historically scaled with
        enrolment and so should this.

        This is the bridge the capability change needed. Making capability follow
        running() was right: a founder used to collect a school's twelve
        scholars and an imperial patron's sixty thousand of credit without ever
        opening either, and without paying a denarius toward them. But it priced
        every institution as though the place were full on the day you founded
        it, and that killed the first rung of the ladder.
        """
        n = self.nodes[k]
        # A THIRD SCHOOL COSTS THREE SCHOOLS' UPKEEP, at three schools' worth
        # of places to fill it against - both sides of this scale together so
        # a run that never founds more than the original single unit sees
        # exactly the arithmetic it always did. See
        # ProjectsMixin.institution_units.
        #
        # NOT YET OPEN MEANS "WHAT WOULD A FIRST FOUNDING COST", not zero.
        # auto_open_ventures (projects.py) calls this on things it has not
        # opened yet to decide whether to; institution_units answers 0 for
        # anything not currently operating, and multiplying by that turned
        # every unopened institution's prospective upkeep into a small
        # negative number (upkeep 0 against real revenue), which read as free
        # and let the affordability gate through on nothing.
        _units = (self.institution_units(k) if k in self.operating else 1.0) \
            if k in self.SCALABLE_INSTITUTIONS else 1.0
        up = n["up"] * _units
        if k not in self.CAPABILITY_INSTITUTIONS or up <= 0:
            return up
        places = self.institution_places(k) * _units
        if places <= 0:
            return up
        used = min(1.0, self.headcount() / max(1.0, places))
        return up * (self.INSTITUTION_FLOOR
                     + (1.0 - self.INSTITUTION_FLOOR) * used)

    def institution_places(self, k):
        """Roughly how many people ONE UNIT of this establishment is built to
        support - see institution_upkeep, which multiplies this by
        institution_units(k) itself, so callers wanting the total should read
        that, not this, for anything in SCALABLE_INSTITUTIONS.

        Read off the same table staff_capacity() and supervision_room() use, so
        that the cost of a place and the existence of a place cannot drift
        apart. Anything absent is sized by its own upkeep at about a wage a
        head, the right order for a building whose cost is its people.
        """
        PLACES = {"workshop_first": 12.0, "school_founded": 34.0,
                  "academy_network": 120.0, "freedman_staff": 10.0,
                  "collegium_licensed": 3.0, "patron_senatorial": 10.0,
                  "patron_imperial": 64.0, "endowment_land": 14.0,
                  "corpus_dispersed": 8.0, "interchangeable_parts": 44.0,
                  # Read off STAFF_CAPACITY_SOURCES (labour.py) the same way
                  # every other row here is: a unit's ar+di, so a chain store
                  # with three people in it is not billed as though every
                  # branch were already fully staffed.
                  "fin_company_town": 20.0, "fin_chain_store": 34.0}
        if k in PLACES:
            return PLACES[k]
        return max(1.0, self.nodes[k]["up"] / 250.0)

    # ---- raw material supply ------------------------------------------------
    CHARCOAL_PER_HA = 0.75          # tonnes per hectare per year, sustainable
    # How much of the empire's annual output you can actually BUY. This is not
    # one number: charcoal is bulky, crumbles when carted, and is therefore a
    # LOCAL commodity no matter how much of it the empire makes in total, while
    # coal is barely used by anyone so you can have almost all of it.
    # gold's 0.01 is not re-guessed: it is commodities.json's own gold entry
    # (market_share, already reasoned there against the same imperial-mint
    # scarcity that makes MARKET_SHARE["silver"] this low), so the two files
    # agree on how tightly a private buyer can get at the metalla's gold.
    MARKET_SHARE = {"charcoal": 0.002, "iron": 0.03, "copper": 0.03, "lead": 0.03,
                    "tin": 0.05, "silver": 0.01, "coal": 0.50, "saltpetre": 0.0,
                    "gold": 0.01}

    # ---- GENERALISING BEYOND THE 9 HAND-NAMED COMMODITIES --------------------
    #
    # data/review/COMMODITY_DYNAMISM.md, an audit run directly against
    # this engine: 149 of the 162 distinct material keys the tech tree uses
    # (about 92%) had a price read once from prices.json at load time and
    # never revisited for scarcity, surplus or anything else, because
    # MATERIAL_CHECKS/MARKET_SHARE above only ever named 13 keys by hand.
    # Its own worked case was aluminium: "no mine, no supply lever of any
    # kind... nothing in economy.py even contains the string aluminium."
    #
    # The fix below is NOT a per-material rule. It is a generic fallback that
    # activates for any material key this file has no curated entry for,
    # using the one number every material already has: its own book price in
    # prices.json (every material key a node's `mat` dict names MUST have a
    # prices.json entry already, or data.py's own load() would have raised
    # building `_material_cost` in the first place - so this genuinely
    # covers all 162, not just the ones anyone thought to add). A cheap,
    # plentiful material gets assumed to have a large national output and a
    # wide buyable share; a dear, rare one gets less of both - fitted, not
    # guessed, from the curated figures the 9 tracked commodities already
    # carry: iron (1.0 den/kg) is rated 82,500 t/yr, copper (4.0) 15,000,
    # gold (3,440) 9. log(output) against log(price) across those three
    # (four orders of magnitude in price) fits close to output =
    # 82,500 / price**1.1 - which reproduces gold's real 9 t/yr to within
    # 20% despite the fit never having seen gold's number, because scarcity
    # and price genuinely do move together, not because gold is special.
    # This is exactly the standard COMMODITY_DYNAMISM.md sets: "a commodity
    # nobody anticipated must behave correctly because the mechanism is
    # supply and demand, not because somebody wrote a rule for it."
    GENERIC_OUTPUT_ANCHOR_T_PER_YR = 82500.0
    GENERIC_OUTPUT_PRICE_EXPONENT = 1.1
    GENERIC_OUTPUT_FLOOR_T_PER_YR = 5.0
    GENERIC_OUTPUT_CEILING_T_PER_YR = 400000.0

    def _commodity_ledger(self):
        """The 9 curated commodities from commodities.json, as a
        CommodityLedger, cached on the CLASS (not the instance): the file
        does not change mid-run and building it involves a JSON load, the
        same reasoning _material_commodity_map below uses. Used two ways:
        as the reverse index from a material key to a curated commodity id
        (cast_iron_kg means "iron" there even though MATERIAL_CHECKS has
        never listed it), and, for the 4 curated-but-never-priced
        commodities this file's own MARKET_SHARE has never named (cloth,
        wool, cotton, copper_wire), as the SOURCE of national output and
        market share instead of the generic price-only guess below - see
        _generic_national_output_t_per_yr's own comment for why real,
        sourced data beats a formula wherever it already exists."""
        cached = getattr(EconomyMixin, "_commod_ledger_cache", None)
        if cached is None:
            cached = EconomyMixin._commod_ledger_cache = _commod.CommodityLedger()
        return cached

    def _material_commodity_map(self):
        """material key -> curated commodity id, from commodities.json's
        own material_keys lists. Cached on the class for the same reason
        as _commodity_ledger."""
        cached = getattr(EconomyMixin, "_material_commod_map_cache", None)
        if cached is None:
            cached = {}
            for cid, c in self._commodity_ledger().commodities.items():
                for mk in c.get("material_keys", []):
                    cached[mk] = cid
            EconomyMixin._material_commod_map_cache = cached
        return cached

    def _material_prices(self):
        """The flat per-kg book price for every material key in
        prices.json, read directly rather than threaded through Sim's
        constructor - the same pattern commodities.py's own
        load_commodities() already uses for its own file. Cached on the
        class: prices.json does not change mid-run."""
        cached = getattr(EconomyMixin, "_material_prices_cache", None)
        if cached is None:
            raw = json.load(open(os.path.join(_commod.ROOT, "data", "prices.json")))
            cached = {k: v["p"] for k, v in raw["purchase_prices_denarii"].items()
                     if isinstance(v, dict) and "p" in v}
            EconomyMixin._material_prices_cache = cached
        return cached

    def _book_price_per_kg(self, tag):
        """Denarii/kg for a raw material key (aluminium_kg, straight out of
        prices.json) or a curated commodity id (cloth, straight out of
        commodities.json's own base_price - the two files agree by
        construction, see commodities.json's own `_doc.reused_from`). None
        if this file cannot price it at all, which should not happen for
        any material key the tech tree actually uses (see the class
        comment above)."""
        prices = self._material_prices()
        if tag in prices:
            return prices[tag]
        c = self._commodity_ledger().commodities.get(tag)
        if c:
            p = float(c.get("base_price_denarii_per_kg", 0.0) or 0.0)
            return p or None
        return None

    def _material_tag(self, mat_key):
        """Which (commodity id, supply-pool tag) a raw material key draws
        on, generalised beyond the 13 keys MATERIAL_CHECKS names by hand.

        Three tiers, most-specific first: MATERIAL_CHECKS (the 9 originally
        tracked commodities, unchanged); commodities.json's own
        material_keys grouping (iron_bloom_kg and cast_iron_kg both mean
        "iron" there, cloth_bag_kg and linen_kg both mean "cloth," though
        none of MATERIAL_CHECKS above has ever listed any of them); and,
        for the material nothing has ever named, its own bare material key
        as a one-member commodity of itself - "aluminium_kg" becomes the
        commodity "aluminium_kg" (its own price identifies it; no reverse
        lookup needed). This is the actual generalisation
        COMMODITY_DYNAMISM.md's finding describes: 149 of 162 material
        keys got no price response at all because nothing but membership
        in a 13-entry hand list was ever asked.
        """
        pair = self.MATERIAL_CHECKS.get(mat_key)
        if pair:
            return pair
        cid = self._material_commodity_map().get(mat_key, mat_key)
        return (cid, "mine:" + cid)

    def _generic_national_output_t_per_yr(self, tag):
        """National output for a commodity/material this file has no
        curated resources.json figure for - the MARKET half of supply (see
        _material_market_tonnes). Prefers real data over a guess wherever
        real data exists: if `tag` is one of the 4 commodities.json defines
        but MARKET_SHARE has never priced (cloth, wool, cotton,
        copper_wire), this reads THAT commodity's own national/manufacturing
        output through CommodityLedger.country_output() - which already
        knows a built power loom raises cloth output, or cyanidation raises
        gold's, per commodities.json's own `produced_by` multipliers. That
        is COMMODITY_DYNAMISM.md's own third finding wired in for real:
        "a genuinely general elasticity-based price function... sitting
        unconnected." Only a material with no curated home at all (silk,
        glass, the acids and dyes and alloys) falls through to the generic
        price-derived formula documented on GENERIC_OUTPUT_ANCHOR_T_PER_YR
        above."""
        ledger = self._commodity_ledger()
        if tag in ledger.commodities:
            return ledger.country_output(tag, built=self.done)
        price = self._book_price_per_kg(tag)
        if price is None or price <= 0:
            return self.GENERIC_OUTPUT_CEILING_T_PER_YR
        out = self.GENERIC_OUTPUT_ANCHOR_T_PER_YR / (price ** self.GENERIC_OUTPUT_PRICE_EXPONENT)
        return max(self.GENERIC_OUTPUT_FLOOR_T_PER_YR,
                   min(self.GENERIC_OUTPUT_CEILING_T_PER_YR, out))

    def _generic_market_share(self, tag):
        """What fraction of _generic_national_output_t_per_yr an ordinary
        buyer (no special standing) can reach, for a commodity/material
        MARKET_SHARE has no curated figure for. Same two-tier preference as
        the output figure: a commodities.json commodity's own market_share
        (cloth 0.5, wool 0.4, cotton 1.0 trade-only, copper_wire 0.6) where
        one exists; otherwise a generic curve fitted the same way
        GENERIC_OUTPUT was - rarer, dearer materials are held closer (gold
        0.01, silver 0.01) and cheap bulk ones are wide open (coal 0.50) -
        clamped well inside that observed range since this is a default
        for a material nobody has separately reasoned about, not a
        specific claim."""
        ledger = self._commodity_ledger()
        if tag in ledger.commodities:
            return float(ledger.commodities[tag].get("market_share", 0.03))
        price = self._book_price_per_kg(tag)
        if price is None or price <= 0:
            return 0.20
        return max(0.01, min(0.35, 0.08 / (max(price, 0.01) ** 0.4)))

    def _normalize_material_name(self, mat):
        """Accept either spelling when a player names a material: the
        short curated name a mine has always used ("iron"), or the exact
        material key the tree itself uses ("aluminium_kg") - a player who
        has only ever seen `why` quote "aluminium_kg" in a bill of
        materials should not have to guess it needs no suffix, and the
        seven original short names must keep working exactly as before."""
        mat = str(mat or "").strip().lower()
        if not mat or mat in self.MINE_CAPEX_PER_T_YR:
            return mat
        prices = self._material_prices()
        if mat in prices or mat in self._commodity_ledger().commodities:
            return mat
        for suffix in ("_kg", "_g"):
            cand = mat + suffix
            if cand in prices:
                return cand
        return mat

    # Coke and charcoal are not interchangeable at one kg for one kg. A charcoal
    # blast furnace burns about 3 kg of charcoal per kg of iron; a coke furnace
    # burns about 1.6 kg of coke, and coke is about 1.6 kg of coal, so 2.56 kg
    # of coal. Switching fuel therefore MOVES the demand to a different material
    # at 0.85 of the mass, and that is the whole reason coke mattered: not that
    # it is better fuel, but that coal is dug and charcoal has to be grown.
    COKE_PER_CHARCOAL = 0.85

    def chosen_fuel(self, k):
        """Which fuel this node would actually burn, given what you have.

        The tree had a fuel OR-group on the blast furnace and a hard-coded
        4,500 tonnes of charcoal in its material list. The group was decorative:
        picking coke changed the quality factor and left the charcoal demand
        exactly where it was, so the model could never show the one substitution
        that actually decided industrial history.
        """
        for g in (self.nodes[k].get("req_any") or []):
            if "fuel" not in str(g.get("group", "")).lower():
                continue
            best, pick = 0.0, None
            for opt, qual in (g.get("options") or {}).items():
                have = opt in self.done or opt not in self.nodes
                if have and float(qual) > best:
                    best, pick = float(qual), opt
            if pick and ("coke" in pick or "coal" in pick):
                return "coke"
        return "charcoal"

    def annual_material_demand(self):
        """Tonnes per year of the materials that actually bind, from work in hand."""
        d = collections.Counter()
        for k in sorted(self.active):
            n = self.nodes[k]
            span = max(1.0, float(n.get("build_yrs") or n.get("yrs") or 1.0))
            coke = self.chosen_fuel(k) == "coke"
            for m, q in n["mat"].items():
                if coke and m in ("charcoal_kg", "firewood_kg"):
                    d["coal_kg"] += float(q) * self.COKE_PER_CHARCOAL / span / 1000.0
                    continue
                d[m] += float(q) / span / 1000.0     # kg -> tonnes per year
        # A furnace does not eat charcoal only while it is being built. It eats
        # charcoal every year it runs, forever. Omitting that was why forest
        # ownership never mattered in the model and always mattered in reality.
        for k in self.done_in_order():
            n = self.nodes[k]
            if n["up"] <= 0 or not n["mat"]:
                continue
            span = max(1.0, float(n.get("build_yrs") or n.get("yrs") or 1.0))
            coke = self.chosen_fuel(k) == "coke"
            for m, q in n["mat"].items():
                if coke and m in ("charcoal_kg", "firewood_kg"):
                    d["coal_kg"] += 0.5 * float(q) * self.COKE_PER_CHARCOAL / span / 1000.0
                    continue
                d[m] += 0.5 * float(q) / span / 1000.0
        return d

    # Which raw material keys (as they appear in a node's `mat` dict) draw on
    # which tracked commodity, and how "your own supply of it" is computed.
    # Factored out of resource_throttle so material_price_factor() below reads
    # the identical figures rather than a second guess at them.
    #
    # copper_wire_kg and wire_drawn_kg were UNTHROTTLED before this: 36 real
    # nodes (the whole el2_ electrical branch, plus gp_magnet_wire_enamelled,
    # hom_piano, en_rotary_converter...) drew drawn copper wire and none of it
    # ever competed with copper_kg for the same finite copper supply. This is
    # precisely the gap COMMODITIES.md section 7 names as "the real test":
    # wire is copper, drawn, and data/world/commodities.json's own
    # copper_wire recipe (a 5% drawing loss) already says so -- see
    # wire_chain_report() below, which asks that exact question against this
    # civilisation's real copper numbers via commodities.py's
    # propagate_demand(). gold_kg (fin_central_bank's 1000 kg, tx2_watch_case,
    # the gold-leaf electroscope) was also untracked despite Sim.open_mine
    # already supporting a gold mine (MINE_CAPEX_PER_T_YR) and
    # resources.json already carrying an empire gold figure (9 t/yr) --
    # nothing wired the two together. gold_g (LEDs, transistors: 1-20 grams)
    # is NOT added here, still: annual_material_demand() assumes every *_kg
    # key is kilograms, so a *_g key divided by 1000 would read as a
    # thousandth of what it is. That used to be "an error too small to
    # matter... but wrong in principle." It now matters: resource_throttle()
    # routes every *_g key through the LAB-SCALE stock path instead (see its
    # own comment and LAB_SCALE_SUFFIX below), which corrects the grams/
    # kilograms reading at the one place that was ever misreading it, rather
    # than by adding gold_g to this dict (that would make grams of gold
    # compete with fin_central_bank's tonnes for the same ANNUAL FLOW, which
    # is precisely the stock-vs-flow confusion this path exists to undo).
    MATERIAL_CHECKS = {
        "charcoal_kg": ("charcoal", "forest1"),
        "firewood_kg": ("charcoal", "forest4"),
        "iron_bar_kg": ("iron", "mine:iron"),
        "iron_ore_kg": ("iron", "mine:iron"),
        "coal_kg":     ("coal", "mine:coal"),
        "copper_kg":       ("copper", "mine:copper"),
        "copper_wire_kg":  ("copper", "mine:copper"),
        "wire_drawn_kg":   ("copper", "mine:copper"),
        "lead_kg":     ("lead", "mine:lead"),
        "tin_kg":      ("tin", "mine:tin"),
        "silver_kg":   ("silver", "mine:silver"),
        "gold_kg":     ("gold", "mine:gold"),
        "nitre_kg":    ("saltpetre", "nitre"),
    }

    def _own_material_supply(self, tag):
        """Tonnes a year of a tracked commodity you supply yourself, not
        bought from anyone: mines you sank, woodland you bought, nitre beds
        you built. See MATERIAL_CHECKS for which tag means what."""
        if tag == "forest1":
            return self.forest_ha * self.CHARCOAL_PER_HA
        if tag == "forest4":
            return self.forest_ha * self.CHARCOAL_PER_HA * 4
        if tag == "nitre":
            return self.nitre_bed_m2 * 0.0008
        if tag.startswith("mine:"):
            mat = tag[5:]
            # DEPLETION AND TECHNOLOGY, not the nominal tonnage you sank
            # capital into. mine_capacity is a historical record of what
            # you PAID for; what a working actually YIELDS this year is
            # that, discounted by how worked-out it is and multiplied by
            # whatever mining technology has done to counter that -- see
            # mine_depletion_factor() and mining_tech()'s own comments.
            yld, _cost = self.mining_tech(mat)
            return (self.mine_capacity.get(mat, 0.0)
                    * self.mine_depletion_factor(mat) * yld)
        return 0.0

    def _material_market_tonnes(self, emp_key):
        """Tonnes a year of `emp_key` the empire's market will sell you, at
        your current standing. The MARKET half of resource_throttle()'s
        `supply`; material_price_factor() reads it too.

        GENERALISED: resources.json's empire_output_100ad table and this
        file's own MARKET_SHARE only ever named a handful of materials by
        hand, so a material without an entry there used to answer 0 tonnes
        a year - not "unknown," an actual hard zero, which is why
        material_price_factor() had to bail out before ever reaching this
        function at all (see its own comment). A real figure, when one
        exists, is used unchanged; _generic_national_output_t_per_yr and
        _generic_market_share supply a reasoned default for everything
        else, so a material nobody named still has a market rather than
        not existing.
        """
        emp = self.res["empire_output_100ad"]
        entry = emp.get(emp_key)
        national = entry.get("t_per_yr", 0) if entry is not None else (
                   self._generic_national_output_t_per_yr(emp_key))
        share = self.MARKET_SHARE.get(emp_key)
        if share is None:
            share = self._generic_market_share(emp_key)
        # How much of a market you can command is a function of STANDING, not
        # just of money. A stranger buys at the margin; a man with senatorial
        # backing buys through their agents; a holder of imperial patronage
        # has the fiscus itself as a supplier, and the metalla were largely
        # imperial property. Charcoal is exempt because no amount of standing
        # makes a bulky crumbling fuel travel further than it can travel.
        if emp_key != "charcoal":
            if self.running("patron_imperial"):     share *= 6.0
            elif self.running("patron_senatorial"): share *= 2.5
            elif self.has("citizenship"):       share *= 1.4
            share = min(share, 0.60)
        # GEOLOGY, NOT DEMOGRAPHY. This used to be `* self.pop_scale`:
        # mineral availability scaled by population, so Norse Scandinavia
        # got 2.3% of Rome's coal because it has 2.3% of the people, and
        # England in 1300 got 7%, when England is precisely where the
        # coal actually is. A coalfield does not care how many people
        # live near it. mineral_scale() derives this instead from the
        # regions this civilization actually holds and can trade with
        # (see _compute_mineral_scale). Charcoal stays on pop_scale: it
        # is not mined, it is a local wood market, and THAT genuinely
        # does track how much local economic activity there is to buy
        # firewood from.
        scale = self.pop_scale if emp_key == "charcoal" else self.mineral_scale(emp_key)
        market = national * share * scale
        # Bengal saltpetre: an existing annual sea route, not a nitre bed.
        # This is the single most useful thing in the geography file.
        if emp_key == "saltpetre" and self.running("exp_trade_route_extend"):
            market += 60.0
        return market

    def _demand_by_supply_tag(self, demand):
        """Group MATERIAL_CHECKS demand by (emp_key, tag) -- i.e. by which
        SHARED supply it actually draws on -- instead of leaving it split by
        raw material key.

        Before this, resource_throttle() and material_price_factor() both
        checked each material key against the WHOLE of its supply
        independently: iron_bar_kg's need was compared to the full iron
        supply, then iron_ore_kg's need was compared to that SAME full
        supply again, as though each had it to itself. A plan needing 5 t/yr
        of ore and 4 t/yr of bar against a 6 t/yr supply passed both checks
        (neither 5 nor 4 alone exceeds 6) while actually needing 9 -- fifty
        per cent more than there is. Adding copper_wire_kg and wire_drawn_kg
        to MATERIAL_CHECKS without fixing this would have made it worse: a
        wire-heavy electrical age could show copper as fully supplied by
        three separate lies at once. Grouping by (emp_key, tag) sums every
        material key that draws on the SAME pool (iron_bar_kg + iron_ore_kg;
        now copper_kg + copper_wire_kg + wire_drawn_kg) while keeping
        charcoal_kg and firewood_kg separate, because they draw on the same
        forest at DIFFERENT yields per hectare (forest1 vs forest4, see
        _own_material_supply) and are not simply additive tonne-for-tonne.
        sorted(): a Counter keyed by tuples is still a dict, and the
        determinism convention here is to iterate sorted regardless of
        whether dict insertion order already happens to be safe, so a caller
        cannot inherit a bug by copying this pattern into a place where it
        is not.

        GENERALISED: this used to iterate MATERIAL_CHECKS's own 13 keys and
        look each one up in `demand`, so any OTHER key `demand` carried was
        silently never looked at - not grouped wrong, simply never
        consulted, which is the exact gap COMMODITY_DYNAMISM.md measured
        (149 of 162 material keys). annual_material_demand() was already
        generic over every material key a node's `mat` dict names; this now
        is too, routing each one through _material_tag (curated grouping
        where one exists, the material's own bare key otherwise) instead of
        only the hand-listed 13.
        """
        by_tag = collections.Counter()
        for mat, amt in sorted(demand.items()):
            if amt:
                by_tag[self._material_tag(mat)] += amt
        return by_tag

    # ---- stock vs flow -----------------------------------------------------
    #
    # A playtester who won the game put this more sharply than anything in
    # the design notes: "If I require 20 grams of gold for a device, creating
    # a tonne/year mining operation should obviously be ridiculous.
    # Realistically, I would just buy 20 grams. This argues strongly for
    # separating stock inventories from annual production capacity."
    #
    # Everything above this point (MATERIAL_CHECKS, _own_material_supply,
    # _material_market_tonnes) answers in TONNES PER YEAR, a flow, and
    # nothing anywhere carried a balance across years: a mine's surplus
    # output in excess of what that year's building programme used simply
    # evaporated rather than banking (the gap DOCS_VS_ENGINE.md ranked #3,
    # "nothing you produce outlives the year you produced it"). That is one
    # half of the fix - a running stock, in tonnes, that PRODUCTION and
    # MARKET PURCHASES feed and CONSUMPTION draws down, carried on the Sim
    # instance across the whole run (lazily, like _material_demand_cache
    # below it: EconomyMixin does not own Sim.__init__).
    #
    # The other half is the playtester's actual complaint: a handful of
    # material keys in this tree are authored in GRAMS, not kilograms
    # (caesium_g, diamond_g, germanium_g, gold_g, indium_g,
    # phosphor_bronze_g, platinum_g - every *_g key in use, see
    # COMMODITY_DYNAMISM's audit), because whoever wrote chm_catalyst_concept
    # or point_contact_transistor meant a benchtop quantity, not a shipment.
    # No list of "laboratory materials" is hand-picked here - the *_kg/*_g
    # distinction is the tree's OWN, already-general convention for exactly
    # this (see the MATERIAL_CHECKS comment above), so it generalises the
    # same way _material_tag already does: any future node that needs a
    # gram-scale quantity of anything gets this for free by being written
    # with a *_g key, the same way it already gets priced by
    # _book_price_per_kg without anyone adding it to a list. A *_g key's
    # demand is met from stock - and, whatever stock cannot cover, bought
    # outright on the spot, uncapped by mine or market flow - and NEVER sets
    # `binding`: buying a gram of something is a purchase, not a capacity
    # call, so it is never the reason a year's work is throttled. A *_kg
    # key's demand is unchanged in kind: it still has to clear the same
    # flow check as before, just against a supply that now includes
    # whatever is banked in stock, not only this year's flow.
    LAB_SCALE_SUFFIX = "_g"

    def _material_stock(self):
        """Tonnes of each tracked commodity (by emp_key) carried over from
        previous years - the stock half of stock vs flow. Lazily created on
        first use and then kept for the life of the Sim: EconomyMixin is a
        mixin, not __init__, and a fresh Counter is exactly what a household
        that has banked nothing yet should read as having. It is included in
        save_state()'s SAVE_FIELDS, so a resumed household retains the tonnes
        it actually produced or purchased.

        Deliberately a plain Counter, not commodities.py's own `Ledger`
        (also "a stock, not a flow," by its own docstring): Ledger works in
        kilograms and by commodity id, keyed for a module core.py still does
        not import; everything around resource_throttle() already works in
        TONNES and by emp_key, and the accounting below (own production vs
        market headroom, lab-scale vs industrial) needs that arithmetic
        inline, not behind add()/remove(). Reaching for Ledger here would
        buy a second unit system and a cross-module dependency, not a
        simpler mechanism - the "what was decided" COMMODITIES.md already
        documents for why commodities.py stays a library Sim calls into for
        specific answers (wire_chain_report's propagate_demand) rather than
        a second source of truth Sim's own state has to agree with."""
        s = getattr(self, "_material_stock_ledger", None)
        if s is None:
            s = self._material_stock_ledger = collections.Counter()
        elif not isinstance(s, collections.Counter):
            # A RESUMED SAVE HANDS THIS BACK AS A PLAIN DICT. It is in
            # SAVE_FIELDS so that a reloaded game is the same game - without it
            # a resume silently restarted at zero stock and played differently
            # from the run that was saved, the same class of fault as a fog
            # that could be rewound by reloading. JSON has no Counter, so
            # promote whatever came back before anything adds to it.
            s = self._material_stock_ledger = collections.Counter(s)
        return s

    def material_stock_t(self, emp_key):
        """Tonnes of `emp_key` currently banked - the STOCK half of stock vs
        flow, which is the thing a player asking "how much iron do I actually
        own" wants. The `materials` command, trading actions, and resource
        throttle all read this same ledger.
        """
        return self._material_stock().get(emp_key, 0.0)

    def material_trade_quote(self, material):
        """Current buy/sell quote for one tonne of a material commodity."""
        material = str(material or "").strip().lower()
        per_kg = self._book_price_per_kg(material)
        if per_kg is None:
            return None
        buy = per_kg * 1000.0 * self.price_index * self.material_price_factor(material)
        return {"material": material, "buy_per_tonne": buy,
                "sell_per_tonne": buy * 0.80,
                "market_available_tonnes_per_year": self._material_market_tonnes(material)}

    def buy_material_stock(self, material, tonnes):
        quote = self.material_trade_quote(material)
        tonnes = float(tonnes)
        if not quote or tonnes <= 0:
            return 0.0
        # The market figure is an annual flow ceiling, not an infinite shop.
        tonnes = min(tonnes, quote["market_available_tonnes_per_year"])
        cost = tonnes * quote["buy_per_tonne"]
        if tonnes <= 0 or cost > self.capital:
            return 0.0
        self.capital -= cost
        self._material_stock()[quote["material"]] += tonnes
        self._stock_throttle_sig = None
        return tonnes

    def sell_material_stock(self, material, tonnes):
        quote = self.material_trade_quote(material)
        tonnes = float(tonnes)
        if not quote or tonnes <= 0:
            return 0.0
        sold = min(tonnes, self.material_stock_t(quote["material"]))
        if sold <= 0:
            return 0.0
        self._material_stock()[quote["material"]] -= sold
        self.capital += sold * quote["sell_per_tonne"]
        self._stock_throttle_sig = None
        return sold

    def materials_report(self):
        """Stocks, annual flows, demand, and current trade values."""
        demand = self._demand_by_emp_key()
        materials = set(self._material_stock()) | {p[0] for p in self.MATERIAL_CHECKS.values()}
        materials |= {m for m in self.mine_capacity}
        rows = []
        for material in sorted(materials):
            quote = self.material_trade_quote(material)
            if not quote:
                continue
            annual_demand = sum(v for _tag, v in demand.get(material, ()))
            own = sum(self._own_material_supply(tag) for emp, tag in self._own_production_tags()
                      if emp == material)
            rows.append({**quote, "stock_on_hand_tonnes": self.material_stock_t(material),
                         "own_production_tonnes_per_year": own,
                         "current_demand_tonnes_per_year": annual_demand,
                         "stock_covers_years_at_current_demand": (
                             self.material_stock_t(material) / annual_demand
                             if annual_demand > 1e-9 else None)})
        return rows

    def _throttle_demand_split(self, demand):
        """`demand` (annual_material_demand()'s raw material-key Counter)
        split into two (emp_key, tag) -> tonnes/yr Counters: industrial
        (unchanged from before - still a flow demand that has to clear
        _own_material_supply + _material_market_tonnes, now plus stock) and
        lab (drawn from stock or bought outright, never throttled - see the
        class comment on LAB_SCALE_SUFFIX above).

        Deliberately NOT _demand_by_supply_tag(): that function is also read
        by material_price_factor() and everything built on it
        (material_market_factor, material_market_summary, wire_chain_report)
        for PRICING, which this pass does not touch - a gram of gold still
        nudges the price of gold exactly as much as it did before. Only the
        CAPACITY question (can this be done at all, or does it wait on a
        mine) changes here, so only resource_throttle() reads this. Fixes,
        in passing, the *_g unit bug the MATERIAL_CHECKS comment names:
        annual_material_demand() divides every raw key by 1000 assuming
        kilograms, which is correct for a *_kg key and 1000x too large for a
        *_g one (a bare quantity already in grams) - corrected here, once,
        at the one place that was ever misreading it.
        """
        industrial, lab = collections.Counter(), collections.Counter()
        for mat, amt in sorted(demand.items()):
            if not amt:
                continue
            tag = self._material_tag(mat)
            if mat.endswith(self.LAB_SCALE_SUFFIX) and not mat.endswith("_kg"):
                lab[tag] += amt / 1000.0
            else:
                industrial[tag] += amt
        return industrial, lab

    def _own_production_tags(self):
        """(emp_key, tag) for every material you currently produce yourself,
        whether or not anything is demanding it THIS year.

        Without this, a mine sunk ahead of need - dug this year for a
        furnace that starts next year - never appears in `industrial` or
        `lab` at all (both are built from DEMAND, and there is none yet),
        so resource_throttle()'s own loop never visits its tag and its
        output is never banked: the exact evaporation DOCS_VS_ENGINE.md's
        #3 describes, just the zero-demand edge of it rather than the
        partially-used one the main loop already banks correctly.
        `self.mine_capacity` is keyed by emp_key already (core.py's own
        auto-mine opens `self.binding`, which IS an emp_key - see
        MATERIAL_CHECKS), so "mine:" + that key is exactly the tag
        _own_material_supply already knows how to read, curated commodity
        or not."""
        out = {(m, "mine:" + m) for m, t in self.mine_capacity.items() if t > 0}
        if self.forest_ha > 0:
            out.add(("charcoal", "forest1"))
            out.add(("charcoal", "forest4"))
        if self.nitre_bed_m2 > 0:
            out.add(("saltpetre", "nitre"))
        return out

    # ---- electricity: a physical quantity, not a capability flag ----------
    #
    # THE GAP THIS CLOSES. cap_power_electric, cap_power_grid, cap_power_steam
    # and cap_power_water are capability nodes whose own NAMES narrate a scale
    # ("kW scale", "MW scale", "portable, hundreds of kW", "tens of kW on one
    # shaft" - see tech_tree.json) and nothing anywhere ever turned that prose
    # into a tracked watt. Two consequences, both real: a player who wanted a
    # generation/demand/reserve-margin display could not be given one (the
    # `capacity` command's power section said so outright), and - worse -
    # electrolytic aluminium, the electric arc furnace, zone refining and a
    # zinc smelter's own ancillary load all list `power_grid` in their `pre`
    # and are charged nothing whatsoever for the electricity that prerequisite
    # implies they need. The aluminium/rubber/etc. MATERIAL gating audit
    # (MATERIAL_GATING.md) closed exactly this shape of hole for MATERIALS
    # two days before this was written; this closes it for the one input
    # that check does not see, because a material key has always been
    # something `mat` can name and a watt never was.
    #
    # THE MODEL. Two sides, matched the way every other tracked commodity in
    # this file is: GENERATION (a rated kW contributed by every prime-mover
    # and generator node you have actually finished building - see
    # generation_breakdown_kw) and DEMAND (a kW drawn by every operating or
    # under-construction concern whose own prerequisite closure requires
    # cap_power_electric, cap_power_grid, or the literal power_grid node -
    # see _electricity_demand_kw). resource_throttle() below folds the two
    # together into the SAME worst-binding-constraint arithmetic iron and
    # copper already use, rather than inventing a second scarcity vocabulary:
    # electricity can become `self.binding`, appears in `self.shortages` the
    # same way "iron" or "saltpetre" already do, and reports itself through
    # the same `throttle_binding`/`why` machinery. It does NOT go through the
    # stock-banking half of that function (see the comment where it is
    # folded in, below) because a rated kilowatt is a RATE, not an inventory:
    # unlike a mine's unworked ore, a kilowatt of unused generating capacity
    # this year does not stockpile for next year, and unlike every other
    # tracked commodity, there is no market anywhere in this model that will
    # sell you a shortfall of electricity - you either generated it or you
    # did not.
    #
    # WHERE THE NUMBERS CAME FROM, AND WHERE THEY ARE A JUDGEMENT CALL.
    #
    # GENERATION: the tree's OWN cap_power_* names/notes state an order of
    # magnitude, never an exact figure - "tens of kW", "kW scale", "hundreds
    # of kW", "MW scale" (see POWER_ANCHOR_KW immediately below). Turning
    # "tens" into 30, "hundreds" into 300 and "MW scale" into 3,000 is a
    # judgement call, made explicitly here rather than smuggled into a bare
    # number with no comment: each is the geometric-ish midpoint of the
    # decade the tree's own prose names. cap_power_electric's "kW scale" is
    # deliberately smaller than cap_power_water's "tens of kW", not a
    # contradiction: cap_power_electric's own note is "one dynamo on the
    # millpond shaft you already built... enough for arc lights,
    # electroplating, a laboratory" - a small slice of an existing shaft's
    # mechanical output diverted through a dynamo, not the shaft's whole
    # output turned electrical. Every node in GENERATION_LOCAL_NODES/
    # GENERATION_GRID_NODES/TRANSMISSION_NODES/MECHANICAL_PRIME_MOVER_CHAINS
    # was found by grepping the whole tree for every node whose id, name or
    # `cat` names a prime mover or an electrical generator (water_prime,
    # steam_prime, electrical_gen, wind_prime, power_station, grid_operations,
    # plus the dynamo/alternator family by name) - a closed, enumerable set
    # today the way the 162 material keys MATERIAL_CHECKS started against
    # never was, so curating it by hand here costs the same one line per
    # future generation node that MATERIAL_CHECKS already costs per future
    # tracked commodity. Deliberately EXCLUDED from that set: dynamo/
    # alternator WINDING VARIANTS (el2_dynamo_series/shunt/compound_wound,
    # el2_alternator_rotating_field) and small auxiliary machines (en_exciter,
    # en_three_phase_gen, en_rotary_converter) - these refine or condition an
    # existing generator's output (regulation, phase, AC/DC conversion) and
    # do not represent a second, additional installation; counting them
    # would double the same generator's rating for every regulation upgrade
    # bought on top of it. Also excluded, for the mirror-image reason: the
    # water-wheel/turbine and steam-turbine FAMILIES are each a linear
    # upgrade chain at one site (undershot -> overshot -> breastshot ->
    # poncelet -> fourneyron -> francis -> kaplan; impulse -> curtis ->
    # reaction), not seven separate wheels - MECHANICAL_PRIME_MOVER_CHAINS
    # reports whichever is the BEST one you have finished, not their sum,
    # and (see generation_breakdown_kw's own note) is informational only:
    # it is not summed into electrical generation at all, because a bare
    # water wheel or steam turbine with no dynamo or alternator attached
    # turns nothing electrical, and that gate is already the existing `pre`
    # graph's job (dynamo's own prerequisites already include
    # water_power_scale; en_alternator's already include cap_power_steam).
    #
    # DEMAND: only two nodes get an individually-researched, real-world-cited
    # specific energy (ELECTRICAL_PROCESSES) - Hall-Heroult aluminium
    # electrolysis (13-17 kWh per kg of aluminium, historical/modern range;
    # applied to electrolysis_industrial's own bauxite_kg draw at a 4.5:1
    # bauxite-to-aluminium mass ratio, Bayer process) and a submerged-arc
    # ferroalloy/carbide furnace (several thousand kWh per tonne of product
    # is the real range; applied to arc_furnace_ferroalloys' own iron_ore_kg
    # draw at a simplifying 1:1 ore-to-product mass assumption, since the
    # tree carries no separate output-mass field for this node - flagged
    # here as the one approximation in this pair). Everything else this
    # file found gated on cap_power_electric/cap_power_grid/power_grid in
    # its own prerequisite closure (81 further nodes: workshop electronics,
    # vacuum-tube and radio equipment, welding, battery charging, the
    # semiconductor line itself, and zinc_industry_scale's own ancillary
    # load, whose actual smelting energy is charcoal/coal-fired per its own
    # note, not electrical - see GENERIC_ELECTRIC_LOAD_KW) gets ONE shared,
    # flat, modest figure rather than a hand-picked number apiece - the same
    # curate-the-important-cases-and-generalise-the-rest shape
    # _generic_market_share/_generic_national_output_t_per_yr already use
    # for materials, chosen so this file does not re-acquire the "13 hand-
    # named commodities out of 162" gap COMMODITY_DYNAMISM.md measured, in a
    # new unit.
    #
    # NOTES TOO VAGUE TO USE, NAMED HONESTLY: no node anywhere in the tree
    # carries a wattage or an output-mass figure for zone_refining, mfg_
    # anodising, met_electro_refining, or any of the mt2_*_electrolysis/
    # electrowinning nodes - their own `mat` dicts name reagents (graphite,
    # sulfuric acid, sulfur, lime) at bench-to-pilot quantities, not a
    # product mass a specific-energy figure could be applied to
    # defensibly. Each falls back to GENERIC_ELECTRIC_LOAD_KW rather than a
    # number invented to look more precise than the data supports.
    HOURS_PER_YEAR = 8760.0

    POWER_ANCHOR_KW = {
        "cap_power_water": 30.0,     # note: "tens of kW on one shaft"
        "cap_power_electric": 10.0,  # note: "kW scale" (see the class
                                      # comment above for why this is
                                      # smaller than cap_power_water's own)
        "cap_power_steam": 300.0,    # note: "portable, hundreds of kW"
        "cap_power_grid": 3000.0,    # note: "MW scale"
    }

    # Standalone local generators: each an actual, distinct machine, so
    # multiple different ones (a dynamo AND a wind generator) add.
    GENERATION_LOCAL_NODES = {
        "dynamo": "cap_power_electric",
        "en_wind_electric": "cap_power_electric",
        "en_alternator": "cap_power_steam",
    }
    # Grid-scale generating STATIONS (power_station category) - distinct
    # from power_grid itself, which is transmission/distribution only (its
    # own `pre` is wires, substations, transformers and steel; no generator
    # anywhere in it - confirmed by reading it).
    GENERATION_GRID_NODES = {
        "en_hydroelectric_station": "cap_power_grid",
        "en_thermal_station": "cap_power_grid",
    }
    TRANSMISSION_NODES = {
        "power_grid": "cap_power_grid",
    }
    # Mechanical prime movers, informational only (see the class comment):
    # each list is one upgrade CHAIN at a single site, so only the best
    # member you have finished counts, never the sum of the chain.
    MECHANICAL_PRIME_MOVER_CHAINS = {
        "water": (("en_undershot_wheel", "en_overshot_wheel", "en_breastshot_wheel",
                   "en_poncelet_wheel", "en_fourneyron_turbine", "en_francis_turbine",
                   "en_kaplan_turbine", "en_pelton_wheel"), "cap_power_water"),
        "steam": (("en_steam_turbine_impulse", "en_steam_turbine_curtis",
                   "en_steam_turbine_reaction"), "cap_power_steam"),
    }

    def generation_breakdown_kw(self):
        """What this civilisation can actually generate and transmit, in
        real kilowatts, right now - local (workshop-scale) generation, grid-
        scale generating stations, grid transmission capacity, and the best
        mechanical prime mover on each site (informational; see the class
        comment above for why mechanical power is never summed into
        electrical generation directly). `total_kw` - local plus grid - is
        what resource_throttle() checks electrical demand against.
        """
        local_kw = sum(self.POWER_ANCHOR_KW[tier]
                       for nid, tier in sorted(self.GENERATION_LOCAL_NODES.items())
                       if nid in self.done)
        grid_kw = sum(self.POWER_ANCHOR_KW[tier]
                     for nid, tier in sorted(self.GENERATION_GRID_NODES.items())
                     if nid in self.done)
        transmission_kw = sum(self.POWER_ANCHOR_KW[tier]
                              for nid, tier in sorted(self.TRANSMISSION_NODES.items())
                              if nid in self.done)
        mechanical_kw = {}
        for fam, (chain, tier) in sorted(self.MECHANICAL_PRIME_MOVER_CHAINS.items()):
            mechanical_kw[fam] = (self.POWER_ANCHOR_KW[tier]
                                  if any(nid in self.done for nid in chain) else 0.0)
        return {
            "local_kw": local_kw,
            "grid_kw": grid_kw,
            "transmission_kw": transmission_kw,
            "mechanical_kw": mechanical_kw,
            "total_kw": local_kw + grid_kw,
        }

    def generation_capacity_kw(self):
        """The one number resource_throttle() needs: total_kw, cached."""
        return self.generation_breakdown_kw()["total_kw"]

    # Hall-Heroult aluminium electrolysis: 13-17 kWh/kg aluminium is the
    # historical-to-modern range; 15 (the midpoint) is used. Bayer process
    # bauxite yield is roughly 4-5 t bauxite per t aluminium (ore grade and
    # process losses vary); 4.5 (the midpoint) is used, so the constant
    # below is kWh per kg of BAUXITE (electrolysis_industrial's own `mat`
    # key), not per kg of aluminium the tree never states a mass for.
    ALUMINIUM_KWH_PER_KG = 15.0
    BAUXITE_PER_ALUMINIUM_KG = 4.5
    # Submerged-arc ferroalloy/carbide furnaces: several thousand kWh per
    # tonne of product is the real range for this FAMILY of processes
    # (ferrosilicon, ferrochrome, calcium carbide - all listed in
    # arc_furnace_ferroalloys' own note) - far higher than plain scrap-steel
    # EAF remelting (a few hundred kWh/t), because this node is specifically
    # the carbide/ferroalloy family, not steel remelting. Applied to the
    # node's own iron_ore_kg draw at a simplifying 1:1 ore-to-product mass
    # assumption - the one approximation in this pair, disclosed because the
    # tree carries no separate output-mass field for this node.
    FERROALLOY_KWH_PER_KG_ORE = 5.0
    # Anything else gated on cap_power_electric/cap_power_grid/power_grid
    # that this file cannot characterise individually - a modest generic
    # workshop load, the same order of magnitude as cap_power_electric's own
    # anchor and a full order of magnitude under the two curated heavy loads
    # above, so an uncharacterised node's demand is present but never
    # dominant.
    GENERIC_ELECTRIC_LOAD_KW = 15.0

    ELECTRICAL_PROCESSES = {
        "electrolysis_industrial": ("bauxite_kg",
                                    ALUMINIUM_KWH_PER_KG / BAUXITE_PER_ALUMINIUM_KG),
        "arc_furnace_ferroalloys": ("iron_ore_kg", FERROALLOY_KWH_PER_KG_ORE),
    }

    # cap_power_electric/cap_power_grid are the CAPABILITY flags; power_grid
    # is the literal transmission node some tier-5 process nodes name in
    # `pre` directly without ever naming the capability flag too (arc_
    # furnace_ferroalloys, zinc_industry_scale - see the class comment).
    # All three are treated as "this node needs generated electricity",
    # because that is what each one actually means physically, regardless
    # of which of the three a given node's author happened to write down.
    _ELECTRICITY_GATE_TOKENS = frozenset(
        {"cap_power_electric", "cap_power_grid", "power_grid"})

    def _electricity_load_node_ids(self):
        """Every node id whose own prerequisite closure needs generated
        electricity - computed once, from self.nodes (the static tree, not
        this run's state), and cached for the Sim's whole life; nothing
        here changes as a run progresses. A single memoised recursion over
        hard_pre(), not one closure() walk per candidate node: this file's
        own MATERIAL_GATING precedent (a cycle-safe visited-set walk of the
        whole tree once) is the reused shape, not the per-node closure()
        calls _power_status/_material_capacity_rows make elsewhere for a
        handful of rows at a time.
        """
        cached = getattr(self, "_electricity_load_ids_cache", None)
        if cached is not None:
            return cached
        tokens = self._ELECTRICITY_GATE_TOKENS
        memo = {}

        def gated(k, on_stack):
            if k in memo:
                return memo[k]
            if k in tokens:
                memo[k] = True
                return True
            if k in on_stack or k not in self.nodes:
                # Cycle guard: hard_pre's own single-option req_any edges are
                # acyclic tree-wide (see closure()'s own comment), but this
                # walk is defensive of that invariant rather than trusting
                # it silently - an unexpected cycle answers "not gated"
                # rather than recursing forever.
                return False
            on_stack.add(k)
            result = any(gated(p, on_stack) for p in hard_pre(self.nodes, k))
            on_stack.discard(k)
            memo[k] = result
            return result

        # UPKEEP IS NOT THE TEST OF WHETHER WORK DRAWS POWER. This required
        # up > 0 as a proxy for "a real installation rather than a technique",
        # which was reasonable on its own and wrong in combination with an
        # earlier decision: upkeep was deliberately stripped from 1,096
        # technique nodes, because a technique is not a going concern you
        # maintain. The two together hid 118 electricity-gated nodes that draw
        # material - MORE than the 111 that were kept - including
        # zone_refining, single_crystal and mfg_anodising, which are about as
        # electrical as this tree gets and sit squarely on the road to the
        # goal. A zone refiner melting a germanium boat by induction is
        # consuming kilowatts whether or not the tree charges it rent.
        #
        # The upkeep test survives where it is genuinely the right question -
        # see the caller, which applies it to the STANDING draw of something
        # already built and running. Work in hand draws power because the work
        # is happening, not because it pays rent.
        ids = {k for k, n in self.nodes.items()
              if n.get("mat") and gated(k, set())}
        self._electricity_load_ids_cache = ids
        return ids

    def _node_annual_tonnes(self, k, mat_key):
        """Tonnes/yr of mat_key ONE node draws, using the exact per-node
        annualisation annual_material_demand() applies when it sums this
        across every node in one pass - factored out so the curated
        electrical processes below can ask for a single node's own draw
        (electrolysis_industrial's bauxite, not the tree-wide bauxite total
        - iron_ore_kg in particular is drawn by many non-electrical nodes,
        and reusing the tree-wide total would attribute every blast furnace
        and forge's ore to arc_furnace_ferroalloys' electric arc)."""
        n = self.nodes.get(k)
        if n is None:
            return 0.0
        q = float((n.get("mat") or {}).get(mat_key, 0.0))
        if q <= 0:
            return 0.0
        span = max(1.0, float(n.get("build_yrs") or n.get("yrs") or 1.0))
        if k in self.active:
            return q / span / 1000.0
        if k in self.done and float(n.get("up") or 0) > 0:
            return 0.5 * q / span / 1000.0
        return 0.0

    def _electricity_demand_kw(self):
        """Average continuous kW drawn by work in hand - the electrical
        mirror of annual_material_demand(), in kilowatts instead of tonnes.
        `sorted()` throughout: this feeds a float sum, and set/dict
        iteration order is not guaranteed stable across PYTHONHASHSEED
        values (see this file's own determinism convention elsewhere)."""
        total = 0.0
        curated = self.ELECTRICAL_PROCESSES
        for k, (mat_key, kwh_per_kg) in sorted(curated.items()):
            t_per_yr = self._node_annual_tonnes(k, mat_key)
            if t_per_yr <= 0:
                continue
            total += (t_per_yr * 1000.0 * kwh_per_kg) / self.HOURS_PER_YEAR
        for k in sorted(self._electricity_load_node_ids() - set(curated)):
            n = self.nodes.get(k)
            if n is None:
                continue
            if k in self.active:
                total += self.GENERIC_ELECTRIC_LOAD_KW
            elif (k in self.done and float(n.get("up") or 0) > 0
                  and k in getattr(self, "operating", ())):
                # STANDING draw, where upkeep IS the right question: a thing
                # that costs nothing to keep is not an installation humming
                # away in the background, and one that is built but shut draws
                # nothing either.
                total += 0.5 * self.GENERIC_ELECTRIC_LOAD_KW
        return total

    def resource_throttle(self):
        """How much of this year's planned work the materials will actually support.

        Charcoal is the one that bites, because it is not mined, it is GROWN.
        A hectare of coppice yields about 0.75 tonnes of charcoal a year, and a
        single blast furnace making 300 tonnes of iron eats 900 tonnes of it. If
        you have not bought the woodland, the furnace idles.
        """
        # CACHED for material_price_factor(). project_cost() now calls that
        # once for every candidate node `available` considers, every year,
        # for every active project, and annual_material_demand() is
        # O(active + done); recomputing it from scratch on every one of those
        # calls is the quadratic blowup this codebase already had to fix once
        # for done_in_order() (see its own comment). Good for one step(): a
        # query between steps reads the demand as of the last one, which is
        # already true of price_index, self.economy and self.throttle itself.
        self._material_demand_cache = self.annual_material_demand()
        industrial, lab = self._throttle_demand_split(self._material_demand_cache)
        stock = self._material_stock()
        # IDEMPOTENT WHEN NOTHING HAS ACTUALLY CHANGED. protocol.py's own
        # `why` handler calls this twice in a row to build one message
        # (s.binding, then s.resource_throttle() again for the percentage)
        # with nothing mutated in between - read-only from its point of
        # view, which it always was before this, because there was nothing
        # here a second call could consume. Now there is: the stock this
        # function draws down must be spent once per genuine recomputation,
        # not once per CALL, or a query asked twice double-depletes it and
        # answers its own two calls with two different numbers. Keyed on the
        # CONTENT that feeds the computation below, including the year. A new
        # year is a new production flow and must bank another year's unused
        # mine output; repeated queries within that year must not. A test,
        # or a player, building a mine or a nitre bed mid-year and asking
        # again in the SAME year must see the new answer immediately, not a
        # stale replay - see test_regressions.py's own
        # "...and stops once your own supply covers the need", which does
        # exactly that). Unchanged content means replaying the cached
        # (worst, who) is not a shortcut, it is the actual answer.
        # ELECTRICITY. Computed here, not inside the stock loop below (see
        # the class comment on _electricity_demand_kw/generation_breakdown_kw
        # for why it never touches `stock`), but its have/need both have to
        # be part of the signature: dynamo, en_alternator and the other
        # generation nodes all carry mat={} (a capability/machine node, not
        # a material purchase), so finishing one changes generation_capacity_
        # kw without changing `industrial`/`lab`/mine_capacity/forest_ha/
        # nitre_bed_m2/stock at all - the exact case the cache below would
        # otherwise silently replay a now-stale (worst, who) for.
        elec_need = self._electricity_demand_kw()
        elec_have = self.generation_capacity_kw()
        sig = (self.year, tuple(sorted(industrial.items())), tuple(sorted(lab.items())),
               tuple(sorted(self.mine_capacity.items())), self.forest_ha,
               self.nitre_bed_m2, tuple(sorted(stock.items())),
               elec_need, elec_have)
        if sig == getattr(self, "_stock_throttle_sig", None):
            self.throttle, self.binding = self._stock_throttle_cache
            return self.throttle
        worst, who = 1.0, None
        if elec_need > 1e-9 and elec_have < elec_need:
            f = max(0.05, elec_have / elec_need)
            if f < worst:
                worst, who = f, "electricity"
        all_tags = set(industrial) | set(lab) | self._own_production_tags()
        for emp_key, tag in sorted(all_tags):
            ind_need = industrial.get((emp_key, tag), 0.0)
            lab_need = lab.get((emp_key, tag), 0.0)
            # Two different things, kept separate on purpose: OWN_AND_STOCK
            # is physically yours - a bed you built, a mine you sank, a
            # surplus banked from an earlier year - and can BANK again if
            # unused this year. `market` is a standing offer (how much the
            # empire's market would sell you, not what you bought), and
            # choosing not to buy it this year does not make it yours to
            # keep: banking unused MARKET headroom as though it were
            # inventory was the bug this split exists to avoid (a material
            # with a large generic market figure and no demand for years
            # would otherwise accumulate thousands of tonnes nobody ever
            # produced or paid for).
            own_and_stock = stock.get(emp_key, 0.0) + self._own_material_supply(tag)
            have = own_and_stock + self._material_market_tonnes(emp_key)
            # Lab-scale first, and unconditionally: drawn from whatever is
            # banked or flowing in this year, topped up by a direct purchase
            # this function never checks capacity for - "I would just buy
            # 20 grams," exactly. It can never be what sets `worst`/`who`.
            lab_drawn = min(lab_need, have)
            have -= lab_drawn
            consumed_ind = 0.0
            if ind_need > 1e-12:
                if have < ind_need:
                    f = max(0.05, have / ind_need)
                    if f < worst:
                        worst, who = f, emp_key
                    consumed_ind = have
                else:
                    consumed_ind = ind_need
            # BANK THE REST OF WHAT WAS YOURS. Own production (and prior
            # stock) this year that neither draw actually touched goes back
            # into stock rather than evaporating - the other half of the fix
            # (DOCS_VS_ENGINE.md #3). Capped at own_and_stock, never at the
            # larger `have`, for exactly the reason in the comment above.
            stock[emp_key] = max(0.0, own_and_stock - lab_drawn - consumed_ind)
        self.throttle, self.binding = worst, who
        # Stored AFTER mutation, against stock as this call actually left
        # it - so an immediate repeat call's sig (computed from that same,
        # now-settled stock) matches and replays rather than spending again.
        self._stock_throttle_sig = (sig[0], sig[1], sig[2], sig[3], sig[4],
                                     sig[5], tuple(sorted(stock.items())),
                                     sig[7], sig[8])
        self._stock_throttle_cache = (worst, who)
        if who:
            self.shortages[who] += 1
        return worst

    def project_resource_throttle(self, k):
        """Material throttle applicable to one active project.

        ``resource_throttle`` still performs the portfolio-level supply and
        stock accounting and identifies the binding pool.  The resulting
        scarcity must only slow work that draws from that pool, however; paper
        research does not become short of saltpetre because a gunpowder project
        is.  Consumers of the scarce pool share its aggregate factor, while
        projects with no matching input retain their full labour pace.
        """
        factor = self.resource_throttle()
        binding = self.binding
        if factor >= 0.999 or not binding:
            return 1.0
        if binding == "electricity":
            return factor if k in self._electricity_load_node_ids() else 1.0
        n = self.nodes.get(k) or {}
        coke = self.chosen_fuel(k) == "coke"
        for mat in (n.get("mat") or {}):
            effective_mat = ("coal_kg" if coke
                             and mat in ("charcoal_kg", "firewood_kg") else mat)
            # Gram-scale purchases never participate in the flow throttle.
            if effective_mat.endswith(self.LAB_SCALE_SUFFIX) \
                    and not effective_mat.endswith("_kg"):
                continue
            if self._material_tag(effective_mat)[0] == binding:
                return factor
        return 1.0

    def _cached_material_demand(self):
        """annual_material_demand(), reusing resource_throttle()'s cache when
        there is one. See the comment there."""
        d = getattr(self, "_material_demand_cache", None)
        return d if d is not None else self.annual_material_demand()

    def _cached_demand_by_tag(self):
        """_demand_by_supply_tag() of the current cached demand, computed
        once and reused for the rest of this tick.

        material_market_factor() now weighs EVERY material key a project
        buys (see its own comment on why it must, now that this is general
        rather than 13 hand-named keys), which means material_price_factor()
        can be called several times for one project_cost() call, and
        project_cost() itself is already called once per candidate node
        `available` considers, every year (see project_cost's own comment
        on why nothing here can afford to be quadratic). Grouping the
        demand dict is the one part of that path that is not already O(1),
        so it is done once per tick and kept, keyed by the demand dict's
        identity so a new tick (a new annual_material_demand() result)
        invalidates it automatically rather than by a second flag that
        could drift out of step with the first.

        THE CACHE ENTRY HOLDS `demand` ITSELF, NOT JUST `id(demand)` - the
        same defence `sim/engine/proto/nodes.py`'s own id()-keyed cache
        documents and takes, for the identical reason. `id()` is only
        unique among objects that are still alive: annual_material_demand()
        returns a brand-new Counter every call, the OLD one is dropped as
        soon as resource_throttle() overwrites self._material_demand_cache
        with the next year's, and CPython hands a freed small object's
        address to the very next same-sized allocation often enough that a
        later tick's Counter regularly landed at the exact address an
        earlier tick's had. `cached[0] == id(demand)` then read as true for
        two DIFFERENT ticks' demand, and this cache quietly replayed a
        stale grouping under a fresh year - the fourth `done_in_order()`-
        class bug (see that method's own docstring for the first three),
        found by bisecting `sim/repro_nondeterminism.py` back from a
        project's ph_left through project_cost() and material_market_factor()
        to material_price_factor() reading exactly this. Comparing `is
        demand` against a STRONG REFERENCE kept alongside the cached
        result, instead of comparing two bare integers, keeps that old
        Counter alive for as long as this cache entry might still be
        checked against it, so its address cannot be recycled into a false
        match while the entry is live - the collision is structurally
        impossible, not just unlikely, exactly as the nodes.py comment
        argues for the same shape of cache.
        """
        demand = self._cached_material_demand()
        cached = getattr(self, "_demand_by_tag_cache", None)
        if cached is not None and cached[0] is demand:
            return cached[1]
        by_tag = self._demand_by_supply_tag(demand)
        self._demand_by_tag_cache = (demand, by_tag)
        return by_tag

    def material_price_factor(self, emp_key):
        """What buying MORE of this tracked commodity costs beyond the flat
        catalogue price, from how hard current demand leans on the empire's
        market for it, versus how much of your own supply makes that market
        unnecessary.

        FINDINGS_ROUND2 section R: MARKET_SHARE was a supply ceiling with no
        price response at all -- buying up to it cost the same per tonne as
        buying one kilogram -- and nothing made owning your own supply make
        the material CHEAPER, only available. Both halves are here: `need`
        and `_material_market_tonnes(emp_key)` are resource_throttle()'s own
        figures, so demand approaching the market ceiling raises the price on
        the same saturating curve labour_price_factor uses (negligible at a
        fifth of the ceiling, roughly double at the whole of it); owning
        enough of your own extraction (mine_capacity, forest_ha,
        nitre_bed_m2) to cover the need removes the premium rather than
        merely making the tonnes exist. This is the actual mechanism behind
        "the price of iron fell because supply rose": opening a mine lowers
        what iron costs YOU, specifically because you stop having to buy it
        at the margin.

        Groups demand the same way resource_throttle() now does
        (_demand_by_supply_tag): the same "checked each key alone" gap
        applied here too, understating the price pressure of a wire-heavy
        electrical age on copper by looking at copper_kg's share in
        isolation from copper_wire_kg's.

        GENERALISED: this used to return exactly 1.0, immediately, for any
        commodity id not already sitting in the hand-written MARKET_SHARE
        dict above - the actual mechanism by which COMMODITY_DYNAMISM.md's
        149 inert material keys never moved at all ("the function's own
        code explains why... it returns 1.0 immediately"). That early
        return is gone: `market` now falls back through
        _material_market_tonnes' own generic default, so an arbitrary
        commodity id (curated or not) reaches the same saturating curve
        the 9 originally-tracked ones always used.
        """
        market = self._material_market_tonnes(emp_key)
        worst = 1.0
        # GROUPED BY emp_key, ONCE A TICK, not scanned-and-filtered from the
        # whole by-tag dict on every one of THIS function's own calls. See
        # _demand_by_emp_key's comment: this is the same "called once per
        # material a project buys, once per candidate node, every year"
        # volume _cached_demand_by_tag() was already added to answer, one
        # level further in. Only max() is taken below, order-independent,
        # so - as with _cached_demand_by_tag's own dict - no sort is needed
        # for the result to be deterministic.
        for tag, need in self._demand_by_emp_key().get(emp_key, ()):
            if need <= 0:
                continue
            supply = max(1e-9, self._own_material_supply(tag) + market)
            share = min(1.5, need / supply)
            worst = max(worst, 1.0 + 0.9 * share * share)
        return worst

    def _demand_by_emp_key(self):
        """_cached_demand_by_tag(), grouped by emp_key - the grouping
        material_price_factor() actually wants. Cached the same tick-
        scoped way _cached_demand_by_tag() itself is, INCLUDING keeping a
        strong reference to `demand` in the cache entry rather than
        comparing bare `id()` integers - see that method's own comment for
        why a bare id() is not safe here (a freed Counter's address gets
        reused often enough that two different ticks compared equal by
        allocator luck alone, which is what made this pair of caches the
        fourth `done_in_order()`-class non-determinism bug, not a
        hypothetical one). A new tick produces a new annual_material_demand()
        result, which invalidates both caches together automatically."""
        demand = self._cached_material_demand()
        cached = getattr(self, "_demand_by_emp_key_cache", None)
        if cached is not None and cached[0] is demand:
            return cached[1]
        grouped = {}
        for (ek, tag), need in self._cached_demand_by_tag().items():
            grouped.setdefault(ek, []).append((tag, need))
        self._demand_by_emp_key_cache = (demand, grouped)
        return grouped

    def material_market_factor(self, k):
        """A project's price pressure from the materials it buys, weighted
        by how many kilograms of each -- the same weighting `_material_cost`
        already uses implicitly by summing kilogram costs.

        GENERALISED: every material key a node names now gets weighed in,
        not only the 13 MATERIAL_CHECKS ever listed by hand. Before this,
        a project buying nothing but glass, silk or aluminium got exactly
        1.0 back - not a small effect, no effect, because the `continue`
        below skipped every one of them (see COMMODITY_DYNAMISM.md: "it
        simply skips any material key not in MATERIAL_CHECKS"). Skipping
        was correct only in the sense that this file could not yet answer
        a price for those materials; now it can (_material_tag /
        material_price_factor's own generalisation), so it does.
        """
        mat = self.nodes[k].get("mat") or {}
        if not mat:
            return 1.0
        total_kg, weighted = 0.0, 0.0
        for m, q in sorted(mat.items()):
            emp_key = self._material_tag(m)[0]
            q = float(q)
            total_kg += q
            weighted += q * self.material_price_factor(emp_key)
        return (weighted / total_kg) if total_kg else 1.0

    def material_market_summary(self):
        """Every raw material currently carrying a real price premium
        because your own demand is leaning on what the market will sell -
        the generalised, aggregate version of material_price_factor(), the
        way goods_market_summary() already is for goods_market_factor().

        A PLAYER MUST SEE IT. Before this pass a material's price response
        was invisible even for the 9 tracked commodities (nothing
        aggregated it for `money`) and non-existent for the other 149; now
        that every material key responds (see material_price_factor's own
        comment), a player whose project costs rose because they are
        buying a lot of one thing, or fell because they sank their own
        mine in it, needs a place that says so in aggregate, not just a
        per-project `why`.
        """
        demand = self._cached_material_demand()
        if not demand:
            return None
        rows, seen = [], set()
        for mat in sorted(demand):
            if demand[mat] <= 0:
                continue
            emp_key = self._material_tag(mat)[0]
            if emp_key in seen:
                continue
            seen.add(emp_key)
            f = self.material_price_factor(emp_key)
            if f > 1.05:
                rows.append((emp_key, f))
        if not rows:
            return None
        rows.sort(key=lambda kv: -kv[1])
        worst = rows[0]
        return ("%d material%s trading above book price because your own "
                "demand is leaning on what the market will sell: worst is "
                "%s at %d%% of book. Sinking your own mine or production "
                "capacity in it brings this back down, the same way it "
                "does for iron - 'quote mine %s' shows the price"
                % (len(rows), "" if len(rows) == 1 else "s",
                   worst[0], round(worst[1] * 100), worst[0]))

    def wire_chain_report(self, wire_t_per_yr):
        """Would THIS shortfall in copper wire actually be a copper shortage,
        or is the wire-drawing bench itself the bottleneck? Named against a
        real link in the tree (el2_three_wire_distribution_system alone
        wants 5 t of copper_wire_kg in one build; the whole electrical
        branch wants far more), because resource_throttle()'s `binding` can
        only ever say "copper" -- it has no notion that copper_wire_kg is
        COPPER, manufactured, not a second independent shortage.

        This is `commodities.py`'s `CommodityLedger.propagate_demand()`
        (COMMODITIES.md section 7, "the real test": a chained shortage
        attributed to whichever link actually broke), handed THIS
        civilisation's actual reachable copper -- resource_throttle()'s own
        `_own_material_supply("mine:copper") + _material_market_tonnes
        ("copper")` -- via `supply_override`, instead of
        commodities.json's own separate national estimate. The two
        happen to agree for Rome (both read from the same
        resources.json/economy.py MARKET_SHARE figures) but would not for a
        civilization with a different mineral_scale, which is exactly why
        overriding with the live number rather than trusting the static one
        matters.
        """
        supply_t = (self._own_material_supply("mine:copper")
                    + self._material_market_tonnes("copper"))
        ledger = _commod.CommodityLedger(supply_override={"copper": supply_t})
        return ledger.propagate_demand("copper_wire", max(0.0, float(wire_t_per_yr)))

    # Capital to create one tonne per year of standing extraction capacity, and
    # the recurring cost of actually getting that tonne out. DERIVED, not
    # measured: a Roman coal hewer working a shallow drift wins on the order of
    # a tonne a day, so 250 t/yr a man, and the miner wage of 0.09 den/hr over
    # 2000 hours is 180 den a year, giving roughly 0.7 den per tonne in wages
    # before haulage. Doubling it for haulage, timbering and overseers gives the
    # figures below. Metal ores cost far more per tonne of METAL because of the
    # ore grade and the smelting, and the capital rises with depth and drainage.
    # Gold is here because a tester asked the obvious question about debasement:
    # "what if you build a mine that can mine gold?" If the money is being ruined
    # by having less silver in it, a man who digs his own metal is not ruined with
    # it. Roman gold (Dacia, Las Medulas) was mined at enormous cost and that is
    # what the capex says.
    MINE_CAPEX_PER_T_YR = {"coal": 9.0, "iron": 60.0, "copper": 240.0,
                           "lead": 80.0, "tin": 420.0, "silver": 9000.0,
                           "gold": 160000.0}
    MINE_OPEX_PER_T     = {"coal": 1.5, "iron": 12.0, "copper": 55.0,
                           "lead": 18.0, "tin": 95.0, "silver": 2200.0,
                           "gold": 42000.0}
    MINE_LEAD_YEARS = 3.0        # sinking, drainage, roads, and hiring

    # ---- A GENERIC PRODUCTION LEVER FOR ANY MATERIAL, NOT ONLY THESE SEVEN ---
    #
    # COMMODITY_DYNAMISM.md's aluminium test, verified by running the engine
    # directly: "no mine, no supply lever of any kind for it... Nothing in
    # economy.py even contains the string 'aluminium.' Producing an enormous
    # amount of it via electrolysis tech changes nothing." open_mine() used
    # to answer nothing at all (a bare `return 0.0`) for any material not in
    # MINE_CAPEX_PER_T_YR above - a literal seven-name dictionary, chosen
    # because those seven are real, well-sourced figures (Roman wage
    # evidence, attested workings) and they stay exactly as they are here.
    # For every other material - not just aluminium, whatever the tech tree
    # is ever extended to include - GENERALISE rather than special-case: the
    # seven curated figures already show capex tracking a material's own
    # book price closely (iron 1.0 den/kg -> capex 60, copper 4.0 -> 240,
    # both a 60x multiple; tin 10.0 -> 420, ~42x; silver 317 -> 9000, ~28x;
    # gold 3440 -> 160000, ~46x - a 30-60x band holding across four decades
    # of price). 50, the middle of that band, is the generic multiple.
    # Running cost tracks capex at close to a fifth across the same seven
    # (12/60=0.20, 55/240=0.229, 18/80=0.225, 95/420=0.226, 2200/9000=0.244,
    # 42000/160000=0.2625 - all 0.20-0.26), so generic opex is 0.22x generic
    # capex. This is a real, general production lever - sink capital, wait
    # out MINE_LEAD_YEARS, pay to keep it standing - for whatever material
    # an unanticipated recipe needs, not a rule written for aluminium by name.
    GENERIC_MINE_CAPEX_MULTIPLE = 50.0
    GENERIC_MINE_OPEX_SHARE = 0.22
    GENERIC_MINE_CAPEX_FLOOR = 5.0
    GENERIC_MINE_CAPEX_CEILING = 400000.0

    def _mine_capex_opex(self, mat):
        """(capex per t/yr to sink, opex per t/yr to run) for standing
        production of `mat` - the curated figure for the seven originally
        tracked metals, unchanged; a generic figure derived from the
        material's own book price (see the class comment above) for
        anything else this file can price at all. (None, None) for a name
        nothing prices - the only way this stays "no such material,"
        rather than an arbitrary string being accepted."""
        if mat in self.MINE_CAPEX_PER_T_YR:
            return self.MINE_CAPEX_PER_T_YR[mat], self.MINE_OPEX_PER_T.get(mat, 0.0)
        price = self._book_price_per_kg(mat)
        if price is None or price <= 0:
            return None, None
        capex = max(self.GENERIC_MINE_CAPEX_FLOOR,
                    min(self.GENERIC_MINE_CAPEX_CEILING,
                        self.GENERIC_MINE_CAPEX_MULTIPLE * price))
        return capex, capex * self.GENERIC_MINE_OPEX_SHARE

    def _mine_capex(self, mat):
        capex, _opex = self._mine_capex_opex(mat)
        return capex

    def _mine_opex(self, mat):
        _capex, opex = self._mine_capex_opex(mat)
        return 0.0 if opex is None else opex

    def mineable(self, mat):
        """Can you sink standing production capacity in this material at
        all? True for the seven curated metals and, generalised, for any
        material key or curated commodity id this file can find a book
        price for - which in practice is anything a node in the tech tree
        actually buys, since every one of those has a prices.json entry by
        construction (data.py's own load() could not have computed
        `_material_cost` otherwise). False only for a name that prices
        nothing at all: a typo, not a real gap."""
        return self._mine_capex(self._normalize_material_name(mat)) is not None

    def mine_catalog_hint(self):
        """What to tell a player who typed a material name this file
        cannot price. This used to be a hard, closed list of seven
        hand-named metals (see COMMODITY_DYNAMISM.md); the list itself is
        still worth naming as the well-sourced headline cases, but it is no
        longer the whole answer."""
        named = ", ".join(sorted(self.MINE_CAPEX_PER_T_YR))
        return ("well-known workings: %s - or any other material key the "
                "tree uses (for example aluminium_kg), priced from its own "
                "book price if nothing more specific is known about it"
                % named)

    # ---- LAND: what is under your feet is geography, not standing --------
    #
    # open_mine()'s ceiling used to depend only on patronage and state
    # capacity, the SAME number for every material: a founder with an
    # imperial patron could sink exactly as large a tin mine as an iron one,
    # in a home province with no tin in it at all. A tester asked the
    # obvious question this gets wrong: "if I need a lot of coal, can I open
    # a lot of coal mines? Are mines limited by land area?" No, and yes they
    # should be. geography.py's mineral_scale() ALREADY answers "how much of
    # this material's national output can THIS civilisation reach," built
    # from geography.json's per-region mineral abundance and this
    # civilization's own home_regions and reach (see its own comment) -- and
    # it already governs the MARKET half of supply (_material_market_tonnes).
    # It had simply never been asked about the OWN-MINE half. Reusing it
    # here, rather than inventing a second geology signal, means a civ that
    # cannot buy much tin also cannot simply out-organise its way to
    # unlimited tin by sinking shafts instead -- the same ground is short
    # either way. Measured: a Rome run's mineral_scale sits at roughly
    # 1.0-1.2 for every metal but saltpetre (it controls most of its own
    # ore-bearing provinces); Mexica sits at 0.10-0.17 for iron and coal
    # (Mesoamerica genuinely worked neither) and 0.47 for copper (it did).
    def mine_land_ceiling(self, mat):
        """The largest standing capacity of this material you could ever
        organise, in tonnes/yr: how big an enterprise your standing and
        state can run, times whether the ore is actually under your feet,
        times what mining technology currently lets a working pull out of a
        given deposit (mining_tech()'s own yield multiplier -- see its
        comment for why a pump or a railway belongs on THIS side of the
        ledger and not only on cost)."""
        sc = float(self.civ.get("state_capacity", 0.5))
        if self.running("patron_imperial"):     base = 20000.0 + 60000.0 * sc
        elif self.running("patron_senatorial"): base = 9000.0 + 20000.0 * sc
        elif self.has("citizenship"):       base = 6000.0 + 8000.0 * sc
        else:                               base = 3000.0 + 4000.0 * sc
        base *= 1.0 + min(5.0, max(0.0, self.revenue()) / 60000.0)
        geo = self.mineral_scale(mat)
        yld, _cost = self.mining_tech(mat)
        return base * geo * yld

    # ---- DEPLETION: the easy seam runs out ---------------------------
    #
    # A tester's second question: "does mine production go down over time,
    # as you mine the easy stuff and it gets harder?" It did not -- output
    # was flat for ever, which is not how any real working behaves. What is
    # tracked is not raw tonnes extracted (an arbitrary absolute figure with
    # no natural scale to compare it to across seven wildly different
    # materials and five civilizations) but INTENSITY: how many YEARS you
    # have worked this material at what fraction of its own land ceiling.
    # Mining at 20% of what the ground could ever support barely touches the
    # easy ore; mining at 100% of it, continuously, is exactly the situation
    # that historically forced a working deeper, or somewhere else, inside a
    # few generations. DEPLETION_HALF_LIFE_YRS=120 is a [C] estimate at that
    # order of magnitude (roughly the span across which real long-worked
    # Old World deposits -- Rio Tinto's and Laurion's near-surface ore --
    # went from rich to markedly poorer and needed new technique, several
    # human generations, not one and not a thousand), chosen deliberately
    # round rather than fitted to any single citation. Floored at 0.5,
    # never lower: the easy half of a deposit running out does not mean the
    # hard half is worthless, and a floor that could reach zero would be the
    # abolished "unobtainable" category wearing a new name (see open_mine's
    # own comment on that history). This is intensity-years, not calendar
    # years, so it accrues faster the harder you lean on a given deposit
    # relative to what the ground can support -- and slower once technology
    # (mining_tech(), below) raises that support, which is the whole of
    # "make depletion something you can fight."
    DEPLETION_HALF_LIFE_YRS = 120.0
    DEPLETION_FLOOR = 0.5

    # ---- A WORKING IS A THING, NOT AN ENTRY IN A MATERIAL-KEYED DICT -------
    #
    # A player who had won the game asked for exactly this: which mine,
    # rated capacity, actual output, cost, utilisation, the year it came on
    # stream, and whether it is a real supply or merely an asset sitting on
    # the books. None of that could be answered before, because there was no
    # "it" - self.mine_capacity was one float per material, open_mine()
    # added to it, and depletion (below) aged the WHOLE material at once, so
    # a shaft opened in year 400 was exactly as worked-out as one opened
    # three centuries earlier purely because they shared a material key.
    # self.mines is the fix: a list of actual workings, each its own dict
    # with the material it raises, its rated capacity, the year it was
    # commissioned, what it cost to sink, and its OWN depletion clock
    # (intensity_yrs) running from that year, not from whenever the
    # material was first touched. self.mine_capacity below is now a
    # PROPERTY summed over this list - the "six bugs in a week from a fact
    # living in two places" the job asked not to repeat - so it can be read
    # everywhere it already was, but nothing can silently drift it out of
    # step with the workings that actually make it up.
    def _workings_of(self, mat):
        """This civilisation's own workings raising `mat`, in the order they
        were commissioned (self.mines is append-only in commission order,
        never hash-ordered, so this is deterministic across runs)."""
        return [w for w in getattr(self, "mines", ()) if w.get("material") == mat]

    @property
    def mine_capacity(self):
        """Rated capacity of your own workings, summed by material -
        DERIVED from self.mines, not a second number that has to agree with
        it. Read-only: opening, closing and mothballing a working all act
        on self.mines itself (see open_mine/commission_mines/close_mine/
        mothball_mines), and this recomputes from whatever that list says."""
        out = {}
        for w in getattr(self, "mines", ()):
            out[w["material"]] = out.get(w["material"], 0.0) + w["capacity"]
        return out

    def mine_depletion_factor_for(self, working):
        """Fraction of day-one yield THIS working still gets, from ITS OWN
        cumulative intensity since ITS OWN commissioning year (see the class
        comment above `_workings_of`) - the per-working half of the fix."""
        i = working.get("intensity_yrs", 0.0)
        return max(self.DEPLETION_FLOOR, 1.0 - i / self.DEPLETION_HALF_LIFE_YRS)

    def mine_depletion_factor(self, mat):
        """This material's CURRENT typical depletion, as the
        capacity-weighted average across your existing workings of it - used
        to price a NEW working before it has any history of its own (see
        mining_cost_scale/mine_quote/open_mine: the ground here is however
        worked-out your existing shafts say it is) and for the one-line
        summary mine_depletion_note() gives. A material with no workings yet
        has no history to weight, so this is 1.0: the book price, day one."""
        workings = self._workings_of(mat)
        total = sum(w["capacity"] for w in workings)
        if total <= 0:
            return 1.0
        return sum(self.mine_depletion_factor_for(w) * w["capacity"]
                   for w in workings) / total

    def _advance_mine_depletion(self):
        """One year of intensity for every working you currently hold,
        each aged from ITS OWN commissioning year rather than the
        material's. Called once a year from commission_mines(), which
        core.py's step() already calls exactly once a year -- see that
        function's own comment -- so this needed no new call site.

        Iterates self.mines (a list, in commission order) and caches
        mine_land_ceiling() per material seen rather than per working, so
        this is neither hash-ordered (self.mines is a list) nor quadratic in
        the number of workings of one material."""
        ceilings = {}
        for w in getattr(self, "mines", ()):
            mat = w["material"]
            if mat not in ceilings:
                ceilings[mat] = max(1.0, self.mine_land_ceiling(mat))
            w["intensity_yrs"] = w.get("intensity_yrs", 0.0) + w["capacity"] / ceilings[mat]

    # ---- TECHNOLOGY: the pump, the railway and cheap steel fight back -----
    #
    # A tester's third question, and the important one: does technology
    # raise yield? It did not, anywhere in the model, which is a real
    # modelling error -- industrialisation paid for itself largely because
    # the pumping engine, the railway and cheap steel made ore worth
    # lifting that was not worth lifting before. Each entry below is a real
    # node (grepped for steam/pump/newcomen/railway/blast/bessemer/
    # explosive/nitro/drill against the actual tree, not invented): `yield`
    # raises mine_land_ceiling() AND mine_depletion_factor()'s effective
    # output together (a pump does not just let you sink a new shaft, it
    # means the shaft you already have stops standing idle half-flooded);
    # `cost` lowers what sinking or running a tonne/yr costs (mining_cost_
    # scale(), below). Multipliers COMPOUND across every one built, the
    # same pattern best_multiplier() in commodities.py uses for gold's
    # pump-times-cyanidation ~20x, because pumping and blasting and a
    # railway are independent improvements, not alternatives.
    MINING_TECH = {
        # Drainage. A flooded shaft simply stops, whatever is below the
        # water table; a pump makes that ore reachable at all (a land-
        # ceiling effect) and removes the single largest recurring cost of
        # a deep working, bailing by hand or beast (a cost effect).
        # met_mine_pumping is any mechanical lift (water-wheel or animal);
        # steam_atmospheric IS the Newcomen engine, built specifically to
        # drain flooding coal and tin workings, so it is both a later tier
        # and a stronger effect on the same problem, and the two compound.
        "met_mine_pumping":          {"yield": 1.4, "cost": 0.85},
        "steam_atmospheric":         {"yield": 1.6, "cost": 0.65},
        # Blasting and drilling break rock faster per man-hour. They do not
        # put new ore in the ground, so cost only, no yield term.
        "met_black_powder_blasting": {"yield": 1.0, "cost": 0.85},
        "met_dynamite_blasting":     {"yield": 1.0, "cost": 0.65},
        "pwr_rotary_drilling":       {"yield": 1.0, "cost": 0.80},
        # A railway does not create ore, it creates REACH: ore too far from
        # a market to be worth carting becomes worth lifting once a railway
        # can move it, which is a yield (economically-reachable tonnage)
        # effect, not a per-tonne extraction-cost effect. Reused from
        # goods_reach_factor()'s own self.running("railway") check.
        "railway":                   {"yield": 1.3, "cost": 1.0},
    }
    # Iron and coal only. For iron this is the specific historical claim
    # the job is about: cheap steel did not change how ore comes out of the
    # ground, it changed whether digging LOW-GRADE ore was worth doing at
    # all. For coal the link runs the other way -- a cheap-steel industry
    # is a coking-coal customer large enough to justify the pit, drainage
    # and rail spur that a smaller demand would not -- but the direction of
    # the effect (more worth digging, cheaper to sink) is the same, so it
    # is applied the same way rather than invented as a second mechanism.
    # blast_furnace and mat_bulk_steel (Bessemer/open-hearth) are the two
    # real steps of that in the tree, each further from ore than the last.
    MINING_TECH_STEEL = {
        "blast_furnace":  {"yield": 1.3, "cost": 0.85},
        "mat_bulk_steel": {"yield": 1.3, "cost": 0.75},
    }

    def mining_tech(self, mat):
        """(yield_mult, cost_mult) technology has bought this material's
        mining so far. yield_mult >= 1 raises what a working can pull out
        of the same deposit; cost_mult <= 1 lowers what getting it out
        costs. Capped/floored like every other compounding factor in this
        file (MARKET_SHARE, goods_reach_factor): a mine at three times the
        book yield is a real historical claim, thirty times is the
        abolished unobtainable category with its sign flipped."""
        y, c = 1.0, 1.0
        techs = self.MINING_TECH
        if mat in ("iron", "coal"):
            techs = dict(techs, **self.MINING_TECH_STEEL)
        for node in sorted(techs):
            if self.running(node):
                y *= techs[node]["yield"]
                c *= techs[node]["cost"]
        return min(y, 3.0), max(0.35, c)

    def mining_cost_scale(self, mat):
        """What sinking or running a tonne/yr of this material costs THIS
        YEAR, relative to MINE_CAPEX_PER_T_YR/MINE_OPEX_PER_T's own book
        price: technology (mining_tech's cost multiplier) against depletion
        (mine_depletion_factor, inverted -- the same effort recovers less
        from a half-worked deposit, so it costs proportionally more per
        tonne) pulling against each other. This is "deeper ones cost more"
        made concrete, and technology is the only thing that pushes back.
        Bounded to keep the tension a real decision rather than a runaway:
        a fully depleted, untooled working costs at most 2x book (not
        infinite), and full mining technology on a fresh deposit costs no
        less than 0.4x (not free)."""
        _y, cost = self.mining_tech(mat)
        return max(0.4, min(2.5, cost / self.mine_depletion_factor(mat)))

    def mining_cost_scale_for(self, working):
        """Same as mining_cost_scale(), but for what running THIS working
        costs this year, from ITS OWN depletion rather than its material's
        average - an old, half-worked shaft costs more per tonne to keep
        running than a fresh one of the same material, which the old
        material-level figure could not say because it had no idea which
        working was which."""
        _y, cost = self.mining_tech(working["material"])
        return max(0.4, min(2.5, cost / self.mine_depletion_factor_for(working)))

    def mine_yield_t_for(self, working):
        """Tonnes a year THIS working actually raises this year, after ITS
        OWN depletion and current mining technology."""
        yld, _cost = self.mining_tech(working["material"])
        return working["capacity"] * self.mine_depletion_factor_for(working) * yld

    def mine_operating_cost_for(self, working):
        """What THIS working costs to run this year, whether or not you use
        what it raises - mine_operating_cost()'s per-working figure, the one
        `mines` shows against each row."""
        mat = working["material"]
        return (working["capacity"] * self._mine_opex(mat) * self.price_index
                * self.mining_cost_scale_for(working))

    def mine_quote(self, mat, t_per_yr):
        """What a mine would cost, BEFORE you commit to it.

        A tester asked for one tonne of gold a year - the same order as the
        example in the help text - and went from 38,151 denarii to zero on a
        single command, with no price shown and no way to ask. Five years later
        the workings were mothballed for non-payment and they were in debt
        bondage. Every other purchase in this game quotes before it charges.
        """
        mat = self._normalize_material_name(mat)
        cap, opex_per_t = self._mine_capex_opex(mat)
        if cap is None:
            return None
        t = max(0.0, float(t_per_yr))
        scale = self.mining_cost_scale(mat)
        sink = t * cap * self.price_index * scale
        opex = t * opex_per_t * self.price_index * scale
        ceiling = self.mine_land_ceiling(mat)
        room = max(0.0, ceiling - self.mine_capacity.get(mat, 0.0)
                   - self.mine_pending.get(mat, 0.0))
        depl = self.mine_depletion_factor(mat)
        note = ("The yearly cost is charged whether or not you use the "
                "output, and goes on until you close it. Mothballing is "
                "not free to reverse: the shaft floods and the crew "
                "disperses, so reopening means sinking it again.")
        if scale > 1.05:
            note += (" This costs %.0f%% of the book price: the easy ore "
                      "here is going, and nothing you have built yet cuts "
                      "the cost of getting at what is left (mine pumping, "
                      "blasting, or a railway would)." % (scale * 100))
        elif scale < 0.95:
            note += (" This costs %.0f%% of the book price: what you have "
                      "built has made this cheaper to get out of the "
                      "ground." % (scale * 100))
        return {"material": mat,
                "tonnes_per_year": round(t, 3),
                "to_sink_it": round(sink, 1),
                "every_year_it_stands": round(opex, 1),
                "years_before_it_produces": self.MINE_LEAD_YEARS,
                "you_have": round(self.capital, 1),
                "you_could_raise": round(self.spending_power("buy"), 1),
                "you_can_afford_about": round(
                    self.spending_power("buy") / max(cap * self.price_index * scale, 1e-9), 3),
                "afford_means": "cash plus half the credit line, which is what "
                                "a lender will advance against a purchase",
                "the_ground_here_could_ever_support": round(ceiling, 1),
                "room_left_before_geology_stops_you": round(room, 1),
                "current_yield_is_this_fraction_of_day_one": round(depl, 3),
                "note": note}

    def mine_yield_t(self, mat):
        """Tonnes a year ALL your workings of this material actually raise
        this year, after each one's OWN depletion and current technology --
        the number `mines` should show summed, not the nominal tonnage
        sunk. Same figure _own_material_supply("mine:"+mat) computes;
        exposed directly so a command surface does not have to know that
        tag-string convention to ask. Sums mine_yield_t_for() over
        _workings_of(mat), a list in commission order, so this needs no
        sorted() to stay deterministic across hash seeds."""
        return sum(self.mine_yield_t_for(w) for w in self._workings_of(mat))

    def _mine_depletion_note_from(self, depl, yld):
        """Shared sentence-builder behind mine_depletion_note() (a
        material's average) and mine_depletion_note_for() (one working's
        own figures) - the same wording either way, just fed a different
        depletion fraction."""
        if abs(depl - 1.0) < 0.01 and abs(yld - 1.0) < 0.01:
            return None
        bits = []
        if depl < 0.999:
            bits.append("the easy ore here is %d%% worked out, so the same "
                        "shaft yields %d%% of its first-year tonnage"
                        % (round((1.0 - depl) * 100), round(depl * 100)))
        if yld > 1.001:
            bits.append("technology you have built raises that back up "
                        "%.1fx" % yld)
        elif depl < 0.999:
            bits.append("mine pumping, drilling or blasting would raise it "
                        "back up")
        return "; ".join(bits)

    def mine_depletion_note(self, mat):
        """One sentence on why this material's workings, ON AVERAGE, yield
        less than the tonnage sunk into them - for the same reason
        goods_market_note() exists for a concern's revenue: a player whose
        coal yield has fallen over the decades must be able to find out why
        without guessing. None if there is nothing to explain (no workings,
        or a fresh one with no relevant technology). See
        mine_depletion_note_for() for the SAME sentence about one
        particular working rather than the material's blended average."""
        if not self._workings_of(mat):
            return None
        yld, _cost = self.mining_tech(mat)
        return self._mine_depletion_note_from(self.mine_depletion_factor(mat), yld)

    def mine_depletion_note_for(self, working):
        """mine_depletion_note(), for one working's OWN depletion rather
        than its material's average across every working of it - the
        figure the `mines` row for this specific working should explain."""
        yld, _cost = self.mining_tech(working["material"])
        return self._mine_depletion_note_from(
            self.mine_depletion_factor_for(working), yld)

    def close_mine(self, mat):
        """Shut your own workings down, on purpose.

        The engine mothballs mines it cannot pay for and there was no way for a
        player to ask. A tester was billed 28.1 a year in perpetuity for a gold
        mine producing 0.0 tonnes and could do nothing about it.
        """
        mat = self._normalize_material_name(mat)
        workings = self._workings_of(mat)
        pend = [t for t in getattr(self, "mine_tranches", []) if t[0] == mat]
        if not workings and not pend:
            return False, ("you have no %s workings, and none being sunk" % mat
                           if self.mineable(mat)
                           else "no such material: %s. %s"
                                % (mat, self.mine_catalog_hint()))
        # Each working's OWN cost, not the material average - closing two
        # workings of very different ages must save exactly what those two
        # were actually costing, not a figure blended across every shaft of
        # this material as if they were all worked equally hard.
        saved = sum(self.mine_operating_cost_for(w) for w in workings)
        self.mines = [w for w in getattr(self, "mines", [])
                     if w.get("material") != mat]
        self.mine_tranches = [t for t in getattr(self, "mine_tranches", [])
                              if t[0] != mat]
        self.log.append((self.year, "you close the %s workings" % mat))
        return True, ("the %s workings are closed. You stop paying %.0f a year. "
                      "What you spent sinking them is gone, and reopening means "
                      "sinking them again." % (mat, saved))

    def open_mine(self, mat, t_per_yr, partial=True):
        """Open your own workings.

        The model used to treat the Empire's ATTESTED output as a hard ceiling,
        so a founder who needed twenty thousand tonnes of coal a year simply
        never got it and sat throttled for centuries. That is the unobtainable
        fallacy wearing different clothes. Rome mined almost no coal because
        almost nobody wanted coal, not because the coal was not there: Britain,
        Gaul and Spain are sitting on it, and Roman engineers already sink
        shafts, drive adits and drain them with wheels at Rio Tinto and Las
        Medulas. If you know what coke is for, you open a mine.

        What it is NOT is free or instant. You pay to sink it, you wait for it,
        and you pay every year to work it.
        """
        if t_per_yr <= 0:
            return 0.0
        mat = self._normalize_material_name(mat)
        cap = self._mine_capex(mat)
        if cap is None:
            return 0.0
        # Scale beyond a local lease needs a concession, which in practice means
        # the fiscus. Metalla were largely imperial property.
        # The ceiling is about STANDING, STATE CAPACITY AND GEOLOGY -- see
        # mine_land_ceiling()'s own comment for why it is geology now, not
        # standing alone, and for why a society with little state capacity
        # genuinely cannot organise a very large mine while a chieftain who
        # can raise a crew can still do better than a foreigner with a local
        # lease. Without the state-capacity/revenue half of this the Norse
        # run ended with 259 million denarii unspent and no iron mine, capped
        # at 3,600 tonnes a year by institutions that civilization does not
        # have; without the geology half, a founder could sink a tin mine in
        # a province with no tin in it, at the same size as one with plenty.
        ceiling = self.mine_land_ceiling(mat)
        have_cap = self.mine_capacity
        t_per_yr = min(t_per_yr, max(0.0, ceiling - have_cap.get(mat, 0.0)
                                          - self.mine_pending.get(mat, 0.0)))
        if t_per_yr <= 0:
            return 0.0
        # DEEPER ONES COST MORE. mining_cost_scale() is 1.0 on a fresh
        # deposit with no relevant technology, so this changes nothing for
        # an early game; it rises as a deposit already worked hard is asked
        # for more, and falls back down with mine pumping, drilling,
        # blasting or a railway -- see that method's own comment.
        scale = self.mining_cost_scale(mat)
        cost = t_per_yr * cap * self.price_index * scale
        if cost > self.capital:
            # A COMMAND YOU TYPED IS NOT A STANDING ORDER TO SPEND EVERYTHING.
            # This quietly took every denarius a break tester had and handed
            # back 22% of the mine they asked for. `hire` refuses and quotes
            # the price; so should this. The automatic policy (auto_mine) still
            # buys what it can afford, because that is the whole of its job:
            # it is spending spare cash on a bottleneck, not answering a
            # request for a particular mine.
            if not partial:
                return 0.0
            t_per_yr = self.capital / (cap * self.price_index * scale)
            cost = self.capital
        if t_per_yr <= 0:
            return 0.0
        self.capital -= cost
        # Each investment is its own working with its own sinking time. Pooling
        # them and taking the LATEST ready date meant a player who invested
        # spare cash every year, which is exactly what a poor civilization must
        # do, pushed the finish line back annually and never got any capacity at
        # all: a playtester funded sixty consecutive years and ended with an
        # empty mine_capacity. It also means each tranche becomes its own
        # WORKING once it commissions (see commission_mines) rather than
        # being folded into one number for the material - `cost` is carried
        # along so that working can say what it actually cost to sink, not
        # a figure recomputed later against a price_index that has since moved.
        self.mine_tranches = getattr(self, "mine_tranches", [])
        self.mine_tranches.append([mat, t_per_yr, self.year + self.MINE_LEAD_YEARS, cost])
        self.mine_pending[mat] = self.mine_pending.get(mat, 0.0) + t_per_yr
        return t_per_yr

    def commission_mines(self):
        """Move finished tranches from pending into standing workings
        (self.mines), tranche by tranche. Each tranche becomes exactly one
        working, commissioned in the year it actually came on stream (the
        tranche's own `ready` year, which is when its own depletion clock
        starts - see _advance_mine_depletion) - not merged into any other
        working of the same material, so a shaft opened in year 400 stays
        a distinct, unworn thing next to one opened three centuries before
        it."""
        self.mines = getattr(self, "mines", [])
        still = []
        for tranche in getattr(self, "mine_tranches", []):
            mat, amount, ready = tranche[0], tranche[1], tranche[2]
            # capex_paid: absent on a tranche written by a save from before
            # this field existed (see SAVE_FIELDS/load_state) - honestly
            # unknown, not fabricated, so 0.0 rather than a guess.
            capex_paid = tranche[3] if len(tranche) > 3 else 0.0
            if self.year >= ready:
                self.mines.append({"material": mat, "capacity": amount,
                                   "opened_year": ready, "capex_paid": capex_paid,
                                   "intensity_yrs": 0.0})
                self.mine_pending[mat] = max(0.0, self.mine_pending.get(mat, 0.0) - amount)
                if self.mine_pending.get(mat, 0.0) <= 0:
                    self.mine_pending.pop(mat, None)
            else:
                still.append(tranche)
        self.mine_tranches = still
        # ONE YEAR OF DEPLETION. core.py's step() calls commission_mines()
        # exactly once a year (see its own comment, "materials: buy the
        # woodland... before the shortage bites"), so this needed no new
        # call site of its own.
        self._advance_mine_depletion()

    def mothball_mines(self):
        """Stop working what you cannot pay for, worst value first.

        Mothballing is not free to reverse: the shaft floods, the timbering
        rots and the crew disperses, so bringing capacity back means paying to
        sink it again through open_mine. That is the honest cost of having
        overbuilt. Cuts every working of the worst-value material by half
        rather than removing whole workings outright, so the ones that
        survive keep their own real commissioning year and depletion clock
        instead of the newest or oldest being arbitrarily preferred."""
        order = sorted(self.mine_capacity, key=lambda m: -self._mine_opex(m))
        for m in order:
            if self.capital >= 0:
                break
            kept = []
            for w in self._workings_of(m):
                cut = w["capacity"] * 0.5
                self.capital += cut * self._mine_opex(m) * self.price_index
                w["capacity"] -= cut
                if w["capacity"] >= 1.0:
                    kept.append(w)
            self.mines = [w for w in self.mines
                         if w.get("material") != m] + kept
            self.log.append((self.year, "MOTHBALLED half the %s workings; you could "
                                        "not pay to keep them running" % m))
        # This used to clamp capital to minus one year's revenue every time any
        # mine was held, which forgave debt the mothballing had not actually
        # paid off. A playtester proved it to the cent: capital landed on
        # exactly -revenue() on two separate steps with different amounts
        # mothballed in between, so the floor, not the arithmetic, set the
        # number. Debt is now whatever the arithmetic says it is.

    def mine_operating_cost(self):
        """Charged every year the workings stand, whether or not you use them.

        Each WORKING's own mining_cost_scale_for(): a shaft you have worked
        hard for a long time, with no pumping or drilling to show for it,
        costs more than book to keep running, exactly as sinking more of it
        now does in open_mine() - and, since this sums per working rather
        than per material average, two workings of the same material at
        different ages now cost what they actually, individually cost.
        Iterates self.mines, a list in commission order rather than a set
        or dict, so this stays deterministic across hash seeds with no
        sorted() needed."""
        return sum(self.mine_operating_cost_for(w) for w in getattr(self, "mines", ()))

    # ~1 iugerum of woodland per 0.25 ha. Named so that `quote forest` and the
    # purchase itself cannot drift apart: a break tester spent 68% of their
    # capital on coppice with no way to ask the price first.
    FOREST_COST_PER_HA = 250.0
    # Land bounds woodland too, not only mines. geography.json carries no
    # per-region forest figure to read the way minerals has one, so this is
    # built from the signal that IS there: how much territory you actually
    # hold (home_regions, a land-area proxy in the absence of a real
    # hectare-of-forest number) and how good your state is at organising
    # land tenure at all (state_capacity) -- a coppice is not a metalla, so
    # no imperial concession gates it, but fencing off and managing a
    # woodland at scale still takes an administration capable of holding
    # the tenure. [C], sized against the one real anchor available:
    # resources.json's empire-wide 500,000 t/yr of charcoal implies roughly
    # 667,000 ha under management across the WHOLE Roman world (at
    # CHARCOAL_PER_HA=0.75 t/ha/yr); Rome's own ceiling below tops out
    # around 190,000 ha even at full revenue-driven scale-up, comfortably
    # under that -- no private holding should rival the entire empire's own
    # managed woodland.
    FOREST_HA_PER_REGION_BASE   = 1500.0
    FOREST_HA_PER_REGION_PER_SC = 3500.0

    def forest_land_ceiling(self):
        """The largest standing coppice you could ever hold, in hectares."""
        n_regions = max(1, len(self.civ.get("home_regions") or ()))
        sc = float(self.civ.get("state_capacity", 0.5))
        base = ((self.FOREST_HA_PER_REGION_BASE
                 + self.FOREST_HA_PER_REGION_PER_SC * sc) * n_regions)
        return base * (1.0 + min(5.0, max(0.0, self.revenue()) / 60000.0))

    def buy_forest(self, ha):
        """Coppice woodland, bought outright. The cheapest thing in the tree that
        nobody thinks to buy, and the one that decides whether a furnace runs."""
        room = max(0.0, self.forest_land_ceiling() - self.forest_ha)
        if ha > room:
            # SILENT TRUNCATION, not a refusal: open_mine's own ceiling does
            # the same (the tranche you get is the room there is, not zero),
            # and a log line, which the player DOES see, is the honest way
            # to say why the hectares bought were fewer than asked.
            self.log.append((self.year,
                             "you can hold at most %.0f hectares of coppice here; "
                             "bought %.0f, not %.0f" % (self.forest_land_ceiling(),
                                                        room, ha)))
            ha = room
        if ha <= 0:
            return 0.0
        cost = ha * self.FOREST_COST_PER_HA * self.price_index
        if cost > self.capital:
            return 0.0
        self.capital -= cost
        self.forest_ha += ha
        return ha

    # Two denarii the square metre, which is the figure step() has always used
    # (spend / 2.0) written down where a quote can read it. A nitre bed is a
    # heap of dung, straw and ash turned for two years; it is cheap to lay and
    # slow to yield, which is exactly why nobody builds one until they are
    # already short.
    NITRE_COST_PER_M2 = 2.0
    NITRE_YIELD_T_PER_M2 = 0.0008

    def build_nitre(self, m2):
        """Lay down nitre beds. Saltpetre is not dug and not grown; it is made.

        There was no way for a player to do this at all. The only thing that
        laid a bed was step(), which took five per cent of your capital every
        year you were short, said nothing, and did it whether or not you had
        turned the automatic policies off. A shortage the game will not let you
        act on is not a constraint, it is a wall.
        """
        m2 = float(m2)
        if m2 <= 0:
            return 0.0
        cost = m2 * self.NITRE_COST_PER_M2 * self.price_index
        if cost > self.capital:
            return 0.0
        self.capital -= cost
        self.nitre_bed_m2 += m2
        return m2

    def shortage_remedy(self, binding):
        """One sentence on what would end this shortage, in things you can type.

        The throttle message used to name the material and the percentage and
        stop, which tells a player they are stuck without telling them it is
        fixable. Every binding constraint in the model has exactly one answer;
        this is that answer, said out loud.
        """
        if not binding:
            return ""
        if binding == "charcoal":
            need = max(0.0, self.annual_material_demand().get("charcoal_kg", 0.0)
                       / 1000.0 - self.forest_ha * self.CHARCOAL_PER_HA)
            ha = max(1.0, round(need / max(self.CHARCOAL_PER_HA, 1e-9)))
            return ("Charcoal is grown, not bought: about %s more hectare%s of "
                    "coppice would cover it ('buy forest %d', roughly %s "
                    "denarii). Ask the price first with 'quote forest %d'."
                    % ("{:,.0f}".format(ha), "" if ha == 1 else "s", ha,
                       "{:,.0f}".format(ha * self.FOREST_COST_PER_HA * self.price_index),
                       ha))
        if binding == "saltpetre":
            demand = self.annual_material_demand().get("saltpetre_kg", 0.0) / 1000.0
            available = (self.nitre_bed_m2 * self.NITRE_YIELD_T_PER_M2
                         + self._material_market_tonnes("saltpetre")
                         + self._material_stock().get("saltpetre", 0.0))
            deficit = max(0.0, demand - available)
            # Twenty per cent headroom prevents a tiny change in the portfolio
            # putting the player straight back into shortage, without turning a
            # one-tonne deficit into the old fixed sixteen-tonne recommendation.
            m2 = max(100, int(math.ceil(
                deficit * 1.20 / max(self.NITRE_YIELD_T_PER_M2, 1e-12) / 100.0)) * 100)
            return ("Saltpetre is made in nitre beds, not mined: you are about "
                    "%.2f tonnes/year short. With a 20%% safety buffer, 'buy "
                    "nitre %d' lays enough bed at %.4f tonnes per square metre "
                    "per year (about %s denarii)."
                    % (deficit, m2, self.NITRE_YIELD_T_PER_M2,
                       "{:,.0f}".format(m2 * self.NITRE_COST_PER_M2
                                       * self.price_index)))
        if binding in self.MINE_CAPEX_PER_T_YR:
            dem = self.annual_material_demand()
            # SAME GROUPING resource_throttle() uses (_demand_by_supply_tag):
            # copper's shortfall can now come from copper_wire_kg or
            # wire_drawn_kg as much as from copper_kg itself (36 electrical
            # nodes draw drawn wire), and this sentence would otherwise name
            # a "you are X tonnes short" figure that silently excluded them.
            keys = {"coal": ("coal_kg",), "iron": ("iron_bar_kg", "iron_ore_kg"),
                    "copper": ("copper_kg", "copper_wire_kg", "wire_drawn_kg"),
                    "lead": ("lead_kg",), "tin": ("tin_kg",),
                    "silver": ("silver_kg",),
                    "gold": ("gold_kg",)}.get(binding, ())
            short = max(0.0, sum(dem.get(kk, 0.0) for kk in keys)
                        - self.mine_capacity.get(binding, 0.0))
            t = max(1.0, round(short))
            return ("The market will not sell you enough %s, so you have to dig "
                    "it: %s. 'quote mine %s %d' for the price, then 'buy mine "
                    "%s %d'. A shaft takes a few years to come into production."
                    % (binding,
                       ("you are about %s tonnes a year short"
                        % "{:,.0f}".format(short)) if short >= 1.0
                       else "your own workings already cover the demand you have "
                            "today, so this is the market, not you",
                       binding, t, binding, t))
        return ("Nothing you own supplies %s and the market is out of it; the "
                "work waits until something upstream of it is built."
                % binding)

    def living_cost(self, _rev=None, _upkeep=None):
        """You have to eat, sleep somewhere, pay tax, and look the part.

        The last one is not a joke. In a patronage society a man who is visibly
        richer than he dresses is suspected, and a man seeking status must spend
        on it: clothes, a household, hospitality, and public benefaction. That
        expense RISES with your wealth and with your standing, which is why so
        many Roman fortunes went sideways into games and buildings.

        `_rev`/`_upkeep`: an already-computed revenue()/upkeep() a caller who
        just paid for one of its own may pass in, to skip this function's
        own copy of that same call - see credit_limit() and
        funding_capacity() below, both of which call this and ALSO need
        revenue()/upkeep() themselves for arithmetic of their own, and both
        of which read self via nothing but plain attribute and dict access
        the whole way down (no assignment anywhere in that call graph), so
        the number cannot have moved between the caller's own call and this
        one. Optional and keyword-only in every caller but those two: every
        other call site in the engine (there are dozens, across
        core.py/projects.py/labour.py/society.py/protocol.py, none of which
        this file may edit) says plain `self.living_cost()`, gets both
        arguments' None default, and computes exactly what it always did.
        """
        # AT THIS SOCIETY'S PRICES. Every figure here was a Rome 100 AD denarius
        # and none of them was ever multiplied by price_index, so a break tester
        # measured "living and appearances 230.0" to the decimal in all five
        # civilisations, against a selection screen advertising "prices 0.75x to
        # 1.40x Rome". Project costs DID scale, and so did wages, the workshop's
        # output and state funding - which meant an expensive society paid 1.4x
        # for everything it built and ate at Roman prices, and a cheap one got
        # the discount twice. Bread costs what bread costs where you are.
        px = self.price_index
        # CALLED ONCE, NOT THREE TIMES. revenue() and wage_bill() are each
        # pure functions of state that does not move within this call (no
        # project completes, no venture opens, nothing is hired between
        # here and the return), so the two more calls this used to make -
        # one more of each, below - recomputed the same figures for no
        # reason. Profiling a 300-year single-seed run found revenue()
        # alone costing 2.4s of its own time and 21.9s cumulative over
        # 28,423 calls; living_cost() was responsible for two of every
        # three of those calls. See PERFORMANCE.md.
        rev = self.revenue() if _rev is None else _rev
        wages = self.wage_bill()
        base = 120.0 * px                             # bare subsistence, one person
        household = 90.0 * px * (1 + self.freedmen * 0.5 + self.slaves * 0.35)
        tax = max(0.0, rev) * 0.06                     # portoria, vicesima, local dues
        status = 0.0
        if self.has("citizenship"):        status += 200 * px
        if self.running("patron_senatorial"):  status += 900 * px
        if self.running("patron_imperial"):    status += 2500 * px
        status += max(0.0, self.capital) * 0.015      # you cannot look poor and rich
        # A RUINED MAN STOPS KEEPING UP APPEARANCES. This was unconditional and
        # there was no way to shed it: a Rome run sat at 1,343 of revenue
        # against 1,391 of living costs, of which 1,100 was the standing upkeep
        # of a citizenship and a senatorial patron it could no longer afford,
        # and bled 741 a year for sixty-four years with no lever anywhere. That
        # is not what happens. You stop giving games, you dismiss the
        # household, you are seen at fewer dinners - and everyone notices,
        # which is what the reputation floor is already for.
        #
        # You spend on appearances out of what is left after eating; never more
        # than the nominal figure, and never so much that the appearances
        # themselves starve you.
        up = self.upkeep() if _upkeep is None else _upkeep
        room = max(0.0, rev - base - household - tax - up - wages)
        status = min(status, room * 0.75 + max(0.0, self.capital) * 0.015)
        return base + household + tax + status + wages

    HOURS_PER_PERSON_YEAR = 2000.0   # prices.json: a 10-hour day, 250 days, less feasts
