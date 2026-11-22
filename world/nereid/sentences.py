"""
Sätze über Wetter und Umwelt in Nereid.

Aufbau siehe `world.wildlands.sentences`. Die Themen und ihre Reihenfolge in
der Beschreibung stehen in `world.wildlands.world.WEATHER_TOPICS`.

Schlüssel für Bedingungen:
    himmel        klar, locker, bedeckt, duester
    niederschlag  kein, niesel, regen, wolkenbruch, schnee, starkschnee
    wind          still, brise, boeig, sturm
    temperatur    frost, kalt, mild, warm, heiss
    nebel         ja, nein
    gewitter      ja, nein
    sicht         frei, verdeckt (z.B. Wald), nebel
    boden         trocken, nass, schnee
    trend         aufzug, abzug, gleich
    tageszeit     nacht, morgen, tag, abend
    jahreszeit    winter, fruehling, sommer, herbst
    biom          grass, forest, beach, swamp, rock, lake
                  in Orten die Art des Raumes: strasse, platz, hof, garten
    band          tief, mittel, hoch, alpin

Platzhalter: {woher} = Richtung, aus der das Wetter kommt.

"""

from world.wildlands.sentences import S

RUHIG = ("still", "brise")
STARK = ("boeig", "sturm")
ORT = ("strasse", "platz", "hof")
HELL = ("morgen", "tag", "abend")

