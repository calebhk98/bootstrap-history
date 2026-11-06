"""The actors' money: one account each in a double-entry book, and their debts as claims against it.

A purse is never negative. Lending goes through one pool, a counterparty in the book that owes its depositors and
is owed by its borrowers. An actor that pays more than its purse holds first takes back its deposit, then draws the
shortfall on its facility: the pool puts the money into its purse and holds one claim for the principal, whatever
the number of lenders behind it. Money that comes in repays the claim first. Interest a borrower pays stays in the
pool until the year's settlement shares it among the depositors in proportion to their deposits; a default's loss
falls on the pool and through it on every deposit in proportion, once. So an actor's net position (purse and
deposit less debt) moves by exactly what the transfers move, which is what `net` reports and `Actor.money` shows.

Depositors are the accounts that offered funds (`set_offers`: a state's reserve, a firm's spare cash) and the
economy's own lenders (cohorts' savings, banks, funds), who deposit what the pool lacks, cheapest ask first and no
dearer than the draw's rate. Their money crosses `edge:exchange` at the coin per economy unit, and returns the same way
with its interest. A draw beyond what the borrower may be lent, or beyond what lenders can supply, is refused with
`InsufficientFunds` and nothing moves: no money appears from nowhere.
"""
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from sim.book import EDGE_EXCHANGE, ROUNDING_SHARE, Book, InsufficientFunds, Transfer, is_edge
from sim.contracts import DEPOSIT, FACILITY, Contracts
from sim.rekey import rekey

from .bonds import BondBook
from .named_lenders import NamedLenders

COIN = "engine_coin"                          # the currency of the actors' money in the shared book (the engine counts in this coin)
EDGE_OUTSIDE = "edge:outside the book"        # the other side of a posting whose payer or payee keeps no account here
FACILITY_DRAW = "facility draw"
FACILITY_REPAYMENT = "facility repayment"
BOND_SOLD = "bond sold"
BOND_REDEEMED = "bond redeemed"
INTEREST_PAID = "interest paid"                 # a borrower's interest to its lenders, as the book labels it
DEPOSIT_LOST = "deposit lost in a default"   # a depositor's share of the pool's loss, as the lender's books label it
POOL = "pool:credit"                          # the one lending counterparty: depositors' funds in, borrowers' facilities out
DEPOSIT_PLACED = "deposit placed"
DEPOSIT_TAKEN_BACK = "deposit taken back"
DEPOSIT_INTEREST = "interest on deposit"
DEBT_FLOOR = 1e-9                             # a debt below this is rounding residue


