"""
Beschreibung einer Welt: Biome, Regionen, Überlagerungen und Kartenebenen.

Eine konkrete Welt (z.B. `world.nereid`) legt ein `WorldDefinition`-Objekt
namens `WORLD` an. Die Mechanik holt es über `get_world("world.nereid")`.

"""

import zlib
from dataclasses import dataclass, field
from importlib import import_module

from .maps import EMPTY, MapLayers

# Fortbewegungsarten
WALK = "walk"
CLIMB = "climb"
SWIM = "swim"
BLOCKED = "blocked"

# Höhenbänder für Texte: (höchstes Level des Bandes, Name)
HEIGHT_BANDS = ((2, "tief"), (5, "mittel"), (7, "hoch"), (9, "alpin"))

# (dx, dy) der vier Hauptrichtungen, mit deutschem Namen
CARDINALS = (
    ((0, 1), "Norden"),
    ((1, 0), "Osten"),
    ((0, -1), "Süden"),
    ((-1, 0), "Westen"),
)


@dataclass(frozen=True)
class Biome:
    """
    Eine Geländeart.

    Attributes:
        key: Interner Name, z.B. "forest". Wird später in Satzbedingungen benutzt.
        symbol: Zeichen in der Biom-Ebene.
        name: Anzeigename, z.B. "Wald".
        movement: `WALK`, `CLIMB`, `SWIM` oder `BLOCKED`.
        height: Standardhöhe 0-9, falls die Höhen-Ebene nichts vorgibt.
        afar: Wie das Biom vom Nachbarfeld aus aussieht, im Akkusativ
            ("dichten Wald"). Leer = wird nicht erwähnt.
        descs: Varianten der Grundbeschreibung.
        details: Mit `look <name>` ansehbare Details, `{"name": "Text"}`.
            Mehrere Namen für einen Text mit `;` trennen.

    """

    key: str
    symbol: str
    name: str
    movement: str = WALK
    height: int = 2
    afar: str = ""
    descs: tuple = ()
    details: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Region:
    """Ein benanntes Gebiet. `symbol` ist das Zeichen in der Regionen-Ebene."""

    key: str
    symbol: str
    name: str
    details: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Overlay:
    """
    Etwas, das über dem Biom liegt, z.B. eine Straße.

    Attributes:
        walkable: Wenn True, kann man hier gehen, auch wenn das Biom sonst
            Klettern oder Schwimmen verlangt (Brücke, Passstraße). Name und
            Beschreibung der Überlagerung ersetzen dann die des Bioms.
        descs: Varianten des Satzes, der an die Beschreibung angehängt wird.

    """

    key: str
    symbol: str
    name: str
    walkable: bool = False
    descs: tuple = ()
    details: dict = field(default_factory=dict)


def expand_details(details):
    """`{"a;b": text}` zu `{"a": text, "b": text}` auflösen (klein geschrieben)."""
    result = {}
    for names, text in details.items():
        for name in names.split(";"):
            if name.strip():
                result[name.strip().lower()] = text
    return result


