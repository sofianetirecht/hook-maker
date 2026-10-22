#!/usr/bin/env python3
"""Hook Maker Studio — assemble la page du studio à partir des fichiers du skill.

La page embarque tes règles, tes modèles de hooks, ta structure de script,
la méthode d'analyse de SKILL.md et tes fiches niches. Relance ce script
(puis republie la page) chaque fois que tu modifies un de ces fichiers.

Usage : build_studio.py [sortie.html]
        (par défaut : analyses/studio/hook-maker-studio.html)
"""
import json
import pathlib
import re
import sys

HM = pathlib.Path(__file__).resolve().parent.parent


def rd(p):
    return (HM / p).read_text(encoding="utf-8")


def main():
    out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HM / "analyses" / "studio" / "hook-maker-studio.html"

    skill = rd("SKILL.md")
    methode = skill.split("## 4. Analyser", 1)[1].split("## 5. Rendre la page", 1)[0].strip()
    schema = re.search(r"```json\n(.*?)```", skill.split("## 5. Rendre la page", 1)[1], re.S).group(1).strip()

    hooks = rd("hooks.md")
    if "## 30 hooks" in hooks:
        hooks = hooks.split("## Transcription du reel")[0] + "## 30 hooks" + hooks.split("## 30 hooks", 1)[1]
    struct = rd("structure-script-video.md")
    if "## Version détaillée" in struct:
        struct = struct.split("## Transcription du reel")[0] + "## Version détaillée" + struct.split("## Version détaillée", 1)[1]

    niches = []
    for f in sorted((HM / "niches").glob("*.md")):
        if f.name.startswith("_"):
            continue
        md = f.read_text(encoding="utf-8")
        nom = md.splitlines()[0].replace("# Niche :", "").lstrip("# ").strip() if md.strip() else f.stem
        niches.append({"nom": nom or f.stem, "md": md})

    kb = {"regles": rd("regles.md"), "hooks": hooks, "structure": struct,
          "methode": methode, "schema": schema, "niches": niches}

    tpl = rd("template/resultat.html")
    exemple = json.loads(re.search(r'id="hm-data">(.*?)</script>', tpl, re.S).group(1))
    css = "\n".join(l for l in tpl.split("</style>", 1)[0].splitlines()
                    if not l.startswith(("<title", '<meta name="claude:viewport')))
    css = css.replace("main .wrap { padding-block: 28px 56px; display: grid; gap: 28px; }",
                      "main .wrap { padding-block: 28px 56px; display: grid; gap: 36px; }")

    def js(o):
        return json.dumps(o, ensure_ascii=False).replace("</", "<\\/")

    body = rd("studio/studio.src.html").replace("/*__KB__*/null", js(kb)).replace("/*__EXEMPLE__*/null", js(exemple))
    body = body.replace('document.querySelectorAll("[data-canal]")', 'document.querySelectorAll("button[data-canal]")')
    html = ('<title>Hook Maker Studio</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
            + css.rstrip() + "\n" + body)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(out)
    print("Niches : " + (", ".join(n["nom"] for n in niches) or "aucune (crée-en une avec /hook-maker)"))


if __name__ == "__main__":
    main()
