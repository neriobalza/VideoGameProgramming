"""
ISPPV1 2026
Study Case: Flappy Birld

Author: Nerio Balza
neriojbd@gmail.com

This file contains the definiton of the class PauseState
"""

from typing import Optional

import pygame

from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text

import settings
from src.Bird import Bird
from src.World import World

class PauseState(BaseState):
    def enter(self, world: Optional[World] = None, bird: Optional[Bird] = None, score: Optional[int] = 0):
        self.world = world if world is not None else World()
        self.bird = bird if bird is not None else Bird(
            settings.VIRTUAL_WIDTH / 2 - settings.BIRD_WIDTH / 2,
            settings.VIRTUAL_HEIGHT / 2 - settings.BIRD_HEIGHT / 2,
            settings.BIRD_WIDTH,
            settings.BIRD_HEIGHT, 
        )
        self.score = score 

    def render(self, surface: pygame.surface):
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
        # overlay = pygame.Surface((settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT), masks=(0,0,0,100))
        # surface.blit(overlay, (0,0));
        # surface.blit(py)
        # pygame.draw.rect(surface, (0,0,0,100), pygame.Rect())
        render_text(
            surface,
            "Game Pused",
            settings.FONTS["flappy"],
            settings.VIRTUAL_WIDTH/2,
            settings.VIRTUAL_HEIGHT/2,
            settings.COLOR_WHITE,
            center=True,
            shadowed=True,
        )
        render_text(
            surface,
            "Press 'q' to go to the title screen",
            settings.FONTS["medium"],
            settings.VIRTUAL_WIDTH/2,
            4 * settings.VIRTUAL_HEIGHT / 5,
            settings.COLOR_WHITE,
            center=True,
            shadowed=True,
        )

    def on_input(self, input_id: str, input_data: InputData):
        if input_id == "pause" and input_data.pressed:
            self.state_machine.change("count_down")