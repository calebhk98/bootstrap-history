"""What the labour package reads of the game's clock, the acting seat's standing and the player's units: two reader groups, each a
plain class holding the module's `needs` (world_reads.py has the rest)."""


class GameReads:
    """The year, the standing policy switches and the player's money and number units."""

    def __init__(self, needs):
        self._needs = needs

    @property
    def year(self):
        return self._needs.year()

    @property
    def policy(self):
        """The acting seat's standing policy switches (read here, never written)."""
        return self._needs.founder()["policy"]

    def money_text(self, amount, grouped=False, short=False):
        """A sum in the civilisation's coin as the player's chosen unit writes it."""
        return self._needs.money_text(amount, grouped, short)

    def plain_number(self, value, digits=0):
        """A count, a number of people or of hours."""
        return self._needs.plain_number(value, digits)


class StandingReads:
    """The founder's life and the bondage the acting seat is under."""

    def __init__(self, needs):
        self._needs = needs

    @property
    def founder_alive(self):
        return self._needs.founder()["alive"]

    @property
    def bondage_years_left(self):
        return self._needs.debt_status()["bondage_years_left"]
