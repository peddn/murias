"""
Tests für die Wildnis-Mechanik, anhand der Testwelt Nereid.

    evennia test --settings settings.py world.wildlands

"""

import itertools
import random
from unittest import mock

from evennia.contrib.grid import wilderness
from evennia.utils.test_resources import BaseEvenniaCommandTest, BaseEvenniaTest

from . import commands
from .check import check_world
from .rooms import WildlandsMapProvider, WildlandsRoom
from .noise import Field
from .places import GateExit, PlaceRoom, find_place_room, sync_portals
from .scripts import weather_messages
from .sentences import S, SentenceBook
from .weather import HOUR, YEAR, season, time_of_day
from .world import BLOCKED, CLIMB, SWIM, WALK, WorldDefinition, get_world

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

# Referenzwerte des Rauschens, siehe TestNoise
REFERENCE = (0.7640841003178759, 0.46214568566664993, 0.23708281740360182)

# feste Spielzeit für Tests: ein Sommernachmittag
SUMMER_DAY = (190 * 24 + 15) * HOUR


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
        self.assertNotIn("schwimmst", self.world.describe(BRIDGE, t=SUMMER_DAY))
        self.assertNotIn("Wellen schlagen dir ins", self.world.describe(BRIDGE, t=SUMMER_DAY))

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
        first = self.world.describe(GRASS, t=SUMMER_DAY)
        self.assertTrue(first)
        self.assertEqual(first, self.world.describe(GRASS, t=SUMMER_DAY))
        variants = {self.world.describe((x, 6), t=SUMMER_DAY) for x in range(10, 30)}
        self.assertGreater(len(variants), 1)

    def test_describe_surroundings(self):
        text = self.world.describe(GRASS_BY_ROCK, t=SUMMER_DAY)
        self.assertIn("Im Norden und Westen siehst du schroffen Fels.", text)

    def test_details(self):
        details = self.world.get_details(FOREST, t=SUMMER_DAY)
        self.assertIn("bäume", details)
        # im Wald sieht man den Himmel nicht: fester Text des Bioms
        self.assertIn("Kronen", details["himmel"])
        # auf der Wiese wird der Himmel aus dem Wetter berechnet
        grass = self.world.get_details(GRASS, t=SUMMER_DAY)
        self.assertEqual(
            grass["himmel"],
            " ".join(
                self.world.describe_weather(
                    GRASS, SUMMER_DAY, topics=("himmel", "niederschlag", "trend")
                )
            ),
        )
        self.assertIn("wetter", grass)
        # Überlagerung bringt eigene Details mit
        self.assertIn("steg", self.world.get_details(BRIDGE, t=SUMMER_DAY))


class TestWildlandsInGame(BaseEvenniaCommandTest):
    def setUp(self):
        super().setUp()
        wilderness.create_wilderness(
            name="nereid", mapprovider=WildlandsMapProvider(WORLD_PATH)
        )
        self.script = wilderness.WildernessScript.objects.get(db_key="nereid")
        # feste Zeit, damit das Wetter während eines Tests nicht umschlägt
        patcher = mock.patch.object(WorldDefinition, "now", return_value=SUMMER_DAY)
        patcher.start()
        self.addCleanup(patcher.stop)

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

    def test_weather_commands(self):
        self.enter(GRASS)
        world = self.char1.location.world
        expected = " ".join(world.describe_weather(GRASS, SUMMER_DAY))
        self.call(commands.CmdWeather(), "", expected)
        self.call(commands.CmdWeatherAdmin(), "", "Wetter bei (14, 13) (grass, Höhe 2), Tag 191, 15.0 Uhr")


