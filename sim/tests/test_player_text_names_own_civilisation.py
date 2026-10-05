"""Player-facing replies in a non-Rome game use that civilisation's own money word and do
not name Rome (Complaints/132)."""
import json
import re

from .harness import *  # noqa: F401,F403

FORBIDDEN = re.compile(r"denari|\bRom(?:e|an)\b|iuger", re.IGNORECASE)
REPLY_COMMANDS = ("status", "money", "help", "land", "labour", "population", "economy")

han_sim = sim(civ="han_china_100ad", capital=50)


def _ask(**command):
    return S._agent_dispatch(han_sim, NODES, command)


for command_name in REPLY_COMMANDS:
    reply_text = json.dumps(_ask(cmd=command_name))
    check("a Han game's %s reply names no Roman money, unit or city" % command_name,
          not FORBIDDEN.search(reply_text), FORBIDDEN.findall(reply_text))

refusals = []
for node_id in [node_id for node_id in NODES if node_id not in han_sim.done][:80]:
    refusals.append(json.dumps(_ask(cmd="start", node=node_id)))
check("a Han game's start refusals name no Roman money",
      not any(FORBIDDEN.search(text) for text in refusals),
      [FORBIDDEN.findall(text) for text in refusals if FORBIDDEN.search(text)][:3])
