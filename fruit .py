import tkinter as tk
from tkinter import messagebox, simpledialog, Toplevel, Label
import random
import time
import json
import os

try:
    import pygame
    pygame.init()
    pygame.mixer.init()
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

WINDOW_WIDTH = 400
WINDOW_HEIGHT = 600
FRUIT_SIZE = 30
BASKET_WIDTH = 80
BASKET_HEIGHT = 20
BASKET_MOVE = 30
LEADERBOARD_FILE = "leaderboard.json"
PLAYER_DATA_FILE = "players.json"
MUSIC_FILE = "background.mp3"

FRUIT_TYPES = [
    {"color": "red", "points": 1},
    {"color": "yellow", "points": 2},
    {"color": "green", "points": 3},
    {"color": "blue", "points": 0, "power": "expand"},
    {"color": "purple", "points": 5, "power": "extra_life"},
    {"color": "gold", "points": 10, "power": "double_points"}
]

LEVELS = [
    {"level": 1, "speed": 5, "next_score": 10},
    {"level": 2, "speed": 7, "next_score": 20},
    {"level": 3, "speed": 9, "next_score": 35},
    {"level": 4, "speed": 11, "next_score": 55},
    {"level": 5, "speed": 13, "next_score": 80},
    {"level": 6, "speed": 15, "next_score": 110},
    {"level": 7, "speed": 18, "next_score": 150}
]

LEVEL_BACKGROUNDS = {
    1: "skyblue",
    2: "lightgreen",
    3: "khaki",
    4: "lightcyan",
    5: "plum",
    6: "midnightblue",
    7: "black"
}

difficulty_speeds = {"Easy": 1, "Medium": 1.5, "Hard": 2}


def hex_color(color_name):
    return tk.Tk().winfo_rgb(color_name)


