"""What the household actor asks of the engine: a state of its own when it is not handed one."""
from typing import Any

from .state import (EconomyState, FounderState, GovernanceState, HouseholdState,
                    PopulationState, ProjectsState, ScenarioState, SimulationState)


class HouseholdPort:
    """The engine's answers to the questions a household asks."""

    def fresh_state(self, starting_capital: float) -> Any:
        return SimulationState(
            household=HouseholdState(capital=float(starting_capital)),
            projects=ProjectsState(),
            economy=EconomyState(),
            governance=GovernanceState(),
            founder=FounderState(),
            scenario=ScenarioState(),
            population=PopulationState(),
        )
