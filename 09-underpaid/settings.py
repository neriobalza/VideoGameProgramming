"""Configuración de pantalla, controles y colores de Underpaid."""

import pygame
from functools import lru_cache
from pathlib import Path

from gale.input_handler import InputHandler


TITLE = "Underpaid"
FPS = 60

# La lógica y los menús siempre se dibujan en estas coordenadas.
VIRTUAL_WIDTH = 640
VIRTUAL_HEIGHT = 480

# Todas las resoluciones de ventana tienen proporción 4:3.
WINDOW_RESOLUTIONS = (
    (640, 480),
    (960, 720),
    (1280, 960),
    (1920, 1440),
)

# Cambia este índice (0–3) para elegir la resolución al iniciar.
DEFAULT_RESOLUTION_INDEX = 0
WINDOW_WIDTH, WINDOW_HEIGHT = WINDOW_RESOLUTIONS[DEFAULT_RESOLUTION_INDEX]

# True para iniciar en pantalla completa; False para iniciar en ventana.
FULLSCREEN = False

BACKGROUND_COLOR = (23, 27, 38)
PANEL_COLOR = (35, 41, 56)
TEXT_COLOR = (235, 238, 245)
MUTED_COLOR = (164, 174, 194)
ACCENT_COLOR = (246, 190, 76)

PLAYER_COLORS = {1: (82, 169, 255), 2: (255, 116, 128)}
PLAYER_SPEED = 180
PLAYER_FRAME_WIDTH = 32
PLAYER_FRAME_HEIGHT = 64
PLAYER_FRAME_INTERVAL = 0.12
STICK_DEADZONE = 0.2
SELECTION_THRESHOLD = 0.6
KEYBOARD_INPUT = "keyboard"

BASE_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def load_player_frames() -> dict[str, tuple[pygame.Surface, ...]]:
    """Carga una vez el spritesheet; cada jugador conserva su propio reloj."""
    sheet = pygame.image.load(BASE_DIR / "assets" / "graphics" / "player_walk.png").convert_alpha()
    return {
        direction: tuple(
            sheet.subsurface(pygame.Rect(
                column * PLAYER_FRAME_WIDTH, row * PLAYER_FRAME_HEIGHT,
                PLAYER_FRAME_WIDTH, PLAYER_FRAME_HEIGHT,
            )).copy()
            for column in range(4)
        )
        for row, direction in enumerate(("down", "right", "up", "left"))
    }


def create_fonts() -> dict[str, pygame.font.Font]:
    """Se llama después de que Gale inicializa Pygame."""
    return {
        "small": pygame.font.Font(None, 22),
        "medium": pygame.font.Font(None, 30),
        "large": pygame.font.Font(None, 64),
    }


for key, action in (
    (pygame.K_UP, "up"),
    (pygame.K_w, "keyboard_up"),
    (pygame.K_DOWN, "down"),
    (pygame.K_s, "keyboard_down"),
    (pygame.K_LEFT, "left"),
    (pygame.K_a, "keyboard_left"),
    (pygame.K_RIGHT, "right"),
    (pygame.K_d, "keyboard_right"),
    (pygame.K_RETURN, "confirm"),
    (pygame.K_SPACE, "confirm"),
    (pygame.K_ESCAPE, "back"),
    (pygame.K_DELETE, "cancel"),
    (pygame.K_BACKSPACE, "cancel"),
):
    InputHandler.set_keyboard_action(key, action)

InputHandler.set_mouse_click_action(pygame.BUTTON_LEFT, "click")
InputHandler.set_mouse_motion_action(None, "mouse_move")

# Botones y ejes estandarizados por el mapeo de SDL para mandos Xbox.
for button, action in (
    (pygame.CONTROLLER_BUTTON_A, "pad_a"),
    (pygame.CONTROLLER_BUTTON_B, "pad_b"),
    (pygame.CONTROLLER_BUTTON_DPAD_UP, "pad_up"),
    (pygame.CONTROLLER_BUTTON_DPAD_DOWN, "pad_down"),
    (pygame.CONTROLLER_BUTTON_DPAD_LEFT, "pad_left"),
    (pygame.CONTROLLER_BUTTON_DPAD_RIGHT, "pad_right"),
):
    InputHandler.set_gamepad_button_action(button, action)

InputHandler.set_gamepad_axis_action(pygame.CONTROLLER_AXIS_LEFTX, "pad_x")
InputHandler.set_gamepad_axis_action(pygame.CONTROLLER_AXIS_LEFTY, "pad_y")
