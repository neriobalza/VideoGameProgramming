"""Exploración de lados, confirmación con A y cancelación con B."""

import pygame
from gale.state import BaseState

import settings
from src.entity.Player import Player
from src.gui.Menu import draw_text


class PlayerSelectState(BaseState):
    def __init__(self, state_machine, game):
        super().__init__(state_machine)
        self.game = game

    def enter(self, players=None) -> None:
        # Sólo las elecciones confirmadas reservan un personaje.
        self.players = dict(players or {})
        self.participants = {p.controller_id: p for p in self.players.values()}
        self.choices = {p.controller_id: p.number for p in self.players.values()}
        self.stick_ready = {instance_id: True for instance_id in self.participants}
        for player in self.participants.values():
            player.stop()
        self.message = ""

    def update(self, dt: float) -> None:
        for instance_id in list(self.participants):
            if not self.game.controllers.is_connected(instance_id):
                player = self.participants.pop(instance_id)
                self.players.pop(player.number, None)
                self.choices.pop(instance_id)
                self.stick_ready.pop(instance_id)
                self.message = "Mando desconectado. Pulsa A para entrar."

    def join(self, instance_id: int) -> None:
        if len(self.participants) >= 2:
            self.message = "Ya hay dos mandos participando."
            return
        self.participants[instance_id] = Player(instance_id)
        self.choices[instance_id] = None
        self.stick_ready[instance_id] = True
        self.message = "Elige un personaje con el joystick y confirma con A."

    def move_choice(self, instance_id: int, value: float) -> None:
        # Una inclinación avanza una posición; soltar rearma el joystick.
        if abs(value) <= settings.STICK_DEADZONE:
            self.stick_ready[instance_id] = True
            return
        if abs(value) < settings.SELECTION_THRESHOLD or not self.stick_ready[instance_id]:
            return
        self.stick_ready[instance_id] = False
        if self.participants[instance_id].number is not None:
            self.message = "Pulsa B para cambiar tu personaje."
            return
        positions = (1, None, 2)
        current = positions.index(self.choices[instance_id])
        destination = max(0, min(2, current + (-1 if value < 0 else 1)))
        choice = positions[destination]
        if choice in self.players:
            self.message = f"Player {choice} ya está confirmado por el otro mando."
            return
        self.choices[instance_id] = choice
        self.message = "Pulsa A para confirmar." if choice else "Elige izquierda o derecha."

    def confirm(self, instance_id: int) -> None:
        player = self.participants[instance_id]
        if player.number is not None:
            return
        choice = self.choices[instance_id]
        if choice is None:
            self.message = "Elige un personaje antes de confirmar."
            return
        if choice in self.players:
            self.message = f"Player {choice} ya está confirmado por el otro mando."
            return
        player.select(choice)
        self.players[choice] = player
        # Si ambos exploraban el mismo personaje, sólo el primero lo reserva.
        for other_id, other_choice in self.choices.items():
            if other_id != instance_id and other_choice == choice:
                self.choices[other_id] = None
        self.message = f"Player {choice} confirmado. B permite volver a elegir."
        if len(self.players) == 2:
            self.state_machine.change("play", players=self.players)

    def cancel(self, instance_id: int) -> None:
        player = self.participants[instance_id]
        self.players.pop(player.number, None)
        player.unselect()
        self.message = "Puedes seguir escogiendo con el joystick. A confirma."

    def on_input(self, input_id, input_data) -> None:
        self.update(0)
        if input_id == "back" and input_data.pressed:
            self.state_machine.change("main_menu")
            return
        instance_id = getattr(input_data, "gamepad_id", None)
        if instance_id is None or not self.game.controllers.is_connected(instance_id):
            return
        if input_id == "pad_a" and input_data.pressed:
            if instance_id not in self.participants:
                self.join(instance_id)
            else:
                self.confirm(instance_id)
        elif instance_id in self.participants:
            if input_id == "pad_b" and input_data.pressed:
                self.cancel(instance_id)
            elif input_id == "pad_x":
                self.move_choice(instance_id, input_data.value)

    def render(self, surface) -> None:
        surface.fill(settings.BACKGROUND_COLOR)
        for number, x in ((1, 20), (2, 380)):
            rect = pygame.Rect(x, 165, 240, 220)
            pygame.draw.rect(surface, settings.PANEL_COLOR, rect, border_radius=10)
            pygame.draw.rect(surface, settings.PLAYER_COLORS[number], rect, width=2, border_radius=10)
            label = "Confirmado" if number in self.players else "Disponible"
            image = self.game.fonts["small"].render(f"Player {number} · {label}", True, settings.PLAYER_COLORS[number])
            surface.blit(image, image.get_rect(center=(rect.centerx, 188)))
        draw_text(surface, "Elección de jugador", self.game.fonts["large"], 65,
                  settings.ACCENT_COLOR)
        draw_text(surface, "A: entrar / confirmar · B: cancelar confirmación",
                  self.game.fonts["small"], 115)
        draw_text(surface, "Joystick: izquierda / centro / derecha · Suelta entre pasos",
                  self.game.fonts["small"], 140, settings.MUTED_COLOR)
        for index, (instance_id, player) in enumerate(self.participants.items()):
            choice = self.choices[instance_id]
            x = {1: 160, None: 320, 2: 480}[choice]
            y = 235 + index * 95
            color = settings.PLAYER_COLORS.get(choice, settings.MUTED_COLOR)
            player.position.update(x, y)
            player.render(surface, color=color)
            label = self.game.fonts["small"].render(f"Mando {index + 1}", True, color)
            surface.blit(label, label.get_rect(center=(x, y - 30)))
            status = "Listo · B" if player.number else "A: confirmar" if choice else "Elige lado"
            label = self.game.fonts["small"].render(status, True, color)
            surface.blit(label, label.get_rect(center=(x, y + 32)))
        draw_text(surface, self.message, self.game.fonts["small"], 418)
        draw_text(surface, "La partida comienza cuando ambos confirman · Esc: volver",
                  self.game.fonts["small"], 452, settings.MUTED_COLOR)
