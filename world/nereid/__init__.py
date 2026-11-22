"""
Nereid - Testwelt für die Wildnis.

Enthält nur Inhalt: Kartenebenen (im Verzeichnis `maps`), Biome, Regionen,
Überlagerungen und Texte. Die Mechanik liegt in `world.wildlands`.

"""

from pathlib import Path

from world.wildlands.sentences import SentenceBook
from world.wildlands.weather import WeatherConfig
from world.wildlands.world import WorldDefinition

from .biomes import BIOMES, DETAILS, OVERLAYS, REGIONS
from .portals import PORTALS
from .sentences import SENTENCES

WORLD = WorldDefinition(
    name="Nereid",
    map_directory=Path(__file__).parent / "maps",
    biomes=BIOMES,
    regions=REGIONS,
    overlays=OVERLAYS,
    details=DETAILS,
    seed=4711,
    # Die Testkarte ist nur 50 Felder breit, deshalb kleine, langsame Fronten.
    # Für eine Karte mit 150 Feldern passen front_size=40 und wind_speed=6.
    weather=WeatherConfig(front_size=16.0, wind=(1.0, 0.25), wind_speed=2.0),
    sentences=SentenceBook(SENTENCES),
    portals=PORTALS,
)
