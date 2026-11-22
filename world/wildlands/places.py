"""
Orte: Gebiete aus normalen Räumen (Städte, Höhlen, Dungeons), die an die
Wildnis angeschlossen sind.

Die Räume liegen auf einer Karte des Contribs `grid/xyzgrid` und benutzen
zugleich `grid/extended_room` für Zustände, Details und jahreszeitliche
Beschreibungen.

Einstellungen eines Gebiets stehen in den `options` seiner XYZ-Karte unter
dem Schlüssel "wildlands":

    "options": {
        "wildlands": {
            "world": "world.nereid",   # Welt, deren Wetter und Sätze gelten
            "weather_at": (18, 5),     # Stelle im Wetterfeld (Wildniskoordinate)
            "biome": "grass",          # Biom, dessen Klima gilt
            "height": 2,               # Höhenlevel 0-9
            "outdoor": True,           # Standard für alle Räume des Gebiets
            "kind": "strasse",         # Standard-Art der Außenräume
        }
    }

Alle Außenräume eines Gebiets haben dasselbe Wetter. Ohne "weather_at" hat
das Gebiet kein Wetter.

Einzelne Räume können im Prototyp abweichen, über die Attribute `outdoor`
(drinnen oder draußen), `place_kind` (Art für die Satzauswahl, z.B. "platz"),
`shelter` (Windschutz in Stufen) und `weather_auto` (False = keine
automatischen Wettersätze, nur `$state(...)` in der Beschreibung).

"""

import re

from evennia import DefaultExit
from evennia.contrib.grid import wilderness
from evennia.contrib.grid.extended_room.extended_room import ExtendedRoom
from evennia.contrib.grid.xyzgrid.xyzroom import XYZExit, XYZRoom
from evennia.utils import create, logger

from .rooms import DIRECTIONS
from .weather import season, time_of_day
from .world import STEPS, Site, get_world

# unsere Namen -> Namen, die Extended Room erwartet (für desc_<jahreszeit> usw.)
_SEASON_NAMES = {
    "winter": "winter",
    "fruehling": "spring",
    "sommer": "summer",
    "herbst": "autumn",
}
_TIME_NAMES = {"nacht": "night", "morgen": "morning", "tag": "afternoon", "abend": "evening"}

OPPOSITE = {
    "north": "south",
    "northeast": "southwest",
    "east": "west",
    "southeast": "northwest",
    "south": "north",
    "southwest": "northeast",
    "west": "east",
    "northwest": "southeast",
}

# zusätzliche Richtungen, die es nur in Orten gibt
PLACE_DIRECTIONS = dict(DIRECTIONS)
PLACE_DIRECTIONS.update(
    {
        "up": (("hoch", "rauf", "oben"), "Oben", "Unten"),
        "down": (("runter", "unten"), "Unten", "Oben"),
    }
)


def prepare_prototypes(prototypes, room_parent, exit_parent):
    """
    Bereitet die Prototypen einer XYZ-Karte vor.

    Setzt die Eltern-Prototypen für Räume und Ausgänge und schützt
    `$state(...)` in Texten. Ohne den Schutz würde Evennia die Funktion schon
    beim Erzeugen des Raumes auswerten wollen und daran scheitern; sie soll
    aber erst beim Ansehen des Raumes ausgewertet werden.

    Args:
        prototypes (dict): `{(x, y): {...}, (x, y, richtung): {...}}`.
        room_parent, exit_parent (dict): Eltern-Prototypen mit `typeclass`.

    Returns:
        dict: Dieselben Prototypen, verändert.

    """
    for key, prototype in prototypes.items():
        prototype["prototype_parent"] = room_parent if len(key) == 2 else exit_parent
        for name, value in prototype.items():
            if isinstance(value, str):
                prototype[name] = value.replace("$$state(", "$state(").replace(
                    "$state(", "$$state("
                )
    prototypes.setdefault(("*", "*", "*"), {"prototype_parent": exit_parent})
    return prototypes


