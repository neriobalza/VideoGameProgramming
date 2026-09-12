"""
ISPPV1 2023
Study Case: Flappy Bird

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the definition of the class World: the scrolling
background/ground, and the log pairs the bird must fly through.
"""

import random
from typing import List, Optional

import pygame

from gale.factory import Factory

import settings
from src.GhostPowerUp import GhostPowerUp
from src.LogPair import LogPair
from src.strategies import GameModeStrategy, NormalModeStrategy


class World:
    def __init__(
        self,
        generate_logs: bool = False,
        strategy: Optional[GameModeStrategy] = None,
    ) -> None:
        self.strategy = strategy if strategy is not None else NormalModeStrategy()
        self.generate_logs: bool = generate_logs
        self.background_x: float = 0.0
        self.ground_x: float = 0.0
        self.logs: List[LogPair] = []
        self.logs_spawn_timer: float = 0.0
        self.last_log_y: float = settings.MIN_LOG_Y + random.randint(0, 80) + 20
        self.next_log_spawn_delay = self.strategy.next_log_spawn_delay()
        self.log_pair_factory: Factory = Factory(LogPair)
        self.power_ups: List[GhostPowerUp] = []
        self.power_up_spawn_timer: float = 0.0
        self.next_power_up_spawn_delay = (
            self.strategy.next_power_up_spawn_delay()
        )
        self.power_up_factory: Factory = Factory(GhostPowerUp)

    def reset(self, generate_logs: bool) -> None:
        self.generate_logs = generate_logs

    def collides(self, rect: pygame.Rect, ignore_logs: bool = False) -> bool:
        if rect.bottom >= settings.VIRTUAL_HEIGHT:
            return True

        return not ignore_logs and any(
            log_pair.collides(rect) for log_pair in self.logs
        )

    def update_scored(self, rect: pygame.Rect) -> bool:
        return any(log_pair.update_scored(rect) for log_pair in self.logs)

    def collect_power_up(self, rect: pygame.Rect) -> bool:
        for power_up in self.power_ups:
            if power_up.collides(rect):
                self.power_ups.remove(power_up)
                return True

        return False

    def update(self, dt: float) -> None:
        if self.generate_logs:
            self.logs_spawn_timer += dt

            if self.logs_spawn_timer >= self.next_log_spawn_delay:
                self.logs_spawn_timer = 0.0
                configuration = self.strategy.create_log_configuration(
                    self.last_log_y,
                    self.next_log_spawn_delay,
                )
                self.last_log_y = configuration.y
                self.logs.append(
                    self.log_pair_factory.create(
                        settings.VIRTUAL_WIDTH,
                        configuration.y,
                        {
                            "gap": configuration.gap,
                            "oscillating": configuration.oscillating,
                        },
                    )
                )
                self.next_log_spawn_delay = self.strategy.next_log_spawn_delay()

            if self.strategy.power_ups_enabled:
                self.power_up_spawn_timer += dt
                if self.power_up_spawn_timer >= self.next_power_up_spawn_delay:
                    self.power_up_spawn_timer = 0.0
                    x = settings.VIRTUAL_WIDTH + random.randint(0, 80)
                    y = random.randint(
                        20,
                        settings.VIRTUAL_HEIGHT
                        - settings.GROUND_HEIGHT
                        - settings.GHOST_POWER_UP_HEIGHT
                        - 20,
                    )
                    self.power_ups.append(self.power_up_factory.create(x, y))
                    self.next_power_up_spawn_delay = (
                        self.strategy.next_power_up_spawn_delay()
                    )

        self.background_x += -settings.BACK_SCROLL_SPEED * dt

        if self.background_x <= -settings.BACKGROUND_LOOPING_POINT:
            self.background_x = 0

        self.ground_x += -settings.MAIN_SCROLL_SPEED * dt

        if self.ground_x <= -settings.VIRTUAL_WIDTH:
            self.ground_x = 0

        for log_pair in self.logs:
            log_pair.update(dt)

        for power_up in self.power_ups:
            power_up.update(dt)

        self.logs = [
            log_pair for log_pair in self.logs if not log_pair.is_out_of_game()
        ]
        self.power_ups = [
            power_up
            for power_up in self.power_ups
            if not power_up.is_out_of_game()
        ]

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(settings.TEXTURES["background"], (round(self.background_x), 0))

        for log_pair in self.logs:
            log_pair.render(surface)

        for power_up in self.power_ups:
            power_up.render(surface)

        surface.blit(
            settings.TEXTURES["ground"],
            (round(self.ground_x), settings.VIRTUAL_HEIGHT - settings.GROUND_HEIGHT),
        )
