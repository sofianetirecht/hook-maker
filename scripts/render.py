#!/usr/bin/env python3
"""Hook Maker — injecte les données d'une analyse dans le gabarit HTML.

Usage :
  render.py <data.json> <sortie.html>               page à publier en Artifact
  render.py <data.json> <sortie.html> --standalone  page complète à ouvrir dans un navigateur
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "template" / "resultat.html"
BLOCK = re.compile(r'(<script type="application/json" id="hm-data">)(.*?)(</script>)', re.S)


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__)
    data = json.loads(pathlib.Path(args[0]).read_text(encoding="utf-8"))
    data.pop("exemple", None)
    payload = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")

    html = TEMPLATE.read_text(encoding="utf-8")
    html, n = BLOCK.subn(lambda m: m.group(1) + "\n" + payload + "\n" + m.group(3), html, count=1)
    if n != 1:
        sys.exit("Bloc hm-data introuvable dans le gabarit.")
    titre = (data.get("titre") or "Analyse").replace("<", "").replace(">", "")
    html = html.replace("<title>Hook Maker</title>", f"<title>{titre} · Hook Maker</title>", 1)

    if "--standalone" in sys.argv:
        html = ('<!doctype html><html lang="fr"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
                "</head><body>\n" + html + "\n</body></html>")

    out = pathlib.Path(args[1])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