def weather_states(state):
    """
    Raumzustände aus einem Wetterzustand, für `$state(...)` in Beschreibungen.

    Beispiele: "regen" bei jeder Art Regen, "schnee" bei jedem Schneefall,
    dazu die genaue Stufe ("niesel", "wolkenbruch"), "boeig", "sturm",
    "nebel", "gewitter", "nass", "verschneit", die Temperaturstufe ("frost"),
    die Bewölkung ("klar"), Tageszeit ("nacht") und Jahreszeit ("winter").

    """
    states = {state["tageszeit"], state["jahreszeit"]}
    if "niederschlag" not in state:
        return states
    precipitation = state["niederschlag"]
    if precipitation in ("niesel", "regen", "wolkenbruch"):
        states.update(("regen", precipitation))
    elif precipitation in ("schnee", "starkschnee"):
        states.update(("schnee", precipitation))
    if state["wind"] != "still":
        states.add(state["wind"])
    if state["nebel"] == "ja":
        states.add("nebel")
    if state["gewitter"] == "ja":
        states.add("gewitter")
    if state["boden"] == "nass":
        states.add("nass")
    elif state["boden"] == "schnee":
        states.add("verschneit")
    states.add(state["temperatur"])
    states.add(state["himmel"])
    return states


class PlaceRoom(XYZRoom, ExtendedRoom):
    """
    Raum in einem Ort. Verbindet XYZRoom (Koordinaten, Kartenanzeige) mit
    ExtendedRoom (Zustände, Details, Beschreibungen je Jahreszeit) und
    ergänzt für Außenräume das Wetter.

    """

    @property
    def area(self):
        """Einstellungen des Gebiets, siehe Modulbeschreibung."""
        try:
            xymap = self.xyzgrid.get_map(self.xyz[2])
        except Exception:
            return {}
        return (xymap.options or {}).get("wildlands", {}) if xymap else {}

    @property
    def world(self):
        path = self.area.get("world")
        return get_world(path) if path else None

    @property
    def is_outdoor(self):
        outdoor = self.db.outdoor
        return bool(self.area.get("outdoor", False) if outdoor is None else outdoor)

    def get_site(self):
        """
        Standort für das Wetter, oder None für Innenräume und Gebiete ohne
        Wetter.

        """
        area = self.area
        world = self.world
        if not world or not self.is_outdoor or not area.get("weather_at"):
            return None
        climate = next(
            (biome for biome in world.biomes.values() if biome.key == area.get("biome")), None
        )
        return Site(
            coordinates=tuple(area["weather_at"]),
            biom=self.db.place_kind or area.get("kind", "strasse"),
            height=area.get("height", climate.height if climate else 2),
            moisture=climate.moisture if climate else 0.0,
            warmth=climate.warmth if climate else 0.0,
            shelter=self.db.shelter or 0,
        )

    def get_weather_site(self):
        """`(welt, standort)` für Wetterbefehle und -meldungen, oder None."""
        site = self.get_site()
        return (self.world, site) if site else None

    # Kalender: derselbe wie in der Wildnis

    def _now(self):
        world = self.world
        if world:
            return world.now()
        from evennia.utils import gametime

        return gametime.gametime(absolute=True)

    def get_time_of_day(self):
        return _TIME_NAMES[time_of_day(self._now())]

    def get_season(self):
        return _SEASON_NAMES[season(self._now())]

    # Zustände: gespeicherte und berechnete

    @property
    def room_states(self):
        states = set(super().room_states)
        t = self._now()
        site = self.get_site()
        if site:
            states.update(weather_states(self.world.site_state(site, t)))
        else:
            states.update((time_of_day(t), season(t)))
        return sorted(states)

    def get_display_desc(self, looker, **kwargs):
        desc = super().get_display_desc(looker, **kwargs)
        # ein $state(...), das gerade nicht zutrifft, hinterlässt eine Lücke
        desc = re.sub(r" {2,}", " ", desc).strip()
        site = self.get_site()
        if site and self.db.weather_auto is not False:
            world = self.world
            t = world.now()
            sentences = world.describe_weather(site.coordinates, t, site=site)
            sentences += world.describe_weather(site.coordinates, t, topics=("nebel",), site=site)
            if sentences:
                desc = f"{desc} {' '.join(sentences)}"
        return desc

    def get_detail(self, key, looker=None):
        detail = super().get_detail(key, looker=looker)
        if detail:
            return detail
        site = self.get_site()
        if site:
            return self.world.weather_details(site, self.world.now()).get(key.strip().lower())
        return None

    def get_display_exits(self, looker, **kwargs):
        order = list(PLACE_DIRECTIONS)
        exits = self.filter_visible(self.contents_get(content_type="exit"), looker, **kwargs)
        exits = sorted(exits, key=lambda ex: order.index(ex.key) if ex.key in order else 99)
        names = ", ".join(exit_obj.get_display_name(looker, **kwargs) for exit_obj in exits)
        return f"|wAusgänge:|n {names}" if names else ""


