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

    def key(self, key, pressed=True):
        InputHandler.handle_input(pygame.event.Event(
            pygame.KEYDOWN if pressed else pygame.KEYUP,
            key=key, mod=0, unicode='',
        ))

    def key_tap(self, key):
        self.key(key)
        self.key(key, pressed=False)

    def keyboard_play(self, number=1):
        self.devices = self.devices[:1]
        self.selection()
        self.key_tap(pygame.K_RETURN)
        self.key_tap(pygame.K_LEFT if number == 1 else pygame.K_RIGHT)
        self.key_tap(pygame.K_RETURN)
        self.button(71)
        self.move_choice(71, 1 if number == 1 else -1)
        self.button(71)
        self.assertIsInstance(self.game.state_machine.current, PlayState)
        return self.game.state_machine.current

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

    def test_play_draws_sprite_and_supports_all_movement_directions(self):
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
        p1.direction.update(0, 1)
        p1.update(0.01)
        p1.stop()
        p1.position.update(160, 240)
        p1.render(surface)
        expected = pygame.Surface((640, 480))
        expected.fill(settings.BACKGROUND_COLOR)
        sheet = pygame.image.load(settings.BASE_DIR / 'assets' / 'graphics' / 'player_walk.png')
        expected.blit(sheet, (144, 208), pygame.Rect(0, 0, 32, 64))
        self.assertEqual(pygame.image.tobytes(surface, 'RGB'), pygame.image.tobytes(expected, 'RGB'))

    def test_walk_animation_is_independent_and_stops_in_last_direction(self):
        state = self.play()
        p1, p2 = state.players[1], state.players[2]
        self.axis(71, 1)
        self.game.update(settings.PLAYER_FRAME_INTERVAL)
        self.assertEqual(p1.facing, 'right')
        self.assertEqual(p1.animation.current_frame_index, 1)
        self.assertEqual(p2.facing, 'down')
        self.assertEqual(p2.animation.current_frame_index, 0)
        self.assertIsNot(p1.animation, p2.animation)
        self.axis(71, 0)
        self.game.update(settings.PLAYER_FRAME_INTERVAL * 2)
        self.assertEqual(p1.facing, 'right')
        self.assertEqual(p1.animation.current_frame_index, 0)

    def test_walk_uses_correct_spritesheet_row_for_each_direction(self):
        player = self.play().players[1]
        sheet = pygame.image.load(settings.BASE_DIR / 'assets' / 'graphics' / 'player_walk.png')
        for dx, dy, facing, row in ((0, 1, 'down', 0), (1, 0, 'right', 1),
                                    (0, -1, 'up', 2), (-1, 0, 'left', 3)):
            self.axis(71, dx)
            self.axis(71, dy, pygame.CONTROLLER_AXIS_LEFTY)
            self.game.update(settings.PLAYER_FRAME_INTERVAL)
            self.assertEqual(player.facing, facing)
            frame = player.animation.get_current_frame()
            expected = sheet.subsurface(pygame.Rect(32, row * 64, 32, 64))
            self.assertEqual(pygame.image.tobytes(frame, 'RGBA'), pygame.image.tobytes(expected, 'RGBA'))

    def test_enter_registers_keyboard_once_and_space_does_not_register(self):
        self.devices.clear()
        self.key_tap(pygame.K_RETURN)  # Open selection from main menu.
        state = self.game.state_machine.current
        self.assertIsInstance(state, PlayerSelectState)
        self.assertEqual(state.participants, {})
        self.key_tap(pygame.K_SPACE)
        self.key(pygame.K_RETURN, pressed=False)
        self.assertEqual(state.participants, {})
        self.key(pygame.K_RETURN)
        self.key(pygame.K_RETURN)  # Simulate repeated keydown while held.
        self.assertEqual(set(state.participants), {settings.KEYBOARD_INPUT})
        self.assertTrue(state.participants[settings.KEYBOARD_INPUT].uses_keyboard)
        self.assertEqual(state.players, {})

    def test_keyboard_arrows_browse_center_and_wasd_do_not_choose(self):
        state = self.selection()
        self.key_tap(pygame.K_RETURN)
        source = settings.KEYBOARD_INPUT
        self.key_tap(pygame.K_a)
        self.assertIsNone(state.choices[source])
        self.key_tap(pygame.K_LEFT)
        self.assertEqual(state.choices[source], 1)
        self.key(pygame.K_RIGHT)
        self.key(pygame.K_RIGHT)
        self.assertIsNone(state.choices[source])
        self.key(pygame.K_RIGHT, pressed=False)
        self.key_tap(pygame.K_RIGHT)
        self.assertEqual(state.choices[source], 2)
        self.assertEqual(state.players, {})

    def test_delete_cancels_only_keyboard_confirmation_and_frees_side(self):
        state = self.selection()
        self.key_tap(pygame.K_RETURN)
        self.key_tap(pygame.K_LEFT)
        self.key_tap(pygame.K_RETURN)
        self.button(71)
        self.move_choice(71, -1)
        self.assertIsNone(state.choices[71])
        self.button(71, pygame.CONTROLLER_BUTTON_B)
        self.assertIn(1, state.players)
        self.key(pygame.K_DELETE, pressed=False)
        self.assertIn(1, state.players)
        self.key_tap(pygame.K_DELETE)
        self.assertEqual(state.players, {})
        self.assertIsNone(state.participants[settings.KEYBOARD_INPUT].number)
        self.move_choice(71, -1)
        self.button(71)
        self.assertEqual(state.players[1].controller_id, 71)
        self.key_tap(pygame.K_RIGHT)
        self.key_tap(pygame.K_RIGHT)
        self.key_tap(pygame.K_RETURN)
        self.assertIsInstance(self.game.state_machine.current, PlayState)
        self.assertTrue(self.game.state_machine.current.players[2].uses_keyboard)

    def test_one_controller_and_keyboard_can_choose_either_character(self):
        for number in (1, 2):
            state = self.keyboard_play(number)
            self.assertTrue(state.players[number].uses_keyboard)
            self.assertEqual(state.players[3 - number].controller_id, 71)
            self.game.state_machine.change('main_menu')

    def test_wasd_moves_only_keyboard_player_and_release_stops_movement(self):
        state = self.keyboard_play()
        keyboard, gamepad = state.players[1], state.players[2]
        gamepad_position = gamepad.position.copy()
        for key, dx, dy in ((pygame.K_w, 0, -1), (pygame.K_a, -1, 0),
                            (pygame.K_s, 0, 1), (pygame.K_d, 1, 0)):
            position = keyboard.position.copy()
            self.key(key)
            self.game.update(0.1)
            self.assertEqual(keyboard.position - position, pygame.Vector2(dx, dy) * 18)
            self.assertEqual(gamepad.position, gamepad_position)
            self.key(key, pressed=False)
            position = keyboard.position.copy()
            self.game.update(0.1)
            self.assertEqual(keyboard.position, position)
        self.key_tap(pygame.K_RIGHT)
        self.game.update(0.1)
        self.assertEqual(keyboard.position, position)
        self.axis(71, 1)
        self.game.update(0.1)
        self.assertEqual(keyboard.position, position)
        self.assertGreater(gamepad.position.x, gamepad_position.x)

    def test_keyboard_diagonals_and_opposing_keys(self):
        keyboard = self.keyboard_play().players[1]
        position = keyboard.position.copy()
        self.key(pygame.K_w)
        self.key(pygame.K_d)
        self.game.update(0.1)
        movement = keyboard.position - position
        self.assertLess(movement.y, 0)
        self.assertGreater(movement.x, 0)
        self.assertAlmostEqual(movement.length(), 18)
        self.key(pygame.K_a)
        self.assertEqual(keyboard.direction.x, 0)
        self.key(pygame.K_s)
        self.assertEqual(keyboard.direction, pygame.Vector2())
        self.key(pygame.K_d, pressed=False)
        self.assertEqual(keyboard.direction.x, -1)
        self.key(pygame.K_w, pressed=False)
        self.assertEqual(keyboard.direction.y, 1)

    def test_gamepad_disconnect_preserves_keyboard_player(self):
        state = self.keyboard_play()
        keyboard = state.players[1]
        self.key(pygame.K_w)
        self.devices.clear()
        self.game.update(0.1)
        state = self.game.state_machine.current
        self.assertIsInstance(state, PlayerSelectState)
        self.assertEqual(state.players, {1: keyboard})
        self.assertEqual(keyboard.direction, pygame.Vector2())
        self.game.update(0.1)
        self.assertIn(settings.KEYBOARD_INPUT, state.participants)
        self.key_tap(pygame.K_DELETE)
        self.assertEqual(state.players, {})

    def test_keyboard_cannot_join_when_two_controllers_are_participating(self):
        state = self.selection()
        self.button(71)
        self.button(203)
        self.key_tap(pygame.K_RETURN)
        self.assertEqual(set(state.participants), {71, 203})
        self.assertNotIn(settings.KEYBOARD_INPUT, state.choices)


if __name__ == "__main__":
    unittest.main()
