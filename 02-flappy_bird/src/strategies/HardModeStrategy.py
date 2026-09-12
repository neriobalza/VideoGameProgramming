"""Dynamic rules used by hard mode."""

import random

from gale.input_handler import InputData

import settings
from src.Bird import Bird
from src.strategies.GameModeStrategy import GameModeStrategy, LogConfiguration


class HardModeStrategy(GameModeStrategy):
    name = "HARD"
    power_ups_enabled = True

    def handle_horizontal_input(
        self,
        bird: Bird,
        input_id: str,
        input_data: InputData,
    ) -> None:
        if input_id == "left":
            if input_data.pressed:
                bird.vx = -settings.HARD_BIRD_HORIZONTAL_SPEED
            elif input_data.released and bird.vx < 0:
                bird.vx = 0.0
        elif input_id == "right":
            if input_data.pressed:
                bird.vx = settings.HARD_BIRD_HORIZONTAL_SPEED
            elif input_data.released and bird.vx > 0:
                bird.vx = 0.0

    def next_log_spawn_delay(self) -> float:
        return random.uniform(
            settings.HARD_MIN_LOG_SPAWN_DELAY,
            settings.HARD_MAX_LOG_SPAWN_DELAY,
        )

    def create_log_configuration(
        self,
        last_y: float,
        spawn_delay: float,
    ) -> LogConfiguration:
        gap = random.randint(settings.HARD_MIN_LOG_GAP, settings.HARD_MAX_LOG_GAP)

        # More horizontal room permits a larger change in opening height.
        delay_range = (
            settings.HARD_MAX_LOG_SPAWN_DELAY
            - settings.HARD_MIN_LOG_SPAWN_DELAY
        )
        distance_factor = (
            spawn_delay - settings.HARD_MIN_LOG_SPAWN_DELAY
        ) / delay_range
        max_height_change = round(18 + 52 * distance_factor)
        max_y = (
            settings.VIRTUAL_HEIGHT
            - settings.GROUND_HEIGHT
            - gap
            - settings.LOG_HEIGHT
        )
        y = max(
            settings.MIN_LOG_Y,
            min(
                last_y + random.randint(-max_height_change, max_height_change),
                max_y,
            ),
        )
        return LogConfiguration(
            y=y,
            gap=gap,
            oscillating=random.random() < settings.HARD_MOVING_LOG_CHANCE,
        )

    def next_power_up_spawn_delay(self) -> float:
        return random.uniform(
            settings.HARD_MIN_POWER_UP_DELAY,
            settings.HARD_MAX_POWER_UP_DELAY,
        )
