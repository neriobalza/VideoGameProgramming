"""
ISPPV1 2023
Study Case: The Legend of the Princess (ARPG)

This file contains the class Projectile.
"""

import math
from typing import Any, Optional

import pygame

import settings

_DIRECTION_VECTORS = {
    "left": (-1.0, 0.0),
    "right": (1.0, 0.0),
    "up": (0.0, -1.0),
    "down": (0.0, 1.0),
}


class Projectile:
    def __init__(
        self,
        x: float,
        y: float,
        direction: str = "down",
        width: float = 16,
        height: float = 16,
        speed: float = 150,
        max_distance: float = settings.TILE_SIZE * 4,
        texture_id: Optional[str] = None,
        obj: Optional[Any] = None,
        velocity_x: Optional[float] = None,
        velocity_y: Optional[float] = None,
        damage: int = 1,
        damage_type: str = "thrown-pot",
        owner: str = "player",
    ) -> None:
        # Keep the original Projectile(obj, direction) call shape valid for
        # thrown pots while also supporting Factory.create(x, y, properties).
        if hasattr(x, "get_collision_rect") and isinstance(y, str):
            obj = x
            direction = y
            x = obj.x
            y = obj.y
            width = obj.width
            height = obj.height

        self.x = x
        self.y = y
        self.direction = direction
        self.width = width
        self.height = height
        self.speed = speed
        self.max_distance = max_distance
        self.texture_id = texture_id
        self.obj = obj
        self.damage = damage
        self.damage_type = damage_type
        self.owner = owner

        if velocity_x is None or velocity_y is None:
            dx, dy = _DIRECTION_VECTORS[direction]
            self.velocity_x = dx * speed
            self.velocity_y = dy * speed
        else:
            self.velocity_x = velocity_x
            self.velocity_y = velocity_y

        self.distance = 0.0
        self.dead = False

    @classmethod
    def from_object(cls, obj: Any, direction: str):
        return cls(
            obj.x,
            obj.y,
            direction=direction,
            width=obj.width,
            height=obj.height,
            obj=obj,
        )

    def get_collision_rect(self) -> pygame.Rect:
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)

    def update(self, dt: float) -> None:
        if self.dead:
            return

        dx = self.velocity_x * dt
        dy = self.velocity_y * dt
        self.x += dx
        self.y += dy

        if self.obj is not None:
            self.obj.x = self.x
            self.obj.y = self.y

        left = settings.MAP_RENDER_OFFSET_X + settings.TILE_SIZE
        right = settings.VIRTUAL_WIDTH - settings.TILE_SIZE * 2
        top = settings.MAP_RENDER_OFFSET_Y + settings.TILE_SIZE
        bottom = (
            settings.MAP_HEIGHT * settings.TILE_SIZE
            + settings.MAP_RENDER_OFFSET_Y
            - settings.TILE_SIZE
        )

        if (
            self.x <= left
            or self.x + self.width >= right
            or self.y <= top
            or self.y + self.height >= bottom
        ):
            self.dead = True

            if self.obj is not None:
                settings.SOUNDS["pot-wall"].play()

            return

        self.distance += math.hypot(dx, dy)

        if self.distance > self.max_distance:
            self.dead = True

    def render(
        self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0
    ) -> None:
        if self.obj is not None:
            self.obj.render(surface, offset_x, offset_y)
            return

        image = settings.TEXTURES[self.texture_id]

        if self.texture_id == "arrow":
            angle = math.degrees(math.atan2(-self.velocity_y, self.velocity_x)) - 90
            image = pygame.transform.rotate(image, angle)

        rect = image.get_rect(
            center=(
                round(self.x + self.width / 2 + offset_x),
                round(self.y + self.height / 2 + offset_y),
            )
        )
        surface.blit(image, rect)

    def collides(self, target: Any) -> bool:
        return self.get_collision_rect().colliderect(target.get_collision_rect())
