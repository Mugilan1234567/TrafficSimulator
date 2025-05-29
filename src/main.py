### File: `main.py`
import pygame
from src.map_editor import MapEditor
from src.simulation import Simulation

pygame.init()

WIDTH, HEIGHT = 1200, 800 + 100
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("EcoRoute Traffic Simulator")
clock = pygame.time.Clock()

editor = MapEditor(screen)
simulation = Simulation(screen)

mode = "editor"  # can be "editor" or "simulation"

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                mode = "simulation"
            elif event.key == pygame.K_BACKSPACE:
                mode = "editor"

    screen.fill((30, 30, 30))
    if mode == "editor":
        editor.update()
    else:
        simulation.update()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()