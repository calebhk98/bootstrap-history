"""The engine's change hooks: what to tell the owners of the memos when the set of techniques done, or of what is operating, changes."""
from sim.knowledge.api import NoteTechniquesChanged
from sim.production.api import RefreshDoneCaches, RefreshOperatingCaches
from sim.ventures.api import NoteOperatingChanged


def done_changed(sim):
    """Call after anything adds to or removes from the set of techniques done (or granted): the production module drops its memos, knowledge counts the change."""
    sim.send(RefreshDoneCaches())
    sim.send(NoteTechniquesChanged())


def operating_changed(sim):
    """Call after anything adds to or removes from what is operating: the production module drops its memos, ventures count the change."""
    sim.send(RefreshOperatingCaches())
    sim.send(NoteOperatingChanged())
