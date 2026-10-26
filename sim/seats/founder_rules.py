"""The founder's death and what follows it: the years a founder has left, and the programme that dissolves when no deputies
can carry the work on."""
# the years of dissolution at which the player is reminded
DISSOLUTION_WARNING_YEARS = (3, 6, 9, 11)


def years_left(life_left: float, extension_running: bool, extension_years: float) -> float:
    """What a living founder has left after one more year: a year less, plus what a running life-extension technique gives."""
    left = life_left - 1
    if extension_running:
        left += extension_years
    return left


def has_died(life_left: float) -> bool:
    return life_left <= 0


def dissolves(alive: bool, deputies_carry_the_work: bool) -> bool:
    """A programme with no director is not paused, it is dissolving: the founder is dead and the deputies cannot carry on."""
    return not alive and not deputies_carry_the_work


def forgets_this_year(stalled: int, years_before_forgetting: int) -> bool:
    return stalled >= years_before_forgetting


def forgotten_count(losable: int, divisor: int) -> int:
    """How many of the losable nodes a dissolving year takes: a fraction of them, never fewer than one."""
    return max(1, losable // divisor)


def warns(stalled: int) -> bool:
    return stalled in DISSOLUTION_WARNING_YEARS


def run_ends(stalled: int, years_until_end: int) -> bool:
    return stalled >= years_until_end


def deputy_hours_sentence(deputies: float, hours: float) -> str:
    if deputies <= 0:
        return "You trained no deputy to take over."
    return "Your deputies carry about %d hours a year, which is not enough to take over." % round(hours)


def deputy_consequence(carry: bool, deputies: float, hours: float) -> str:
    if carry:
        return ("Your %.1f deputies direct the work in your name and the programme goes on without you." % deputies)
    return (deputy_hours_sentence(deputies, hours) + " Nothing that needs your hours can be begun again, and what you built "
            "will be forgotten over the next twelve years unless deputies grow to carry the work.")


def what_survived(any_dispersed: bool, built: int) -> str:
    if any_dispersed:
        return "the school dispersed, but its codices survive in other hands (%d works of yours with them)" % built
    return "the school dispersed and the work was forgotten"


def death_line(age: int, consequence: str) -> str:
    return "THE FOUNDER DIES, aged about %d. %s" % (age, consequence)


def dissolving_line(stalled: int, hours_sentence: str) -> str:
    return ("THE PROGRAMME IS DISSOLVING: %d year(s) since the founder died. %s What you built is being forgotten. "
            "The run ends at twelve." % (stalled, hours_sentence))


def dissolution_end(what_survived_words: str) -> str:
    return "the founder died without training successors; " + what_survived_words


def run_ends_line(reason: str) -> str:
    return "RUN ENDS: " + reason
