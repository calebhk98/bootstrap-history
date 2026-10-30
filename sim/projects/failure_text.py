"""What a failed attempt says: the three lines (a claimant's, a minor loss, a major one) as functions of the figures."""

FAILED_PREFIX = "FAILED at"
MINOR_MARK = "(minor)"


def claimed_line(name: str, attempts_so_far: int, next_risk: float) -> str:
	"""A bounty's claimant failed: the poster's prize holds and nothing more falls on the poster."""
	return ("%s %s: the claimant's attempt failed. The prize you posted holds "
	        "and they try again (attempt %d, chance of failing %d%%); nothing "
	        "more falls on you."
	        % (FAILED_PREFIX, name, attempts_so_far + 1, round(next_risk * 100)))


def minor_line(name: str, lost_text: str, reset_share: float, attempts_so_far: int, next_risk: float, diagnosis: str) -> str:
	"""A small loss, reported as one compact line."""
	return ("%s %s %s: lost %s, %d%% of the hours to redo; "
	        "attempt %d, next attempt's live chance of failing %d%%."
	        % (FAILED_PREFIX, name, MINOR_MARK, lost_text, round(reset_share * 100), attempts_so_far + 1,
	           round(next_risk * 100)) + (" " + diagnosis if diagnosis else ""))


def major_line(name: str, cause: str, reset_share: float, hours_redone_text: str, lost_text: str, attempts_so_far: int,
               learned: bool, next_risk: float, risk_this_attempt: float, banked_years: float, years_before: float,
               diagnosis: str) -> str:
	"""A failure that cost real money and hours: what failed, what is to do again and what the next attempt faces."""
	return (FAILED_PREFIX + " %s: it did not work. What failed: %s. "
	        "%d%% of the hours "
	        "are to do again (%s of your own) and %s is gone. "
	        "Attempt %d. %s the next attempt's live chance of failing "
	        "(the figure `risk`, `why` and `portfolio` now quote) "
	        "is %d%%, down from the %d%% this attempt "
	        "just faced, and %.1f of the %.1f years already "
	        "spent count toward next time's wait. %s"
	        % (name, cause, round(reset_share * 100), hours_redone_text, lost_text, attempts_so_far + 1,
	           "What went wrong is now understood well enough that" if learned else "Nothing was learned, so",
	           round(next_risk * 100), round(risk_this_attempt * 100), banked_years, years_before, diagnosis))
