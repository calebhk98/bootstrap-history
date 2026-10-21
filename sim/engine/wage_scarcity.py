"""The scarcity-driven wage index: labour is dearer the further the working population sits below its unshocked trend."""


def wage_index_of(base_index, scarcity_elasticity, population_scale, unshocked_scale):
    """The base index raised in proportion to the shortfall of the population scale below its unshocked trend."""
    shortfall = max(0.0, 1.0 - population_scale / unshocked_scale)
    return base_index * (1.0 + scarcity_elasticity * shortfall)
