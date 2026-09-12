"""
ISPPV1 2023
Study Case: Flappy Bird

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the definition of the class TitleScreenState.
"""

import pygame

from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text

import settings
from src.World import World
from src.strategies import HardModeStrategy, NormalModeStrategy


class TitleScreenState(BaseState):
    def enter(self) -> None:
        self.world = World()
        self.modes = (NormalModeStrategy(), HardModeStrategy())
        self.selected_mode = self.state_machine.selected_mode

    def update(self, dt: float) -> None:
        self.world.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        self.world.render(surface)
        render_text(
            surface,
            "Flappy Bird",
            settings.FONTS["flappy"],
            settings.VIRTUAL_WIDTH / 2,
            54,
            settings.COLOR_WHITE,
            center=True,
            shadowed=True,
        )
        render_text(
            surface,
            "Select game mode",
            settings.FONTS["medium"],
            settings.VIRTUAL_WIDTH / 2,
            94,
            settings.COLOR_WHITE,
            center=True,
            shadowed=True,
        )
        for index, mode in enumerate(self.modes):
            label = mode.name
            if index == self.selected_mode:
                label = f"> {label} <"
            render_text(
                surface,
                label,
                settings.FONTS["medium"],
                settings.VIRTUAL_WIDTH / 2,
                128 + index * 30,
                settings.COLOR_WHITE,
                center=True,
                shadowed=True,
            )
        descriptions = (
            "Classic gameplay",
            "Move with A/D or arrows - Ghost power-ups",
        )
        render_text(
            surface,
            descriptions[self.selected_mode],
            settings.FONTS["medium"],
            settings.VIRTUAL_WIDTH / 2,
            184,
            settings.COLOR_WHITE,
            center=True,
            shadowed=True,
        )
        render_text(
            surface,
            f"Best score: {self.state_machine.best_score}",
            settings.FONTS["medium"],
            settings.VIRTUAL_WIDTH / 2,
            214,
            settings.COLOR_WHITE,
            center=True,
            shadowed=True,
        )
        render_text(
            surface,
            "Arrows / A D to select - Enter to start",
            settings.FONTS["medium"],
            settings.VIRTUAL_WIDTH / 2,
            246,
            settings.COLOR_WHITE,
            center=True,
            shadowed=True,
        )

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if not input_data.pressed:
            return

        if input_id in ("up", "left"):
            self.selected_mode = (self.selected_mode - 1) % len(self.modes)
            self.state_machine.selected_mode = self.selected_mode
        elif input_id in ("down", "right"):
            self.selected_mode = (self.selected_mode + 1) % len(self.modes)
            self.state_machine.selected_mode = self.selected_mode
        elif input_id == "confirm":
            world = World(strategy=self.modes[self.selected_mode])
            self.state_machine.change("count_down", world)
