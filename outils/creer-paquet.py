"""Transforme un fichier source (.txt) en paquet que Flash peut importer (.json).

Aucune dépendance à installer. Usage, depuis la racine du dépôt :

    python outils/creer-paquet.py sources/exemple/histoire-revolution.txt

(Sous Windows, si « python » ouvre le Microsoft Store, écris « py » à la place.)

Le fichier produit est écrit dans paquets/, au même endroit relatif que la source
(sources/exemple/x.txt donne paquets/exemple/x.json). On peut passer un second argument
pour choisir un autre fichier de sortie.

Format de la source (enregistrée en UTF-8) :

    # Matière : Histoire
    # Paquet : La Révolution française

    question ; réponse
    autre question ; autre réponse

Une carte par ligne, avec un seul point-virgule. Les lignes vides et les lignes ``` sont ignorées.
Une ligne facultative « # Description : … » donne la courte description affichée dans la liste des
paquets de l'application (elle n'entre pas dans le fichier du paquet).

Pour un sous-paquet, ajoute une ligne « # Parent : … » : « # Paquet » est alors le nom du sous-paquet
et « # Parent » celui du paquet qui le contient (un seul niveau de sous-paquets) :

    # Matière : CEJM
    # Parent : Thème 1
    # Paquet : Économique

Le catalogue des paquets (lu par l'application) se fabrique avec :

    python outils/creer-paquet.py --catalogue

Il écrit catalogue.json à la racine du dépôt : à relancer, puis à envoyer avec les paquets,
chaque fois qu'un paquet est ajouté, modifié ou retiré.

Les identifiants sont calculés à partir des textes : relancer le script donne exactement le
même fichier, et importer deux fois le même paquet ne crée aucun doublon. Toutes les dates sont
fixées au 1er janvier 2000 : importer un paquet n'écrase donc jamais la progression ni les
corrections d'une personne qui a déjà ces cartes. Chaque carte a une seconde de plus que la
précédente, pour que Flash les propose dans l'ordre de la source.
"""
import datetime
import json
import pathlib
import re
import sys
import unicodedata
import uuid

NAMESPACE = uuid.UUID("6f1c1b6e-0b52-4c0b-9a52-7b1f1a6a2d10")
DATE = "2000-01-01T00:00:00.000Z"
COLOR = 0xFF3F51B5
FORMAT_VERSION = 3  # version du fichier d'export de Flash (lisible dès Flash 1.1.0)
SUBDECK_FORMAT_VERSION = 5  # un sous-paquet a besoin du format 5 (Flash 1.5.0)


class SourceError(Exception):
    pass


def parse_source(text):
    """Renvoie (matière, paquet, [(question, réponse), ...], description, parent) ou lève SourceError.

    La description et le parent sont facultatifs : une chaîne vide si la ligne « # Description : … »
    ou « # Parent : … » manque.
    """
    text = unicodedata.normalize("NFC", text)  # un « é » décomposé donnerait d'autres identifiants
    subject = deck = description = parent = None
    cards = []
    seen = set()
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip().lstrip("﻿")
        if not line or line.startswith("```"):
            continue
        if line.startswith("#"):
            key, _, value = line.lstrip("#").partition(":")
            key, value = key.strip().lower(), value.strip()
            if key in ("matière", "matiere"):
                if subject is not None:
                    raise SourceError(f"ligne {number} : la matière est déjà indiquée plus haut")
                subject = value
            elif key == "paquet":
                if deck is not None:
                    raise SourceError(f"ligne {number} : le paquet est déjà indiqué plus haut")
                deck = value
            elif key == "description":
                if description is not None:
                    raise SourceError(f"ligne {number} : la description est déjà indiquée plus haut")
                description = value
            elif key == "parent":
                if parent is not None:
                    raise SourceError(f"ligne {number} : le parent est déjà indiqué plus haut")
                if not value:
                    raise SourceError(f"ligne {number} : le nom du parent est vide")
                parent = value
            else:
                raise SourceError(f"ligne {number} : en-tête inconnu « {line} » "
                                  "(attendu : Matière, Parent, Paquet ou Description)")
            continue
        parts = line.split(";")
        if len(parts) != 2:
            raise SourceError(f"ligne {number} : il faut exactement un point-virgule (« question ; réponse »)")
        question, answer = parts[0].strip(), parts[1].strip()
        if not question or not answer:
            raise SourceError(f"ligne {number} : la question et la réponse ne doivent pas être vides")
        if question in seen:
            raise SourceError(f"ligne {number} : cette question existe déjà dans le paquet")
        seen.add(question)
        cards.append((question, answer))
    if not subject:
        raise SourceError("il manque la ligne « # Matière : … »")
    if not deck:
        raise SourceError("il manque la ligne « # Paquet : … »")
    if not cards:
        raise SourceError("le paquet ne contient aucune carte")
    return subject, deck, cards, description or "", parent or ""


def make_id(*parts):
    return str(uuid.uuid5(NAMESPACE, "␟".join(parts)))