class TestNoise(BaseEvenniaTest):
    def test_reference_values(self):
        """
        Wetter und Ressourcen hängen an den exakten Zahlen. Schlägt dieser Test
        nach einem Update der Noise-Bibliothek fehl, hat sich die Welt verschoben.
        """
        field = Field(seed=4711, scale=40, octaves=3, warp=0.5)
        self.assertAlmostEqual(field.at(0, 0, 0), REFERENCE[0], places=6)
        self.assertAlmostEqual(field.at(12.5, 80.0, 3.2), REFERENCE[1], places=6)
        self.assertAlmostEqual(field.at(-300.0, 41.0, 100.0), REFERENCE[2], places=6)

    def test_range_and_smoothness(self):
        field = Field(seed=1, scale=40, octaves=3, warp=0.5)
        values = [field.at(x * 3.7, y * 2.9, 0.4) for x in range(30) for y in range(30)]
        self.assertGreaterEqual(min(values), 0.0)
        self.assertLessEqual(max(values), 1.0)
        # der ganze Bereich wird genutzt
        self.assertLess(min(values), 0.1)
        self.assertGreater(max(values), 0.9)
        # Nachbarfelder unterscheiden sich kaum
        self.assertLess(abs(field.at(10, 10) - field.at(11, 10)), 0.15)


class TestWeather(BaseEvenniaTest):
    def setUp(self):
        super().setUp()
        self.world = get_world(WORLD_PATH)
        rng = random.Random(7)
        valid = [c for c in self.world.maps.iter_coordinates() if self.world.is_valid(c)]
        self.samples = [(rng.choice(valid), rng.uniform(0, YEAR)) for _ in range(600)]

    def test_calendar(self):
        self.assertEqual(time_of_day(3 * HOUR), "nacht")
        self.assertEqual(time_of_day(7 * HOUR), "morgen")
        self.assertEqual(time_of_day(13 * HOUR), "tag")
        self.assertEqual(time_of_day(20 * HOUR), "abend")
        self.assertEqual(season(0), "winter")
        self.assertEqual(season(SUMMER_DAY), "sommer")
        self.assertEqual(season(100 * 24 * HOUR), "fruehling")
        self.assertEqual(season(280 * 24 * HOUR), "herbst")

    def test_is_a_pure_function(self):
        for coordinates, t in self.samples[:20]:
            self.assertEqual(
                self.world.get_weather(coordinates, t), self.world.get_weather(coordinates, t)
            )

    def test_no_impossible_combinations(self):
        seen = set()
        for coordinates, t in self.samples:
            weather = self.world.get_weather(coordinates, t)
            seen.add(weather.precipitation)
            if weather.precipitation != "kein":
                self.assertIn(weather.sky, ("bedeckt", "duester"))
                self.assertFalse(weather.fog)
            if weather.is_snow:
                self.assertLess(weather.temperature, 0.5)
            if weather.is_wet:
                self.assertGreaterEqual(weather.temperature, 0.5)
            if weather.fog:
                self.assertEqual(weather.wind, "still")
            if weather.thunder:
                self.assertEqual(weather.precipitation, "wolkenbruch")
        # über ein Jahr kommt Regen wie Schnee vor
        self.assertIn("regen", seen)
        self.assertIn("schnee", seen)

    def test_neighbours_have_similar_weather(self):
        for coordinates, t in self.samples[:100]:
            x, y = coordinates
            here = self.world.weather_model.at((x, y), t)
            there = self.world.weather_model.at((x + 1, y), t)
            self.assertLess(abs(here.cloudiness - there.cloudiness), 0.2)

    def test_height_and_season_change_temperature(self):
        model = self.world.weather_model
        low = model.at((20, 10), SUMMER_DAY, height=1).temperature
        high = model.at((20, 10), SUMMER_DAY, height=8).temperature
        self.assertGreater(low - high, 10)
        winter = model.at((20, 10), 10 * 24 * HOUR + 15 * HOUR, height=1).temperature
        self.assertGreater(low - winter, 8)

    def test_shelter_reduces_wind(self):
        model = self.world.weather_model
        levels = ("still", "brise", "boeig", "sturm")
        for coordinates, t in self.samples[:100]:
            open_wind = levels.index(model.at(coordinates, t).wind)
            sheltered = levels.index(model.at(coordinates, t, shelter=1).wind)
            self.assertEqual(sheltered, max(0, open_wind - 1))

    def test_state(self):
        state = self.world.get_state(FOREST, SUMMER_DAY)
        self.assertEqual(state["biom"], "forest")
        self.assertEqual(state["tageszeit"], "tag")
        self.assertEqual(state["jahreszeit"], "sommer")
        self.assertEqual(state["sicht"], "verdeckt")
        self.assertEqual(state["woher"], "Westen")
        self.assertIn(state["boden"], ("trocken", "nass", "schnee"))
        self.assertIn(state["trend"], ("aufzug", "abzug", "gleich"))

    def test_ground_remembers_rain(self):
        """Nach dem Regen ist der Boden noch eine Weile nass."""
        found = False
        for hours in range(0, 24 * 60):
            t = SUMMER_DAY + hours * HOUR
            now = self.world.get_weather(GRASS, t)
            before = self.world.get_weather(GRASS, t - HOUR)
            if now.precipitation == "kein" and before.is_wet:
                self.assertEqual(self.world.get_state(GRASS, t)["boden"], "nass")
                found = True
                break
        self.assertTrue(found, "in 60 Tagen hat es auf der Wiese nie geregnet")

    def test_description_contains_weather(self):
        text = self.world.describe(GRASS, t=SUMMER_DAY)
        for sentence in self.world.describe_weather(GRASS, SUMMER_DAY):
            self.assertIn(sentence, text)


