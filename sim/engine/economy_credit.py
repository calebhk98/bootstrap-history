"""Debt, insolvency and what a household can actually afford.

Split out of economy.py (see that file's own docstring for why): every
method here answers "how far into arrears will anyone let you go, what
does that cost you every year, and what happens when you go past it" -
credit_limit(), committed_spend() and funding_capacity() (the
affordability question), debt_interest_rate()/charge_interest() (what
arrears cost), warn_near_the_limit()/enforce_credit_limit()/
shed_loss_makers() (what happens as you approach and then cross the
limit), stall_diagnosis() and spending_power() (diagnosing and quoting
against that same limit), and living_cost() (the personal running cost
- subsistence, household, tax, status - that credit_limit(),
funding_capacity() and stall_diagnosis() all measure a household
against).

CreditMixin is composed into EconomyMixin (economy.py) alongside the
other economy sub-mixins; see that file for the composition and for the
grouping evidence.
"""
from .data import ANNUAL_WAGE, WAGES
from sim.constants import declare


class CreditMixin:

    CREDIT_LINE_EARNING_MULTIPLE = declare(
        "CREDIT_LINE_EARNING_MULTIPLE", 0.5, kind="temporary_heuristic",
        unit="denarii of credit per denarii of standing yearly earning",
        source=None, confidence="D",
        why="How many years of standing income a lender extends to a "
            "complete stranger with nothing else vouching for them. No "
            "attested Roman credit-scoring source; a real figure needs a "
            "model of what a moneylender could actually observe and enforce "
            "against a given borrower's income, which this engine does not "
            "have.")
    CREDIT_LINE_IDENTITY_COVER = declare(
        "CREDIT_LINE_IDENTITY_COVER", 400.0, kind="temporary_heuristic",
        unit="denarii", source=None, confidence="D",
        why="Extra credit a respectable cover identity is worth. Tuned so "
            "the opening decision (reach a cover identity or not) is a real "
            "one; not sourced to any attested figure.")
    CREDIT_LINE_PATRON_LOCAL = declare(
        "CREDIT_LINE_PATRON_LOCAL", 3000.0, kind="temporary_heuristic",
        unit="denarii", source=None, confidence="D",
        why="Extra credit a local patron's name is worth. Game-balance "
            "figure, not a sourced credit line.")
    CREDIT_LINE_PATRON_SENATORIAL = declare(
        "CREDIT_LINE_PATRON_SENATORIAL", 15000.0, kind="temporary_heuristic",
        unit="denarii", source=None, confidence="D",
        why="Extra credit a senatorial patron's name is worth. Scaled up "
            "from the local-patron figure by feel, not by any attested "
            "ratio of patron wealth or standing.")
    CREDIT_LINE_PATRON_IMPERIAL = declare(
        "CREDIT_LINE_PATRON_IMPERIAL", 60000.0, kind="temporary_heuristic",
        unit="denarii", source=None, confidence="D",
        why="Extra credit an imperial patron's name is worth. As with the "
            "other patron tiers, a tuned step up rather than a sourced "
            "figure - see the CREDIT_LINE_SERVICEABLE bound below for the "
            "mechanism that stops this alone turning into an unpayable "
            "trap.")
    CREDIT_LINE_PER_COLLEGIUM_UNIT = declare(
        "CREDIT_LINE_PER_COLLEGIUM_UNIT", 4000.0, kind="temporary_heuristic",
        unit="denarii per licensed collegium unit", source=None,
        confidence="D",
        why="Credit value of one licensed collegium, linear rather than "
            "sqrt because this is collateral (a real, seizable asset) "
            "rather than fame - see the comment this replaces for that "
            "reasoning. The rate itself is tuned, not appraised.")
    CREDIT_LINE_ENDOWMENT_LAND = declare(
        "CREDIT_LINE_ENDOWMENT_LAND", 30000.0, kind="temporary_heuristic",
        unit="denarii", source=None, confidence="D",
        why="Credit value of an endowment of land, treated as real "
            "collateral. No land valuation model backs this figure; it is "
            "a flat, tuned amount.")
    CREDIT_LINE_PER_REPUTATION_POINT = declare(
        "CREDIT_LINE_PER_REPUTATION_POINT", 250.0, kind="temporary_heuristic",
        unit="denarii of credit per reputation point", source=None,
        confidence="D",
        why="How much a point of reputation (itself a heuristic score, see "
            "STANDING_* above) is worth in raw borrowing power. Doubly "
            "removed from any measurement: reputation is invented and this "
            "conversion rate is invented on top of it.")
    CREDIT_LINE_PER_FOREST_HA = declare(
        "CREDIT_LINE_PER_FOREST_HA", 120.0, kind="temporary_heuristic",
        unit="denarii of credit per hectare of owned forest", source=None,
        confidence="D",
        why="Forest is real collateral, so it counts toward credit the way "
            "FOREST_COST_PER_HA says it cost to buy; the per-hectare figure "
            "here is not tied back to that purchase price by any explicit "
            "loan-to-value ratio, just a plausible-feeling fraction of it.")
    CREDIT_LINE_FLOOR_UPKEEP_BUFFER_SHARE = declare(
        "CREDIT_LINE_FLOOR_UPKEEP_BUFFER_SHARE", 0.5, kind="temporary_heuristic",
        unit="fraction of upkeep added to the running-tab floor",
        source=None, confidence="D",
        why="Extra headroom above bare living costs that ordinary "
            "tradesmen and landlords will still carry you for, on top of "
            "living_cost() itself - large enough that the floor does not "
            "sit exactly on the edge of insolvency, tuned rather than "
            "derived from any attested trade-credit practice.")
    CREDIT_SURPLUS_YEARS_MULTIPLE = declare(
        "CREDIT_SURPLUS_YEARS_MULTIPLE", 5.0,
        kind="temporary_heuristic", unit="years of income/surplus",
        source=None, confidence="D",
        why="How many years of turnover (here) or of net surplus "
            "(funding_capacity(), below) a lender is willing to advance "
            "against - the bound that stops a large patron-name credit line "
            "turning into unpayable debt for a household with modest "
            "income. Chosen, per the comment this replaces, to leave the "
            "game's own opening decision unaffected, not fitted to any "
            "lending data.")

    def credit_limit(self, _rev=None, _upkeep=None):
        """How far into arrears anyone will actually let you go.

        Unbounded debt is an accounting fiction: a household could sit
        deeply negative for centuries, making no progress, with the clock
        running. That is not a hard game, it is a game that has stopped
        and not said so.

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
        # What a STRANGER can borrow is almost nothing: you have walked into
        # a town with no name, no land and no one to vouch for you. A flat
        # floor handing a newcomer years of living expenses on nothing but
        # arrival would be wrong. Credit here is what someone will advance
        # against your income and the people who will stand behind you.
        # WHAT YOU NORMALLY EARN, not what this particular year came to: a
        # lender looks at your practice and your concerns; he does not cut
        # your line because you spent this year working for somebody else.
        # Using this year's actual revenue instead would let `work scholar
        # 2000` - which sells the founder's whole year and so takes the
        # practice's income to nothing for it - collapse the credit line
        # mid-step, breaching spending already committed against the old
        # line.
        earning = self.revenue_capacity()
        base = earning * self.CREDIT_LINE_EARNING_MULTIPLE
        if self.running("identity_cover"):     base += self.CREDIT_LINE_IDENTITY_COVER
        if self.running("patron_local"):       base += self.CREDIT_LINE_PATRON_LOCAL
        if self.running("patron_senatorial"):  base += self.CREDIT_LINE_PATRON_SENATORIAL
        if self.running("patron_imperial"):    base += self.CREDIT_LINE_PATRON_IMPERIAL
        # LINEAR, NOT SQRT: a licensed collegium's credit is collateral, not
        # fame, and three of them really do stand behind three times the
        # borrowing the first one did.
        if self.running("collegium_licensed"):
            base += self.CREDIT_LINE_PER_COLLEGIUM_UNIT * self.institution_units("collegium_licensed")
        if self.running("endowment_land"):     base += self.CREDIT_LINE_ENDOWMENT_LAND      # real collateral
        base += max(0.0, self.state.household.reputation) * self.CREDIT_LINE_PER_REPUTATION_POINT
        base += self.state.economy.forest_ha * self.CREDIT_LINE_PER_FOREST_HA                   # also collateral
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
        upkeep_amount = self.upkeep() if _upkeep is None else _upkeep
        floor = self.living_cost(_rev=_rev, _upkeep=upkeep_amount) + upkeep_amount * self.CREDIT_LINE_FLOOR_UPKEEP_BUFFER_SHARE
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
        serviceable = floor + max(0.0, earning) * self.CREDIT_SURPLUS_YEARS_MULTIPLE
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
        return sum(state.get("cost_left") or 0.0 for state in self.state.projects.active.values())

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

        This formula does the same job for the un-manual director's own
        start heuristic (see step(), core.py), where a naive "three times
        capital plus six years of gross revenue" heuristic would let the
        optimizer commit to more than a household could ever fund.
        Factored out here so the player-facing aggregate warning (protocol.py's `start` handler)
        uses the identical number rather than a second formula that could
        quietly drift from it - one rule in two places is how a game like
        this accumulates its worst bugs.

        revenue()/upkeep() computed ONCE, here, and handed to both
        living_cost() and credit_limit() (which itself forwards them to its
        own living_cost() call) as `_rev`/`_upkeep`, rather than recomputed
        by separate calls for the same two numbers - see living_cost's own
        docstring for why reusing them is safe: nothing in this whole call
        graph assigns to self anywhere.
        """
        rev = self.revenue()
        upkeep_amount = self.upkeep()
        household = self.state.household
        fixed = (upkeep_amount + self.living_cost(_rev=rev, _upkeep=upkeep_amount)
                 + self.mine_operating_cost()
                 + max(0.0, -household.capital) * self.debt_interest_rate())
        return (max(0.0, household.capital)
                + self.credit_limit(_rev=rev, _upkeep=upkeep_amount) * self.SPENDING_DRAW_SHARE_ORDINARY
                + max(0.0, rev - fixed) * self.CREDIT_SURPLUS_YEARS_MULTIPLE)

    def shed_loss_makers(self, year):
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
        household = self.state.household
        projects = self.state.projects
        if household.capital >= 0:
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
                for node_id in sorted(projects.operating):
                    node = self.nodes[node_id]
                    if (node["up"] <= node["rev"] or node_id in projects.granted
                            or self.never_abandon(node_id)):
                        continue
                    if (node_id in self.CAPABILITY_INSTITUTIONS) != bool(_pass):
                        continue
                    if worst is None or (node["rev"] - node["up"]) < (self.nodes[worst]["rev"]
                                                               - self.nodes[worst]["up"]):
                        worst = node_id
                if worst is not None:
                    break
            if worst is None:
                break
            # CLOSE IT, do not unlearn it: shedding a loss-maker in ruin is
            # shutting the doors, and what that saves is its running cost.
            # The knowledge stays in `done` - you cannot forget how a thing
            # works because you could not pay for it this year.
            projects.operating.discard(worst)
            # MOTHBALLED, not merely discarded: this is the plant falling into
            # disrepair, exactly like a deliberate `mothball`, and it must show
            # up the same way - in `state.mothballed`, and NOT back in
            # `available` looking like research you have never done, nor
            # indistinguishable from something you had never built, with
            # `restore` (a fraction of the cost) never offered for it.
            projects.mothballed.add(worst)
            shed.append(worst)
        if shed:
            # NAME THEM: "stopped maintaining 1 works" tells a player
            # nothing - not which one, not how to get it back.
            household.log.append((year, "in arrears, so closed %d concern%s that cost more "
                                 "than they returned: %s. You still know how; "
                                 "'restore' reopens one when you can pay for it"
                             % (len(shed), "" if len(shed) == 1 else "s",
                                ", ".join(shed))))

    DEBT_BASE_RATE = declare(
        "DEBT_BASE_RATE", 0.12, kind="hardcoded_outcome",
        unit="fraction of arrears charged per year", source=
        "The Roman legal maximum on ordinary loans (centesimae usurae, "
        "literally 'hundredths', i.e. 1%/month) was twelve per cent a year; "
        "widely attested as the respectable-lending ceiling of the period "
        "this scenario starts in.",
        confidence="B",
        why="What an ordinary, unsecured borrower with no patron pays on "
            "arrears - a real attested legal ceiling for Rome specifically, "
            "not a guess, but used here as a flat PRICE OF MONEY asserted "
            "from the historical record rather than a rate this model "
            "derives from capital scarcity, expected default and lending "
            "risk the way CLAUDE.md SS3.1 asks a price to be derived. It is "
            "also the one figure every OTHER civilisation in this game "
            "reuses as its own starting rate (nothing here varies it by "
            "civ), which a real mechanism would have to. Reclassified from "
            "temporary_heuristic to hardcoded_outcome (see "
            "Complaints/36 and Complaints/37): this is not scaffolding "
            "waiting on a mechanism that has simply not been written yet, "
            "it is a historical number standing in for a market this "
            "project has not yet built - see ENDOGENOUS_COSTS_AND_DOMAINS.md's "
            "wage/price solver for the kind of mechanism a real interest "
            "rate would fall out of.")
    DEBT_RATE_DISCOUNT_PATRON_LOCAL = declare(
        "DEBT_RATE_DISCOUNT_PATRON_LOCAL", 0.015, kind="temporary_heuristic",
        unit="fraction off the base annual rate", source=None,
        confidence="D",
        why="How much cheaper a local patron's name makes borrowing. No "
            "source ties a specific rate discount to a specific patronage "
            "tier; a real figure needs a model of how a lender actually "
            "prices counterparty risk in a patronage economy.")
    DEBT_RATE_DISCOUNT_PATRON_SENATORIAL = declare(
        "DEBT_RATE_DISCOUNT_PATRON_SENATORIAL", 0.03, kind="temporary_heuristic",
        unit="fraction off the base annual rate", source=None,
        confidence="D",
        why="As DEBT_RATE_DISCOUNT_PATRON_LOCAL, larger tier - tuned to "
            "feel proportionate, not derived from lending data.")
    DEBT_RATE_DISCOUNT_PATRON_IMPERIAL = declare(
        "DEBT_RATE_DISCOUNT_PATRON_IMPERIAL", 0.03, kind="temporary_heuristic",
        unit="fraction off the base annual rate", source=None,
        confidence="D",
        why="As DEBT_RATE_DISCOUNT_PATRON_SENATORIAL - the imperial and "
            "senatorial tiers happen to carry the same discount here, which "
            "is itself an unexamined choice rather than a considered one.")
    DEBT_RATE_DISCOUNT_ENDOWMENT_LAND = declare(
        "DEBT_RATE_DISCOUNT_ENDOWMENT_LAND", 0.02, kind="temporary_heuristic",
        unit="fraction off the base annual rate", source=None,
        confidence="D",
        why="Secured lending against land collateral is cheaper than "
            "personal credit in general, which is a real effect; the "
            "specific two-point discount is tuned, not taken from an "
            "attested Roman secured-loan rate.")
    DEBT_RATE_DISCOUNT_BANKER = declare(
        "DEBT_RATE_DISCOUNT_BANKER", 0.01, kind="temporary_heuristic",
        unit="fraction off the base annual rate", source=None,
        confidence="D",
        why="A banker you know (fin_argentarii) shaves a little off the "
            "rate through a personal relationship - plausible in kind, "
            "invented in size.")
    DEBT_RATE_REPUTATION_DISCOUNT_CAP = declare(
        "DEBT_RATE_REPUTATION_DISCOUNT_CAP", 0.03, kind="temporary_heuristic",
        unit="fraction off the base annual rate (maximum)", source=None,
        confidence="D",
        why="Ceiling on how much sheer personal reputation, independent of "
            "any named patron, can cheapen credit. Tuned so reputation "
            "alone cannot out-discount every patronage tier combined.")
    DEBT_RATE_REPUTATION_SCALE = declare(
        "DEBT_RATE_REPUTATION_SCALE", 3000.0, kind="temporary_heuristic",
        unit="reputation points per percentage point of discount",
        source=None, confidence="D",
        why="How fast reputation converts into a cheaper interest rate, "
            "against DEBT_RATE_REPUTATION_DISCOUNT_CAP above. Reputation's "
            "own scale is itself invented (see STANDING_* above), so this "
            "is a heuristic layered on a heuristic.")

    def debt_interest_rate(self):
        """What arrears cost you a year.

        Roman lending was expensive and the legal ceiling of twelve per cent was
        a ceiling on the RESPECTABLE end of it; maritime loans ran far higher
        because the risk was real. A man with no standing borrows from whoever
        will have him and pays for it. Standing is what makes money cheap, which
        is the same rule as everything else in this model: patronage is the
        currency underneath the currency.
        """
        rate = self.DEBT_BASE_RATE
        if self.running("patron_local"):        rate -= self.DEBT_RATE_DISCOUNT_PATRON_LOCAL
        if self.running("patron_senatorial"):   rate -= self.DEBT_RATE_DISCOUNT_PATRON_SENATORIAL
        if self.running("patron_imperial"):     rate -= self.DEBT_RATE_DISCOUNT_PATRON_IMPERIAL
        if self.running("endowment_land"):      rate -= self.DEBT_RATE_DISCOUNT_ENDOWMENT_LAND          # secured, not personal
        if self.running("fin_argentarii"):      rate -= self.DEBT_RATE_DISCOUNT_BANKER          # a banker you know
        rate -= min(self.DEBT_RATE_REPUTATION_DISCOUNT_CAP,
                    max(0.0, self.state.household.reputation) / self.DEBT_RATE_REPUTATION_SCALE)
        return max(0.0, rate)

    def charge_interest(self, year):
        """Arrears accrue. They did not before, which made debt free money."""
        household = self.state.household
        if household.capital >= 0:
            return 0.0
        rate = self.debt_interest_rate()
        owed = -household.capital * rate
        household.capital -= owed
        household.interest_paid = (household.interest_paid or 0.0) + owed
        if owed > 0 and (getattr(household, "insolvent_years", 0) in (1, 5, 15)):
            household.log.append((year, "interest on %0.f denarii of arrears at %.1f%% a year"
                                 % (-household.capital, rate * 100)))
        return owed

    def warn_near_the_limit(self, year):
        """Say it BEFORE the creditors do, while there is still a decision left.

        A limit you can only discover by crossing it is not a limit, it is
        an ambush: everything that could still save a household (stop a
        project, close a loss-maker, let somebody go) has to be available
        while there is still time to act on it, not only after the
        recoverable-looking dip has already become "CREDIT EXHAUSTED: N
        projects halted".
        """
        limit = self.credit_limit()
        household = self.state.household
        if limit <= 0 or household.capital >= 0:
            household._said_near_limit = False
            return
        used = -household.capital / limit
        # PAST IT IS NOT "CLOSE TO" IT, and past it the halting has already
        # happened: enforce_credit_limit runs immediately after this and
        # deals with it, so this must not still say "CLOSE TO THE LIMIT
        # ... every project in hand is halted" in a year when nothing here
        # actually halts anything. Warn about what is still ahead of you,
        # not about what has just been done.
        if used >= 1.0:
            household._said_near_limit = True
            return
        if used < 0.7:
            household._said_near_limit = False
            return
        if getattr(household, "_said_near_limit", False):
            return
        household._said_near_limit = True
        household.log.append((year, "CLOSE TO THE LIMIT: you owe %s of the %s anyone "
                             "here will advance you (%d%%). Past it every "
                             "project in hand is halted unfinished and nobody "
                             "funds new work for some years. 'stop' a project, "
                             "'mothball' a loss-maker or 'fire' somebody while "
                             "it is still your choice"
                         % ("{:,.0f}".format(-household.capital),
                            "{:,.0f}".format(limit), used * 100)))

    CREDIT_FREEZE_YEARS_AFTER_HALT = declare(
        "CREDIT_FREEZE_YEARS_AFTER_HALT", 5, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="How long nobody will fund new work after projects are halted "
            "for exhausted credit. A real figure needs a model of how "
            "quickly a specific lending community forgives a specific "
            "default; this is a tuned, round number chosen to feel like a "
            "real but recoverable setback.")
    CREDITOR_SEIZURE_VALUE_MULTIPLE = declare(
        "CREDITOR_SEIZURE_VALUE_MULTIPLE", 2.0, kind="temporary_heuristic",
        unit="years of upkeep recovered per concern seized", source=None,
        confidence="D",
        why="What creditors recover, in cash, for seizing and selling a "
            "concern that costs more than it earns - valued at twice its "
            "annual upkeep rather than any appraised resale value, because "
            "this model has no market for used capital goods. A real "
            "figure needs one.")
    HOUSEHOLD_DISPERSAL_ARTISANS_RETENTION = declare(
        "HOUSEHOLD_DISPERSAL_ARTISANS_RETENTION", 0.4, kind="temporary_heuristic",
        unit="fraction of artisans kept after the household disperses",
        source=None, confidence="D",
        why="How many trained artisans stay with a ruined household after "
            "the rest are freed or sold - some core of skilled people is "
            "plausible, but the specific 40% retained is tuned game "
            "balance, not derived from any account of how a Roman household "
            "actually broke up under debt.")
    HOUSEHOLD_DISPERSAL_ARTISANS_FLOOR = declare(
        "HOUSEHOLD_DISPERSAL_ARTISANS_FLOOR", 3.0, kind="temporary_heuristic",
        unit="artisans", source=None, confidence="D",
        why="The minimum artisan headcount a dispersed household keeps, so "
            "a small household does not round to zero and become unable to "
            "ever recover. Chosen so recovery stays possible, not measured.")
    DEBT_BONDAGE_DEFAULT_TERM_YEARS = declare(
        "DEBT_BONDAGE_DEFAULT_TERM_YEARS", 10.0, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="Fallback term of debt bondage/service for a civilisation whose "
            "own data does not specify one (civ.get('bondage_years', ...)). "
            "Historical debt-service terms across the systems this method's "
            "own docstring names (Han, Norse, Mexica) varied by circumstance "
            "rather than clustering on a single figure, so this is a round "
            "placeholder, not a citation.")
    SETTLEMENT_MIN_INTERVAL_YEARS = declare(
        "SETTLEMENT_MIN_INTERVAL_YEARS", 10.0, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="Minimum gap between one insolvency write-off and the next, so "
            "settling is a once-in-a-life humiliation rather than an annual "
            "accounting entry (see the comment this replaces for the bug "
            "this fixed). The specific gap is a game-balance choice.")
    SETTLEMENT_CAPITAL_RETAINED_FRACTION = declare(
        "SETTLEMENT_CAPITAL_RETAINED_FRACTION", 0.35, kind="temporary_heuristic",
        unit="fraction of the credit limit still owed after settlement",
        source=None, confidence="D",
        why="How much debt survives an insolvency write-off, as a fraction "
            "of the credit limit rather than of the actual arrears - so "
            "settlement always leaves you owing something (a real write-off "
            "rarely erases a debt entirely) without the residue growing "
            "without bound. Tuned, not modelled on any attested bankruptcy "
            "practice.")
    SETTLEMENT_REPUTATION_HIT = declare(
        "SETTLEMENT_REPUTATION_HIT", 12.0, kind="temporary_heuristic",
        unit="reputation points", source=None, confidence="D",
        why="How much standing an insolvency write-off costs. Reputation's "
            "own scale is already invented (STANDING_* above); this is a "
            "further tuned penalty on top of it.")
    SETTLEMENT_CREDIT_FREEZE_YEARS = declare(
        "SETTLEMENT_CREDIT_FREEZE_YEARS", 12, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="How long nobody extends fresh credit after a write-off - "
            "longer than CREDIT_FREEZE_YEARS_AFTER_HALT because an actual "
            "default is worse than a temporary halt, but the specific "
            "figure is tuned game feel, not a lending-market estimate.")

    def enforce_credit_limit(self, year):
        """Nobody lends past the limit, so past the limit you simply stop.

        The order matters and is the realistic one: first you stop paying for new
        work, then you let go of what you cannot maintain, and only then, if it is
        still hopeless, your creditors write the rest off and take everything
        that was not nailed down. You are left poor rather than impossibly
        indebted, which is a position you can work out of.
        """
        limit = self.credit_limit()
        household = self.state.household
        projects = self.state.projects
        if household.capital >= -limit:
            return
        # stop everything in progress: you cannot fund it
        if projects.active:
            dropped = sorted(projects.active)
            # WHAT YOU PAID IS NOT BURNED: "Halted" must mean paused, not
            # deleted - a half-built thing is still half built when the
            # money runs out, the site does not un-dig itself. What you
            # paid stands to your credit and comes off the bill when you
            # begin again.
            _paid = getattr(projects, "paid_towards", None)
            if _paid is None:
                _paid = projects.paid_towards = {}
            _kept = 0.0
            for node_id in dropped:
                active_entry = projects.active.pop(node_id, None)
                if active_entry:
                    spent_val = active_entry.get("spent", 0.0) if isinstance(active_entry, dict) else getattr(active_entry, "spent", 0.0)
                    _paid[node_id] = _paid.get(node_id, 0.0) + max(0.0, spent_val)
                    _kept += max(0.0, spent_val)
                projects.bountied.discard(node_id)
            household.credit_frozen_until = year + self.CREDIT_FREEZE_YEARS_AFTER_HALT
            household.log.append((year, "CREDIT EXHAUSTED: %d project%s stopped, "
                                 "unfinished: %s. The %s denarii already paid "
                                 "stands to your credit and comes off the "
                                 "bill if you begin again. Nobody will fund new "
                                 "work here until %d"
                             % (len(dropped), "" if len(dropped) == 1 else "s",
                                ", ".join(dropped[:4])
                                + (" and others" if len(dropped) > 4 else ""),
                                "{:,.0f}".format(_kept), year + self.CREDIT_FREEZE_YEARS_AFTER_HALT)))
        # let go of what you cannot maintain
        if household.capital < -limit:
            self.mothball_mines()
        if household.capital < -limit:
            # From what you are RUNNING: a creditor cannot seize a thing you
            # merely know how to do, and closing something that was not open
            # saves nobody anything.
            burden = sorted((node_id for node_id in projects.operating
                             if self.nodes[node_id]["up"] > self.nodes[node_id]["rev"]
                             and node_id not in projects.granted
                             and not self.never_abandon(node_id)),
                            key=lambda node_id: (self.nodes[node_id]["rev"] - self.nodes[node_id]["up"]))
            taken = []
            for node_id in burden:
                if household.capital >= -limit:
                    break
                # THEY TAKE THE CONCERN, NOT YOUR MEMORY OF HOW IT WORKED:
                # discarding the node from `done` while leaving it in
                # `operating` would make it simultaneously forgotten and
                # running - `state` saying the concern is running,
                # `ventures` billing for it, `money` charging nothing, and
                # `start`/`restore`/`open`/`mothball` refusing it on
                # mutually contradictory grounds, with no way to clear the
                # entry.
                #
                # Closing it is both the fix and the more honest event: what a
                # creditor can carry away is the shop.
                projects.operating.discard(node_id)
                household.capital += self.nodes[node_id]["up"] * self.CREDITOR_SEIZURE_VALUE_MULTIPLE
                # MOTHBALLED, not merely discarded - see the identical comment
                # in shed_loss_makers. Without this a work creditors took stood
                # indistinguishable from research never begun, and `restore`
                # (a fraction of the cost) was never offered for it.
                projects.mothballed.add(node_id)
                taken.append(node_id)
            # Only say it if it happened: firing this every year regardless
            # of whether anything was actually taken would log creditors
            # seizing something for a run that has nothing left to take,
            # over and over.
            # NAME THEM, for the same reason shed_loss_makers does: a
            # player cannot understand what they lost, or why it reappeared
            # mothballed rather than gone, from a bare count.
            if taken:
                household.log.append((year, "creditors took what they could: %d concerns "
                                     "closed and sold up: %s. You keep the "
                                     "knowledge; reopening means paying for the "
                                     "premises again"
                                     % (len(taken), ", ".join(taken))))
        # AND THE HOUSEHOLD GOES: nobody keeps four hundred dependants they
        # cannot feed. Without shedding them, the upkeep of a household a
        # civilisation can no longer feed would consume every denarius of
        # income forever, pinning a run at the credit floor with no way to
        # make progress. People are sold or freed and they leave, and the
        # point of modelling it is that shedding them is how you become
        # solvent again.
        if household.capital < -limit and (household.slaves or household.freedmen):
            freed = household.slaves + household.freedmen
            self.manumit(household.slaves)          # you do not sell them on
            household.freedmen = 0
            household.artisans = max(self.HOUSEHOLD_DISPERSAL_ARTISANS_FLOOR,
                                          household.artisans * self.HOUSEHOLD_DISPERSAL_ARTISANS_RETENTION)
            household.log.append((year, "the household disperses: %d people leave, because "
                                 "you can no longer feed them" % freed))

        # DEBT BONDAGE, where the society had it, modelled as a TERM OF
        # SERVICE that is worked off, because that is what it mostly was:
        # Han debt servitude, the Norse debt-thrall and Mexica tlacotin
        # were all terms of service that ended, were redeemable, and in
        # the Mexica case were not heritable. Rome is the exception, not
        # the rule, because nexum was abolished in 326 BC, so Rome carries
        # debt_bondage false and goes straight to the write-off below.
        #
        # In bondage your hours are not your own. That is the whole penalty, and
        # it is a heavy one in a game whose scarcest resource is your hours; but
        # it ends, and it ends sooner if the work is worth something.
        if (household.capital < -limit and self.civ.get("debt_bondage")
                and not household.bondage_years_left):
            term = float(self.civ.get("bondage_years", self.DEBT_BONDAGE_DEFAULT_TERM_YEARS))
            household.bondage_years_left = term
            household.bondage_debt = -household.capital
            household.capital = 0.0
            household.log.append((year, "BONDAGE: you cannot pay, and you enter service for "
                                 "your debt. For about %d years most of your hours "
                                 "belong to someone else. It is not the end: it is "
                                 "worked off, and then you are free again" % term))
            return

        # and the rest is written off. You keep your standing, your knowledge and
        # your practice, which is exactly what you started with.
        #
        # ONCE A DECADE AT MOST: settling whenever the balance sits a
        # denarius past the line would "settle" a household whose rent
        # slightly exceeds its credit every single year, logging the same
        # dramatic event over and over. A write-off is a once-in-a-life
        # humiliation, not an annual accounting entry, and between them you
        # are simply in arrears, which already has consequences of its own.
        if household.capital < -limit and year - getattr(household, "last_settlement", -999) >= self.SETTLEMENT_MIN_INTERVAL_YEARS:
            household.last_settlement = year
            household.capital = -limit * self.SETTLEMENT_CAPITAL_RETAINED_FRACTION
            # THE NUMBER ANNOUNCED HAS TO BE THE NUMBER APPLIED: quoting a
            # fixed "reputation -12" against a reputation of 4.9 would say
            # the same thing twice while the second application does
            # nothing at all - a penalty that cannot be paid should not be
            # quoted as though it were.
            _rep_hit = min(self.SETTLEMENT_REPUTATION_HIT, max(0.0, household.reputation))
            household.reputation = max(0.0, household.reputation - self.SETTLEMENT_REPUTATION_HIT)
            # AND NOBODY LENDS TO YOU FOR A WHILE. Without this, walking away
            # from a debt cost a little standing and nothing else, and standing
            # grows back. A person who has just been written off does not get
            # a fresh line of credit the following morning.
            _frozen_before = getattr(household, "credit_frozen_until", 0)
            household.credit_frozen_until = max(_frozen_before, year + self.SETTLEMENT_CREDIT_FREEZE_YEARS)
            # SAY WHAT ACTUALLY HAPPENED: "the debt is written off" while
            # leaving the player owing a third of their credit line
            # contradicts the number on the next line. Most of it goes;
            # what is left, and what it cost your name, is the part worth
            # reading.
            #
            # AND SAY IF THE UNLOCK DATE JUST MOVED: a second settlement
            # while the first freeze had not yet lifted pushes it from
            # year+5 or year+12 out to a fresh year+12, and that has to be
            # announced - a deadline that quietly slides is worse than a
            # longer fixed one would have been.
            # A FREEZE HAS TO HAVE BEEN ACTUALLY IN FORCE to "move" - the
            # default _frozen_before of 0 is "never frozen", not a freeze
            # that this settlement then extended, and comparing only the
            # before/after VALUES said a date had moved on every first-ever
            # settlement (0 -> year+12 is a bigger number, by that test, same
            # as a real extension).
            _moved = (_frozen_before > year
                     and household.credit_frozen_until > _frozen_before)
            household.log.append((year, "INSOLVENCY SETTLED: most of the debt is written "
                                 "off and you still owe about %s denarii. Your "
                                 "name is worth less for it (reputation %s), and "
                                 "you keep your knowledge and your practice%s"
                                 % ("{:,.0f}".format(limit * self.SETTLEMENT_CAPITAL_RETAINED_FRACTION),
                                    "-%.1f" % _rep_hit if _rep_hit > 0.05
                                    else "already at nothing, so no further",
                                    (". Settling again while still frozen out "
                                     "pushes the date nobody will fund you "
                                     "again until from %d out to %d - it moves "
                                     "with every settlement, not just the first"
                                     % (_frozen_before, household.credit_frozen_until))
                                    if _moved else "")))

    WAGE_REPUTATION_BONUS_CAP = declare(
        "WAGE_REPUTATION_BONUS_CAP", 0.5, kind="temporary_heuristic",
        unit="multiple on wage income (maximum bonus)", source=None,
        confidence="D",
        why="Ceiling on how much personal reputation can raise what "
            "working for wages pays, in the stall-diagnosis advice shown "
            "to a stuck player. A defensive cap on an already-invented "
            "reputation scale (see STANDING_* above), not derived from any "
            "attested wage-premium-for-reputation relationship.")
    WAGE_REPUTATION_BONUS_SCALE = declare(
        "WAGE_REPUTATION_BONUS_SCALE", 200.0, kind="temporary_heuristic",
        unit="reputation points per 100% of the bonus cap", source=None,
        confidence="D",
        why="How fast reputation converts into a wage-work bonus, against "
            "WAGE_REPUTATION_BONUS_CAP above. Reputation's own scale is "
            "itself invented, so this is a heuristic layered on a "
            "heuristic, the same shape as DEBT_RATE_REPUTATION_SCALE.")

    def stall_diagnosis(self):
        """None if the run is going somewhere; otherwise what is wrong and what
        would actually change it.

        A player who makes one bad purchase early can be locked out of the
        goal for the rest of the game, with the game continuing to accept
        commands and give the impression of an ongoing playthrough for
        centuries, and the only feedback being the same static "in
        arrears" message every time INSOLVENCY SETTLED fires.

        The arithmetic is not wrong and the state is not even a dead end -
        it can be escaped, working for wages among other things - but
        nothing says so. A game that has effectively stopped has to say
        so, and say what would restart it, because the alternative is a
        player spending an hour discovering it by experiment.
        """
        household = self.state.household
        projects = self.state.projects
        insolvent_years = getattr(household, "insolvent_years", 0) or 0
        if household.capital >= 0 or insolvent_years < 8:
            return None
        # THE SAME NET THE LEDGER PRINTS: must include the interest on the
        # arrears, the one cost that exists BECAUSE you are in arrears -
        # leaving it out would quote a loss (e.g. "you lose 46 denarii a
        # year") that disagrees with the ledger's own "Net/yr" figure
        # directly above it.
        interest = max(0.0, -household.capital) * self.debt_interest_rate()
        # revenue_capacity(), NOT plain revenue(): the ledger's own
        # net_per_year reads revenue_capacity() too, so this and that net
        # can only actually be "the same net" if both call the same
        # standing-figure function.
        standing_revenue = self.revenue_capacity()
        standing_upkeep = self.upkeep()
        standing_living = self.living_cost(
            _rev=standing_revenue, _upkeep=standing_upkeep)
        net = (standing_revenue - standing_upkeep - standing_living
               - self.mine_operating_cost() - interest)
        if net >= 0:
            return None
        ways = []
        pool = self.director_pool() - getattr(household, "wage_hours_this_year", 0.0)
        if pool > 100:
            # ONLY IF IT WOULD ACTUALLY GAIN: selling your hours takes them
            # out of your own practice, so with a practice to lose this is
            # often the losing move, and this advice must not recommend a
            # move that `work` itself would then report as a net loss.
            # NAME THE TRADE, and pick the one that actually pays best
            # here: advice that says only "work for wages" without naming
            # which job, and takes the cheapest trade in the table by
            # default, is advice that can be followed into a loss.
            trades = [trade for trade in WAGES if self.trade_available(trade)]
            best_trade = max(trades, key=lambda trade: ANNUAL_WAGE.get(trade, self.DEFAULT_ANNUAL_WAGE_FALLBACK),
                         default=None)
            if best_trade:
                rate = ANNUAL_WAGE[best_trade] / self.HOURS_PER_PERSON_YEAR
                would_earn = (pool * rate * self.price_index * self.wage_index
                              * (1.0 + min(self.WAGE_REPUTATION_BONUS_CAP,
                                           household.reputation / self.WAGE_REPUTATION_BONUS_SCALE)))
                # What those same hours are already earning in the practice.
                practice = sum(self.nodes[node_id]["rev"] for node_id in self._practice_set())
                would_cost = (practice * self.PRACTICE_SHARE
                              * (pool / max(1.0, self.director_pool())))
                if would_earn > would_cost:
                    ways.append("work as a %s: %.0f of your own hours are left "
                                "this year and would bring in about %s against "
                                "the %s of practice they come out of, so you are "
                                "up %s. Nobody has to lend you anything for that"
                                % (best_trade, pool,
                                   "{:,.0f}".format(would_earn),
                                   "{:,.0f}".format(would_cost),
                                   "{:,.0f}".format(would_earn - would_cost)))
        losers = sorted((node_id for node_id in projects.operating
                         if self.nodes[node_id]["up"] > self.nodes[node_id]["rev"]),
                        key=lambda node_id: self.nodes[node_id]["rev"] - self.nodes[node_id]["up"])
        if losers:
            ways.append("close what costs more than it brings in: %s"
                        % ", ".join("%s (%+.0f a year)"
                                    % (node_id, self.nodes[node_id]["rev"] - self.nodes[node_id]["up"])
                                    for node_id in losers[:3]))
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
                                  % (household.insolvent_years,
                                     "{:,.0f}".format(-net))),
                "this_is_not_the_end_of_the_run": ("it is escapable, and none of "
                                                   "these need anybody to lend "
                                                   "you a denarius"),
                "what_would_change_it": ways}

    # THREE ANSWERS TO "CAN I AFFORD THIS" is two too many: `quote`
    # counting cash alone, `available afford` and `hire` counting cash
    # plus half the credit line, and `start` counting cash plus the whole
    # of it collapses to two real distinctions, not three, so the
    # distinction is named here once and used everywhere.
    #
    # A lender advances against WORK - there is something half-built to point
    # at - and will not advance against a payroll or a purchase, where the
    # money is gone the moment it is spent. That is why `start` may draw the
    # whole line and `hire` and `buy` may draw half of it. `quote` counted
    # neither, which was simply wrong: it is the command whose entire job is
    # to tell you what you can pay for.
    SPENDING_DRAW_SHARE_ORDINARY = declare(
        "SPENDING_DRAW_SHARE_ORDINARY", 0.5, kind="temporary_heuristic",
        unit="fraction of the credit line drawable for buy/hire", source=None,
        confidence="D",
        why="A lender advances against unfinished WORK (a `start`) more "
            "readily than against a payroll or a purchase that leaves "
            "nothing half-built to point at - a real distinction, per this "
            "method's own docstring - but the specific half-vs-whole split "
            "is a tuned game-balance choice, not derived from any lending "
            "practice.")

    def spending_power(self, kind="buy"):
        """What you could actually raise, by what you mean to spend it on."""
        share = 1.0 if kind == "start" else self.SPENDING_DRAW_SHARE_ORDINARY
        # THE DEBT YOU ALREADY CARRY COUNTS AGAINST YOU. This read
        # max(0.0, self.household.capital) + credit_limit() * share, which floored the
        # capital term and so ignored arrears entirely: a household 500 into
        # a 210-denarii credit line was told it could still raise 105. It
        # cannot. credit_limit() is "how far into arrears anyone will let you
        # go" - an absolute floor on capital, which is exactly how
        # enforce_credit_limit() reads it (`if self.household.capital >= -limit`), not
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
            # Two traced runs are in the suite for this: a household deep
            # in arrears with several finished concerns worth real money a
            # year, shut, must still be able to open them, and a concern
            # that takes years to clear its own capex must not open just
            # because arrears are otherwise ignored here. See the checks
            # named "a completed concern that pays for its own door within
            # months opens even while deep in arrears" and its slow-payback sibling,
            # which holds the line the other way: a concern that takes YEARS
            # to clear its own capex still does not open on this.
            return max(0.0, self.state.household.capital) + self.credit_limit() * share
        return max(0.0, self.state.household.capital + self.credit_limit() * share)

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
        # AT THIS SOCIETY'S PRICES: project costs scale with price_index,
        # and so do wages, the workshop's output and state funding, so
        # living costs must too - otherwise an expensive society pays more
        # for everything it builds while eating at Roman prices, and a
        # cheap one gets the discount twice. Bread costs what bread costs
        # where you are.
        price_index = self.price_index
        # CALLED ONCE, NOT THREE TIMES: revenue() and wage_bill() are each
        # pure functions of state that does not move within this call (no
        # project completes, no venture opens, nothing is hired between
        # here and the return), so recomputing them a second or third time
        # for the same figures is pure waste. Profiling a 300-year
        # single-seed run found revenue()
        # alone costing 2.4s of its own time and 21.9s cumulative over
        # 28,423 calls; living_cost() was responsible for two of every
        # three of those calls. See PERFORMANCE.md.
        rev = self.revenue() if _rev is None else _rev
        wages = self.wage_bill()
        household_state = self.state.household
        base = self.LIVING_COST_BASE_SUBSISTENCE * price_index         # bare subsistence, one person
        household = (self.LIVING_COST_HOUSEHOLD_BASE * price_index
                     * (1 + household_state.freedmen * self.LIVING_COST_FREEDMAN_SHARE
                        + household_state.slaves * self.LIVING_COST_SLAVE_SHARE))
        tax = max(0.0, rev) * self.LIVING_COST_TAX_RATE                # portoria, vicesima, local dues
        status = 0.0
        if self.has("citizenship"):        status += self.LIVING_COST_STATUS_CITIZENSHIP * price_index
        if self.running("patron_senatorial"):  status += self.LIVING_COST_STATUS_PATRON_SENATORIAL * price_index
        if self.running("patron_imperial"):    status += self.LIVING_COST_STATUS_PATRON_IMPERIAL * price_index
        status += max(0.0, household_state.capital) * self.LIVING_COST_STATUS_PER_CAPITAL      # you cannot look poor and rich
        # A RUINED MAN STOPS KEEPING UP APPEARANCES: status spending must be
        # capped by what is actually left after eating (`room` below), not
        # carried as a fixed, unconditional cost - an uncapped citizenship
        # or patron upkeep a household can no longer afford would bleed it
        # every year with no lever to reduce it. You stop giving games, you
        # dismiss the household, you are seen at fewer dinners - and
        # everyone notices, which is what the reputation floor is already
        # for.
        #
        # You spend on appearances out of what is left after eating; never more
        # than the nominal figure, and never so much that the appearances
        # themselves starve you.
        upkeep_amount = self.upkeep() if _upkeep is None else _upkeep
        room = max(0.0, rev - base - household - tax - upkeep_amount - wages)
        status = min(status, room * self.LIVING_COST_APPEARANCES_SHARE_OF_ROOM
                     + max(0.0, household_state.capital) * self.LIVING_COST_STATUS_PER_CAPITAL)
        return base + household + tax + status + wages

    LIVING_COST_BASE_SUBSISTENCE = declare(
        "LIVING_COST_BASE_SUBSISTENCE", 120.0, kind="temporary_heuristic",
        unit="denarii/year at price_index=1", source=None, confidence="D",
        why="Bare subsistence cost for one person (food, the plainest "
            "shelter, nothing else) at this society's reference prices. No "
            "attested Roman subsistence-basket figure backs this exact "
            "number; a real figure needs the same physical grounding "
            "sim/world/agriculture.py gives food (CALORIES_PER_PERSON_DAY, "
            "a real crop and price), not a flat denarii figure.")
    LIVING_COST_HOUSEHOLD_BASE = declare(
        "LIVING_COST_HOUSEHOLD_BASE", 90.0, kind="temporary_heuristic",
        unit="denarii/year at price_index=1, one dependant-equivalent",
        source=None, confidence="D",
        why="Cost of keeping one household dependant beyond bare personal "
            "subsistence - rent, ordinary household goods, the plain cost "
            "of a household rather than a single person camping. Not "
            "sourced to an attested figure.")
    LIVING_COST_FREEDMAN_SHARE = declare(
        "LIVING_COST_FREEDMAN_SHARE", 0.5, kind="temporary_heuristic",
        unit="dimensionless multiple of LIVING_COST_HOUSEHOLD_BASE per freedman",
        source=None, confidence="D",
        why="How much one freedman adds to household living costs, "
            "relative to the base household-dependant figure. Tuned, not "
            "measured against any attested household-maintenance record.")
    LIVING_COST_SLAVE_SHARE = declare(
        "LIVING_COST_SLAVE_SHARE", 0.35, kind="temporary_heuristic",
        unit="dimensionless multiple of LIVING_COST_HOUSEHOLD_BASE per slave",
        source=None, confidence="D",
        why="As LIVING_COST_FREEDMAN_SHARE, for an enslaved household "
            "member - lower, reflecting a bare rather than a dignified "
            "standard of upkeep. Tuned, not measured.")
    LIVING_COST_TAX_RATE = declare(
        "LIVING_COST_TAX_RATE", 0.06, kind="hardcoded_outcome",
        unit="fraction of revenue", source=
        "Named after real Roman levies - portoria (customs dues, "
        "typically a few per cent), the vicesima (a nominal 5% on certain "
        "transactions) and local dues - but combined into one flat rate "
        "rather than modelling any of them as its own mechanism.",
        confidence="C",
        why="What fraction of revenue goes to tax and local dues each "
            "year. The NAMED taxes are real; this file has no separate "
            "customs, transaction or local-dues mechanism, so their "
            "combined bite is approximated as one flat share of revenue "
            "rather than computed from an actual fiscal structure. "
            "Reclassified from temporary_heuristic to "
            "hardcoded_outcome (see Complaints/36 and "
            "Complaints/37), alongside DEBT_BASE_RATE: this stands "
            "in for state revenue extraction, which CLAUDE.md SS3.1 asks "
            "to fall out of trade volume, customs enforcement and imperial "
            "administrative reach rather than being asserted as one number "
            "reused unchanged by every civilisation this game starts.")
    LIVING_COST_STATUS_CITIZENSHIP = declare(
        "LIVING_COST_STATUS_CITIZENSHIP", 200.0, kind="temporary_heuristic",
        unit="denarii/year at price_index=1", source=None, confidence="D",
        why="Standing upkeep of maintaining the appearance citizenship "
            "expects - clothes, hospitality, being seen. Tuned game "
            "balance, not an attested figure.")
    LIVING_COST_STATUS_PATRON_SENATORIAL = declare(
        "LIVING_COST_STATUS_PATRON_SENATORIAL", 900.0, kind="temporary_heuristic",
        unit="denarii/year at price_index=1", source=None, confidence="D",
        why="As LIVING_COST_STATUS_CITIZENSHIP, for a senatorial patron's "
            "expectations of you. Tuned, not attested.")
    LIVING_COST_STATUS_PATRON_IMPERIAL = declare(
        "LIVING_COST_STATUS_PATRON_IMPERIAL", 2500.0, kind="temporary_heuristic",
        unit="denarii/year at price_index=1", source=None, confidence="D",
        why="As LIVING_COST_STATUS_PATRON_SENATORIAL, for the imperial "
            "tier. Tuned, not attested.")
    LIVING_COST_STATUS_PER_CAPITAL = declare(
        "LIVING_COST_STATUS_PER_CAPITAL", 0.015, kind="temporary_heuristic",
        unit="fraction of capital spent on appearances per year",
        source=None, confidence="D",
        why="'You cannot look poor and rich': how much of a wealthy "
            "household's own capital its visible standard of living must "
            "track, reused as both the raw status cost and the ceiling on "
            "how far the appearances budget can be trimmed. A real figure "
            "needs an actual model of conspicuous consumption in a "
            "patronage society, not a flat share of capital.")
    LIVING_COST_APPEARANCES_SHARE_OF_ROOM = declare(
        "LIVING_COST_APPEARANCES_SHARE_OF_ROOM", 0.75, kind="temporary_heuristic",
        unit="fraction of remaining income", source=None, confidence="D",
        why="How much of what is left after eating, tax, upkeep and wages "
            "a household will spend on keeping up appearances, so status "
            "spending draws down what is left rather than starving the "
            "household outright - see the comment above for the ruined-"
            "household bug this fixed. The specific three-quarters share "
            "is tuned game balance, not derived from any household-budget "
            "study.")

    HOURS_PER_PERSON_YEAR = declare(
        "HOURS_PER_PERSON_YEAR", 2000.0, kind="engineering_estimate",
        unit="hours/person/year", source=
        "prices.json: a 10-hour day, 250 working days a year, less feasts "
        "and holidays.",
        confidence="B",
        why="Converts an annual wage into an hourly rate (stall_diagnosis' "
            "own wage-comparison arithmetic) and back - the same working-"
            "year convention prices.json itself uses, so the two stay "
            "consistent.")
