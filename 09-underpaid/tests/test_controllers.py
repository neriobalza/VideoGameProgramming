"""Pruebas de propiedad y selección con eventos SDL y dispositivos simulados."""

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_RENDER_DRIVER", "software")

import pygame
from gale.input_handler import InputHandler

from src.Underpaid import Underpaid
from src.states.game.PlayerSelectState import PlayerSelectState
from src.states.game.PlayState import PlayState
import settings


class Device:
    def __init__(self, instance_id):
        self.id = instance_id
        self.closed = False

    def get_instance_id(self):
        return self.id

    def quit(self):
        self.closed = True


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.devices = [Device(71), Device(203)]
        for target, replacement in (
            ("pygame.joystick.get_count", lambda: len(self.devices)),
            ("pygame.joystick.Joystick", lambda index: self.devices[index]),
            ("pygame._sdl2.controller.is_controller", lambda index: True),
            ("pygame._sdl2.controller.Controller", lambda index: self.devices[index]),
        ):
            patcher = patch(target, side_effect=replacement)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.game = Underpaid()
        self.addCleanup(self.game.quit)

    def button(self, instance_id, button=pygame.CONTROLLER_BUTTON_A, pressed=True):
        InputHandler.handle_input(pygame.event.Event(
            pygame.CONTROLLERBUTTONDOWN if pressed else pygame.CONTROLLERBUTTONUP,
            instance_id=instance_id, button=button,
        ))

    def axis(self, instance_id, value, axis=pygame.CONTROLLER_AXIS_LEFTX):
        InputHandler.handle_input(pygame.event.Event(
            pygame.CONTROLLERAXISMOTION, instance_id=instance_id,
            axis=axis, value=round(value * 32767),
        ))

    def selection(self):
        self.button(71)
        self.assertIsInstance(self.game.state_machine.current, PlayerSelectState)
        return self.game.state_machine.current

    def move_choice(self, instance_id, value):
        self.axis(instance_id, 0)
        self.axis(instance_id, value)
        self.axis(instance_id, 0)

    def play(self, reverse=False):
        self.selection()
        self.button(71)
        self.button(203)
        self.move_choice(71, 1 if reverse else -1)
        self.move_choice(203, -1 if reverse else 1)
        self.button(71)
        self.button(203)
        self.assertIsInstance(self.game.state_machine.current, PlayState)
        return self.game.state_machine.current

    def test_join_requires_a_on_selection_and_ignores_releases(self):
        state = self.selection()
        self.assertEqual(state.participants, {})
        self.axis(71, -1)
        self.button(71, pressed=False)
        self.assertEqual(state.participants, {})
        self.button(71)
        self.button(71)
        self.button(203)
        self.assertEqual(set(state.participants), {71, 203})
        self.assertEqual(state.players, {})
        self.assertTrue(all(p.position.x == 320 for p in state.participants.values()))

    def test_confirmed_side_cannot_be_taken_and_requires_b_to_change(self):
        state = self.selection()
        self.button(71)
        self.button(203)
        self.move_choice(71, -1)
        self.button(71)
        self.move_choice(203, -1)
        self.assertEqual(state.players[1].controller_id, 71)
        self.assertIsNone(state.participants[203].number)
        self.move_choice(71, 1)
        self.assertEqual(state.players[1].controller_id, 71)
        self.assertNotIn(2, state.players)
        self.move_choice(203, 1)
        self.assertIsInstance(self.game.state_machine.current, PlayerSelectState)
        self.button(203)
        self.assertIsInstance(self.game.state_machine.current, PlayState)

    def test_either_controller_can_choose_either_player(self):
        state = self.play(reverse=True)
        self.assertEqual(state.players[1].controller_id, 203)
        self.assertEqual(state.players[2].controller_id, 71)

    def test_selection_ignores_drift_and_vertical_axis(self):
        state = self.selection()
        self.button(71)
        self.axis(71, 0.3)
        self.axis(71, 1, pygame.CONTROLLER_AXIS_LEFTY)
        self.assertEqual(state.players, {})

    def test_only_owner_moves_each_player_and_keyboard_does_not_move(self):
        state = self.play()
        p1, p2 = state.players[1], state.players[2]
        start1, start2 = p1.position.copy(), p2.position.copy()
        self.axis(71, 1)
        self.game.update(0.1)
        self.assertGreater(p1.position.x, start1.x)
        self.assertEqual(p2.position, start2)
        self.axis(71, 0)
        start1 = p1.position.copy()
        self.axis(203, -1, pygame.CONTROLLER_AXIS_LEFTY)
        self.game.update(0.1)
        self.assertEqual(p1.position, start1)
        self.assertLess(p2.position.y, start2.y)
        self.axis(203, 0, pygame.CONTROLLER_AXIS_LEFTY)
        InputHandler.handle_input(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_RIGHT, mod=0, unicode='',
        ))
        start2 = p2.position.copy()
        self.game.update(0.1)
        self.assertEqual(p1.position, start1)
        self.assertEqual(p2.position, start2)

    def test_extra_or_unknown_controller_cannot_join_or_control(self):
        state = self.selection()
        self.button(71)
        self.button(203)
        self.devices.append(Device(999))
        self.button(999)
        self.assertEqual(set(state.participants), {71, 203})
        self.axis(71, -1)
        self.axis(203, 1)
        self.button(71)
        self.button(203)
        players = self.game.state_machine.current.players
        positions = {n: p.position.copy() for n, p in players.items()}
        self.axis(999, 1)
        self.axis(12345, -1)
        self.game.update(0.1)
        self.assertEqual(positions, {n: p.position for n, p in players.items()})

    def test_deadzone_and_screen_boundaries(self):
        state = self.play()
        p1 = state.players[1]
        position = p1.position.copy()
        self.axis(71, 0.1)
        self.game.update(0.1)
        self.assertEqual(p1.position, position)
        self.axis(71, 1)
        self.axis(71, 1, pygame.CONTROLLER_AXIS_LEFTY)
        self.game.update(100)
        self.assertLess(p1.position.x, 640)
        self.assertLess(p1.position.y, 480)

    def test_disconnect_frees_only_owner_slot_and_reconnect_requires_join(self):
        state = self.play()
        survivor = state.players[2]
        self.axis(203, 1)
        disconnected = self.devices.pop(0)
        self.game.update(0.1)
        state = self.game.state_machine.current
        self.assertIsInstance(state, PlayerSelectState)
        self.assertEqual(state.players, {2: survivor})
        self.assertEqual(survivor.direction.length_squared(), 0)
        self.assertTrue(disconnected.closed)
        self.devices.append(Device(407))
        self.game.update(0)
        self.axis(407, -1)
        self.assertNotIn(1, state.players)
        self.button(407)
        self.move_choice(407, 1)
        self.assertNotIn(1, state.players)
        self.move_choice(407, -1)
        self.assertIsInstance(self.game.state_machine.current, PlayerSelectState)
        self.button(407)
        self.assertIsInstance(self.game.state_machine.current, PlayState)
        self.assertEqual(self.game.state_machine.current.players[1].controller_id, 407)

    def test_disconnect_waiting_controller_allows_replacement(self):
        state = self.selection()
        self.button(71)
        self.button(203)
        self.devices.pop(0)
        self.devices.append(Device(407))
        self.button(407)
        self.assertEqual(set(state.participants), {203, 407})

    def test_selection_and_play_render_at_virtual_resolution(self):
        state = self.selection()
        self.button(71)
        self.button(203)
        self.game._Game__render()
        self.axis(71, -1)
        self.game._Game__render()
        self.axis(203, 1)
        self.button(71)
        self.button(203)
        self.game._Game__render()
        self.assertEqual(self.game.render_surface.get_size(), (640, 480))

    def test_browsing_visits_both_characters_and_center_without_confirming(self):
        state = self.selection()
        self.button(71)
        for direction, expected in ((-1, 1), (1, None), (1, 2), (-1, None), (-1, 1)):
            self.move_choice(71, direction)
            self.assertEqual(state.choices[71], expected)
            self.assertEqual(state.players, {})
            self.assertIsNone(state.participants[71].number)

    def test_held_stick_does_not_skip_center(self):
        state = self.selection()
        self.button(71)
        self.move_choice(71, -1)
        self.axis(71, 0.8)
        self.axis(71, 0.9)
        self.axis(71, 1)
        self.assertIsNone(state.choices[71])
        self.move_choice(71, 1)
        self.assertEqual(state.choices[71], 2)

    def test_b_releases_character_and_allows_switching(self):
        state = self.selection()
        self.button(71)
        self.button(203)
        self.move_choice(71, -1)
        self.button(71)
        self.button(203, pygame.CONTROLLER_BUTTON_B)
        self.assertIn(1, state.players)  # B only cancels its own selection.
        self.button(71, pygame.CONTROLLER_BUTTON_B, pressed=False)
        self.assertIn(1, state.players)
        self.button(71, pygame.CONTROLLER_BUTTON_B)
        self.assertEqual(state.players, {})
        self.assertIsNone(state.participants[71].number)
        self.move_choice(71, 1)
        self.assertIsNone(state.choices[71])
        self.move_choice(71, 1)
        self.assertEqual(state.choices[71], 2)
        self.button(71)
        self.move_choice(203, -1)
        self.button(203)
        self.assertIsInstance(self.game.state_machine.current, PlayState)
        self.assertEqual(self.game.state_machine.current.players[2].controller_id, 71)

    def test_two_previews_do_not_start_game_and_cannot_confirm_same_character(self):
        state = self.selection()
        self.button(71)
        self.button(203)
        self.move_choice(71, -1)
        self.move_choice(203, -1)
        self.assertEqual(state.choices, {71: 1, 203: 1})
        self.assertEqual(state.players, {})
        self.button(71, pressed=False)
        self.assertEqual(state.players, {})
        self.button(71)
        self.assertIsNone(state.choices[203])
        self.button(203)
        self.assertEqual(set(state.players), {1})
        self.assertIsInstance(self.game.state_machine.current, PlayerSelectState)

    def test_play_draws_squares_and_supports_all_movement_directions(self):
        state = self.play()
        p1 = state.players[1]
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)):
            start = p1.position.copy()
            self.axis(71, dx)
            self.axis(71, dy, pygame.CONTROLLER_AXIS_LEFTY)
            self.game.update(0.1)
            movement = p1.position - start
            self.assertEqual(movement.x > 0, dx > 0)
            self.assertEqual(movement.x < 0, dx < 0)
            self.assertEqual(movement.y > 0, dy > 0)
            self.assertEqual(movement.y < 0, dy < 0)
            # SDL representa el extremo positivo del eje como 32767/32768.
            self.assertAlmostEqual(movement.length(), settings.PLAYER_SPEED * 0.1, delta=0.001)
        surface = pygame.Surface((640, 480))
        surface.fill(settings.BACKGROUND_COLOR)
        p1.position.update(160, 240)
        p1.render(surface)
        self.assertEqual(surface.get_at((144, 224))[:3], settings.PLAYER_COLORS[1])
        self.assertEqual(surface.get_at((175, 255))[:3], settings.PLAYER_COLORS[1])
        self.assertEqual(surface.get_at((176, 256))[:3], settings.BACKGROUND_COLOR)


if __name__ == "__main__":
    unittest.main()
