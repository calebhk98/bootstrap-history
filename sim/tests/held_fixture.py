"""Set up what a test seat holds through the knowledge module's own commands (the held sets refuse any other write)."""
from sim.knowledge.api import ForgetTechnique, LearnTechnique, ReceiveTechniques, RevealNodes, StartDoneYearRecord
from sim.knowledge.module import Knowledge
from sim.production.api import RefreshDoneCaches
from . import module_harness


def _module(seat):
    return module_harness.build(Knowledge, seat=seat, answers={RefreshDoneCaches: None}, module_id="knowledge")


def hold(seat, nodes, granted=False):
    """`seat` (a KnowledgeSeat) now holds `nodes`, as its country's own when `granted`."""
    _module(seat).receive_techniques(ReceiveTechniques(tuple(sorted(nodes)), granted))


def finish(seat, node_id, year):
    """`seat` finished `node_id` in `year`."""
    _module(seat).learn_technique(LearnTechnique(node_id, year=year))


def start_record(seat):
    _module(seat).start_done_year_record(StartDoneYearRecord())


def drop(seat, nodes):
    _module(seat).forget_technique(ForgetTechnique(tuple(sorted(nodes))))


def hear(seat, nodes):
    _module(seat).reveal_nodes(RevealNodes(tuple(sorted(nodes))))
