"""
ISPPV1 2023
Study Case: The Legend of the Princess (ARPG)

This file contains the Bow weapon and its projectile factory.
"""

from typing import Any

from gale.factory import Factory

import settings
from src.Projectile import Projectile

_ARROW_SPEED = 190
_FIRE_COOLDOWN = 0.3


class Bow:
    def __init__(self) -> None:
        self.projectile_factory = Factory(Projectile)
        self.cooldown = 0.0

    def update(self, dt: float) -> None:
        self.cooldown = max(0.0, self.cooldown - dt)

    def fire(self, player: Any, room: Any):
        """Creates one arrow through Factory and adds it to the active room."""
        if self.cooldown > 0:
            return None

        width = settings.FRAMES["arrow"][0].width
        height = settings.FRAMES["arrow"][0].height
        x = player.x + player.width / 2 - width / 2
        y = player.y + player.height / 2 - height / 2

        if player.direction == "left":
            x = player.x - width
        elif player.direction == "right":
            x = player.x + player.width
        elif player.direction == "up":
            y = player.y - height
        else:
            y = player.y + player.height

        arrow = self.projectile_factory.create(
            x,
            y,
            {
                "direction": player.direction,
                "width": width,
                "height": height,
                "speed": _ARROW_SPEED,
                "max_distance": settings.TILE_SIZE * 20,
                "texture_id": "arrow",
                "damage_type": "arrow",
                "owner": "player",
            },
        )
        room.projectiles.append(arrow)
        self.cooldown = _FIRE_COOLDOWN
        return arrow
