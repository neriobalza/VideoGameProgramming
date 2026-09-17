"""
ISPPV1 2023
Study Case: Ultimate Fantasy (RPG)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains PartyStatusState: an overworld party/status screen
with one card per character. Every known action is shown, but only healing
actions remain opaque and selectable outside battle.
"""

from typing import Any, Dict, List, Tuple

import pygame

from gale.state import BaseState

import settings
from src.definitions.entity import DEFAULT_CHARACTER_FRAME
from src.gui.Panel import Panel

CARD_MARGIN = 6
CARD_GAP = 4
CARD_TOP = 19
CARD_HEIGHT = 90
CARD_WIDTH = (settings.VIRTUAL_WIDTH - CARD_MARGIN * 2 - CARD_GAP) // 2
INACTIVE_ALPHA = 80


class PartyStatusState(BaseState):
    def enter(self, play_state: Any) -> None:
        self.play_state = play_state
        self.party = play_state.world.party
        self.characters = [
            (key, self.party.characters[key])
            for key in sorted(self.party.characters.keys())
        ]
        self.cards: Dict[int, Panel] = {}
        self.healing_actions: List[Tuple[Any, Dict[str, Any]]] = []
        self.selected_action = 0
        self.message = "Up/Down: healing action   Enter: use   P: back"
        self.shade = pygame.Surface(
            (settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT), pygame.SRCALPHA
        )
        self.shade.fill((0, 0, 0, 190))

        for index, (key, character) in enumerate(self.characters):
            column = index % 2
            row = index // 2
            x = CARD_MARGIN + column * (CARD_WIDTH + CARD_GAP)
            y = CARD_TOP + row * (CARD_HEIGHT + CARD_GAP)
            self.cards[key] = Panel(x, y, CARD_WIDTH, CARD_HEIGHT)

            if character.dead:
                continue

            for action in character.actions:
                if self._is_healing(action):
                    self.healing_actions.append((character, action))

        if not self.healing_actions:
            self.message = "No healing actions are currently available.   P: back"

    @staticmethod
    def _is_healing(action: Dict[str, Any]) -> bool:
        return (
            action.get("target_type") == "character"
            and callable(action.get("func"))
        )

    @staticmethod
    def _number(value: float) -> str:
        return str(int(value)) if float(value).is_integer() else f"{value:.1f}"

    def _selected(self, character: Any, action: Dict[str, Any]) -> bool:
        if not self.healing_actions:
            return False

        selected_character, selected_action = self.healing_actions[
            self.selected_action
        ]
        return selected_character is character and selected_action is action

    def _select_healing_action(self) -> None:
        if not self.healing_actions:
            return

        character, action = self.healing_actions[self.selected_action]
        targets = [
            target for _, target in self.characters if not target.dead
        ]

        if not targets:
            self.message = "There are no living targets to heal."
            return

        if action.get("require_target", True):
            from src.states.game.SelectTargetState import SelectTargetState

            self.message = "Left/Right: choose a living target   Enter: heal"
            self.state_machine.push(
                SelectTargetState(self.state_machine),
                battle_state=None,
                targets=targets,
                cursor_position=self.target_cursor_position,
                on_target_selected=lambda target: self._resolve_healing(
                    character, action, target
                ),
            )
        else:
            # This is the same list shape and action function used by the
            # battle action state for Global Heal.
            self._resolve_healing(character, action, targets)

    def _resolve_healing(
        self, character: Any, action: Dict[str, Any], target_or_targets: Any
    ) -> None:
        action_func = action.get("func")

        if not callable(action_func):
            self.message = "That healing action is not available."
            return

        targets = (
            target_or_targets
            if isinstance(target_or_targets, list)
            else [target_or_targets]
        )
        living_targets = [target for target in targets if not target.dead]

        if not living_targets:
            self.message = "There are no living targets to heal."
            return

        before = [target.current_hp for target in living_targets]
        argument = (
            living_targets
            if not action.get("require_target", True)
            else living_targets[0]
        )

        try:
            amount = action_func(character, argument, action.get("strength"))
        except (ArithmeticError, TypeError, ValueError):
            self.message = "The healing action could not be resolved."
            return

        sound = settings.SOUNDS.get(action.get("sound_effect"))
        if sound is not None:
            sound.play()

        if any(
            target.current_hp != old_hp
            for target, old_hp in zip(living_targets, before)
        ):
            self.play_state.world.dirty = True

        if action.get("require_target", True):
            self.message = (
                f"{action.get('name', 'Heal')}: {amount} HP to "
                f"{living_targets[0].name}."
            )
        else:
            self.message = (
                f"{action.get('name', 'Global Heal')}: {amount} HP to each ally."
            )

    def target_cursor_position(self, target: Any) -> Tuple[float, float]:
        for key, character in self.characters:
            if character is target:
                card = self.cards[key]
                return card.x - 5, card.y + card.height / 2 - 4

        return 0, 0

    def on_input(self, input_id: str, input_data: Any) -> None:
        if not input_data.pressed:
            return

        if input_id == "pause":
            self.state_machine.pop()
        elif input_id == "move_up" and self.healing_actions:
            self.selected_action = (
                self.selected_action - 1
            ) % len(self.healing_actions)
            settings.SOUNDS["blip"].play()
        elif input_id == "move_down" and self.healing_actions:
            self.selected_action = (
                self.selected_action + 1
            ) % len(self.healing_actions)
            settings.SOUNDS["blip"].play()
        elif input_id == "enter":
            self._select_healing_action()

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(self.shade, (0, 0))

        title = settings.FONTS["small"].render(
            "PARTY STATUS / HEALING", True, (255, 255, 255)
        )
        surface.blit(title, title.get_rect(centerx=settings.VIRTUAL_WIDTH / 2, y=5))

        for key, character in self.characters:
            self._render_character(surface, key, character)

        footer = settings.FONTS["small"].render(
            self.message, True, (255, 255, 255)
        )
        surface.blit(
            footer,
            footer.get_rect(centerx=settings.VIRTUAL_WIDTH / 2, y=210),
        )

    def _render_character(
        self, surface: pygame.Surface, key: int, character: Any
    ) -> None:
        card = self.cards[key]
        card.render(surface)
        font = settings.FONTS["small"]
        color = (155, 155, 155) if character.dead else (255, 255, 255)

        surface.blit(
            settings.TEXTURES[character.texture],
            (card.x + 8, card.y + 16),
            settings.frame(character.texture, DEFAULT_CHARACTER_FRAME),
        )

        labels = [
            (character.name, card.x + 30, card.y + 6),
            (f"{character.klass}  Lv {character.level}", card.x + 30, card.y + 17),
            (
                f"HP {self._number(character.current_hp)}/{self._number(character.hp)}",
                card.x + 8,
                card.y + 39,
            ),
            (
                "EXP "
                f"{self._number(character.current_exp)}/"
                f"{self._number(character.exp_to_level)}",
                card.x + 8,
                card.y + 49,
            ),
            (f"Magic {self._number(character.magic)}", card.x + 8, card.y + 59),
            (f"Attack {self._number(character.attack)}", card.x + 8, card.y + 69),
            (f"Defense {self._number(character.defense)}", card.x + 8, card.y + 79),
            ("Actions", card.x + 106, card.y + 17),
        ]

        for label, x, y in labels:
            surface.blit(font.render(label, True, color), (x, y))

        for action_index, action in enumerate(character.actions):
            is_healing = self._is_healing(action) and not character.dead
            action_color = (
                (255, 224, 96)
                if self._selected(character, action)
                else (255, 255, 255)
            )
            action_text = font.render(
                action.get("name", "Unknown"), True, action_color
            )
            action_text.set_alpha(255 if is_healing else INACTIVE_ALPHA)
            action_x = card.x + 106
            action_y = card.y + 29 + action_index * 12
            surface.blit(action_text, (action_x, action_y))

            if self._selected(character, action):
                surface.blit(
                    settings.TEXTURES["cursor-right"],
                    (action_x - 10, action_y),
                )
