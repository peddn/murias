"""
Zugänge von der Wildnis in die Orte von Nereid.

Jeder Zugang liegt auf einem Tor-Feld (`o`) der Biom-Ebene. `targets` sagt,
aus welcher Bewegungsrichtung man in welchen Raum kommt: "south" heißt, man
läuft nach Süden auf das Feld, kommt also von Norden.

"""

from world.wildlands.world import Portal

_FURTHEIM = "Die Mauer von Furtheim ist hier geschlossen. Hinein kommst du nur durch ein Tor."

PORTALS = (
    Portal((18, 7), "Nordtor", {"south": (2, 4, "furtheim")},
           afar="das Nordtor von Furtheim", refuse=_FURTHEIM),
    Portal((18, 3), "Südtor", {"north": (2, 0, "furtheim")},
           afar="das Südtor von Furtheim", refuse=_FURTHEIM),
    Portal((16, 5), "Westtor", {"east": (0, 2, "furtheim")},
           afar="das Westtor von Furtheim", refuse=_FURTHEIM),
    Portal((20, 5), "Osttor", {"west": (4, 2, "furtheim")},
           afar="das Osttor von Furtheim", refuse=_FURTHEIM),
    # Ein Ort, der nur ein Feld belegt: die Richtung entscheidet.
    Portal((42, 15), "Tor des Wachturms", {"north": (0, 0, "wachturm")},
           afar="einen hölzernen Wachturm",
           refuse="Von hier aus kannst du den Wachturm nicht betreten. Die Palisade hat nur"
                  " im Süden ein Tor."),
)
