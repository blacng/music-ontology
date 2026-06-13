"""Apply the three structural fixes agreed in the Modeller Dialogue (Artefact 4).

Fix 1 - Genre: gist:Category pattern.
  * :MusicGenre  rdfs:subClassOf gist:Category   (was gist:Concept)
  * :hasGenre    rdfs:subPropertyOf gist:isCategorizedBy  (kept, range :MusicGenre)
  * genre hierarchy: skos:broader  ->  transitive :hasBroaderGenre
  * top-level genres marked with :TopLevelGenre (subClassOf :MusicGenre);
    their skos:broader :MusicGenre and skos:narrower lists are dropped.

Fix 2 - Geography: structured :Place graph with regional roll-up.
  * :originatesFrom  becomes an ObjectProperty, domain gist:Agent, range :Place.
  * :locatedIn (transitive) for org/venue/festival location AND city->country containment.
  * free-text origins rewritten to :City individuals; orgs/venues/festivals use :locatedIn.

Fix 3 - Personal attributes.
  * :hasHeight removed (property def + all instance triples).
  * :hasAge removed; replaced by :bornOn (xsd:date) populated with real birth dates.

Run: uv run python music_ontology/scripts/apply_structural_fixes.py
"""
import re
from pathlib import Path

TTL = Path("music_ontology/music_vocabulary_comprehensive.ttl")

# free-text origin literal -> city IRI
ORIGIN_MAP = {
    "Liverpool, England": ":Liverpool",
    "London, England": ":London",
    "Oxford, England": ":Oxford",
    "Somerset, England": ":Somerset",
    "Seattle, Washington, USA": ":Seattle",
    "Chicago, Illinois, USA": ":Chicago",
    "Long Beach, New York, USA": ":LongBeach_NY",
    "Lawrence, Massachusetts, USA": ":Lawrence_MA",
    "Duluth, Minnesota, USA": ":Duluth",
    "Houston, Texas, USA": ":Houston",
    "Alton, Illinois, USA": ":Alton",
    "West Reading, Pennsylvania, USA": ":WestReading",
    "Gary, Indiana, USA": ":Gary",
    "Aberdeen, Washington, USA": ":Aberdeen_WA",
    "New York City, USA": ":NewYorkCity",
    "Santa Monica, California, USA": ":SantaMonica",
    "Indio, California, USA": ":Indio",
    "Paris, France": ":Paris",
    "Salzburg, Austria": ":Salzburg",
    "Bonn, Germany": ":Bonn",
    "Eisenach, Germany": ":Eisenach",
    "Berlin, Germany": ":Berlin",
    "Nine Mile, Jamaica": ":NineMile",
    "Kingston, Jamaica": ":Kingston",
}
# city IRI -> (label, country IRI)
PLACES = {
    ":Liverpool": ("Liverpool", ":England"),
    ":London": ("London", ":England"),
    ":Oxford": ("Oxford", ":England"),
    ":Somerset": ("Somerset", ":England"),
    ":Seattle": ("Seattle, Washington", ":UnitedStates"),
    ":Chicago": ("Chicago, Illinois", ":UnitedStates"),
    ":LongBeach_NY": ("Long Beach, New York", ":UnitedStates"),
    ":Lawrence_MA": ("Lawrence, Massachusetts", ":UnitedStates"),
    ":Duluth": ("Duluth, Minnesota", ":UnitedStates"),
    ":Houston": ("Houston, Texas", ":UnitedStates"),
    ":Alton": ("Alton, Illinois", ":UnitedStates"),
    ":WestReading": ("West Reading, Pennsylvania", ":UnitedStates"),
    ":Gary": ("Gary, Indiana", ":UnitedStates"),
    ":Aberdeen_WA": ("Aberdeen, Washington", ":UnitedStates"),
    ":NewYorkCity": ("New York City", ":UnitedStates"),
    ":SantaMonica": ("Santa Monica, California", ":UnitedStates"),
    ":Indio": ("Indio, California", ":UnitedStates"),
    ":Paris": ("Paris", ":France"),
    ":Salzburg": ("Salzburg", ":Austria"),
    ":Bonn": ("Bonn", ":Germany"),
    ":Eisenach": ("Eisenach", ":Germany"),
    ":Berlin": ("Berlin", ":Germany"),
    ":NineMile": ("Nine Mile", ":Jamaica"),
    ":Kingston": ("Kingston", ":Jamaica"),
}
COUNTRIES = {
    ":England": "England", ":UnitedStates": "United States", ":France": "France",
    ":Austria": "Austria", ":Germany": "Germany", ":Jamaica": "Jamaica",
}
# subjects that had :hasAge -> real birth date (replaces the time-varying age snapshot)
BORN_MAP = {
    ":PaulMcCartney": "1942-06-18", ":KanyeWest": "1977-06-08",
    ":SadeAdu": "1959-01-16", ":BeyonceKnowles": "1981-09-04",
    ":MilesDavis": "1926-05-26", ":TaylorSwift": "1989-12-13",
}
ORG_TYPES = {":RecordLabel", ":Venue", ":MusicFestival"}

warnings = []


def block_meta(block):
    """Return (subject, set_of_types) for a stanza block, or (None, set())."""
    for line in block.splitlines():
        m = re.match(r"^(:[A-Za-z0-9_]+)\s+a\s+(.+?)\s*[;.]", line)
        if m:
            types = {t.strip() for t in m.group(2).split(",")}
            return m.group(1), types
    return None, set()


