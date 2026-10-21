"""The soonest a project can finish: the longer of its calendar floor and its payment schedule."""


def calendar_floor_years(nominal_years, reputation, rebuild_factor, diffusion_threshold_years, minimum_years,
                         reputation_scale):
    """Calendar years an attempt needs before a completion roll can fire. A diffusion-limited node (nominal years at
    or above the threshold) shrinks as reputation grows, never below `minimum_years`; others keep their nominal years.
    Scaled by what is left to do (`rebuild_factor`)."""
    floor = nominal_years
    if nominal_years >= diffusion_threshold_years:
        floor = max(minimum_years, nominal_years / (1.0 + reputation / reputation_scale))
    return floor * rebuild_factor


def payment_schedule_years(nominal_years, rebuild_factor):
    """Years the bill takes to pay in full: equal yearly instalments over the nominal years, which reputation never shortens."""
    return max(1.0, nominal_years * rebuild_factor)


def earliest_completion_years(calendar_floor, payment_schedule, served_years=None):
    """The soonest a project can finish with no failure: the longer of the floor and the schedule, less what a running
    attempt has already served (`served_years` None when none is running)."""
    earliest = max(calendar_floor, payment_schedule)
    return earliest if served_years is None else max(0.0, earliest - served_years)
