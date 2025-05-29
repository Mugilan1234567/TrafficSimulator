import pygame
import math
import random

TILE_SIZE = 40
CAR_LENGTH = 20
CAR_WIDTH = 10
BASE_SAFE_DISTANCE = 20
LANE_OFFSET = 10
ACCELERATION = 0.08
DECELERATION = 0.15

ROAD_SPEEDS = {
    "road": 1.5,
    "highway": 2.5,
    "intersection": 1.0,
    "residential": 0.8,
    "workplace": 0.8
}

class Car:
    COLORS = [(255, 0, 0), (0, 200, 0), (0, 128, 255), (255, 165, 0), (160, 32, 240)]

    def __init__(self, start, destination, grid, overlays, cars):
        self.grid = grid
        self.overlays = overlays
        self.other_cars = cars
        self.path = []
        self.index = 0
        self.start = start
        self.end = destination
        self.x = start[0] * TILE_SIZE + TILE_SIZE // 2
        self.y = start[1] * TILE_SIZE + TILE_SIZE // 2
        self.dest_x = self.x
        self.dest_y = self.y
        self.speed = 0.0
        self.max_speed = 2.5
        self.color = random.choice(Car.COLORS)
        self.reached = False
        self.stop_counter = 0
        self.rotation = 0
        self.age = 0  # Number of frames since spawn

        self.personality = random.choice(["normal", "cautious", "aggressive"])
        self.blinker = None
        self.blink_timer = 0

    def get_tile_type(self, grid_x, grid_y):
        if 0 <= grid_y < len(self.grid) and 0 <= grid_x < len(self.grid[0]):
            return self.grid[grid_y][grid_x]
        return None

    def current_tile(self):
        return self.path[self.index] if self.index < len(self.path) else None

    def next_tile(self):
        return self.path[self.index + 1] if self.index + 1 < len(self.path) else None

    def tile_center(self, tile):
        return (tile[0] * TILE_SIZE + TILE_SIZE // 2, tile[1] * TILE_SIZE + TILE_SIZE // 2)

    def get_lane_offset(self, curr, nxt):
        dx = nxt[0] - curr[0]
        dy = nxt[1] - curr[1]
        if dx == 1: return (0, LANE_OFFSET)
        if dx == -1: return (0, -LANE_OFFSET)
        if dy == 1: return (-LANE_OFFSET, 0)
        if dy == -1: return (LANE_OFFSET, 0)
        return (0, 0)

    def is_too_close_to_front_car(self):
        if not self.next_tile():
            return False

        dx = self.dest_x - self.x
        dy = self.dest_y - self.y
        mag = math.hypot(dx, dy)
        if mag == 0:
            return False
        dir_x = dx / mag
        dir_y = dy / mag

        safe_distance = BASE_SAFE_DISTANCE
        if self.personality == "cautious":
            safe_distance += 8
        elif self.personality == "aggressive":
            safe_distance -= 2

        for other in self.other_cars:
            if other is self or other.reached:
                continue
            ox = other.x - self.x
            oy = other.y - self.y
            dist = math.hypot(ox, oy)
            try:
                if dist < safe_distance:
                    dot = (ox * dir_x + oy * dir_y) / dist
                    if dot > 0.5:
                        return True
            except ZeroDivisionError:
                print("⚠️ ZeroDivisionError caught in car logic. Marking car as reached.")
                self.reached = True
                return False

        return False

    def should_yield(self):
        curr = self.current_tile()
        nxt = self.next_tile()
        if not curr or not nxt:
            return False

        tile_type = self.get_tile_type(*nxt)
        if tile_type not in ["intersection", "highway"]:
            return False

        if tile_type == "highway":
            return False

        for other in self.other_cars:
            if other is self or other.reached:
                continue
            other_curr = other.current_tile()
            other_nxt = other.next_tile()
            if not other_curr or not other_nxt:
                continue
            if other_nxt == nxt:
                self_dist = math.hypot(self.x - self.dest_x, self.y - self.dest_y)
                other_dist = math.hypot(other.x - other.dest_x, other.y - other.dest_y)
                if other_dist < self_dist:
                    return True
        return False

    def compute_bezier_target(self, curr, nxt):
        cx, cy = self.tile_center(curr)
        nx, ny = self.tile_center(nxt)
        mx, my = (cx + nx) / 2, (cy + ny) / 2
        offset_x, offset_y = self.get_lane_offset(curr, nxt)
        return mx + offset_x, my + offset_y

    def update(self):
        self.age += 1
        if self.reached:
            self.stop_counter += 1
            return

        if not self.path or self.index >= len(self.path):
            self.reached = True
            return

        curr = self.current_tile()
        nxt = self.next_tile()

        if nxt:
            self.dest_x, self.dest_y = self.compute_bezier_target(curr, nxt)
        else:
            self.dest_x, self.dest_y = self.tile_center(curr)

        dx = self.dest_x - self.x
        dy = self.dest_y - self.y
        distance = math.hypot(dx, dy)

        if distance < 1.5:
            self.index += 1
            if self.index >= len(self.path):
                self.reached = True
            return

        if distance > 0:
            dx_unit = dx / distance
            dy_unit = dy / distance
            self.rotation = math.degrees(math.atan2(dy_unit, dx_unit))

        grid_x = int(self.x // TILE_SIZE)
        grid_y = int(self.y // TILE_SIZE)
        tile_type = self.get_tile_type(grid_x, grid_y)
        target_speed = ROAD_SPEEDS.get(tile_type, 1.0)

        if self.personality == "cautious":
            target_speed *= 0.8
        elif self.personality == "aggressive":
            target_speed *= 1.2

        if self.index >= len(self.path) - 1:
            target_speed = min(target_speed, 1.0)

        if self.age > 30 and (self.is_too_close_to_front_car() or self.should_yield()):
            target_speed = 0.0

        if self.speed < target_speed:
            self.speed = min(self.speed + ACCELERATION, target_speed)
        else:
            self.speed = max(self.speed - DECELERATION, target_speed)

        if distance != 0:
            dx /= distance
            dy /= distance
            self.x += dx * self.speed
            self.y += dy * self.speed

    def draw(self, screen):
        surface = pygame.Surface((CAR_LENGTH, CAR_WIDTH), pygame.SRCALPHA)
        pygame.draw.rect(surface, self.color, (0, 0, CAR_LENGTH, CAR_WIDTH), border_radius=6)
        pygame.draw.circle(surface, (255, 255, 200), (CAR_LENGTH - 2, 3), 2)
        pygame.draw.circle(surface, (255, 255, 200), (CAR_LENGTH - 2, CAR_WIDTH - 3), 2)

        if self.blinker == "left" and (pygame.time.get_ticks() // 300) % 2 == 0:
            pygame.draw.circle(surface, (255, 255, 0), (2, 3), 2)
        elif self.blinker == "right" and (pygame.time.get_ticks() // 300) % 2 == 0:
            pygame.draw.circle(surface, (255, 255, 0), (2, CAR_WIDTH - 3), 2)

        rotated = pygame.transform.rotate(surface, -self.rotation)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(rotated, rect)
