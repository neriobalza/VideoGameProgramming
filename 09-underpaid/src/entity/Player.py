"""Personaje vinculado exclusivamente a un mando o al teclado."""

import pygame
from gale.animation import Animation

import settings


class Player:
    def __init__(self, input_source: int | str) -> None:
        self.input_source = input_source
        self.number: int | None = None
        self.position = pygame.Vector2(settings.VIRTUAL_WIDTH / 2, 260)
        self.direction = pygame.Vector2()
        self.keyboard_keys: set[int] = set()
        self.facing = "down"
        self.animations = {
            direction: Animation(frames, settings.PLAYER_FRAME_INTERVAL)
            for direction, frames in settings.load_player_frames().items()
        }
        self.animation = self.animations[self.facing]

    @property
    def uses_keyboard(self) -> bool:
        return self.input_source == settings.KEYBOARD_INPUT

    @property
    def controller_id(self) -> int | None:
        return None if self.uses_keyboard else self.input_source

    def is_connected(self, controllers) -> bool:
        return self.uses_keyboard or controllers.is_connected(self.controller_id)

    @property
    def hitbox(self) -> pygame.Rect:
        """Área de apoyo en el suelo; la cabeza puede sobresalir sobre paredes."""
        return pygame.Rect(
            round(self.position.x - settings.PLAYER_COLLISION_WIDTH / 2),
            round(self.position.y + settings.PLAYER_FRAME_HEIGHT / 2 - settings.PLAYER_COLLISION_HEIGHT),
            settings.PLAYER_COLLISION_WIDTH,
            settings.PLAYER_COLLISION_HEIGHT,
        )

    def select(self, number: int) -> None:
        if self.number is not None:
            raise ValueError("El jugador ya tiene un lado asignado")
        if number not in (1, 2):
            raise ValueError("Sólo existen los jugadores 1 y 2")
        self.number = number
        self.position.update(settings.VIRTUAL_WIDTH * (0.25 if number == 1 else 0.75), 260)
        self.stop()

    def stop(self) -> None:
        self.direction.update(0, 0)
        self.keyboard_keys.clear()
        self.animation.reset()

    def unselect(self) -> None:
        self.number = None
        self.stop()

    def on_input(self, input_id, input_data) -> None:
        if self.number is None:
            return
        if self.uses_keyboard:
            if not input_id.startswith("keyboard_") or not hasattr(input_data, "key"):
                return
            key = input_data.key
            if key not in (pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d):
                return
            if input_data.pressed:
                self.keyboard_keys.add(key)
            else:
                self.keyboard_keys.discard(key)
            self.direction.update(
                int(pygame.K_d in self.keyboard_keys) - int(pygame.K_a in self.keyboard_keys),
                int(pygame.K_s in self.keyboard_keys) - int(pygame.K_w in self.keyboard_keys),
            )
            return
        if getattr(input_data, "gamepad_id", None) != self.controller_id:
            return
        if input_id not in ("pad_x", "pad_y"):
            return
        value = input_data.value
        value = 0 if abs(value) <= settings.STICK_DEADZONE else value
        if input_id == "pad_x":
            self.direction.x = value
        else:
            self.direction.y = value

    def update(self, dt: float, bounds: pygame.Rect | None = None) -> None:
        direction = self.direction.copy()
        # Limitar la longitud a 1 iguala la velocidad máxima en ejes y
        # diagonales, conservando el movimiento lento del joystick analógico.
        if direction.length_squared() > 1:
            direction.normalize_ip()
        self.position += direction * settings.PLAYER_SPEED * dt
        half_width = settings.PLAYER_FRAME_WIDTH / 2
        half_height = settings.PLAYER_FRAME_HEIGHT / 2
        if bounds is None:
            self.position.x = max(half_width, min(settings.VIRTUAL_WIDTH - half_width, self.position.x))
            self.position.y = max(half_height, min(settings.VIRTUAL_HEIGHT - half_height, self.position.y))
        else:
            # El límite de la sala afecta al apoyo de los pies, dejando libre
            # la parte superior del sprite para dibujarse sobre la pared.
            half_collision_width = settings.PLAYER_COLLISION_WIDTH / 2
            top_offset = half_height - settings.PLAYER_COLLISION_HEIGHT
            self.position.x = max(bounds.left + half_collision_width, min(bounds.right - half_collision_width, self.position.x))
            self.position.y = max(bounds.top - top_offset, min(bounds.bottom - half_height, self.position.y))
        if direction.length_squared() == 0:
            self.animation.reset()
            return
        if abs(direction.x) > abs(direction.y):
            facing = "right" if direction.x > 0 else "left"
        else:
            facing = "down" if direction.y > 0 else "up"
        if facing != self.facing:
            self.facing = facing
            self.animation = self.animations[facing]
            self.animation.reset()
        self.animation.update(dt)

    def render(self, surface) -> None:
        frame = self.animation.get_current_frame()
        rect = frame.get_rect(center=(round(self.position.x), round(self.position.y)))
        surface.blit(frame, rect)
