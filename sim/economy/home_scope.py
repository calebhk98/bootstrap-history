"""Which tiles and cohorts the home country's state and the unqualified questions about 'the economy' are about."""

_LAST_ANSWER = []      # [setup, has_partners] for the setup last asked about; a setup is frozen, so the answer holds


def has_partners(setup) -> bool:
    """Whether the economy holds more than the home country. Asked once per cohort and producer a year, while
    `countries()` scans every tile, so the last setup's answer is kept (held by reference, never by `id`)."""
    if _LAST_ANSWER and _LAST_ANSWER[0] is setup:
        return _LAST_ANSWER[1]
    answer = len(setup.countries()) > 1
    _LAST_ANSWER[:] = [setup, answer]
    return answer


def on_home_tile(setup, tile: str) -> bool:
    """Whether the home country holds `tile` (always, with one country): the home state taxes and hires only there."""
    return not has_partners(setup) or setup.country_of(tile) == setup.civ_id


def home_cohorts(setup, record) -> list:
    """The cohorts living on home tiles."""
    return [cohort for cohort in record.cohorts.values() if on_home_tile(setup, cohort.tile)]