def transform_block(block):
    if block.lstrip().startswith("#") or not block.strip():
        return block
    subject, types = block_meta(block)
    if subject in (":hasAge", ":hasHeight"):
        return None  # drop the property definitions entirely

    is_genre_ind = subject != ":MusicGenre" and ":MusicGenre" in types
    top_level = is_genre_ind and any("skos:broader :MusicGenre" in l for l in block.splitlines())
    is_org = bool(types & ORG_TYPES)

    out = []
    for line in block.splitlines():
        s = line.strip()
        indent = line[: len(line) - len(line.lstrip())]

        # --- drops ---
        if "hasHeight" in line:
            continue
        if is_genre_ind and "skos:broader :MusicGenre" in line:
            continue
        if (is_genre_ind or subject == ":MusicGenre") and s.startswith("skos:narrower"):
            continue

        # --- genre re-modelling ---
        if subject == ":MusicGenre" and "rdfs:subClassOf gist:Concept" in line:
            line = line.replace("gist:Concept", "gist:Category")
        if is_genre_ind and "skos:broader :" in line:
            line = line.replace("skos:broader", ":hasBroaderGenre")
        if is_genre_ind and top_level and "a :MusicGenre" in line:
            line = line.replace("a :MusicGenre", "a :TopLevelGenre")

        # --- hasGenre becomes a gist categorization sub-property ---
        if subject == ":hasGenre" and s.startswith("rdfs:domain"):
            out.append(line)
            out.append(indent + "rdfs:subPropertyOf gist:isCategorizedBy ;")
            continue

        # --- originatesFrom property definition: datatype -> object, -> :Place ---
        if subject == ":originatesFrom":
            line = line.replace("owl:DatatypeProperty", "owl:ObjectProperty")
            if "rdfs:domain" in line:
                line = indent + "rdfs:domain gist:Agent ;"
            if "rdfs:range" in line:
                line = indent + "rdfs:range :Place ;"

        # --- instance-level origin literal rewrite ---
        m = re.search(r":originatesFrom\s+\"([^\"]+)\"", line)
        if m and subject != ":originatesFrom":
            city = ORIGIN_MAP.get(m.group(1))
            if city is None:
                warnings.append(f"unmapped origin: {m.group(1)} on {subject}")
            else:
                prop = ":locatedIn" if is_org else ":originatesFrom"
                line = f"{indent}{prop} {city} ;"

        # --- instance-level hasAge -> bornOn ---
        m2 = re.search(r":hasAge\s+\"(\d+)\"\^\^xsd:integer", line)
        if m2 and subject != ":hasAge":
            date = BORN_MAP.get(subject)
            if date is None:
                warnings.append(f"no birth date for {subject}; dropping hasAge")
                continue
            line = f'{indent}:bornOn "{date}"^^xsd:date ;'

        out.append(line)
    return "\n".join(out)


ADDITIONS = """

###############################################################################
# STRUCTURAL-FIX ADDITIONS (Artefact 4 - Modeller Dialogue)
###############################################################################

# --- Genre: gist:Category pattern ---

:TopLevelGenre a owl:Class ;
    rdfs:subClassOf :MusicGenre ;
    rdfs:label "Top-Level Genre"@en ;
    skos:definition "A music genre that is a root of the genre hierarchy (no broader genre)."@en ;
    .

:hasBroaderGenre a owl:ObjectProperty, owl:TransitiveProperty ;
    rdfs:label "has broader genre"@en ;
    rdfs:domain :MusicGenre ;
    rdfs:range :MusicGenre ;
    skos:definition "Relates a subgenre to a broader genre; transitive, so closure reaches all ancestors."@en ;
    .

# --- Geography: structured place graph ---

:Place a owl:Class ;
    rdfs:subClassOf gist:Place ;
    rdfs:label "Place"@en ;
    skos:definition "A geographic location at which an agent originates or an organisation, venue, or event is situated."@en ;
    .

:City a owl:Class ;
    rdfs:subClassOf :Place ;
    rdfs:label "City"@en ;
    skos:definition "A place that is a city or town."@en ;
    .

:Country a owl:Class ;
    rdfs:subClassOf :Place ;
    rdfs:label "Country"@en ;
    skos:definition "A place that is a country or national-level region."@en ;
    .

:locatedIn a owl:ObjectProperty, owl:TransitiveProperty ;
    rdfs:label "located in"@en ;
    rdfs:range :Place ;
    skos:definition "Relates an organisation, venue, event, or place to a containing place; transitive for regional roll-up."@en ;
    .

# --- Time: bornOn replaces the removed hasAge ---

:bornOn a owl:DatatypeProperty ;
    rdfs:label "born on"@en ;
    rdfs:domain gist:Agent ;
    rdfs:range xsd:date ;
    skos:definition "The date on which an agent was born."@en ;
    .
"""


def place_individuals():
    lines = ["\n###############################################################################",
             "# INSTANCES - PLACES",
             "###############################################################################\n"]
    for c_iri, c_label in COUNTRIES.items():
        lines.append(f'{c_iri} a :Country ;\n    rdfs:label "{c_label}"@en ;\n    .\n')
    for city, (label, country) in PLACES.items():
        lines.append(f'{city} a :City ;\n    rdfs:label "{label}"@en ;\n    :locatedIn {country} ;\n    .\n')
    return "\n".join(lines)


def main():
    content = TTL.read_text()
    blocks = re.split(r"\n\s*\n", content)
    new_blocks = [b for b in (transform_block(b) for b in blocks) if b is not None]
    result = "\n\n".join(new_blocks).rstrip() + "\n" + ADDITIONS + place_individuals()
    TTL.write_text(result)
    print(f"transformed -> {TTL}")
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print("  -", w)
    else:
        print("no warnings")


if __name__ == "__main__":
    main()