SENTENCES = (
    # ---------------------------------------------------------------- Himmel
    S("himmel", "Der Himmel ist wolkenlos und tiefblau.",
      "Kein Wölkchen steht am Himmel.",
      himmel="klar", tageszeit="tag", sicht="frei"),
    S("himmel", "Der Morgenhimmel ist klar und blass.",
      himmel="klar", tageszeit="morgen", sicht="frei"),
    S("himmel", "Die Abendsonne färbt den klaren Himmel rot und golden.",
      himmel="klar", tageszeit="abend", sicht="frei"),
    S("himmel", "Über dir funkeln unzählige Sterne.",
      "Die Nacht ist klar, die Sterne stehen scharf am Himmel.",
      himmel="klar", tageszeit="nacht", sicht="frei"),
    S("himmel", "Ein paar weiße Wolken ziehen über den Himmel.",
      "Zwischen lockeren Wolken zeigt sich immer wieder die Sonne.",
      himmel="locker", tageszeit="tag", sicht="frei"),
    S("himmel", "Ein paar Wolken ziehen über den dämmrigen Himmel.",
      himmel="locker", tageszeit=("morgen", "abend"), sicht="frei"),
    S("himmel", "Wolkenfetzen ziehen vor den Sternen vorbei.",
      himmel="locker", tageszeit="nacht", sicht="frei"),
    S("himmel", "Eine geschlossene graue Wolkendecke liegt über dem Land.",
      "Der Himmel ist grau verhangen.",
      himmel="bedeckt", tageszeit=HELL, sicht="frei"),
    S("himmel", "Die Nacht ist stockfinster, kein Stern ist zu sehen.",
      himmel=("bedeckt", "duester"), tageszeit="nacht", sicht="frei"),
    S("himmel", "Schwere, dunkle Wolken hängen tief über dem Land.",
      "Der Himmel ist fast schwarz vor Wolken.",
      himmel="duester", tageszeit=HELL, sicht="frei"),
    # unter Bäumen sieht man nur, wie hell es ist
    S("himmel", "Durch das Blätterdach dringt kaum noch Licht.",
      himmel="duester", tageszeit=HELL, sicht="verdeckt"),
    S("himmel", "Sonnenflecken tanzen auf dem Waldboden.",
      himmel=("klar", "locker"), tageszeit="tag", sicht="verdeckt"),
    S("himmel", "Unter den Bäumen ist es so finster, dass du kaum deine Hand siehst.",
      tageszeit="nacht", sicht="verdeckt"),

    # ---------------------------------------------------------- Niederschlag
    # Wind und Niederschlag werden zusammen beschrieben, damit sie sich nicht
    # widersprechen. Der Wind bekommt nur ohne Niederschlag einen eigenen Satz.
    S("niederschlag", "Feiner Nieselregen fällt gleichmäßig.",
      "Ein dünner Regen sprüht dir ins Gesicht.",
      niederschlag="niesel", wind=RUHIG),
    S("niederschlag", "Der Wind treibt dir feine Tropfen ins Gesicht.",
      "Sprühregen jagt in Schleiern über das Land.",
      niederschlag="niesel", wind=STARK),
    S("niederschlag", "Es regnet in dichten, senkrechten Schnüren.",
      "Gleichmäßig rauscht der Regen herab.",
      niederschlag="regen", wind=RUHIG),
    S("niederschlag", "Regenschauer fegen in Schüben heran.",
      niederschlag="regen", wind="boeig"),
    S("niederschlag", "Der Sturm peitscht den Regen fast waagerecht vor sich her.",
      niederschlag="regen", wind="sturm"),
    S("niederschlag", "Ein Wolkenbruch geht nieder. In Augenblicken bist du nass bis auf die Haut.",
      niederschlag="wolkenbruch", wind=RUHIG),
    S("niederschlag", "Regen stürzt in Sturzbächen vom Himmel, vom Wind zu Wänden zusammengetrieben.",
      niederschlag="wolkenbruch", wind=STARK),
    S("niederschlag", "Blitze zucken durch den strömenden Regen, Donner rollt über das Land.",
      niederschlag="wolkenbruch", gewitter="ja", wind=RUHIG),
    S("niederschlag", "Ein Gewitter tobt. Blitz und Donner folgen Schlag auf Schlag, der Sturm reißt"
      " an allem.",
      niederschlag="wolkenbruch", gewitter="ja", wind=STARK),
    S("niederschlag", "Vereinzelte Flocken sinken lautlos herab.",
      "Es schneit leicht.",
      niederschlag="schnee", wind=RUHIG),
    S("niederschlag", "Schnee wirbelt um dich herum.",
      niederschlag="schnee", wind=STARK),
    S("niederschlag", "Dicke Flocken fallen so dicht, dass die Welt dahinter verschwimmt.",
      niederschlag="starkschnee", wind=RUHIG),
    S("niederschlag", "Im Schneetreiben siehst du kaum die Hand vor Augen.",
      niederschlag="starkschnee", wind=STARK),
    # Wald
    S("niederschlag", "Es tropft unablässig aus dem Blätterdach.",
      niederschlag=("niesel", "regen"), wind=RUHIG, biom="forest"),
    S("niederschlag", "Der Regen prasselt auf die Kronen, und in dicken Tropfen fällt er weiter"
      " bis zu dir.",
      niederschlag=("regen", "wolkenbruch"), wind=STARK, biom="forest"),
    S("niederschlag", "Schnee rieselt durch die Äste herab.",
      niederschlag=("schnee", "starkschnee"), wind=RUHIG, biom="forest"),
    # See
    S("niederschlag", "Regentropfen zerplatzen rings um dich auf dem Wasser.",
      niederschlag=("niesel", "regen"), wind=RUHIG, biom="lake"),
    # Fels
    S("niederschlag", "Regen rinnt in kleinen Bächen den Fels hinab und macht jeden Griff glatt.",
      niederschlag=("regen", "wolkenbruch"), wind=RUHIG, biom="rock"),

    # Orte
    S("niederschlag", "Regen rinnt von den Dächern und sammelt sich in der Gosse.",
      "Der Regen trommelt auf Dächer und Pflaster.",
      niederschlag=("regen", "wolkenbruch"), wind=RUHIG, biom=ORT),
    S("niederschlag", "Der Wind treibt den Regen in Böen durch die Gassen.",
      niederschlag=("regen", "wolkenbruch"), wind=STARK, biom=ORT),
    S("niederschlag", "Schnee fällt auf Dächer und Pflaster und dämpft jeden Laut.",
      niederschlag=("schnee", "starkschnee"), wind=RUHIG, biom=ORT),

    # ------------------------------------------------------------------ Wind
    S("wind", "Ein leichter Luftzug weht durch die Gassen.",
      "",
      niederschlag="kein", wind="brise", biom=ORT),
    S("wind", "Der Wind pfeift um die Hausecken und lässt die Fensterläden klappern.",
      niederschlag="kein", wind=STARK, biom=ORT),
    S("wind", "Der Wind fährt durch die Beete und biegt die Stauden.",
      niederschlag="kein", wind=("brise", "boeig", "sturm"), biom="garten"),
    S("wind", "Ein leichter Wind streicht über das Land.",
      "",
      niederschlag="kein", wind="brise"),
    S("wind", "Böen zerren an deiner Kleidung.",
      "Der Wind frischt immer wieder kräftig auf.",
      niederschlag="kein", wind="boeig"),
    S("wind", "Ein Sturm fegt über das Land. Du musst dich gegen den Wind stemmen.",
      niederschlag="kein", wind="sturm"),
    S("wind", "Wellen laufen durch das hohe Gras.",
      niederschlag="kein", wind=("brise", "boeig"), biom="grass", boden=("trocken", "nass")),
    S("wind", "Die Baumkronen rauschen und ächzen im Wind.",
      niederschlag="kein", wind=("boeig", "sturm"), biom="forest"),
    S("wind", "Der Wind treibt dir feinen Sand in die Augen.",
      niederschlag="kein", wind=("boeig", "sturm"), biom="beach"),
    S("wind", "Der Wind pfeift ungebremst über den Fels und zerrt an dir.",
      niederschlag="kein", wind=("boeig", "sturm"), biom="rock"),
    S("wind", "Der Wind wühlt das Wasser auf. Wellen schlagen dir über den Kopf.",
      niederschlag="kein", wind=("boeig", "sturm"), biom="lake"),

    # ------------------------------------------------------------ Temperatur
    S("temperatur", "Es ist bitterkalt. Dein Atem steht als Wolke in der Luft.",
      "Der Frost beißt in Gesicht und Finger.",
      temperatur="frost"),
    S("temperatur", "Die Nachtluft ist empfindlich kühl.",
      temperatur="kalt", tageszeit="nacht"),
    S("temperatur", "Die Luft ist angenehm warm.",
      temperatur="warm", tageszeit=("tag", "abend"), niederschlag="kein"),
    S("temperatur", "Die Hitze ist drückend. Die Luft flimmert.",
      temperatur="heiss"),
    S("temperatur", "Das Wasser ist eisig. Lange hältst du es hier nicht aus.",
      temperatur=("frost", "kalt"), biom="lake"),

    # ----------------------------------------------------------------- Boden
    # nur wenn gerade nichts fällt: erinnert an das Wetter der letzten Stunden
    S("boden", "Der Boden ist noch nass vom Regen.",
      boden="nass", niederschlag="kein"),
    S("boden", "Das Gras ist nass und schwer vom Regen.",
      "In den Senken stehen noch Pfützen.",
      boden="nass", niederschlag="kein", biom="grass"),
    S("boden", "Von den Blättern fallen noch einzelne Tropfen.",
      boden="nass", niederschlag="kein", biom="forest"),
    S("boden", "Der Sand ist dunkel und fest vom Regen.",
      boden="nass", niederschlag="kein", biom="beach"),
    S("boden", "Eine Schneedecke liegt über allem.",
      "Schnee knirscht unter deinen Schritten.",
      boden="schnee", niederschlag="kein"),
    S("boden", "Die Äste biegen sich unter der Schneelast.",
      boden="schnee", niederschlag="kein", biom="forest"),

    S("boden", "Das Pflaster glänzt nass.",
      "In den Fugen des Pflasters steht noch das Wasser.",
      boden="nass", niederschlag="kein", biom=ORT),
    S("boden", "Schnee liegt auf Dächern und Simsen, auf dem Pflaster ist er zu Matsch"
      " getreten.",
      boden="schnee", niederschlag="kein", biom=ORT),
    S("boden", "Die Erde in den Beeten ist dunkel und feucht.",
      boden="nass", niederschlag="kein", biom="garten"),

    # ----------------------------------------------------------------- Trend
    S("trend", "Im {woher} türmt sich eine dunkle Wolkenwand auf.",
      "Vom {woher} her schiebt sich eine graue Front heran.",
      trend="aufzug", sicht="frei", tageszeit=HELL),
    S("trend", "Im {woher} wird der Himmel bereits heller.",
      trend="abzug", sicht="frei", tageszeit=HELL),

    # ----------------------------------------------------------------- Nebel
    # ersetzt die Sätze über die Nachbarfelder
    S("nebel", "Dichter Nebel verschluckt alles, was weiter als ein paar Schritte entfernt ist.",
      "Nebelschwaden ziehen um dich. Die Ferne ist nur noch graues Nichts.",
      nebel="ja"),
    S("nebel", "Nebel liegt über dem Moor. Jeder Schritt führt ins Ungewisse.",
      nebel="ja", biom="swamp"),
    S("nebel", "Nebel liegt auf dem Wasser. Du weißt kaum noch, wo das Ufer ist.",
      nebel="ja", biom="lake"),

    # --------------------------------------------- Meldungen bei Wetterwechsel
    # "von" und "zu" sind der alte und der neue Wert.
    S("wechsel", "Es beginnt zu nieseln.", von="kein", zu="niesel"),
    S("wechsel", "Es beginnt zu regnen.", von="kein", zu="regen"),
    S("wechsel", "Schlagartig setzt heftiger Regen ein.", von="kein", zu="wolkenbruch"),
    S("wechsel", "Der Regen wird stärker.", von="niesel", zu=("regen", "wolkenbruch")),
    S("wechsel", "Der Regen schwillt zu einem Wolkenbruch an.", von="regen", zu="wolkenbruch"),
    S("wechsel", "Der Regen lässt nach.", von=("regen", "wolkenbruch"), zu="niesel"),
    S("wechsel", "Der Wolkenbruch geht in gleichmäßigen Regen über.", von="wolkenbruch", zu="regen"),
    S("wechsel", "Der Regen hört auf.", von=("niesel", "regen", "wolkenbruch"), zu="kein"),
    S("wechsel", "Es beginnt zu schneien.", von="kein", zu=("schnee", "starkschnee")),
    S("wechsel", "Der Schneefall wird dichter.", von="schnee", zu="starkschnee"),
    S("wechsel", "Der Schneefall lässt nach.", von="starkschnee", zu="schnee"),
    S("wechsel", "Es hört auf zu schneien.", von=("schnee", "starkschnee"), zu="kein"),
    S("wechsel", "Der Regen geht in Schnee über.",
      von=("niesel", "regen", "wolkenbruch"), zu=("schnee", "starkschnee")),
    S("wechsel", "Der Schnee geht in Regen über.",
      von=("schnee", "starkschnee"), zu=("niesel", "regen", "wolkenbruch")),
    S("wechsel_wind", "Der Wind schwillt zum Sturm an.", zu="sturm"),
    S("wechsel_wind", "Der Sturm flaut ab.", von="sturm"),
    S("wechsel_nebel", "Nebel zieht auf.", zu="ja"),
    S("wechsel_nebel", "Der Nebel lichtet sich.", zu="nein"),
)
