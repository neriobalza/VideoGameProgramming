"""
ISPPV1 2023
Study Case: Flappy Bird

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the definition of the class CountDownState.
"""

from typing import Optional

import pygame

from gale.state import BaseState
from gale.text import render_text

import settings
from src.Bird import Bird
from src.World import World


class CountDownState(BaseState):
    def enter(
        self,
        world: Optional[World] = None,
        bird: Optional[Bird] = None,
        score: int = 0,
    ) -> None:
        self.world = world if world is not None else World(generate_logs=False)
        self.bird = bird
        self.score = score
        self.is_resuming = bird is not None
        self.counter = 3
        self.timer = 0.0

    def update(self, dt: float) -> None:
        self.timer += dt

        if self.timer >= 1.0:
            self.timer = 0.0
            self.counter -= 1

            if self.counter == 0:
                self.state_machine.change(
                    "playing",
                    world=self.world,
                    bird=self.bird,
                    score=self.score,
                )
                return

        # The title-screen countdown keeps its animated background. When
        # resuming, every gameplay object remains frozen until the countdown
        # finishes so the player gets a fair restart.
        if not self.is_resuming:
            self.world.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        self.world.render(surface)

        if self.bird is not None:
            self.bird.render(surface)
            render_text(
                surface,
                f"Score: {self.score}",
                settings.FONTS["flappy"],
                20,
                10,
                settings.COLOR_WHITE,
                shadowed=True,
            )
            best_score_text = f"Best: {self.state_machine.best_score}"
            render_text(
                surface,
                best_score_text,
                settings.FONTS["flappy"],
                settings.VIRTUAL_WIDTH
                - settings.FONTS["flappy"].size(best_score_text)[0]
                - 20,
                10,
                settings.COLOR_WHITE,
                shadowed=True,
            )

        render_text(
            surface,
            str(self.counter),
            settings.FONTS["huge"],
            settings.VIRTUAL_WIDTH / 2,
            settings.VIRTUAL_HEIGHT / 2,
            settings.COLOR_WHITE,
            center=True,
            shadowed=True,
        )
