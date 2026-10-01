"""The skill stays one helper, and a generated lesson still plays."""
import copy
import importlib.util
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _pick(number):
    return {
        "type": "pick",
        "title": f"Where does value {number} live?",
        "choices": [
            {"t": "On the stack", "ok": True},
            {"t": "On the heap", "ok": False},
            {"t": "In the code", "ok": False},
            {"t": "In the file", "ok": False},
        ],
        "why": "A local variable occupies a stack slot until the function returns.",
    }


FIXTURE = {
    "title": "Locals die on return",
    "source": {"label": "Example source", "url": "https://example.com"},
    "screens": [
        {
            "type": "intro",
            "title": "A local dies when the function returns.",
            "text": "The stack slot is gone after return. A heap cell stays until you free it.",
            "code": "int x = 5;",
            "cta": "Start",
        },
        *[_pick(n) for n in range(1, 7)],
    ],
}

EXPECTED = {
    "SKILL.md",
    "README.md",
    "LICENSE",
    "agents/openai.yaml",
    ".gitignore",
    "scripts/lesson.py",
    "tests/test_lesson.py",
}

RETIRED = (
    "GLOSSARY-FORMAT.md",
    "LEARNING-RECORD-FORMAT.md",
    "MISSION-FORMAT.md",
    "RESOURCES-FORMAT.md",
    "assets/duo.css",
    "assets/duo-sound.js",
    "assets/duo-icons.js",
    "assets/lesson-template.html",
    "assets/build-lesson.py",
    "example",
    "tests/fixtures/upstream-SKILL.md",
    "tests/test_package.py",
    "assets/lesson.html",
    "references/design.md",
    "references/workspace.md",
    "tests/fixtures/stack-vs-heap.json",
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
  function param(value) {
    return {
      value: value || 0,
      setValueAtTime: function () {},
      exponentialRampToValueAtTime: function () {},
      linearRampToValueAtTime: function () {},
    };
  }
  return {
    currentTime: 0, state: "running", destination: {},
    resume: function () {},
    createGain: function () {
      return { gain: param(1), connect: function () {}, disconnect: function () {} };
    },
    createOscillator: function () {
      return {
        type: "sine", frequency: param(440),
        connect: function () {}, disconnect: function () {},
        start: function () {}, stop: function () {},
      };
    },
  };
};
global.__el = function (id) { return registry[id]; };
"""
).replace("__IDS__", json.dumps(ELEMENT_IDS))

EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\u2190-\u21FF\u2300-\u27BF\u2600-\u26FF\u2B00-\u2BFF\uFE0F]"
)


def write_fixture(directory):
    path = Path(directory) / "lesson.json"
    path.write_text(json.dumps(FIXTURE), encoding="utf-8")
    return path


def load_lesson():
    spec = importlib.util.spec_from_file_location("teach_duo_lesson", ROOT / "scripts" / "lesson.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scripts_of(html):
    blocks = re.findall(r"<script>\n(.*?)\n</script>", html, re.DOTALL)
    if len(blocks) < 3:
        raise AssertionError("lesson is missing its inline scripts")
    return blocks


def sound_script(html):
    for block in scripts_of(html):
        if "global.DuoSound" in block:
            return block
    raise AssertionError("sound engine missing")


def screen_data(script):
    marker = "const LESSON = "
    start = script.index(marker) + len(marker)
    while script[start] in " \n":
        start += 1
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
                return json.loads(script[start:index + 1])["screens"]
    raise AssertionError("lesson pack is not terminated")


def run_with_bun(script, driver):
    with tempfile.TemporaryDirectory(prefix="teach-duo-run-") as temporary:
        path = Path(temporary) / "run.js"
        path.write_text(DOM_STUB + "\n" + script + "\n" + driver, encoding="utf-8")
        result = subprocess.run(
            ["bun", "run", str(path)], capture_output=True, text=True, timeout=60
        )
    if result.returncode != 0:
        raise AssertionError(f"lesson run failed:\n{result.stderr}")
    return json.loads(result.stdout.strip())


class PackageTests(unittest.TestCase):
    def test_files_are_the_small_set(self):
        found = {
            path.relative_to(ROOT).as_posix()
            for path in ROOT.rglob("*")
            if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts
        }
        self.assertEqual(found, EXPECTED)

    def test_retired_files_stay_gone(self):
        for name in RETIRED:
            self.assertFalse((ROOT / name).exists(), name)

    def test_one_skill_entrypoint(self):
        self.assertEqual(list(ROOT.rglob("SKILL.md")), [ROOT / "SKILL.md"])

    def test_doc_links_resolve(self):
        documents = [ROOT / "SKILL.md", ROOT / "README.md"]
        for document in documents:
            for target in re.findall(r"\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
                if "://" in target or target.startswith("#"):
                    continue
                self.assertTrue(
                    (document.parent / target.split("#")[0]).is_file(),
                    f"{document.name} -> {target}",
                )

    def test_template_marker_is_only_the_pack(self):
        template = load_lesson().PAGE
        self.assertEqual(set(re.findall(r"\{\{([A-Z_]+)\}\}", template)), {"LESSON_PACK"})
        self.assertIn("--green: #58cc02", template.lower())
        self.assertIn("global.DuoSound", template)
        self.assertIn('data-icon="heart"', template)


class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lesson = load_lesson()
        cls.directory = tempfile.TemporaryDirectory(prefix="teach-duo-out-")
        cls.page = Path(cls.directory.name) / "0001-stack-vs-heap.html"
        cls.lesson.build_file(write_fixture(cls.directory.name), cls.page, False)
        cls.html = cls.page.read_text(encoding="utf-8")
        runtime = "\n".join(scripts_of(cls.html))
        cls.screens = screen_data(runtime)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def test_page_has_no_markers_and_keeps_the_shell(self):
        self.assertNotRegex(self.html, r"\{\{[A-Z_]+\}\}")
        for marker in ("progress-fill", "checkBtn", "soundBtn", "DuoIcons", 'data-icon="heart"'):
            self.assertIn(marker, self.html)

    def test_screens_are_real_questions(self):
        self.assertEqual(self.screens[0]["type"], "intro")
        for screen in self.screens[1:]:
            self.assertTrue(screen.get("why"), screen.get("id"))
            correct = [choice for choice in screen["choices"] if choice["ok"]]
            self.assertEqual(len(correct), 1, screen.get("id"))

    def test_options_do_not_leak_by_length(self):
        for screen in self.screens:
            if "choices" not in screen:
                continue
            lengths = {len(choice["t"].split()) for choice in screen["choices"]}
            self.assertLessEqual(max(lengths) - min(lengths), 2, screen.get("id"))

    def test_highlight_is_a_line_number_not_html(self):
        pack = copy.deepcopy(FIXTURE)
        pack["screens"][1]["code"] = "int a;\nint b;"
        pack["screens"][1]["hl"] = 2
        page = self.lesson.render(self.lesson.validate(pack))
        runtime = "\n".join(scripts_of(page))
        out = run_with_bun(runtime, r"""
