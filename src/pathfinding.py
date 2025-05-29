import random
from collections import deque

# Global cache dictionary
path_cache = {}

# Adjustable car spawn rate
CAR_SPAWN_RATE = 5  # Lower means more frequent spawning (e.g., 1 = spawn every frame)

def find_all_paths(grid, start, end, max_paths=10, max_depth=200):
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    def neighbors(x, y):
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                yield nx, ny

    results = []
    queue = deque()
    queue.append(([start], set([start])))

    while queue and len(results) < max_paths:
        path, visited = queue.popleft()
        x, y = path[-1]

        if (x, y) == end:
            results.append(path)
            continue

        if len(path) >= max_depth:
            continue

        for nx, ny in neighbors(x, y):
            if grid[ny][nx] in ["road", "highway", "intersection", "residential", "workplace"] and (nx, ny) not in visited:
                queue.append((path + [(nx, ny)], visited | {(nx, ny)}))

    return results if results else [[]]  # Ensure at least an empty list is returned if no path

def get_cached_paths(grid, start, end, max_paths=10, max_depth=200):
    key = (start, end)
    if key not in path_cache:
        path_cache[key] = find_all_paths(grid, start, end, max_paths, max_depth)
    return path_cache[key]

def choose_random_path(paths):
    if not paths or all(len(p) == 0 for p in paths):
        return []

    valid_paths = [p for p in paths if len(p) > 0]
    return random.choice(valid_paths)
