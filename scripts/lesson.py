"""Stamp a lesson into the bundled page. Python 3.10+, standard library only."""
import sys

if __name__ == "__main__" and sys.argv[1:] in (["--version"], ["-v"], ["-V"]):
    print("1.0.0")
    raise SystemExit(0)

import argparse
import json
import re
import threading
import time
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "assets" / "lesson.html"
TYPES = {"intro", "info", "pick", "mem", "write", "truefalse"}
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
    if screens[0].get("type") not in ("intro", "info"):
        raise ValueError("the first screen must be an intro or info screen")
    source = pack.get("source")
    if source is not None:
        if not isinstance(source, dict):
            raise ValueError("source must be an object with label and url")
        for key in ("label", "url"):
            if not isinstance(source.get(key), str) or not source[key].strip():
                raise ValueError(f"source.{key} is required")
    for field, label in (("reference", "referenceLabel"),):
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
        if kind in ("intro", "info"):
            _need(screen, "text", ident)
            if kind == "intro":
                _need(screen, "cta", ident)
            continue
        _need(screen, "why", ident)
        if kind == "write":
            _need(screen, "answer", ident)
            points = screen.get("points")
            if (not isinstance(points, list) or not 1 <= len(points) <= 4
                    or not all(isinstance(p, str) and p.strip() for p in points)):
                raise ValueError(f"{ident} needs one to four points to check the answer against")
            if screen.get("grade", "agent") not in ("agent", "self"):
                raise ValueError(f"{ident} grade must be agent or self")
            for key in ("starter", "file"):
                if not isinstance(screen.get(key, ""), str):
                    raise ValueError(f"{ident} {key} must be a string")
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


GRADE_TIMEOUT = 300


class _Finish(SimpleHTTPRequestHandler):
    """Serve the workspace. POST /grade waits for the agent's verdict. POST /done carries the result."""

    def _json(self, status, payload):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        if self.path == "/grade":
            self._grade(json.loads(body or b"{}"))
        elif self.path == "/done":
            self.server.result = json.loads(body or b"{}")
            self.send_response(204)
            self.end_headers()
            threading.Thread(target=self.server.shutdown).start()
        else:
            self.send_error(404)

    def _grade(self, request):
        """Hand a written answer to the agent and block until it writes a verdict file."""
        with self.server.lock:
            self.server.grade_count += 1
            ident = self.server.grade_count
        folder = Path(self.server.workspace) / ".grading"
        folder.mkdir(exist_ok=True)
        verdict = folder / f"{ident}.verdict.json"
        verdict.unlink(missing_ok=True)
        report(status="grade", id=str(ident), question=request.get("question", ""),
               answer=request.get("answer", ""), model=request.get("model", ""),
               points=json.dumps(request.get("points", []), ensure_ascii=False),
               reply=f'python lesson.py verdict "{self.server.workspace}" {ident} --ok|--not-yet --feedback "..."')
        deadline = time.monotonic() + GRADE_TIMEOUT
        while time.monotonic() < deadline:
            if verdict.exists():
                self._json(200, json.loads(verdict.read_text(encoding="utf-8")))
                return
            time.sleep(0.5)
        self._json(200, {"timeout": True})

    def log_message(self, *args):
        pass


def wait_for_finish(output):
    """Open the lesson over localhost and block until the learner presses Next."""
    root = output.parent.parent
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(_Finish, directory=str(root)))
    server.result = {}
    server.workspace = str(root)
    server.lock = threading.Lock()
    server.grade_count = 0
    url = f"http://127.0.0.1:{server.server_port}/{output.relative_to(root).as_posix()}"
    report(status="waiting", url=url)
    webbrowser.open(url)
    server.serve_forever()
    server.server_close()
    return server.result


def write_verdict(workspace, ident, ok, feedback):
    folder = Path(workspace) / ".grading"
    folder.mkdir(exist_ok=True)
    (folder / f"{ident}.verdict.json").write_text(
        json.dumps({"ok": ok, "feedback": feedback}, ensure_ascii=False), encoding="utf-8")


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
    build.add_argument("--wait", action="store_true")
    reference = commands.add_parser("reference")
    reference.add_argument("fragment")
    reference.add_argument("output")
    reference.add_argument("--title", required=True)
    verdict = commands.add_parser("verdict")
    verdict.add_argument("workspace")
    verdict.add_argument("id")
    verdict.add_argument("--feedback", default="")
    mark = verdict.add_mutually_exclusive_group(required=True)
    mark.add_argument("--ok", action="store_true")
    mark.add_argument("--not-yet", action="store_true")
    args = parser.parse_args()
    if not args.command:
        report(status="usage", hint="python scripts/lesson.py build <data.json> <output.html>")
        return 2
    try:
        if args.command == "build":
            output, count = build_file(args.data, args.output, args.open and not args.wait)
            report(status="wrote", path=str(output), screens=str(count))
            if args.wait:
                result = wait_for_finish(output)
                report(status="done", lesson=result.get("title", ""), xp=str(result.get("xp", 0)),
                       misses=json.dumps(result.get("misses", []), ensure_ascii=False),
                       answers=json.dumps(result.get("answers", []), ensure_ascii=False))
        elif args.command == "verdict":
            write_verdict(args.workspace, args.id, args.ok, args.feedback)
            report(status="sent", id=args.id, ok=str(args.ok).lower())
        else:
            output = reference_file(args.fragment, args.output, args.title)
            report(status="wrote", path=str(output), kind="reference")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report(status="error", error=str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
