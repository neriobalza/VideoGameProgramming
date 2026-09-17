# Video Game Programming I

Source code of the study cases developed throughout the *Video Game Programming I*
(ISPPV1) course at Universidad de Los Andes (ULA), Venezuela.

Each folder is a self-contained game built incrementally to illustrate a specific
set of game-programming concepts (game loop, states, collisions, tile maps, UI,
inventory systems, physics, etc.), using [Gale](https://pypi.org/project/gale-engine/),
a small Python game engine built on top of [Pygame](https://www.pygame.org/).

## Getting started

[`00-hello_world`](00-hello_world) is a minimal introductory exercise to get
familiar with Gale before diving into an actual game.

## Study cases

| # | Project | Study case |
|---|---------|------------|
| 01 | [`01-pong`](01-pong) | Pong |
| 02 | [`02-flappy_bird`](02-flappy_bird) | Flappy Bird |
| 03 | [`03-breakout`](03-breakout) | Breakout |
| 04 | [`04-match3`](04-match3) | Match-3 |
| 05 | [`05-super_martian`](05-super_martian) | Super Martian (Platformer) |
| 06 | [`06-princess`](06-princess) | The Legend of the Princess (ARPG) |
| 07 | [`07-ultimate_fantasy`](07-ultimate_fantasy) | Ultimate Fantasy (RPG) |
| 08 | [`08-throw_a_bird`](08-throw_a_bird) | Throw a Bird |
| 09 | [`09-underpaid`](09-underpaid) | Underpaid (Menus and display settings) |

Every project follows the same layout:

```
<NN-project_name>/
├── main.py          # Entry point: creates and runs the game instance
├── settings.py       # Window/virtual resolution, input bindings, fonts, constants
├── src/               # Game-specific code (states, entities, world, etc.)
└── assets/            # Images, spritesheets, sounds and fonts (when applicable)
```

## Requirements

- Python 3.12+
- A single dependency shared by every project: [`gale-engine`](https://pypi.org/project/gale-engine/)
  (which in turn depends on Pygame). It is declared once in the
  [`requirements.txt`](requirements.txt) at the root of this repository, since
  every study case uses the exact same dependency.

## Setup

Clone the repository and create a virtual environment at the root:

```bash
git clone https://github.com/R3mmurd/VideoGameProgrammingI.git
cd VideoGameProgrammingI
python3 -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running a study case

Every project is run from within its own folder, since each one resolves its
assets and modules relative to its own directory:

```bash
cd 01-pong
python main.py
```

Replace `01-pong` with the folder of the study case you want to try.

## License

This project is licensed under the terms of the [MIT License](LICENSE).

## Author

Alejandro Mujica — alejandro.j.mujic4@gmail.com
