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

## Starten und testen

    evennia migrate
    evennia start
    evennia test --settings settings.py world.wildlands

Im Spiel (als Builder): `@wildnis nereid = 16,17`. Danach `look`,
`look <detail>`, Richtungen (`n`, `no`, `o`, `so`, `s`, `sw`, `w`, `nw`),
`klettere <richtung>` und `schwimme <richtung>`.
