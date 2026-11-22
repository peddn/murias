"""
Kartenebenen aus Textdateien.

Jede Ebene ist eine Textdatei mit einem Zeichen pro Feld. Die erste Zeile der
Datei ist der Norden der Karte. Koordinaten sind `(x, y)`, wobei `(0, 0)` wie im
Wilderness-Contrib die linke untere Ecke ist. Ein Leerzeichen bedeutet "kein
Eintrag" (in der Biom-Ebene: das Feld existiert nicht).

"""

from pathlib import Path

EMPTY = " "


class MapLayers:
    """
    Mehrere gleich große Textebenen.

    Args:
        directory (str or Path): Verzeichnis mit den Dateien `<name>.map`.
        names (iterable): Namen der Ebenen. Fehlende Dateien ergeben eine
            leere Ebene.

    """

    def __init__(self, directory, names):
        self.directory = Path(directory)
        self.layers = {}
        raw = {}
        for name in names:
            path = self.directory / f"{name}.map"
            lines = []
            if path.exists():
                lines = path.read_text(encoding="utf-8").split("\n")
                # eine abschließende Leerzeile gehört nicht zur Karte
                while lines and not lines[-1].strip():
                    lines.pop()
            raw[name] = lines

        self.height = max((len(lines) for lines in raw.values()), default=0)
        self.width = max((len(line) for lines in raw.values() for line in lines), default=0)

        for name, lines in raw.items():
            padded = [line.ljust(self.width, EMPTY) for line in lines]
            padded += [EMPTY * self.width] * (self.height - len(padded))
            self.layers[name] = padded

    def get(self, layer, coordinates, default=EMPTY):
        """
        Zeichen einer Ebene an einer Koordinate.

        Args:
            layer (str): Name der Ebene.
            coordinates (tuple): `(x, y)`.
            default (str): Rückgabe außerhalb der Karte.

        Returns:
            str: Das Zeichen an dieser Stelle.

        """
        x, y = coordinates
        if not (0 <= x < self.width and 0 <= y < self.height):
            return default
        return self.layers[layer][self.height - 1 - y][x]

    def iter_coordinates(self):
        """Alle Koordinaten der Karte, zeilenweise von Norden nach Süden."""
        for y in range(self.height - 1, -1, -1):
            for x in range(self.width):
                yield (x, y)
