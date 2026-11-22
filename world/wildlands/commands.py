"""
Befehle für die Wildnis: klettern, schwimmen, Details ansehen und ein
Builder-Befehl zum Betreten.

"""

from evennia import CmdSet
from evennia.commands.default.muxcommand import MuxCommand
from evennia.contrib.grid import wilderness
from evennia.contrib.grid.extended_room.extended_room import CmdExtendedRoomLook

from .rooms import WildlandsMapProvider, WildlandsRoom
from .world import CLIMB, SWIM, WALK, get_world


class CmdWildLook(CmdExtendedRoomLook):
    """
    Umsehen

    Usage:
      look
      look <objekt>
      look <detail>

    Zeigt deine Umgebung, ein Objekt oder ein Detail der Umgebung.
    """

    def look_detail(self):
        caller = self.caller
        location = caller.location
        if not hasattr(location, "get_detail"):
            return False
        detail = location.get_detail(self.args, looker=caller)
        if not detail:
            return False
        caller.msg(detail)
        return True


class _CmdMoveMode(MuxCommand):
    """Gemeinsame Logik für Klettern und Schwimmen."""

    mode = WALK
    not_needed = "Das ist hier nicht nötig."
    locks = "cmd:all()"
    help_category = "Bewegung"

    def func(self):
        caller = self.caller
        location = caller.location
        direction = self.args.strip().lower()
        if not direction:
            caller.msg(f"Wohin? ({self.key} <richtung>)")
            return
        if not isinstance(location, WildlandsRoom):
            caller.msg(self.not_needed)
            return

        exit_obj = None
        for candidate in location.exits:
            if direction == candidate.key or direction in candidate.aliases.all():
                exit_obj = candidate
                break
        if not exit_obj or not exit_obj.access(caller, "traverse"):
            caller.msg("In diese Richtung geht es nicht weiter.")
            return
        if exit_obj.required_movement(caller) != self.mode:
            caller.msg(self.not_needed)
            return

        caller.ndb.wild_move_mode = self.mode
        try:
            exit_obj.at_traverse(caller, exit_obj.destination)
        finally:
            del caller.ndb.wild_move_mode


class CmdClimb(_CmdMoveMode):
    """
    Klettern

    Usage:
      klettere <richtung>

    Bewegt dich kletternd in eine Richtung. Nötig für jeden Schritt, der in
    felsiges Gelände hinein, darin oder wieder hinaus führt.
    """

    key = "klettere"
    aliases = ["klettern", "climb"]
    mode = CLIMB
    not_needed = "Dorthin musst du nicht klettern."


class CmdSwim(_CmdMoveMode):
    """
    Schwimmen

    Usage:
      schwimme <richtung>

    Bewegt dich schwimmend in eine Richtung. Nötig für jeden Schritt, der in
    tiefes Wasser hinein, darin oder wieder hinaus führt.
    """

    key = "schwimme"
    aliases = ["schwimmen", "swim"]
    mode = SWIM
    not_needed = "Dorthin musst du nicht schwimmen."


class CmdEnterWild(MuxCommand):
    """
    Wildnis betreten (Builder)

    Usage:
      @wildnis <welt> [= <x>,<y>]

    Legt die Wildnis einer Welt an, falls es sie noch nicht gibt, und setzt
    dich auf die angegebene Koordinate. Ohne Koordinate landest du auf dem
    ersten begehbaren Feld.

    Example:
      @wildnis nereid = 12,8
    """

    key = "@wildnis"
    locks = "cmd:perm(Builder)"
    help_category = "Building"

    def func(self):
        caller = self.caller
        name = self.lhs.strip().lower()
        if not name:
            caller.msg("Usage: @wildnis <welt> [= <x>,<y>]")
            return
        world_path = f"world.{name}"
        try:
            world = get_world(world_path)
        except (ImportError, AttributeError):
            caller.msg(f"Es gibt keine Welt '{name}' (gesucht: {world_path}.WORLD).")
            return

        wilderness.create_wilderness(name=name, mapprovider=WildlandsMapProvider(world_path))

        if self.rhs:
            try:
                x, y = (int(part) for part in self.rhs.split(","))
            except ValueError:
                caller.msg("Koordinaten bitte als x,y angeben.")
                return
            coordinates = (x, y)
        else:
            coordinates = next(
                (
                    coords
                    for coords in world.maps.iter_coordinates()
                    if world.get_movement(coords) == WALK
                ),
                None,
            )
        if coordinates is None or not world.is_valid(coordinates):
            caller.msg(f"Das Feld {coordinates} kann man nicht betreten.")
            return

        if wilderness.enter_wilderness(caller, coordinates=coordinates, name=name):
            caller.msg(caller.at_look(caller.location))
        else:
            caller.msg("Das hat nicht geklappt.")


class WildlandsCmdSet(CmdSet):
    """Alle Befehle der Wildnis. In das Character-Cmdset einhängen."""

    def at_cmdset_creation(self):
        self.add(CmdWildLook())
        self.add(CmdClimb())
        self.add(CmdSwim())
        self.add(CmdEnterWild())
