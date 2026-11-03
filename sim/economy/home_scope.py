"""Which tiles and cohorts the home country's state and the unqualified questions about 'the economy' are about."""


def has_partners(setup) -> bool:
    """Whether the economy holds more than the home country."""
    return len(setup.countries()) > 1


def on_home_tile(setup, tile: str) -> bool:
    """Whether the home country holds `tile` (always, with one country): the home state taxes and hires only there."""
    return not has_partners(setup) or setup.country_of(tile) == setup.civ_id


def home_cohorts(setup, record) -> list:
    """The cohorts living on home tiles."""
    return [cohort for cohort in record.cohorts.values() if on_home_tile(setup, cohort.tile)]
