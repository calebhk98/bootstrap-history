"""Whether you may begin, the levers that change the answer, and beginning.

Split out of sim/engine/projects.py (see that file's own docstring for why):
start_reason() is the legality test a project must pass before it may be
started, and the three things that can change its answer live here beside
it because start_reason's own text names all three directly - bribe() buys
down the scandal and state opposition start_reason checks, bounty_eligible()/
post_bounty() convert denarii into someone else's hours instead of the
founder's own, and substitution_quality() resolves the req_any groups
start_reason calls before anything else. can_start() is a thin wrapper
around start_reason, and start_project()/stop_project() are the two actions
a passed (or overridden) legality test leads to.

These are methods of Sim; they are a mixin only so that they can live in a
file of their own. Behaviour is unchanged and verified byte-identical.
"""
from .data import win_condition_describe
from constants import declare


class StartingMixin:
    BRIBE_MEMORY_DECAY = declare(
        "BRIBE_MEMORY_DECAY", 0.7, kind="temporary_heuristic",
        unit="fraction of bribes_ytd carried into the running total",
        source=None, confidence="D",
        why="How much of what has already been spent buying protection "
            "this year still counts when a new bribe is offered - past "
            "advocacy fades rather than vanishing outright or lasting "
            "forever. Tuned decay, not measured against any real "
            "patronage-buying persistence.")
    BRIBE_PROTECTION_CAP = declare(
        "BRIBE_PROTECTION_CAP", 0.30, kind="temporary_heuristic",
        unit="protection points (0-1 scale)", source=None, confidence="D",
        why="The most protection money alone can buy, however much is "
            "spent - a break tester spent a million denarii for the "
            "identical result a hundred bought, and this is why: what a "
            "man cannot be paid to do more of, he cannot be paid more "
            "for. Tuned ceiling, not measured.")
    BRIBE_INCOME_SHARE = declare(
        "BRIBE_INCOME_SHARE", 0.6, kind="temporary_heuristic",
        unit="fraction of revenue", source=None, confidence="D",
        why="The income scale bribery is measured against - what counts "
            "as a serious sum is relative to this share of revenue, not a "
            "flat denarii figure, so a rich household is not bought off "
            "as cheaply as a poor one. Tuned scale, not measured.")
    BRIBE_DENARII_PER_SCANDAL_POINT = declare(
        "BRIBE_DENARII_PER_SCANDAL_POINT", 300.0, kind="temporary_heuristic",
        unit="denarii per point of household.scandal, at bribability=1",
        source=None, confidence="D",
        why="What it costs to erase one point of scandal outright. Scandal "
            "itself has no independent source model for who spreads it or "
            "how fast (the same gap STANDING_SCANDAL_PENALTY_PER_POINT in "
            "economy.py notes), so this conversion rate is a placeholder "
            "for that whole missing mechanism, not a measured price of "
            "silence.")

    def bribe(self, amount):
        """Pay your way out of trouble, deliberately, for a stated sum."""
        amount = float(amount)
        if amount <= 0:
            return False, "amount must be greater than zero. Nothing was changed."
        if amount > self.household.capital:
            return False, "you have %.0f denarii" % self.household.capital
        before = self.household.scandal
        prot_before = self.household.protection
        # DO NOT CHARGE FOR NOTHING. This took the money and then said, in the
        # same breath, "you had no scandal to answer and are already as
        # protected as money can make you, so this bought nothing" - a break
        # tester lost 5,000 to a single mistyped command that way, with no cap
        # and no confirmation. Work out whether it would move anything BEFORE
        # taking the money, and refuse if it would not.
        if before <= 0.0005:
            spent = self.BRIBE_MEMORY_DECAY * self.household.bribes_ytd + amount
            income = max(1.0, self.revenue())
            would = min(self.BRIBE_PROTECTION_CAP, (spent / (income * self.BRIBE_INCOME_SHARE)) * self.w["bribability"])
            already = min(self.BRIBE_PROTECTION_CAP,
                          (self.household.bribes_ytd / (income * self.BRIBE_INCOME_SHARE)) * self.w["bribability"])
            if would - already < 0.005:
                # SAY WHICH IT IS. A break tester was refused `bribe 1` at 0%
                # protection and told they were "already as protected as money
                # can make you", which is false and reads as a bug. One denarius
                # buys nothing measurable; a thousand would.
                _floor = 0.005 * (max(1.0, self.revenue()) * self.BRIBE_INCOME_SHARE) / max(
                    1e-9, self.w["bribability"])
                if already < 0.29:
                    return False, ("you have no scandal to answer, and %s "
                                   "denarii is too little to buy any advocacy "
                                   "worth having. About %s would begin to move "
                                   "your protection. Nothing was changed."
                                   % ("{:,.0f}".format(amount),
                                      "{:,.0f}".format(max(1.0, _floor))))
                return False, ("you have no scandal to answer and you are already "
                               "as protected as money can make you here, so this "
                               "would buy nothing. Nothing was changed.")
        # NEVER TAKE MORE THAN IT CAN SPEND. Both things a bribe buys are
        # bounded: scandal stops at zero and the protection it buys saturates
        # at 0.30. A break tester typed `bribe 1000000`, got exactly the same
        # 0% -> 32% as `bribe 100`, and was left with nothing at all - one
        # command, no cap, no warning, and the run was over. What a man cannot
        # be paid to do more of, he cannot be paid more for.
        bribability = max(1e-9, self.w["bribability"])
        for_scandal = self.household.scandal * self.BRIBE_DENARII_PER_SCANDAL_POINT / bribability
        income = max(1.0, self.revenue())
        # spent/(income*BRIBE_INCOME_SHARE) * bribability = BRIBE_PROTECTION_CAP, solved for the carried total
        for_protection = max(0.0, (self.BRIBE_PROTECTION_CAP * income * self.BRIBE_INCOME_SHARE) / bribability
                             - self.BRIBE_MEMORY_DECAY * self.household.bribes_ytd)
        useful = max(for_scandal, for_protection)
        refused = 0.0
        if amount > useful + 0.5:
            refused, amount = amount - useful, useful
        self.household.capital -= amount
        self.household.bribes_ytd = self.BRIBE_MEMORY_DECAY * self.household.bribes_ytd + amount
        self.household.scandal = max(0.0, self.household.scandal - amount / self.BRIBE_DENARII_PER_SCANDAL_POINT * bribability)
        self.update_protection()
        # BOTH THINGS IT BUYS. A break tester spent 500 denarii against a
        # scandal of zero, read "scandal 0.00 -> 0.00", and wrote it down as
        # money silently burned. It was not: bribes_ytd feeds protection, which
        # is what keeps an accusation from being made in the first place. A
        # reply that names only the half that did not move is what made a real
        # effect look like a bug.
        msg = "scandal %.2f -> %.2f for %.0f denarii" % (before, self.household.scandal, amount)
        if refused > 0.5:
            msg += ("; %s denarii of what you offered was not taken, because "
                    "this is as far as money goes here - you kept it"
                    % "{:,.0f}".format(refused))
        if self.household.protection > prot_before + 0.0005:
            msg += ("; advocacy and piety bought as well: protection %.2f -> %.2f"
                    % (prot_before, self.household.protection))
        elif before <= 0.0005:
            msg += ("; you had no scandal to answer and are already as protected "
                    "as money can make you, so this bought nothing")
        return True, msg

    BOUNTY_ELIGIBLE_COST_ADVANTAGE = declare(
        "BOUNTY_ELIGIBLE_COST_ADVANTAGE", 0.95, kind="temporary_heuristic",
        unit="dimensionless (civ_cost_factor)", source=None, confidence="D",
        why="A civilisation whose own cost multiplier for a technology is "
            "below this is treated as measurably good at it, and so able "
            "to recognise a bounty's success even outside the fixed "
            "craft-category allow-list (see this function's own comment "
            "on the Norse shipbuilding case this fixed). Tuned threshold "
            "for 'measurably good', not derived from any real skill "
            "assessment.")

    def bounty_eligible(self, k):
        """Can this be bought as a prize instead of built with your own hands?

        A public prize ("ten thousand sesterces to the first glassworker who
        brings me a clear sphere of glass the size of a millet seed") converts
        DENARII into someone else's HOURS, which is the trade you most want to
        make. It only works where the craft already exists in the Empire and the
        artisan can recognise success without understanding the theory. You
        cannot post a bounty for zone refining; nobody would know what to aim at.
        """
        node = self.nodes[k]
        # THE ALLOW-LIST IS ROME'S CRAFTS, BUT NOT THE WHOLE RULE: anything
        # this society is measurably GOOD at (its own cost multipliers say
        # so) can be recognised by its own craftsmen, whatever Rome's craft
        # categories happen to be - a civilisation whose own profile marks
        # shipbuilding as what it is best at in the world should not be
        # refused a bounty on it for want of a Roman artisan's judgement.
        if node["cat"] in ("glass_optics", "metallurgy", "precision", "power",
                        "agriculture", "information", "instruments"):
            return all(prereq_id in self.household.done for prereq_id in node["pre"])
        if self.civ_cost_factor(k) < self.BOUNTY_ELIGIBLE_COST_ADVANTAGE:
            return all(prereq_id in self.household.done for prereq_id in node["pre"])
        return False

    BOUNTY_PRICE_MULTIPLIER = declare(
        "BOUNTY_PRICE_MULTIPLIER", 2.5, kind="temporary_heuristic",
        unit="dimensionless multiplier on this society's own build cost",
        source=None, confidence="D",
        why="How far over the odds a public prize pays - converting "
            "denarii into someone else's hours is a real trade a founder "
            "would want to make, and it should cost a real premium to "
            "make it. Tuned so a bounty is a genuine but expensive "
            "shortcut, not measured against any real prize-versus-wage "
            "ratio.")
    BOUNTY_FOUNDER_HOURS_SHARE = declare(
        "BOUNTY_FOUNDER_HOURS_SHARE", 0.35, kind="temporary_heuristic",
        unit="fraction of the node's founder-hours still owed",
        source=None, confidence="D",
        why="A bounty saves the founder most, not all, of their own hours "
            "on the work - some direction and oversight is still needed, "
            "which is why this is 0.35 rather than 0.0 ('save 65% of your "
            "own hours', this method's own docstring). Tuned split, not "
            "measured.")

    def post_bounty(self, k):
        """Pay well over the odds, save 65% of your own hours, gain visibility."""
        node = self.nodes[k]
        # BOUNTY_PRICE_MULTIPLIER x the cost THIS society would actually incur,
        # not x an abstract base. A playtester found `why` quoting 188 denarii
        # to build a node while `bounty` demanded 588 for the same thing,
        # because the bounty ignored the civilization and price factors the
        # build applies.
        price = (node["_total_cost"] * self.BOUNTY_PRICE_MULTIPLIER * self.civ_cost_factor(k)
                 * self.material_cost_factor(k) * self.cost_money_factor())
        if price > self.household.capital:
            return False
        self.household.capital -= price
        self.household.total_spend += price
        self.household.bounties_paid += 1
        self.household.active[k] = dict(ph_left=node["ph"] * self.BOUNTY_FOUNDER_HOURS_SHARE, yrs=0.0, spent=price)
        self.household.bountied.add(k)
        # A public prize makes you conspicuous - and that is what `scandal`
        # and `eminence` measure; see core.py's note on scandal.
        self.household.log.append((self.year, "posted a public bounty for %s (%s den)"
                         % (node["name"], f"{price:,.0f}")))
        return True

    PURCHASABLE_SUBSTITUTE_QUALITY_DISCOUNT = declare(
        "PURCHASABLE_SUBSTITUTE_QUALITY_DISCOUNT", 0.9, kind="temporary_heuristic",
        unit="dimensionless multiplier on the option's stated quality",
        source=None, confidence="D",
        why="A substitution option that is a purchasable commodity rather "
            "than something built or known scores slightly below its "
            "stated quality - buying a fuel or a vessel off the market is "
            "not quite as good as having built the specific thing the "
            "tree names. Tuned discount, not measured.")

    def substitution_quality(self, k):
        """Resolve `req_any` groups: for each, the best option you actually have.

        A steam engine does not REQUIRE coal and steel. It requires a fuel and a
        pressure vessel. Wood in a bronze boiler works. It is just bad, and the
        quality factor is how bad: it multiplies output and divides efficiency.
        """
        node = self.nodes[k]
        groups = node.get("req_any") or []
        if not groups:
            return 1.0, True
        quality = 1.0
        for group in groups:
            best = self._substitution_group_best(k, group)
            if best <= 0:
                self._record_substitution_gap(group)
                return 0.0, False        # no option in this group is available
            quality *= best
        self.household._last_subst_gap = None
        return quality, True

    def _substitution_group_best(self, k, group):
        """The best quality any option in one `req_any` group actually offers."""
        best = 0.0
        for opt, qual in (group.get("options") or {}).items():
            if opt in self.household.done or opt in self.nodes.get(k, {}).get("mat", {}):
                best = max(best, float(qual))
            elif opt not in self.nodes:
                best = max(best, float(qual) * self.PURCHASABLE_SUBSTITUTE_QUALITY_DISCOUNT)   # a purchasable commodity
        return best

    def _record_substitution_gap(self, group):
        """Record which group failed and what would have satisfied it.

        WHICH GROUP, AND WHAT WOULD SATISFY IT. "no viable option in a
        required substitution group (fuel, vessel, etc.)" was the one
        blocked-reason a play tester never decoded in a whole run: it
        names no candidate and no fix, and the parenthesis is a guess
        at what the group might be about rather than what it is.
        A GROUP KEY IS A SLUG, NOT PROSE. Surfacing it verbatim put
        "unknown_source" in front of a player, which is data, not
        English. Say it as words.
        """
        _gname = (group.get("name") or group.get("group") or "").replace("_", " ")
        if _gname:
            _gname = ("an " if _gname[0] in "aeiou" else "a ") + _gname
        self.household._last_subst_gap = (
            _gname or "one of the things it can be made from",
            sorted((group.get("options") or {}), key=lambda o:
                   -float((group.get("options") or {})[o]))[:4])

    ARREARS_GRACE_YEARS = declare(
        "ARREARS_GRACE_YEARS", 3, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="How many consecutive years insolvent before new work starts "
            "being restricted at all - creditors care about PERSISTENT "
            "insolvency, not one bad year. Declared as the INT the source "
            "wrote: compared against an integer year-count "
            "(household.insolvent_years) with no fractional meaning, so "
            "widening it to a float would only invite the kind of "
            "int-to-float SAVE_FIELDS drift CLAUDE.md warns about "
            "elsewhere, for no benefit here. Tuned grace period, not "
            "measured.")
    ARREARS_CHEAP_PROJECT_FLOOR = declare(
        "ARREARS_CHEAP_PROJECT_FLOOR", 600.0, kind="temporary_heuristic",
        unit="denarii", source=None, confidence="D",
        why="Even deep in persistent arrears, a project costing less than "
            "this is always 'cheap enough to need nobody's permission' - a "
            "flat floor under ARREARS_CHEAP_PROJECT_SURPLUS_MULTIPLE's own "
            "surplus-based figure so a household with zero surplus is not "
            "locked out of every project whatever. Tuned, not measured.")
    ARREARS_CHEAP_PROJECT_SURPLUS_MULTIPLE = declare(
        "ARREARS_CHEAP_PROJECT_SURPLUS_MULTIPLE", 2.0, kind="temporary_heuristic",
        unit="years of true surplus", source=None, confidence="D",
        why="While persistently insolvent, a project is 'cheap enough' if "
            "it costs no more than this many years of the household's "
            "actual surplus (revenue minus upkeep, living cost and mine "
            "operating cost) - measured against what is actually LEFT, "
            "not gross turnover, which the fix here specifically corrects "
            "(see this method's own comment on the 11,637-revenue "
            "household this was measured against gross for). Tuned "
            "multiple, not derived.")
    ARREARS_HARD_STOP_FLOOR = declare(
        "ARREARS_HARD_STOP_FLOOR", 4000.0, kind="temporary_heuristic",
        unit="denarii", source=None, confidence="D",
        why="However cheap a project looks, new work stops outright once "
            "the household is this far underwater - a flat floor under "
            "ARREARS_HARD_STOP_REVENUE_MULTIPLE's revenue-based figure so "
            "a household with negligible revenue is not exempted from the "
            "hard stop entirely. Tuned, not measured.")
    ARREARS_HARD_STOP_REVENUE_MULTIPLE = declare(
        "ARREARS_HARD_STOP_REVENUE_MULTIPLE", 2.0, kind="temporary_heuristic",
        unit="years of revenue", source=None, confidence="D",
        why="The debt-to-revenue ratio, in years of gross revenue, past "
            "which new work stops outright regardless of a project's own "
            "cost. Tuned ceiling, not derived from any real lending "
            "standard.")
    STATE_WARY_THRESHOLD = declare(
        "STATE_WARY_THRESHOLD", -0.4, kind="temporary_heuristic",
        unit="state_interest score", source=None, confidence="D",
        why="Below this state_interest score, the state is merely wary of "
            "a technology and a local patron's name is enough cover to "
            "proceed. See docs/architecture 03_SOCIAL_POLITICS.md section "
            "4 for the social-approval mechanism this gates; the specific "
            "cutoff is tuned game balance over that mechanism, not itself "
            "derived from a historical record of state reactions.")
    STATE_OPPOSED_THRESHOLD = declare(
        "STATE_OPPOSED_THRESHOLD", -1.2, kind="temporary_heuristic",
        unit="state_interest score", source=None, confidence="D",
        why="Below this state_interest score, the state actively opposes "
            "a technology and only senatorial-tier patronage or high "
            "personal protection can proceed anyway. Tuned cutoff, three "
            "times STATE_WARY_THRESHOLD's own magnitude so opposition is a "
            "meaningfully harder wall than wariness, not derived from any "
            "historical record.")
    STATE_OPPOSITION_PROTECTION_OVERRIDE = declare(
        "STATE_OPPOSITION_PROTECTION_OVERRIDE", 0.45, kind="temporary_heuristic",
        unit="protection points (0-1 scale)", source=None, confidence="D",
        why="Personal protection above this substitutes for senatorial "
            "patronage when the state actively opposes a technology. "
            "Tuned so protection is a real alternative route, not "
            "measured.")

    def start_reason(self, k, ignore_trade=False, _memo=None, _why=True):
        """Same legality test as `can_start`, but explains a refusal instead of
        just returning False. `can_start` is a thin wrapper around this;
        the wrapper exists because the optimizer's inner loop calls it a huge
        number of times and does not want to build a string it will discard.
        The reason text is what a PLAYER needs (human or agent): not just "no",
        but "no, because you need a local patron first".

        ignore_trade skips only the "does the trade exist" check below, so
        auto_train can ask a narrower question than "what would help
        eventually": "is THIS the one thing standing between me and starting
        this, right now?" See its use in step(), 4a2.

        _memo is is_visible()'s shared per-descent cache, passed straight
        through to the is_visible() calls below for a missing node's own
        visibility. Not this function's concern otherwise; see is_visible's
        docstring for why it exists.

        _why=False: the caller only wants the boolean (can_start, and
        is_visible's own recursive descent through this same function) and
        will throw the second element away. Every `return False, <message>`
        below becomes `return False, None` in that case, which matters
        because several of those messages are themselves built by walking
        the tree - missing_prereq_message chief among them, which calls
        is_visible on every missing prerequisite, which calls back into
        start_reason on each. None of that recursion changes the boolean
        this function is about to return; it only decides which prerequisite
        NAMES a player refusal is allowed to mention. Skipping it here is
        purely an optimisation: every branch below still runs exactly the
        same tests it always did to arrive at True/False, and only the
        prose built FROM that answer is elided. See the callers of this
        flag (can_start, is_visible) for why they are the only two that may
        pass False - every other caller (why, available, stuck, path,
        bounty, the protocol layer) still wants the sentence and so keeps
        the default.

        The body below is a fixed sequence of independent legality checks,
        each in its own method (_check_win_condition,
        _check_already_done, and the rest of _START_REASON_CHECKS below),
        run in the exact order they always ran in. Each one returns either
        None ("no verdict, ask the next check") or the (ok, message) tuple
        this function should return right now - so the FIRST check with an
        opinion wins, exactly as the old single `if`/`elif` chain did. See
        _START_REASON_CHECKS's own comment for why the order is the one
        contract this split cannot touch.
        """
        if k not in self.nodes:
            return False, ("no such node" if _why else None)
        node = self.nodes[k]
        for check in self._START_REASON_CHECKS:
            verdict = check(self, k, node, ignore_trade, _memo, _why)
            if verdict is not None:
                return verdict
        return True, None

    def _check_win_condition(self, k, node, ignore_trade, _memo, _why):
        if node.get("win_condition"):
            # A THRESHOLD GOAL, NOT A PROJECT. This is measured, not built:
            # nobody ever spends hours or money on it, so it is never
            # offered as something to start, whatever its (always zero)
            # cost fields say and however satisfied its `pre` looks. It
            # completes itself the moment the live measurement crosses the
            # target - see core.py's per-year win-condition check, the only
            # other place that reads this field. See
            # win_condition_describe() for the player-facing sentence.
            #
            # win_condition_describe() is pure formatting (data.py - no rng,
            # no mutation, no log) but there is no reason to call it at all
            # when nobody will read the string it returns.
            return False, (("this is not something you build; it happens on "
                           "its own once %s" % win_condition_describe(node))
                           if _why else None)
        return None

    def _check_already_done(self, k, node, ignore_trade, _memo, _why):
        if k in self.household.done:
            # A MOTHBALLED WORK IS NOT FRESH RESEARCH, and it is not "already
            # done" either: you know how, and the plant is gone. `restore`
            # puts it back at a fraction of the cost, so this branch must be
            # checked BEFORE the flat "already done" case below, or a
            # mothballed work gets swallowed by the wrong, less useful
            # advice.
            if k in getattr(self.household, "mothballed", set()):
                # project_cost() is pure (no rng, no log, no mutation - see
                # its own docstring and the factor functions it calls) but
                # it is real arithmetic over several factor tables, and
                # nobody reads the number when _why is False.
                return False, (("you built this once and let it go; you already "
                               'know how, so restoring it is cheaper than '
                               'starting over: {"cmd":"restore","id":"%s"} for '
                               "about %.0f denarii"
                               % (k, self.project_cost(k) * self.RESTORE_COST_SHARE_OF_BUILD)) if _why else None)
            return False, ("already done" if _why else None)
        return None

    def _check_already_active(self, k, node, ignore_trade, _memo, _why):
        if k in self.household.active:
            return False, ("already active" if _why else None)
        return None

    def _check_needs_first(self, k, node, ignore_trade, _memo, _why):
        # NOT DEAR HERE, IMPOSSIBLE HERE. See SocietyMixin.needs_first.
        # needs_first() itself is always called: `_nf` IS the answer, not
        # just words about it. Only the sentence built from the two strings
        # it hands back is skippable.
        _nf, _why_nf = self.needs_first(k)
        if _nf:
            return False, (("%s. Build %s first and this opens with it"
                           % (_why_nf, _nf)) if _why else None)
        return None

    def _check_unobtainable(self, k, node, ignore_trade, _memo, _why):
        # A MOTHBALL ENTRY WITHOUT THE KNOWLEDGE IS A STALE ENTRY: it must
        # fall through to the ordinary checks below, not be refused here and
        # sent to `restore`, which answers "you no longer know how" and
        # cannot actually rebuild the node - a deadlock no verb could clear
        # for a node that gates a whole branch of the tree.
        if node["cat"] == "unobtainable":
            return False, ("retired category: unobtainable in this tree"
                           if _why else None)
        return None

    def _check_foreign_only(self, k, node, ignore_trade, _memo, _why):
        if self._is_foreign_only(k):
            return False, (("that is an institution of a different society. %s has "
                           "no such thing, and it is not something you can build "
                           "here" % self.civ.get("name", "this society"))
                           if _why else None)
        return None

    def _check_missing_prereqs(self, k, node, ignore_trade, _memo, _why):
        missing = [prereq_id for prereq_id in node["pre"] if prereq_id not in self.household.done]
        if missing:
            # NAME ONLY WHAT YOU HAVE HEARD OF. A tester wrote a twenty-line
            # crawler that did nothing but read this message, and mapped 163
            # nodes - the entire ancestor closure of the transistor - in eight
            # rounds, while `why` and `path` dutifully refused every one of them.
            # Fog that one error message undoes is not fog. The formatting
            # itself lives in missing_prereq_message (fog.py) now, shared with
            # `bounty`, so there is exactly one fog filter for this sentence
            # rather than one per caller.
            #
            # THIS is the call the profiler found: missing_prereq_message
            # calls is_visible() on every missing prerequisite, which
            # recurses back into start_reason on each - a full descent
            # through the tree purely to decide which of these ids a fogged
            # player is allowed to be told. `missing` (the boolean-relevant
            # part - there ARE missing prerequisites) is already known
            # above; only the message about which ones is skippable.
            return False, (self.missing_prereq_message(missing, _memo=_memo)
                           if _why else None)
        return None

    def _check_substitution(self, k, node, ignore_trade, _memo, _why):
        if not self.substitution_quality(k)[1]:
            # substitution_quality(k) ITSELF is always called, above - it is
            # not just words, it sets self.household._last_subst_gap as a side effect
            # (read a few lines down) and its second return value is the
            # actual test this branch is on. What is skippable is only the
            # _seen filter below, which calls is_visible() on every option in
            # the gap (another recursive descent), and the sentence built
            # from it.
            if not _why:
                return False, None
            _grp, _opts = getattr(self.household, "_last_subst_gap", None) or (None, [])
            _seen = [option_id for option_id in _opts
                     if option_id not in self.nodes or self.is_visible(option_id, _memo=_memo)]
            return False, ("this needs %s and you have none of the things that "
                           "would serve%s"
                           % (_grp or "a material or a vessel it can be built "
                                      "around",
                              (": any of " + ", ".join(_seen) + " would do")
                              if _seen else
                              ", and none of them is anything you have heard "
                              "of yet"))
        return None

    # A refusal must name the remedy, not only the shortfall: staff is not
    # a technical prerequisite, so it never appears in `path`, and a
    # refusal that only names the shortage leaves a player with no way to
    # discover what would fix it.
    # Arrears blocks NEW commitments, with two escape hatches, because
    # without them a household that goes bankrupt and has a prerequisite
    # abandoned out from under it could never rebuild it - an unrecoverable
    # softlock, not a setback. First hatch: creditors care about PERSISTENT
    # insolvency, not one bad year. Second: anything you can fund from this
    # year's income needs nobody's permission.
    # "Cheap enough to need nobody's permission" means payable out of what
    # is actually LEFT, not out of turnover: measuring against gross
    # revenue would let a bankrupt household with 11,637 of income and
    # 6,020 of upkeep start 11,000-denarius projects every year, each one
    # halted by the creditors a year later with nothing to show for it.
    # COMPUTED ONLY WHEN IT CAN MATTER. revenue() walks every technology you
    # have, and start_reason is called for every node in the tree, several
    # times over, by can_start and by is_visible under fog. A 45-year
    # fogged Mexica run made 335,276 calls to revenue() from here and spent
    # 38 of its 100 seconds inside them - to compute a surplus that is only
    # read when the household has been insolvent three years or more, which
    # in most runs is never.
    # A CREDIT FREEZE HAS TO APPLY TO THE PLAYER TOO: creditors seize
    # CONCERNS, so a player who opens none can default over and over for
    # nothing but reputation, which regenerates - and building raises
    # reputation, which raises the credit limit. Checking the freeze only
    # in the optimizer's own start loop would let a person at the keyboard
    # be frozen out on paper while carrying on borrowing and starting
    # things regardless.
    def _check_credit_frozen(self, k, node, ignore_trade, _memo, _why):
        if self.year < getattr(self.household, "credit_frozen_until", 0):
            # SAY IF IT WILL NEVER LIFT IN TIME: a freeze date past the
            # run's own horizon is not a date, it is the end of the run
            # wearing a date's clothes.
            _end = getattr(self, "end_year", None) or (
                self.cfg["start_year"] + self.cfg["horizon_years"])
            return False, (("nobody here will fund new work: your creditors were "
                           "left unpaid and the word is out. They will deal with "
                           "you again in %d%s, and until then you may finish what "
                           "is running, and pay for something out of money you "
                           "actually hold."
                           % (int(self.household.credit_frozen_until),
                              " - which is past the horizon at %d, so not within "
                              "this run" % int(_end)
                              if self.household.credit_frozen_until > _end else ""))
                           if _why else None)
        return None

    def _check_arrears(self, k, node, ignore_trade, _memo, _why):
        if getattr(self.household, "insolvent_years", 0) >= self.ARREARS_GRACE_YEARS:
            surplus = (self.revenue() - self.upkeep() - self.living_cost()
                       - self.mine_operating_cost())
            cheap_enough = (self.project_cost(k) <= max(self.ARREARS_CHEAP_PROJECT_FLOOR,
                                                          surplus * self.ARREARS_CHEAP_PROJECT_SURPLUS_MULTIPLE))
        else:
            cheap_enough = True
        if (getattr(self.household, "insolvent_years", 0) >= self.ARREARS_GRACE_YEARS
                and not cheap_enough
                and self.household.capital < -max(self.ARREARS_HARD_STOP_FLOOR,
                                                   self.revenue() * self.ARREARS_HARD_STOP_REVENUE_MULTIPLE)):
            return False, (("you have been in arrears %d years and are %.0f denarii down; "
                           "nobody will fund a new undertaking of this size. Something "
                           "you can pay for out of this year's income is still allowed, "
                           "so is finishing or stopping what is running."
                           % (getattr(self.household, "insolvent_years", 0), -self.household.capital))
                           if _why else None)
        return None

    def _check_scholar_staff(self, k, node, ignore_trade, _memo, _why):
        # SCHOLARS UNDER CONTRACT COUNT TOO - Complaints/34. This read
        # effective_scholars(), the standing headcount, so scholar hours you
        # had already bought and paid for could not satisfy the requirement,
        # and the refusal's own advice was to go and commission them.
        # Reproduced against the live protocol: a 2,000-hour commission
        # succeeded, took the money, and left this refusal byte-identical.
        #
        # Exactly the bug the craft gate below was fixed for, never extended
        # to scholars - see scholar_hands_available() in labour.py, which is
        # craft_hands_available() with the trade family changed.
        if node["sch"] > self.scholar_hands_available():
            # _staff_advice is pure (labour.py: no rng, no log, no mutation -
            # it only reads is_venture/is_visible/nodes/artisans/scholars),
            # but it walks STAFF_SOURCES and can itself call is_visible, so
            # it is skipped along with the rest of the sentence.
            return False, (("needs %d trained scholars, and you have %.1f - "
                            "counting people on your staff and yourself, plus "
                            "any hours already bought under contract as that "
                            "share of one more. %s"
                           % (node["sch"], self.scholar_hands_available(),
                              self._staff_advice("scholars")))
                           if _why else None)
        return None

    def _check_craft_staff(self, k, node, ignore_trade, _memo, _why):
        # CRAFTSMEN YOU HAVE UNDER CONTRACT COUNT TOO. This read self.household.artisans
        # alone, so work you had already paid an outside shop to do could not
        # satisfy the requirement - and the refusal's own advice was to go and
        # commission it. `commission` could not unblock the gate that
        # recommended commission.
        #
        # It is also what deadlocked an entire civilisation. A Norse run ended
        # at year 1500 with 31,068 denarii, 136 technologies and 1.6 craftsmen,
        # unable to build workshop_first because it needs 2 - while every
        # institution that would raise the staff ceiling (freedman_staff,
        # collegium_licensed, school_founded) needs workshop_first first. You
        # needed two craftsmen to build the place craftsmen work, and could
        # never get to two. The Norse reached the goal in 0% of runs.
        #
        # Buying a jobbing carpenter for a season to raise your workshop is
        # what a person in this position actually did.
        if node["art"] > self.craft_hands_available():
            # A SHARE OF A YEAR, NOT ONLY BODIES. craft_hands_available()
            # adds hours already bought under contract as that fraction of
            # one more craftsman's year (see its own docstring: "a year of
            # a carpenter's time IS a carpenter") - so the figure below can
            # be fractional even when every actual person on the payroll is
            # a whole one. Said inline, not left for the player to work out
            # from a number that otherwise looks like a body cut short.
            return False, (("needs %d trained craftsmen, and you have %.1f - "
                           "counting people on your staff plus any hours "
                           "already bought under contract as that share of "
                           "one more. %s"
                           % (node["art"], self.craft_hands_available(),
                              self._staff_advice("artisans")))
                           if _why else None)
        return None

    def _check_absent_trades(self, k, node, ignore_trade, _memo, _why):
        # THE TRADE HAS TO EXIST. A node wanting 450 hours of an engineer cannot
        # be built by smiths, and in 100 AD there is no such person as a private
        # engineer: the wage table says so itself. You make one by teaching one.
        absent = [] if ignore_trade else sorted(trade_id for trade_id in node["lab"]
                                                if not self.trade_available(trade_id))
        if absent:
            return False, (("this needs %s and there are none in this society. "
                           'Teach one: {"cmd":"train","trade":"%s","n":2} '
                           "(about 450 of your own hours each, two years)"
                           % (", ".join(trade_id + "s" for trade_id in absent), absent[0]))
                           if _why else None)
        return None

    def _check_none_left_trades(self, k, node, ignore_trade, _memo, _why):
        # AND SOMEBODY HAS TO BE LEFT. A trade you taught still counts as
        # existing after the last of them has died or been poached, so `why`
        # and `available` said CAN START NOW while the project, once begun,
        # counted down four years and was abandoned with the spend lost - the
        # trade check asked whether the trade existed and never whether anyone
        # could be had. A play tester lost six projects in one year to it and
        # could only find out by starting them.
        # People already being TAUGHT count: they will be ready, and starting
        # work that lands the year they qualify is the right thing to do.
        _none_left = [] if ignore_trade else sorted(
            trade_id for trade_id, want in (node["lab"] or {}).items()
            if want > 0 and self.market_supply(trade_id) <= 0.0
            and self._trade_headcount_pending(trade_id) <= 0.0)
        if _none_left:
            return False, (("this needs %s and there is not one left here to do "
                           "it: you taught the trade and nobody is currently "
                           'holding it. {"cmd":"train","trade":"%s","n":2} makes '
                           "more, or hire from your own if you have any"
                           % (", ".join(trade_id + "s" for trade_id in _none_left), _none_left[0]))
                           if _why else None)
        return None

    def _check_social_approval(self, k, node, ignore_trade, _memo, _why):
        # SOCIAL APPROVAL GATE. Some things the State does not want built, and no
        # amount of money substitutes for someone powerful being willing to be
        # associated with it. See 03_SOCIAL_POLITICS.md section 4.
        # SOCIAL APPROVAL. Computed from this civilization's values and this
        # technology's traits, not from a number baked into the technology.
        # Never let the gate ask for a thing in order to get that same thing:
        # the patronage and institution nodes are how you BUY permission, so they
        # cannot themselves require permission.
        if node["cat"] in ("social", "institution", "foundation", "capability", "material"):
            return True, None
        state_interest_score = self.state_interest(node)
        # state_interest() itself is always computed, above: it decides the
        # branch. _patron_advice, below, is not - it is pure (no rng, no
        # log, no mutation: see its own docstring) but it can call
        # is_visible() on a prerequisite chain, which is another recursive
        # descent nobody needs when only the boolean was asked for.
        if state_interest_score < self.STATE_WARY_THRESHOLD and not self.running("patron_local"):
            # NAME THE NODE, by the word you would type. "Get at least a local
            # patron first" was the whole message, and a play tester who read
            # it several times never connected it to `patron_local`, which was
            # sitting startable in the list in front of them the entire time.
            #
            # BUT ONLY IF THEY HAVE HEARD OF IT. A Mexica play tester read this
            # exact line in `available`, typed the command it gave them, and
            # was told "you have never heard of any such thing" - by the same
            # engine, one command later. Naming an undiscovered id here is the
            # third instance of one filter living in one place: start_reason
            # had it, `bounty` skipped it, `why` leaked another node's id
            # through a kb path, and this line skipped it too. The advice is
            # worth nothing when the command it gives is refused, and under
            # fog it is worse than nothing, because it is a free reveal.
            return False, (("the state is wary of this (state interest %.1f); "
                           "%s"
                           % (state_interest_score, self._patron_advice("patron_local",
                                                      "a local patron's name "
                                                      "behind you")))
                           if _why else None)
        if state_interest_score < self.STATE_OPPOSED_THRESHOLD and not (
                self.running("patron_senatorial")
                or self.household.protection > self.STATE_OPPOSITION_PROTECTION_OVERRIDE):
            return False, (("the state actively opposes this (state interest "
                           "%.1f); %s, or protection above %.2f (you have "
                           "%.2f)"
                           % (state_interest_score, self._patron_advice("patron_senatorial",
                                                      "patronage at the very "
                                                      "top"),
                              self.STATE_OPPOSITION_PROTECTION_OVERRIDE,
                              self.household.protection))
                           if _why else None)
        return None

    # THE ORDER IS THE CONTRACT. start_reason reports the FIRST reason in
    # this sequence that has an opinion, exactly as the single if/elif chain
    # it replaced did line by line - a player choosing between two blockers
    # reads only ever the one named here first, so re-ordering this tuple
    # changes what a refusal says even when every check's own logic is
    # untouched. Plain functions, not bound methods: referencing them by
    # their bare class-body name (rather than through an instance) gets the
    # underlying function object, which is why each call below passes `self`
    # explicitly.
    _START_REASON_CHECKS = (
        _check_win_condition,
        _check_already_done,
        _check_already_active,
        _check_needs_first,
        _check_unobtainable,
        _check_foreign_only,
        _check_missing_prereqs,
        _check_substitution,
        _check_credit_frozen,
        _check_arrears,
        _check_scholar_staff,
        _check_craft_staff,
        _check_absent_trades,
        _check_none_left_trades,
        _check_social_approval,
    )

    def _patron_advice(self, k, in_world):
        """What to tell a player who needs `k` before they may begin.

        The id and the command only when they have heard of it; the same
        advice in plain words when they have not, which under fog is most of
        the time this fires. `in_world` is that plain-words version.
        """
        if not self.is_visible(k):
            return "you will need %s before anyone here will let you begin" % in_world
        if k in self.household.done:
            return ("get %s: you have built it already, so 'open %s' to put "
                    "it behind you" % (in_world, k))
        # AND IT HAS TO BE STARTABLE, or this is still a refusal recommending
        # a refusal. patron_local itself needs identity_cover, so even with
        # the fog off, "get a local patron first: 'start patron_local'" sent
        # the player straight into "missing prerequisites: identity_cover".
        # Prerequisites read directly rather than through start_reason,
        # because this is called FROM start_reason and a second entry into it
        # is a recursion this line does not need: the missing-prereq case is
        # the one that actually bit, and the fog filter for naming them
        # already exists.
        missing = [prereq_id for prereq_id in self.nodes[k]["pre"] if prereq_id not in self.household.done]
        if missing:
            seen = [prereq_id for prereq_id in missing if self.is_visible(prereq_id)]
            return ("get %s first, which itself wants %s"
                    % (in_world,
                       ", ".join(seen) if seen
                       else "something you have not heard of yet"))
        return "get %s first: 'start %s'" % (in_world, k)

    def can_start(self, k, _memo=None):
        # _why=False: this discards the message anyway, and it is the
        # optimizer's own per-year loop that calls this for every node in
        # the tree - the single hottest path in the engine (see
        # start_reason's own docstring on _why for what this skips).
        return self.start_reason(k, _memo=_memo, _why=False)[0]

    def start_project(self, k):
        """PLAYER-CHOSEN start. This is the whole reason `--manual` and the
        `agent` JSON protocol exist: the old `play` command let you type a
        node id, but all that did was move it to the front of `order`, the
        list the OPTIMIZER in step() still walked on its own; the optimizer
        went on starting whatever ELSE it wanted that year regardless of what
        you typed. You never actually chose anything, you only nudged a
        priority queue you did not otherwise control. This method is the real
        thing: it applies the same legality check as the optimizer
        (`start_reason`), and if it passes, THIS is the only place besides the
        optimizer's own loop that ever adds to `self.household.active`. In `--manual`
        mode the optimizer's loop is switched off entirely (see step(), 4b),
        so this becomes the only way anything ever starts.
        """
        ok, why = self.start_reason(k)
        if not ok:
            return False, why
        # YOU MAY COMMIT PAST WHAT YOU HOLD, AND NOT PAST WHAT ANYONE WILL LEND.
        # `help economy` states exactly that contract, and nothing enforced the
        # second half. A break tester started all 104 available projects in a
        # fresh England game - 43,914 denarii of work in hand against 400 in
        # cash and a displayed credit limit of 1,503 - and was at -3,672 one
        # step later. Committing to something you cannot yet afford is
        # realistic project accounting and stays; committing to thirty times
        # what anyone will advance you is not a plan, it is an accounting
        # fiction, and the limit the player read a second earlier has to mean
        # something.
        price = self.project_cost(k)
        # WHAT IS LEFT TO PAY, not the whole bill. Money already sunk into this
        # node - by you stopping it, or by the creditors stopping it - comes
        # off, and testing against the gross would refuse a project that is
        # nearly paid for. See stop_project.
        _paid_now = min(price, max(0.0, (getattr(self.household, "paid_towards", None)
                                         or {}).get(k, 0.0)))
        price -= _paid_now
        # sorted(): summing floats over a dict whose keys came from a set.
        owed = sum(project_state.get("cost_left") or 0.0
                   for project_state in (self.household.active[node_id] for node_id in sorted(self.household.active)))
        ceiling = max(0.0, self.household.capital) + self.credit_limit()
        # THE AFFORDABILITY TEST MUST APPLY TO THE FIRST PROJECT TOO: a
        # guard that only checked once something was already active would
        # let an opening move be started far beyond what cash and credit
        # could cover, only to see the identical command refused - quoting
        # the shortfall exactly - the moment a second, much cheaper project
        # was started right after.
        if owed + price > ceiling:
            return False, ("you already owe %s denarii on work in hand; this "
                           "would take it to %s, and between cash and credit "
                           "you can raise %s. Finish or stop something first."
                           % ("{:,.0f}".format(owed), "{:,.0f}".format(owed + price),
                              "{:,.0f}".format(ceiling)))
        node = self.nodes[k]
        # CREDIT FOR WHAT YOU ALREADY PAID. See enforce_credit_limit: when the
        # creditors stop a project the money already sunk into it is kept
        # against the node, and this is where it comes back off the bill.
        _paid = getattr(self.household, "paid_towards", None) or {}
        _paid.pop(k, None)          # spent once; the figure is _paid_now above
        _already = _paid_now
        # A THING YOU ARE REBUILDING IS NOT A THING SITTING IDLE. If the
        # knowledge was destroyed and only the mothball entry survived, that
        # entry is stale the moment you begin again - and while it stands,
        # `available` hides the node and `restore` claims it can reopen it.
        self.household.mothballed.discard(k)
        # lab_left STARTS FULL, SET HERE - not lazily the first time
        # lab_year_draw runs. step() reduces ph_left for THIS year before it
        # ever reaches the labour section, so a lazy init reading ph_left at
        # that point sees a project already most of the way through its
        # founder-hours and (wrongly) concludes the hired-labour total must be
        # nearly done too. Setting the real total here, before any of that
        # runs, is what fixed it.
        self.household.active[k] = dict(ph_left=float(node["ph"]), yrs=0.0,
                              spent=_already, cost_left=price,
                              lab_left=dict(node["lab"]))
        # A genuinely instantaneous capability should not need an otherwise
        # empty annual turn merely to trip the completion check in step().
        # Keep anything with money, labour, risk, or a calendar floor on the
        # normal path: those are projects even when founder-hours happen to be
        # zero.
        if (node["ph"] <= 0 and self.calendar_floor(k) <= 0 and price <= 0.5
                and not node["lab"] and self.effective_risk(k) <= 0):
            self._complete(k)
            return True, None
        if _already > 0.5:
            self.household.log.append((self.year, "%s begun again; the %s denarii already "
                                        "paid on it before comes off the bill"
                             % (k, "{:,.0f}".format(_already))))
        # Director hours in step() 5 are handed out by priority in `order`.
        # A thing you just chose to work on should get first call on your own
        # hours, exactly as the old (cosmetic) reprioritisation implied it did.
        if k in self.order:
            self.order.remove(k)
        self.order.insert(0, k)
        return True, None

    def stop_project(self, k):
        """Stop a project you started. Your HOURS are gone; the money stands.

        Money already spent must stand against the node - the same credit
        enforce_credit_limit keeps - and come off the bill if you begin
        again, rather than being burned along with the hours: burning both
        would make stopping something yourself cost exactly as much as
        letting the creditors take it, so no branch would ever make `stop`
        the right move. The site does not un-dig itself either way. The
        hours really are gone: that is your year, and you spent it.
        """
        if k not in self.household.active:
            return False, "not active"
        project_state = self.household.active.pop(k)
        self.household.bountied.discard(k)
        _paid = getattr(self.household, "paid_towards", None)
        if _paid is None:
            _paid = self.household.paid_towards = {}
        kept = max(0.0, project_state.get("spent", 0.0))
        if kept > 0.5:
            _paid[k] = _paid.get(k, 0.0) + kept
        return True, ("stopped. The %s denarii already paid stands to your "
                      "credit and comes off the bill if you begin again; the "
                      "hours are gone" % "{:,.0f}".format(kept)
                      if kept > 0.5 else "stopped; nothing had been paid yet")

