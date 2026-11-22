"""
Wetter als reine Funktion von Ort und Zeit.

Mehrere Rauschfelder (Luftdruck, Wolken, Feuchte, Temperatur) werden mit einem
festen Wind über die Karte geschoben und verformen sich dabei langsam. Nichts
wird gespeichert: dieselbe Koordinate zur selben Spielzeit ergibt immer
dasselbe Wetter, auch nach einem Neustart.

Abgeleitete Größen (Niederschlag, Schnee, Nebel, Windstärke) hängen von den
Feldern ab, statt eigene Felder zu sein. So entstehen keine unmöglichen
Kombinationen wie Regen bei klarem Himmel oder Nebel im Sturm.

"""

import math
from dataclasses import dataclass

from .noise import Field, clamp

HOUR = 3600
DAY = 24 * HOUR
YEAR = 360 * DAY

SEASONS = ("winter", "fruehling", "sommer", "herbst")

# Stufen, jeweils (obere Grenze, Name). Die letzte Stufe gilt für alles darüber.
SKY_LEVELS = ((0.36, "klar"), (0.52, "locker"), (0.66, "bedeckt"), (9, "duester"))
WIND_LEVELS = ("still", "brise", "boeig", "sturm")
WIND_LIMITS = (0.6, 1.3, 1.85)
TEMPERATURE_LEVELS = ((0, "frost"), (8, "kalt"), (18, "mild"), (26, "warm"), (99, "heiss"))

# Namen der Himmelsrichtungen, aus denen das Wetter kommen kann
_COMPASS = (
    "Osten",
    "Nordosten",
    "Norden",
    "Nordwesten",
    "Westen",
    "Südwesten",
    "Süden",
    "Südosten",
)


@dataclass(frozen=True)
class WeatherConfig:
    """
    Stellschrauben für das Wetter einer Welt.

    Attributes:
        front_size: Größe einer Wetterlage in Feldern.
        wind: Richtung, in die das Wetter zieht, als `(dx, dy)`. Die Länge
            ist egal. `(1, 0)` zieht nach Osten.
        wind_speed: Zuggeschwindigkeit in Feldern pro Spielstunde.
        morph_hours: Nach so vielen Spielstunden hat sich eine Wetterlage
            deutlich verformt.
        wetness: Verschiebt, wie oft es bewölkt ist und regnet (-0.2 bis 0.2).
        base_temperature: Jahresmittel in Grad auf Höhe 0 in der Kartenmitte.
        season_swing: Abweichung von Sommer und Winter vom Jahresmittel.
        day_swing: Abweichung von Nachmittag und Nacht vom Tagesmittel.
        height_cooling: Grad weniger pro Höhenlevel.
        north_cooling: Grad Unterschied zwischen Süd- und Nordrand der Karte.

    """

    front_size: float = 40.0
    wind: tuple = (1.0, 0.25)
    wind_speed: float = 6.0
    morph_hours: float = 36.0
    wetness: float = 0.0
    base_temperature: float = 13.0
    season_swing: float = 10.0
    day_swing: float = 4.0
    height_cooling: float = 1.8
    north_cooling: float = 4.0


@dataclass(frozen=True)
class Weather:
    """
    Das Wetter an einem Ort zu einer Zeit.

    Die Zahlen sind Rohwerte zum Abstimmen. Für Texte zählen die benannten
    Stufen, die `as_state()` liefert.

    """

    cloudiness: float
    humidity: float
    pressure: float
    temperature: float
    wind_force: float
    sky: str
    precipitation: str
    wind: str
    temperature_level: str
    fog: bool
    thunder: bool

    @property
    def is_wet(self):
        """True bei Regen in jeder Stärke."""
        return self.precipitation in ("niesel", "regen", "wolkenbruch")

    @property
    def is_snow(self):
        return self.precipitation in ("schnee", "starkschnee")

    def as_state(self):
        """Die benannten Stufen als Dict, für Bedingungen in Sätzen."""
        return {
            "himmel": self.sky,
            "niederschlag": self.precipitation,
            "wind": self.wind,
            "temperatur": self.temperature_level,
            "nebel": "ja" if self.fog else "nein",
            "gewitter": "ja" if self.thunder else "nein",
        }


def hour_of_day(t):
    """Stunde des Spieltages, 0 bis unter 24."""
    return (t / HOUR) % 24


def time_of_day(t):
    """Tageszeit: "nacht", "morgen", "tag" oder "abend"."""
    hour = hour_of_day(t)
    if hour < 5 or hour >= 22:
        return "nacht"
    if hour < 9:
        return "morgen"
    if hour < 18:
        return "tag"
    return "abend"


