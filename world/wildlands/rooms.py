"""
Provider, Raum und Ausgang für die Wildnis.

- `WildlandsMapProvider` verbindet das Wilderness-Contrib mit einer
  Weltdefinition. Er wird vom Contrib in der Datenbank gespeichert und hält
  deshalb nur den Python-Pfad der Welt.
- `WildlandsRoom` berechnet Beschreibung und Details bei jedem `look` neu.
- `WildlandsExit` prüft, ob ein Schritt Klettern oder Schwimmen verlangt.

"""

from evennia.contrib.grid.wilderness.wilderness import (
    WildernessExit,
    WildernessMapProvider,
    WildernessRoom,
    get_new_coordinates,
)

from .world import CLIMB, SWIM, WALK, get_world

# Schlüssel des Ausgangs -> (Kürzel und Namen zum Eingeben, Anzeigename, Gegenrichtung)
DIRECTIONS = {
    "north": (("norden",), "Norden", "Süden"),
    "northeast": (("no", "nordosten"), "Nordosten", "Südwesten"),
    "east": (("o", "osten"), "Osten", "Westen"),
    "southeast": (("so", "südosten"), "Südosten", "Nordwesten"),
    "south": (("süden",), "Süden", "Norden"),
    "southwest": (("südwesten",), "Südwesten", "Nordosten"),
    "west": (("westen",), "Westen", "Osten"),
    "northwest": (("nordwesten",), "Nordwesten", "Südosten"),
}

# Fortbewegungsart -> (Verb für andere im Raum, Hinweis wenn man nur geht, Zusatz am Ausgang)
MOVEMENT_TEXT = {
    WALK: ("geht", "", ""),
    CLIMB: (
        "klettert",
        "Dort ist es zu steil zum Gehen. Du müsstest klettern (|wklettere <richtung>|n).",
        "klettern",
    ),
    SWIM: (
        "schwimmt",
        "Dort ist das Wasser zu tief zum Gehen. Du müsstest schwimmen (|wschwimme <richtung>|n).",
        "schwimmen",
    ),
}


class WildlandsMapProvider(WildernessMapProvider):
    """
    Map-Provider, der seine Daten aus einer Weltdefinition holt.

    Args:
        world_path (str): Python-Pfad des Welt-Pakets, z.B. "world.nereid".

    """

    def __init__(self, world_path):
        self.world_path = world_path

    @property
    def room_typeclass(self):
        return WildlandsRoom

    @property
    def exit_typeclass(self):
        return WildlandsExit

    @property
    def world(self):
        return get_world(self.world_path)

    def is_valid_coordinates(self, wilderness, coordinates):
        return self.world.is_valid(coordinates)

    def get_location_name(self, coordinates):
        return self.world.get_location_name(coordinates)

    def at_prepare_room(self, coordinates, caller, room):
        # Die Beschreibung wird nicht hier eingefroren, sondern beim Ansehen
        # berechnet (siehe WildlandsRoom.get_display_desc).
        room.ndb.active_desc = None


class WildlandsRoom(WildernessRoom):
    """
    Ein Sichtfenster in die Wildnis.

    Der Raum speichert nichts über das Feld, auf das er gerade zeigt. Alles
    wird aus den Koordinaten berechnet.

    """

    @property
    def world(self):
        return self.wilderness.mapprovider.world

    def get_display_name(self, looker=None, **kwargs):
        name = self.location_name
        if looker and self.locks.check_lockstring(looker, "perm(Builder)"):
            x, y = self.coordinates
            height = self.world.get_height(self.coordinates)
            name += f" |x({x},{y} h{height})|n"
        return name

    def get_display_desc(self, looker, **kwargs):
        return self.world.describe(self.coordinates, looker=looker)

    def get_weather_site(self):
        """`(welt, standort)` für Wetterbefehle und -meldungen, oder None."""
        world = self.world
        site = world.site_at(self.coordinates)
        return (world, site) if site and world.weather_model else None

    def get_display_exits(self, looker, **kwargs):
        order = list(DIRECTIONS)
        exits = self.filter_visible(self.contents_get(content_type="exit"), looker, **kwargs)
        exits = sorted(exits, key=lambda ex: order.index(ex.key) if ex.key in order else 99)
        names = ", ".join(exit_obj.get_display_name(looker, **kwargs) for exit_obj in exits)
        return f"|wAusgänge:|n {names}" if names else ""

    def get_detail(self, key, looker=None):
        """
        Sucht ein Detail dieses Feldes. Wird vom `look`-Befehl aufgerufen, wenn
        kein Objekt mit diesem Namen gefunden wurde.

        Returns:
            str or None: Der Text des Details.

        """
        key = key.strip().lower()
        details = self.world.get_details(self.coordinates)
        if key in details:
            return details[key]
        # sonst das kürzeste Detail, das mit der Eingabe beginnt
        matches = sorted((name for name in details if name.startswith(key)), key=len)
        return details[matches[0]] if matches else None


