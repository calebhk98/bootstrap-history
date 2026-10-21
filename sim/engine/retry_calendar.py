"""How much of a failed attempt's elapsed calendar time the next attempt starts with."""


def retry_calendar_retain(cap, decay, failed_attempts):
    """The share of the calendar floor banked after `failed_attempts` failures: nothing before any, then each failure closes
    the fraction `1 - decay` of the gap to `cap`, so it rises with every failure and never reaches the cap."""
    if failed_attempts <= 0:
        return 0.0
    return cap * (1.0 - decay ** failed_attempts)
