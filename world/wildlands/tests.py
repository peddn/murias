"""
Tests für die Wildnis-Mechanik, anhand der Testwelt Nereid.

    evennia test --settings settings.py world.wildlands

"""

from evennia.contrib.grid import wilderness
from evennia.utils.test_resources import BaseEvenniaCommandTest, BaseEvenniaTest

from . import commands
from .check import check_world
from .rooms import WildlandsMapProvider, WildlandsRoom
from .world import BLOCKED, CLIMB, SWIM, WALK, get_world

WORLD_PATH = "world.nereid"

# Felder der Testkarte
GRASS = (14, 13)
GRASS_BY_ROCK = (16, 17)  # westlich davon liegt Fels
ROCK = (15, 17)
ROCK_BY_CLIFF = (12, 17)  # westlich und nördlich davon Steilwand
CLIFF = (10, 18)
LAKE = (22, 11)
SHORE = (14, 11)  # Wiese; östlich davon (15, 11) noch Wiese, dann See
BRIDGE = (22, 12)
FOREST = (30, 18)
PLATEAU = (27, 16)  # Wald mit gezeichneter Höhe 4


class TestWorld(BaseEvenniaTest):
    def setUp(self):
        super().setUp()
        self.world = get_world(WORLD_PATH)

    def test_map_has_no_problems(self):
        self.assertEqual(check_world(self.world), [])

    def test_biomes(self):
        self.assertEqual(self.world.get_biome(GRASS).key, "grass")
        self.assertEqual(self.world.get_biome(ROCK).key, "rock")
        self.assertEqual(self.world.get_biome(LAKE).key, "lake")
        self.assertIsNone(self.world.get_biome((0, 0)))
        self.assertIsNone(self.world.get_biome((-5, 999)))

    def test_movement(self):
        self.assertEqual(self.world.get_movement(GRASS), WALK)
        self.assertEqual(self.world.get_movement(ROCK), CLIMB)
        self.assertEqual(self.world.get_movement(LAKE), SWIM)
        self.assertEqual(self.world.get_movement(CLIFF), BLOCKED)
        self.assertEqual(self.world.get_movement((0, 0)), BLOCKED)
        self.assertFalse(self.world.is_valid(CLIFF))

    def test_walkable_overlay(self):
        self.assertEqual(self.world.get_biome(BRIDGE).key, "lake")
        self.assertEqual(self.world.get_movement(BRIDGE), WALK)
        # auf der Brücke gelten ihr Name und ihre Beschreibung, nicht die des Sees
        self.assertEqual(self.world.get_location_name(BRIDGE), "Spiegelsee (Brücke)")
        self.assertNotIn("schwimmst", self.world.describe(BRIDGE))
        self.assertNotIn("Wellen schlagen", self.world.describe(BRIDGE))

    def test_required_movement(self):
        world = self.world
        # hinein, innerhalb und hinaus zählt alles als Klettern
        self.assertEqual(world.required_movement(GRASS_BY_ROCK, ROCK), CLIMB)
        self.assertEqual(world.required_movement(ROCK, (14, 17)), CLIMB)
        self.assertEqual(world.required_movement(ROCK, GRASS_BY_ROCK), CLIMB)
        self.assertEqual(world.required_movement(GRASS, (15, 13)), WALK)
        # von der Brücke ins Wasser muss man schwimmen, auf der Brücke nicht
        self.assertEqual(world.required_movement(BRIDGE, LAKE), SWIM)
        self.assertEqual(world.required_movement(BRIDGE, (23, 12)), WALK)

    def test_height(self):
        self.assertEqual(self.world.get_height(GRASS), 2)  # Standard der Wiese
        self.assertEqual(self.world.get_height(PLATEAU), 4)  # gezeichnet
        self.assertEqual(self.world.get_height_band(GRASS), "tief")
        self.assertEqual(self.world.get_height_band(PLATEAU), "mittel")
        self.assertEqual(self.world.get_height_band(ROCK_BY_CLIFF), "alpin")

    def test_names(self):
        self.assertEqual(self.world.get_location_name(GRASS), "Wiese")
        self.assertEqual(self.world.get_location_name(FOREST), "Düsterwald (Wald)")

    def test_describe_is_stable_and_varied(self):
        first = self.world.describe(GRASS)
        self.assertTrue(first)
        self.assertEqual(first, self.world.describe(GRASS))
        variants = {self.world.describe((x, 6)) for x in range(10, 30)}
        self.assertGreater(len(variants), 1)

    def test_describe_surroundings(self):
        text = self.world.describe(GRASS_BY_ROCK)
        self.assertIn("Im Norden und Westen siehst du schroffen Fels.", text)

    def test_details(self):
        details = self.world.get_details(FOREST)
        self.assertIn("bäume", details)
        # das Biom überschreibt das überall geltende Detail
        self.assertIn("Kronen", details["himmel"])
        self.assertIn("weiter Himmel", self.world.get_details(GRASS)["himmel"])
        # Überlagerung bringt eigene Details mit
        self.assertIn("steg", self.world.get_details(BRIDGE))


