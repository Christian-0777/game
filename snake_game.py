"""A polished, keyboard-controlled Snake game built with Python's tkinter."""

from __future__ import annotations

import json
import random
import tkinter as tk
from pathlib import Path


# --- Game and drawing settings ------------------------------------------------
CELL = 20
COLS = 30
ROWS = 26
BOARD_W = COLS * CELL
BOARD_H = ROWS * CELL
WINDOW_W = 680
WINDOW_H = 700
BOARD_X = (WINDOW_W - BOARD_W) // 2
BOARD_Y = 112

BG = "#101815"
PANEL = "#19231e"
BOARD = "#141e19"
GRID = "#1b2821"
TEXT = "#edf6ee"
MUTED = "#91a397"
GREEN = "#a5f36b"
GREEN_DARK = "#70cc48"
FOOD = "#ff6b6b"

DIRECTIONS = {
    "Up": (0, -1), "w": (0, -1), "W": (0, -1),
    "Down": (0, 1), "s": (0, 1), "S": (0, 1),
    "Left": (-1, 0), "a": (-1, 0), "A": (-1, 0),
    "Right": (1, 0), "d": (1, 0), "D": (1, 0),
}


class SnakeGame:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("Snake — Tkinter Arcade")
        root.resizable(False, False)
        root.configure(bg=BG)
        root.bind("<KeyPress>", self.on_key)

        self.canvas = tk.Canvas(
            root, width=WINDOW_W, height=WINDOW_H, bg=BG,
            highlightthickness=0, bd=0,
        )
        self.canvas.pack()

        self.high_score_path = Path.home() / ".snake_tkinter_highscore.json"
        self.high_score = self.load_high_score()
        self.score = 0
        self.snake: list[tuple[int, int]] = []
        self.food = (0, 0)
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.state = "ready"
        self.after_id: str | None = None

        self.draw()

    def load_high_score(self) -> int:
        try:
            data = json.loads(self.high_score_path.read_text(encoding="utf-8"))
            return max(0, int(data.get("high_score", 0)))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return 0

    def save_high_score(self) -> None:
        try:
            self.high_score_path.write_text(
                json.dumps({"high_score": self.high_score}), encoding="utf-8"
            )
        except OSError:
            # The game is still fully playable if the home folder is read-only.
            pass

    def start_game(self) -> None:
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        mid_x, mid_y = COLS // 2, ROWS // 2
        self.snake = [(mid_x, mid_y), (mid_x - 1, mid_y), (mid_x - 2, mid_y)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.score = 0
        self.state = "playing"
        self.place_food()
        self.draw()
        self.schedule_tick()

    def place_food(self) -> None:
        free_cells = [
            (x, y)
            for y in range(ROWS)
            for x in range(COLS)
            if (x, y) not in self.snake
        ]
        if free_cells:
            self.food = random.choice(free_cells)
        else:
            self.state = "won"

    def schedule_tick(self) -> None:
        if self.state == "playing":
            # Speed rises gently as the snake grows, with a fair lower limit.
            delay = max(62, 125 - (self.score // 50) * 7)
            self.after_id = self.root.after(delay, self.tick)

    def tick(self) -> None:
        self.after_id = None
        if self.state != "playing":
            return

        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)
        eating = new_head == self.food

        # Moving into the tail's current cell is safe if the tail moves away.
        body_to_check = self.snake if eating else self.snake[:-1]
        if (
            new_head[0] < 0 or new_head[0] >= COLS
            or new_head[1] < 0 or new_head[1] >= ROWS
            or new_head in body_to_check
        ):
            self.state = "game_over"
            self.draw()
            return

        self.snake.insert(0, new_head)
        if eating:
            self.score += 10
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()
            self.place_food()
        else:
            self.snake.pop()

        self.draw()
        self.schedule_tick()

    def on_key(self, event: tk.Event) -> None:
        key = event.keysym
        if key in ("Return", "KP_Enter") and self.state in ("ready", "game_over", "won"):
            self.start_game()
            return
        if key.lower() == "r":
            self.start_game()
            return
        if key in ("space", "Escape"):
            if self.state == "playing":
                self.state = "paused"
                if self.after_id is not None:
                    self.root.after_cancel(self.after_id)
                    self.after_id = None
                self.draw()
            elif self.state == "paused":
                self.state = "playing"
                self.draw()
                self.schedule_tick()
            return

        requested = DIRECTIONS.get(key)
        if requested and self.state == "playing":
            dx, dy = requested
            current_x, current_y = self.direction
            if (dx, dy) != (-current_x, -current_y):
                self.next_direction = (dx, dy)

    def rounded_rect(self, x1: int, y1: int, x2: int, y2: int,
                     radius: int, fill: str, outline: str = "") -> None:
        # Smooth polygon keeps the canvas self-contained (no image dependencies).
        points = [
            x1 + radius, y1, x2 - radius, y1,
            x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2,
            x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius,
            x1, y1 + radius, x1, y1,
        ]
        self.canvas.create_polygon(
            points, smooth=True, splinesteps=12, fill=fill,
            outline=outline or fill, width=1,
        )

    def draw(self) -> None:
        c = self.canvas
        c.delete("all")

        # Header and score cards.
        c.create_text(BOARD_X, 37, text="SNAKE", anchor="w", fill=TEXT,
                      font=("TkDefaultFont", 23, "bold"))
        c.create_text(BOARD_X, 69, text="CLASSIC ARCADE", anchor="w", fill=GREEN,
                      font=("TkDefaultFont", 9, "bold"))
        self.rounded_rect(BOARD_X + 345, 25, BOARD_X + 447, 82, 12, PANEL)
        c.create_text(BOARD_X + 363, 42, text="SCORE", anchor="w", fill=MUTED,
                      font=("TkDefaultFont", 8, "bold"))
        c.create_text(BOARD_X + 363, 63, text=f"{self.score:03d}", anchor="w", fill=TEXT,
                      font=("TkDefaultFont", 16, "bold"))
        self.rounded_rect(BOARD_X + 458, 25, BOARD_X + 560, 82, 12, PANEL)
        c.create_text(BOARD_X + 476, 42, text="BEST", anchor="w", fill=MUTED,
                      font=("TkDefaultFont", 8, "bold"))
        c.create_text(BOARD_X + 476, 63, text=f"{self.high_score:03d}", anchor="w", fill=GREEN,
                      font=("TkDefaultFont", 16, "bold"))

        # Game board and quiet grid lines.
        c.create_rectangle(BOARD_X, BOARD_Y, BOARD_X + BOARD_W, BOARD_Y + BOARD_H,
                           fill=BOARD, outline="#29372e", width=2)
        for x in range(1, COLS):
            px = BOARD_X + x * CELL
            c.create_line(px, BOARD_Y, px, BOARD_Y + BOARD_H, fill=GRID)
        for y in range(1, ROWS):
            py = BOARD_Y + y * CELL
            c.create_line(BOARD_X, py, BOARD_X + BOARD_W, py, fill=GRID)

        if self.snake:
            self.draw_food()
            for index, (x, y) in enumerate(reversed(self.snake)):
                self.draw_segment(x, y, is_head=(index == len(self.snake) - 1))

        footer_y = BOARD_Y + BOARD_H + 28
        c.create_text(BOARD_X, footer_y, text="MOVE", anchor="w", fill=MUTED,
                      font=("TkDefaultFont", 8, "bold"))
        c.create_text(BOARD_X + 42, footer_y, text="ARROWS  /  W A S D", anchor="w", fill=TEXT,
                      font=("TkDefaultFont", 9, "bold"))
        c.create_text(BOARD_X + BOARD_W, footer_y,
                      text="SPACE  PAUSE     ·     R  RESTART", anchor="e", fill=MUTED,
                      font=("TkDefaultFont", 9))

        if self.state != "playing":
            self.draw_overlay()

    def draw_segment(self, x: int, y: int, is_head: bool) -> None:
        px = BOARD_X + x * CELL
        py = BOARD_Y + y * CELL
        inset = 2 if is_head else 3
        color = GREEN if is_head else GREEN_DARK
        self.rounded_rect(px + inset, py + inset, px + CELL - inset,
                          py + CELL - inset, 6, color)
        if is_head:
            # Eyes face the direction the snake is traveling.
            dx, dy = self.direction
            if dx:
                eye_x = px + (14 if dx > 0 else 6)
                eyes = [(eye_x, py + 6), (eye_x, py + 14)]
            else:
                eye_y = py + (14 if dy > 0 else 6)
                eyes = [(px + 6, eye_y), (px + 14, eye_y)]
            for ex, ey in eyes:
                self.canvas.create_oval(ex - 1.5, ey - 1.5, ex + 1.5, ey + 1.5,
                                        fill="#18321c", outline="")

    def draw_food(self) -> None:
        x, y = self.food
        px = BOARD_X + x * CELL
        py = BOARD_Y + y * CELL
        self.canvas.create_oval(px + 3, py + 3, px + 17, py + 17,
                                fill="#642d32", outline="")
        self.canvas.create_oval(px + 5, py + 5, px + 15, py + 15,
                                fill=FOOD, outline="")
        self.canvas.create_oval(px + 7, py + 6, px + 10, py + 9,
                                fill="#ffd2bd", outline="")

    def draw_overlay(self) -> None:
        c = self.canvas
        cx = BOARD_X + BOARD_W // 2
        cy = BOARD_Y + BOARD_H // 2
        c.create_rectangle(BOARD_X + 2, BOARD_Y + 2, BOARD_X + BOARD_W - 2,
                           BOARD_Y + BOARD_H - 2, fill="#0b100d", stipple="gray50",
                           outline="")
        if self.state == "ready":
            title, subtitle, action = "SNAKE", "Eat, grow, and don't hit the walls.", "PRESS ENTER TO PLAY"
        elif self.state == "paused":
            title, subtitle, action = "PAUSED", "Take a breath. Your snake can wait.", "SPACE TO RESUME"
        elif self.state == "won":
            title, subtitle, action = "YOU WIN!", "You filled the whole board.", "ENTER TO PLAY AGAIN"
        else:
            title, subtitle, action = "GAME OVER", f"You scored {self.score} points.", "ENTER TO TRY AGAIN"

        c.create_text(cx, cy - 48, text=title, fill=TEXT,
                      font=("TkDefaultFont", 30, "bold"))
        c.create_text(cx, cy - 8, text=subtitle, fill=MUTED,
                      font=("TkDefaultFont", 12))
        self.rounded_rect(cx - 108, cy + 24, cx + 108, cy + 66, 12, GREEN)
        c.create_text(cx, cy + 45, text=action, fill="#14200f",
                      font=("TkDefaultFont", 9, "bold"))


def main() -> None:
    root = tk.Tk()
    SnakeGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
