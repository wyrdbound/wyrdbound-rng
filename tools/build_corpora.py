#!/usr/bin/env python3
"""
Build ancestry name corpora for wyrdbound-rng.

Method
------

Names are not transcribed from anyone's compiled list. They are built from the
*name-element stock* of each source tradition -- the documented inventory of
prototheme and deutrotheme morphemes that the tradition actually combined --
plus a seed of independently attested monothematic names.

This matters for three reasons:

1. Legal. Individual names are uncopyrightable facts; a curated list can carry
   thin compilation copyright. Composing from morpheme stock reproduces no
   one's selection or arrangement.

2. Authenticity. Germanic, Norse, Old English and Welsh naming were genuinely
   productive systems. A name built from attested elements by the tradition's
   own rules is the same kind of object as a name that happens to be recorded.

3. Generator quality. Composed names reuse syllables by construction, which is
   exactly what raises bigram coverage. The measured failure mode of the
   existing `generic-fantasy` corpus is 685 unique syllables across 679 names --
   one new syllable per name, nothing to learn from. Element stock cannot fail
   that way.

Orthography is ASCII-normalised throughout (Thor- not Þór-, -grimr not -grímr).
The segmenter is built for Latin-alphabet fantasy names and the game renders in
a terminal; diacritics buy nothing here and cost both.

Usage:
    python build_corpora.py <output-dir>
"""

from __future__ import annotations

import sys
import unicodedata
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set

# ---------------------------------------------------------------------------
# Seam repair
#
# Real dithematic compounding does not just concatenate. Norse Sig- + -gerdr
# gives Sigridr, not Siggerdr; Old English Ead- + -dweard gives Eadweard. These
# rules approximate the assimilations the traditions actually applied, so the
# composed names do not read as machine output.
# ---------------------------------------------------------------------------

def join(first: str, second: str) -> str:
    """Join two name elements, repairing the seam the way the tradition would."""
    if not first or not second:
        return first + second

    a, b = first[-1].lower(), second[0].lower()

    # Degeminate at the seam: Sig + gerdr -> Sigerdr, not Siggerdr.
    if a == b and a not in "aeiouy":
        second = second[1:]
    # Vowel + vowel across the seam elides the first: Ida + arr -> Idarr.
    elif a in "aeiou" and b in "aeiou":
        first = first[:-1]

    out = first + second

    # No tradition here tolerates a triple letter.
    for ch in set(out.lower()):
        out = out.replace(ch * 3, ch * 2)

    return out[0].upper() + out[1:]


def compose(
    firsts: Sequence[str], seconds: Sequence[str], min_first: int = 2
) -> List[str]:
    """Every prototheme x deuterotheme combination, seam-repaired.

    `min_first` guards against stems too short to carry a suffix: 'Ad' + 'by'
    gives 'Adby', which is a syllable and a shrug rather than a name.
    """
    out = []
    for f in firsts:
        if len(f) < min_first:
            continue
        for s in seconds:
            # A tradition does not compound an element with itself: Hild + hild
            # is not a name, it is a stutter.
            if f.lower()[:3] == s.lower()[:3]:
                continue
            out.append(join(f, s))
    return out


