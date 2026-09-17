"""Personaje vinculado exclusivamente al ID de instancia de un mando."""

import pygame

import settings


class Player:
    def __init__(self, controller_id: int) -> None:
        self.controller_id = controller_id
        self.number: int | None = None
        self.position = pygame.Vector2(settings.VIRTUAL_WIDTH / 2, 260)
        self.direction = pygame.Vector2()

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

    def unselect(self) -> None:
        self.number = None
        self.stop()

    def on_input(self, input_id, input_data) -> None:
        if self.number is None or getattr(input_data, "gamepad_id", None) != self.controller_id:
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
