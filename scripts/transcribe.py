"""Hook Maker — transcrit audio.wav avec faster-whisper, sort transcript.srt et transcript.txt.

Usage : .venv/bin/python transcribe.py <audio.wav> <prefixe-sortie> <modele>
"""
import sys

from faster_whisper import WhisperModel


def ts(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main() -> None:
    audio, out, model_name = sys.argv[1], sys.argv[2], sys.argv[3]
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio, language="fr", vad_filter=True)

    srt, txt = [], []
    for i, seg in enumerate(segments, 1):
        text = seg.text.strip()
        srt.append(f"{i}\n{ts(seg.start)} --> {ts(seg.end)}\n{text}\n")
        txt.append(text)

    with open(out + ".srt", "w", encoding="utf-8") as f:
        f.write("\n".join(srt))
    with open(out + ".txt", "w", encoding="utf-8") as f:
        f.write("\n".join(txt) + "\n")


if __name__ == "__main__":
    main()
