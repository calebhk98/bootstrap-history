"""A workforce module over a stand-in host, for the tests of its yearly steps and hiring.

The host carries `state.household`, `state.scenario.year` and `labour`; the module reads the household and the year from
it, uses its `labour`, and the reporting commands it sends land in the host's household as `event_stand_in` applies them.
Further views the step reads are given as keywords."""
from sim.engine.units_prose import plain_number
from sim.ledger.api import PayEdge
from sim.reporting.api import DiscardEventsAfter, RecordAutomation, RecordAutomationSkip, RecordEvent
from sim.tests import event_stand_in, module_harness
from sim.workforce.module import Workforce


def workforce_over(host, **views):
    answers = {kind: (lambda command, host=host: event_stand_in.send(host, command))
               for kind in (RecordEvent, RecordAutomation, RecordAutomationSkip, DiscardEventsAfter)}
    answers[PayEdge] = lambda command: None
    given = {"legacy_acting_household": host.state.household, "year": host.state.scenario.year,
             "plain_number": plain_number}
    given.update(views)
    module = module_harness.build(Workforce, views=given, answers=answers)
    module.labour = host.labour
    return module
