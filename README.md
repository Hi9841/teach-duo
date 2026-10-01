# Teach Duo

Teach one concept at a time as a short browser lesson. Hearts, XP, immediate feedback, and one design that does not change between topics.

One Python file does the work. No framework, no CDN, no third-party packages.

## Install

```bash
bunx skills add Hi9841/teach-duo
```

The repository root is the skill.

```text
skills/teach-duo/
  SKILL.md
  scripts/lesson.py
  agents/openai.yaml
  LICENSE
```

Python 3.10+ and a browser on the same computer as the agent.

## Use it

> Use teach-duo to teach me C++ memory.

1. The agent asks why, if the workspace does not already say.
2. It writes one JSON lesson and runs `scripts/lesson.py build`. The page opens in the browser.
3. Finish the lesson. Come back with what was unclear.

Lessons land in the workspace, not in the skill folder:

```text
MISSION.md
RESOURCES.md
NOTES.md
lessons/0001-name.html
reference/sheet.html
learning-records/0001-what-they-showed.md
```

## Generate a page

```bash
python scripts/lesson.py build lesson.json lessons/0001-name.html --open
python scripts/lesson.py reference fragment.html reference/sheet.html --title "Memory"
```

`build` checks the question shape and writes one HTML file. `reference` wraps prose in the same stylesheet. The helper refuses emoji, uneven options, and a lesson written into the skill directory.

## Verification

```bash
python -B -m unittest discover -s tests -v
```

The tests use the standard library and Bun. They do not open a browser. Before shipping a lesson, open the generated file and run it once.

## Credits and license

The teaching workspace is adapted from [Matt Pocock's teach skill](https://github.com/mattpocock/skills/tree/main/skills/productivity/teach). The lesson shell is the work in this repository. Packaging follows [grill-with-docs-ui](https://github.com/Hi9841/grill-with-docs-ui).

[MIT license](LICENSE).