class TestWildlandsInGame(BaseEvenniaCommandTest):
    def setUp(self):
        super().setUp()
        wilderness.create_wilderness(
            name="nereid", mapprovider=WildlandsMapProvider(WORLD_PATH)
        )
        self.script = wilderness.WildernessScript.objects.get(db_key="nereid")

    def enter(self, coordinates):
        self.assertTrue(
            wilderness.enter_wilderness(self.char1, coordinates=coordinates, name="nereid")
        )

    def coordinates(self):
        return self.script.db.itemcoordinates[self.char1]

    def test_room_and_exits(self):
        self.enter(GRASS)
        room = self.char1.location
        self.assertIsInstance(room, WildlandsRoom)
        self.assertEqual(room.get_display_name(None), "Wiese")
        self.assertEqual(room.get_display_desc(self.char1), room.world.describe(GRASS))
        north = [exit_obj for exit_obj in room.exits if exit_obj.key == "north"][0]
        self.assertEqual(north.get_display_name(self.char1), "Norden")
        self.enter(GRASS_BY_ROCK)
        west = [e for e in self.char1.location.exits if e.key == "west"][0]
        self.assertEqual(west.get_display_name(self.char1), "Westen (klettern)")
        self.assertIn("Ausgänge:", self.char1.location.get_display_exits(self.char1))
        self.assertIn("norden", north.aliases.all())
        self.assertIn("n", north.aliases.all())

    def test_description_follows_coordinates(self):
        self.enter(GRASS)
        self.assertIn(
            self.char1.location.world.describe(GRASS),
            self.call(commands.CmdWildLook(), "", "Wiese"),
        )
        self.script.move_obj(self.char1, FOREST)
        self.call(commands.CmdWildLook(), "", "Düsterwald (Wald)")

    def test_look_detail(self):
        self.enter(FOREST)
        self.call(commands.CmdWildLook(), "bäume", "Die Stämme sind so dick")
        self.call(commands.CmdWildLook(), "bäu", "Die Stämme sind so dick")
        self.call(commands.CmdWildLook(), "einhorn", "Could not find 'einhorn'.")

    def test_walking_into_rock_is_refused(self):
        self.enter(GRASS_BY_ROCK)
        west = [e for e in self.char1.location.exits if e.key == "west"][0]
        self.assertFalse(west.at_traverse(self.char1, west.destination))
        self.assertEqual(self.coordinates(), GRASS_BY_ROCK)

    def test_climb(self):
        self.enter(GRASS_BY_ROCK)
        self.call(commands.CmdClimb(), "süden", "Dorthin musst du nicht klettern.")
        self.call(commands.CmdClimb(), "w", "Grauzinnen (Fels)")
        self.assertEqual(self.coordinates(), ROCK)
        # im Fels und wieder hinaus geht es auch nur kletternd
        east = [e for e in self.char1.location.exits if e.key == "east"][0]
        self.assertFalse(east.at_traverse(self.char1, east.destination))
        self.call(commands.CmdClimb(), "o", "Wiese")
        self.assertEqual(self.coordinates(), GRASS_BY_ROCK)
        self.assertIsNone(self.char1.ndb.wild_move_mode)

    def test_swim_and_bridge(self):
        self.enter(BRIDGE)
        east = [e for e in self.char1.location.exits if e.key == "east"][0]
        self.assertTrue(east.at_traverse(self.char1, east.destination))
        self.assertEqual(self.coordinates(), (23, 12))
        self.call(commands.CmdSwim(), "süden", "Spiegelsee (See)")
        self.assertEqual(self.coordinates(), (23, 11))
        self.call(commands.CmdClimb(), "süden", "Dorthin musst du nicht klettern.")

    def test_blocked_field_has_no_exit(self):
        self.enter(ROCK_BY_CLIFF)
        self.call(commands.CmdClimb(), "norden", "In diese Richtung geht es nicht weiter.")