def season(t):
    """Jahreszeit. Das Jahr hat 360 Tage und beginnt mitten im Winter."""
    month = int((t % YEAR) / YEAR * 12)
    return SEASONS[((month + 1) % 12) // 3]


def _level(value, levels):
    for upper, name in levels:
        if value < upper:
            return name
    return levels[-1][1]


class WeatherModel:
    """
    Berechnet das Wetter einer Welt.

    Args:
        config (WeatherConfig): Die Stellschrauben.
        seed (int): Startwert der Welt.
        map_height (int): Höhe der Karte in Feldern, für das Nord-Süd-Gefälle.

    """

    def __init__(self, config, seed, map_height):
        self.config = config
        self.map_height = max(1, map_height)
        size = config.front_size
        # Große, langsame Drucksysteme bilden die Fronten. Kleinere, schnellere
        # Wolkenfelder liegen darüber. Die Temperatur bewegt sich kaum.
        self.pressure = Field(seed + 1, size * 2.5, octaves=2, warp=0.35)
        self.clouds = Field(seed + 2, size, octaves=3, warp=0.5)
        self.moisture = Field(seed + 3, size * 1.6, octaves=2, warp=0.3)
        self.warmth = Field(seed + 4, size * 4.0, octaves=1)
        self.gusts = Field(seed + 5, size * 0.4, octaves=1)

        length = math.hypot(*config.wind) or 1.0
        self.direction = (config.wind[0] / length, config.wind[1] / length)

    @property
    def wind_origin(self):
        """Name der Himmelsrichtung, aus der das Wetter heranzieht."""
        angle = math.degrees(math.atan2(-self.direction[1], -self.direction[0])) % 360
        return _COMPASS[int((angle + 22.5) // 45) % 8]

    def _shifted(self, x, y, hours, speed=1.0):
        """Abfragepunkt eines Feldes, das mit dem Wind über die Karte zieht."""
        distance = self.config.wind_speed * hours * speed
        return x - self.direction[0] * distance, y - self.direction[1] * distance

    def at(self, coordinates, t, height=0, moisture=0.0, warmth=0.0, shelter=0):
        """
        Wetter an einer Koordinate.

        Args:
            coordinates (tuple): `(x, y)`.
            t (float): Spielzeit in Sekunden.
            height (int): Höhenlevel 0-9 des Feldes.
            moisture (float): Klima des Bioms, feuchter (+) oder trockener (-).
            warmth (float): Klima des Bioms in Grad.
            shelter (int): Windschutz des Bioms in Stufen. Negativ = ausgesetzt.

        Returns:
            Weather: Das Wetter dort.

        """
        config = self.config
        x, y = coordinates
        hours = t / HOUR
        morph = hours / config.morph_hours

        px, py = self._shifted(x, y, hours)
        pressure = self.pressure.at(px, py, morph)
        cx, cy = self._shifted(x, y, hours, speed=1.3)
        clouds = self.clouds.at(cx, cy, morph * 1.5)
        mx, my = self._shifted(x, y, hours, speed=0.8)
        moist = self.moisture.at(mx, my, morph)

        # Tiefer Druck bringt Wolken. Feuchtes Klima verstärkt das.
        cloudiness = clamp(
            0.55 * (1.0 - pressure) + 0.45 * clouds + 0.5 * moisture + config.wetness
        )
        humidity = clamp(0.6 * moist + 0.4 * (1.0 - pressure) + moisture + config.wetness)

        # Temperatur: Jahreszeit, Tageszeit, Höhe, Nord-Süd-Lage, Klima
        year_part = (t % YEAR) / YEAR
        temperature = config.base_temperature - config.season_swing * math.cos(
            2 * math.pi * (year_part - 0.04)
        )
        # Wolken dämpfen den Tagesgang: bedeckte Nächte sind milder, Tage kühler
        day_part = math.cos(2 * math.pi * (hour_of_day(t) - 15) / 24)
        temperature += config.day_swing * day_part * (1.0 - 0.6 * cloudiness)
        temperature -= config.height_cooling * height
        temperature -= config.north_cooling * (y / self.map_height - 0.5)
        wx, wy = self._shifted(x, y, hours, speed=0.3)
        temperature += 8.0 * (self.warmth.at(wx, wy, morph * 0.5) - 0.5) + warmth

        # Wind: je steiler das Druckfeld, desto stärker. In der Höhe mehr.
        gx, gy = self.pressure.gradient(px, py, morph)
        gust = self.gusts.at(*self._shifted(x, y, hours, speed=1.6), morph * 3.0)
        wind_force = math.hypot(gx, gy) * (0.75 + 0.5 * gust) + 0.03 * height
        wind_index = sum(1 for limit in WIND_LIMITS if wind_force >= limit)
        wind_index = max(0, min(len(WIND_LEVELS) - 1, wind_index - shelter))
        wind = WIND_LEVELS[wind_index]

        # Niederschlag gibt es nur, wenn Bewölkung und Feuchte beide hoch sind
        amount = max(0.0, cloudiness - 0.60) * (0.4 + 1.2 * humidity)
        if amount <= 0.02:
            precipitation = "kein"
        elif temperature < 0.5:
            precipitation = "schnee" if amount < 0.17 else "starkschnee"
        elif amount < 0.08:
            precipitation = "niesel"
        elif amount < 0.20:
            precipitation = "regen"
        else:
            precipitation = "wolkenbruch"

        # Nebel: feucht, windstill, kein Niederschlag, nicht in der Mittagswärme
        cool_hours = time_of_day(t) != "tag" or temperature < 6
        fog = (
            precipitation == "kein"
            and humidity > 0.62
            and wind_index == 0
            and cool_hours
        )
        thunder = precipitation == "wolkenbruch" and temperature >= 17 and pressure < 0.25

        return Weather(
            cloudiness=cloudiness,
            humidity=humidity,
            pressure=pressure,
            temperature=temperature,
            wind_force=wind_force,
            sky=_level(cloudiness, SKY_LEVELS),
            precipitation=precipitation,
            wind=wind,
            temperature_level=_level(temperature, TEMPERATURE_LEVELS),
            fog=fog,
            thunder=thunder,
        )
