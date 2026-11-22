"""
Sätze mit Bedingungen.

Jeder Satz gehört zu einem Thema (z.B. "niederschlag") und nennt die
Bedingungen, unter denen er passt. Pro Thema wird höchstens ein Satz gewählt:
unter allen passenden der mit den meisten Bedingungen, also der speziellste.
Sätze ohne Bedingung sind der Rückfall und müssen immer stimmen.

Beispiel:

    S("niederschlag", "Feiner Regen fällt gleichmäßig.",
      niederschlag="regen", wind=("still", "brise"))
    S("niederschlag", "Es tropft unablässig aus dem Blätterdach.",
      niederschlag="regen", wind=("still", "brise"), biom="forest")

Im Wald gewinnt der zweite Satz, überall sonst der erste.

"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Sentence:
    """
    Attributes:
        topic: Thema des Satzes.
        texts: Gleichwertige Varianten.
        when: Bedingungen, `{schlüssel: wert oder tuple erlaubter werte}`.

    """

    topic: str
    texts: tuple
    when: tuple

    def matches(self, state):
        for key, allowed in self.when:
            if state.get(key) not in allowed:
                return False
        return True


def S(topic, *texts, **when):
    """Kurzschreibweise für einen Satz, siehe Modulbeschreibung."""
    conditions = tuple(
        (key, value if isinstance(value, tuple) else (value,)) for key, value in when.items()
    )
    return Sentence(topic, texts, conditions)


class SentenceBook:
    """
    Sammlung von Sätzen.

    Args:
        sentences (iterable): Die Sätze.

    """

    def __init__(self, sentences):
        self.by_topic = {}
        for sentence in sentences:
            self.by_topic.setdefault(sentence.topic, []).append(sentence)

    def candidates(self, topic, state):
        """Texte der speziellsten Sätze, die zum Zustand passen."""
        best = -1
        texts = []
        for sentence in self.by_topic.get(topic, ()):
            if not sentence.matches(state):
                continue
            specificity = len(sentence.when)
            if specificity > best:
                best = specificity
                texts = list(sentence.texts)
            elif specificity == best:
                texts.extend(sentence.texts)
        return texts

    def choose(self, topic, state, pick):
        """
        Wählt einen Satz zu einem Thema.

        Args:
            topic (str): Das Thema.
            state (dict): Der aktuelle Zustand.
            pick (callable): `pick(options, salt)` wählt stabil eine Variante.

        Returns:
            str: Der Satz, oder "" wenn keiner passt. Platzhalter wie
            `{woher}` werden aus dem Zustand gefüllt.

        """
        texts = self.candidates(topic, state)
        if not texts:
            return ""
        return pick(texts, topic).format_map(_Fallback(state))


class _Fallback(dict):
    """Lässt unbekannte Platzhalter stehen, statt einen Fehler zu werfen."""

    def __missing__(self, key):
        return "{" + key + "}"
