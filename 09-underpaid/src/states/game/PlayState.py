"""Pantalla de los dos personajes, cada uno movido sólo por su mando."""

from gale.state import BaseState

import settings
from src.gui.Menu import draw_text


class PlayState(BaseState):
    def __init__(self, state_machine, game):
        super().__init__(state_machine)
        self.game = game

    def enter(self, players) -> None:
        self.players = dict(players)
        for player in self.players.values():
            player.stop()
            player.position.update(settings.VIRTUAL_WIDTH * (0.25 if player.number == 1 else 0.75),
                                   settings.VIRTUAL_HEIGHT / 2)

    def update(self, dt: float) -> None:
        connected = {
            number: player for number, player in self.players.items()
            if self.game.controllers.is_connected(player.controller_id)
        }
        if len(connected) != 2:
            self.state_machine.change("player_select", players=connected)
            return
        for player in self.players.values():
            player.update(dt)

    def on_input(self, input_id, input_data) -> None:
        if input_id == "back" and input_data.pressed:
            self.state_machine.change("main_menu")
            return
        for player in self.players.values():
            player.on_input(input_id, input_data)

    def render(self, surface) -> None:
        surface.fill(settings.BACKGROUND_COLOR)
        draw_text(surface, "UNDERPAID", self.game.fonts["large"], 55,
                  settings.ACCENT_COLOR)
        draw_text(surface, "Cada jugador se mueve con el joystick de su mando",
                  self.game.fonts["small"], 93, settings.MUTED_COLOR)
        for player in self.players.values():
            player.render(surface)
        draw_text(surface, "Esc: volver al menú", self.game.fonts["small"], 455,
                  settings.MUTED_COLOR)
