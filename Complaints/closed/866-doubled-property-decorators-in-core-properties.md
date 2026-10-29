# Two doubled `@property` decorators in the game's forwarding properties made `bounties_paid` and `_said_stack_caution` unreadable

**Status:** closed - fixed in the scenario module move (the protocol golden could not pass without it)

Commit 8038b456 (workforce reads through views) left a stray `@property` above two properties in
`sim/engine/core_properties.py`: `bounties_paid` and `_said_stack_caution`. A property wrapped in a property is not
callable, so reading either raised `TypeError: 'property' object is not callable`. `ui_port.said_stack_caution` reads
`_said_stack_caution` on the first non-empty `available` digest, so `{"cmd":"available"}` answered an internal error
(`norse_session_round_trips` of `python3 -m sim.tests --only protocol_golden` failed at command 1 with `cheapest_six` absent).

The stray decorators are removed; the behaviour is the base's. No regression test of its own: the protocol golden covers
the `available` digest.
