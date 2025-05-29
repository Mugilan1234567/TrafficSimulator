import pygame
import json
import os

TILE_SIZE = 40
MAP_WIDTH, MAP_HEIGHT = 30, 20
TOOLBAR_HEIGHT = 130

BASE_COLORS = {
    "residential": (102, 204, 255),
    "workplace": (255, 223, 88),
    "road": (150, 150, 150),
    "highway": (255, 99, 71),  # tomato red
    "intersection": (100, 255, 100),  # light green
    "erase": (30, 30, 30)
}

OVERLAY_COLORS = {
    "stop_sign": (220, 20, 60),      # crimson
    "traffic_light": (0, 191, 255),  # deep sky blue
}

TOOLS = ["residential", "workplace", "road", "highway", "intersection", "erase"]
OVERLAYS = ["stop_sign", "traffic_light"]

class MapEditor:
    def __init__(self, screen):
        self.screen = screen
        self.map = [[None for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        self.overlays = [[None for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        self.current_tool = "road"
        self.mode = "tile"  # or "overlay"
        self.font = pygame.font.SysFont("arial", 16)
        self.base_buttons = self.create_buttons(TOOLS, top=MAP_HEIGHT * TILE_SIZE + 10)
        self.overlay_buttons = self.create_buttons(OVERLAYS, top=MAP_HEIGHT * TILE_SIZE + 50)
        self.mode_button = pygame.Rect(900, MAP_HEIGHT * TILE_SIZE + 10, 120, 30)

    def create_buttons(self, items, top):
        buttons = []
        for i, name in enumerate(items):
            rect = pygame.Rect(10 + i * 110, top, 100, 30)
            buttons.append((rect, name))
        return buttons

    def draw_grid(self):
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                tile_type = self.map[y][x]
                if tile_type:
                    pygame.draw.rect(self.screen, BASE_COLORS[tile_type], rect)
                pygame.draw.rect(self.screen, (50, 50, 50), rect, 1)
                # Overlay
                overlay = self.overlays[y][x]
                if overlay:
                    center = rect.center
                    radius = 6
                    pygame.draw.circle(self.screen, OVERLAY_COLORS[overlay], center, radius)

    def draw_toolbar(self):
        pygame.draw.rect(self.screen, (20, 20, 20), (0, MAP_HEIGHT * TILE_SIZE, MAP_WIDTH * TILE_SIZE, TOOLBAR_HEIGHT))

        # Draw tile buttons
        label = self.font.render("Base Tiles", True, (255, 255, 255))
        self.screen.blit(label, (10, MAP_HEIGHT * TILE_SIZE - 20))
        for rect, name in self.base_buttons:
            color = BASE_COLORS[name]
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            text = self.font.render(name.capitalize(), True, (0, 0, 0))
            self.screen.blit(text, (rect.x + 5, rect.y + 5))

        # Draw overlay buttons
        label = self.font.render("Overlays", True, (255, 255, 255))
        self.screen.blit(label, (10, MAP_HEIGHT * TILE_SIZE + 40))
        for rect, name in self.overlay_buttons:
            color = OVERLAY_COLORS[name]
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            text = self.font.render(name.replace('_', ' ').capitalize(), True, (0, 0, 0))
            self.screen.blit(text, (rect.x + 5, rect.y + 5))

        # Draw mode toggle
        mode_label = self.font.render("Mode: " + self.mode.upper(), True, (255, 255, 255))
        pygame.draw.rect(self.screen, (60, 60, 60), self.mode_button, border_radius=6)
        self.screen.blit(mode_label, (self.mode_button.x + 10, self.mode_button.y + 5))

        # Instructions
        instructions = [
            "Left Click: Draw / Select",
            "Press S to Save, L to Load",
            "ENTER to Simulate, BACKSPACE to return"
        ]
        for i, text in enumerate(instructions):
            instr = self.font.render(text, True, (200, 200, 200))
            self.screen.blit(instr, (10, MAP_HEIGHT * TILE_SIZE + 90 + i * 15))

    def save_map(self):
        os.makedirs("data", exist_ok=True)
        data = []
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if self.map[y][x]:
                    tile = {"x": x, "y": y, "type": self.map[y][x]}
                    if self.overlays[y][x]:
                        tile["overlay"] = self.overlays[y][x]
                    data.append(tile)
        with open("data/city_map.json", "w") as f:
            json.dump({
                "tile_size": TILE_SIZE,
                "width": MAP_WIDTH,
                "height": MAP_HEIGHT,
                "tiles": data
            }, f, indent=2)
        print("✅ Map saved.")

    def load_map(self):
        try:
            with open("data/city_map.json") as f:
                raw = json.load(f)
            self.map = [[None for _ in range(raw["width"])] for _ in range(raw["height"])]
            self.overlays = [[None for _ in range(raw["width"])] for _ in range(raw["height"])]
            for tile in raw["tiles"]:
                x, y = tile["x"], tile["y"]
                self.map[y][x] = tile["type"]
                if "overlay" in tile:
                    self.overlays[y][x] = tile["overlay"]
            print("✅ Map loaded.")
        except Exception as e:
            print("❌ Failed to load map:", e)

    def handle_mouse(self):
        mx, my = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0]:
            # Clicked in map grid
            if my < MAP_HEIGHT * TILE_SIZE:
                gx, gy = mx // TILE_SIZE, my // TILE_SIZE
                if 0 <= gx < MAP_WIDTH and 0 <= gy < MAP_HEIGHT:
                    if self.current_tool == "erase":
                        self.map[gy][gx] = None
                        self.overlays[gy][gx] = None
                    elif self.mode == "tile":
                        self.map[gy][gx] = self.current_tool
                    elif self.mode == "overlay":
                        base = self.map[gy][gx]
                        if base in ["road", "highway", "intersection"]:
                            self.overlays[gy][gx] = self.current_tool
            else:
                # Clicked a base button
                for rect, name in self.base_buttons:
                    if rect.collidepoint(mx, my):
                        self.current_tool = name
                        self.mode = "tile"
                for rect, name in self.overlay_buttons:
                    if rect.collidepoint(mx, my):
                        self.current_tool = name
                        self.mode = "overlay"
                if self.mode_button.collidepoint(mx, my):
                    self.mode = "overlay" if self.mode == "tile" else "tile"

    def handle_keyboard(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_s]: self.save_map()
        if keys[pygame.K_l]: self.load_map()

    def update(self):
        self.handle_keyboard()
        self.handle_mouse()
        self.draw_grid()
        self.draw_toolbar()
