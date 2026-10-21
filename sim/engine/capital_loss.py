"""What a catastrophe takes from capital: a share of what is held, never of what is owed."""


def capital_lost(capital, fraction):
    """The money destroyed when `fraction` of `capital` is lost. Nothing is lost from zero or a debt, so a catastrophe
    never pays off what is owed, and a fraction outside zero to one is clamped."""
    if capital <= 0:
        return 0.0
    return capital * max(0.0, min(1.0, fraction))
