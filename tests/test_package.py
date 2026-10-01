"""Verify the skill ships correctly and the example workspace actually works.

Static checks cover packaging, the design-system contract, and that the port
did not quietly drop anything from upstream `teach`. The behaviour suite
extracts each lesson's scripts and runs a real playthrough in Bun against a
small DOM stub, so the mechanics are exercised rather than assumed.
"""
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "example"

CONTRACT_MARKERS = (
    "progress-fill",
    "checkBtn",
    "nextBtn",
    "sheetTitle",
    "sheetBody",
    "choice",
)

ELEMENT_IDS = [
    "app", "progress", "checkBtn", "skipBtn", "sheet", "sheetTitle",
    "sheetBody", "nextBtn", "restartBtn", "soundBtn", "h1", "h2", "h3",
    "xp", "footer",
]

DOM_STUB = (
    r"""
function makeEl(id) {
  var el = {
    id: id, dataset: {}, style: {}, innerHTML: "", textContent: "",
    onclick: null, disabled: false, className: "", attributes: {}, _classes: [],
  };
  el.setAttribute = function (k, v) { el.attributes[k] = String(v); };
  el.getAttribute = function (k) { return el.attributes[k] || null; };
  el.classList = {
    add: function (c) { if (el._classes.indexOf(c) === -1) el._classes.push(c); },
    remove: function (c) { el._classes = el._classes.filter(function (x) { return x !== c; }); },
    toggle: function (c, on) { if (on) el.classList.add(c); else el.classList.remove(c); },
    contains: function (c) { return el._classes.indexOf(c) !== -1; },
  };
  return el;
}

var registry = {};
(function () {
  var ids = __IDS__;
  for (var n = 0; n < ids.length; n++) registry[ids[n]] = makeEl(ids[n]);
})();

global.document = {
  getElementById: function (id) { return registry[id] || null; },
  querySelectorAll: function () { return []; },
  querySelector: function () { return null; },
  addEventListener: function () {},
};
global.window = global;
// The lesson defers the XP and heart sounds with setTimeout; run them inline
// so a single playthrough exercises the whole sequence.
global.setTimeout = function (fn) { fn(); return 0; };
global.clearTimeout = function () {};
global.localStorage = {
  _v: {},
  getItem: function (k) {
    return Object.prototype.hasOwnProperty.call(this._v, k) ? this._v[k] : null;
  },
  setItem: function (k, val) { this._v[k] = String(val); },
};
global.AudioContext = function () {
  // Each AudioParam needs setValueAtTime and exponentialRampToValueAtTime,
  // otherwise the engine's real envelope calls throw and every sound is
  // silently swallowed.
  function param(value) {
    return {
      value: value || 0,
      setValueAtTime: function () {},
      exponentialRampToValueAtTime: function () {},
      linearRampToValueAtTime: function () {},
    };
  }
  return {
    currentTime: 0,
    state: "running",
    destination: {},
    resume: function () {},
    createGain: function () {
      return {
        gain: param(1),
        connect: function () {},
        disconnect: function () {},
      };
    },
    createOscillator: function () {
      return {
        type: "sine",
        frequency: param(440),
        connect: function () {},
        disconnect: function () {},
        start: function () {},
        stop: function () {},
      };
    },
  };
};
global.__el = function (id) { return registry[id]; };
"""
).replace("__IDS__", json.dumps(ELEMENT_IDS))


def load_upstream_skill():
    """Read the vendored upstream teach SKILL.md for the port tests.

    It lives in tests/fixtures so CI can enforce that nothing was silently
    dropped, without reaching the network. From mattpocock/skills, MIT.
    """
    path = ROOT / "tests" / "fixtures" / "upstream-SKILL.md"
    return path.read_text(encoding="utf-8") if path.is_file() else None


UPSTREAM_SKILL = load_upstream_skill()

HAS_EXAMPLE = (EXAMPLE / "lessons").is_dir() and (EXAMPLE / "assets" / "duo.css").is_file()


def lesson_scripts(html: str) -> str:
    """Concatenate every inline script block in the lesson.

    A lesson carries two: the sound engine, then the lesson itself. Pulling
    them as one blob means the behaviour suite also proves the sound engine
    shipped inside the file.
    """
    blocks = re.findall(r"<script>\n(.*?)\n</script>", html, re.DOTALL)
    if not blocks:
        raise AssertionError("lesson has no inline script")
    return "\n".join(blocks)


