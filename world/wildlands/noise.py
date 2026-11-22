"""
Rauschfelder.

Dünne Schicht über der Bibliothek `opensimplex`. Wetter und Ressourcen benutzen
nur dieses Modul, damit die Bibliothek an einer Stelle austauschbar bleibt.

Wichtig: Wetter und Ressourcen hängen an den exakten Zahlen. Die Version der
Bibliothek ist deshalb in `requirements.txt` festgelegt, und die Tests halten
Referenzwerte fest.

"""

import math

from opensimplex import OpenSimplex

# Generatoren pro Startwert. Sie werden hier gehalten und nicht in den
# Feldern, damit Felder einfache, kopierbare Daten bleiben.
_generators = {}


def _generator(seed):
    if seed not in _generators:
        _generators[seed] = OpenSimplex(seed=seed)
    return _generators[seed]


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


class Field:
    """
    Ein Rauschfeld über zwei Raumachsen und einer dritten Achse (meist Zeit).

    Args:
        seed (int): Startwert. Gleicher Startwert ergibt dasselbe Feld.
        scale (float): Größe der Strukturen in Feldern der Karte.
        octaves (int): Anzahl überlagerter Schichten. Mehr Schichten ergeben
            feinere Details an den Rändern.
        warp (float): Stärke der Verzerrung, als Anteil von `scale`. Macht
            Formen geschwungen statt rundlich.

    """

    def __init__(self, seed, scale, octaves=1, warp=0.0):
        self.seed = seed
        self.scale = float(scale)
        self.octaves = octaves
        self.warp = warp

    def raw(self, x, y, z=0.0):
        """Wert des Feldes, ungefähr im Bereich -1 bis 1."""
        x /= self.scale
        y /= self.scale
        if self.warp:
            warper = _generator(self.seed + 7919)
            dx = warper.noise3(x * 0.5 + 31.4, y * 0.5, z)
            dy = warper.noise3(x * 0.5, y * 0.5 + 47.1, z)
            x += self.warp * dx
            y += self.warp * dy
        generator = _generator(self.seed)
        total = 0.0
        amplitude = 1.0
        frequency = 1.0
        norm = 0.0
        for octave in range(self.octaves):
            # jede Schicht an einer anderen Stelle des Rauschens abtasten
            total += amplitude * generator.noise3(
                x * frequency + octave * 19.7, y * frequency - octave * 11.3, z
            )
            norm += amplitude
            amplitude *= 0.5
            frequency *= 2.0
        return total / norm

    def at(self, x, y, z=0.0):
        """
        Wert des Feldes im Bereich 0 bis 1.

        Die Rohwerte häufen sich um die Mitte. Sie werden so gestreckt, dass
        der ganze Bereich genutzt wird und Schwellwerte gut greifen.

        """
        return clamp(0.5 + 0.5 * math.tanh(self.raw(x, y, z) * 2.2) / math.tanh(1.1))

    def gradient(self, x, y, z=0.0):
        """Steigung des Feldes pro `scale`, als `(gx, gy)`."""
        step = self.scale * 0.05
        gx = (self.at(x + step, y, z) - self.at(x - step, y, z)) / 0.1
        gy = (self.at(x, y + step, z) - self.at(x, y - step, z)) / 0.1
        return gx, gy