class WildlandsExit(WildernessExit):
    """
    Ausgang in der Wildnis mit deutschen Richtungsnamen und Fortbewegungsarten.

    Klettern und Schwimmen werden von den Befehlen in `commands.py` ausgelöst.
    Sie setzen `traversing_object.ndb.wild_move_mode`, bevor sie den Ausgang
    benutzen.

    """

    def at_object_creation(self):
        super().at_object_creation()
        aliases = DIRECTIONS.get(self.key, ((),))[0]
        if aliases:
            self.aliases.add(list(aliases))

    def get_display_name(self, looker=None, **kwargs):
        name = DIRECTIONS.get(self.key, ((), self.key))[1]
        # Hinweis, wenn dort ein Zugang liegt oder der Schritt Klettern oder
        # Schwimmen verlangt
        try:
            portal = self.get_portal(looker)
            if portal:
                # den Namen nur zeigen, wenn man von hier aus hineinkommt
                hint = portal.name if self.key in portal.targets else ""
            else:
                hint = MOVEMENT_TEXT[self.required_movement(looker)][2]
        except (AttributeError, KeyError, TypeError):
            hint = ""
        return f"{name} ({hint})" if hint else name

    def get_portal(self, traversing_object):
        """Zugang auf dem Feld, zu dem dieser Ausgang führt, oder None."""
        wilderness = self.wilderness
        start = wilderness.db.itemcoordinates[traversing_object]
        return wilderness.mapprovider.world.get_portal(get_new_coordinates(start, self.key))

    def enter_portal(self, traversing_object, portal):
        """
        Führt das Objekt durch einen Zugang aus der Wildnis in den Zielraum.

        Returns:
            bool: True, wenn es hindurchgegangen ist.

        """
        from .places import find_place_room

        target = portal.targets.get(self.key)
        if not target or (traversing_object.ndb.wild_move_mode or WALK) != WALK:
            traversing_object.msg(portal.refuse)
            return False
        room = find_place_room(target)
        if not room:
            traversing_object.msg("Der Zugang ist versperrt.")
            return False
        if not traversing_object.at_pre_move(room):
            return False
        name = traversing_object.get_display_name(None)
        origin = traversing_object.location
        origin.msg_contents(
            f"{name} geht nach {DIRECTIONS[self.key][1]} durch das {portal.name}.",
            exclude=[traversing_object],
        )
        if not traversing_object.move_to(room, quiet=True, move_type="traverse"):
            return False
        room.msg_contents(
            f"{name} kommt durch das {portal.name} herein.", exclude=[traversing_object]
        )
        return True

    def required_movement(self, traversing_object):
        """Fortbewegungsart, die dieser Ausgang für das Objekt verlangt."""
        wilderness = self.wilderness
        start = wilderness.db.itemcoordinates[traversing_object]
        target = get_new_coordinates(start, self.key)
        return wilderness.mapprovider.world.required_movement(start, target)

    def at_traverse_coordinates(self, traversing_object, current_coordinates, new_coordinates):
        wilderness = self.wilderness
        if not wilderness.is_valid_coordinates(new_coordinates):
            return False
        required = wilderness.mapprovider.world.required_movement(
            current_coordinates, new_coordinates
        )
        mode = traversing_object.ndb.wild_move_mode or WALK
        if required != mode:
            if mode == WALK:
                traversing_object.msg(MOVEMENT_TEXT[required][1])
            else:
                traversing_object.msg("Das geht hier nicht.")
            return False
        return True

    def at_traverse(self, traversing_object, target_location):
        wilderness = self.wilderness
        current_coordinates = wilderness.db.itemcoordinates[traversing_object]
        new_coordinates = get_new_coordinates(current_coordinates, self.key)

        portal = wilderness.mapprovider.world.get_portal(new_coordinates)
        if portal:
            return self.enter_portal(traversing_object, portal)

        if not self.at_traverse_coordinates(
            traversing_object, current_coordinates, new_coordinates
        ):
            return False
        if not traversing_object.at_pre_move(None):
            return False

        _, direction, opposite = DIRECTIONS[self.key]
        verb = MOVEMENT_TEXT[traversing_object.ndb.wild_move_mode or WALK][0]
        name = traversing_object.get_display_name(None)
        traversing_object.location.msg_contents(
            f"{name} {verb} nach {direction}.", exclude=[traversing_object]
        )
        wilderness.move_obj(traversing_object, new_coordinates)
        traversing_object.location.msg_contents(
            f"{name} kommt aus dem {opposite}.", exclude=[traversing_object]
        )
        traversing_object.at_post_move(None)
        return True