console.log(JSON.stringify({html: codeBlock(lesson[1].code, lesson[1].hl)}));
""")
        self.assertIn('<span class="hl">int b;</span>', out["html"])
        self.assertNotIn('<span class="hl">int a;</span>', out["html"])

    def test_uneven_options_are_refused(self):
        pack = copy.deepcopy(FIXTURE)
        pack["screens"][1]["choices"][0]["t"] = "Yes this answer is much longer"
        with self.assertRaises(ValueError):
            self.lesson.validate(pack)

    def test_skill_directory_is_refused(self):
        with self.assertRaises(ValueError):
            self.lesson.build_file(write_fixture(self.directory.name), ROOT / "lessons" / "nope.html", False)

    def test_reference_reuses_the_lesson_stylesheet(self):
        fragment = Path(self.directory.name) / "body.html"
        fragment.write_text("<h2>Stack</h2>\n<p>Locals die on return.</p>\n", encoding="utf-8")
        output = Path(self.directory.name) / "sheet.html"
        self.lesson.reference_file(fragment, output, "Memory")
        page = output.read_text(encoding="utf-8")
        self.assertIn("--green: #58cc02", page.lower())
        self.assertIn("<h2>Stack</h2>", page)
        self.assertNotIn("<script", page.lower())

    def test_reference_rejects_its_own_style(self):
        fragment = Path(self.directory.name) / "bad.html"
        fragment.write_text("<style>body{color:red}</style>", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.lesson.reference_page("Memory", fragment.read_text(encoding="utf-8"))


class BehaviourTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lesson = load_lesson()
        cls.directory = tempfile.TemporaryDirectory(prefix="teach-duo-play-")
        page = Path(cls.directory.name) / "lesson.html"
        lesson.build_file(write_fixture(cls.directory.name), page, False)
        cls.script = "\n".join(scripts_of(page.read_text(encoding="utf-8")))

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def test_perfect_run_earns_xp(self):
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
        self.assertEqual(out["quiet"], [False, False])
        self.assertEqual(out["xp"], "60")
        self.assertEqual(out["heartsLost"], [])
        self.assertTrue(out["finalHtml"])
        self.assertFalse(out["reviewed"])

    def test_wrong_answers_drain_hearts(self):
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
        self.assertEqual(out["xp"], "0")
        self.assertEqual(out["heartsLost"], 3)
        self.assertTrue(out["outOfHearts"])
        self.assertTrue(out["explanation"])

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
        self.assertEqual(out["xp"], "0")
        self.assertEqual(out["lost"], 0)
        self.assertEqual(out["at"], 1)

    def test_sounds_follow_the_outcome(self):
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
console.log(JSON.stringify({ correctPlayed: afterCorrect, wrongPlayed: afterWrong }));
"""
        out = run_with_bun(self.script, driver)
        self.assertIn("correct", out["correctPlayed"])
        self.assertIn("xp", out["correctPlayed"])
        self.assertIn("wrong", out["wrongPlayed"])
        self.assertIn("heartLost", out["wrongPlayed"])

    def test_mute_is_a_gate(self):
        driver = r"""
DuoSound.setMuted(true);
var whileMuted = DuoSound.play("correct");
DuoSound.setMuted(false);
var whileUnmuted = DuoSound.play("select");
console.log(JSON.stringify({ whileMuted: whileMuted, whileUnmuted: whileUnmuted }));
"""
        out = run_with_bun(self.script, driver)
        self.assertFalse(out["whileMuted"])
        self.assertTrue(out["whileUnmuted"])


