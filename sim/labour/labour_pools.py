"""The two aggregate pools the tech tree asks for (`art`, `sch`), rebuilt from the people on the books, and the
outright grants of trained people that institutions make."""
from sim.constants import declare

from sim.workforce.api import rules as workforce_rules

from . import trade_data


class StaffPools:
    def __init__(self, world, book, trades):
        self._world = world
        self.book = book
        self.trades = trades

    def grant_staff(self, scholars=0.0, artisans=0.0):
        """An institution hands you people outright, on completion - the
        school's own professors, the freedmen a patron staffs your workshop
        with. They are people of the scholar and craft trades like any
        others: they go on the staff book, where `resync_pools()` counts
        them, and into the labour core, where the seat's places hire them at
        the year's clearing at the market wage.
        """
        self.book.add_newcomers(trade_data.scholar_trade(), scholars)
        self.book.add_newcomers(trade_data.generic_craft_trade(), artisans)
        self.resync_pools()

    # ---- losses: written to the people on the books, which `resync_pools` counts, and to the places the books keep
    # (`StaffBook.set_employed` moves the standing bid down by the people lost, so the next clearing does not refill the dead)

    def lose_share(self, survival_share):
        """Every trade's hired people, and the slaves and freedmen, fall to the share that survives, fractions kept."""
        workforce = self._world.workforce
        for trade in sorted(workforce.employees):
            self.book.set_employed(trade, workforce_rules.surviving_people(workforce.employees[trade], survival_share))
        workforce.slaves = int(round(workforce_rules.surviving_people(workforce.slaves, survival_share)))
        workforce.freedmen = int(round(workforce_rules.surviving_people(workforce.freedmen, survival_share)))
        self.resync_pools()

    def lose_crew(self, share_by_trade):
        """Each (trade, share) loses that share of the trade's hired people. Answers (trade, had, kept) per trade."""
        lost = []
        for trade, share in share_by_trade:
            have = self.book.employed(trade)
            kept = workforce_rules.surviving_people(have, 1.0 - share)
            self.book.set_employed(trade, kept)
            lost.append((trade, have, kept))
        self.resync_pools()
        return tuple(lost)

    def bleed(self, artisan_floor, artisan_bleed, scholar_floor, scholar_bleed):
        """People the household cannot pay leave: the craft pool falls by `artisan_bleed` (not below the floor), the scholars
        by `scholar_bleed` (not below theirs)."""
        workforce = self._world.workforce
        self.book.set_employed(trade_data.scholar_trade(),
                               workforce_rules.count_after_bleed(self.book.employed(trade_data.scholar_trade()), scholar_floor, scholar_bleed))
        self._scale_craft_people(workforce_rules.count_after_bleed(workforce.artisans, artisan_floor, artisan_bleed) / workforce.artisans
                                 if workforce.artisans > 0 else 1.0)
        self.resync_pools()

    def disperse_dependants(self, artisan_floor, artisan_retention):
        """The freedmen leave the household and the craft pool keeps the share `artisan_retention` of itself (not below the floor)."""
        workforce = self._world.workforce
        before = workforce.artisans
        workforce.freedmen = 0
        self._scale_craft_people(workforce_rules.count_after_bleed(before, artisan_floor, 1.0 - artisan_retention) / before if before > 0 else 1.0)
        self.resync_pools()

    def _scale_craft_people(self, ratio):
        """Hired craft people and slaves fall to `ratio` of what they were; the craft pool follows by `resync_pools`."""
        workforce = self._world.workforce
        for trade in sorted(workforce.employees):
            if self.trades.is_craft_trade(trade):
                self.book.set_employed(trade, workforce.employees[trade] * ratio)
        workforce.slaves = int(round(workforce.slaves * ratio))

    FREEDMAN_ARTISAN_PRODUCTIVITY = declare(
        "FREEDMAN_ARTISAN_PRODUCTIVITY", 1.0, kind="temporary_heuristic",
        unit="fraction of a full worker's artisan capacity", source=None,
        confidence="D",
        why="A trained, freed person counts as a full worker. Paired with "
            "TRAINED_SLAVE_ARTISAN_PRODUCTIVITY below: the gap between the "
            "two is this model's stand-in for the real productivity cost "
            "of coercion, which nothing here derives from an actual "
            "measured difference in enslaved versus free labour output.")

    TRAINED_SLAVE_ARTISAN_PRODUCTIVITY = declare(
        "TRAINED_SLAVE_ARTISAN_PRODUCTIVITY", 0.7, kind="temporary_heuristic",
        unit="fraction of a full worker's artisan capacity", source=None,
        confidence="D",
        why="A trained person still held as a slave is worth less than a "
            "freedman doing the same work - coerced labour is real but "
            "worse, which is also the whole argument for manumission "
            "being strictly better on these numbers (see buy_slaves' own "
            "docstring). The specific 0.7 is tuned game balance, not a "
            "measured efficiency gap.")

    def resync_pools(self):
        """Recompute the two aggregate pools the tech tree asks for (`art` and `sch`: trained people who understand your
        methods) from the people on the books. Only the `scholar` trade counts as a scholar; scribes, chemists, engineers and
        merchants share its market family but are not natural philosophers. Staff an institution granted outright are on the
        books as staff of their trade (see grant_staff) and count with the rest."""
        workforce = self._world.workforce
        craft = sum(count for trade, count in self.book.employed_by_trade().items() if self.trades.is_craft_trade(trade))
        schol = self.book.employed(trade_data.scholar_trade())
        # Anyone still in the training queue is excluded from the count; once a row matures its capacity is part of `owned`.
        # buy_slaves stores WORKER_EQUIVALENT_UNTRAINED of a worker per person
        # bought, so that is the divisor that recovers the headcount still
        # learning.
        learning = sum(row[0] for row in workforce.training
                       if len(row) <= 2) / self.WORKER_EQUIVALENT_UNTRAINED
        owned = max(0.0, workforce.freedmen + workforce.slaves - learning)
        # Split what is left in the same proportion as what is held.
        held = workforce.freedmen + workforce.slaves
        if held > 0:
            free_share = workforce.freedmen / held
        else:
            free_share = 0.0
        workforce.artisans = (craft + owned * free_share * self.FREEDMAN_ARTISAN_PRODUCTIVITY
                         + owned * (1.0 - free_share) * self.TRAINED_SLAVE_ARTISAN_PRODUCTIVITY)
        workforce.scholars = schol

    WORKER_EQUIVALENT_UNTRAINED = declare(
        "WORKER_EQUIVALENT_UNTRAINED", 0.55, kind="temporary_heuristic",
        unit="fraction of a full worker's artisan capacity", source=None,
        confidence="D",
        why="What fraction of a full worker a person newly bought is "
            "assumed to represent, entered into the training queue and "
            "matured over TRAINING_YEARS. Not a measured productivity "
            "ratio; picked so the training lag is real (see buy_slaves' "
            "own docstring on the exploit this closed) without being all "
            "or nothing.")
