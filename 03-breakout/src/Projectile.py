"""
ISPPV1 2023
Study Case: Breakout

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class Projectile.
"""

from typing import Any

import pygame

import settings


class Projectile:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
        self.previous_y = y
        self.width = settings.PROJECTILE_WIDTH
        self.height = settings.PROJECTILE_HEIGHT
        self.vy = -settings.PROJECTILE_SPEED
        self.active = True

    def get_collision_rect(self) -> pygame.Rect:
        top = min(self.y, self.previous_y)
        bottom = max(self.y + self.height, self.previous_y + self.height)
        return pygame.Rect(self.x, top, self.width, bottom - top)

    def collides(self, another: Any) -> bool:
        return self.get_collision_rect().colliderect(another.get_collision_rect())

    def update(self, dt: float) -> None:
        self.previous_y = self.y
        self.y += self.vy * dt

        if self.y + self.height < 0:
            self.active = False

    def render(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(
            surface,
            settings.PROJECTILE_COLOR,
            (self.x, self.y, self.width, self.height),
        )
