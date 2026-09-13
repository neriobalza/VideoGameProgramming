"""Celebration shown after defeating the dungeon boss."""

import random

import pygame

from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text

import settings

_CELEBRATION_DURATION = 5.0
_CONFETTI_COLORS = (
    (255, 196, 64),
    (175, 53, 42),
    (100, 210, 255),
    (120, 230, 130),
    (235, 120, 220),
)


class VictoryState(BaseState):
    def enter(self) -> None:
        self.elapsed = 0.0
        rng = random.Random()
        self.confetti = [
            {
                "x": rng.randrange(settings.VIRTUAL_WIDTH),
                "y": rng.randrange(-settings.VIRTUAL_HEIGHT, settings.VIRTUAL_HEIGHT),
                "speed": rng.randrange(25, 65),
                "size": rng.randrange(2, 5),
                "color": rng.choice(_CONFETTI_COLORS),
            }
            for _ in range(70)
        ]

        pygame.mixer.music.load(settings.MUSIC["start"])
        pygame.mixer.music.play(loops=-1)
        settings.SOUNDS["heart-taken"].play()

    def exit(self) -> None:
        pygame.mixer.music.stop()

    def _return_to_menu(self) -> None:
        self.state_machine.change("start")

    def update(self, dt: float) -> None:
        self.elapsed += dt

        for particle in self.confetti:
            particle["y"] += particle["speed"] * dt

            if particle["y"] > settings.VIRTUAL_HEIGHT:
                particle["y"] = -particle["size"]

        if self.elapsed >= _CELEBRATION_DURATION:
            self._return_to_menu()

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((28, 16, 48))

        for particle in self.confetti:
            pygame.draw.rect(
                surface,
                particle["color"],
                (
                    round(particle["x"]),
                    round(particle["y"]),
                    particle["size"],
                    particle["size"] * 2,
                ),
            )

        render_text(
            surface,
            "VICTORY!",
            settings.FONTS["princess"],
            settings.VIRTUAL_WIDTH / 2 + 2,
            settings.VIRTUAL_HEIGHT / 2 - 38,
            settings.COLOR_TITLE_SHADOW,
            center=True,
        )
        render_text(
            surface,
            "VICTORY!",
            settings.FONTS["princess"],
            settings.VIRTUAL_WIDTH / 2,
            settings.VIRTUAL_HEIGHT / 2 - 40,
            (255, 196, 64),
            center=True,
        )
        render_text(
            surface,
            "The skeleton has fallen",
            settings.FONTS["princess-small"],
            settings.VIRTUAL_WIDTH / 2,
            settings.VIRTUAL_HEIGHT / 2 + 12,
            settings.COLOR_WHITE,
            center=True,
        )
        render_text(
            surface,
            "Returning to menu...",
            settings.FONTS["princess-small"],
            settings.VIRTUAL_WIDTH / 2,
            settings.VIRTUAL_HEIGHT / 2 + 48,
            settings.COLOR_WHITE,
            center=True,
        )

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "enter" and input_data.pressed:
            self._return_to_menu()
