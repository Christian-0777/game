# Snake — Tkinter Arcade

A classic Snake game made with Python's built-in `tkinter` GUI toolkit. No third-party packages or image assets are required.

## Run

```bash
python3 snake_game.py
```

If your Python installation does not include Tkinter, install the OS package for it (for example, `python3-tk` on Debian/Ubuntu).

## Controls

- **Arrow keys** or **W A S D** — move
- **Space** or **Escape** — pause / resume
- **R** — start a new game
- **Enter** — start or play again from the title/game-over screen

Eat the red food to grow and earn 10 points. The game gets faster as your score climbs. Your best score is saved locally in `~/.snake_tkinter_highscore.json`.
