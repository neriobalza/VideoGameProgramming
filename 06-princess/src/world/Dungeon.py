"""
ISPPV1 2023
Study Case: The Legend of the Princess (ARPG)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class Dungeon.
"""

import math
import random
from typing import Callable, Optional, TypeVar

import pygame

from gale.timer import Timer

import settings
from src.world.Room import Room

_BOSS_ROOM_CHANCE = 0.25


class Dungeon:
    def __init__(
        self,
        player: TypeVar("Player"),
        on_game_over: Callable[[], None],
        on_victory: Optional[Callable[[], None]] = None,
    ) -> None:
        self.player = player
        self.on_game_over = on_game_over
        self.on_victory = on_victory or (lambda: None)

        # The chest's room is selected once per dungeon. Counting rooms
        # instead of rolling every time guarantees exactly one chest.
        self.rooms_created = 0
        self.chest_room_number = random.randint(1, 3)
        self.chest_generated = False
        self.boss_room_generated = False

        # Current room we're operating in.
        self.current_room = self._create_normal_room()

        # Room we're moving the camera to during a shift; becomes the
        # active room afterwards.
        self.next_room = None

        # Translation offsets, only used while shifting screens.
        self.camera_x = 0
        self.camera_y = 0
        self.shifting = False

    def _create_normal_room(self) -> Room:
        self.rooms_created += 1
        spawn_chest = (
            not self.chest_generated
            and self.rooms_created == self.chest_room_number
        )
        room = Room(
            self.player,
            self.on_game_over,
            spawn_chest=spawn_chest,
            on_victory=self.on_victory,
        )

        if spawn_chest:
            self.chest_generated = True

        return room

    def _create_next_room(self, shift_x: float, shift_y: float) -> Room:
        entry_direction = "bottom"

        if shift_x > 0:
            entry_direction = "left"
        elif shift_x < 0:
            entry_direction = "right"
        elif shift_y > 0:
            entry_direction = "top"

        if (
            self.player.has_bow
            and not self.boss_room_generated
            and random.random() < _BOSS_ROOM_CHANCE
        ):
            self.boss_room_generated = True
            return Room(
                self.player,
                self.on_game_over,
                boss_room=True,
                entry_direction=entry_direction,
                on_victory=self.on_victory,
            )

        return self._create_normal_room()

    def begin_shifting(self, shift_x: float, shift_y: float) -> None:
        """
        Prepares for the camera shifting process, kicking off a tween of the
        camera position. Triggered via a doorway collision, from
        PlayerWalkState/PlayerPotWalkState.
        """
        self.shifting = True
        self.next_room = self._create_next_room(shift_x, shift_y)

        # Start all doors in next room as open until we get in.
        for doorway in self.next_room.doorways:
            doorway.open = True

        self.next_room.adjacent_offset_x = shift_x
        self.next_room.adjacent_offset_y = shift_y

        player_x, player_y = self.player.x, self.player.y

        if shift_x > 0:
            player_x = settings.VIRTUAL_WIDTH + (
                settings.MAP_RENDER_OFFSET_X + settings.TILE_SIZE
            )
        elif shift_x < 0:
            player_x = -settings.VIRTUAL_WIDTH + (
                settings.MAP_RENDER_OFFSET_X
                + settings.MAP_WIDTH * settings.TILE_SIZE
                - settings.TILE_SIZE
                - self.player.width
            )
        elif shift_y > 0:
            player_y = settings.VIRTUAL_HEIGHT + (
                settings.MAP_RENDER_OFFSET_Y + self.player.height / 2
            )
        else:
            player_y = -settings.VIRTUAL_HEIGHT + settings.MAP_RENDER_OFFSET_Y + (
                settings.MAP_HEIGHT * settings.TILE_SIZE
                - settings.TILE_SIZE
                - self.player.height
            )

        # Tween the camera in whichever direction the new room is in, as
        # well as the player to be at the opposite door in the next room,
        # walking through the wall (whose art will cover them there).
        to_tween = [
            (self, {"camera_x": shift_x, "camera_y": shift_y}),
            (self.player, {"x": player_x, "y": player_y}),
        ]

        pot = getattr(self.player.state_machine.current, "pot", None)

        if pot is not None:
            to_tween.append((pot, {"x": player_x, "y": player_y - pot.height / 2}))

        Timer.tween(1, to_tween, on_finish=self._finish_shifting_and_place_player)

    def _finish_shifting_and_place_player(self) -> None:
        shift_x = self.camera_x
        shift_y = self.camera_y

        self._finish_shifting()

        # Reset player to the correct location in the room.
        if shift_x < 0:
            self.player.x = (
                settings.MAP_RENDER_OFFSET_X
                + settings.MAP_WIDTH * settings.TILE_SIZE
                - settings.TILE_SIZE
                - self.player.width
            )
            self.player.direction = "left"
        elif shift_x > 0:
            self.player.x = settings.MAP_RENDER_OFFSET_X + settings.TILE_SIZE
            self.player.direction = "right"
        elif shift_y < 0:
            self.player.y = (
                settings.MAP_RENDER_OFFSET_Y
                + settings.MAP_HEIGHT * settings.TILE_SIZE
                - settings.TILE_SIZE
                - self.player.height
            )
            self.player.direction = "up"
        else:
            self.player.y = settings.MAP_RENDER_OFFSET_Y + self.player.height / 2
            self.player.direction = "down"

        # Close all doors in the room we just entered (self.current_room
        # was just swapped to it by _finish_shifting above) — they were
        # only forced open so the player could visually walk through the
        # wall opening during the transition.
        for doorway in self.current_room.doorways:
            doorway.open = False

        # Avoid receiving damage right as we enter the new room.
        self.player.go_invulnerable(1)

        settings.SOUNDS["door"].play()

    def _finish_shifting(self) -> None:
        """
        Resets a few variables needed to perform a camera shift and swaps
        the next and current room.
        """
        self.camera_x = 0
        self.camera_y = 0
        self.shifting = False
        self.current_room = self.next_room
        self.next_room = None
        self.current_room.adjacent_offset_x = 0
        self.current_room.adjacent_offset_y = 0

    def update(self, dt: float) -> None:
        # Pause updating if we're in the middle of shifting.
        if not self.shifting:
            self.current_room.update(dt)
        else:
            # Still update the player animation if we're shifting rooms.
            if self.player.current_animation:
                self.player.current_animation.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        # Applied directly to every draw call (rather than composited
        # through an intermediate surface) so a room positioned a full
        # screen away by its adjacent offset isn't clipped away by an
        # equally screen-sized buffer before the camera pans over to it.
        offset_x = -math.floor(self.camera_x)
        offset_y = -math.floor(self.camera_y)

        self.current_room.render(surface, offset_x, offset_y)

        if self.next_room:
            self.next_room.render(surface, offset_x, offset_y)
