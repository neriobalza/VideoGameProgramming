"""
ISPPV1 2023
Study Case: Ultimate Fantasy (RPG)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class SelectTargetState: cycles a cursor sprite
through the (alive-only) members of a target list with left/right, and
confirms the highlighted one with enter.
"""

from typing import Any, Callable, List, Optional, Tuple

import pygame

from gale.state import BaseState

import settings


class SelectTargetState(BaseState):
    def enter(
        self,
        battle_state: Any,
        targets: List[Any],
        on_target_selected: Callable[[Any], None],
        cursor_position: Optional[Callable[[Any], Tuple[float, float]]] = None,
    ) -> None:
        self.battle_state = battle_state
        self.targets = [target for target in targets if not target.dead]
        self.on_target_selected = on_target_selected
        self.cursor_position = cursor_position

        self.current_selection = 0

    def _next_alive(self) -> None:
        n = len(self.targets)

        if n == 0:
            return

        for step in range(1, n + 1):
            i = (self.current_selection + step) % n

            if not self.targets[i].dead:
                self.current_selection = i
                return

    def _prev_alive(self) -> None:
        n = len(self.targets)

        if n == 0:
            return

        for step in range(1, n + 1):
            i = (self.current_selection - step) % n

            if not self.targets[i].dead:
                self.current_selection = i
                return

    def update(self, dt: float) -> None:
        if self.battle_state is None:
            return

        for enemy in self.battle_state.enemies:
            if not enemy.dead:
                enemy.update(dt)

    def on_input(self, input_id: str, input_data: Any) -> None:
        if not input_data.pressed:
            return

        if input_id == "move_left":
            self._prev_alive()
        elif input_id == "move_right":
            self._next_alive()
        elif input_id == "enter":
            if not self.targets:
                return

            target = self.targets[self.current_selection]
            self.state_machine.pop()
            self.on_target_selected(target)

    def render(self, surface: pygame.Surface) -> None:
        if not self.targets:
            return

        target = self.targets[self.current_selection]
        position = (
            self.cursor_position(target)
            if self.cursor_position is not None
            else (target.x - settings.TILE_SIZE, target.y)
        )
        surface.blit(
            settings.TEXTURES["cursor-right"],
            position,
        )