def ascii_fold(text: str) -> str:
    """Strip diacritics; map the Norse/OE letters the fold does not handle."""
    replacements = {
        "þ": "th", "Þ": "Th", "ð": "d", "Ð": "D",
        "æ": "ae", "Æ": "Ae", "ø": "o", "Ø": "O",
        "ö": "o", "Ö": "O", "å": "a", "Å": "A",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

# Names strongly identified with a single modern author's work. All of these
# are old enough to be public domain -- most of the dwarf names are straight out
# of the 13th-century Dvergatal -- but a player who meets "Thorin" in a dungeon
# is not thinking about the Poetic Edda. Excluded for recognisability, not law.
RECOGNISABLE: Set[str] = {
    # Dvergatal names Tolkien used for the Company and their kin
    "thorin", "fili", "kili", "dwalin", "gloin", "oin", "ori", "nori", "dori",
    "bifur", "bofur", "bombur", "durin", "gandalf", "balin", "thrain", "thror",
    "dain", "nain", "gimli", "thranduil",
    # Hobbits
    "frodo", "bilbo", "samwise", "meriadoc", "peregrin", "hamfast", "lobelia",
    "drogo", "bungo", "took", "baggins", "brandybuck", "proudfoot", "gamgee",
    "rosie", "otho", "lotho", "fredegar",
    # Other high-recognition fantasy
    "aragorn", "arwen", "legolas", "galadriel", "elrond", "celeborn", "eowyn",
    "eomer", "theoden", "boromir", "faramir", "denethor", "isildur", "gollum",
    "saruman", "radagast", "beren", "luthien", "turin", "feanor", "fingolfin",
    "drizzt", "bruenor", "tanis", "raistlin", "caramon", "tasslehoff",
    "elminster", "conan", "geralt", "ciri", "yennefer", "triss",
}

# Composed forms that are phonotactically legal but read badly in play.
def is_wellformed(name: str, min_len: int = 3, max_len: int = 12) -> bool:
    if not (min_len <= len(name) <= max_len):
        return False
    low = name.lower()
    if low in RECOGNISABLE:
        return False
    if not low.isalpha():
        return False
    # Needs a vowel in every 4-character window, or it is unpronounceable.
    for i in range(0, max(1, len(low) - 3)):
        if not any(c in "aeiouy" for c in low[i:i + 4]):
            return False
    # No four-consonant runs.
    run = 0
    for c in low:
        run = run + 1 if c not in "aeiouy" else 0
        if run >= 4:
            return False
    return True


def finalise(names: Iterable[str], min_len: int = 3, max_len: int = 12) -> List[str]:
    """Fold, filter, dedupe case-insensitively, sort."""
    seen: Dict[str, str] = {}
    for raw in names:
        name = ascii_fold(raw).strip()
        if not name:
            continue
        name = name[0].upper() + name[1:]
        if not is_wellformed(name, min_len, max_len):
            continue
        seen.setdefault(name.lower(), name)
    return sorted(seen.values())


def trim(names: Sequence[str], target: int, keep: Sequence[str] = ()) -> List[str]:
    """Thin a list to roughly `target`, keeping everything in `keep`.

    Attested names are kept unconditionally; the composed forms around them are
    strided so the survivors stay spread across the alphabet rather than
    stopping at G. Deterministic, so rebuilding gives the same corpus.
    """
    protected = {n.lower() for n in keep}
    kept = [n for n in names if n.lower() in protected]
    rest = [n for n in names if n.lower() not in protected]

    room = max(0, target - len(kept))
    if room and len(rest) > room:
        stride = len(rest) / room
        rest = [rest[int(i * stride)] for i in range(room)]

    return sorted(dict.fromkeys(kept + rest))


# ===========================================================================
# DWARF -- Old Norse / Old Icelandic
#
# The Norse dithematic system, which is also the historical source of the
# fantasy dwarf register: the Dvergatal in Voluspa is where the whole naming
# convention comes from. Hard onsets, heavy codas, -r and -nn masculine
# terminations.
# ===========================================================================

ON_FIRST = [
    "Ala", "Alf", "Am", "An", "Ar", "Arn", "As", "Aud", "Bald", "Berg",
    "Bjarn", "Bod", "Bot", "Brand", "Bryn", "Dag", "Eil", "Eir", "Ey", "Finn",
    "Folk", "Frey", "Frid", "Gauk", "Gaut", "Geir", "Gest", "Gis", "Gnup",
    "Grim", "Gud", "Gunn", "Haf", "Hak", "Hall", "Ham", "Har", "Hedin", "Helg",
    "Her", "Hild", "Hjal", "Hjor", "Hlod", "Holm", "Hrafn", "Hroar", "Hrod",
    "Hun", "Ing", "Isl", "Jar", "Jor", "Kar", "Ketil", "Kjal", "Kol", "Leif",
    "Lid", "Ljot", "Mag", "Mar", "Mod", "Munn", "Njal", "Odd", "Of", "Ol",
    "Orm", "Os", "Ottar", "Rad", "Ragn", "Rand", "Ref", "Reyn", "Rik", "Run",
    "Sae", "Sig", "Skarp", "Snae", "Sol", "Stein", "Styr", "Sum", "Svan",
    "Svein", "Thjod", "Thor", "Thrand", "Torf", "Ulf", "Un", "Val", "Ve",
    "Vig", "Yng",
]

ON_MALE_SECOND = [
    "arr", "bjorn", "bodi", "brandr", "dan", "fastr", "finnr", "fridr",
    "gardr", "gautr", "geirr", "gestr", "gils", "grimr", "hallr", "kell",
    "laugr", "leifr", "ljotr", "modr", "mundr", "nefr", "ormr", "rekr",
    "rikr", "steinn", "thorr", "ulfr", "valdr", "vardr", "vidr", "vindr",
]

ON_FEMALE_SECOND = [
    "a", "bjorg", "borg", "dis", "finna", "fridr", "gerdr", "gunn", "gyda",
    "heidr", "hildr", "katla", "laug", "leif", "lin", "ljot", "ny", "run",
    "unn", "veig", "vor", "thrudr",
]

# Monothematic Norse names and Dvergatal dwarf-names, attested in the Poetic
# Edda and the Icelandic sagas. Public domain by nine centuries.
ON_MALE_SIMPLE = [
    "Alfr", "Ali", "Ani", "Api", "Ari", "Atli", "Baugr", "Beli", "Bersi",
    "Bildr", "Blesi", "Bodvar", "Bolli", "Bragi", "Broddi", "Bruni", "Brusi",
    "Bui", "Bundi", "Dagr", "Dolgr", "Draupnir", "Dufr", "Eldr", "Eyvindr",
    "Fjalarr", "Flosi", "Frar", "Frosti", "Galti", "Gardi", "Gaukr", "Geiti",
    "Gellir", "Ginnarr", "Gisli", "Glamr", "Grani", "Grettir", "Gripr", "Hagi",
    "Haki", "Hamr", "Haugspori", "Haukr", "Hepti", "Hlevangr", "Hnefi",
    "Hornbori", "Hoskuldr", "Hradi", "Hrappr", "Hringr", "Hrokr", "Hrutr",
    "Illugi", "Iri", "Jari", "Kalfr", "Kari", "Klakkr", "Kleppr", "Krakr",
    "Leistr", "Litr", "Loni", "Lopt", "Mani", "Mjodvitnir", "Modsognir",
    "Mugi", "Nafni", "Nali", "Nar", "Nessi", "Nipingr", "Nokkvi", "Nyr",
    "Radsvidr", "Reginn", "Refr", "Saxi", "Sindri", "Skafidr", "Skeggi",
    "Skirfir", "Skorri", "Skuti", "Snorri", "Soti", "Stari", "Starri", "Surtr",
    "Svadi", "Svanr", "Svartr", "Sviurr", "Teitr", "Tindr", "Tjorvi", "Toki",
    "Tumi", "Veggr", "Virfir", "Vitr", "Yngvi",
]

ON_FEMALE_SIMPLE = [
    "Aesa", "Alof", "Asa", "Asta", "Bera", "Besja", "Bjorg", "Dalla", "Disa",
    "Driva", "Dota", "Edla", "Eyfura", "Freyja", "Frida", "Geira", "Gerd",
    "Goda", "Grima", "Groa", "Gyda", "Halla", "Hedda", "Helga", "Hervor",
    "Hlif", "Hrefna", "Inga", "Jodis", "Jorunn", "Kadlin", "Katla", "Kraka",
    "Liot", "Luta", "Nanna", "Osk", "Ota", "Ragna", "Rannveig", "Runa", "Saeunn",
    "Sigga", "Signy", "Sinna", "Skadi", "Svala", "Thora", "Thyra", "Tola",
    "Una", "Unn", "Vigdis", "Yrsa",
]

# ===========================================================================
# ELF -- Welsh / Brythonic
#
# The register fantasy has used for elves since Tolkien built Sindarin on Welsh
# phonology. Liquid consonants, vowel-heavy, soft mutation. Kept readable:
# no "ll"/"dd" clusters that an English-reading player will stumble over.
# ===========================================================================

WELSH_FIRST = [
    "Aer", "Alun", "Ang", "Arian", "Arth", "Bed", "Bel", "Ber", "Bran", "Bryn",
    "Cad", "Cael", "Car", "Ced", "Cel", "Cer", "Cled", "Cyn", "Dan", "Der",
    "Dyf", "Dyl", "Eil", "Eir", "El", "Elf", "Em", "Eur", "Gar", "Ger", "Gla",
    "Gwal", "Gwen", "Gwyd", "Gwyn", "Hael", "Heil", "Hel", "Hyw", "Idr", "Ith",
    "Llyr", "Mab", "Mad", "Mael", "Mer", "Mor", "Myr", "Ner", "Nia", "Ol",
    "Pen", "Rhi", "Rhon", "Rhyd", "Sel", "Sion", "Sul", "Tal", "Tan", "Teg",
    "Tir", "Tud", "Vae", "Ynyr",
]

WELSH_MALE_SECOND = [
    "an", "ael", "afon", "ain", "arth", "awg", "edd", "en", "fael", "for",
    "gan", "iel", "in", "ion", "is", "lyn", "og", "on", "ryn", "wal", "wyn",
    "yn", "ys", "wyth", "gar", "wen", "ael", "ydd", "erth", "wg", "ael",
    "iaw", "ant", "el", "or",
]

WELSH_FEMALE_SECOND = [
    "a", "aeth", "an", "el", "en", "eth", "ia", "ien", "is", "lys", "nen",
    "wen", "wy", "wyn", "ys", "wedd", "ryd", "ora", "ana", "eli", "ith",
    "erys", "ona", "yl", "wena",
]

WELSH_MALE_SIMPLE = [
    "Aeron", "Alun", "Amlyn", "Aneirin", "Arawn", "Berwyn", "Bleddyn", "Bryn",
    "Cadfael", "Cadog", "Caradog", "Carwyn", "Cefin", "Cledwyn", "Conwy",
    "Cynan", "Dafyd", "Deiniol", "Derwyn", "Dewi", "Dyfan", "Dyfed", "Eifion",
    "Einion", "Elfed", "Elis", "Emlyn", "Emrys", "Eurig", "Gafran", "Geraint",
    "Gethin", "Glyn", "Gruffud", "Gwilym", "Gwydion", "Heilyn", "Hywel",
    "Iestyn", "Ifor", "Illtyd", "Ioan", "Iorwerth", "Islwyn", "Ithel", "Kynon",
    "Llewelyn", "Lloyd", "Macsen", "Madog", "Maelgwn", "Meilyr", "Meirion",
    "Meredyd", "Morgan", "Myrdin", "Neirin", "Owain", "Padarn", "Pedran",
    "Penllyn", "Rhisiart", "Rhydian", "Rhys", "Sulien", "Taliesin", "Tegid",
    "Trahaearn", "Tudur", "Urien", "Wynfor",
]

WELSH_FEMALE_SIMPLE = [
    "Aerona", "Angharad", "Anwen", "Arianwen", "Arwen", "Blodwen", "Braith",
    "Branwen", "Bronwen", "Caron", "Carys", "Catrin", "Ceinwen", "Ceri",
    "Ceridwen", "Cerys", "Creirwy", "Dilys", "Dwynwen", "Efa", "Eira",
    "Eiriona", "Eleri", "Elin", "Eluned", "Enid", "Esyllt", "Ffion", "Gaenor",
    "Generys", "Glenys", "Glynis", "Gwenda", "Gwenllian", "Gwyneth", "Haf",
    "Heledd", "Heulwen", "Hywela", "Ianto", "Iola", "Lowri", "Luned", "Mabli",
    "Meinir", "Meinwen", "Meredith", "Morwen", "Myfanwy", "Nerys", "Nesta",
    "Olwen", "Rhiannon", "Rhonwen", "Rhosyn", "Sian", "Sioned", "Tegan",
    "Tegwen", "Tesni", "Tirion", "Wenna",
]

# ===========================================================================
# HALFLING -- medieval English hypocoristics
#
# Not Old English royal dithematics: Aethelred is a king's name, not a
# halfling's. This is the homely register -- the pet-forms and diminutives
# recorded in the poll tax rolls and manor court books: Hob, Wat, Gib, Tibb,
# plus the productive suffixes -kin, -cock, -ot, -et, -y that made hundreds
# more. Small, warm, and morphologically dense, which suits both the ancestry
# and the generator.
# ===========================================================================

EN_MALE_STEM = [
    "Bart", "Bat", "Brock", "Colle", "Cuth", "Dav", "Dick", "Dob", "Dunn",
    "Ellis", "Ev", "Garn", "Gib", "Gil", "God", "Hal", "Hank", "Hick", "Hob",
    "Hodge", "Holl", "Hugh", "Jack", "Jan", "Jeff", "Jud", "Kester", "Lamb",
    "Lark", "Lott", "Mart", "Merr", "Milb", "Nob", "Nick", "Orr", "Pad",
    "Per", "Phil", "Pip", "Quill", "Rand", "Rob", "Row", "Rud", "Sim", "Som",
    "Tam", "Tarr", "Tib", "Toll", "Tom", "Wad", "Wick", "Wil", "Wyn",
]

# -cock and -son are surname-forming (Adcock, Hancock, Wilson are attested, but
# as bynames rather than given names). Excluded: this list is given names.
EN_MALE_SUFFIX = [
    "kin", "et", "ot", "in", "ett", "kyn", "on", "by", "ry", "well", "ard",
    "ley", "ow", "as", "ken", "lin", "man", "wick", "ric", "bald", "stan",
]

EN_MALE_SIMPLE = [
    "Alfric", "Anselm", "Barnaby", "Bartle", "Bennet", "Bevis", "Brockle",
    "Bryde", "Cuddy", "Dickon", "Dobbin", "Dunstan", "Elric", "Everard",
    "Garnock", "Gilbie", "Godric", "Goodwin", "Grimbald", "Hamo", "Harding",
    "Hodgkin", "Hollis", "Jankin", "Jenkin", "Jocelin", "Kester", "Lambkin",
    "Merrick", "Milbry", "Nobbs", "Orrick", "Osbert", "Perkin", "Pipkin",
    "Quill", "Rankin", "Robin", "Rowley", "Simkin", "Somer", "Tamkin",
    "Tarry", "Thurstan", "Tibbot", "Tolman", "Wadlow", "Warin", "Wickam",
    "Wilkin", "Wyman",
]

EN_FEMALE_STEM = [
    "Ally", "Amm", "Ann", "Ave", "Bess", "Bett", "Cis", "Clem", "Dow", "Edd",
    "Ellice", "Em", "Fill", "Gill", "God", "Good", "Hawis", "Hild", "Ibb",
    "Idon", "Isod", "Joan", "Juli", "Lett", "Lev", "Mab", "Mald", "Mall",
    "Marge", "Marg", "Matt", "Meg", "Mill", "Nell", "Nest", "Parn", "Pern",
    "Petr", "Rose", "Sib", "Syb", "Tiff", "Till", "Wenn", "Wilm", "Wym",
]

EN_FEMALE_SUFFIX = [
    "ot", "et", "ie", "y", "kin", "ota", "ina", "elle", "en", "a", "ota",
    "isa", "ild", "ice", "ella", "ota",
]

EN_FEMALE_SIMPLE = [
    "Alison", "Ameline", "Avice", "Avelina", "Bettris", "Clemence", "Cissot",
    "Custance", "Dowsabel", "Dyot", "Edusa", "Emmot", "Ellice", "Fillida",
    "Gillot", "Godelot", "Goodith", "Hawise", "Hilda", "Ibbot", "Idony",
    "Isolda", "Jonet", "Juliana", "Lettice", "Levina", "Mabel", "Maldie",
    "Malkin", "Marion", "Marget", "Mawde", "Milly", "Nesta", "Parnell",
    "Pernel", "Petronel", "Rosamund", "Sibbie", "Sibyl", "Tiffany", "Tillot",
    "Wenna", "Wilmot", "Wymark",
]

# ===========================================================================
# HUMAN -- Frankish / Norman, the dithematic stock of medieval Western Europe
#
# The largest real stock of the five, and the one a player reads as simply
# "person". Germanic two-element compounds as they were actually used across
# the Frankish and Norman world, with the Latin-Christian layer alongside.
# ===========================================================================

FR_FIRST = [
    "Adal", "Aim", "Alb", "Ald", "Arn", "Baud", "Bern", "Bert", "Burg", "Con",
    "Drog", "Eber", "Engel", "Ev", "Ferr", "Folc", "Frid", "Gar", "Gaut",
    "Ger", "Gis", "God", "Guil", "Gun", "Hard", "Hart", "Heim", "Hild", "Hug",
    "Isen", "Lam", "Land", "Leod", "Lud", "Man", "Meg", "Nord", "Od", "Ort",
    "Rain", "Ram", "Rand", "Reg", "Rich", "Rod", "Rol", "Sig", "Theo", "Wal",
    "War", "Werin", "Wid", "Wil", "Wolf",
]

FR_MALE_SECOND = [
    "ard", "bald", "bert", "brand", "fred", "gar", "ger", "hard", "helm",
    "mar", "mund", "olf", "rand", "ric", "ulf", "ward", "win", "old", "aud",
    "bod", "frid", "her", "lac", "leif", "man", "mer", "nand", "rad", "vald",
    "wig", "bern", "gis", "lin",
]

FR_FEMALE_SECOND = [
    "a", "burg", "gard", "gund", "hild", "linde", "sinde", "trude", "wara",
    "wise", "ia", "elle", "ette", "berta", "flede", "mund", "rada", "swinth",
    "wina", "eve", "sende", "isa", "iane", "olde",
]

FR_MALE_SIMPLE = [
    "Alard", "Alberic", "Amaury", "Ancel", "Anselm", "Arnaud", "Aubrey",
    "Baldric", "Bardolf", "Bartel", "Baudoin", "Benet", "Bertrand", "Blaise",
    "Bohemond", "Bricius", "Cathal", "Clovis", "Conrad", "Corbin", "Dreux",
    "Eudes", "Eustace", "Fulk", "Galeran", "Garnier", "Gaultier", "Gervais",
    "Gilles", "Girard", "Gosselin", "Guarin", "Guyon", "Hamelin", "Herluin",
    "Hervey", "Ivo", "Jocelyn", "Lambert", "Lanfranc", "Leufroy", "Mainard",
    "Manfred", "Marcel", "Milo", "Norman", "Otho", "Pagan", "Payen", "Percival",
    "Ranulf", "Raoul", "Regnier", "Renaud", "Rolant", "Sanson", "Serlo",
    "Tancred", "Thibaut", "Turstin", "Ulric", "Valeran", "Vivien", "Warner",
    "Wymund",
]

FR_FEMALE_SIMPLE = [
    "Adela", "Adelisa", "Agatha", "Aline", "Alix", "Amice", "Amiria", "Anseline",
    "Arletta", "Aveline", "Basilia", "Beatrix", "Berthe", "Blanche", "Bela",
    "Cecily", "Clarisse", "Clemence", "Constance", "Denise", "Editha", "Douce",
    "Eleanor", "Elise", "Emeline", "Ermengarde", "Ermentrude", "Eustacia",
    "Felice", "Gisele", "Guenievre", "Hadwisa", "Hersende", "Hodierna",
    "Isabeau", "Ismena", "Jehanne", "Joceline", "Juette", "Laurette",
    "Lucienne", "Mahaut", "Margery", "Mathilde", "Melisende", "Muriel",
    "Nicola", "Oriel", "Perrette", "Rohese", "Sibylla", "Sybille", "Tiphaine",
    "Yolande", "Ysabel",
]

# ===========================================================================
# GOBLIN -- constructed
#
# The one ancestry with no real-world onomastic tradition to draw on, so this
# list is original content rather than sourced content, built from an explicit
# phonotactic rule set:
#
#   - one or two syllables, rarely three
#   - closed syllables preferred; codas are stops, sibilants or clusters
#   - harsh onset clusters: gr kr skr sn sk shr thr zr vr dr
#   - back and high vowels (a i u o); mid front /e/ is rare, which is what
#     keeps the register from drifting toward the human and halfling lists
#   - masculine forms end in a consonant; feminine forms end in -a -i -ka -za
#
# The rules are the deliverable as much as the names are: they are what lets
# the list be regenerated or extended consistently later.
# ===========================================================================

# Goblin is built from a small fixed SYLLABLE inventory rather than from free
# onset x vowel x coda combination. The first attempt did the latter, and the
# corpus tool caught the result immediately: 645 distinct syllables across 700
# names -- the exact pathology measured in `generic-fantasy`, where every name
# teaches the generator one throwaway syllable and nothing transfers.
#
# A deliberately SMALL inventory is the fix. Roughly 60 syllables across 700
# names means every syllable recurs about a dozen times, which is what gives
# the Bayesian model real transition probabilities to learn. It is the same
# shape as `japanese-sengoku-samurai`, the best-scoring corpus in the library.

# Closed initial syllables double as complete one-syllable names.
GOB_INITIAL_CLOSED = [
    "Bok", "Dug", "Gag", "Gaz", "Gob", "Gor", "Grim", "Gruk", "Kaz", "Krug",
    "Mog", "Mur", "Nag", "Naz", "Nok", "Rag", "Rik", "Rud", "Skar", "Snag",
    "Snik", "Sturg", "Thrak", "Urk", "Vrog", "Zag", "Zar", "Zik", "Zog",
]

# Open initial syllables need a consonant-initial partner to close the name.
GOB_INITIAL_OPEN = [
    "Bra", "Bru", "Dro", "Gna", "Gra", "Gri", "Gru", "Kli", "Kra", "Kru",
    "Sna", "Snu", "Spa", "Sta", "Thra", "Thro", "Vra", "Zru",
]

# Endings for open initials: consonant-initial, so the seam is a clean CV.CVC.
GOB_MALE_END_C = [
    "bak", "dok", "gak", "gash", "grit", "guk", "gul", "gur", "kaz", "krit",
    "nak", "nash", "rak", "rig", "rok", "ruk", "shak", "tak", "thuk", "zak",
    "zuk", "murk", "gorn",
]

# Endings for closed initials: vowel-initial, so no cluster forms at the seam.
GOB_MALE_END_V = [
    "ak", "uk", "ash", "og", "urk", "azk", "ugz", "it", "ok", "ang", "ush",
    "izg", "ub", "art",
]

GOB_FEMALE_END_C = [
    "ka", "sha", "za", "ga", "ri", "ki", "na", "tha", "zi", "gra", "kra",
    "sna", "zra", "la", "mi",
]

GOB_FEMALE_END_V = [
    "a", "i", "u", "ash", "ira", "uka", "aza", "isha", "ula", "ika", "ura",
    "esh", "ozi",
]


def build_goblin(end_c: Sequence[str], end_v: Sequence[str]) -> List[str]:
    """Combine the syllable inventory, respecting the seam rule.

    An open initial takes a consonant-initial ending and a closed initial takes
    a vowel-initial one, so no name ever grows a consonant cluster it cannot
    carry. Closed initials are also emitted bare, since a one-syllable goblin
    name is the register at its most characteristic.
    """
    names = list(GOB_INITIAL_CLOSED)
    names += [i + e for i in GOB_INITIAL_OPEN for e in end_c]
    names += [i + e for i in GOB_INITIAL_CLOSED for e in end_v]
    return list(dict.fromkeys(names))


# ===========================================================================
# Assembly
# ===========================================================================

CORPORA = {
    "ancestry-dwarf-male": {
        "description": (
            "Dwarf names in the Old Norse register - dithematic compounds from "
            "attested Norse name elements, plus monothematic names and "
            "dwarf-names from the Dvergatal of the Poetic Edda"
        ),
        "sources": [
            "Old Norse dithematic name elements (composed, not transcribed)",
            "Dvergatal, Voluspa, Poetic Edda (public domain)",
            "Monothematic names attested in the Icelandic sagas (public domain)",
        ],
        "build": lambda: compose(ON_FIRST, ON_MALE_SECOND) + ON_MALE_SIMPLE,
    },
    "ancestry-dwarf-female": {
        "description": (
            "Dwarf names in the Old Norse register - feminine dithematic "
            "compounds from attested Norse name elements, plus monothematic names"
        ),
        "sources": [
            "Old Norse dithematic name elements (composed, not transcribed)",
            "Monothematic names attested in the Icelandic sagas (public domain)",
        ],
        "build": lambda: compose(ON_FIRST, ON_FEMALE_SECOND) + ON_FEMALE_SIMPLE,
    },
    "ancestry-elf-male": {
        "description": (
            "Elf names in the Welsh/Brythonic register - liquid consonants and "
            "vowel-heavy compounds from Welsh name elements"
        ),
        "sources": [
            "Welsh name elements (composed, not transcribed)",
            "Names attested in the Mabinogion and Welsh Triads (public domain)",
        ],
        "build": lambda: compose(WELSH_FIRST, WELSH_MALE_SECOND) + WELSH_MALE_SIMPLE,
    },
    "ancestry-elf-female": {
        "description": (
            "Elf names in the Welsh/Brythonic register - feminine compounds from "
            "Welsh name elements"
        ),
        "sources": [
            "Welsh name elements (composed, not transcribed)",
            "Names attested in the Mabinogion and Welsh Triads (public domain)",
        ],
        "build": lambda: compose(WELSH_FIRST, WELSH_FEMALE_SECOND) + WELSH_FEMALE_SIMPLE,
    },
    "ancestry-halfling-male": {
        "description": (
            "Halfling names in the medieval English hypocoristic register - "
            "homely pet-forms and diminutives, not the royal dithematic stock"
        ),
        "sources": [
            "Medieval English diminutive morphology (-kin, -cock, -ot, -et)",
            "Hypocoristic forms recorded in English manorial and poll tax rolls "
            "(public domain)",
        ],
        "build": lambda: compose(EN_MALE_STEM, EN_MALE_SUFFIX, min_first=3)
        + EN_MALE_SIMPLE,
    },
    "ancestry-halfling-female": {
        "description": (
            "Halfling names in the medieval English hypocoristic register - "
            "feminine pet-forms and diminutives"
        ),
        "sources": [
            "Medieval English diminutive morphology (-ot, -et, -ie, -kin)",
            "Hypocoristic forms recorded in English manorial and poll tax rolls "
            "(public domain)",
        ],
        "build": lambda: compose(EN_FEMALE_STEM, EN_FEMALE_SUFFIX, min_first=3)
        + EN_FEMALE_SIMPLE,
    },
    "ancestry-human-male": {
        "description": (
            "Human names in the Frankish/Norman register - the dithematic stock "
            "of medieval Western Europe with its Latin-Christian layer"
        ),
        "sources": [
            "Frankish and Norman dithematic name elements (composed, not transcribed)",
            "Names attested in medieval Western European chronicles (public domain)",
        ],
        "build": lambda: compose(FR_FIRST, FR_MALE_SECOND) + FR_MALE_SIMPLE,
    },
    "ancestry-human-female": {
        "description": (
            "Human names in the Frankish/Norman register - feminine dithematic "
            "compounds and the Latin-Christian layer"
        ),
        "sources": [
            "Frankish and Norman dithematic name elements (composed, not transcribed)",
            "Names attested in medieval Western European chronicles (public domain)",
        ],
        "build": lambda: compose(FR_FIRST, FR_FEMALE_SECOND) + FR_FEMALE_SIMPLE,
    },
    "ancestry-goblin-male": {
        "description": (
            "Goblin names - original constructed phonology: harsh onset clusters, "
            "closed syllables, back and high vowels, consonant-final"
        ),
        "sources": [
            "Original constructed phonotactics - no real-world source tradition",
        ],
        "build": lambda: build_goblin(GOB_MALE_END_C, GOB_MALE_END_V),
    },
    "ancestry-goblin-female": {
        "description": (
            "Goblin names - original constructed phonology: harsh onset clusters, "
            "closed syllables, back and high vowels, vowel-final"
        ),
        "sources": [
            "Original constructed phonotactics - no real-world source tradition",
        ],
        "build": lambda: build_goblin(GOB_FEMALE_END_C, GOB_FEMALE_END_V),
    },
}


# Target corpus size, and the attested names that survive trimming no matter
# what. Targets sit above where the metrics are expected to saturate, so there
# is headroom for later features without the lists going slack.
TARGETS: Dict[str, int] = {
    "ancestry-dwarf-male": 820,
    "ancestry-dwarf-female": 700,
    "ancestry-elf-male": 780,
    "ancestry-elf-female": 620,
    "ancestry-halfling-male": 560,
    "ancestry-halfling-female": 540,
    "ancestry-human-male": 800,
    "ancestry-human-female": 720,
    "ancestry-goblin-male": 700,
    "ancestry-goblin-female": 700,
}

PROTECTED: Dict[str, Sequence[str]] = {
    "ancestry-dwarf-male": ON_MALE_SIMPLE,
    "ancestry-dwarf-female": ON_FEMALE_SIMPLE,
    "ancestry-elf-male": WELSH_MALE_SIMPLE,
    "ancestry-elf-female": WELSH_FEMALE_SIMPLE,
    "ancestry-halfling-male": EN_MALE_SIMPLE,
    "ancestry-halfling-female": EN_FEMALE_SIMPLE,
    "ancestry-human-male": FR_MALE_SIMPLE,
    "ancestry-human-female": FR_FEMALE_SIMPLE,
}


def write_yaml(path: Path, identifier: str, spec: Dict, names: List[str]) -> None:
    def quote(text: str) -> str:
        """Always quote: several descriptions contain ': ', which unquoted YAML
        reads as a nested mapping and rejects."""
        return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'

    lines = [
        "metadata:",
        f"  description: {quote(spec['description'])}",
        "  segmenter: fantasy",
        "  sources:",
    ]
    lines += [f"    - {quote(s)}" for s in spec["sources"]]
    lines += [
        '  version: "1.0"',
        "names:",
    ]
    lines += [f"  - {n}" for n in names]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)

    for identifier, spec in CORPORA.items():
        names = finalise(spec["build"]())
        raw = len(names)
        names = trim(
            names,
            TARGETS.get(identifier, 700),
            keep=finalise(PROTECTED.get(identifier, [])),
        )
        write_yaml(out / f"{identifier}.yaml", identifier, spec, names)
        print(f"{identifier:<30} {len(names):>5} names  (from {raw} well-formed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
