"""
ISPPV1 2023
Study Case: Breakout

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the specialization of PowerUp to protect the bottom boundary.
"""

from typing import TypeVar

from src.powerups.PowerUp import PowerUp


class GhostPaddle(PowerUp):
    """
    Power-up to make every ball rebound at the paddle height.
    """

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y, 5)

    def take(self, play_state: TypeVar("PlayState")) -> None:
        play_state.activate_ghost_paddle()
        self.active = False