class TestSentences(BaseEvenniaTest):
    def setUp(self):
        super().setUp()
        self.world = get_world(WORLD_PATH)
        self.book = self.world.sentences

    def test_most_specific_wins(self):
        book = SentenceBook(
            (
                S("t", "allgemein"),
                S("t", "regen", niederschlag="regen"),
                S("t", "regen im wald", niederschlag="regen", biom="forest"),
            )
        )
        first = lambda options, salt: options[0]  # noqa: E731
        self.assertEqual(book.choose("t", {}, first), "allgemein")
        self.assertEqual(book.choose("t", {"niederschlag": "regen"}, first), "regen")
        self.assertEqual(
            book.choose("t", {"niederschlag": "regen", "biom": "forest"}, first), "regen im wald"
        )
        self.assertEqual(book.choose("x", {}, first), "")

    def test_placeholders(self):
        book = SentenceBook((S("t", "Aus dem {woher} kommt {unbekannt}."),))
        text = book.choose("t", {"woher": "Westen"}, lambda options, salt: options[0])
        self.assertEqual(text, "Aus dem Westen kommt {unbekannt}.")

    def test_every_precipitation_has_a_sentence(self):
        """Für jede Kombination aus Niederschlag, Wind und Biom gibt es einen Satz."""
        precipitation = ("niesel", "regen", "wolkenbruch", "schnee", "starkschnee")
        wind = ("still", "brise", "boeig", "sturm")
        biomes = [biome.key for biome in self.world.biomes.values()]
        for combo in itertools.product(precipitation, wind, biomes, ("ja", "nein")):
            state = dict(zip(("niederschlag", "wind", "biom", "gewitter"), combo))
            self.assertTrue(self.book.candidates("niederschlag", state), state)

    def test_wind_and_rain_never_contradict(self):
        """Bei starkem Wind darf kein Satz von ruhigem Regen sprechen."""
        calm_words = ("gleichmäßig", "senkrecht", "lautlos", "unablässig")
        for precipitation in ("niesel", "regen", "wolkenbruch", "schnee", "starkschnee"):
            for biome in self.world.biomes.values():
                state = {
                    "niederschlag": precipitation,
                    "wind": "sturm",
                    "biom": biome.key,
                    "gewitter": "nein",
                }
                for text in self.book.candidates("niederschlag", state):
                    for word in calm_words:
                        self.assertNotIn(word, text, state)

    def test_every_open_sky_has_a_sentence(self):
        for sky, daytime in itertools.product(
            ("klar", "locker", "bedeckt", "duester"), ("nacht", "morgen", "tag", "abend")
        ):
            state = {"himmel": sky, "tageszeit": daytime, "sicht": "frei"}
            self.assertTrue(self.book.candidates("himmel", state), state)

    def test_every_change_has_a_message(self):
        levels = ("kein", "niesel", "regen", "wolkenbruch", "schnee", "starkschnee")
        for old, new in itertools.permutations(levels, 2):
            self.assertTrue(self.book.candidates("wechsel", {"von": old, "zu": new}), (old, new))

    def test_weather_messages(self):
        """Findet einen Regenbeginn und prüft die Meldung dazu."""
        world = self.world
        for hours in range(0, 24 * 60):
            t = SUMMER_DAY + hours * HOUR
            before = world.get_weather(GRASS, t)
            after = world.get_weather(GRASS, t + HOUR)
            if before.precipitation == "kein" and after.is_wet:
                site = world.site_at(GRASS)
                messages = weather_messages(world, site, before, after, t)
                self.assertTrue(any("egen" in message or "niesel" in message for message in messages))
                self.assertEqual(weather_messages(world, site, after, after, t), [])
                return
        self.fail("in 60 Tagen hat es auf der Wiese nie zu regnen begonnen")


