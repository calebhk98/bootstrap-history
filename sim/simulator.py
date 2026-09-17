#!/usr/bin/env python3
"""
ROME 100 AD -> TRANSISTOR : tech-tree simulator, planner and game.

  a RECORD : validate, costs, path   dump the tree and its economics
  a TOOL   : run, compare, sweep     Monte-Carlo a strategy, find where it breaks
  a GAME   : play, agent             step through it yourself, or let a script play

    python3 sim/simulator.py validate
    python3 sim/simulator.py civs                       who you can play
    python3 sim/simulator.py play --manual               free choice, no autopilot
    python3 sim/simulator.py agent --civ rome_100ad --fog

`agent` speaks one JSON object per line in and one per line out. It explains
itself: it prints a welcome on first run and answers {"cmd":"help"}. There is
no protocol document to read, on purpose.

No third-party dependencies. Python 3.8+.
Design notes and the full protocol: sim/PROTOCOL.md

THIS FILE IS THE FRONT DOOR, not the engine. The engine was one 5,600-line
module; it is now sim/engine/, split by subject. Everything that was
importable from `simulator` still is, because every playtest note, every test
and every instruction anyone has ever been given says `sim/simulator.py`,
and that must not stop being true because the inside was tidied.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.data import *            # noqa: F401,F403
from engine.data import (ANNUAL_WAGE, CIVDIR, DEFAULTS, GEOFILE, PRICES,
                         RESFILE, STARTING_KITS, STRATS, TECH_EFFECTS,
                         TRADES_ABSENT, TRADE_FAMILY, TRADE_NOTES, TREE, WAGES,
                         closure, critical_path, haversine_km, load, load_civ,
                         load_geography, load_resources, topo_order,
                         trade_family, goal_catalog, goal_lookup, resolve_goal,
                         # The private loaders too. They are private, and they
                         # are also part of what `import simulator` used to
                         # give you, and a split is not the moment to decide
                         # somebody's tool should stop working.
                         _load_annual_wages, _load_tech_effects,
                         _load_trade_notes, _load_wages)      # noqa: F401
from engine.core import Sim                                  # noqa: F401
from engine.protocol import (_agent_available, _agent_dispatch,  # noqa: F401
                             _agent_end_reason, _agent_help, _agent_state,
                             _waiting_on,
                             _brief, _clean, _flag, _full_entry, _node_explain,
                             _num, _subject_of, load_state, save_state,
                             SAVE_FIELDS, SUBJECTS, HELP_TOPICS,
                             KNOWN_COMMANDS)
from engine.cli import (cmd_agent, cmd_civs, cmd_compare, cmd_costs,  # noqa: F401
                        cmd_goals, cmd_path, cmd_plan, cmd_play, cmd_run,
                        cmd_search, cmd_sensitivity, cmd_sweep, cmd_validate,
                        cmd_why, cmd_menu, load_strategy, main, topo_stable,
                        _summarise, DetRNG, ensure_fixed_hash_seed)

if __name__ == "__main__":
    main()
