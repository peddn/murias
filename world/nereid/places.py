"""
Orte von Nereid: Karten für das Contrib `grid/xyzgrid`.

Einrichten oder nach Änderungen aktualisieren (im Spielverzeichnis):

    evennia xyzgrid add world.nereid.places
    evennia xyzgrid spawn

Die Einstellungen unter "wildlands" sind in `world.wildlands.places`
beschrieben. Die Zugänge aus der Wildnis stehen in `world.nereid.portals`.

"""

from world.wildlands.places import prepare_prototypes

ROOM_PARENT = {
    "prototype_key": "nereid_place_room",
    "typeclass": "world.wildlands.places.PlaceRoom",
    "key": "Ein Raum",
    "desc": "Ein leerer Raum.",
}

EXIT_PARENT = {
    "prototype_key": "nereid_place_exit",
    "typeclass": "world.wildlands.places.PlaceExit",
}


def _finish(prototypes):
    return prepare_prototypes(prototypes, ROOM_PARENT, EXIT_PARENT)


# ------------------------------------------------------------------ Furtheim
# Eine kleine ummauerte Stadt mit vier Toren. In der Wildnis belegt sie die
# Felder (16,3) bis (20,7).

FURTHEIM_MAP = r"""
 + 0 1 2 3 4

 4     #
       |
 3   #-#-#
       |
 2 #-#-#-#-#
       |
 1     #-#
       |
 0     #

 + 0 1 2 3 4
"""

INDOOR = [("outdoor", False)]

FURTHEIM_PROTOTYPES = _finish(
    {
        (2, 4): {
            "key": "Am Nordtor",
            "desc": "Hinter dem wuchtigen Nordtor beginnt eine gepflasterte Gasse, die nach"
            " Süden in die Stadt führt. $state(nacht, Eine Fackel am Torbogen wirft"
            " unruhiges Licht auf die Mauer.)",
            "attrs": [("details", {"tor": "Schwere Eichenbohlen, mit Eisenbändern beschlagen."})],
        },
        (2, 3): {
            "key": "Nordgasse",
            "desc": "Die Gasse führt zwischen Fachwerkhäusern hindurch. Im Westen steht die"
            " Tür einer Schmiede offen, im Osten hängt das Schild eines Gasthauses."
            " $state(regen, Aus den Dachrinnen plätschert es auf das Pflaster.)",
        },
        (1, 3): {
            "key": "Schmiede",
            "desc": "Die Esse glüht, und es riecht nach Kohle und heißem Eisen. An den Wänden"
            " hängen Zangen und Hämmer.",
            "attrs": INDOOR + [("details", {"esse": "Ein Bett aus glühender Holzkohle."})],
        },
        (3, 3): {
            "key": "Gasthaus Zur Furt",
            "desc": "Eine niedrige Stube mit rußgeschwärzten Balken. Lange Tische und Bänke"
            " stehen vor einem gemauerten Kamin.",
            "attrs": INDOOR,
        },
        (2, 2): {
            "key": "Marktplatz",
            "desc": "Der Marktplatz ist das Herz von Furtheim. In seiner Mitte steht ein"
            " steinerner Brunnen. $state(verschneit, Auf dem Brunnenrand liegt eine"
            " weiße Haube aus Schnee.) $state(nacht, Die Stände sind abgebaut, der"
            " Platz liegt verlassen da.)",
            "attrs": [
                ("place_kind", "platz"),
                ("details", {"brunnen": "Ein achteckiges Becken aus grauem Stein."}),
            ],
        },
        (1, 2): {"key": "Westgasse", "desc": "Eine schmale Gasse führt vom Markt zum Westtor."},
        (0, 2): {"key": "Am Westtor", "desc": "Das Westtor öffnet sich auf die Wiesen."},
        (3, 2): {"key": "Ostgasse", "desc": "Eine schmale Gasse führt vom Markt zum Osttor."},
        (4, 2): {"key": "Am Osttor", "desc": "Durch das Osttor siehst du hinaus ins Land."},
        (2, 1): {
            "key": "Südgasse",
            "desc": "Die Gasse führt vom Markt zum Südtor. Im Osten liegt hinter einer"
            " niedrigen Mauer ein Garten.",
        },
        (3, 1): {
            "key": "Kräutergarten",
            "desc": "Ordentliche Beete liegen zwischen Kieswegen."
            " $state(verschneit, Jetzt ist alles unter Schnee begraben.)",
            "attrs": [("place_kind", "garten"), ("shelter", 1)],
        },
        (2, 0): {"key": "Am Südtor", "desc": "Das Südtor ist das kleinste der vier Tore."},
    }
)

FURTHEIM = {
    "zcoord": "furtheim",
    "map": FURTHEIM_MAP,
    "prototypes": FURTHEIM_PROTOTYPES,
    "options": {
        "map_visual_range": 2,
        "wildlands": {
            "world": "world.nereid",
            "weather_at": (18, 5),
            "biome": "grass",
            "height": 2,
            "outdoor": True,
            "kind": "strasse",
        },
    },
}

# ------------------------------------------------------------------ Wachturm
# Ein einzelnes Feld in der Wildnis bei (42,15), nur von Süden zu betreten.

WACHTURM_MAP = r"""
 + 0

 1 #
   |
 0 #

 + 0
"""

WACHTURM_PROTOTYPES = _finish(
    {
        (0, 0): {
            "key": "Hof des Wachturms",
            "desc": "Ein enger, von einer Palisade umgebener Hof. Im Norden führt eine Tür"
            " in den Turm.",
            "attrs": [("place_kind", "hof"), ("shelter", 1)],
        },
        (0, 1): {
            "key": "Turmstube",
            "desc": "Eine runde Stube mit schmalen Fensterschlitzen. Eine Leiter führt"
            " weiter hinauf, doch die Luke ist verriegelt.",
            "attrs": INDOOR,
        },
    }
)

WACHTURM = {
    "zcoord": "wachturm",
    "map": WACHTURM_MAP,
    "prototypes": WACHTURM_PROTOTYPES,
    "options": {
        "map_visual_range": 1,
        "wildlands": {
            "world": "world.nereid",
            "weather_at": (42, 15),
            "biome": "grass",
            "height": 3,
            "outdoor": True,
            "kind": "hof",
        },
    },
}

XYMAP_DATA_LIST = [FURTHEIM, WACHTURM]
