"""
ISPPV1 2026
Study Case: Flappy Bird

Author: Nerio Balza
neriojbd@gmail.com

This file contains the definition of the class PauseState.
"""

import pygame

from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text

import settings
from src.Bird import Bird
from src.World import World


class PauseState(BaseState):
    def enter(self, world: World, bird: Bird, score: int) -> None:
        """Keep the live game objects untouched while the state is paused."""
        self.world = world
        self.bird = bird
        self.score = score
        self.overlay = pygame.Surface(
            (settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT), pygame.SRCALPHA
        )
        self.overlay.fill((0, 0, 0, 145))
        pygame.mixer.music.pause()

    def exit(self) -> None:
        pygame.mixer.music.unpause()

    def render(self, surface: pygame.Surface) -> None:
        self.world.render(surface)
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

        surface.blit(self.overlay, (0, 0))

        panel = pygame.Rect(76, 68, settings.VIRTUAL_WIDTH - 152, 152)
        pygame.draw.rect(surface, (18, 35, 55), panel, border_radius=8)
        pygame.draw.rect(surface, settings.COLOR_WHITE, panel, width=2, border_radius=8)

        render_text(
            surface,
            "PAUSED",
            settings.FONTS["flappy"],
            settings.VIRTUAL_WIDTH / 2,
            100,
            settings.COLOR_WHITE,
            center=True,
            shadowed=True,
        )
        render_text(
            surface,
            "TAB / P: resume",
            settings.FONTS["medium"],
            settings.VIRTUAL_WIDTH / 2,
            151,
            settings.COLOR_WHITE,
            center=True,
            shadowed=True,
        )
        render_text(
            surface,
            "ENTER: title screen",
            settings.FONTS["medium"],
            settings.VIRTUAL_WIDTH / 2,
            184,
            settings.COLOR_WHITE,
            center=True,
            shadowed=True,
        )

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if not input_data.pressed:
            return

        if input_id == "pause":
            self.state_machine.change(
                "count_down",
                world=self.world,
                bird=self.bird,
                score=self.score,
            )
        elif input_id == "confirm":
            self.state_machine.change("title")