def build_pack(subject, deck, cards, parent=""):
    subject_id = make_id("matiere", subject)
    if parent:
        # Le paquet parent est le même (même identifiant) dans tous les fichiers de ses sous-paquets.
        parent_id = make_id("paquet", subject, parent)
        deck_id = make_id("sous-paquet", subject, parent, deck)
        decks = [
            {"id": parent_id, "updatedAt": DATE, "deletedAt": None, "subjectId": subject_id,
             "name": parent, "parentId": None},
            {"id": deck_id, "updatedAt": DATE, "deletedAt": None, "subjectId": subject_id,
             "name": deck, "parentId": parent_id},
        ]
        card_key = (subject, parent, deck)
    else:
        deck_id = make_id("paquet", subject, deck)
        decks = [{"id": deck_id, "updatedAt": DATE, "deletedAt": None, "subjectId": subject_id,
                  "name": deck}]
        card_key = (subject, deck)
    rows = {
        "subjects": [{"id": subject_id, "updatedAt": DATE, "deletedAt": None, "name": subject,
                      "color": COLOR}],
        "decks": decks,
        "cards": [],
        "card_states": [],
        "review_logs": [],
        "quiz_answers": [],
        "exams": [],
        "study_sessions": [],
    }
    start = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    for index, (question, answer) in enumerate(cards):
        created = (start + datetime.timedelta(seconds=index)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        card_id = make_id("carte", *card_key, question)
        rows["cards"].append({"id": card_id, "updatedAt": DATE, "deletedAt": None, "deckId": deck_id,
                              "front": question, "back": answer, "createdAt": created})
        rows["card_states"].append({"id": make_id("etat", card_id), "updatedAt": DATE, "deletedAt": None,
                                    "cardId": card_id, "phase": 0, "stepIndex": 0, "ease": 2.5,
                                    "intervalDays": 0, "dueAt": DATE, "lapses": 0})
    version = SUBDECK_FORMAT_VERSION if parent else FORMAT_VERSION
    return {"format": "flash-backup", "version": version, "exportedAt": DATE, "tables": rows}


def default_output(source):
    root = pathlib.Path(__file__).resolve().parent.parent
    try:
        relative = source.resolve().relative_to(root / "sources")
    except ValueError:
        raise SourceError("la source doit se trouver dans le dossier sources/, "
                          "ou indique le fichier de sortie en second argument")
    return root / "paquets" / relative.with_suffix(".json")


def read_source(source):
    try:
        return source.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise SourceError("le fichier n'est pas en UTF-8 : enregistre-le à nouveau en UTF-8 "
                          "(Bloc-notes : Enregistrer sous, puis Encodage)")
    except OSError:
        raise SourceError(f"impossible de lire « {source} »")


def write_pack(output, pack):
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(pack, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    except OSError:
        raise SourceError(f"impossible d'écrire « {output} »")


PACK_PATH = re.compile(r"^paquets/[\w-]+/[\w-]+\.json$")  # ce que l'application accepte de télécharger


def read_pack_summary(path, relative):
    """(matière, paquet, parent, nombre de cartes) d'un fichier de paquet, ou SourceError.

    Pour un sous-paquet, « paquet » est le nom du sous-paquet ; sans parent, « parent » vaut "".
    """
    try:
        tables = json.loads(path.read_text(encoding="utf-8"))["tables"]
        subject = tables["subjects"][0]["name"]
        decks = tables["decks"]
        child = next((d for d in decks if d.get("parentId")), None)
        if child is None:
            deck, parent = decks[0]["name"], ""
        else:
            deck = child["name"]
            parent = next(d["name"] for d in decks if d["id"] == child["parentId"])
        cards = sum(1 for card in tables["cards"] if card.get("deletedAt") is None)
    except (OSError, ValueError, KeyError, IndexError, TypeError, AttributeError, StopIteration):
        raise SourceError(f"paquet illisible : {relative} (ce n'est pas un fichier produit par ce script ?)")
    return subject, deck, parent, cards


def build_catalogue(root):
    """Le catalogue de tous les paquets de root/paquets, trié par matière puis paquet."""
    packs_dir = root / "paquets"
    if not packs_dir.is_dir():
        raise SourceError(f"il n'y a pas de dossier paquets/ dans « {root} »")
    packs = []
    for path in sorted(packs_dir.rglob("*.json")):
        relative = path.relative_to(root).as_posix()
        if not PACK_PATH.match(relative):
            raise SourceError(f"nom de fichier non pris en charge : {relative} "
                              "(utilise paquets/<dossier>/<nom>.json, avec des lettres, chiffres, - ou _)")
        subject, deck, parent, cards = read_pack_summary(path, relative)
        description = ""
        source = root / "sources" / path.relative_to(packs_dir).with_suffix(".txt")
        if source.is_file():
            description = parse_source(read_source(source))[3]
        entry = {"subject": subject, "deck": deck, "cards": cards,
                 "description": description, "path": relative}
        if parent:
            entry["parent"] = parent
        packs.append(entry)
    packs.sort(key=lambda p: (p["subject"].casefold(), p.get("parent", p["deck"]).casefold(),
                              "parent" not in p, p["deck"].casefold()))
    return {"format": "flash-catalogue", "version": 1, "packs": packs}


def catalogue_main(args):
    if len(args) > 1:
        print(__doc__)
        return 2
    root = pathlib.Path(args[0]) if args else pathlib.Path(__file__).resolve().parent.parent
    try:
        catalogue = build_catalogue(root)
        write_pack(root / "catalogue.json", catalogue)
    except SourceError as error:
        print(f"Erreur : {error}", file=sys.stderr)
        return 1
    print(f"{len(catalogue['packs'])} paquets -> {root / 'catalogue.json'}")
    return 0


def main(argv):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors="replace")  # une console Windows ancienne ne doit pas faire planter l'affichage
    if len(argv) >= 2 and argv[1] == "--catalogue":
        return catalogue_main(argv[2:])
    if len(argv) not in (2, 3):
        print(__doc__)
        return 2
    source = pathlib.Path(argv[1])
    try:
        subject, deck, cards, _description, parent = parse_source(read_source(source))
        output = pathlib.Path(argv[2]) if len(argv) == 3 else default_output(source)
        write_pack(output, build_pack(subject, deck, cards, parent))
    except SourceError as error:
        print(f"Erreur : {error}", file=sys.stderr)
        return 1
    print(f"{len(cards)} cartes -> {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
