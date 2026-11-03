"""The need ids an `EconomySetup` falls back to when its port does not state them. TRANSITIONAL: the port
(sim/markets/port_setup.py) should pass `need_roles.need_of_role(need_data, role)` for each; once it does, this file
and the setup defaults are deleted. Nothing else in the economy names a need id."""

FUEL_NEED_ID = "warmth"
HUNGER_NEED_ID = "food"
WORK_NEED_ID = "household_work"
