"""
ISPPV1 2023
Study Case: Breakout

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class to define the Play state.
"""

import random

import pygame

from gale.factory import AbstractFactory, Factory
from gale.state import BaseState
from gale.input_handler import InputData
from gale.text import render_text

import settings
import src.powerups
from src.Projectile import Projectile


class PlayState(BaseState):
    def enter(self, **params: dict):
        self.level = params["level"]
        self.score = params["score"]
        self.lives = params["lives"]
        self.paddle = params["paddle"]
        self.balls = params["balls"]
        self.brickset = params["brickset"]
        self.live_factor = params["live_factor"]
        self.points_to_next_live = params["points_to_next_live"]
        self.points_to_next_grow_up = (
            self.score
            + settings.PADDLE_GROW_UP_POINTS * (self.paddle.size + 1) * self.level
        )
        self.powerups = params.get("powerups", [])
        self.capture_time_remaining = params.get("capture_time_remaining", 0)
        self.caught_balls = params.get("caught_balls", {})
        self.cannons_ready = params.get("cannons_ready", False)
        self.projectiles = params.get("projectiles", [])

        if not params.get("resume", False):
            self.balls[0].vx = random.randint(-80, 80)
            self.balls[0].vy = random.randint(-170, -100)
            settings.SOUNDS["paddle_hit"].play()

        self.powerups_abstract_factory = AbstractFactory("src.powerups")
        self.projectile_factory = Factory(Projectile)

    def activate_ball_capture(self) -> None:
        self.capture_time_remaining = settings.CATCH_BALL_POWERUP_DURATION

    def catch_ball(self, ball) -> None:
        max_offset = max(0, self.paddle.width - ball.width)
        offset = max(0, min(ball.x - self.paddle.x, max_offset))

        ball.vx = 0
        ball.vy = 0
        self.caught_balls[ball] = offset
        self.position_caught_ball(ball)

    def position_caught_ball(self, ball) -> None:
        offset = self.caught_balls.get(ball)

        if offset is None:
            return

        max_offset = max(0, self.paddle.width - ball.width)
        ball.x = self.paddle.x + min(offset, max_offset)
        ball.y = self.paddle.y - ball.height

    def launch_caught_balls(self) -> None:
        for ball in self.caught_balls:
            ball.vx = random.randint(-80, 80)
            ball.vy = random.randint(-170, -100)

        if self.caught_balls:
            settings.SOUNDS["paddle_hit"].stop()
            settings.SOUNDS["paddle_hit"].play()

        self.caught_balls = {}

    def fire_projectiles(self) -> None:
        if not self.cannons_ready or self.projectiles:
            return

        projectile_y = self.paddle.y - settings.PROJECTILE_HEIGHT
        self.projectiles = [
            self.projectile_factory.create(self.paddle.x, projectile_y),
            self.projectile_factory.create(
                self.paddle.x + self.paddle.width - settings.PROJECTILE_WIDTH,
                projectile_y,
            ),
        ]
        self.cannons_ready = False

    def update_score(self, brick) -> None:
        self.score += brick.score()

        # Check earn life
        if self.score >= self.points_to_next_live:
            settings.SOUNDS["life"].play()
            self.lives = min(3, self.lives + 1)
            self.live_factor += 0.5
            self.points_to_next_live += settings.LIVE_POINTS_BASE * self.live_factor

        # Check growing up of the paddle
        if self.score >= self.points_to_next_grow_up:
            settings.SOUNDS["grow_up"].play()
            self.points_to_next_grow_up += (
                settings.PADDLE_GROW_UP_POINTS * (self.paddle.size + 1) * self.level
            )
            self.paddle.inc_size()

    def generate_powerup(self, brick) -> None:
        if random.random() >= 0.1:
            return

        r = brick.get_collision_rect()
        powerup_name = random.choice(("TwoMoreBall", "CatchBall", "Cannons"))
        self.powerups.append(
            self.powerups_abstract_factory.get_factory(powerup_name).create(
                r.centerx - 8, r.centery - 8
            )
        )

    def update_projectiles(self, dt: float) -> None:
        for projectile in self.projectiles:
            projectile.update(dt)

            for brick in self.brickset.bricks.values():
                if brick.broken or not projectile.collides(brick):
                    continue

                self.update_score(brick)
                brick.destroy()
                self.generate_powerup(brick)

        self.projectiles = [
            projectile for projectile in self.projectiles if projectile.active
        ]

    def update(self, dt: float) -> None:
        self.capture_time_remaining = max(0, self.capture_time_remaining - max(0, dt))
        self.paddle.update(dt)

        for ball in self.balls:
            if ball in self.caught_balls:
                self.position_caught_ball(ball)
                continue

            ball.update(dt)
            ball.solve_world_boundaries()

            # Check collision with the paddle
            if ball.collides(self.paddle):
                settings.SOUNDS["paddle_hit"].stop()
                settings.SOUNDS["paddle_hit"].play()

                if self.capture_time_remaining > 0:
                    self.catch_ball(ball)
                    continue

                ball.rebound(self.paddle)
                ball.push(self.paddle)

            # Check collision with brickset
            if not ball.collides(self.brickset):
                continue

            brick = self.brickset.get_colliding_brick(ball.get_collision_rect())

            if brick is None:
                continue

            brick.hit()
            self.update_score(brick)
            ball.rebound(brick)
            self.generate_powerup(brick)

        # Removing all balls that are not in play
        self.balls = [ball for ball in self.balls if ball.active]
        self.caught_balls = {
            ball: offset
            for ball, offset in self.caught_balls.items()
            if ball.active and ball in self.balls
        }

        self.update_projectiles(dt)
        self.brickset.update(dt)

        if not self.balls:
            self.lives -= 1
            if self.lives == 0:
                self.state_machine.change("game_over", score=self.score)
            else:
                self.paddle.dec_size()
                self.state_machine.change(
                    "serve",
                    level=self.level,
                    score=self.score,
                    lives=self.lives,
                    paddle=self.paddle,
                    brickset=self.brickset,
                    points_to_next_live=self.points_to_next_live,
                    live_factor=self.live_factor,
                )

        # Update powerups
        for powerup in self.powerups:
            powerup.update(dt)

            if powerup.collides(self.paddle):
                powerup.take(self)

        # Remove powerups that are not in play
        self.powerups = [p for p in self.powerups if p.active]

        # Check victory
        if not any(not brick.broken for brick in self.brickset.bricks.values()):
            self.state_machine.change(
                "victory",
                lives=self.lives,
                level=self.level,
                score=self.score,
                paddle=self.paddle,
                balls=self.balls,
                points_to_next_live=self.points_to_next_live,
                live_factor=self.live_factor,
            )

    def render(self, surface: pygame.Surface) -> None:
        heart_x = settings.VIRTUAL_WIDTH - 120

        i = 0
        # Draw filled hearts
        while i < self.lives:
            surface.blit(
                settings.TEXTURES["hearts"], (heart_x, 5), settings.FRAMES["hearts"][0]
            )
            heart_x += 11
            i += 1

        # Draw empty hearts
        while i < 3:
            surface.blit(
                settings.TEXTURES["hearts"], (heart_x, 5), settings.FRAMES["hearts"][1]
            )
            heart_x += 11
            i += 1

        render_text(
            surface,
            f"Score: {self.score}",
            settings.FONTS["tiny"],
            settings.VIRTUAL_WIDTH - 80,
            5,
            (255, 255, 255),
        )

        self.brickset.render(surface)

        self.paddle.render(surface)

        if self.cannons_ready:
            cannon_y = self.paddle.y - settings.CANNON_HEIGHT
            pygame.draw.rect(
                surface,
                settings.CANNON_COLOR,
                (
                    self.paddle.x,
                    cannon_y,
                    settings.CANNON_WIDTH,
                    settings.CANNON_HEIGHT,
                ),
            )
            pygame.draw.rect(
                surface,
                settings.CANNON_COLOR,
                (
                    self.paddle.x + self.paddle.width - settings.CANNON_WIDTH,
                    cannon_y,
                    settings.CANNON_WIDTH,
                    settings.CANNON_HEIGHT,
                ),
            )

        for ball in self.balls:
            ball.render(surface)

        for projectile in self.projectiles:
            projectile.render(surface)

        for powerup in self.powerups:
            powerup.render(surface)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "move_left":
            if input_data.pressed:
                self.paddle.vx = -settings.PADDLE_SPEED
            elif input_data.released and self.paddle.vx < 0:
                self.paddle.vx = 0
        elif input_id == "move_right":
            if input_data.pressed:
                self.paddle.vx = settings.PADDLE_SPEED
            elif input_data.released and self.paddle.vx > 0:
                self.paddle.vx = 0
        elif input_id == "fire" and input_data.pressed:
            self.fire_projectiles()
        elif input_id == "pause" and input_data.pressed:
            if self.caught_balls:
                self.launch_caught_balls()
            else:
                self.state_machine.change(
                    "pause",
                    level=self.level,
                    score=self.score,
                    lives=self.lives,
                    paddle=self.paddle,
                    balls=self.balls,
                    brickset=self.brickset,
                    points_to_next_live=self.points_to_next_live,
                    live_factor=self.live_factor,
                    powerups=self.powerups,
                    capture_time_remaining=self.capture_time_remaining,
                    caught_balls=self.caught_balls,
                    cannons_ready=self.cannons_ready,
                    projectiles=self.projectiles,
                )
