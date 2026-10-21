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

Les identifiants sont calculés à partir des textes : relancer le script donne exactement le
même fichier, et importer deux fois le même paquet ne crée aucun doublon. Toutes les dates sont
fixées au 1er janvier 2000 : importer un paquet n'écrase donc jamais la progression ni les
corrections d'une personne qui a déjà ces cartes. Chaque carte a une seconde de plus que la
précédente, pour que Flash les propose dans l'ordre de la source.
"""
import datetime
import json
import pathlib
import sys
import unicodedata
import uuid

NAMESPACE = uuid.UUID("6f1c1b6e-0b52-4c0b-9a52-7b1f1a6a2d10")
DATE = "2000-01-01T00:00:00.000Z"
COLOR = 0xFF3F51B5
FORMAT_VERSION = 3  # version du fichier d'export de Flash (lisible dès Flash 1.1.0)


class SourceError(Exception):
    pass


def parse_source(text):
    """Renvoie (matière, paquet, [(question, réponse), ...]) ou lève SourceError."""
    text = unicodedata.normalize("NFC", text)  # un « é » décomposé donnerait d'autres identifiants
    subject = deck = None
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
            else:
                raise SourceError(f"ligne {number} : en-tête inconnu « {line} » (attendu : Matière ou Paquet)")
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
    return subject, deck, cards


def make_id(*parts):
    return str(uuid.uuid5(NAMESPACE, "␟".join(parts)))


def build_pack(subject, deck, cards):
    subject_id = make_id("matiere", subject)
    deck_id = make_id("paquet", subject, deck)
    rows = {
        "subjects": [{"id": subject_id, "updatedAt": DATE, "deletedAt": None, "name": subject,
                      "color": COLOR}],
        "decks": [{"id": deck_id, "updatedAt": DATE, "deletedAt": None, "subjectId": subject_id,
                   "name": deck}],
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
        card_id = make_id("carte", subject, deck, question)
        rows["cards"].append({"id": card_id, "updatedAt": DATE, "deletedAt": None, "deckId": deck_id,
                              "front": question, "back": answer, "createdAt": created})
        rows["card_states"].append({"id": make_id("etat", card_id), "updatedAt": DATE, "deletedAt": None,
                                    "cardId": card_id, "phase": 0, "stepIndex": 0, "ease": 2.5,
                                    "intervalDays": 0, "dueAt": DATE, "lapses": 0})
    return {"format": "flash-backup", "version": FORMAT_VERSION, "exportedAt": DATE, "tables": rows}


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


def main(argv):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors="replace")  # une console Windows ancienne ne doit pas faire planter l'affichage
    if len(argv) not in (2, 3):
        print(__doc__)
        return 2
    source = pathlib.Path(argv[1])
    try:
        subject, deck, cards = parse_source(read_source(source))
        output = pathlib.Path(argv[2]) if len(argv) == 3 else default_output(source)
        write_pack(output, build_pack(subject, deck, cards))
    except SourceError as error:
        print(f"Erreur : {error}", file=sys.stderr)
        return 1
    print(f"{len(cards)} cartes -> {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
