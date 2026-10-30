"""The actors' literacy views and commands over a stand-in country, for tests of the diffusion module: the stand-in has `get`,
`copy`, `school` and `teach` (as `CountryLiteracy` has), and the module's reads and sends reach it as they reach the actors."""
from sim.actors.api import SchoolLiteracy, TeachLiteracy
from sim.actors.literacy_rules import school


def over(literacy, ceiling=None):
    """(views, answers) for `module_harness.build`: the figure and the preview read the stand-in, the commands move it."""
    views = {"country_literacy_figure": lambda country, field: literacy.get(field),
             "literacy_after_schooling": lambda country, steps: school(literacy.copy(), steps)}
    if ceiling is not None:
        views["country_literacy_ceiling"] = lambda country, common, propertied: ceiling
    answers = {SchoolLiteracy: lambda command: school(literacy, command.steps),
               TeachLiteracy: lambda command: literacy.teach(command.field, command.value, command.ceiling)}
    return views, answers
