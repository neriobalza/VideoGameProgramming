"""
ISPPV1 2023
Study Case: Flappy Bird

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the definition of the class Bird.
"""

import pygame

import settings


class Bird:
    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        self.x: float = x
        self.y: float = y
        self.width: float = width
        self.height: float = height
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.jumping: bool = False
        self.ghost_time_remaining: float = 0.0

    @property
    def is_ghost(self) -> bool:
        return self.ghost_time_remaining > 0

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)

    def jump(self) -> None:
        self.jumping = True

    def activate_ghost(self) -> None:
        self.ghost_time_remaining = settings.GHOST_EFFECT_DURATION
        settings.SOUNDS["power_up"].play()
        settings.play_music("ghost")

    def deactivate_ghost(self) -> None:
        if not self.is_ghost:
            return

        self.ghost_time_remaining = 0.0
        settings.play_music("normal")

    def stop_horizontal_movement(self) -> None:
        self.vx = 0.0

    def update(self, dt: float) -> None:
        if self.is_ghost:
            self.ghost_time_remaining = max(0.0, self.ghost_time_remaining - dt)
            if not self.is_ghost:
                settings.play_music("normal")

        self.vy += settings.GRAVITY * dt

        if self.jumping:
            settings.SOUNDS["jump"].play()
            self.vy = -settings.JUMP_TAKEOFF_SPEED
            self.jumping = False

        self.x += self.vx * dt
        self.x = max(0, min(self.x, settings.VIRTUAL_WIDTH - self.width))
        self.y += self.vy * dt

    def render(self, surface: pygame.Surface) -> None:
        texture = (
            settings.TEXTURES["ghost_bird"]
            if self.is_ghost
            else settings.TEXTURES["bird"]
        )
        surface.blit(texture, self.get_rect())
