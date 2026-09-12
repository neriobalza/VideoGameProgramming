"""
ISPPV1 2023
Study Case: Breakout

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the specialization of PowerUp to add cannons to the paddle.
"""

from typing import TypeVar

from src.powerups.PowerUp import PowerUp


class Cannons(PowerUp):
    """
    Power-up to arm the paddle with a single pair of projectiles.
    """

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y, 6)

    def take(self, play_state: TypeVar("PlayState")) -> None:
        play_state.cannons_ready = True
        self.active = False