class TestPlaces(BaseEvenniaCommandTest):
    """Orte aus normalen Räumen und ihre Zugänge, anhand von Furtheim und dem Wachturm."""

    def setUp(self):
        super().setUp()
        from evennia.contrib.grid.xyzgrid.xyzgrid import get_xyzgrid

        self.grid = get_xyzgrid()
        # über den Modulpfad laden, wie es `evennia xyzgrid add` tut
        self.grid.add_maps(*self.grid.maps_from_module("world.nereid.places"))
        self.grid.reload()
        self.grid.spawn()
        wilderness.create_wilderness(
            name="nereid", mapprovider=WildlandsMapProvider(WORLD_PATH)
        )
        self.script = wilderness.WildernessScript.objects.get(db_key="nereid")
        self.problems = sync_portals(WORLD_PATH, "nereid")
        self.world = get_world(WORLD_PATH)
        self.set_time(SUMMER_DAY)

    def set_time(self, t):
        patcher = mock.patch.object(WorldDefinition, "now", return_value=t)
        patcher.start()
        self.addCleanup(patcher.stop)

    def place(self, x, y, z="furtheim"):
        return find_place_room((x, y, z))

    def enter(self, coordinates):
        self.assertTrue(
            wilderness.enter_wilderness(self.char1, coordinates=coordinates, name="nereid")
        )

    def wild_exit(self, key):
        return [e for e in self.char1.location.exits if e.key == key][0]

    def test_rooms_combine_both_contribs(self):
        market = self.place(2, 2)
        self.assertIsInstance(market, PlaceRoom)
        self.assertEqual(market.xyz, (2, 2, "furtheim"))
        self.assertEqual(market.get_detail("brunnen"), "Ein achteckiges Becken aus grauem Stein.")
        self.assertEqual(self.problems, [])

    def test_indoor_and_outdoor(self):
        market = self.place(2, 2)
        smithy = self.place(1, 3)
        self.assertTrue(market.is_outdoor)
        self.assertFalse(smithy.is_outdoor)
        self.assertIsNone(smithy.get_site())
        self.assertIsNone(smithy.get_weather_site())
        self.assertIsNone(smithy.get_detail("wetter"))
        # drinnen bleibt die Beschreibung, wie sie geschrieben wurde
        self.assertTrue(smithy.get_display_desc(self.char1).endswith("Zangen und Hämmer."))

    def test_site_comes_from_area_settings(self):
        site = self.place(2, 2).get_site()
        self.assertEqual(site.coordinates, (18, 5))
        self.assertEqual(site.biom, "platz")
        self.assertEqual(site.height, 2)
        self.assertEqual(self.place(2, 3).get_site().biom, "strasse")
        garden = self.place(3, 1).get_site()
        self.assertEqual((garden.biom, garden.shelter), ("garten", 1))
        tower = self.place(0, 0, "wachturm").get_site()
        self.assertEqual((tower.coordinates, tower.height, tower.biom), ((42, 15), 3, "hof"))

    def test_same_weather_everywhere_outdoors(self):
        first = self.world.site_weather(self.place(2, 3).get_site(), SUMMER_DAY)
        second = self.world.site_weather(self.place(1, 2).get_site(), SUMMER_DAY)
        self.assertEqual(first, second)
        desc = self.place(1, 2).get_display_desc(self.char1)
        for sentence in self.world.describe_weather(
            (18, 5), SUMMER_DAY, site=self.place(1, 2).get_site()
        ):
            self.assertIn(sentence, desc)

    def test_calendar_and_states(self):
        market = self.place(2, 2)
        self.assertEqual(market.get_season(), "summer")
        self.assertEqual(market.get_time_of_day(), "afternoon")
        states = market.room_states
        self.assertIn("sommer", states)
        self.assertIn("tag", states)
        state = self.world.site_state(market.get_site(), SUMMER_DAY)
        self.assertIn(state["himmel"], states)
        self.assertIn(state["temperatur"], states)
        # drinnen gibt es Tages- und Jahreszeit, aber kein Wetter
        self.assertEqual(self.place(1, 3).room_states, ["sommer", "tag"])

    def test_state_function_in_description(self):
        market = self.place(2, 2)
        self.assertNotIn("Die Stände sind abgebaut", market.get_display_desc(self.char1))
        self.assertNotIn("  ", market.get_display_desc(self.char1))
        self.set_time(SUMMER_DAY + 10 * HOUR)  # ein Uhr nachts
        self.assertIn("Die Stände sind abgebaut", market.get_display_desc(self.char1))

    def test_enter_through_gate(self):
        self.enter((18, 8))
        south = self.wild_exit("south")
        self.assertEqual(south.get_display_name(self.char1), "Süden (Nordtor)")
        self.assertTrue(south.at_traverse(self.char1, south.destination))
        self.assertEqual(self.char1.location, self.place(2, 4))
        self.assertNotIn(self.char1, self.script.db.itemcoordinates)

    def test_wall_refuses_diagonal_entry(self):
        self.enter((17, 8))
        southeast = self.wild_exit("southeast")
        # der Name des Tores steht nur dort, wo man hineinkommt
        self.assertEqual(southeast.get_display_name(self.char1), "Südosten")
        self.assertFalse(southeast.at_traverse(self.char1, southeast.destination))
        self.assertEqual(self.script.db.itemcoordinates[self.char1], (17, 8))
        self.assertEqual([e for e in self.char1.location.exits if e.key == "south"][0].key, "south")

    def test_climbing_through_a_gate_is_refused(self):
        self.enter((18, 8))
        self.call(commands.CmdClimb(), "s", "Dorthin musst du nicht klettern.")
        self.assertEqual(self.script.db.itemcoordinates[self.char1], (18, 8))

    def test_leave_through_gate(self):
        gate_room = self.place(2, 4)
        self.char1.location = gate_room
        north = [e for e in gate_room.exits if e.key == "north"][0]
        self.assertIsInstance(north, GateExit)
        self.assertEqual(north.get_display_name(self.char1), "Norden (hinaus)")
        self.assertTrue(north.at_traverse(self.char1, north.destination))
        self.assertEqual(self.script.db.itemcoordinates[self.char1], (18, 8))

    def test_single_field_place_depends_on_direction(self):
        self.enter((41, 15))
        east = self.wild_exit("east")
        self.assertFalse(east.at_traverse(self.char1, east.destination))
        self.assertEqual(self.script.db.itemcoordinates[self.char1], (41, 15))
        self.script.move_obj(self.char1, (42, 14))
        north = self.wild_exit("north")
        self.assertTrue(north.at_traverse(self.char1, north.destination))
        self.assertEqual(self.char1.location, self.place(0, 0, "wachturm"))

    def test_nobody_can_be_placed_on_a_gate(self):
        self.call(commands.CmdEnterWild(), "nereid = 18,7", "Das Feld (18, 7) kann man nicht")

    def test_sync_portals_is_repeatable(self):
        before = GateExit.objects.count()
        self.assertEqual(before, 5)
        sync_portals(WORLD_PATH, "nereid")
        self.assertEqual(GateExit.objects.count(), before)

    def test_weather_command_in_places(self):
        self.char1.location = self.place(2, 2)
        expected = self.world.weather_details(self.place(2, 2).get_site(), SUMMER_DAY)["wetter"]
        self.call(commands.CmdWeather(), "", expected)
        self.char1.location = self.place(1, 3)
        self.call(commands.CmdWeather(), "", "Hier merkst du nichts vom Wetter.")
