"""The opening words of the census line that reports literacy gains from schooling."""


def census_phrase(year, school_started, generation_years):
    """A generation of schooling is claimed only once the school has run for a generation."""
    if school_started is not None and year - school_started >= generation_years:
        return "a generation of schooling shows in the census"
    return "schooling shows in the census"
