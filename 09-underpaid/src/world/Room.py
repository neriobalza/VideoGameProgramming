"""Sala de suelo y paredes basada en el mapa de 06-princess."""

import random

import pygame
from gale.tilemap import TileMap

import settings
from src.world.Box import Box


class Room:
    def __init__(self) -> None:
        size = settings.TILE_RENDER_SIZE
        self.tilemap = TileMap(size, size, settings.MAP_WIDTH, settings.MAP_HEIGHT)
        self.tilemap.add_tileset(settings.load_room_tileset())
        self.bounds = pygame.Rect(
            settings.MAP_RENDER_OFFSET_X, settings.MAP_RENDER_OFFSET_Y,
            self.tilemap.pixel_width, self.tilemap.pixel_height,
        )
        self.walkable_area = self.bounds.inflate(-2 * size, -2 * size)
        self._generate_tiles()
        self.objects = [
            Box(self.bounds.x + col * size, self.bounds.y + row * size)
            for col in (3, self.tilemap.cols - 4)
            for row in (3, self.tilemap.rows - 4)
        ]

        # La sala es estática: se dibuja una vez y se reutiliza cada frame.
        self.background = pygame.Surface(self.bounds.size)
        self.background.fill(settings.BACKGROUND_COLOR)
        self.tilemap.render(self.background)

    def _generate_tiles(self) -> None:
        tiles = self.tilemap.add_layer("floor")
        cols, rows = self.tilemap.cols, self.tilemap.rows
        corners = {
            (0, 0): settings.TILE_TOP_LEFT_CORNER,
            (0, cols - 1): settings.TILE_TOP_RIGHT_CORNER,
            (rows - 1, 0): settings.TILE_BOTTOM_LEFT_CORNER,
            (rows - 1, cols - 1): settings.TILE_BOTTOM_RIGHT_CORNER,
        }
        # Misma sala en cada partida, con las variaciones de suelo de Princess.
        rng = random.Random(9)
        for row in range(rows):
            for col in range(cols):
                if (row, col) in corners:
                    tile = corners[row, col]
                elif col == 0:
                    tile = rng.choice(settings.TILE_LEFT_WALLS)
                elif col == cols - 1:
                    tile = rng.choice(settings.TILE_RIGHT_WALLS)
                elif row == 0:
                    tile = rng.choice(settings.TILE_TOP_WALLS)
                elif row == rows - 1:
                    tile = rng.choice(settings.TILE_BOTTOM_WALLS)
                else:
                    tile = rng.choice(settings.TILE_FLOORS)
                tiles[row][col] = tile

    def spawn_position(self, number: int) -> tuple[float, float]:
        fraction = 0.25 if number == 1 else 0.75
        return (
            self.walkable_area.left + self.walkable_area.width * fraction,
            self.walkable_area.centery,
        )

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(self.background, self.bounds)

    def try_lift(self, player) -> bool:
        """Busca una vasija próxima delante de los pies del jugador."""
        if player.carrying is not None:
            return False
        feet = player.hitbox
        reach = settings.TILE_RENDER_SIZE
        interaction = {
            "left": pygame.Rect(feet.left - reach, feet.top, reach, feet.height),
            "right": pygame.Rect(feet.right, feet.top, reach, feet.height),
            "up": pygame.Rect(feet.left, feet.top - reach, feet.width, reach),
            "down": pygame.Rect(feet.left, feet.bottom, feet.width, reach),
        }[player.facing]
        candidates = [obj for obj in self.objects if obj.solid and interaction.colliderect(obj.hitbox)]
        if not candidates:
            return False
        obj = min(candidates, key=lambda obj: pygame.Vector2(obj.hitbox.center).distance_squared_to(feet.center))
        player.lift(obj)
        return True

    def interact(self, player, players) -> bool:
        if player.carrying is None:
            return self.try_lift(player)
        return self.try_put_down(player, players)

    def try_put_down(self, player, players) -> bool:
        """Coloca la vasija delante del jugador en cualquier posición libre."""
        obj = player.carrying
        if obj is None or player.lift_elapsed < settings.POT_LIFT_DURATION:
            return False
        feet = player.hitbox
        positions = {
            "left": (feet.left - obj.width, feet.centery - obj.height / 2),
            "right": (feet.right, feet.centery - obj.height / 2),
            "up": (feet.centerx - obj.width / 2, feet.top - obj.height),
            "down": (feet.centerx - obj.width / 2, feet.bottom),
        }
        x, y = positions[player.facing]
        target = pygame.Rect(round(x), round(y), obj.width, obj.height)
        if not self.walkable_area.contains(target):
            return False
        if any(other.solid and target.colliderect(other.hitbox) for other in self.objects):
            return False
        if any(target.colliderect(other.hitbox) for other in players):
            return False
        player.put_down(target.topleft)
        return True
