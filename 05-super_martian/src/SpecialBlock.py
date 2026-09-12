"""
Special score-gated block and the key hidden inside it.
"""

from typing import Any, Optional

import pygame

import settings
from src import mixins


class LevelKey(mixins.CollidableMixin):
    EMERGE_DISTANCE = 18
    EMERGE_DURATION = 0.65

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.width = 16
        self.height = 16
        self.start_y = y
        self.end_y = y - self.EMERGE_DISTANCE
        self.elapsed = 0.0
        self.collidable = False
        self.active = True

    def update(self, dt: float) -> None:
        if self.collidable or not self.active:
            return

        self.elapsed = min(self.EMERGE_DURATION, self.elapsed + dt)
        progress = self.elapsed / self.EMERGE_DURATION
        eased_progress = 1 - (1 - progress) ** 3
        self.y = self.start_y + (self.end_y - self.start_y) * eased_progress

        if progress >= 1:
            self.collidable = True

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        if not self.active:
            return

        image = pygame.Surface((16, 16), pygame.SRCALPHA)
        dark_gold = (170, 100, 18)
        gold = (255, 213, 58)
        shine = (255, 247, 166)

        pygame.draw.circle(image, dark_gold, (5, 5), 5)
        pygame.draw.circle(image, gold, (5, 5), 3)
        pygame.draw.circle(image, (0, 0, 0, 0), (5, 5), 1)
        pygame.draw.rect(image, dark_gold, (7, 4, 4, 10))
        pygame.draw.rect(image, gold, (7, 5, 2, 8))
        pygame.draw.rect(image, dark_gold, (9, 10, 5, 3))
        pygame.draw.rect(image, gold, (9, 10, 3, 1))
        pygame.draw.rect(image, shine, (3, 3, 2, 1))

        destination = camera.apply(
            pygame.Rect(self.x, self.y, self.width, self.height)
        )
        if destination.size != image.get_size():
            image = pygame.transform.scale(image, destination.size)
        surface.blit(image, destination)


class SpecialBlock(mixins.DrawableMixin, mixins.CollidableMixin):
    REVEAL_DURATION = 0.3

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        target_score: int,
    ) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.target_score = target_score
        self.texture_id = "tiles"
        self.frame_index = 41
        self.flipped = False
        self.active = False
        self.used = False
        self.reveal_elapsed = 0.0

    def activate(self) -> None:
        self.active = True

    def hit(self) -> Optional[LevelKey]:
        if not self.active or self.used:
            return None

        self.used = True
        return LevelKey(self.x, self.y)

    def update(self, dt: float) -> None:
        if self.active:
            self.reveal_elapsed = min(
                self.REVEAL_DURATION, self.reveal_elapsed + dt
            )

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        if not self.active:
            return

        frame = settings.FRAMES[self.texture_id][self.frame_index]
        image = pygame.Surface((frame.width, frame.height), pygame.SRCALPHA)
        image.blit(settings.TEXTURES[self.texture_id], (0, 0), frame)

        if not self.used:
            pygame.draw.rect(image, (255, 214, 60), (7, 3, 2, 7))
            pygame.draw.rect(image, (255, 214, 60), (7, 12, 2, 2))

        progress = self.reveal_elapsed / self.REVEAL_DURATION
        scale = max(0.1, 1 - (1 - progress) ** 3)
        destination = camera.apply(
            pygame.Rect(self.x, self.y, self.width, self.height)
        )
        scaled_size = (
            max(1, round(destination.width * scale)),
            max(1, round(destination.height * scale)),
        )
        image = pygame.transform.scale(image, scaled_size)
        draw_x = destination.centerx - scaled_size[0] // 2
        draw_y = destination.centery - scaled_size[1] // 2
        surface.blit(image, (draw_x, draw_y))
