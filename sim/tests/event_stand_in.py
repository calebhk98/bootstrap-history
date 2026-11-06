"""A stand-in for the game's `send` on a test host whose household is a plain object: the reporting commands land in
`state.household.log` and `state.household.automation_audit`, shaped by reporting's own rules.

    class Phase(SomeMixin):
        send = event_stand_in.send              # on a class
    game = event_stand_in.stood_in(SimpleNamespace(...))   # on an instance

The host needs `state.household` (with `log`, and for audit rows `automation_audit` and `capital`) and
`state.scenario.year` unless the command names its year. An event for a named seat lands in
`state.seats[seat].household`. Only the reporting commands and the workforce module's are understood."""
from sim.reporting import rules
from sim.reporting.api import DiscardEventsAfter, RecordAutomation, RecordAutomationSkip, RecordEvent


def send(host, command):
    state = host.state
    if isinstance(command, RecordEvent):
        household = state.seats[command.seat].household if command.seat is not None else state.household
        year = command.year if command.year is not None else state.scenario.year
        household.log.append(rules.log_entry(year, command.kind, command.text, command.facts))
        return None
    household = state.household
    if isinstance(command, DiscardEventsAfter):
        del household.log[command.kept:]
        return None
    if isinstance(command, RecordAutomation):
        row = rules.audit_row(state.scenario.year, command.policy, command.action, command.what, command.reason,
                              command.capital_before, household.capital, command.facts)
    elif isinstance(command, RecordAutomationSkip):
        row = rules.audit_row(state.scenario.year, command.policy, "skipped", command.what, command.reason,
                              household.capital, household.capital, command.facts)
    else:
        return workforce_command(household, command)
    household.automation_audit.append(row)
    return row


def workforce_command(household, command):
    """The workforce module's own handler applies a workforce command to the household object standing in for its seat."""
    import dataclasses
    from sim.labour import legacy_trade_defaults
    from sim.labour.trade_data import generic_craft_trade, scholar_trade
    from sim.tests import module_harness
    from sim.workforce.module import Workforce
    from sim.workforce.module_spec import MODULE_SPECS
    from sim.workforce.state import WorkforceSeat
    handlers = dict(MODULE_SPECS[0].applies)
    if type(command) not in handlers:
        raise AssertionError("the stand-in does not apply %s" % type(command).__name__)
    # the household's fields become a workforce seat (shared containers stay shared; craft and scholar people go on the staff book) and its scalar fields are read back
    seat = WorkforceSeat(**{field.name: getattr(household, field.name) for field in dataclasses.fields(WorkforceSeat) if hasattr(household, field.name)})
    if not seat.employees:
        seat.employees = {trade: float(count) for trade, count in ((generic_craft_trade(), seat.artisans), (scholar_trade(), seat.scholars)) if count}
    families = {"trade_family": lambda trade: "scholar" if trade == scholar_trade() else legacy_trade_defaults.CRAFT_FAMILY}
    module = module_harness.build(Workforce, seat=seat, views=families)
    answer = getattr(module, handlers[type(command)])(command)
    for field in dataclasses.fields(WorkforceSeat):
        if hasattr(household, field.name):
            setattr(household, field.name, getattr(seat, field.name))
    return answer


def bound(host):
    return lambda command: send(host, command)


def stood_in(host):
    """`host` with a `send` that applies the reporting commands to its household."""
    host.send = bound(host)
    return host