class PlaceExit(XYZExit):
    """Ausgang innerhalb eines Ortes, mit deutschen Richtungsnamen."""

    def at_object_creation(self):
        super().at_object_creation()
        self.add_german_aliases()

    def add_german_aliases(self):
        aliases = PLACE_DIRECTIONS.get(self.key, ((),))[0]
        if aliases:
            self.aliases.add(list(aliases))

    def get_display_name(self, looker=None, **kwargs):
        return PLACE_DIRECTIONS.get(self.key, ((), self.key))[1]


class GateExit(DefaultExit):
    """
    Ausgang aus einem Ort in die Wildnis. Wird von `sync_portals` aus den
    Zugängen der Welt angelegt, nicht von Hand.

    Attributes (db):
        wild_name (str): Name der Wildnis.
        wild_coordinates (tuple): Feld vor dem Tor.
        gate_name (str): Name des Zugangs, z.B. "Nordtor".

    """

    def get_display_name(self, looker=None, **kwargs):
        name = PLACE_DIRECTIONS.get(self.key, ((), self.key))[1]
        return f"{name} (hinaus)"

    def at_traverse(self, traversing_object, target_location):
        if not traversing_object.at_pre_move(None):
            return False
        name = traversing_object.get_display_name(None)
        origin = traversing_object.location
        gate = self.db.gate_name or "Tor"
        if not wilderness.enter_wilderness(
            traversing_object, coordinates=tuple(self.db.wild_coordinates), name=self.db.wild_name
        ):
            traversing_object.msg("Der Weg hinaus ist versperrt.")
            return False
        if origin:
            origin.msg_contents(f"{name} verlässt den Ort durch das {gate}.")
        traversing_object.location.msg_contents(
            f"{name} kommt durch das {gate} heraus.", exclude=[traversing_object]
        )
        traversing_object.at_post_move(origin)
        return True


def find_place_room(xyz):
    """Raum an einer XYZ-Koordinate, oder None, wenn er nicht gespawnt ist."""
    try:
        return XYZRoom.objects.get_xyz(xyz=xyz)
    except Exception:
        return None


def sync_portals(world_path, wilderness_name):
    """
    Legt für jeden Zugang einer Welt den Ausgang zurück in die Wildnis an.

    Kommt man nach Süden gehend durch das Nordtor herein, führt im Torraum
    der Ausgang "north" auf das Feld nördlich des Tores. Vorhandene Ausgänge
    werden aktualisiert, die Funktion kann beliebig oft laufen.

    Returns:
        list: Meldungen über fehlende Zielräume.

    """
    world = get_world(world_path)
    problems = []
    for coordinates, portal in world.portals.items():
        for direction, xyz in portal.targets.items():
            room = find_place_room(xyz)
            if not room:
                problems.append(f"Zugang '{portal.name}': Raum {xyz} gibt es (noch) nicht.")
                continue
            key = OPPOSITE[direction]
            dx, dy = STEPS[direction]
            outside = (coordinates[0] - dx, coordinates[1] - dy)
            exit_obj = next(
                (obj for obj in room.contents if isinstance(obj, GateExit) and obj.key == key),
                None,
            )
            if not exit_obj:
                exit_obj = create.create_object(
                    GateExit,
                    key=key,
                    location=room,
                    destination=room,
                    aliases=[alias for alias in PLACE_DIRECTIONS[key][0]] + [_short(key)],
                    report_to=None,
                )
            exit_obj.db.wild_name = wilderness_name
            exit_obj.db.wild_coordinates = outside
            exit_obj.db.gate_name = portal.name
    for problem in problems:
        logger.log_warn(f"wildlands: {problem}")
    return problems


def _short(key):
    """Übliches Kürzel einer Richtung ("north" -> "n")."""
    return {
        "north": "n",
        "northeast": "ne",
        "east": "e",
        "southeast": "se",
        "south": "s",
        "southwest": "sw",
        "west": "w",
        "northwest": "nw",
    }[key]
