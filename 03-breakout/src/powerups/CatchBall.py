"""
ISPPV1 2023
Study Case: Breakout

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the specialization of PowerUp to let the paddle catch balls.
"""

from typing import TypeVar

from src.powerups.PowerUp import PowerUp


class CatchBall(PowerUp):
    """
    Power-up to let the paddle catch balls for a limited time.
    """

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y, 7)

    def take(self, play_state: TypeVar("PlayState")) -> None:
        play_state.activate_ball_capture()
        self.active = False
