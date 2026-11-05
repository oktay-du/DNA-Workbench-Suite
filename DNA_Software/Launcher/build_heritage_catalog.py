import network_io

"""Build original German place summaries plus the CLDR German place index."""
from pathlib import Path
import hashlib, json

APP = Path(__file__).parent
TEXT = {
    "DE": (
        "Deutschland",
        "German,Germany,Deutsch,Southern German",
        "Between the North and Baltic coasts, the Middle Mountains and the Alps there are very different cultural landscapes.",
        "Brick Gothic, half-timbered, baroque residences and modernism show different chapters of architectural history, and a single castle does not stand for the whole of Germany.",
    ),
    "AT": (
        "Austria",
        "Austria, Austria",
        "Alpine valleys, lakes and the Danube region connect mountain landscapes with historic cities.",
        "Viennese city palaces, baroque churches and regional wooden buildings show different building traditions.",
    ),
    "CH": (
        "Schweiz",
        "Swiss,Switzerland,Schweizer",
        "The Alps, the Pre-Alpines and the Mediumland characterise the landscape; several language areas are close together.",
        "Old towns with arbor aisles, regional wooden houses and modern architecture form a variety of townscapes.",
    ),
    "CZ": (
        "Tschechien",
        "Czech,Czechia,Bohemian,Tschech",
        "Bohemia and Moravia connect hillside landscapes, river valleys and historic cities.",
        "Gothic, Renaissance and Baroque characterize many city centers; Prague is a well-known but not only example.",
    ),
    "PL": (
        "Polen",
        "Polish,Poland,Polnisch",
        "From the Baltic coast to the Carpathians stretch lake landscapes, plains and mountains.",
        "Brick Gothic, historical marketplaces and regional wooden churches tell of different building and city traditions.",
    ),
    "HU": (
        "Ungarn",
        "Hungarian,Hungary,Ungar",
        "Danube, Balaton and the Great Hungarian Plain form different landscapes.",
        "Budapest urban architecture, thermal baths and rural forms of construction provide various insights into the region.",
    ),
    "SK": (
        "Slowakei",
        "Slovak,Slovakia,Slowak",
        "The Carpathians and river valleys connect mountain landscapes with historical settlements.",
        "Castles, wooden churches and old town squares characterize many places.",
    ),
    "PT": (
        "Portugal",
        "Portuguese,Portugal,Portugies",
        "The Atlantic coast, river valleys and the interior of the country form different cultural landscapes.",
        "Azulejo tiles, historic districts and Manueline architecture offer different design motifs.",
    ),
    "ES": (
        "Spanien",
        "Spanish,Spain,Galician,Galicia,Spanisch",
        "Atlantic, Mediterranean, plateaus and mountains make the Iberian Peninsula scenically diverse.",
        "Romanesque, Gothic, Islamic-influenced architecture and modernism stand for various regional stories.",
    ),
    "TR": (
        "Turkey / Anatolia",
        "Turkey,Turkish,Turkey,Anatolian,Anatolia,Anatolia,Anatolia",
        "Anatolia connects coasts, highlands and mountains between several historical transport and cultural areas.",
        "Byzantine, Armenian, Seljuk and Ottoman architectural monuments make different historical layers visible.",
    ),
    "IR": (
        "Iran",
        "Iranian,Iran,Persian,Persisch",
        "Highlands, mountains and dry basins connect very different landscapes and settlement spaces.",
        "Gardens, courtyards, brick vaults and colored tiles are examples of a diverse architectural history.",
    ),
    "GE": (
        "Georgien",
        "Georgian,Georgia,Kartvelian,Georgien",
        "Between the Black Sea and the Caucasus are wine-growing regions, valleys and high mountain villages.",
        "Swanese fortified towers, historic churches and Tbilisi townhouses show regional building traditions.",
    ),
    "AM": (
        "Armenien",
        "Armenian,Armenia,Armenisch",
        "Highlands, volcanic landscapes and valleys characterize many parts of the country.",
        "Stone churches and monasteries as well as the cross stones, Khachkare, are important parts of the cultural heritage.",
    ),
    "AZ": (
        "Aserbaidschan",
        "Azerbaijani,Azerbaijan,Azeri",
        "Caspian Sea, dry plains and Caucasus mountains form different landscapes.",
        "The old town of Baku and historical caravanserai show different layers of regional building history.",
    ),
    "IQ": (
        "Irak / Mesopotamien",
        "Iraqi,Iraq,Mesopotamian,Mesopotamia,Mesopotamien",
        "Euphrates and Tigris connect historical settlement spaces with plains and marsh landscapes.",
        "Archaeological cities, brick buildings and religious buildings show a long and diverse history.",
    ),
    "GR": (
        "Griechenland",
        "Greek,Greece,Griechisch",
        "Aegean islands, coasts and mountains form very different cultural landscapes.",
        "Ancient temples, Byzantine churches and regional island architecture belong to different eras and places.",
    ),
    "IT": (
        "Italien",
        "Italian,Italy,Italienisch",
        "From the Alps and the Po Valley to the Mediterranean coasts and islands, there is a great variety of landscapes.",
        "Ancient cities, Romanesque churches, Renaissance palaces and modern buildings show different regional histories.",
    ),
    "FR": (
        "France",
        "French, France, French",
        "Atlantic, Mediterranean, river landscapes and mountains connect different regional habitats.",
        "Romanesque and Gothic churches, half-timbered places, castles and modern architecture stand side by side.",
    ),
    "GB": (
        "United Kingdom",
        "British,Britain,United Kingdom,English,Scottish,Welsh",
        "Coasts, hillside landscapes and historic cities characterize the different parts of the country.",
        "Castles, terraced houses, industrial architecture and modern buildings show different regional developments.",
    ),
    "IE": (
        "Irland",
        "Irish,Ireland,Irisch",
        "Atlantic coasts, grasslands and moors characterize many regions of the island.",
        "Monastery complexes, stone round towers and Georgian townhouses offer different historical insights.",
    ),
    "NL": (
        "Netherlands",
        "Dutch,Netherlands, Dutch",
        "Estuaries, coasts and polder landscapes combine hydraulic engineering with settlement history.",
        "Canal houses, brick buildings and modern urban planning are well-known, regionally different design motifs.",
    ),
    "BE": (
        "Belgien",
        "Belgian,Belgium,Belgisch",
        "The North Sea coast, lowlands and Ardennes lie in a densely interconnected European area.",
        "Historic marketplaces, bellies and Art Nouveau buildings show various urban traditions.",
    ),
    "DK": (
        "Denmark",
        "Danish,Denmark,Danish",
        "Islands, peninsulas and coasts characterize the landscape.",
        "Brick churches, coloured townhouses and modern architecture give different insights into the history of construction.",
    ),
    "NO": (
        "Norwegen",
        "Norwegian,Norway,Norwegisch",
        "Fjords, mountains and a long coastline characterize very different settlement areas.",
        "Stab churches, wooden buildings and coastal towns show regional craft and building traditions.",
    ),
    "SE": (
        "Schweden",
        "Swedish,Sweden,Schwedisch",
        "Forests, lakes, archipelagos and northern mountain areas form different landscapes.",
        "Wooden houses, historic city centers and modern architecture show several chapters of architectural history.",
    ),
    "FI": (
        "Finnland",
        "Finnish,Finland,Finnisch",
        "Lakes, forests, coasts and northern landscapes characterize different regions.",
        "Wooden construction, traditional saunas and the architecture of modernity offer different design motifs.",
    ),
    "RO": (
        "Romania",
        "Romanian, Romania, Romanian",
        "The Carpathians, the Danube and the Black Sea coast connect very different cultural landscapes.",
        "Wooden churches, fortified church complexes and historic city centers show regional diversity.",
    ),
    "BG": (
        "Bulgarien",
        "Bulgarian,Bulgaria,Bulgarisch",
        "The Balkan and Rhodopen mountains, plains and Black Sea coasts characterise different regions.",
        "Monastery complexes, historical townhouses and archaeological sites provide insights into different eras.",
    ),
    "HR": (
        "Kroatien",
        "Croatian,Croatia,Kroatisch",
        "Adriatic coast, islands and the interior form different landscapes.",
        "Historic stone towns on the coast and regional buildings inland show various influences.",
    ),
    "RS": (
        "Serbien",
        "Serbian,Serbia,Serbisch",
        "Danube and Save area, plains and mountains connect different settlement areas.",
        "Monasteries, fortresses and historic districts represent different chapters of regional history.",
    ),
    "UA": (
        "Ukraine",
        "Ukrainian,Ukraine,Ukrainisch",
        "River landscapes, steppes and Carpathians characterize different parts of the country.",
        "Wooden churches, historic city centers and monasteries are part of a diverse cultural heritage.",
    ),
    "BY": (
        "Belarus",
        "Belarusian,Belarus,Belarusisch",
        "Plains, forests and river landscapes characterize large parts of the country.",
        "Castle complexes, religious buildings and historical centers show different cultural connections.",
    ),
    "LT": (
        "Litauen",
        "Lithuanian,Lithuania,Litauisch",
        "Baltic coast, dunes, lakes and forests connect different landscapes.",
        "The old town of Vilnius, timber construction and regional sacred architecture offer historical insights.",
    ),
    "LV": (
        "Lettland",
        "Latvian,Latvia,Lettisch",
        "The Baltic coast, rivers and forests characterise different regions.",
        "Riga’s Art Nouveau, historic wooden houses and older town centres show several chapters of the history of construction.",
    ),
    "EE": (
        "Estland",
        "Estonian,Estonia,Estnisch",
        "Islands, coasts and forest landscapes form different habitats.",
        "Tallinn’s old town and regional timber buildings are examples of architectural heritage.",
    ),
    "RU": (
        "Russland",
        "Russian,Russia,Russisch",
        "The large area comprises numerous landscape, language and cultural areas.",
        "Regional wood and stone architecture differs greatly; a single motif cannot summarize this diversity.",
    ),
    "CN": (
        "China",
        "Chinese,China,Chinesisch",
        "Mountains, river basins, coasts and dry landscapes form very different regions.",
        "Historic courthouses, gardens and temples stand alongside numerous regional and modern forms of construction.",
    ),
    "JP": (
        "Japan",
        "Japanese,Japan,Japanisch",
        "Mountain landscapes and coasts characterize the islands and their different settlement areas.",
        "Wooden temples, shrines, gardens and contemporary architecture show different design approaches.",
    ),
    "KR": (
        "South Korea",
        "Korean,Korea,Koreanisch",
        "Mountains, coasts and historical settlements characterize the southern Korean peninsula.",
        "Hanok houses, palace complexes and modern urban architecture show different eras.",
    ),
    "IN": (
        "Indien",
        "Indian,India,Indisch",
        "Himalayas, river plains, highlands and coasts connect numerous regions and cultures.",
        "Temples, mosques, fortresses and regional housing show a variety that does not reflect a single style.",
    ),
    "PK": (
        "Pakistan",
        "Pakistani,Pakistan",
        "Indus Valley, dry highlands and mountains form different landscapes.",
        "Archaeological cities, fortresses and religious buildings show different historical layers.",
    ),
    "EG": (
        "Egypt",
        "Egyptian, Egypt, Egyptian",
        "Nile valley, delta, deserts and coasts characterize different habitats.",
        "Ancient monuments, historic neighbourhoods and recent architecture stand for different eras.",
    ),
    "MA": (
        "Marokko",
        "Moroccan,Morocco,Marokkanisch",
        "Atlantic, Mediterranean, Atlas Mountains and dry landscapes connect different regions.",
        "Medinas, courtyard houses and mud buildings show various regional designs.",
    ),
    "ET": (
        "Ethiopia",
        "Ethiopian, Ethiopia",
        "Highlands and rift landscapes form very different natural spaces.",
        "Rock churches, historical installations and regional residential buildings provide insights into a wide range of building traditions.",
    ),
    "NG": (
        "Nigeria",
        "Nigerian,Nigeria,Nigerianisch",
        "Coasts, rivers and savannahs connect numerous linguistic and cultural areas.",
        "Historical urban complexes and regional construction methods are diverse and cannot be assigned to a single motif.",
    ),
    "KE": (
        "Kenia",
        "Kenyan,Kenya,Kenianisch",
        "The Indian Ocean, the highlands and the rift landscapes form different regions.",
        "Swahili coastal towns and various constructions inland show regional cultural heritage.",
    ),
    "ZA": (
        "South Africa",
        "South African, South Africa, South African",
        "Coasts, highlands and dry areas form different landscapes.",
        "Numerous communities and eras characterize the architectural heritage; no single style stands for the whole country.",
    ),
    "US": (
        "USA",
        "United States,American,USA",
        "Coasts, mountains, plains and deserts connect very different landscapes.",
        "Indigenous building history, immigrant building traditions and modern urban architecture form a diverse heritage.",
    ),
    "CA": (
        "Kanada",
        "Canadian,Canada,Kanadisch",
        "The Atlantic and Pacific coasts, forests, prairies and Arctic regions characterize the large area.",
        "Indigenous building traditions, historical settlements and modern architecture are part of different regional histories.",
    ),
    "MX": (
        "Mexiko",
        "Mexican,Mexico,Mexikanisch",
        "Highlands, coasts and different climates connect numerous regions.",
        "Pre-colonial sites, historic city centers and modern buildings show several historical layers.",
    ),
    "BR": (
        "Brasilien",
        "Brazilian,Brazil,Brasilianisch",
        "Amazonia, coasts and highlands form different landscapes.",
        "Indigenous building traditions, historic cities and modern architecture are part of a diverse cultural heritage.",
    ),
    "PE": (
        "Peru",
        "Peruvian,Peru,Peruanisch",
        "The Pacific coast, the Andes and the Amazon region combine very different habitats.",
        "Pre-colonial sites and historic cities provide insights into different eras and regional histories.",
    ),
    "AR": (
        "Argentinien",
        "Argentinian,Argentina,Argentinisch",
        "Andes, Pampas and Patagonia form different landscapes.",
        "Regional forms of settlement and historical urban architecture show different cultural connections.",
    ),
    "AU": (
        "Australien",
        "Australian,Australia,Australisch",
        "Coasts, dry inland areas and tropical landscapes form different regions.",
        "The cultural history of the Aboriginal Peoples and Torres Strait Islander Peoples is distinct and diverse; recent urban architecture shows further eras.",
    ),
    "NZ": (
        "Neuseeland",
        "New Zealand,Neuseeland",
        "Mountains, coasts and volcanic landscapes characterize the islands.",
        "Māori building and design traditions as well as recent architecture show different stories and perspectives.",
    ),
}


