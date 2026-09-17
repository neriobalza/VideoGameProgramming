"""Personaje vinculado exclusivamente a un mando o al teclado."""

import pygame

import settings


class Player:
    def __init__(self, input_source: int | str) -> None:
        self.input_source = input_source
        self.number: int | None = None
        self.position = pygame.Vector2(settings.VIRTUAL_WIDTH / 2, 260)
        self.direction = pygame.Vector2()
        self.keyboard_keys: set[int] = set()

    @property
    def uses_keyboard(self) -> bool:
        return self.input_source == settings.KEYBOARD_INPUT

    @property
    def controller_id(self) -> int | None:
        return None if self.uses_keyboard else self.input_source

    def is_connected(self, controllers) -> bool:
        return self.uses_keyboard or controllers.is_connected(self.controller_id)

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

    def update(self, dt: float) -> None:
        direction = self.direction.copy()
        if direction.length_squared() > 1:
            direction.normalize_ip()
        self.position += direction * settings.PLAYER_SPEED * dt
        half_size = settings.PLAYER_SIZE / 2
        self.position.x = max(half_size, min(settings.VIRTUAL_WIDTH - half_size, self.position.x))
        self.position.y = max(half_size, min(settings.VIRTUAL_HEIGHT - half_size, self.position.y))

    def render(self, surface, color=None) -> None:
        color = color or settings.PLAYER_COLORS.get(self.number, settings.MUTED_COLOR)
        rect = pygame.Rect(0, 0, settings.PLAYER_SIZE, settings.PLAYER_SIZE)
        rect.center = (round(self.position.x), round(self.position.y))
        pygame.draw.rect(surface, color, rect)
