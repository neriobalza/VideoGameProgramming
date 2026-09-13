"""Final skeleton boss and its ranged combat behaviour."""

import math
from typing import Any

import pygame

from gale.factory import Factory

import settings
from src.Entity import Entity
from src.Projectile import Projectile
from src.definitions.entity import ENTITY_DEFS
from src.states.entity.EntityIdleState import EntityIdleState
from src.states.entity.EntityWalkState import EntityWalkState

_HITPOINTS = 8
_ATTACK_INTERVAL = 2.0
_FIREBALL_SPEED = 45
_SWORD_VULNERABILITY_DURATION = 3.0
_WALK_SPEED = 18


class Boss(Entity):
    def __init__(self, x: float, y: float) -> None:
        definition = ENTITY_DEFS["skeleton"]
        super().__init__(
            x=x,
            y=y,
            width=32,
            height=32,
            walk_speed=_WALK_SPEED,
            health=_HITPOINTS,
            animation_defs=definition["animations"],
            states={},
        )
        self.is_boss = True
        self.contact_damage = 2
        self.max_hitpoints = _HITPOINTS
        self.hitpoints = _HITPOINTS
        self.sword_vulnerable = False
        self.sword_vulnerability_timer = 0.0
        self.attack_timer = 1.0
        self.projectile_factory = Factory(Projectile)

        self.state_machine.states = {
            "walk": lambda sm: EntityWalkState(self, sm),
            "idle": lambda sm: EntityIdleState(self, sm),
        }
        self.change_state("walk")

    def update(self, dt: float) -> None:
        super().update(dt)

        if self.sword_vulnerable:
            self.sword_vulnerability_timer -= dt

            if self.sword_vulnerability_timer <= 0:
                self.sword_vulnerable = False
                self.sword_vulnerability_timer = 0.0

    def process_ai(self, room: Any, dt: float) -> None:
        # Reuse the same random walk/idle decisions as every regular enemy.
        self.state_machine.current.process_ai(room, dt)
        self.attack_timer -= dt

        if self.attack_timer <= 0:
            self.fire(room)
            self.attack_timer = _ATTACK_INTERVAL

    def fire(self, room: Any):
        """Aims once at the player's current position, then fires in that line."""
        player = room.player
        x = self.x + self.width / 2 - 5
        y = self.y + self.height / 2 - 5
        target_x = player.x + player.width / 2
        target_y = player.y + player.height / 2
        dx = target_x - (x + 5)
        dy = target_y - (y + 5)
        length = math.hypot(dx, dy) or 1

        fireball = self.projectile_factory.create(
            x,
            y,
            {
                "width": 10,
                "height": 10,
                "texture_id": "fireball",
                "velocity_x": dx / length * _FIREBALL_SPEED,
                "velocity_y": dy / length * _FIREBALL_SPEED,
                "max_distance": settings.TILE_SIZE * 30,
                "damage": 6,
                "damage_type": "fireball",
                "owner": "boss",
            },
        )
        room.projectiles.append(fireball)
        return fireball

    def damage(self, dmg: int, damage_type: str = "sword") -> bool:
        if damage_type == "arrow":
            self.sword_vulnerable = True
            self.sword_vulnerability_timer = _SWORD_VULNERABILITY_DURATION
        elif damage_type == "sword":
            if not self.sword_vulnerable:
                return False
        else:
            return False

        self.hitpoints = max(0, self.hitpoints - dmg)
        self.health = self.hitpoints
        self.go_invulnerable(0.15)
        return True

    def render_sprite(
        self, surface: pygame.Surface, texture_id: str, frame_index: int
    ) -> None:
        frame = settings.frame(texture_id, frame_index)
        image = pygame.Surface((frame.width, frame.height), pygame.SRCALPHA)
        image.blit(settings.TEXTURES[texture_id], (0, 0), frame)
        image = pygame.transform.scale(image, (32, 32))

        if self.invulnerable and self.flash_timer > 0.06:
            self.flash_timer = 0
            image.set_alpha(64)

        x = round(self.x)
        y = round(self.y)
        surface.blit(image, (x, y))

        if self.sword_vulnerable:
            pygame.draw.rect(surface, (255, 196, 64), (x - 2, y - 2, 36, 36), 1)
