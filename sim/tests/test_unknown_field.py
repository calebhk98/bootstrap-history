"""SCENARIO (Complaint 574): a field no command reads is refused with `unknown_field`, not accepted as a no-op. The refusal rule is
`field_check.unknown_field_refusal` (test_field_check_rule); this is the wiring that dispatch refuses before the handler runs."""
from .harness import *  # noqa: F401,F403
from .agent_command_helpers import ask_agent

game = unopened_sim()

policy = ask_agent(game, cmd="policy", auto_hire="on")
check("policy given a switch name instead of `set` is refused as an unknown field",
      policy.get("ok") is False and getattr(policy.get("error"), "cause", None) == "unknown_field", policy)
check("...and changed nothing", game.policy.get("auto_hire") in (False, None), game.policy.get("auto_hire"))
