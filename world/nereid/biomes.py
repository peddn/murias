"""
Biome, Regionen und Überlagerungen von Nereid.

Die Zeichen entsprechen denen in den Kartenebenen unter `maps/`.

"""

from world.wildlands.world import BLOCKED, CLIMB, SWIM, Biome, Overlay, Region

BIOMES = (
    Biome(
        key="grass",
        symbol=".",
        name="Wiese",
        height=2,
        afar="offenes Grasland",
        descs=(
            "Kniehohes Gras wiegt sich um dich, durchsetzt von Disteln und gelbem Hahnenfuß.",
            "Du stehst auf einer weiten Wiese. Zwischen den Halmen summen Insekten.",
            "Sanft gewelltes Grasland erstreckt sich um dich, hier und da von einem"
            " Maulwurfshügel unterbrochen.",
        ),
        details={
            "gras;wiese;halme": "Das Gras ist zäh und reicht dir bis ans Knie.",
            "boden;erde": "Dunkle, krümelige Erde unter einer dichten Grasnarbe.",
        },
    ),
    Biome(
        key="forest",
        shelter=1,
        open_sky=False,
        dries=6,
        symbol="&",
        name="Wald",
        height=3,
        afar="dichten Wald",
        descs=(
            "Alte Buchen und Eichen stehen dicht an dicht. Ihr Blätterdach lässt nur"
            " grünes Dämmerlicht durch.",
            "Du stehst zwischen moosbewachsenen Stämmen. Farn wuchert in den Lücken"
            " dazwischen.",
            "Der Wald ist hier voller Unterholz. Dürre Äste knacken unter deinen Füßen.",
        ),
        details={
            "bäume;baum;stämme;buchen;eichen": "Die Stämme sind so dick, dass zwei"
            " Menschen sie kaum umfassen könnten.",
            "boden;laub;moos": "Eine federnde Schicht aus altem Laub und Moos bedeckt den"
            " Waldboden.",
            "himmel": "Vom Himmel siehst du nur ein paar helle Flecken zwischen den Kronen.",
        },
    ),
    Biome(
        key="beach",
        warmth=1.0,
        dries=1,
        symbol="*",
        name="Strand",
        height=0,
        afar="hellen Sandstrand",
        descs=(
            "Feiner, heller Sand gibt unter deinen Schritten nach. Angespültes Treibholz"
            " liegt verstreut herum.",
            "Du stehst auf einem breiten Sandstrand. Muschelschalen knirschen unter deinen"
            " Sohlen.",
        ),
        details={
            "sand;boden": "Heller, feiner Sand, in dem deine Füße tiefe Spuren hinterlassen.",
            "treibholz;holz": "Vom Salz gebleichtes Holz, glatt geschliffen wie Knochen.",
            "muscheln;muschelschalen": "Leere Schalen in Weiß, Rosa und Grau.",
        },
    ),
    Biome(
        key="swamp",
        moisture=0.12,
        dries=0,
        symbol="=",
        name="Moor",
        height=1,
        afar="sumpfiges Moor",
        descs=(
            "Der Boden schwankt unter dir. Zwischen Binsen und Wollgras steht schwarzes"
            " Wasser.",
            "Du watest durch knöcheltiefen Morast. Es riecht nach Fäulnis und nassem Torf.",
            "Bleiche, abgestorbene Birken ragen aus dem Moor. Irgendwo gluckst es.",
        ),
        details={
            "boden;morast;torf": "Schwarzer, nasser Torf, der an deinen Stiefeln saugt.",
            "wasser;tümpel": "Das Wasser ist braun wie starker Tee und völlig still.",
            "binsen;wollgras": "Harte Binsen und weiße Wollgrasbüschel.",
            "birken": "Die Birken sind längst tot. Ihre Rinde hängt in Fetzen herab.",
        },
    ),
    Biome(
        key="rock",
        dries=0,
        symbol="^",
        name="Fels",
        movement=CLIMB,
        height=6,
        afar="schroffen Fels",
        descs=(
            "Du klammerst dich an grauen, rissigen Fels. Loses Geröll rieselt unter dir"
            " in die Tiefe.",
            "Steile Felsbänder umgeben dich. In den Spalten halten sich zähe Polster aus"
            " Steinbrech.",
            "Du hängst in einer zerklüfteten Flanke. Jeder Griff will geprüft sein.",
        ),
        details={
            "fels;felsen;stein;wand": "Grauer, von Frost gesprengter Stein. Scharfkantig,"
            " aber griffig.",
            "geröll;boden": "Lose Steine, die bei der kleinsten Berührung ins Rutschen kommen.",
            "steinbrech;pflanzen": "Kleine, harte Polster mit winzigen weißen Blüten.",
        },
    ),
    Biome(
        key="cliff",
        symbol="%",
        name="Steilwand",
        movement=BLOCKED,
        height=9,
        afar="eine glatte, unbezwingbare Steilwand",
    ),
    Biome(
        key="lake",
        moisture=0.05,
        dries=0,
        symbol="~",
        name="See",
        movement=SWIM,
        height=2,
        afar="einen See",
        descs=(
            "Du schwimmst in kühlem, klarem Wasser. Unter dir verliert sich der Grund im"
            " Dunkel.",
            "Kleine Wellen schlagen dir ins Gesicht. Das Ufer wirkt von hier aus weit"
            " entfernt.",
        ),
        details={
            "wasser;see": "Das Wasser ist klar und so kalt, dass es dir den Atem nimmt.",
            "grund;boden": "Tief unter dir ahnst du helle Steine.",
        },
    ),
)

# Orte: Mauern sperren, Tore sind Zugänge (siehe portals.py)
BIOMES += (
    Biome(
        key="wall",
        symbol="x",
        name="Mauer",
        movement=BLOCKED,
        height=2,
        afar="eine hohe Stadtmauer",
    ),
    Biome(key="gate", symbol="o", name="Tor", height=2, is_portal=True),
)

REGIONS = (
    Region(
        key="grauzinnen",
        symbol="G",
        name="Grauzinnen",
        details={"gipfel;zinnen": "Die höchsten Zacken stecken in den Wolken."},
    ),
    Region(key="duesterwald", symbol="D", name="Düsterwald"),
    Region(key="spiegelsee", symbol="S", name="Spiegelsee"),
    Region(key="nebelmoor", symbol="N", name="Nebelmoor"),
)

OVERLAYS = (
    Overlay(
        key="road",
        symbol="#",
        name="Straße",
        descs=(
            "Eine gepflasterte Straße führt hier entlang.",
            "Du stehst auf einer alten Straße. Tiefe Wagenspuren haben sich in das"
            " Pflaster gegraben.",
        ),
        details={
            "straße;pflaster;weg": "Rundgetretene Pflastersteine, zwischen denen Gras"
            " wächst.",
            "wagenspuren;spuren": "Zwei Rillen, über Generationen von Rädern ausgeschliffen.",
        },
    ),
    Overlay(
        key="bridge",
        symbol="H",
        name="Brücke",
        walkable=True,
        descs=(
            "Du stehst auf einem langen Holzsteg, der die Straße über den See trägt. Unter"
            " den Bohlen gluckst das Wasser.",
            "Der Steg schwankt leicht unter deinen Schritten. Links und rechts liegt der"
            " See glatt und dunkel.",
        ),
        details={
            "steg;brücke;holzsteg": "Dicke Eichenbohlen auf Pfählen. Sie knarren, aber sie"
            " halten.",
        },
    ),
)

# Details, die überall gelten. Biome können sie überschreiben.
DETAILS = {
    "himmel": "Über dir spannt sich ein weiter Himmel.",
}
