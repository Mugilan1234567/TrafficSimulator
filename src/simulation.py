import pygame
import json
import random
from src.car import Car
from src.heatmap import Heatmap
from src.pathfinding import find_all_paths, choose_random_path

TILE_SIZE = 40
MAP_WIDTH, MAP_HEIGHT = 30, 20
TOOLBAR_HEIGHT = 100

BASE_COLORS = {
    "residential": (102, 204, 255),
    "workplace": (255, 223, 88),
    "road": (150, 150, 150),
    "highway": (255, 99, 71),
    "intersection": (100, 255, 100),
}
OVERLAY_COLORS = {
    "stop_sign": (220, 20, 60),
    "traffic_light": (0, 191, 255),
}

# Adjustable car spawn configuration
MAX_CARS = 200
DEFAULT_SPAWN_INTERVAL = 9 # Lower means more frequent spawns

class Simulation:
    def __init__(self, screen):
        self.screen = screen
        self.map = []
        self.overlays = []
        self.cars = []
        self.width = 0
        self.height = 0
        self.time_of_day = "Morning"
        self.paused = False
        self.font = pygame.font.SysFont("arial", 16)
        self.timer = 0
        self.last_spawn_frame = -999
        self.spawn_interval = DEFAULT_SPAWN_INTERVAL

        self.load_map()
        self.heatmap = Heatmap(self.width, self.height, TILE_SIZE, screen.get_width(), screen.get_height())

        self.time_buttons = self.create_buttons(["Morning", "Midday", "Evening"], y=MAP_HEIGHT * TILE_SIZE + 10)
        self.pause_button = pygame.Rect(650, MAP_HEIGHT * TILE_SIZE + 10, 100, 30)
        self.clear_button = pygame.Rect(760, MAP_HEIGHT * TILE_SIZE + 10, 100, 30)

    def create_buttons(self, labels, y):
        return [ (pygame.Rect(10 + i * 110, y, 100, 30), label) for i, label in enumerate(labels) ]

    def load_map(self):
        try:
            with open("data/city_map.json") as f:
                raw = json.load(f)
            self.width = raw["width"]
            self.height = raw["height"]
            self.map = [[None for _ in range(self.width)] for _ in range(self.height)]
            self.overlays = [[None for _ in range(self.width)] for _ in range(self.height)]
            for tile in raw["tiles"]:
                x, y = tile["x"], tile["y"]
                self.map[y][x] = tile["type"]
                if "overlay" in tile:
                    self.overlays[y][x] = tile["overlay"]
            print("✅ Simulation map loaded.")
        except Exception as e:
            print("❌ Failed to load map:", e)

    def draw_map(self):
        for y in range(self.height):
            for x in range(self.width):
                tile = self.map[y][x]
                if tile in BASE_COLORS:
                    rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    pygame.draw.rect(self.screen, BASE_COLORS[tile], rect)
                    pygame.draw.rect(self.screen, (50, 50, 50), rect, 1)
                overlay = self.overlays[y][x]
                if overlay:
                    center = (x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2)
                    pygame.draw.circle(self.screen, OVERLAY_COLORS[overlay], center, 6)

    def draw_toolbar(self):
        pygame.draw.rect(self.screen, (20, 20, 20), (0, MAP_HEIGHT * TILE_SIZE, self.width * TILE_SIZE, TOOLBAR_HEIGHT))

        for rect, label in self.time_buttons:
            color = (100, 100, 255) if label == self.time_of_day else (180, 180, 180)
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            text = self.font.render(label, True, (0, 0, 0))
            self.screen.blit(text, (rect.x + 10, rect.y + 5))

        pygame.draw.rect(self.screen, (255, 165, 0), self.pause_button, border_radius=6)
        label = "Resume" if self.paused else "Pause"
        self.screen.blit(self.font.render(label, True, (0, 0, 0)), (self.pause_button.x + 10, self.pause_button.y + 5))

        pygame.draw.rect(self.screen, (255, 99, 71), self.clear_button, border_radius=6)
        self.screen.blit(self.font.render("Clear Cars", True, (0, 0, 0)), (self.clear_button.x + 10, self.clear_button.y + 5))

        self.screen.blit(self.font.render("Press BACKSPACE to return to Editor", True, (200, 200, 200)), (10, MAP_HEIGHT * TILE_SIZE + 60))

    def handle_mouse(self):
        mx, my = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0]:
            for rect, label in self.time_buttons:
                if rect.collidepoint(mx, my):
                    self.time_of_day = label
                    self.spawn_interval = 10 if label in ["Morning", "Evening"] else 20
            if self.pause_button.collidepoint(mx, my):
                self.paused = not self.paused
            if self.clear_button.collidepoint(mx, my):
                self.cars.clear()
                print("🚗 All cars cleared.")

    def get_adjacent_road(self, x, y):
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                if self.map[ny][nx] in ["road", "highway", "intersection"]:
                    return (nx, ny)
        return None

    def spawn_car(self):
        if len(self.cars) >= MAX_CARS:
            return

        if self.timer - self.last_spawn_frame < self.spawn_interval:
            return

        homes = [(x, y) for y in range(self.height) for x in range(self.width) if self.map[y][x] == "residential"]
        works = [(x, y) for y in range(self.height) for x in range(self.width) if self.map[y][x] == "workplace"]
        if not homes or not works:
            return

        if self.time_of_day == "Morning":
            raw_start = random.choice(homes)
            raw_end = random.choice(works)
        elif self.time_of_day == "Evening":
            raw_start = random.choice(works)
            raw_end = random.choice(homes)
        else:
            if random.random() < 0.5:
                raw_start = random.choice(homes)
                raw_end = random.choice(works)
            else:
                raw_start = random.choice(works)
                raw_end = random.choice(homes)

        path_start = self.get_adjacent_road(*raw_start)
        path_end = self.get_adjacent_road(*raw_end)

        if not path_start or not path_end:
            print("❌ No adjacent road found for spawn or destination.")
            return

        paths = find_all_paths(self.map, path_start, path_end, max_paths=5)
        if not paths:
            print("❌ No path found from", path_start, "to", path_end)
            return

        path = choose_random_path(paths)
        if not path:
            return

        car = Car(raw_start, raw_end, self.map, self.overlays, self.cars)
        car.path = [raw_start] + path + [raw_end]  # Ensure it reaches the destination tile
        self.cars.append(car)
        self.last_spawn_frame = self.timer
        print("🚗 Spawned car from", raw_start, "to", raw_end)

    def update(self):
        self.handle_mouse()
        self.timer += 1
        self.cars = [car for car in self.cars if not car.reached or car.stop_counter < 60]

        if not self.paused:
            self.spawn_car()
            for car in self.cars:
                car.update()

        self.heatmap.update(self.cars)
        self.heatmap.draw(self.screen)

        self.draw_map()
        for car in self.cars:
            car.draw(self.screen)
        self.draw_toolbar()
