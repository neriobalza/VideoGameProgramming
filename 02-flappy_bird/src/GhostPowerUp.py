"""Collectible that temporarily turns the bird into a ghost."""

import pygame

import settings


class GhostPowerUp:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def get_rect(self) -> pygame.Rect:
        texture = settings.TEXTURES["ghost_power_up"]
        return pygame.Rect(
            round(self.x),
            round(self.y),
            texture.get_width(),
            texture.get_height(),
        )

    def update(self, dt: float) -> None:
        self.x -= settings.MAIN_SCROLL_SPEED * dt

    def collides(self, rect: pygame.Rect) -> bool:
        return self.get_rect().colliderect(rect)

    def is_out_of_game(self) -> bool:
        return self.get_rect().right < 0

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(settings.TEXTURES["ghost_power_up"], self.get_rect())