class WorldDefinition:
    """
    Alles, was die Mechanik über eine Welt wissen muss.

    Args:
        name (str): Name der Welt.
        map_directory (str or Path): Verzeichnis mit `biome.map`, `height.map`,
            `region.map` und `overlay.map`.
        biomes, regions, overlays (iterable): Die Tabellen der Welt.
        seed (int): Startwert für alles Pseudozufällige.
        details (dict): Details, die überall gelten.

    """

    layer_names = ("biome", "height", "region", "overlay")

    def __init__(self, name, map_directory, biomes, regions=(), overlays=(), seed=0, details=None):
        self.name = name
        self.map_directory = map_directory
        self.seed = seed
        self.biomes = {biome.symbol: biome for biome in biomes}
        self.regions = {region.symbol: region for region in regions}
        self.overlays = {overlay.symbol: overlay for overlay in overlays}
        self.details = details or {}
        self._maps = None

    @property
    def maps(self):
        """Die Kartenebenen; werden beim ersten Zugriff geladen."""
        if self._maps is None:
            self._maps = MapLayers(self.map_directory, self.layer_names)
        return self._maps

    # Abfragen pro Koordinate

    def get_biome(self, coordinates):
        """Biom an der Koordinate oder None, wenn das Feld nicht existiert."""
        return self.biomes.get(self.maps.get("biome", coordinates))

    def get_region(self, coordinates):
        return self.regions.get(self.maps.get("region", coordinates))

    def get_overlay(self, coordinates):
        return self.overlays.get(self.maps.get("overlay", coordinates))

    def get_height(self, coordinates):
        """Höhenlevel 0-9: aus der Höhen-Ebene, sonst Standardhöhe des Bioms."""
        symbol = self.maps.get("height", coordinates)
        if symbol.isdigit():
            return int(symbol)
        biome = self.get_biome(coordinates)
        return biome.height if biome else 0

    def get_height_band(self, coordinates):
        """Name des Höhenbandes ("tief", "mittel", "hoch", "alpin")."""
        height = self.get_height(coordinates)
        for upper, band in HEIGHT_BANDS:
            if height <= upper:
                return band
        return HEIGHT_BANDS[-1][1]

    def get_movement(self, coordinates):
        """Fortbewegungsart, die dieses Feld verlangt."""
        biome = self.get_biome(coordinates)
        if not biome:
            return BLOCKED
        overlay = self.get_overlay(coordinates)
        if overlay and overlay.walkable:
            return WALK
        return biome.movement

    def is_valid(self, coordinates):
        """True, wenn man das Feld überhaupt betreten kann."""
        return self.get_movement(coordinates) != BLOCKED

    def required_movement(self, start, target):
        """
        Fortbewegungsart für einen Schritt von `start` nach `target`.

        Jede Bewegung, die ein Kletter- oder Schwimmfeld berührt, verlangt diese
        Fortbewegungsart. Verlangen Start und Ziel verschiedene Arten, zählt
        das Ziel.

        """
        target_mode = self.get_movement(target)
        if target_mode != WALK:
            return target_mode
        return self.get_movement(start)

    # Pseudozufall

    def pick(self, options, coordinates, salt=""):
        """
        Wählt stabil eine der `options` für diese Koordinate.

        Dieselbe Koordinate ergibt immer dieselbe Wahl, auch nach einem
        Neustart. `salt` unterscheidet mehrere unabhängige Auswahlen.

        """
        if not options:
            return ""
        x, y = coordinates
        value = zlib.crc32(f"{self.seed}:{x}:{y}:{salt}".encode())
        return options[value % len(options)]

    # Texte

    @staticmethod
    def _overlay_replaces_biome(biome, overlay):
        """
        True, wenn die Überlagerung das Biom für den Spieler ersetzt: Auf einer
        Brücke steht man nicht im See, also gelten Name und Beschreibung der
        Brücke statt die des Sees.

        """
        return bool(overlay and overlay.walkable and biome.movement != WALK)

    def get_location_name(self, coordinates):
        biome = self.get_biome(coordinates)
        region = self.get_region(coordinates)
        if not biome:
            return "Nirgendwo"
        overlay = self.get_overlay(coordinates)
        name = overlay.name if self._overlay_replaces_biome(biome, overlay) else biome.name
        if region:
            return f"{region.name} ({name})"
        return name

    def get_details(self, coordinates):
        """Alle Details dieses Feldes. Speziellere überschreiben allgemeinere."""
        details = expand_details(self.details)
        for source in (
            self.get_biome(coordinates),
            self.get_region(coordinates),
            self.get_overlay(coordinates),
        ):
            if source:
                details.update(expand_details(source.details))
        return details

    def describe_surroundings(self, coordinates):
        """Sätze über abweichendes Gelände auf den vier Nachbarfeldern."""
        here = self.get_biome(coordinates)
        seen = {}
        x, y = coordinates
        for (dx, dy), direction in CARDINALS:
            neighbor = self.get_biome((x + dx, y + dy))
            if neighbor and neighbor is not here and neighbor.afar:
                seen.setdefault(neighbor.afar, []).append(direction)
        sentences = []
        for afar, directions in seen.items():
            if len(directions) > 1:
                where = ", ".join(directions[:-1]) + " und " + directions[-1]
            else:
                where = directions[0]
            sentences.append(f"Im {where} siehst du {afar}.")
        return sentences

    def describe(self, coordinates, looker=None):
        """
        Setzt die Beschreibung eines Feldes zusammen.

        Returns:
            str: Die Beschreibung. Wird bei jedem `look` neu berechnet.

        """
        biome = self.get_biome(coordinates)
        if not biome:
            return "Hier ist nichts."
        overlay = self.get_overlay(coordinates)
        sentences = []
        if not self._overlay_replaces_biome(biome, overlay):
            sentences.append(self.pick(biome.descs, coordinates, "biome"))
        if overlay:
            sentences.append(self.pick(overlay.descs, coordinates, "overlay"))
        sentences.extend(self.describe_surroundings(coordinates))
        return " ".join(sentence for sentence in sentences if sentence)


def get_world(path):
    """
    Holt die Weltdefinition aus einem Modul.

    Args:
        path (str): Python-Pfad des Welt-Pakets, z.B. "world.nereid".

    Returns:
        WorldDefinition: Das Objekt `WORLD` des Moduls.

    """
    return import_module(path).WORLD


__all__ = (
    "BLOCKED",
    "CLIMB",
    "EMPTY",
    "SWIM",
    "WALK",
    "Biome",
    "Overlay",
    "Region",
    "WorldDefinition",
    "get_world",
)
