"""The land ceilings of mines and woodland (Complaint 640): called on built inputs, no game."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.resources.ceilings import forest_ceiling_hectares
from sim.resources.ceilings import mine_ceiling_tonnes, room_under_ceiling

FAVOUR = {"base": 1000.0, "state_scale": 4000.0}

# --- the ceiling of one material
plenty = mine_ceiling_tonnes(None, 0.5, 3000.0, 1000.0, 1.0, 1.0)
scarce = mine_ceiling_tonnes(None, 0.5, 3000.0, 1000.0, 1.0, 0.1)
check("the ceiling differs by material: a material the ground holds little of has a lower ceiling than one it holds"
      " plenty of", scarce < plenty and abs(scarce - 0.1 * plenty) < 1e-9, (scarce, plenty))
check("a ground holding none of a material has no ceiling for it",
      mine_ceiling_tonnes(None, 0.5, 3000.0, 1000.0, 1.0, 0.0) == 0.0)
check("a stranger's ceiling is the stranger base plus the stranger scale times state capacity",
      abs(plenty - (3000.0 + 1000.0 * 0.5)) < 1e-9, plenty)
favoured = mine_ceiling_tonnes(FAVOUR, 0.5, 3000.0, 1000.0, 1.0, 1.0)
check("a held ceiling effect replaces the stranger terms", abs(favoured - (1000.0 + 4000.0 * 0.5)) < 1e-9, favoured)
check("a more capable state raises the ceiling",
      mine_ceiling_tonnes(FAVOUR, 0.9, 3000.0, 1000.0, 1.0, 1.0) > favoured)
check("a larger revenue multiple raises the ceiling in proportion",
      abs(mine_ceiling_tonnes(FAVOUR, 0.5, 3000.0, 1000.0, 2.5, 1.0) - 2.5 * favoured) < 1e-9)

# --- what is left under a ceiling
check("room under a ceiling is the ceiling less what stands and what is on order",
      room_under_ceiling(100.0, 30.0, 20.0) == 50.0)
check("room under a ceiling counts nothing on order when none is given", room_under_ceiling(100.0, 30.0) == 70.0)
check("room under a ceiling is never negative", room_under_ceiling(100.0, 80.0, 40.0) == 0.0)
asked, room = 5000.0, room_under_ceiling(100.0, 30.0, 20.0)
check("asking for far more than the ceiling allows delivers only the room", min(asked, room) == 50.0)

# --- woodland: the same room rule over the forest ceiling
forest = forest_ceiling_hectares(2.0e6, 0.5, 100.0, 50.0, 1.0)
check("woodland already held counts against the forest ceiling", room_under_ceiling(forest, forest * 0.25) == forest * 0.75)
check("woodland held above a ceiling that shrank leaves no room", room_under_ceiling(forest, forest * 2.0) == 0.0)
