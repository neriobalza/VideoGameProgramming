"""Animated victory sequence shown after completing every level."""

import math
import random

import pygame

from gale.animation import Animation
from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text
from gale.timer import Timer

import settings


class VictoryState(BaseState):
    def enter(self, total_score: int, levels_completed: int) -> None:
        self.total_score = total_score
        self.levels_completed = levels_completed
        self.elapsed = 0.0
        self.title_y = -24.0
        self.martian_x = -20.0
        self.martian_y = settings.VIRTUAL_HEIGHT // 2 - 10
        self.martian_animation = Animation(
            [settings.FRAMES["martian"][9], settings.FRAMES["martian"][10]],
            0.15,
        )
        self.confetti = self._create_confetti()
        Timer.clear()

    def _create_confetti(self):
        randomizer = random.Random(7)
        colors = [
            (255, 226, 80),
            (255, 92, 112),
            (91, 222, 255),
            (121, 235, 126),
            (216, 130, 255),
        ]
        return [
            {
                "x": randomizer.uniform(0, settings.VIRTUAL_WIDTH),
                "y": randomizer.uniform(-settings.VIRTUAL_HEIGHT, 0),
                "speed": randomizer.uniform(28, 58),
                "phase": randomizer.uniform(0, math.tau),
                "color": randomizer.choice(colors),
                "size": randomizer.choice([2, 2, 3]),
            }
            for _ in range(42)
        ]

    def update(self, dt: float) -> None:
        self.elapsed += dt
        self.martian_animation.update(dt)

        title_progress = min(1.0, self.elapsed / 1.1)
        offset = title_progress - 1
        eased_title = 1 + 2.70158 * offset**3 + 1.70158 * offset**2
        self.title_y = -24 + 62 * eased_title

        martian_progress = min(1.0, self.elapsed / 1.4)
        eased_martian = 1 - (1 - martian_progress) ** 3
        center_x = settings.VIRTUAL_WIDTH // 2 - 8
        self.martian_x = -20 + (center_x + 20) * eased_martian
        if martian_progress >= 1:
            self.martian_y = (
                settings.VIRTUAL_HEIGHT // 2
                - 10
                + math.sin(self.elapsed * 5) * 3
            )

        for particle in self.confetti:
            particle["y"] += particle["speed"] * dt
            particle["x"] += math.sin(self.elapsed * 4 + particle["phase"]) * 8 * dt
            if particle["y"] > settings.VIRTUAL_HEIGHT:
                particle["y"] = -4

        if self.elapsed >= settings.VICTORY_SCREEN_DURATION:
            self._return_to_start()

    def _return_to_start(self) -> None:
        Timer.clear()
        self.state_machine.change("start")

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((15, 67, 119))

        for particle in self.confetti:
            pygame.draw.rect(
                surface,
                particle["color"],
                (
                    round(particle["x"]),
                    round(particle["y"]),
                    particle["size"],
                    particle["size"] + 1,
                ),
            )

        render_text(
            surface,
            "Victory!",
            settings.FONTS["medium"],
            settings.VIRTUAL_WIDTH // 2,
            round(self.title_y),
            (255, 226, 80),
            center=True,
            shadowed=True,
        )

        surface.blit(
            settings.TEXTURES["martian"],
            (round(self.martian_x), round(self.martian_y)),
            self.martian_animation.get_current_frame(),
        )

        render_text(
            surface,
            "All levels complete!",
            settings.FONTS["small"],
            settings.VIRTUAL_WIDTH // 2,
            122,
            (255, 255, 255),
            center=True,
            shadowed=True,
        )
        render_text(
            surface,
            f"Total score: {self.total_score}",
            settings.FONTS["small"],
            settings.VIRTUAL_WIDTH // 2,
            140,
            (255, 255, 255),
            center=True,
            shadowed=True,
        )

        seconds_left = max(
            0, math.ceil(settings.VICTORY_SCREEN_DURATION - self.elapsed)
        )
        render_text(
            surface,
            f"Back to title in {seconds_left}",
            settings.FONTS["small"],
            settings.VIRTUAL_WIDTH // 2,
            settings.VIRTUAL_HEIGHT - 20,
            (255, 255, 255),
            center=True,
            shadowed=True,
        )

        fade_start = (
            settings.VICTORY_SCREEN_DURATION - settings.LEVEL_TRANSITION_DURATION
        )
        if self.elapsed > fade_start:
            progress = (
                self.elapsed - fade_start
            ) / settings.LEVEL_TRANSITION_DURATION
            fade = pygame.Surface(
                (settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT), pygame.SRCALPHA
            )
            fade.fill((0, 0, 0, min(255, round(progress * 255))))
            surface.blit(fade, (0, 0))

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "enter" and input_data.pressed:
            self._return_to_start()
