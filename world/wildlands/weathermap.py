"""
Zeigt das Wetter einer Welt als Textkarte über die Zeit, zum Abstimmen.

Aufruf im Spielverzeichnis:

    python -m world.wildlands.weathermap world.nereid [--start STUNDE]
                                         [--frames ANZAHL] [--step STUNDEN]

Zeichen:  . klar   : locker   - bedeckt   = düster   N Nebel
          , Niesel   / Regen   # Wolkenbruch   G Gewitter
          * Schnee   % starker Schnee

"""

import argparse
from collections import Counter

from .weather import HOUR, season, time_of_day
from .world import get_world

SKY = {"klar": ".", "locker": ":", "bedeckt": "-", "duester": "="}
PRECIPITATION = {
    "niesel": ",",
    "regen": "/",
    "wolkenbruch": "#",
    "schnee": "*",
    "starkschnee": "%",
}


def symbol(weather):
    if weather.thunder:
        return "G"
    if weather.precipitation != "kein":
        return PRECIPITATION[weather.precipitation]
    if weather.fog:
        return "N"
    return SKY[weather.sky]


def frame(world, t):
    """Eine Wetterkarte als Text und die Häufigkeit der Zeichen."""
    maps = world.maps
    counts = Counter()
    lines = []
    for y in range(maps.height - 1, -1, -1):
        line = ""
        for x in range(maps.width):
            weather = world.get_weather((x, y), t)
            if weather is None:
                line += " "
                continue
            char = symbol(weather)
            counts[char] += 1
            line += char
        lines.append(line)
    return "\n".join(lines), counts


def main():
    parser = argparse.ArgumentParser(description="Wetterkarte einer Welt über die Zeit")
    parser.add_argument("world", help="Python-Pfad der Welt, z.B. world.nereid")
    parser.add_argument("--start", type=float, default=0.0, help="erste Spielstunde")
    parser.add_argument("--frames", type=int, default=4, help="Anzahl der Karten")
    parser.add_argument("--step", type=float, default=3.0, help="Spielstunden zwischen Karten")
    args = parser.parse_args()

    world = get_world(args.world)
    if not world.weather_model:
        print("Diese Welt hat kein Wetter.")
        return 1
    print(f"{world.name}: Wetter zieht aus {world.weather_model.wind_origin} heran\n")
    total = Counter()
    for index in range(args.frames):
        hours = args.start + index * args.step
        t = hours * HOUR
        text, counts = frame(world, t)
        total.update(counts)
        day = int(hours // 24) + 1
        print(f"Tag {day}, {hours % 24:04.1f} Uhr ({season(t)}, {time_of_day(t)})")
        print(text + "\n")
    fields = sum(total.values()) or 1
    print(
        "Anteile: "
        + "  ".join(f"{char} {count / fields:.0%}" for char, count in total.most_common())
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
