# murias

Ein MUD auf Basis von [Evennia](https://www.evennia.com) (entwickelt mit 6.1.0).

## Aufbau

- `world/wildlands/` – Mechanik für eine handgezeichnete Wildnis, aufbauend auf
  dem Evennia-Contrib `grid/wilderness`. Enthält keinen Weltinhalt.
- `world/nereid/` – Testwelt: Kartenebenen (`maps/*.map`), Biome, Regionen,
  Überlagerungen und Texte.
- `tools/play.py` – kleiner Telnet-Client, um einen laufenden Server per Skript
  zu bespielen.

## Karte

Jede Ebene ist eine Textdatei mit einem Zeichen pro Feld, die erste Zeile ist
Norden. `(0, 0)` ist die linke untere Ecke.

| Datei | Inhalt |
|---|---|
| `biome.map` | Geländeart. Leerzeichen = Feld existiert nicht. |
| `height.map` | Höhenlevel 0–9. Leer = Standardhöhe des Bioms. |
| `region.map` | Benannte Gebiete. |
| `overlay.map` | Straßen, Brücken und Ähnliches über dem Biom. |

Karte anzeigen und prüfen:

    python -m world.wildlands.check world.nereid

## Wetter

Das Wetter wird aus Ort und Spielzeit berechnet (`world/wildlands/weather.py`),
gespeichert wird nichts. Rauschfelder aus `opensimplex` werden mit festem Wind
über die Karte geschoben. Die Stellschrauben stehen als `WeatherConfig` in
`world/nereid/__init__.py`, die Sätze mit ihren Bedingungen in
`world/nereid/sentences.py`.

Wetterkarte über die Zeit ansehen:

    python -m world.wildlands.weathermap world.nereid --start 0 --frames 4 --step 3

Im Spiel: `wetter` für alle, `@wetter` zeigt Buildern die Rohwerte,
`@wetter/vor <stunden>` spult die Wetterzeit vor, `@wetter/reset` zurück.

## Orte

Städte, Höhlen und Dungeons sind Gebiete aus normalen Räumen auf Karten des
Contribs `grid/xyzgrid`. Die Räume (`world/wildlands/places.py`) verbinden
XYZRoom mit ExtendedRoom. Ein Gebiet legt in den `options` seiner Karte fest,
von welcher Wildniskoordinate es sein Wetter bekommt und welches Klima gilt.
Drinnen oder draußen wird pro Raum im Prototyp gesetzt. Beispiel:
`world/nereid/places.py`.

In der Wildnis belegt ein Ort Felder der Biom-Ebene: `x` Mauer, `o` Tor. Zu
jedem Tor gehört ein Zugang in `world/nereid/portals.py`, der sagt, aus
welcher Richtung man in welchen Raum kommt.

Karten registrieren und Räume erzeugen (auch nach Änderungen):

    evennia xyzgrid add world.nereid.places
    evennia xyzgrid spawn

Beim Serverstart werden die Wildnis angelegt und die Ausgänge der Tore zurück
in die Wildnis abgeglichen (`WILDLANDS_WORLDS` in den Einstellungen).

## Starten und testen

    pip install -r requirements.txt     # dazu scipy für das XYZGrid
    evennia migrate
    evennia xyzgrid add world.nereid.places
    evennia xyzgrid spawn
    evennia start
    evennia test --settings settings.py world.wildlands

Im Spiel (als Builder): `@wildnis nereid = 16,17`. Danach `look`,
`look <detail>`, Richtungen (`n`, `no`, `o`, `so`, `s`, `sw`, `w`, `nw`),
`klettere <richtung>` und `schwimme <richtung>`.
