"""
Meldungen bei Wetterwechsel.

Das Wetter selbst braucht keinen Takt, es wird beim Ansehen berechnet. Dieses
Script sorgt nur dafür, dass Spieler, die irgendwo stehen bleiben, von einem
Wechsel erfahren ("Es beginnt zu regnen."). Es prüft dazu regelmäßig alle
Felder der Wildnis, auf denen gerade jemand steht.

Eingerichtet wird es über `GLOBAL_SCRIPTS` in den Einstellungen.

"""

from evennia import DefaultScript
from evennia.contrib.grid.wilderness.wilderness import WildernessScript

from .rooms import WildlandsMapProvider


def weather_messages(world, coordinates, before, after, t):
    """
    Meldungen für den Wechsel von einem Wetter zum nächsten.

    Args:
        before, after (Weather): Wetter bei der letzten und der jetzigen Prüfung.

    Returns:
        list: Sätze, kann leer sein.

    """
    if not world.sentences:
        return []
    biome = world.get_biome(coordinates)
    changes = (
        ("wechsel", before.precipitation, after.precipitation),
        ("wechsel_wind", before.wind, after.wind),
        ("wechsel_nebel", "ja" if before.fog else "nein", "ja" if after.fog else "nein"),
    )
    messages = []
    for topic, old, new in changes:
        if old == new:
            continue
        state = {"von": old, "zu": new, "biom": biome.key if biome else ""}
        text = world.sentences.choose(
            topic, state, lambda options, salt: world.pick(options, coordinates, f"{salt}:{t}")
        )
        if text:
            messages.append(text)
    return messages


class WeatherWatch(DefaultScript):
    """Prüft regelmäßig das Wetter auf allen besetzten Feldern der Wildnis."""

    def at_script_creation(self):
        self.key = "wildlands_weather"
        self.desc = "Meldet Wetterwechsel in der Wildnis"
        self.interval = 30
        self.persistent = True

    def at_repeat(self):
        for wilderness in WildernessScript.objects.all():
            provider = wilderness.db.mapprovider
            if not isinstance(provider, WildlandsMapProvider):
                continue
            world = provider.world
            if not world.weather_model:
                continue
            t = world.now()
            for coordinates, room in list(wilderness.db.rooms.items()):
                listeners = [obj for obj in room.contents if obj.has_account]
                if not listeners:
                    room.ndb.weather_seen = None
                    continue
                weather = world.get_weather(coordinates, t)
                seen = room.ndb.weather_seen
                room.ndb.weather_seen = (coordinates, weather)
                # der Raum zeigt vielleicht inzwischen auf ein anderes Feld
                if not seen or seen[0] != coordinates:
                    continue
                for message in weather_messages(world, coordinates, seen[1], weather, t):
                    room.msg_contents(message)
