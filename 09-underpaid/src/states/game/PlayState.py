"""Dos personajes animados con métodos de entrada independientes."""

from gale.state import BaseState

import settings
from src.gui.Menu import draw_text
from src.world.Room import Room


class PlayState(BaseState):
    def __init__(self, state_machine, game):
        super().__init__(state_machine)
        self.game = game

    def enter(self, players) -> None:
        self.players = dict(players)
        self.room = Room()
        for player in self.players.values():
            player.stop()
            player.position.update(self.room.spawn_position(player.number))

    def update(self, dt: float) -> None:
        connected = {
            number: player for number, player in self.players.items()
            if player.is_connected(self.game.controllers)
        }
        if len(connected) != 2:
            self.state_machine.change("player_select", players=connected)
            return
        for player in self.players.values():
            player.update(dt, self.room.walkable_area)

    def on_input(self, input_id, input_data) -> None:
        if input_id == "back" and input_data.pressed:
            self.state_machine.change("main_menu")
            return
        for player in self.players.values():
            player.on_input(input_id, input_data)

    def render(self, surface) -> None:
        surface.fill(settings.BACKGROUND_COLOR)
        self.room.render(surface)
        draw_text(surface, "UNDERPAID", self.game.fonts["medium"], 23,
                  settings.ACCENT_COLOR)
        for player in sorted(self.players.values(), key=lambda player: player.position.y):
            player.render(surface)
        draw_text(surface, "Joystick / WASD: mover · Esc: volver al menú", self.game.fonts["small"], 457,
                  settings.MUTED_COLOR)
