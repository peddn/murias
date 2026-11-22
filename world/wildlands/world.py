"""
Beschreibung einer Welt: Biome, Regionen, Überlagerungen und Kartenebenen.

Eine konkrete Welt (z.B. `world.nereid`) legt ein `WorldDefinition`-Objekt
namens `WORLD` an. Die Mechanik holt es über `get_world("world.nereid")`.

"""

import zlib
from dataclasses import dataclass, field
from importlib import import_module

from .maps import EMPTY, MapLayers
from .weather import HOUR, WeatherModel, season, time_of_day

# Fortbewegungsarten
WALK = "walk"
CLIMB = "climb"
SWIM = "swim"
BLOCKED = "blocked"

# Höhenbänder für Texte: (höchstes Level des Bandes, Name)
HEIGHT_BANDS = ((2, "tief"), (5, "mittel"), (7, "hoch"), (9, "alpin"))

# Themen der Wettersätze in der Reihenfolge, in der sie in der Beschreibung
# stehen. "nebel" steht am Ende und ersetzt die Sätze über Nachbarfelder.
WEATHER_TOPICS = ("himmel", "niederschlag", "wind", "temperatur", "boden", "trend")

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
        moisture: Klima, feuchter (+) oder trockener (-), etwa -0.2 bis 0.2.
        warmth: Klima in Grad wärmer (+) oder kälter (-).
        shelter: Windschutz in Stufen. 1 = eine Stufe weniger Wind spürbar,
            -1 = ausgesetzt, eine Stufe mehr.
        open_sky: False, wenn man den Himmel hier kaum sieht (dichter Wald).
        dries: Stunden, die der Boden nach Regen nass bleibt. 0 = der Boden
            spielt hier keine Rolle (Wasser, nackter Fels).
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
    moisture: float = 0.0
    warmth: float = 0.0
    shelter: int = 0
    open_sky: bool = True
    dries: int = 3
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
        weather (WeatherConfig): Stellschrauben des Wetters. Ohne sie gibt es
            kein Wetter.
        sentences (SentenceBook): Sätze für Wetter und Umwelt.

    """

    layer_names = ("biome", "height", "region", "overlay")

    def __init__(
        self,
        name,
        map_directory,
        biomes,
        regions=(),
        overlays=(),
        seed=0,
        details=None,
        weather=None,
        sentences=None,
    ):
        self.name = name
        self.map_directory = map_directory
        self.seed = seed
        self.biomes = {biome.symbol: biome for biome in biomes}
        self.regions = {region.symbol: region for region in regions}
        self.overlays = {overlay.symbol: overlay for overlay in overlays}
        self.details = details or {}
        self.weather_config = weather
        self.sentences = sentences
        self._maps = None
        self._weather_model = None
        self._time_offset = None

    @property
    def maps(self):
        """Die Kartenebenen; werden beim ersten Zugriff geladen."""
        if self._maps is None:
            self._maps = MapLayers(self.map_directory, self.layer_names)
        return self._maps

    # Zeit

    @property
    def _offset_key(self):
        return f"wildlands_time_offset_{self.name.lower()}"

    @property
    def time_offset(self):
        """
        Verschiebung der Wetterzeit in Sekunden. Zum Testen und Abstimmen:
        damit lässt sich das Wetter vor- und zurückspulen, ohne die Spielzeit
        anzufassen. Wird in der Datenbank gehalten.

        """
        if self._time_offset is None:
            from evennia.server.models import ServerConfig

            self._time_offset = ServerConfig.objects.conf(self._offset_key, default=0.0)
        return self._time_offset

    @time_offset.setter
    def time_offset(self, seconds):
        from evennia.server.models import ServerConfig

        ServerConfig.objects.conf(self._offset_key, float(seconds))
        self._time_offset = float(seconds)

    def now(self):
        """Aktuelle Spielzeit in Sekunden, einschließlich der Verschiebung."""
        from evennia.utils import gametime

        return gametime.gametime(absolute=True) + self.time_offset

    # Wetter

    @property
    def weather_model(self):
        if self._weather_model is None and self.weather_config:
            self._weather_model = WeatherModel(self.weather_config, self.seed, self.maps.height)
        return self._weather_model

    def get_weather(self, coordinates, t):
        """
        Wetter an einer Koordinate, wie es dort gemessen würde.

        Returns:
            Weather or None: None, wenn die Welt kein Wetter hat oder das Feld
            nicht existiert.

        """
        biome = self.get_biome(coordinates)
        if not biome or not self.weather_model:
            return None
        return self.weather_model.at(
            coordinates,
            t,
            height=self.get_height(coordinates),
            moisture=biome.moisture,
            warmth=biome.warmth,
            shelter=biome.shelter,
        )

    def get_state(self, coordinates, t):
        """
        Alles, was Sätze über ein Feld wissen dürfen, als Dict.

        Schlüssel: biom, band, bewegung, ueberlagerung, region, tageszeit,
        jahreszeit und, falls die Welt Wetter hat: himmel, niederschlag, wind,
        temperatur, nebel, gewitter, sicht (frei, verdeckt, nebel), boden
        (trocken, nass, schnee), trend (aufzug, abzug, gleich), woher.

        """
        biome = self.get_biome(coordinates)
        overlay = self.get_overlay(coordinates)
        region = self.get_region(coordinates)
        state = {
            "biom": biome.key if biome else "",
            "band": self.get_height_band(coordinates),
            "bewegung": self.get_movement(coordinates),
            "ueberlagerung": overlay.key if overlay else "",
            "region": region.key if region else "",
            "tageszeit": time_of_day(t),
            "jahreszeit": season(t),
        }
        weather = self.get_weather(coordinates, t)
        if not weather:
            return state
        state.update(weather.as_state())
        # Im Nebel sieht man weder Himmel noch Ferne, unter Bäumen kaum.
        if weather.fog:
            state["sicht"] = "nebel"
        else:
            state["sicht"] = "frei" if biome.open_sky else "verdeckt"
        state["woher"] = self.weather_model.wind_origin

        # Gedächtnis: Das Wetter ist eine Funktion der Zeit, also lässt sich
        # die Vergangenheit einfach noch einmal abfragen.
        state["boden"] = "trocken"
        if biome.dries:
            if weather.is_snow or (
                weather.temperature < 1.0
                and any(
                    self.get_weather(coordinates, t - hours * HOUR).is_snow for hours in (2, 5)
                )
            ):
                state["boden"] = "schnee"
            elif weather.is_wet:
                state["boden"] = "nass"
            else:
                for hours in (1, 3, 6, 12):
                    if hours > biome.dries:
                        break
                    if self.get_weather(coordinates, t - hours * HOUR).is_wet:
                        state["boden"] = "nass"
                        break

        # Trend: Was in zwei Stunden hier ist, steht jetzt windaufwärts.
        soon = self.get_weather(coordinates, t + 2 * HOUR)
        now_dry = weather.precipitation == "kein"
        soon_dry = soon.precipitation == "kein"
        if now_dry and not soon_dry:
            state["trend"] = "aufzug"
        elif not now_dry and soon_dry:
            state["trend"] = "abzug"
        else:
            state["trend"] = "gleich"
        return state

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

    def describe_weather(self, coordinates, t, topics=None):
        """
        Sätze über Wetter und Umwelt an einer Koordinate.

        Die Wahl zwischen gleichwertigen Varianten bleibt eine Spielstunde
        lang stabil und unterscheidet sich von Feld zu Feld.

        Args:
            topics (iterable): Themen in der gewünschten Reihenfolge.
                Standard: `WEATHER_TOPICS`.

        Returns:
            list: Die Sätze, ohne leere.

        """
        if not self.sentences or not self.weather_model:
            return []
        state = self.get_state(coordinates, t)
        hour = int(t // HOUR)

        def pick(options, salt):
            return self.pick(options, coordinates, f"{salt}:{hour}")

        sentences = (
            self.sentences.choose(topic, state, pick) for topic in topics or WEATHER_TOPICS
        )
        return [sentence for sentence in sentences if sentence]

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

    def get_details(self, coordinates, t=None):
        """
        Alle Details dieses Feldes. Speziellere überschreiben allgemeinere.

        Mit Wetter kommen "wetter" und, wo man ihn sieht, "himmel" dazu. Sie
        werden aus den Wettersätzen gebildet.

        """
        details = expand_details(self.details)
        biome = self.get_biome(coordinates)
        if biome and self.sentences and self.weather_model:
            t = self.now() if t is None else t
            weather = " ".join(self.describe_weather(coordinates, t))
            if weather:
                details["wetter"] = weather
            sky = " ".join(
                self.describe_weather(coordinates, t, topics=("himmel", "niederschlag", "trend"))
            )
            if sky and biome.open_sky:
                details["himmel"] = sky
        for source in (biome, self.get_region(coordinates), self.get_overlay(coordinates)):
            if source:
                source_details = expand_details(source.details)
                if "himmel" in details and biome and biome.open_sky:
                    # der berechnete Himmel geht vor einem festen Text
                    source_details.pop("himmel", None)
                details.update(source_details)
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

    def describe(self, coordinates, looker=None, t=None):
        """
        Setzt die Beschreibung eines Feldes zusammen.

        Args:
            t (float): Spielzeit in Sekunden. Standard: jetzt.

        Returns:
            str: Die Beschreibung. Wird bei jedem `look` neu berechnet.

        """
        biome = self.get_biome(coordinates)
        if not biome:
            return "Hier ist nichts."
        if t is None and self.weather_model:
            t = self.now()
        overlay = self.get_overlay(coordinates)
        sentences = []
        if not self._overlay_replaces_biome(biome, overlay):
            sentences.append(self.pick(biome.descs, coordinates, "biome"))
        if overlay:
            sentences.append(self.pick(overlay.descs, coordinates, "overlay"))
        fog = ""
        if self.weather_model:
            sentences.extend(self.describe_weather(coordinates, t))
            fog = " ".join(self.describe_weather(coordinates, t, topics=("nebel",)))
        # im Nebel sieht man die Nachbarfelder nicht
        if fog:
            sentences.append(fog)
        else:
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
