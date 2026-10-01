"""Generate a standalone lesson from assets/lesson-template.html.

The template keeps {{DUO_CSS}} and {{LESSON_DATA}} as the only two things a
generator has to fill in, so a generated lesson can never drift from the Duo
design system or lose the interactive shell.

Usage:
    python build-lesson.py <template.html> <output.html> <data.json>
"""
import json
import re
import sys
from pathlib import Path


def build(template_path: Path, css_path: Path, data_path: Path) -> str:
    template = template_path.read_text(encoding="utf-8")
    css = css_path.read_text(encoding="utf-8").strip()
    sound_path = template_path.parent / "duo-sound.js"
    if not sound_path.is_file():
        raise SystemExit(f"missing sound engine: {sound_path}")
    sound = sound_path.read_text(encoding="utf-8").strip()
    icons_path = template_path.parent / "duo-icons.js"
    if not icons_path.is_file():
        raise SystemExit(f"missing icon set: {icons_path}")
    icons = icons_path.read_text(encoding="utf-8").strip()
    payload = json.loads(data_path.read_text(encoding="utf-8"))

    out = template.replace("{{DUO_CSS}}", css)
    out = out.replace("{{DUO_SOUND}}", sound)
    out = out.replace("{{DUO_ICONS}}", icons)

    meta = {
        "title": payload["title"],
        "next": payload.get("next", ""),
        "nextLabel": payload.get("nextLabel", ""),
        "reference": payload.get("reference", ""),
        "referenceLabel": payload.get("referenceLabel", ""),
        "source": payload.get("source"),
    }
    out = out.replace("{{TITLE}}", meta["title"])
    out = out.replace("{{NEXT_HREF}}", meta["next"])
    out = out.replace("{{NEXT_LABEL}}", meta["nextLabel"])
    out = out.replace("{{REFERENCE_HREF}}", meta["reference"])
    out = out.replace("{{REFERENCE_LABEL}}", meta["referenceLabel"])
    out = out.replace("{{SOURCE}}", json.dumps(meta["source"]))
    out = out.replace(
        "{{LESSON_DATA}}",
        json.dumps(payload["screens"], indent=2, ensure_ascii=False),
    )

    leftovers = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if leftovers:
        raise SystemExit("unfilled template markers: " + ", ".join(sorted(set(leftovers))))
    return out


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    template_path, output_path, data_path = (Path(p) for p in sys.argv[1:])
    css_path = template_path.parent / "duo.css"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build(template_path, css_path, data_path), encoding="utf-8")
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())