class SoundTests(unittest.TestCase):
    def _run(self, prelude, body):
        script = prelude + sound_script(load_lesson().PAGE) + "\n" + body
        with tempfile.TemporaryDirectory(prefix="teach-duo-sound-") as temporary:
            path = Path(temporary) / "sound.js"
            path.write_text(script, encoding="utf-8")
            result = subprocess.run(["bun", "run", str(path)], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout.strip())

    def test_degrades_without_audio(self):
        out = self._run(
            "delete global.AudioContext; delete global.webkitAudioContext;\n",
            "console.log(JSON.stringify({supported: DuoSound.isSupported(), played: DuoSound.play('correct')}));\n",
        )
        self.assertFalse(out["supported"])
        self.assertFalse(out["played"])

    def test_unknown_sound_is_silent(self):
        out = self._run("", "console.log(JSON.stringify({played: DuoSound.play('missing')}));\n")
        self.assertFalse(out["played"])

    def test_cues_exist(self):
        out = self._run("", "console.log(JSON.stringify({names: DuoSound.available}));\n")
        for name in ("select", "correct", "wrong", "heartLost", "xp", "complete", "fail"):
            self.assertIn(name, out["names"])


class IconTests(unittest.TestCase):
    def test_no_emoji_in_shipped_text(self):
        offenders = []
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
                continue
            if path.suffix not in {".html", ".md", ".json", ".py", ".yaml"}:
                continue
            glyphs = EMOJI.findall(path.read_text(encoding="utf-8", errors="replace"))
            if glyphs:
                offenders.append(f"{path.name}: {''.join(sorted(set(glyphs)))}")
        self.assertEqual(offenders, [])
