"""Whether the hidden spin-up trims the workforce between its stages and at its end (the rule sets'
`spin_up_trims_workforce`). The trim (workforce_settle.py) cuts each skilled trade to the hours a plan made on last
year's wage wants, for rules under which a glutted trade thins too slowly for the spin-up's years. Where the wage
clears each trade's market the years have moved the people already, and the trim would move them again."""


def trims() -> bool:
    """The workforce is trimmed to the hours employers plan to want."""
    return True


def leaves_the_workforce() -> bool:
    """The workforce stays as the years made it."""
    return False
