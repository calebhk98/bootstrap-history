"""Whether a patron dies this year."""


def patron_dies(roll, annual_chance, patron_is_mortal, last_death_year, year, cooldown_years):
    """The roll came under the annual chance, a mortal patron is running (`patron_is_mortal` is asked only then),
    and the last death was more than `cooldown_years` ago."""
    return (roll < annual_chance and bool(patron_is_mortal())
            and (last_death_year is None or year - last_death_year > cooldown_years))
