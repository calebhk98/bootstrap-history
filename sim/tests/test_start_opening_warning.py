"""start_opening_warning: Complaint 131 - warn at start when free staff are insufficient to open the finished concern."""
from .harness import *  # noqa: F401,F403


# --- Complaint 131: start should warn when a concern cannot be opened with today's staff.
# Concern with insufficient free staff to open.
short_sim = sim(capital=1_000_000)
# Complete prerequisites so we can start school_founded
short_sim.done.update(NODES["school_founded"]["pre"])
short_sim.venture_staff_free = lambda: (0.0, 0.0)
short_sim.venture_hands = lambda node_id: (5.0, 5.0)
short_reply = S._agent_dispatch(short_sim, NODES, {"cmd": "start", "id": "school_founded"})
check("a concern started with insufficient staff says so in the warning",
      "could not open it" in short_reply.get("today_you_could_not_open_this_when_it_is_done", ""),
      short_reply.get("today_you_could_not_open_this_when_it_is_done"))

# Concern with sufficient free staff.
staffed_sim = sim(capital=1_000_000)
# Complete prerequisites so we can start school_founded
staffed_sim.done.update(NODES["school_founded"]["pre"])
staffed_sim.venture_staff_free = lambda: (50.0, 50.0)
staffed_sim.venture_hands = lambda node_id: (5.0, 5.0)
staffed_reply = S._agent_dispatch(staffed_sim, NODES, {"cmd": "start", "id": "school_founded"})
check("...and stays quiet when the staff are free",
      "could not open it" not in staffed_reply.get("today_you_could_not_open_this_when_it_is_done", ""),
      staffed_reply.get("today_you_could_not_open_this_when_it_is_done"))

# Non-concern technology has no warning.
tech_sim = sim(capital=1_000_000)
tech_sim.venture_staff_free = lambda: (0.0, 0.0)
tech_sim.venture_hands = lambda node_id: (5.0, 5.0)
tech_reply = S._agent_dispatch(tech_sim, NODES, {"cmd": "start", "id": "ag2_balanced_ration"})
check("a non-concern technology has no opening staff warning",
      "today_you_could_not_open_this_when_it_is_done" not in tech_reply,
      tech_reply.get("today_you_could_not_open_this_when_it_is_done"))
