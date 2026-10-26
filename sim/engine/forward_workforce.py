"""One-line forwarders from the old `Sim` names of workforce to the workforce module, for callers not yet in a module.

The screens, the economy port, the mods and the engine's mixins still say `sim.labour.<member>`, `sim.wage_index` or
`sim.HOURS_PER_PERSON_YEAR`; each line goes when its last caller reads the view (`sim.view(name)`) or sends the command
(`sim.send(command)`) itself."""


class ForwardWorkforceMixin:

    @property
    def labour(self):
        """The workforce module's labour implementation (its members are what callers outside a module still use)."""
        return self.assembly.modules["workforce"].labour

    @property
    def wage_index(self):
        return self.view("wage_index")()

    @property
    def HOURS_PER_PERSON_YEAR(self):
        """Hours a person gives in a year, the working day's length counted."""
        return self.view("hours_per_person_year")()
