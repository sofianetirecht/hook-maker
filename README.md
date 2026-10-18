# Hook Maker

Un skill **Claude Code** qui analyse et écrit les hooks de tes reels Instagram et TikTok, adaptés à ta niche, puis affiche le résultat dans une page interactive au style rétro anime des années 90.

Donne-lui un lien de reel, un hook, un script ou juste un sujet. Il te rend :

- un **niveau de puissance** de ton hook actuel (sur 10 000, façon scouter) ;
- un diagnostic : **alignement avec ta niche, forces, faiblesses, recommandations** ;
- **5 nouveaux hooks** (3 à dire, 2 à afficher à l'écran), chacun avec le modèle utilisé et pourquoi il marche ;
- le **script réécrit** sur une ligne de temps : HOOK → PROMESSE → VALEUR → BOUCLE → VALEUR → BOUCLE → VALEUR → CTA → RÉSOLUTION ;
- un **contrôle avant tournage** (le hook couvre-t-il tout le contenu ? mots concrets ? pas de disclaimer ?).

Sur la page, chaque hook a des boutons **« Autre version »**, **« Plus percutant »** et **« Plus court »** : Claude le réécrit directement depuis la page.

---

## Installation

### Ce qu'il faut

- Un **Mac** (puce Apple M1, M2… ou Intel), macOS 12 ou plus récent.
- **Claude Code**, dans l'application Claude (desktop) de préférence : le résultat s'affiche en Artifact. En terminal, il s'ouvre dans ton navigateur.
- **[Homebrew](https://brew.sh)**.
- Pour le mode vidéo seulement : **yt-dlp**, **ffmpeg** et le **Python d'Apple** (`/usr/bin/python3`).

Les modes hook, script et sujet n'ont besoin de rien d'autre que Claude Code.

### Le plus simple : demande à Claude

Dans Claude Code, colle :

```
Installe le skill https://github.com/sofianetirecht/hook-maker en suivant son README.
```

### À la main

```bash
# 1. Le skill
git clone https://github.com/sofianetirecht/hook-maker.git ~/.claude/skills/hook-maker

# 2. Les outils du mode vidéo
brew install yt-dlp ffmpeg

# 3. Le Python d'Apple (si une fenêtre propose d'installer les outils de ligne de commande, accepte)
/usr/bin/python3 --version
```

Relance ensuite Claude Code (ou ouvre une nouvelle session) pour qu'il voie le skill.

### Instructions pour Claude Code

> Cette section s'adresse à Claude quand un utilisateur lui demande d'installer ce skill.

1. Vérifie que la machine est un Mac (`uname -s` doit renvoyer `Darwin`). Sinon, préviens que le mode vidéo n'est prévu que pour macOS ; les autres modes marchent partout.
2. Si `~/.claude/skills/hook-maker` existe déjà, fais `git -C ~/.claude/skills/hook-maker pull` au lieu de cloner. Sinon :
   `git clone https://github.com/sofianetirecht/hook-maker.git ~/.claude/skills/hook-maker`
3. Vérifie Homebrew avec `command -v brew`. S'il manque, ne l'installe pas toi-même : donne à l'utilisateur la commande officielle de https://brew.sh et attends qu'il l'ait lancée.
4. Installe ce qui manque parmi les outils du mode vidéo : `brew install yt-dlp ffmpeg` (seulement ceux absents de `command -v`).
5. Vérifie `/usr/bin/python3 --version`. S'il manque, demande à l'utilisateur de lancer `xcode-select --install` (une fenêtre s'ouvre, c'est à lui de valider).
6. Optionnel, pour un premier lancement rapide : installe faster-whisper dès maintenant.
   ```bash
   /usr/bin/python3 -m venv ~/.claude/skills/hook-maker/.venv
   ~/.claude/skills/hook-maker/.venv/bin/pip install -q faster-whisper==1.2.1
   ```
   Sinon, le script le fera au premier reel analysé.
7. Préviens l'utilisateur :
   - qu'il doit ouvrir une nouvelle session pour que `/hook-maker` apparaisse ;
   - que le premier reel analysé télécharge le modèle de transcription une seule fois (~1,5 Go sur puce Apple, ~500 Mo sur Intel) ;
   - qu'au premier lancement le skill lui posera 5 questions pour créer sa fiche niche.

N'utilise pas le Python de Homebrew pour faster-whisper : les versions récentes (3.13 et plus) n'ont pas encore tous les paquets nécessaires. Le Python d'Apple (3.9) fonctionne.

---

## Utilisation

Tape `/hook-maker` suivi de ce que tu as :

```
/hook-maker https://www.instagram.com/reel/...
/hook-maker /chemin/vers/ma-video.mp4
/hook-maker Fais ces 5 exercices tous les jours pour perdre du ventre
/hook-maker [ton script collé]
/hook-maker une vidéo sur les outils gratuits pour monter ses reels
```

Le skill reconnaît le mode tout seul :

| Tu donnes | Il fait |
|---|---|
| Un **lien de reel** ou un **fichier vidéo** | Télécharge, transcrit, lit le texte à l'écran, note le hook, propose de nouveaux hooks et réécrit tout le script |
| Un **hook** écrit à la main | Note le hook, diagnostic, réécritures, et le début conseillé (hook + promesse + première boucle) |
| Un **script** | Note son hook, propose de nouveaux hooks, réécrit le script |
| Un **sujet** | Propose une structure complète et des hooks |

Ensuite, tu peux continuer dans la conversation : « refais le hook 2 plus court », « adapte en carrousel », « change le CTA pour vendre ma formation ». La même page est mise à jour.

### Ta niche

Au premier lancement, le skill te pose 5 questions : à qui tu parles, ce que ta cible vit, ce qu'elle pense, ce qu'elle veut, et où mène ton appel à l'action. Il enregistre une fiche dans `niches/` et s'en sert à chaque analyse. Tu peux en avoir plusieurs ; il te demande laquelle utiliser.

---

## Ce qu'il y a dans le dossier

```
hook-maker/
├── SKILL.md                    Les instructions que suit Claude (modes, notation, rendu)
├── hooks.md                    Rôle du hook, 4 modèles, 30 hooks, pourquoi ils marchent
├── structure-script-video.md   La structure d'un script qui retient
├── regles.md                   Règles maison, prioritaires sur tout le reste
├── niches/
│   └── _modele.md              Modèle de fiche niche (tes fiches arrivent ici)
├── scripts/
│   ├── transcribe.sh           Télécharge la vidéo, extrait l'audio et 3 images, lance la transcription
│   ├── transcribe.py           Transcription avec faster-whisper (sous-titres horodatés)
│   └── render.py               Injecte l'analyse dans la page de résultat
├── template/
│   └── resultat.html           La page de résultat (style, mise en page, boutons)
└── analyses/                   Tes analyses (une par vidéo), créé à l'usage
```

`niches/`, `analyses/` et `.venv/` restent sur ta machine : ils ne sont pas dans le dépôt.

### Comment marche la transcription

Tout se passe **en local**, sans clé d'API et sans envoyer l'audio nulle part :

1. **yt-dlp** télécharge le reel (720p max).
2. **ffmpeg** extrait l'audio et 3 images (à 0,5 s, 1,5 s et 3 s) pour lire le texte affiché à l'écran.
3. **faster-whisper** transcrit en français, avec l'horodatage, pour isoler les 3 premières secondes.

Le modèle dépend de la puce :

| Machine | Modèle | Taille | Durée pour un reel d'une minute |
|---|---|---|---|
| Puce Apple | large-v3-turbo | ~1,5 Go | ~20 à 30 s, téléchargement compris |
| Intel | small | ~500 Mo | quelques dizaines de secondes |

Pour forcer un autre modèle (par exemple si la transcription n'est pas assez précise sur Intel) :

```bash
export HOOK_MAKER_MODEL=medium
```

---

## Personnaliser

- **`regles.md`** : ajoute tes propres règles. Quand tu corriges un hook en expliquant pourquoi, le skill te propose de l'y ajouter.
- **`niches/`** : modifie tes fiches à la main quand ta cible évolue.
- **`hooks.md`** : ajoute tes modèles de hooks favoris, le skill les utilisera.

## Limites

- Instagram bloque parfois le téléchargement (compte privé, trop de requêtes). Dans ce cas, télécharge la vidéo et donne le fichier.
- Whisper écorche les noms propres et certains mots. L'analyse n'en souffre pas, mais relis le script réécrit.
- Les boutons « Autre version » sur la page ne marchent que dans l'Artifact publié (pas dans la version ouverte dans le navigateur).

## Licence

[MIT](LICENSE).
