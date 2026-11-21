"""
Prüft die Kartenebenen einer Welt auf Widersprüche und zeigt die Karte an.

Aufruf im Spielverzeichnis:

    python -m world.wildlands.check world.nereid

"""

import sys
from collections import Counter, deque

from .maps import EMPTY
from .world import BLOCKED, CLIMB, SWIM, WALK, get_world


def check_world(world):
    """
    Sucht Fehler in den Kartenebenen.

    Returns:
        list: Meldungen als Text. Leer, wenn alles passt.

    """
    maps = world.maps
    problems = []

    tables = {"biome": world.biomes, "region": world.regions, "overlay": world.overlays}
    for coordinates in maps.iter_coordinates():
        biome_symbol = maps.get("biome", coordinates)
        for layer, table in tables.items():
            symbol = maps.get(layer, coordinates)
            if symbol != EMPTY and symbol not in table:
                problems.append(f"{coordinates}: unbekanntes Zeichen '{symbol}' in '{layer}'.")
        height_symbol = maps.get("height", coordinates)
        if height_symbol != EMPTY and not height_symbol.isdigit():
            problems.append(f"{coordinates}: '{height_symbol}' in 'height' ist keine Ziffer.")
        if biome_symbol == EMPTY:
            for layer in ("height", "region", "overlay"):
                if maps.get(layer, coordinates) != EMPTY:
                    problems.append(f"{coordinates}: Eintrag in '{layer}', aber kein Biom.")

    # Zusammenhang: alle betretbaren Felder sollten von einem aus erreichbar sein
    valid = {coords for coords in maps.iter_coordinates() if world.is_valid(coords)}
    islands = []
    remaining = set(valid)
    while remaining:
        start = remaining.pop()
        island = {start}
        queue = deque([start])
        while queue:
            x, y = queue.popleft()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    neighbor = (x + dx, y + dy)
                    if neighbor in remaining:
                        remaining.discard(neighbor)
                        island.add(neighbor)
                        queue.append(neighbor)
        islands.append(island)
    islands.sort(key=len, reverse=True)
    for island in islands[1:]:
        example = sorted(island)[0]
        problems.append(
            f"{len(island)} Feld(er) bei {example} sind vom Rest der Karte nicht erreichbar."
        )

    return problems


def render(world):
    """Die Karte als Text: Überlagerung vor Biom, wie der Spieler sie sähe."""
    maps = world.maps
    lines = []
    for y in range(maps.height - 1, -1, -1):
        line = ""
        for x in range(maps.width):
            overlay = maps.get("overlay", (x, y))
            line += overlay if overlay != EMPTY else maps.get("biome", (x, y))
        lines.append(f"{y:3d} {line}")
    return "\n".join(lines)


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    world = get_world(argv[1])
    maps = world.maps
    print(f"{world.name}: {maps.width} x {maps.height} Felder\n")
    print(render(world))

    counts = Counter()
    modes = Counter()
    for coordinates in maps.iter_coordinates():
        biome = world.get_biome(coordinates)
        if biome:
            counts[biome.name] += 1
            modes[world.get_movement(coordinates)] += 1
    print("\nBiome: " + ", ".join(f"{name} {count}" for name, count in counts.most_common()))
    print(
        "Bewegung: "
        + ", ".join(
            f"{label} {modes[mode]}"
            for mode, label in (
                (WALK, "gehen"),
                (CLIMB, "klettern"),
                (SWIM, "schwimmen"),
                (BLOCKED, "gesperrt"),
            )
        )
    )

    problems = check_world(world)
    if problems:
        print(f"\n{len(problems)} Problem(e):")
        for problem in problems:
            print("  - " + problem)
        return 1
    print("\nKeine Probleme gefunden.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