def build():
    source = "https://raw.githubusercontent.com/unicode-org/cldr-json/main/cldr-json/cldr-localenames-full/main/de/territories.json"
    raw = network_io.open_https(source, timeout=30).read()
    territories = json.loads(raw)["main"]["de"]["localeDisplayNames"]["territories"]
    places = []
    for code, name in territories.items():
        if not re_full_country(code):
            continue
        row = TEXT.get(code)
        title, aliases, landscape, architecture = (
            row
            if row
            else (
                name,
                name,
                "Ortsinformationen zu " + name + "will be gradually supplemented.",
                "For this place, no architectural and cultural text has yet been deposited.",
            )
        )
        places.append(
            {
                "id": code.lower(),
                "name": title,
                "aliases": list(dict.fromkeys([name, title] + aliases.split(","))),
                "landscape": landscape,
                "architecture": architecture,
                "curated": bool(row),
                "theme": {"accent": "#127f80", "motif": "courtyard"},
                "sources": [
                    {
                        "title": "UNESCO · World Heritage and Regions",
                        "url": "https://whc.unesco.org/en/statesparties/"
                        + code.lower()
                        + "/",
                    }
                ]
                if row
                else [],
            }
        )
    extras = [
        (
            "de-bw",
            "Baden-Württemberg",
            "Baden-Württemberg, Baden Wurttemberg, Black Forest, Black Forest",
            "The Black Forest, Swabian Alb and Neckartal connect different landscape areas.",
            "Half-timbered workshops, monastery complexes and historical residences show various epochs of southwest German architectural history.",
            "de",
        ),
        (
            "de-by",
            "Bavaria",
            "Bavaria,Bavarian,Bayern,Bayerisch",
            "Alps, lakes, river valleys and middle mountains form very different landscapes.",
            "Baroque churches, historic towns and 19th century castles offer different cultural insights.",
            "de",
        ),
        (
            "tr-ardahan",
            "Ardahan",
            "Ardahan,Ardahan Province",
            "The province in northeastern Turkey is located in a highland region near the Caucasus.",
            "The fortress of Ardahan and historical buildings in the area provide regional insights, and motifs from other provinces are explicitly named.",
            "tr",
        ),
        (
            "caucasus",
            "Caucasus",
            "Caucasian,Caucasus,Kaukasisch,Kaukasus",
            "Between the Black Sea and the Caspian Sea are high mountains, valleys and numerous language and cultural areas.",
            "Defence towers, monasteries, fortresses and historic towns show very different regional building traditions.",
            "ge",
        ),
        (
            "central-europe",
            "Central Europe",
            "Central European,Western European,European,Europa,Europe",
            "River landscapes, low mountains, plains and Alps connect numerous regions.",
            "Gothic, half-timbered, Baroque and modern cross the borders of today's state. The motifs serve the cultural exploration.",
            "de",
        ),
        (
            "eastern-europe",
            "Central and Eastern Europe",
            "Eastern European,Central & Eastern European,Osteuropa",
            "The Baltic coast, river basins, plains and Carpathians connect many different regions.",
            "Wooden churches, historic town squares and regional stone buildings show the cultural diversity of this large space.",
            "pl",
        ),
        (
            "west-asia",
            "Western Asia",
            "Western Asian,Northern West Asian,West Asian,Westasien",
            "Anatolia, Caucasus, Mesopotamia and Iranian highlands comprise different landscapes.",
            "Historic cities, courthouses, churches, mosques and fortresses reflect numerous eras and communities.",
            "tr",
        ),
    ]
    for code, title, aliases, landscape, architecture, parent in extras:
        places.append(
            {
                "id": code,
                "name": title,
                "aliases": aliases.split(","),
                "landscape": landscape,
                "architecture": architecture,
                "curated": True,
                "parent": parent,
                "theme": {
                    "accent": "#8b6548" if parent in ("tr", "ge") else "#326a82",
                    "motif": "towers" if parent == "ge" else "gable",
                },
                "sources": [
                    {
                        "title": "UNESCO · Cultural heritage of the region",
                        "url": "https://whc.unesco.org/en/statesparties/"
                        + parent
                        + "/",
                    }
                ],
            }
        )
    for p in places:
        if p["id"] in ("de", "at", "ch", "cz", "pl"):
            p["theme"] = {"accent": "#315d77", "motif": "gable"}
        elif p["id"] in ("ir", "tr", "iq", "ma"):
            p["theme"] = {"accent": "#976138", "motif": "arch"}
        elif p["id"] in ("ge", "am"):
            p["theme"] = {"accent": "#497165", "motif": "towers"}
        elif p["id"] in ("pt", "es"):
            p["theme"] = {"accent": "#316e9a", "motif": "tiles"}
    result = {
        "version": "2026-11-03.1",
        "places": places,
        "note": "Location and culture information are not DNA findings; a motive does not stand for all people or regions.",
        "territory_source": {
            "url": source,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "license": "Unicode License v3",
            "license_url": "https://www.unicode.org/license.txt",
        },
    }
    (APP / "heritage-places.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        len(places), "places,", sum(p["curated"] for p in places), "original summaries"
    )


def re_full_country(code):
    return (
        len(code) == 2
        and code.isalpha()
        and code.isupper()
        and code not in ("ZZ", "QO", "XA", "XB", "EU", "EZ", "UN")
    )


if __name__ == "__main__":
    build()
