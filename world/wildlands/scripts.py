"""
Meldungen bei Wetterwechsel.

Das Wetter selbst braucht keinen Takt, es wird beim Ansehen berechnet. Dieses
Script sorgt nur dafür, dass Spieler, die irgendwo stehen bleiben, von einem
Wechsel erfahren ("Es beginnt zu regnen."). Es prüft dazu regelmäßig alle
Räume mit Wetter, in denen gerade ein Spieler steht: Felder der Wildnis und
Außenräume von Orten.

Eingerichtet wird es über `GLOBAL_SCRIPTS` in den Einstellungen.

"""

from evennia import SESSION_HANDLER, DefaultScript

from .weather import DAY


def weather_messages(world, site, before, after, t):
    """
    Meldungen für den Wechsel von einem Wetter zum nächsten.

    Args:
        site (Site): Der Standort.
        before, after (Weather): Wetter bei der letzten und der jetzigen Prüfung.

    Returns:
        list: Sätze, kann leer sein.

    """
    if not world.sentences:
        return []
    changes = (
        ("wechsel", before.precipitation, after.precipitation),
        ("wechsel_wind", before.wind, after.wind),
        ("wechsel_nebel", "ja" if before.fog else "nein", "ja" if after.fog else "nein"),
    )
    messages = []
    for topic, old, new in changes:
        if old == new:
            continue
        state = {"von": old, "zu": new, "biom": site.biom}
        text = world.sentences.choose(
            topic,
            state,
            lambda options, salt: world.pick(options, site.coordinates, f"{salt}:{t}"),
        )
        if text:
            messages.append(text)
    return messages


class WeatherWatch(DefaultScript):
    """Prüft regelmäßig das Wetter in allen Räumen, in denen Spieler stehen."""

    def at_script_creation(self):
        self.key = "wildlands_weather"
        self.desc = "Meldet Wetterwechsel in der Wildnis"
        self.interval = 30
        self.persistent = True

    def at_repeat(self):
        rooms = set()
        for session in SESSION_HANDLER.get_sessions():
            puppet = session.get_puppet()
            if puppet and puppet.location:
                rooms.add(puppet.location)
        for room in rooms:
            getter = getattr(room, "get_weather_site", None)
            found = getter() if getter else None
            if not found:
                continue
            world, site = found
            t = world.now()
            weather = world.site_weather(site, t)
            seen = room.ndb.weather_seen
            room.ndb.weather_seen = (site, weather, t)
            # Der Raum zeigt vielleicht inzwischen auf ein anderes Feld, oder
            # es stand mehr als einen Spieltag niemand hier: dann gibt es
            # nichts zu melden.
            if not seen or seen[0] != site or abs(t - seen[2]) > DAY:
                continue
            for message in weather_messages(world, site, seen[1], weather, t):
                room.msg_contents(message)
