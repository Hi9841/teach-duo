"""Stamp a lesson into the bundled page. Python 3.10+, standard library only."""
import sys

if __name__ == "__main__" and sys.argv[1:] in (["--version"], ["-v"], ["-V"]):
    print("1.0.0")
    raise SystemExit(0)

import argparse
import json
import re
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "assets" / "lesson.html"
TYPES = {"intro", "pick", "mem", "build", "truefalse"}
EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\u2190-\u21FF\u2300-\u27BF\u2600-\u26FF\u2B00-\u2BFF\uFE0F]"
)


def quote(value):
    escapes = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"}
    return '"' + "".join(
        escapes.get(char, f"\\u{ord(char):04x}" if ord(char) < 32 else char)
        for char in str(value)
    ) + '"'


def report(**fields):
    print("\n".join(f"{key}: {quote(value)}" for key, value in fields.items()), flush=True)


def _need(screen, key, ident):
    value = screen.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{ident} needs {key}")
    return value


def _choices(screen, ident):
    choices = screen.get("choices")
    if not isinstance(choices, list) or len(choices) < 2:
        raise ValueError(f"{ident} needs at least two choices")
    correct = 0
    lengths = []
    for choice in choices:
        if not isinstance(choice, dict):
            raise ValueError(f"{ident} has a choice that is not an object")
        text = choice.get("t")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"{ident} has an empty choice")
        if not isinstance(choice.get("ok"), bool):
            raise ValueError(f"{ident} choices need an ok boolean")
        correct += choice["ok"]
        lengths.append(len(text.split()))
    if correct != 1:
        raise ValueError(f"{ident} needs exactly one correct choice")
    if max(lengths) - min(lengths) > 2:
        raise ValueError(f"{ident} options differ in length, which leaks the answer")


def validate(pack):
    if not isinstance(pack, dict):
        raise ValueError("lesson file must be one JSON object")
    raw = json.dumps(pack, ensure_ascii=False)
    if EMOJI.search(raw):
        raise ValueError("lesson text contains an emoji or symbol glyph; use the icon set")
    title = pack.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title is required")
    screens = pack.get("screens")
    if not isinstance(screens, list) or not screens:
        raise ValueError("screens must be a non-empty list")
    if screens[0].get("type") != "intro":
        raise ValueError("the first screen must be an intro")
    source = pack.get("source")
    if source is not None:
        if not isinstance(source, dict):
            raise ValueError("source must be an object with label and url")
        for key in ("label", "url"):
            if not isinstance(source.get(key), str) or not source[key].strip():
                raise ValueError(f"source.{key} is required")
    for field, label in (("next", "nextLabel"), ("reference", "referenceLabel")):
        href = pack.get(field) or ""
        text = pack.get(label) or ""
        if bool(href) != bool(text):
            raise ValueError(f"{field} and {label} are set together")
    for index, screen in enumerate(screens):
        if not isinstance(screen, dict):
            raise ValueError(f"screen {index + 1} is not an object")
        kind = screen.get("type")
        ident = screen.get("id") or f"screen {index + 1}"
        if kind not in TYPES:
            raise ValueError(f"{ident} has unknown type {kind}")
        _need(screen, "title", ident)
        if screen.get("hl") is not None and not isinstance(screen.get("hl"), int):
            raise ValueError(f"{ident} hl must be a line number")
        if kind == "intro":
            _need(screen, "text", ident)
            _need(screen, "cta", ident)
            continue
        _need(screen, "why", ident)
        if kind == "build":
            tokens = screen.get("tokens")
            answer = screen.get("answer")
            if not isinstance(tokens, list) or not tokens or not all(isinstance(t, str) for t in tokens):
                raise ValueError(f"{ident} needs a token list")
            if not isinstance(answer, list) or not answer or not all(isinstance(t, str) for t in answer):
                raise ValueError(f"{ident} needs an answer list")
            continue
        _choices(screen, ident)
        if kind == "mem":
            for side in ("stack", "heap"):
                cells = screen.get(side)
                if not isinstance(cells, list) or not cells or not all(isinstance(c, str) for c in cells):
                    raise ValueError(f"{ident} needs {side} cells")
    return pack


def render(pack):
    template = TEMPLATE.read_text(encoding="utf-8")
    meta = {
        "title": pack["title"],
        "next": pack.get("next") or "",
        "nextLabel": pack.get("nextLabel") or "",
        "reference": pack.get("reference") or "",
        "referenceLabel": pack.get("referenceLabel") or "",
        "source": pack.get("source"),
        "screens": pack["screens"],
    }
    blob = json.dumps(meta, indent=2, ensure_ascii=False)
    blob = blob.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    if template.count("{{LESSON_PACK}}") != 1:
        raise ValueError("template must contain LESSON_PACK once")
    page = template.replace("{{LESSON_PACK}}", blob)
    leftovers = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", page)))
    if leftovers:
        raise ValueError("unfilled template markers: " + ", ".join(leftovers))
    return page


def style_block():
    template = TEMPLATE.read_text(encoding="utf-8")
    match = re.search(r"<style>\n(.*)\n</style>", template, re.DOTALL)
    if not match:
        raise ValueError("template has no style block")
    return match.group(1)


def reference_page(title, body):
    if re.search(r"<\s*(script|style|link)\b", body, re.IGNORECASE):
        raise ValueError("reference body is content only; the helper supplies the page")
    safe = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"UTF-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        f"<title>{safe}</title>\n<style>\n{style_block()}\n</style>\n</head>\n"
        "<body class=\"reference\">\n<main class=\"prose\">\n"
        "<p class=\"eyebrow\">Reference</p>\n"
        f"<h1 class=\"q\">{safe}</h1>\n"
        f"{body.rstrip()}\n"
        "</main>\n</body>\n</html>\n"
    )


def _outside_skill(path):
    resolved = path.resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        raise ValueError("write into the teaching workspace, not the skill directory")
    return resolved


def build_file(data_path, output_path, open_page):
    pack = validate(json.loads(Path(data_path).read_text(encoding="utf-8")))
    output = _outside_skill(Path(output_path))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(pack), encoding="utf-8")
    if open_page:
        webbrowser.open(output.as_uri())
    return output, len(pack["screens"])


def reference_file(fragment_path, output_path, title):
    body = Path(fragment_path).read_text(encoding="utf-8")
    output = _outside_skill(Path(output_path))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(reference_page(title, body), encoding="utf-8")
    return output


def main():
    parser = argparse.ArgumentParser(prog="lesson.py", add_help=True)
    commands = parser.add_subparsers(dest="command")
    build = commands.add_parser("build")
    build.add_argument("data")
    build.add_argument("output")
    build.add_argument("--open", action="store_true")
    reference = commands.add_parser("reference")
    reference.add_argument("fragment")
    reference.add_argument("output")
    reference.add_argument("--title", required=True)
    args = parser.parse_args()
    if not args.command:
        report(status="usage", hint="python scripts/lesson.py build <data.json> <output.html>")
        return 2
    try:
        if args.command == "build":
            output, count = build_file(args.data, args.output, args.open)
            report(status="wrote", path=str(output), screens=str(count))
        else:
            output = reference_file(args.fragment, args.output, args.title)
            report(status="wrote", path=str(output), kind="reference")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report(status="error", error=str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
