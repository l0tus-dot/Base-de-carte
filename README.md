# Cartes Flash partagées

Ce dépôt contient des **paquets de cartes prêts à importer** dans l'application Flash : une matière, un paquet, des cartes. Rien à installer en plus, et aucune carte n'arrive avec une progression : tout le monde repart de zéro, à son rythme.

Il faut **Flash 1.1.0 ou plus récent** (une version plus ancienne refuse ces fichiers).

## Utiliser un paquet

1. Dans ce dépôt, ouvre le dossier `paquets/`, choisis une matière puis un fichier `.json`.
2. Télécharge-le avec le bouton de téléchargement en haut à droite de la page du fichier (« Download raw file »). C'est le plus simple. Tu peux aussi télécharger tout le dépôt avec le bouton vert « Code », puis « Download ZIP » : **décompresse alors le zip** (Windows : clic droit, « Extraire tout… » ; téléphone : appui long sur le fichier, puis « Extraire »), car Flash n'accepte que le fichier `.json`, pas le zip.
3. Dans Flash : **Réglages**, puis **Importer un fichier**. Une fenêtre s'ouvre : **ne coche pas** « Restaurer aussi ce que j'ai supprimé depuis » (cette case ferait revenir les cartes du paquet que tu avais supprimées), touche **Importer**, puis choisis le fichier `.json` téléchargé.
4. Les cartes arrivent dans leur matière et leur paquet, prêtes à réviser.

Importer deux fois le même paquet ne crée **pas de doublons**, et ne touche ni à ta progression ni aux cartes que tu as modifiées.

## Paquets disponibles

| Matière | Paquet | Cartes | Fichier |
| --- | --- | --- | --- |
| CEJMA | Les licences logicielles | 21 | `paquets/cejma/les-licences-logicielles.json` |
| Réseau | Routage statique | 18 | `paquets/reseau/routage-statique.json` |
| Réseau | Routage Dynamique (RIPv2) | 26 | `paquets/reseau/routage-dynamique-ripv2.json` |
| Réseau | NAT et PAT | 25 | `paquets/reseau/nat-et-pat.json` |
| Réseau | DHCP | 22 | `paquets/reseau/dhcp.json` |
| Réseau | Active Directory | 30 | `paquets/reseau/active-directory.json` |
| Réseau | Dépannage réseau | 33 | `paquets/reseau/depannage-reseau.json` |
| Cybersécurité | Segmentation VLSM | 18 | `paquets/cybersecurite/segmentation-vlsm.json` |
| Cybersécurité | VPN | 28 | `paquets/cybersecurite/vpn.json` |
| Cybersécurité | Délégation de droit avec sudo | 31 | `paquets/cybersecurite/delegation-sudo.json` |
| Cybersécurité | ACL cisco | 32 | `paquets/cybersecurite/acl-cisco.json` |

*(Tenir cette liste à jour à chaque nouveau paquet.)*

## Ajouter un paquet

Il faut Python (aucune bibliothèque à installer). Sous Windows, si la commande `python` ouvre le Microsoft Store, écris `py` à la place.

1. Écris un fichier source dans `sources/<matière>/<paquet>.txt`, sur le modèle de `sources/exemple/histoire-revolution.txt` :

   ```text
   # Matière : Histoire
   # Paquet : La Révolution française

   question ; réponse
   autre question ; autre réponse
   ```

   Une carte par ligne, **un seul point-virgule**. Le prompt du guide Flash (« Créer tes cartes avec une IA ») produit déjà ce format : colle le bloc de code obtenu sous les deux lignes d'en-tête.
2. Génère le fichier à importer, depuis la racine du dépôt :

   ```bash
   python outils/creer-paquet.py sources/histoire/revolution.txt
   ```

   Le fichier est écrit dans `paquets/histoire/revolution.json`. Le script s'arrête avec un message clair si une ligne est mal formée ou si une question est en double. Il est un peu plus strict que « Importer du texte » dans Flash : une ligne ne doit contenir qu'**un** point-virgule. Enregistre le `.txt` en UTF-8.
3. **Relis les cartes** (une IA peut se tromper), ajoute le paquet à la liste ci-dessus, puis envoie le tout sur GitHub.

## Règles

- Ne publie que des contenus que tu as le droit de partager : tes propres cartes, tes synthèses. Des cartes reformulées à partir d'un cours, oui ; recopier le cours ou un sujet protégé par des droits d'auteur, non, sans autorisation. Ce dépôt est public.
- Pas de données personnelles (noms, notes, adresses) dans les cartes.
- Garde les fichiers `.txt` et `.json` ensemble : le `.txt` est la source, le `.json` est ce que les autres importent.

## À savoir

- **Un paquet ne se met pas à jour tout seul.** Quand tu complètes un paquet, ceux qui le réimportent reçoivent les **nouvelles** cartes. Une carte déjà importée garde le texte que la personne a chez elle, même si tu l'as corrigée ici : c'est voulu, pour ne jamais écraser ce qu'un camarade a modifié.
- Si tu changes la **question** d'une carte, le script la considère comme une nouvelle carte : l'ancienne reste chez ceux qui l'ont déjà.
- **Ne renomme jamais la matière ou le paquet d'un fichier déjà publié**, même pour une faute de frappe : les identifiants viennent de ces noms, donc tout le paquet arriverait en double chez ceux qui le réimportent.
- Les cartes d'un paquet arrivent **dans l'ordre de la source**, et avant les cartes nouvelles que tu as créées toi-même (Flash propose d'abord les plus anciennes). Avec un gros paquet et un quota de nouvelles cartes par jour, tes propres cartes attendent donc quelques jours.
- Si tu veux recevoir les ajouts futurs d'un paquet, **ne supprime pas** sa matière ni son paquet dans Flash (tu peux déplacer ses cartes ailleurs, mais laisse-les là) : les nouvelles cartes seraient ajoutées sans que tu les voies.
- La matière est reconnue par son **nom exact**. Si tu as déjà créé à la main une matière « Histoire », celle du paquet arrive à côté sous le même nom : tu peux déplacer les cartes d'un paquet à l'autre dans Flash.
- Les fichiers sont tous datés du 1er janvier 2000 : c'est ce qui garantit qu'un import n'écrase rien.

## Mettre ce dossier en ligne

Ce dossier est un modèle : pour l'utiliser, crée un nouveau dépôt **public** sur GitHub, copie-y le contenu de ce dossier, puis envoie-le. Donne ensuite l'adresse du dépôt à tes camarades.
