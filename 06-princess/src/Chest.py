"""Interactive chest that grants the dungeon's bow."""

from typing import Any

import pygame

import settings
from src.GameObject import GameObject
from src.definitions.game_objects import GAME_OBJECT_DEFS


class Chest(GameObject):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(GAME_OBJECT_DEFS["chest"], x, y)
        self.opened = False
        self.reward_timer = 0.0

    def open(self, player: Any) -> bool:
        if self.opened:
            return False

        self.opened = True
        self.state = "opened"
        self.reward_timer = 1.25
        player.give_bow()
        return True

    def update(self, dt: float) -> None:
        self.reward_timer = max(0.0, self.reward_timer - dt)

    def render(
        self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0
    ) -> None:
        x = round(self.x + offset_x)
        y = round(self.y + offset_y)
        texture = settings.TEXTURES["chest"]

        if not self.opened:
            surface.blit(texture, (x, y))
        else:
            # The supplied chest has one frame; separating its lid provides
            # a readable open state while preserving that original asset.
            surface.blit(texture, (x, y + 2), pygame.Rect(0, 13, 32, 19))
            surface.blit(texture, (x, y - 3), pygame.Rect(0, 0, 32, 13))

        if self.reward_timer > 0:
            surface.blit(settings.TEXTURES["bow"], (x + 8, y - 18))
