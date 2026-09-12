"""Strategy interface shared by the available game modes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from gale.input_handler import InputData

if TYPE_CHECKING:
    from src.Bird import Bird


@dataclass(frozen=True)
class LogConfiguration:
    """Values needed by World to create one pair of logs."""

    y: float
    gap: float
    oscillating: bool = False


class GameModeStrategy(ABC):
    """Defines every rule that changes with the selected game mode."""

    name: str
    power_ups_enabled: bool = False

    @abstractmethod
    def handle_horizontal_input(
        self,
        bird: "Bird",
        input_id: str,
        input_data: InputData,
    ) -> None:
        """Apply horizontal controls supported by this mode."""

    @abstractmethod
    def next_log_spawn_delay(self) -> float:
        """Return the delay before the next log pair is created."""

    @abstractmethod
    def create_log_configuration(
        self,
        last_y: float,
        spawn_delay: float,
    ) -> LogConfiguration:
        """Return the position and behavior of the next log pair."""

    def next_power_up_spawn_delay(self) -> float:
        """Modes without power-ups never use this value."""
        return float("inf")
