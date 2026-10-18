#!/usr/bin/env bash
# Hook Maker — récupère une vidéo (lien ou fichier), extrait l'audio, transcrit avec faster-whisper
# et sort quelques images des premières secondes (pour lire l'accroche écrite à l'écran).
#
# Usage : transcribe.sh <url-ou-fichier> <dossier-de-sortie>
# Sortie dans le dossier :
#   video.*            la vidéo (si lien)
#   audio.wav          audio 16 kHz mono
#   transcript.srt     transcription avec horodatage
#   transcript.txt     transcription brute
#   frame_0.5s.jpg …   images à 0,5 s, 1,5 s et 3 s
#   info.txt           durée, machine, modèle utilisé

set -euo pipefail

SRC="${1:?Donne un lien de reel ou un chemin de fichier vidéo}"
OUT="${2:?Donne un dossier de sortie}"
HM="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$HM/.venv"

# --- Outils requis -----------------------------------------------------------
missing=()
command -v ffmpeg >/dev/null || missing+=(ffmpeg)
if [[ "$SRC" =~ ^https?:// ]]; then command -v yt-dlp >/dev/null || missing+=(yt-dlp); fi
if (( ${#missing[@]} )); then
  echo "MANQUANT: ${missing[*]}"
  echo "Installe avec : brew install ${missing[*]}"
  exit 2
fi
if [[ ! -x /usr/bin/python3 ]]; then
  echo "MANQUANT: Python d'Apple (/usr/bin/python3)"
  echo "Installe avec : xcode-select --install"
  exit 2
fi

# --- faster-whisper, installé une fois dans le dossier du skill ---------------
# Python d'Apple (3.9) : les versions Homebrew récentes n'ont pas encore les paquets nécessaires.
if ! "$VENV/bin/python" -c "import faster_whisper" 2>/dev/null; then
  echo "Installation de faster-whisper (une seule fois, ~1 min)…"
  rm -rf "$VENV"
  /usr/bin/python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q --disable-pip-version-check faster-whisper==1.2.1
fi

# --- Modèle selon la puce ----------------------------------------------------
# Puce Apple (M1, M2…) : large-v3-turbo, le plus précis.
# Mac Intel : small, ~4x plus léger, pour rester rapide.
# Téléchargé une seule fois dans ~/.cache/huggingface.
if [[ "$(uname -m)" == "arm64" ]]; then MODEL="large-v3-turbo"; else MODEL="small"; fi
MODEL="${HOOK_MAKER_MODEL:-$MODEL}"
mkdir -p "$OUT"

# --- Récupération de la vidéo ------------------------------------------------
if [[ "$SRC" =~ ^https?:// ]]; then
  echo "Téléchargement de la vidéo…"
  yt-dlp -q --no-warnings --no-playlist \
    -f "bv*[height<=720]+ba/b[height<=720]/b" \
    -o "$OUT/video.%(ext)s" "$SRC"
  VIDEO="$(ls "$OUT"/video.* | head -1)"
else
  [[ -f "$SRC" ]] || { echo "Fichier introuvable : $SRC"; exit 1; }
  VIDEO="$SRC"
fi

# --- Audio + images ----------------------------------------------------------
ffmpeg -hide_banner -loglevel error -y -i "$VIDEO" -vn -ac 1 -ar 16000 -c:a pcm_s16le "$OUT/audio.wav"
DURATION="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$VIDEO" | cut -d. -f1)"
if ffprobe -v error -select_streams v -show_entries stream=codec_type -of csv=p=0 "$VIDEO" | grep -q video; then
  for t in 0.5 1.5 3; do
    ffmpeg -hide_banner -loglevel error -y -ss "$t" -i "$VIDEO" -frames:v 1 -vf "scale=-2:720" "$OUT/frame_${t}s.jpg" || true
  done
fi

# --- Transcription -----------------------------------------------------------
echo "Transcription ($MODEL)…"
"$VENV/bin/python" "$HM/scripts/transcribe.py" "$OUT/audio.wav" "$OUT/transcript" "$MODEL"

{
  echo "source: $SRC"
  echo "duree_s: ${DURATION:-?}"
  echo "machine: $(uname -m)"
  echo "modele: faster-whisper $MODEL"
} > "$OUT/info.txt"

echo "OK → $OUT"
cat "$OUT/info.txt"
