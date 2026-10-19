"""Complaint 574: a field no command reads is refused with `unknown_field`, not accepted as a no-op."""
from .harness import *  # noqa: F401,F403
from .agent_command_helpers import ask_agent, pristine_game

game = pristine_game()


def refusal_cause(reply):
    error = reply.get("error")
    return getattr(error, "cause", None) or reply.get("cause")


policy = ask_agent(game, cmd="policy", auto_hire="on")
check("policy given a switch name instead of `set` is refused as an unknown field",
      policy.get("ok") is False and refusal_cause(policy) == "unknown_field", policy)
check("...and the reply names the field and the accepted ones",
      policy.get("field") == "auto_hire" and "set" in (policy.get("accepted_fields") or []), policy)
check("...and changed nothing", game.policy.get("auto_hire") in (False, None), game.policy.get("auto_hire"))

helped = ask_agent(game, cmd="help", command="sell")
check("help given `command` is refused as an unknown field naming topic as the accepted one",
      helped.get("ok") is False and refusal_cause(helped) == "unknown_field"
      and helped.get("field") == "command" and "topic" in (helped.get("accepted_fields") or []), helped)

check("a declared field is still accepted", ask_agent(game, cmd="help", topic="sell").get("ok") is True)
check("policy `set` is still accepted", ask_agent(game, cmd="policy", set={}).get("ok") is True)
check("the shared output flag is still accepted", ask_agent(game, cmd="state", compact=True).get("ok") is True)