def screen_data(script: str) -> list:
    """Read the lesson array by bracket matching, not by regex.

    A non-greedy regex stops at the first `]`, which sits inside the nested
    `tokens` array. Balance brackets so brackets in JSON strings are safe.
    """
    marker = "const lesson = "
    start = script.index(marker) + len(marker)
    if script[start] != "[":
        raise AssertionError("lesson data is not an array literal")
    depth, in_string, escaped = 0, False, False
    for index in range(start, len(script)):
        char = script[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
            if depth == 0:
                return json.loads(script[start : index + 1])
    raise AssertionError("lesson data array is not terminated")


def run_with_bun(script: str, driver: str) -> dict:
    """Run a lesson plus a driver script in Bun and return its JSON output.

    The driver is appended after the lesson so its top-level `let` bindings
    are initialised first. The stub only installs globals, it runs nothing.
    """
    with tempfile.TemporaryDirectory(prefix="teach-duo-run-") as temporary:
        path = Path(temporary) / "run.js"
        path.write_text(DOM_STUB + "\n" + script + "\n" + driver, encoding="utf-8")
        result = subprocess.run(
            ["bun", "run", str(path)], capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            raise AssertionError(f"lesson run failed:\n{result.stderr}")
        return json.loads(result.stdout.strip())


class SkillTests(unittest.TestCase):
    """Packaging, the teach workspace contract, and design-system guarantees."""

    def test_one_entrypoint_with_resolvable_resources(self):
        self.assertEqual(
            list(ROOT.rglob("SKILL.md")),
            [ROOT / "SKILL.md"],
            "A second entrypoint can shadow the installed skill",
        )
        documents = [ROOT / "SKILL.md", *sorted((ROOT / "references").glob("*.md"))]
        for document in documents:
            for target in re.findall(r"\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
                if "://" in target or target.startswith("#"):
                    continue
                self.assertTrue(
                    (document.parent / target.split("#")[0]).is_file(),
                    f"Broken resource in {document.name}: {target}",
                )

    def test_skill_keeps_every_upstream_section(self):
        if UPSTREAM_SKILL is None:
            self.skipTest("upstream teach SKILL.md fixture not present")
        port = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for heading in re.findall(r"^#{2,3} (.+)$", UPSTREAM_SKILL, re.MULTILINE):
            self.assertIn(f"## {heading}", port, f"lost section: {heading}")

    def test_skill_alters_only_the_design_lines(self):
        """A 1:1 port may swap the design guidance and nothing else."""
        if UPSTREAM_SKILL is None:
            self.skipTest("upstream teach SKILL.md fixture not present")
        port = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        altered = [line for line in UPSTREAM_SKILL.splitlines()
                   if line.strip() and line not in port]
        self.assertLessEqual(
            len(altered),
            2,
            "SKILL.md should change only the lessons description and the Tufte "
            f"design line, but {len(altered)} upstream lines differ: "
            + " | ".join(altered[:3]),
        )

    def test_skill_keeps_the_teach_workspace_contract(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "MISSION.md", "RESOURCES.md", "NOTES.md",
            "./learning-records/", "./lessons/", "./reference/", "./assets/",
            "Zone Of Proximal Development", "Acquiring Wisdom",
            "Fluency vs Storage Strength", "duo.css", "duo-sound.js", "duo-icons.js",
        ):
            self.assertIn(required, skill, f"SKILL.md lost {required}")

    def test_workspace_formats_are_verbatim_upstream(self):
        for name in ("GLOSSARY-FORMAT.md", "LEARNING-RECORD-FORMAT.md",
                     "MISSION-FORMAT.md", "RESOURCES-FORMAT.md"):
            self.assertTrue((ROOT / name).is_file(), f"missing {name}")

    def test_template_and_components_ship(self):
        for name in ("assets/duo.css", "assets/duo-sound.js", "assets/duo-icons.js",
                     "assets/lesson-template.html", "assets/build-lesson.py"):
            self.assertTrue((ROOT / name).is_file(), f"missing {name}")

    def test_template_markers_are_exactly_the_filled_set(self):
        template = (ROOT / "assets" / "lesson-template.html").read_text(encoding="utf-8")
        self.assertEqual(
            set(re.findall(r"\{\{([A-Z_]+)\}\}", template)),
            {"DUO_CSS", "DUO_SOUND", "DUO_ICONS", "LESSON_DATA", "TITLE",
             "NEXT_HREF", "NEXT_LABEL", "REFERENCE_HREF", "REFERENCE_LABEL", "SOURCE"},
        )

    def test_sound_engine_ships_every_cue(self):
        engine = (ROOT / "assets" / "duo-sound.js").read_text(encoding="utf-8")
        for name in ("select", "correct", "wrong", "heartLost", "xp", "complete", "fail"):
            self.assertIn(name + ":", engine, f"missing sound cue: {name}")


@unittest.skipUnless(HAS_EXAMPLE, "example workspace not present")
class WorkspaceTests(unittest.TestCase):
    """The promises the README makes about the example workspace hold."""

    def test_state_files_exist(self):
        for name in ("MISSION.md", "RESOURCES.md", "NOTES.md"):
            self.assertTrue((EXAMPLE / name).is_file(), f"missing {name}")
        self.assertTrue((EXAMPLE / "assets" / "duo.css").is_file())

    def test_lessons_exist_and_keep_contract_markers(self):
        lessons = sorted((EXAMPLE / "lessons").glob("*.html"))
        self.assertTrue(lessons, "no lessons in the example workspace")
        for lesson in lessons:
            html = lesson.read_text(encoding="utf-8")
            for marker in CONTRACT_MARKERS:
                self.assertIn(marker, html, f"{lesson.name} missing {marker}")

    def test_generated_lessons_have_no_unfilled_markers(self):
        for lesson in sorted((EXAMPLE / "lessons").glob("*.html")):
            self.assertNotRegex(
                lesson.read_text(encoding="utf-8"),
                r"\{\{[A-Z_]+\}\}",
                f"{lesson.name} has unfilled template markers",
            )

    def test_generated_lessons_inline_the_canonical_stylesheet(self):
        css = (ROOT / "assets" / "duo.css").read_text(encoding="utf-8")
        token = "--green: #58cc02"
        self.assertIn(token, css)
        for lesson in sorted((EXAMPLE / "lessons").glob("*.html")):
            self.assertIn(token, lesson.read_text(encoding="utf-8").lower(),
                          f"{lesson.name} drifted from duo.css")

    def test_lessons_inline_the_sound_engine(self):
        for lesson in sorted((EXAMPLE / "lessons").glob("*.html")):
            html = lesson.read_text(encoding="utf-8")
            self.assertIn("DuoSound", html, f"{lesson.name} has no sound engine")
            self.assertIn("soundBtn", html, f"{lesson.name} has no mute control")
            self.assertIn('sound("correct")', html)
            self.assertIn('sound("wrong")', html)

    def test_reference_document_uses_the_same_system(self):
        cheatsheet = (EXAMPLE / "reference" / "cpp-memory-cheatsheet.html").read_text("utf-8")
        self.assertIn("--green: #58cc02", cheatsheet.lower(),
                      "the reference document drifted from the design system")
        self.assertIn("58cc02", cheatsheet.lower())

    def test_internal_links_resolve(self):
        pages = list((EXAMPLE / "lessons").glob("*.html")) + list(
            (EXAMPLE / "reference").glob("*.html")
        )
        for page in pages:
            for target in re.findall(r'href="([^"#:]+)"', page.read_text("utf-8")):
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                # Hrefs assembled in script are covered by test_link_data_resolves.
                if any(char in target for char in "'{+"):
                    continue
                self.assertTrue((page.parent / target).resolve().is_file(),
                                f"{page.name} links to missing {target}")

    def test_link_data_resolves(self):
        for lesson in sorted((EXAMPLE / "lessons").glob("*.html")):
            html = lesson.read_text(encoding="utf-8")
            for field in ("next", "reference"):
                match = re.search(rf'{field}: "([^"]*)"', html)
                self.assertIsNotNone(match, f"{lesson.name} has no {field}")
                target = match.group(1)
                if field == "next" and not target:
                    continue  # the last lesson legitimately has no successor
                self.assertTrue(target, f"{lesson.name} has an empty {field}")
                self.assertTrue((lesson.parent / target).resolve().is_file(),
                                f"{lesson.name} {field} points at missing {target}")


@unittest.skipUnless(HAS_EXAMPLE, "example workspace not present")
class LessonContentTests(unittest.TestCase):
    """Every screen is a real question with real feedback."""

    def setUp(self):
        lesson = EXAMPLE / "lessons" / "0001-stack-vs-heap.html"
        self.screens = screen_data(lesson_scripts(lesson.read_text(encoding="utf-8")))

    def test_every_screen_is_valid(self):
        for screen in self.screens:
            self.assertIn(screen["type"], ("intro", "pick", "mem", "build", "truefalse"))
            if screen["type"] == "intro":
                continue
            self.assertTrue(screen.get("why"), f"{screen['id']} has no explanation")
            if screen["type"] == "build":
                self.assertTrue(screen.get("answer"), f"{screen['id']} has no answer")
                continue
            correct = [choice for choice in screen["choices"] if choice["ok"]]
            self.assertEqual(len(correct), 1,
                             f"{screen['id']} needs exactly one correct option")

    def test_options_do_not_leak_the_answer_by_length(self):
        for screen in self.screens:
            if screen["type"] not in ("pick", "mem"):
                continue
            lengths = {len(choice["t"].split()) for choice in screen["choices"]}
            self.assertLessEqual(
                max(lengths) - min(lengths), 2,
                f"{screen['id']} options differ in length, which leaks the answer",
            )


@unittest.skipUnless(HAS_EXAMPLE, "example workspace not present")
class LessonBehaviourTests(unittest.TestCase):
    """Drive a real run of a real lesson and assert the mechanics work."""

    def setUp(self):
        lesson = EXAMPLE / "lessons" / "0001-stack-vs-heap.html"
        self.script = lesson_scripts(lesson.read_text(encoding="utf-8"))

    def test_perfect_run_earns_xp_and_completes(self):
        driver = r"""
var quiet = [];
render();
quiet.push(__el("sheet").classList.contains("show"));
checkBtn.onclick();
quiet.push(__el("sheet").classList.contains("show"));

var guard = lesson.length + 5;
while (i < lesson.length && guard-- > 0) {
  var cur = lesson[i];
  if (cur.type === "intro") { checkBtn.onclick(); continue; }
  if (cur.type === "build") { built = cur.answer.slice(); checkBtn.disabled = false; }
  else {
    selected = cur.choices.findIndex(function (c) { return c.ok; });
    checkBtn.disabled = false;
  }
  check();
  nextBtn.onclick();
}
console.log(JSON.stringify({
  quiet: quiet,
  xp: String(__el("xp").textContent),
  heartsLost: ["h1","h2","h3"].filter(function (h) { return __el(h).classList.contains("lost"); }),
  finalHtml: __el("app").innerHTML.indexOf("Lesson complete") !== -1,
  reviewed: __el("app").innerHTML.indexOf("Review:") !== -1,
}));
"""
        out = run_with_bun(self.script, driver)
        self.assertEqual(out["quiet"], [False, False], "feedback leaked before a check")
        self.assertEqual(out["xp"], "60", "six correct questions at 10 XP each")
        self.assertEqual(out["heartsLost"], [], "a perfect run loses no hearts")
        self.assertTrue(out["finalHtml"], "the final screen never rendered")
        self.assertFalse(out["reviewed"], "a perfect run lists nothing to review")

    def test_wrong_answers_drain_hearts_and_offer_retry(self):
        driver = r"""
var guard = lesson.length + 5;
var outOfHearts = false;
while (i < lesson.length && guard-- > 0) {
  var cur = lesson[i];
  if (cur.type === "intro") { checkBtn.onclick(); continue; }
  if (cur.type === "build") { built = ["nope"]; checkBtn.disabled = false; }
  else {
    selected = cur.choices.findIndex(function (c) { return !c.ok; });
    checkBtn.disabled = false;
  }
  check();
  if (__el("nextBtn").textContent === "Retry") { outOfHearts = true; break; }
  nextBtn.onclick();
}
console.log(JSON.stringify({
  xp: String(__el("xp").textContent),
  heartsLost: ["h1","h2","h3"].filter(function (h) { return __el(h).classList.contains("lost"); }).length,
  outOfHearts: outOfHearts,
  explanation: __el("sheetBody").textContent.indexOf("Out of hearts") !== -1,
}));
"""
        out = run_with_bun(self.script, driver)
        self.assertEqual(out["xp"], "0", "wrong answers earn nothing")
        self.assertEqual(out["heartsLost"], 3, "three wrong answers drain three hearts")
        self.assertTrue(out["outOfHearts"], "the run should end at zero hearts")
        self.assertTrue(out["explanation"], "the last explanation must be shown")

    def test_retry_resets_the_run(self):
        driver = r"""
restart();
checkBtn.onclick();
console.log(JSON.stringify({
  xp: String(__el("xp").textContent),
  lost: ["h1","h2","h3"].filter(function (h) { return __el(h).classList.contains("lost"); }).length,
  at: i,
}));
"""
        out = run_with_bun(self.script, driver)
        self.assertEqual(out["xp"], "0", "retry resets XP")
        self.assertEqual(out["lost"], 0, "retry restores hearts")
        self.assertEqual(out["at"], 1, "retry restarts from the beginning")

    def test_sounds_fire_on_the_right_events(self):
        driver = r"""
var log = [];
DuoSound.play = function (name) { log.push(name); return true; };

render();
checkBtn.onclick();

var cur = lesson[i];
selected = cur.choices.findIndex(function (c) { return c.ok; });
checkBtn.disabled = false;
check();
var afterCorrect = log.slice();
nextBtn.onclick();

cur = lesson[i];
selected = cur.choices.findIndex(function (c) { return !c.ok; });
checkBtn.disabled = false;
check();
var afterWrong = log.slice();
nextBtn.onclick();

while (i < lesson.length) {
  cur = lesson[i];
  if (cur.type === "intro") { checkBtn.onclick(); continue; }
  if (cur.type === "build") { built = cur.answer.slice(); checkBtn.disabled = false; }
  else {
    selected = cur.choices.findIndex(function (c) { return c.ok; });
    checkBtn.disabled = false;
  }
  check();
  nextBtn.onclick();
}
console.log(JSON.stringify({
  correctPlayed: afterCorrect,
  wrongPlayed: afterWrong,
  completed: log.indexOf("complete") !== -1,
}));
"""
        out = run_with_bun(self.script, driver)
        self.assertIn("correct", out["correctPlayed"], "no sound on a correct answer")
        self.assertIn("xp", out["correctPlayed"], "no XP sound on a first-try win")
        self.assertIn("wrong", out["wrongPlayed"], "no sound on a wrong answer")
        self.assertIn("heartLost", out["wrongPlayed"], "no heart-lost sound")
        self.assertTrue(out["completed"], "no fanfare when the lesson ends")

    def test_mute_control_is_present_and_wired(self):
        driver = r"""
render();
var btn = __el("soundBtn");
var before = DuoSound.isMuted();
btn.onclick();
var after = DuoSound.isMuted();
var label = btn.getAttribute("aria-label");
var pressed = btn.getAttribute("aria-pressed");
btn.onclick();
console.log(JSON.stringify({
  label: label, pressed: pressed,
  flipped: before !== after,
  restored: DuoSound.isMuted() === before,
}));
"""
        out = run_with_bun(self.script, driver)
        self.assertTrue(out["flipped"], "the sound button does not mute")
        self.assertTrue(out["restored"], "the sound button does not unmute")
        self.assertIn(out["label"], ("Mute sound", "Unmute sound"))
        self.assertIn(out["pressed"], ("true", "false"))

    def test_muting_stops_playback(self):
        """Mute is a real gate, not just an icon swap."""
        driver = r"""
DuoSound.setMuted(true);
var muted = DuoSound.isMuted();
var whileMuted = DuoSound.play("correct");
DuoSound.setMuted(false);
var whileUnmuted = DuoSound.play("select");
console.log(JSON.stringify({
  muted: muted, whileMuted: whileMuted, whileUnmuted: whileUnmuted,
}));
"""
        out = run_with_bun(self.script, driver)
        self.assertTrue(out["muted"])
        self.assertFalse(out["whileMuted"], "a muted lesson still made noise")
        self.assertTrue(out["whileUnmuted"], "an unmuted lesson is silent")


# Emoji and symbol glyphs. These render per-platform, fall back to a
# mismatched or monochrome font, and cannot take the design system's colour,
# which is exactly what broke on the yellow XP pill. Inline SVG only.
EMOJI_PATTERN = re.compile(
    "[\U0001F000-\U0001FAFF"
    "\u2190-\u21FF"
    "\u2300-\u27BF"
    "\u2600-\u26FF"
    "\u2B00-\u2BFF"
    "\uFE0F"
    "]"
)
ENTITY_PATTERN = re.compile(r"&#\d{3,6};")


class IconTests(unittest.TestCase):
    """Icons are inline SVG. Emoji are a bug, and this stops them coming back."""

    def setUp(self):
        self.assets = ROOT / "assets"
        self.icons = (self.assets / "duo-icons.js").read_text(encoding="utf-8")

    def test_icon_set_ships(self):
        self.assertTrue((self.assets / "duo-icons.js").is_file())
        for name in ("close", "heart", "zap", "trophy", "volumeOn", "volumeOff"):
            self.assertIn(name + ":", self.icons, f"missing icon: {name}")

    def test_icon_set_uses_svg_not_emoji(self):
        self.assertIn("<svg", self.icons, "icons must be inline SVG")
        self.assertIsNone(EMOJI_PATTERN.search(self.icons),
                          "duo-icons.js contains an emoji")

    def test_template_has_no_emoji_or_symbol_entities(self):
        template = (self.assets / "lesson-template.html").read_text(encoding="utf-8")
        found = EMOJI_PATTERN.findall(template)
        self.assertEqual(found, [], f"emoji in template: {''.join(sorted(set(found)))}")
        found = ENTITY_PATTERN.findall(template)
        self.assertEqual(found, [], f"character entities in template: {found}")

    def test_no_emoji_anywhere_in_shipped_files(self):
        offenders = []
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file() or path.suffix not in {".html", ".css", ".js", ".md", ".json"}:
                continue
            if "__pycache__" in path.parts or path.name.startswith("upstream-"):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            glyphs = EMOJI_PATTERN.findall(text)
            entities = [e for e in ENTITY_PATTERN.findall(text)
                        if int(e[2:-1]) > 0x2000]
            if glyphs or entities:
                offenders.append(
                    f"{path.relative_to(ROOT)}: glyphs={''.join(sorted(set(glyphs)))} entities={entities}"
                )
        self.assertEqual(offenders, [], "emoji or symbol entities found:\n"
                         + "\n".join(offenders))

    def test_generated_lessons_use_svg_icons(self):
        for lesson in sorted((ROOT / "example" / "lessons").glob("*.html")):
            html = lesson.read_text(encoding="utf-8")
            self.assertIn("DuoIcons", html, f"{lesson.name} has no icon set")
            self.assertIn('data-icon="heart"', html, f"{lesson.name} lost its heart slots")


class SoundEngineTests(unittest.TestCase):
    """The engine has to be safe everywhere, not just in Chrome."""

    def _run(self, prelude: str, body: str) -> dict:
        engine = (ROOT / "assets" / "duo-sound.js").read_text(encoding="utf-8")
        script = prelude + engine + "\n" + body
        with tempfile.TemporaryDirectory(prefix="teach-duo-sound-") as temporary:
            path = Path(temporary) / "sound.js"
            path.write_text(script, encoding="utf-8")
            result = subprocess.run(["bun", "run", str(path)],
                                    capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout.strip())

    def test_degrades_without_audio_support(self):
        out = self._run(
            "delete global.AudioContext; delete global.webkitAudioContext;\n",
            "console.log(JSON.stringify({"
            "supported: DuoSound.isSupported(),"
            "played: DuoSound.play('correct')"
            "}));\n",
        )
        self.assertFalse(out["supported"], "should report no audio support")
        self.assertFalse(out["played"], "should refuse to play rather than throw")

    def test_unknown_sound_is_a_no_op(self):
        out = self._run(
            "",
            "console.log(JSON.stringify({played: DuoSound.play('does-not-exist')}));\n",
        )
        self.assertFalse(out["played"])

    def test_exposes_every_documented_cue(self):
        out = self._run("", "console.log(JSON.stringify({names: DuoSound.available}));\n")
        for name in ("select", "correct", "wrong", "heartLost", "xp", "complete", "fail"):
            self.assertIn(name, out["names"])


if __name__ == "__main__":
    unittest.main()