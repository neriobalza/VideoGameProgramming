"""
ISPPV1 2023
Study Case: Flappy Bird

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the definition of the class LogPair: a top log
(rendered flipped upside down) and a bottom log, LOGS_GAP pixels
apart, that scroll left together and score once the bird passes them.
"""

import pygame

import settings


class LogPair:
    def __init__(
        self,
        x: float,
        y: float,
        gap: float = settings.LOGS_GAP,
        oscillating: bool = False,
    ) -> None:
        self.x: float = x
        self.center_y: float = y + settings.LOG_HEIGHT + gap / 2
        self.gap: float = gap
        self.max_gap: float = gap
        self.oscillating: bool = oscillating
        self.gap_direction: int = -1
        self.scored: bool = False

    def get_top_rect(self) -> pygame.Rect:
        top_y = self.center_y - self.gap / 2 - settings.LOG_HEIGHT
        return pygame.Rect(
            round(self.x),
            round(top_y),
            settings.LOG_WIDTH,
            settings.LOG_HEIGHT,
        )

    def get_bottom_rect(self) -> pygame.Rect:
        bottom_y = self.center_y + self.gap / 2
        return pygame.Rect(
            round(self.x),
            round(bottom_y),
            settings.LOG_WIDTH,
            settings.LOG_HEIGHT,
        )

    def collides(self, rect: pygame.Rect) -> bool:
        return (
            self.get_top_rect().colliderect(rect)
            or self.get_bottom_rect().colliderect(rect)
        )

    def update(self, dt: float) -> None:
        self.x += -settings.MAIN_SCROLL_SPEED * dt

        if not self.oscillating:
            return

        self.gap += self.gap_direction * settings.HARD_MOVING_LOG_SPEED * dt

        if self.gap <= 0:
            self.gap = 0
            self.gap_direction = 1
            settings.SOUNDS["logs_hit"].play()
        elif self.gap >= self.max_gap:
            self.gap = self.max_gap
            self.gap_direction = -1

    def is_out_of_game(self) -> bool:
        return self.x < -settings.LOG_WIDTH

    def update_scored(self, rect: pygame.Rect) -> bool:
        if self.scored:
            return False

        if rect.left > self.x + settings.LOG_WIDTH:
            self.scored = True
            return True

        return False

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(settings.TEXTURES["log_inverted"], self.get_top_rect())
        surface.blit(settings.TEXTURES["log"], self.get_bottom_rect())
