"""
Nereid - Testwelt für die Wildnis.

Enthält nur Inhalt: Kartenebenen (im Verzeichnis `maps`), Biome, Regionen,
Überlagerungen und Texte. Die Mechanik liegt in `world.wildlands`.

"""

from pathlib import Path

from world.wildlands.world import WorldDefinition

from .biomes import BIOMES, DETAILS, OVERLAYS, REGIONS

WORLD = WorldDefinition(
    name="Nereid",
    map_directory=Path(__file__).parent / "maps",
    biomes=BIOMES,
    regions=REGIONS,
    overlays=OVERLAYS,
    details=DETAILS,
    seed=4711,
)