class FruitCatcher:
    def __init__(self, root, player_name, difficulty):
        self.root = root
        self.player_name = player_name
        self.difficulty_factor = difficulty_speeds[difficulty]
        self.root.title(f"\U0001F353 Fruit Catcher PRO - Player: {player_name}")
        self.canvas = tk.Canvas(root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg=LEVEL_BACKGROUNDS[1])
        self.canvas.pack()

        self.score = 0
        self.level = 1
        self.speed = LEVELS[0]["speed"] * self.difficulty_factor
        self.misses = 0
        self.lives = 5
        self.start_time = time.time()
        self.fruit = None
        self.current_points = 0
        self.combo = 0
        self.fruit_count = 0
        self.high_score = self.load_high_score()
        self.paused = False
        self.expanded = False
        self.double_points_active = False

        self.basket = self.canvas.create_rectangle(
            (WINDOW_WIDTH - BASKET_WIDTH) / 2,
            WINDOW_HEIGHT - BASKET_HEIGHT - 10,
            (WINDOW_WIDTH + BASKET_WIDTH) / 2,
            WINDOW_HEIGHT - 10,
            fill="brown"
        )

        self.info_texts()
        self.root.bind("<Left>", self.move_left)
        self.root.bind("<Right>", self.move_right)
        self.root.bind("p", self.toggle_pause)

        if SOUND_AVAILABLE and os.path.exists(MUSIC_FILE):
            pygame.mixer.music.load(MUSIC_FILE)
            pygame.mixer.music.play(-1)

        self.spawn_fruit()
        self.update_timer()

    def info_texts(self):
        self.score_text = self.canvas.create_text(10, 10, anchor="nw", font=("Arial", 14, "bold"), fill="white", text="Score: 0")
        self.level_text = self.canvas.create_text(10, 30, anchor="nw", font=("Arial", 14, "bold"), fill="white", text="Level: 1")
        self.miss_text = self.canvas.create_text(10, 50, anchor="nw", font=("Arial", 14, "bold"), fill="white", text="Misses: 0")
        self.lives_text = self.canvas.create_text(10, 70, anchor="nw", font=("Arial", 14, "bold"), fill="white", text=f"Lives: {'\u2764 ' * self.lives}")
        self.high_text = self.canvas.create_text(10, 90, anchor="nw", font=("Arial", 14, "bold"), fill="white", text=f"High Score: {self.high_score}")
        self.fruit_count_text = self.canvas.create_text(10, 110, anchor="nw", font=("Arial", 14, "bold"), fill="white", text="Caught: 0")
        self.combo_text = self.canvas.create_text(10, 130, anchor="nw", font=("Arial", 14, "bold"), fill="white", text="Combo: 0")
        self.timer_text = self.canvas.create_text(WINDOW_WIDTH - 10, 10, anchor="ne", font=("Arial", 14, "bold"), fill="white", text="Time: 0")

    def move_left(self, event): self.canvas.move(self.basket, -BASKET_MOVE, 0)
    def move_right(self, event): self.canvas.move(self.basket, BASKET_MOVE, 0)

    def toggle_pause(self, event=None):
        self.paused = not self.paused
        if self.paused and SOUND_AVAILABLE:
            pygame.mixer.music.pause()
        elif not self.paused and SOUND_AVAILABLE:
            pygame.mixer.music.unpause()
            self.drop_fruit()

    def spawn_fruit(self):
        fruit_type = random.choice(FRUIT_TYPES)
        self.current_points = fruit_type.get("points", 1)
        self.current_power = fruit_type.get("power")
        color = fruit_type["color"]
        shape = random.choice(["oval", "rect", "triangle"])
        x = random.randint(20, WINDOW_WIDTH - FRUIT_SIZE - 20)
        y = 0

        if shape == "oval":
            self.fruit = self.canvas.create_oval(x, y, x + FRUIT_SIZE, y + FRUIT_SIZE, fill=color)
        elif shape == "rect":
            self.fruit = self.canvas.create_rectangle(x, y, x + FRUIT_SIZE, y + FRUIT_SIZE, fill=color)
        else:
            self.fruit = self.canvas.create_polygon(x + FRUIT_SIZE // 2, y, x, y + FRUIT_SIZE, x + FRUIT_SIZE, y + FRUIT_SIZE, fill=color)
        self.drop_fruit()

    def drop_fruit(self):
        if self.paused or not self.fruit: return
        self.canvas.move(self.fruit, 0, self.speed)
        fruit_coords = self.canvas.coords(self.fruit)
        basket_coords = self.canvas.coords(self.basket)

        if len(fruit_coords) > 4:
            xs = fruit_coords[::2]; ys = fruit_coords[1::2]
            fruit_box = [min(xs), min(ys), max(xs), max(ys)]
        else:
            fruit_box = fruit_coords

        if fruit_box[3] >= WINDOW_HEIGHT:
            self.misses += 1; self.lives -= 1; self.combo = 0
            self.update_texts()
            self.canvas.delete(self.fruit)
            if self.lives <= 0:
                self.game_over()
            else:
                self.spawn_fruit()
            return

        if self.check_collision(fruit_box, basket_coords):
            earned_points = self.current_points * (2 if self.double_points_active else 1)
            self.score += earned_points
            self.combo += 1; self.fruit_count += 1

            if self.current_power == "extra_life" and self.lives < 5:
                self.lives += 1
            if self.current_power == "expand": self.expand_basket()
            if self.current_power == "double_points": self.activate_double_points()

            self.update_texts()
            self.check_level_up()
            self.canvas.delete(self.fruit)
            self.spawn_fruit()
            return

        self.root.after(30, self.drop_fruit)

    def update_texts(self):
        self.canvas.itemconfigure(self.score_text, text=f"Score: {self.score}")
        self.canvas.itemconfigure(self.fruit_count_text, text=f"Caught: {self.fruit_count}")
        self.canvas.itemconfigure(self.combo_text, text=f"Combo: {self.combo}")
        self.canvas.itemconfigure(self.miss_text, text=f"Misses: {self.misses}")
        self.canvas.itemconfigure(self.lives_text, text=f"Lives: {'\u2764 ' * self.lives}")

    def expand_basket(self):
        if not self.expanded:
            self.expanded = True
            self.canvas.scale(self.basket, 0, 0, 1.5, 1)
            self.root.after(5000, self.reset_basket)

    def reset_basket(self):
        if self.expanded:
            self.canvas.scale(self.basket, 0, 0, 2/3, 1)
            self.expanded = False

    def activate_double_points(self):
        if not self.double_points_active:
            self.double_points_active = True
            self.root.after(5000, self.deactivate_double_points)

    def deactivate_double_points(self):
        self.double_points_active = False

    def check_collision(self, a, b):
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        return ax2 >= bx1 and ax1 <= bx2 and ay2 >= by1 and ay1 <= by2

    def check_level_up(self):
        for config in LEVELS:
            if self.score < config["next_score"]:
                if config["level"] > self.level:
                    self.level = config["level"]
                    self.speed = config["speed"] * self.difficulty_factor
                    self.animate_background(LEVEL_BACKGROUNDS.get(self.level, "pink"))
                    self.canvas.itemconfigure(self.level_text, text=f"Level: {self.level}")
                    self.canvas.create_text(WINDOW_WIDTH//2, 160, text=f"\U0001F680 Level {self.level} Reached!", font=("Helvetica", 16, "bold"), fill="orange")
                break

    def animate_background(self, target_color, steps=10):
        current_color = self.canvas["bg"]
        c1 = [x//256 for x in self.root.winfo_rgb(current_color)]
        c2 = [x//256 for x in self.root.winfo_rgb(target_color)]

        def fade(step=0):
            r = c1[0] + (c2[0] - c1[0]) * step // steps
            g = c1[1] + (c2[1] - c1[1]) * step // steps
            b = c1[2] + (c2[2] - c1[2]) * step // steps
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.canvas.configure(bg=color)
            if step < steps:
                self.root.after(40, lambda: fade(step + 1))

        fade()

    def update_timer(self):
        elapsed = int(time.time() - self.start_time)
        self.canvas.itemconfigure(self.timer_text, text=f"Time: {elapsed}s")
        self.root.after(1000, self.update_timer)

    def game_over(self):
        self.canvas.create_text(WINDOW_WIDTH//2, WINDOW_HEIGHT//2, text="\U0001F6D1 GAME OVER", font=("Helvetica", 24, "bold"), fill="red")
        self.canvas.create_text(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 30, text=f"Final Score: {self.score}", font=("Helvetica", 16), fill="white")
        self.canvas.create_text(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 60, text=f"Reached Level: {self.level}", font=("Helvetica", 14), fill="yellow")

        if self.score > self.high_score:
            self.high_score = self.score

        self.save_player_data()
        self.show_leaderboard()

        if messagebox.askyesno("Play Again?", "Do you want to restart the game?"):
            self.root.destroy()
            main()

    def show_leaderboard(self):
        top = Toplevel(self.root)
        top.title("\U0001F3C6 Leaderboard")
        top.geometry("280x180")
        scores = []

        if os.path.exists(LEADERBOARD_FILE):
            with open(LEADERBOARD_FILE, "r") as f:
                scores = json.load(f).get("scores", [])

        Label(top, text="Top Scores:", font=("Arial", 14, "bold")).pack(pady=10)
        for i, record in enumerate(scores):
            Label(top, text=f"{i+1}. {record['name']} - {record['score']}", font=("Arial", 12)).pack()

    def save_player_data(self):
        leaderboard = []
        if os.path.exists(LEADERBOARD_FILE):
            with open(LEADERBOARD_FILE, "r") as f:
                leaderboard = json.load(f).get("scores", [])

        leaderboard.append({"name": self.player_name, "score": self.score})
        leaderboard = sorted(leaderboard, key=lambda x: x['score'], reverse=True)[:3]

        with open(LEADERBOARD_FILE, "w") as f:
            json.dump({"scores": leaderboard, "high_score": leaderboard[0]['score']}, f)

    def load_high_score(self):
        if os.path.exists(LEADERBOARD_FILE):
            with open(LEADERBOARD_FILE, "r") as f:
                data = json.load(f)
                return data.get("high_score", 0)
        return 0

def main():
    root = tk.Tk()
    player_name = simpledialog.askstring("Player Name", "Enter your name:") or "Guest"
    difficulty = simpledialog.askstring("Difficulty", "Choose difficulty (Easy / Medium / Hard):", initialvalue="Medium")
    difficulty = difficulty if difficulty in difficulty_speeds else "Medium"
    FruitCatcher(root, player_name, difficulty)
    root.mainloop()

if __name__ == "__main__":
    main()
