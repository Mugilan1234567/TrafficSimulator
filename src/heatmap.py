import numpy as np
import pygame
from scipy.ndimage import gaussian_filter

class Heatmap:
    def __init__(self, grid_width, grid_height, tile_size, screen_width, screen_height, decay=0.92, blur_sigma=1.6):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.tile_size = tile_size
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.decay = decay
        self.blur_sigma = blur_sigma

        self.heatmap_data = np.zeros((grid_height, grid_width), dtype=np.float32)
        self.last_blurred = np.zeros_like(self.heatmap_data)
        self.surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        self.update_counter = 0

    def update(self, cars):
        self.heatmap_data *= self.decay
        for car in cars:
            if car.reached:
                continue
            gx = int(car.x // self.tile_size)
            gy = int(car.y // self.tile_size)
            if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height:
                self.heatmap_data[gy, gx] += 1.0

        self.update_counter += 1
        if self.update_counter % 3 == 0:
            self.last_blurred = gaussian_filter(self.heatmap_data, sigma=self.blur_sigma)
            self.update_surface()

    def update_surface(self):
        normalized = self.last_blurred / np.max(self.last_blurred) if np.max(
            self.last_blurred) > 0 else self.last_blurred
        img = np.zeros((self.grid_height, self.grid_width, 4), dtype=np.uint8)

        r = (255 * np.clip(normalized * 2, 0, 1)).astype(np.uint8)
        g = (255 * (1 - normalized)).astype(np.uint8)
        b = np.zeros_like(r)
        a = (200 * normalized).astype(np.uint8)

        img[..., 0] = r
        img[..., 1] = g
        img[..., 2] = b
        img[..., 3] = a

        # Convert to pygame surface with alpha support
        surface_rgba = pygame.image.frombuffer(
            img.tobytes(), (self.grid_width, self.grid_height), "RGBA"
        )
        surface_rgba = surface_rgba.convert_alpha()

        # Smooth scale to screen size
        self.surface = pygame.transform.smoothscale(surface_rgba, (self.screen_width, self.screen_height))

    def draw(self, screen):
        screen.blit(self.surface, (0, 0))
