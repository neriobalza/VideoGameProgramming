"""
ISPPV1 2023
Study Case: Flappy Bird

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the definition of the class PlayingState.
"""

from typing import Optional

import pygame

from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text

import settings
from src.Bird import Bird
from src.World import World


class PlayingState(BaseState):
    def enter(
        self,
        world: Optional[World] = None,
        bird: Optional[Bird] = None,
        score: int = 0,
    ) -> None:
        self.world = world if world is not None else World()
        self.world.reset(True)
        self.bird = (
            bird
            if bird is not None
            else Bird(
                settings.VIRTUAL_WIDTH / 2 - settings.BIRD_WIDTH / 2,
                settings.VIRTUAL_HEIGHT / 2 - settings.BIRD_HEIGHT / 2,
                settings.BIRD_WIDTH,
                settings.BIRD_HEIGHT,
            )
        )
        self.score = score
        self.state_machine.best_score = max(
            self.state_machine.best_score,
            self.score,
        )

    def update(self, dt: float) -> None:
        self.bird.update(dt)
        self.world.update(dt)

        if self.world.collect_power_up(self.bird.get_rect()):
            self.bird.activate_ghost()

        if self.world.collides(
            self.bird.get_rect(),
            ignore_logs=self.bird.is_ghost,
        ):
            self.bird.deactivate_ghost()
            settings.SOUNDS["explosion"].play()
            settings.SOUNDS["hurt"].play()
            self.state_machine.change(
                "count_down",
                World(strategy=self.world.strategy),
            )
            return

        if self.world.update_scored(self.bird.get_rect()):
            self.score += 1
            self.state_machine.best_score = max(
                self.state_machine.best_score,
                self.score,
            )
            settings.SOUNDS["score"].play()

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
        render_text(
            surface,
            self.world.strategy.name,
            settings.FONTS["medium"],
            20,
            42,
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

        if self.bird.is_ghost:
            ghost_text = f"Ghost: {self.bird.ghost_time_remaining:.1f}s"
            render_text(
                surface,
                ghost_text,
                settings.FONTS["medium"],
                settings.VIRTUAL_WIDTH
                - settings.FONTS["medium"].size(ghost_text)[0]
                - 20,
                42,
                settings.COLOR_WHITE,
                shadowed=True,
            )

    def on_input(self, input_id: str, input_data: InputData) -> None:
        self.world.strategy.handle_horizontal_input(
            self.bird,
            input_id,
            input_data,
        )

        if input_id == "jump" and input_data.pressed:
            self.bird.jump()
        elif input_id == "pause" and input_data.pressed:
            self.bird.stop_horizontal_movement()
            self.state_machine.change(
                "pause",
                world=self.world,
                bird=self.bird,
                score=self.score,
            )
