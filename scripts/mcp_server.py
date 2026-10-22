#!/usr/bin/env python3
"""Hook Maker — petit serveur MCP local (stdio, sans dépendance).

Il donne à la page Hook Maker Studio l'accès à yt-dlp + ffmpeg + faster-whisper
de ce Mac, via scripts/transcribe.sh. Claude, lui, reste sur l'abonnement.

Outils :
  lancer_transcription(source)  lien de reel ou chemin de fichier → id de tâche
  etat_transcription(id)        état ; une fois fini : transcription + images
"""
import base64
import datetime
import json
import os
import re
import subprocess
import sys
import threading

HM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(HM, "scripts", "transcribe.sh")
ENV = dict(os.environ)
ENV["PATH"] = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:" + ENV.get("PATH", "")

JOBS = {}
LOCK = threading.Lock()

TOOLS = [
    {
        "name": "lancer_transcription",
        "description": "Télécharge un reel (lien Instagram, TikTok, YouTube Shorts) ou lit un fichier vidéo local, "
                       "puis le transcrit avec faster-whisper. Renvoie un id de tâche à suivre avec etat_transcription.",
        "inputSchema": {
            "type": "object",
            "properties": {"source": {"type": "string", "description": "Lien du reel ou chemin absolu d'un fichier vidéo/audio"}},
            "required": ["source"],
        },
    },
    {
        "name": "etat_transcription",
        "description": "État d'une transcription. status = en_cours | fini | erreur. "
                       "Quand c'est fini : srt (horodaté), texte, duree_s et frames (images JPEG en base64 à 0,5 s, 1,5 s et 3 s).",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
        },
        "annotations": {"readOnlyHint": True},
    },
]


def slug(src):
    base = re.sub(r"[?#].*$", "", src.rstrip("/")).split("/")[-1] or "video"
    base = re.sub(r"\.[A-Za-z0-9]{2,4}$", "", base)
    return re.sub(r"[^A-Za-z0-9_-]+", "-", base)[:40].strip("-") or "video"


def run(job_id, src, out):
    try:
        p = subprocess.run(["bash", SCRIPT, src, out], env=ENV, capture_output=True, text=True, timeout=1800)
        log = (p.stdout + p.stderr).strip()
        with LOCK:
            JOBS[job_id]["log"] = log[-2000:]
            JOBS[job_id]["status"] = "fini" if p.returncode == 0 else "erreur"
            JOBS[job_id]["code"] = p.returncode
    except Exception as e:  # noqa: BLE001
        with LOCK:
            JOBS[job_id].update(status="erreur", log=str(e))


def lancer(args):
    src = str(args.get("source", "")).strip()
    if not src:
        raise ValueError("Donne un lien de reel ou un chemin de fichier.")
    if not re.match(r"^https?://", src):
        src = os.path.expanduser(src)
        if not os.path.isfile(src):
            raise ValueError("Fichier introuvable : " + src)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    job_id = stamp + "-" + slug(src)
    out = os.path.join(HM, "analyses", job_id)
    with LOCK:
        JOBS[job_id] = {"status": "en_cours", "out": out, "source": src, "log": ""}
    threading.Thread(target=run, args=(job_id, src, out), daemon=True).start()
    return {"id": job_id, "status": "en_cours", "dossier": out}


def read(path, limit=None):
    try:
        with open(path, encoding="utf-8") as f:
            t = f.read()
        return t[:limit] if limit else t
    except OSError:
        return ""


def small_frame(path):
    if not os.path.isfile(path):
        return None
    small = path.replace(".jpg", "_small.jpg")
    if not os.path.isfile(small):
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", path,
                        "-vf", "scale=-2:480", "-q:v", "6", small], env=ENV, capture_output=True)
    target = small if os.path.isfile(small) else path
    with open(target, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def etat(args):
    job_id = str(args.get("id", ""))
    with LOCK:
        job = dict(JOBS.get(job_id) or {})
    if not job:
        out = os.path.join(HM, "analyses", os.path.basename(job_id))
        if job_id and os.path.isfile(os.path.join(out, "transcript.srt")):
            job = {"status": "fini", "out": out}
        else:
            raise ValueError("Tâche inconnue : " + job_id)
    res = {"id": job_id, "status": job["status"]}
    if job["status"] == "en_cours":
        res["message"] = "Téléchargement et transcription en cours…"
        return res
    if job["status"] == "erreur":
        log = job.get("log", "")
        res["message"] = log or "La transcription a échoué."
        if job.get("code") == 2:
            res["message"] = "Outil manquant sur le Mac. " + log
        return res
    out = job["out"]
    info = read(os.path.join(out, "info.txt"))
    m = re.search(r"duree_s:\s*(\S+)", info)
    res.update(
        srt=read(os.path.join(out, "transcript.srt"), 40000),
        texte=read(os.path.join(out, "transcript.txt"), 30000).strip(),
        duree_s=m.group(1) if m else "?",
        dossier=out,
        frames=[f for f in (
            {"t": t, "jpeg_base64": small_frame(os.path.join(out, "frame_%ss.jpg" % t))} for t in ("0.5", "1.5", "3")
        ) if f["jpeg_base64"]],
    )
    return res


HANDLERS = {"lancer_transcription": lancer, "etat_transcription": etat}


def send(msg):
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def handle(msg):
    mid, method, params = msg.get("id"), msg.get("method"), msg.get("params") or {}
    if mid is None:
        return  # notification
    if method == "initialize":
        result = {
            "protocolVersion": params.get("protocolVersion", "2025-06-18"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "hook-maker", "version": "1.0.0"},
        }
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        fn = HANDLERS.get(params.get("name"))
        if not fn:
            send({"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": "Outil inconnu"}})
            return
        try:
            data = fn(params.get("arguments") or {})
            result = {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}], "structuredContent": data}
        except Exception as e:  # noqa: BLE001
            result = {"content": [{"type": "text", "text": str(e)}], "isError": True}
    else:
        send({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "Méthode inconnue : %s" % method}})
        return
    send({"jsonrpc": "2.0", "id": mid, "result": result})


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            handle(json.loads(line))
        except Exception as e:  # noqa: BLE001
            sys.stderr.write("hook-maker mcp: %s\n" % e)


if __name__ == "__main__":
    main()