class Purses:
    """The accounts of the actors, and the claims against them."""

    def __init__(self, book: Any = None, contracts: Optional[Contracts] = None) -> None:
        self.book = book if book is not None else Book()
        # the debts: each draw on an actor's facility is a contract in the registry the economy shares
        self.contracts: Contracts = contracts if contracts is not None else Contracts()
        # depositor -> funds it offers this year
        self.offers: Dict[str, float] = {}
        # the economy's lenders that have deposited in the pool, and the unit and coin per unit their money crosses at
        self.unit_lenders: Set[str] = set()
        # coin each economy lender has put in the pool since the last settlement (what its listed offer no longer covers)
        self.placed: Dict[str, float] = {}
        self.unit: Optional[str] = None
        self.coin_per_unit: float = 1.0
        # never saved, set by the actors module: what an account may be lent of a draw (limit), and the economy's lenders
        # for a draw by an account: (unit, coin per unit, [(lender, offered, balance, ask)] cheapest first) or None
        self.limit: Optional[Callable[[str, float], float]] = None
        self.lenders_for: Optional[Callable[[str, float], Optional[Tuple[str, float, List[Tuple[str, float, float, float]]]]]] = None
        self._limits_off = False
        # interest borrowers have paid the pool since the last settlement, owed to the depositors
        self.interest_pending: float = 0.0
        # told (account, signed amount, label) when a lender's net position moves by a draw or a repayment
        self.observer: Optional[Callable[[str, float, str], None]] = None
        # told (lender, signed amount in the economy's unit, label) when an economy lender's deposit earns interest or loses to a default
        # (never saved, set by the module that owns the economy)
        self.unit_observer: Optional[Callable[[str, float, str], None]] = None
        # the borrowers (a state) that name their lenders, and who lent each what (named_lenders.py)
        self.named_lenders = NamedLenders()
        # the issuers (a state) that raise cash by bonds, the terms they sell at, and the bonds outstanding (bonds.py)
        self.bonds = BondBook()

    # ---- reads ------------------------------------------------------------------------------
    def purse(self, account: str) -> float:
        """What the account holds; an actor's is never below zero."""
        return self.book.balance(account, COIN)

    def has_account(self, account: str) -> bool:
        return self.book.knows(account)

    def debt(self, account: str) -> float:
        """What the account owes, on every kind of contract and at face on its bonds, in the actors' coin."""
        return self.contracts.debt(account, COIN) + self.bonds.debt(account)

    def deposit(self, account: str) -> float:
        """What the pool owes the account."""
        return self.contracts.deposit_of(account)

    def net(self, account: str) -> float:
        """The purse and the deposit less the debt: what the actor is worth in cash."""
        return self.purse(account) + self.deposit(account) - self.debt(account)

    def lent(self, lender: Optional[str] = None) -> float:
        """What the lender has out (its deposit and its loans); every lender's loans when none is named."""
        if lender is not None:
            return self.contracts.exposure(lender, COIN)
        return (sum(contract.principal for contract in self.contracts.all() if contract.kind != DEPOSIT and contract.currency == COIN)
                + self.bonds.total_paid())

    def drawable(self, account: str, shortfall: float, taking: float = 0.0) -> float:
        """The most of a draw of `shortfall` the account is lent now: what its borrower may be lent (`limit`), and what the pool
        holds beyond the interest it owes plus what the economy's lenders can supply for a draw of that size (`_lender_capacities`,
        the same plan `_draw` takes funds by), so a draw this approves is never refused for want of funds. `taking` is a deposit the
        account takes back first, which the same funds must pay."""
        if is_edge(account):
            return max(0.0, shortfall)   # an edge is the other side of a posting: it is never short
        if shortfall <= DEBT_FLOOR:
            return 0.0
        allowed = shortfall if self.limit is None or self._limits_off else max(0.0, min(shortfall, self.limit(account, shortfall)))
        free = max(0.0, self.purse(POOL) - self.interest_pending)
        if allowed - free + taking <= DEBT_FLOOR:
            return allowed
        capacities = self._lender_capacities(account, allowed)
        supply = 0.0 if capacities is None else capacities[1] * sum(units for _lender, units in capacities[2])
        return max(0.0, min(allowed, free + supply - taking))

    def takeable(self, account: str) -> float:
        """What the account can take back of its deposit now: the deposit, as far as the pool holds it free or the lenders refill it."""
        deposit = self.deposit(account)
        if deposit <= DEBT_FLOOR:
            return 0.0
        free = max(0.0, self.purse(POOL) - self.interest_pending)
        if deposit - free <= DEBT_FLOOR:
            return deposit
        capacities = self._lender_capacities("", deposit)
        refill = 0.0 if capacities is None else capacities[1] * sum(units for _lender, units in capacities[2])
        return min(deposit, free + refill)

    def payable(self, account: str, amount: float) -> float:
        """The most of `amount` the account can pay now: its purse, its deposit as far as it can take it back (`takeable`) and what
        it is lent beyond."""
        if is_edge(account) or amount <= DEBT_FLOOR:
            return max(0.0, amount)
        purse = self.purse(account)
        taking = min(self.takeable(account), max(0.0, amount - purse))
        held = purse + taking
        if held >= amount * (1.0 - ROUNDING_SHARE):
            return amount
        return min(amount, held + self.drawable(account, amount - held, taking))

    def set_offers(self, offers: Dict[str, float]) -> None:
        """The funds each lender offers from now on: a lender's deposit in the pool moves to what it offers (from its
        purse, or back to it)."""
        self.offers = {lender: amount for lender, amount in offers.items() if amount > 0.0}
        for account in sorted(set(self.offers) | set(self.contracts.deposits)):
            if is_edge(account) or account in self.unit_lenders:
                continue
            held = self.deposit(account)
            target = self.offers.get(account, 0.0)
            if target > held:
                self._place(account, min(target - held, self.purse(account)))
            elif held > target:
                self._take_back(account, held - target)

    # ---- postings ---------------------------------------------------------------------------
    def transfer(self, payer: str, payee: str, amount: float, purpose: str) -> None:
        """Move `amount`; a payer short of it draws the rest on its facility first, and a payee in debt repays. The draw
        and the posting are one step: a posting the book refuses undoes what the draw did before it raises."""
        if not amount > DEBT_FLOOR:
            return   # rounding residue: the books carry noise larger than this
        undo = self._cover(payer, amount)
        try:
            self.book.transfer(Transfer(payer, payee, COIN, amount, purpose))
        except InsufficientFunds:
            for reverse in reversed(undo):
                reverse()
            raise
        if not is_edge(payee):
            self._repay(payee)

    def reverse(self, payee: str, payer: str, amount: float, purpose: str) -> None:
        """Undo an earlier payment of `amount` from `payer` to `payee`: one posting back. The payee draws what it
        has since spent; no facility of the payer is repaid by it, and a refused posting undoes the draw."""
        if not amount > DEBT_FLOOR:
            return
        undo = self._cover(payee, amount)
        try:
            self.book.transfer(Transfer(payee, payer, COIN, amount, purpose))
        except InsufficientFunds:
            for reverse in reversed(undo):
                reverse()
            raise

    def cover(self, payer: str, amount: float) -> Callable[[], None]:
        """Make the payer's purse hold `amount`: it takes back its deposit first and draws the rest on its facility,
        both in one go (an account that will make several payments covers their sum first). Answers the call that gives
        back what this did, for a caller whose payments then fail before any money has moved."""
        undo = self._cover(payer, amount)

        def give_back() -> None:
            for reverse in reversed(undo):
                reverse()
        return give_back

    def _cover(self, payer: str, amount: float) -> List[Callable[[], None]]:
        """`cover`, answering the steps that undo what it did, in the order it did them."""
        undo: List[Callable[[], None]] = []
        if not is_edge(payer) and amount > DEBT_FLOOR:
            held = self.purse(payer)
            if held < amount * (1.0 - ROUNDING_SHARE):   # a purse short only by float dust pays as it is
                beyond = amount - held - self.takeable(payer)   # what no deposit it can take back covers: refused now, before anything moves
                if beyond > DEBT_FLOOR and not self._limits_off and self.drawable(payer, beyond) < beyond * (1.0 - ROUNDING_SHARE):
                    raise InsufficientFunds("%s may be lent %.2f of the %.2f it lacks" % (payer, self.drawable(payer, beyond), beyond))
                taken = self._take_back(payer, min(amount - held, self.deposit(payer)))
                if taken > DEBT_FLOOR:
                    undo.append(lambda: self._place(payer, taken))
                held = self.purse(payer)
                if held < amount * (1.0 - ROUNDING_SHARE):
                    try:
                        undo.append(self._draw(payer, amount - held))
                    except InsufficientFunds:
                        for reverse in reversed(undo):   # a refused draw leaves the deposit where it was
                            reverse()
                        raise
        return undo

    def pay_interest(self, borrower: str, owed: float, purpose: str = INTEREST_PAID) -> Dict[str, float]:
        """Pay `owed` to the pool its facility is drawn on; it reaches the depositors at the next settlement."""
        if owed <= 0.0 or (sum(self.contracts.facility_of(borrower).values()) <= 0.0 and self.bonds.debt(borrower) <= 0.0):
            return {}
        self.transfer(borrower, POOL, owed, purpose)
        self.interest_pending += owed
        return {POOL: owed}

    def pay_arrears(self, borrower: str, owed: float) -> float:
        """Pay interest that went unpaid in earlier years from the purse, taking the deposit back first when the purse is short;
        like any interest it waits in the pool. Never borrows to pay; answers what reached the pool."""
        short = owed - self.purse(borrower)
        if short > DEBT_FLOOR:
            self._take_back(borrower, min(short, self.deposit(borrower)))
        paid = min(owed, self.purse(borrower))
        if paid > DEBT_FLOOR:
            self.book.transfer(Transfer(borrower, POOL, COIN, paid, INTEREST_PAID))
            self.interest_pending += paid
            return paid
        return 0.0

    def settle_interest(self) -> Dict[str, float]:
        """Share the interest the pool received among its depositors in proportion to their deposits, never more
        than the pool holds (the deposit rate is whatever that comes to; interest lost in a default is not paid),
        then give the economy's lenders back what the pool holds beyond its lending; what each depositor received (coin)."""
        paid: Dict[str, float] = {}
        shares = {depositor: contract.principal for depositor, contract in sorted(self.contracts.deposits.items()) if depositor != EDGE_OUTSIDE}   # the account outside the book earns nothing
        total = sum(shares.values())
        owed, self.interest_pending = self.interest_pending, 0.0
        available = min(owed, max(0.0, self.purse(POOL)))
        if available > DEBT_FLOOR and total > 0.0:
            for depositor, principal in shares.items():
                part = min(available * principal / total, max(0.0, self.purse(POOL)))
                if part > DEBT_FLOOR:
                    self._pay_depositor(depositor, part, DEPOSIT_INTEREST)
                    paid[depositor] = part
                    if depositor in self.unit_lenders:   # an actor's interest is entered by the module that shares it out
                        self._tell(depositor, part, DEPOSIT_INTEREST)
            for depositor in paid:
                if not is_edge(depositor) and depositor not in self.unit_lenders:
                    self._repay(depositor)
        for lender in sorted(self.unit_lenders) + [EDGE_OUTSIDE]:
            back = min(self.deposit(lender), self.purse(POOL))
            if back > DEBT_FLOOR:
                self._pay_depositor(lender, back, DEPOSIT_TAKEN_BACK)
                self.contracts.withdraw(lender, back, DEBT_FLOOR)
            if self.deposit(lender) <= DEBT_FLOOR:
                self.unit_lenders.discard(lender)
        self.placed = {}
        return paid

    def _pay_depositor(self, depositor: str, coin: float, purpose: str) -> None:
        """The pool pays `coin` to a depositor: an economy lender is paid in the economy's unit across the exchange."""
        if depositor in self.unit_lenders and self.unit is not None:
            self.book.transfer(Transfer(POOL, EDGE_EXCHANGE, COIN, coin, purpose))
            self.book.transfer(Transfer(EDGE_EXCHANGE, depositor, self.unit, coin / self.coin_per_unit, purpose))
        else:
            self.book.transfer(Transfer(POOL, depositor, COIN, coin, purpose))

    def set_net(self, account: str, value: float, purpose: str) -> None:
        """Bring the account's net position to `value`, the other side being the account outside the book."""
        difference = value - self.net(account)
        self._limits_off = True   # bookkeeping reset, not a purchase: a draw it makes is not held to the borrower's limit
        try:
            if difference > 0.0:
                self.transfer(EDGE_OUTSIDE, account, difference, purpose)
            elif difference < 0.0:
                self.transfer(account, EDGE_OUTSIDE, -difference, purpose)
        finally:
            self._limits_off = False

    def repay_from_purse(self, borrower: str) -> None:
        """The borrower takes back its deposit and pays the pool what its purse holds."""
        self._take_back(borrower, self.deposit(borrower))
        self._repay(borrower)

    def write_off(self, borrower: str, amount: Optional[float] = None) -> Dict[str, float]:
        """The lenders drop the claim against the borrower and the pool bears the loss, every deposit losing in proportion (the
        cash was booked as an outlay when it left and no repayment follows); the loss. The whole claim when no `amount` is named,
        else that much of its facility: one rule for a closing firm and a household settling."""
        if amount is None:
            lost = sum(contract.principal for contract in self.contracts.default(borrower, FACILITY)) + self.bonds.write_off(borrower)
        else:
            lost = self.contracts.forgive_facility(borrower, amount)
        if self.named_lenders.names(borrower):
            deposits = {depositor: contract.principal for depositor, contract in self.contracts.deposits.items()}
            for depositor, part in self.named_lenders.settle_default(borrower, lost, deposits).items():
                self.contracts.withdraw(depositor, part, DEBT_FLOOR)
                self._tell(depositor, -part, DEPOSIT_LOST)
                lost -= part
        total = self.contracts.total_deposits()
        if lost > 0.0 and total > 0.0:
            factor = max(0.0, (total - lost) / total)
            for depositor, contract in sorted(self.contracts.deposits.items()):
                self._tell(depositor, -contract.principal * (1.0 - factor), DEPOSIT_LOST)
            self.contracts.scale_deposits(factor)
        return {POOL: lost} if lost > 0.0 else {}

    def _draw(self, borrower: str, shortfall: float) -> Callable[[], None]:
        """The borrower draws `shortfall`; answers the step that gives it back. Raises `InsufficientFunds`, with nothing moved,
        when the borrower may not be lent so much (`limit`) or the lenders cannot supply it."""
        if not self._limits_off:
            allowed = self.drawable(borrower, shortfall)
            if allowed < shortfall * (1.0 - ROUNDING_SHARE):
                raise InsufficientFunds("%s may be lent %.2f of the %.2f it lacks" % (borrower, allowed, shortfall))
        self._fund_pool(shortfall, borrower)
        deposits = {depositor: contract.principal for depositor, contract in self.contracts.deposits.items()}
        if self.bonds.issues(borrower):
            # the market buys a bond for the shortfall: the borrower owes its face, the depositors paid the price
            self.book.transfer(Transfer(POOL, borrower, COIN, shortfall, BOND_SOLD))
            bond = self.bonds.sell(borrower, shortfall)
        else:
            self.book.transfer(Transfer(POOL, borrower, COIN, shortfall, FACILITY_DRAW))
            self.contracts.draw(borrower, POOL, COIN, shortfall)
            bond = None
        named = self.named_lenders.names(borrower)
        if named:
            self.named_lenders.drew(borrower, shortfall, deposits)

        def give_back() -> None:
            if bond is not None:
                self.book.transfer(Transfer(borrower, POOL, COIN, shortfall, BOND_REDEEMED))
                self.bonds.held[borrower].remove(bond)
                if not self.bonds.held[borrower]:
                    del self.bonds.held[borrower]
            else:
                self.book.transfer(Transfer(borrower, POOL, COIN, shortfall, FACILITY_REPAYMENT))
                self.contracts.repay_facility(borrower, POOL, shortfall)
                self.contracts.tidy_facility(borrower, DEBT_FLOOR)
            total = sum(deposits.values())
            if named and total > 0.0:   # `drew` recorded nothing against an empty pool
                for lender, deposit in deposits.items():
                    self.named_lenders.held[borrower][lender] -= shortfall * deposit / total
        return give_back

    def _fund_pool(self, amount: float, borrower: Optional[str] = None, draw: Optional[float] = None) -> None:
        """The pool can pay out `amount` and still hold the interest it owes its depositors: what its depositors' funds
        leave short is lent to it by the economy's lenders, cheapest ask first (`_lender_plan`), or the draw is refused.
        `draw` is the size of the draw the funds are for (it sets the rate lenders are asked to meet); `amount` when none."""
        lacking = amount - (self.purse(POOL) - self.interest_pending)
        if lacking <= DEBT_FLOOR:
            return
        plan = None if self._limits_off else self._lender_plan(lacking, borrower, amount if draw is None else draw)
        if plan is None and self._limits_off:
            # a bookkeeping reset (`set_net`) that sets an actor's net position below zero: the account outside the book
            # stands behind the debt it writes, and is paid back like a lender
            self.book.transfer(Transfer(EDGE_OUTSIDE, POOL, COIN, lacking, DEPOSIT_PLACED))
            self.contracts.deposit(EDGE_OUTSIDE, POOL, COIN, lacking)
            return
        if plan is None:
            raise InsufficientFunds("lenders cannot supply the %.2f the pool lacks" % lacking)
        unit, per_unit, parts = plan
        self.unit, self.coin_per_unit = unit, per_unit
        for lender, units in parts:
            coin = units * per_unit
            self.book.transfer(Transfer(lender, EDGE_EXCHANGE, unit, units, DEPOSIT_PLACED))
            self.book.transfer(Transfer(EDGE_EXCHANGE, POOL, COIN, coin, DEPOSIT_PLACED))
            self.contracts.deposit(lender, POOL, COIN, coin, unit_value=1.0 / per_unit)
            self.unit_lenders.add(lender)
            self.placed[lender] = self.placed.get(lender, 0.0) + coin

    def _lender_capacities(self, account: str, draw: float) -> Optional[Tuple[str, float, List[Tuple[str, float]]]]:
        """(unit, coin per unit, [(lender, units it can still put in the pool)]) cheapest ask first, for a draw of `draw` by the
        account: each lender gives at most what it offered beyond what it has put in the pool since the last settlement (the
        deposits of earlier years were out of its account when it made the offer) and what its account holds.
        None before lenders have met. The one reading of the lenders the gate (`drawable`) and the plan (`_lender_plan`) share."""
        offer = None if self.lenders_for is None else self.lenders_for(account, draw)
        if offer is None:
            return None
        unit, per_unit, lenders = offer
        return unit, per_unit, [(lender, max(0.0, min(offered - self.placed.get(lender, 0.0) / per_unit, balance)))
                                for lender, offered, balance, _ask in lenders]

    def _lender_plan(self, lacking: float, borrower: Optional[str], draw: float) -> Optional[Tuple[str, float, List[Tuple[str, float]]]]:
        """(unit, coin per unit, [(lender, units)]) covering `lacking` coin from the cheapest ask up out of what each can still
        put in (`_lender_capacities`, for a draw of `draw`); None when they fall short."""
        capacities = self._lender_capacities(borrower if borrower is not None else "", draw)
        if capacities is None:
            return None
        unit, per_unit, lenders = capacities
        remaining = lacking
        parts: List[Tuple[str, float]] = []
        for lender, available in lenders:
            units = min(available, remaining / per_unit)
            if units * per_unit > DEBT_FLOOR:
                parts.append((lender, units))
                remaining -= units * per_unit
            if remaining <= draw * ROUNDING_SHARE:
                return unit, per_unit, parts
        return None

    def _place(self, account: str, amount: float) -> None:
        if amount > DEBT_FLOOR:
            self.book.transfer(Transfer(account, POOL, COIN, amount, DEPOSIT_PLACED))
            self.contracts.deposit(account, POOL, COIN, amount)

    def _take_back(self, account: str, amount: float) -> float:
        """The account takes back up to `amount` of its deposit, as far as the pool holds it or the lenders refill it;
        answers what it took."""
        amount = min(amount, self.deposit(account))
        if amount <= DEBT_FLOOR:
            return 0.0
        try:
            self._fund_pool(amount)
        except InsufficientFunds:
            # the lenders offered cannot refill it all: what they can refill and what the pool holds free is taken, the rest stays deposited
            capacities = self._lender_capacities("", amount)
            refill = 0.0 if capacities is None else capacities[1] * sum(units for _lender, units in capacities[2])
            free = max(0.0, self.purse(POOL) - self.interest_pending)
            if refill > DEBT_FLOOR:
                self._fund_pool(free + refill)
            amount = min(amount, free + refill)
            if amount <= DEBT_FLOOR:
                return 0.0
        self._pay_depositor(account, amount, DEPOSIT_TAKEN_BACK)
        self.contracts.withdraw(account, amount, DEBT_FLOOR)
        return amount

    def redeem_bonds(self, issuer: str) -> float:
        """A year passes for the issuer's bonds: those at their term fall due and are paid off at face, the issuer drawing
        the cash (on a new bond when its purse falls short); the face repaid. A payment refused leaves the due bonds on the
        book as debt, due again next year (the issuer is in arrears). Call once a year."""
        due = self.bonds.age(issuer)
        if due <= DEBT_FLOOR:
            return 0.0
        try:
            self.transfer(issuer, POOL, due, BOND_REDEEMED)
        except InsufficientFunds:
            return 0.0
        self.interest_pending += self.bonds.retire_due(issuer)   # the discount is the depositors' return
        if self.named_lenders.names(issuer):
            owed = self.debt(issuer) + due
            self.named_lenders.repaid(issuer, due / owed if owed > 0.0 else 1.0)
        return due

    def _repay(self, borrower: str) -> None:
        held = self.contracts.facilities.get(borrower)
        if not held:
            return
        purse = self.purse(borrower)
        if purse > DEBT_FLOOR:   # a purse of rounding residue repays nothing
            debt = sum([contract.principal for contract in held.values()])
            repaid = min(debt, purse)
            if repaid > DEBT_FLOOR:
                for lender in sorted(held):
                    share = repaid * held[lender].principal / debt
                    if share <= DEBT_FLOOR:   # a lender owed so little takes no part
                        continue
                    part = min(share, max(0.0, purse))   # shares sum to the purse only to rounding
                    if part > DEBT_FLOOR:
                        self.book.transfer(Transfer(borrower, lender, COIN, part, FACILITY_REPAYMENT))
                        purse -= part   # what the book now holds for the borrower
                        self.contracts.repay_facility(borrower, lender, part)
                if self.named_lenders.names(borrower):
                    self.named_lenders.repaid(borrower, repaid / debt)
        self.contracts.tidy_facility(borrower, DEBT_FLOOR)

    def _tell(self, account: str, signed: float, label: str) -> None:
        """A depositor's wealth moved by interest or a default's loss: it is told, so the books it keeps account for it. An
        actor is told in coin (`observer`); an economy lender in its unit (`unit_observer`)."""
        if is_edge(account) or account == POOL:
            return
        if account in self.unit_lenders:
            if self.unit_observer is not None:
                self.unit_observer(account, signed / self.coin_per_unit, label)
        elif self.observer is not None:
            self.observer(account, signed, label)

    def adopt_book(self, book: Any, contracts: Optional[Contracts] = None) -> None:
        """Keep the accounts in `book` and the contracts in `contracts` from now on (the economy's own, so purses
        and markets share one book and one registry); what this book holds in the actors' currency, and the
        facilities drawn so far, move over."""
        if contracts is not None and contracts is not self.contracts:
            contracts.adopt(self.contracts)
            self.contracts = contracts
        if book is self.book:
            return
        book.absorb(Book.from_record(self.book.to_record(only=(COIN,))))
        self.book = book

    def rename_account(self, old: str, new: str) -> None:
        """`old` becomes `new` with all it holds and owes: its purse and goods, its deposit, its facility and term
        loans as borrower and as lender, its bonds, its named lenders and its offer of funds. Nothing is paid, so
        every total in the book and the registry is what it was."""
        self.book.rename_agent(old, new)
        self.contracts.rename(old, new)
        if old in self.unit_lenders:
            self.unit_lenders.discard(old)
            self.unit_lenders.add(new)
        rekey(self.placed, old, new)
        for held in (self.bonds.terms, self.bonds.held, self.named_lenders.borrowers, self.named_lenders.held,
                     self.named_lenders.written_down, self.offers):
            rekey(held, old, new)

    # ---- the save file ----------------------------------------------------------------------
    def to_canon_dict(self) -> Dict[str, Any]:
        return {"book": self.book.to_record(only=(COIN,)),
                "facilities": self.contracts.to_records(facilities=True),
                "offers": dict(sorted(self.offers.items())), "interest_pending": self.interest_pending,
                "unit_lenders": sorted(self.unit_lenders), "placed": dict(sorted(self.placed.items())), "unit": self.unit, "coin_per_unit": self.coin_per_unit,
                "named_lenders": self.named_lenders.to_canon_dict(), "bonds": self.bonds.to_canon_dict()}

    @classmethod
    def from_record(cls, record: Dict[str, Any]) -> "Purses":
        purses = cls(Book.from_record(record["book"]))
        purses.contracts.load_records(record["facilities"])
        purses.offers = dict(record.get("offers") or {})
        purses.interest_pending = float(record.get("interest_pending", 0.0))
        purses.unit_lenders = set(record.get("unit_lenders") or ())
        purses.placed = dict(record.get("placed") or {})
        purses.unit = record.get("unit")
        purses.coin_per_unit = float(record.get("coin_per_unit", 1.0))
        purses.named_lenders = NamedLenders.from_record(record.get("named_lenders") or {})
        purses.bonds = BondBook.from_record(record.get("bonds") or {})
        return purses
