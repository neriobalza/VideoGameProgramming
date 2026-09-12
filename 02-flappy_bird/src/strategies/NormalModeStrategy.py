"""Standard Flappy Bird rules."""

import random

from gale.input_handler import InputData

import settings
from src.Bird import Bird
from src.strategies.GameModeStrategy import GameModeStrategy, LogConfiguration


class NormalModeStrategy(GameModeStrategy):
    name = "NORMAL"

    def handle_horizontal_input(
        self,
        bird: Bird,
        input_id: str,
        input_data: InputData,
    ) -> None:
        # Horizontal movement is intentionally disabled in normal mode.
        bird.vx = 0.0

    def next_log_spawn_delay(self) -> float:
        return settings.TIME_TO_SPAWN_LOGS

    def create_log_configuration(
        self,
        last_y: float,
        spawn_delay: float,
    ) -> LogConfiguration:
        del spawn_delay
        y = max(
            settings.MIN_LOG_Y,
            min(last_y + random.randint(-20, 20), settings.MAX_LOG_Y),
        )
        return LogConfiguration(y=y, gap=settings.LOGS_GAP)
