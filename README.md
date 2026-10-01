# Teach Duo

Teach a skill or concept as interactive lessons with immediate feedback. One tightly-scoped idea per lesson, one question per screen, hearts and XP, and a design system that never drifts between lessons.

This is a port of [`teach`](https://github.com/mattpocock/skills/tree/main/skills/productivity/teach) with one change: every lesson and reference document it produces is built in the fixed Duo design system instead of a generic document.

## Install

Using the [Skills CLI](https://github.com/vercel-labs/skills), choose your agent and installation scope:

```bash
pnpm dlx skills add Hi9841/teach-duo
```

Or with Bun:

```bash
bunx skills add Hi9841/teach-duo
```

The repository root is the skill. There is no inner skill folder.

For manual installation, download or clone the repository and put these inside your agent's configured `skills/teach-duo/` directory:

```text
skills/teach-duo/
  SKILL.md
  MISSION-FORMAT.md
  LEARNING-RECORD-FORMAT.md
  RESOURCES-FORMAT.md
  GLOSSARY-FORMAT.md
  agents/openai.yaml
  assets/
    duo.css
    duo-sound.js
    lesson-template.html
    build-lesson.py
  references/
  LICENSE
```

`agents/openai.yaml` supplies Codex display metadata; the workflow itself is agent-neutral.

## Use it

Ask your agent:

> Use teach-duo to teach me C++ memory management.

For agents supporting dollar-prefixed skill invocation, use `$teach-duo`.

The agent turns the current directory into a teaching workspace and works through it across sessions:

| File | Holds |
| --- | --- |
| `MISSION.md` | why the learner wants this, and what success looks like |
| `RESOURCES.md` | trusted sources, annotated, plus a `Gaps` section |
| `NOTES.md` | how they like to be taught |
| `lessons/0001-*.html` | the lessons themselves, one concept each |
| `reference/*.html` | compressed cheat sheets that outlive any single lesson |
| `learning-records/*.md` | what has actually been learned, used to pick the next lesson |
| `assets/` | the shared stylesheet plus any component a later lesson reuses |

Each lesson opens as one HTML file with the same shell: a progress bar, three hearts, an XP counter, one question per screen, immediate feedback on Check, and a final screen listing what to review with a Retry button.

## The example workspace

`example/` is a real, working teaching workspace, not a mock-up. Open it to see the output:

- `example/lessons/0001-stack-vs-heap.html` - six questions on stack vs heap ownership
- `example/lessons/0002-pointers-and-dereference.html` - six questions on `p` versus `*p`
- `example/reference/cpp-memory-cheatsheet.html` - the compressed reference, same design system, prose instead of quiz

## Generating a lesson

`assets/lesson-template.html` is the template. It has exactly nine placeholders, and `assets/build-lesson.py` fills them:

```bash
python assets/build-lesson.py \
  assets/lesson-template.html \
  lessons/0003-smart-pointers.html \
  lesson-data.json
```

The lesson data is a JSON object with `title`, optional `next`, `reference` and `source` links, and a `screens` array. Each screen is `intro`, `pick`, `mem`, `build`, or `truefalse`, with a prompt, optional code or diagram, options, and a short explanation of the mechanism.

The generator inlines `duo.css`, so a generated lesson can never drift from the design system. As a workspace grows past one lesson you can link the shared stylesheet instead and edit it in one place.

## Design system

`assets/duo.css` is the canonical stylesheet and the first component every workspace earns. Fixed tokens: green `#58CC02`, blue `#1CB0F6`, red `#FF4B4B`, yellow `#FFC800`, `#E5E5E5` borders, `#3C3C3C` text. `16px` radius. Shadows are flat 4px bottom borders, never blurred. Nunito at weight 800.

`assets/duo-sound.js` is the canonical feedback engine. Every outcome gets a sound as well as a colour: a rising two-tone for correct, a falling buzz for wrong, a falling tone for a lost heart, an XP blip, a fanfare on completion, and a low groan at zero hearts. Sounds are synthesised with the Web Audio API rather than shipped as audio files, so a lesson stays a single self-contained HTML file with no binary assets. The mute button in the top bar is a real gate and the preference persists.

Every lesson carries the same shell and the same question types, so a workspace looks like one course. See `references/duo-design.md` for the component contract and `references/lesson-format.md` for the question rules, including the requirement that answer options are the same length so formatting cannot leak the answer.

## Relationship to upstream

This is a faithful port of [`teach`](https://github.com/mattpocock/skills/tree/main/skills/productivity/teach). The teaching workspace, philosophy, fluency and storage strength split, zone of proximal development, knowledge versus skills versus wisdom, and the four `*-FORMAT.md` files are carried over unchanged.

Exactly two lines differ, and both are the design substitution:

- The `./lessons/*.html` entry notes that a lesson is an interactive quiz rather than a document.
- The "should be beautiful, think Tufte" line becomes the Duo design system.

`tests/fixtures/upstream-SKILL.md` vendors the upstream file so `SKILL.md` is diffed against it in CI. `test_skill_alters_only_the_design_lines` fails if a third line drifts, and `test_skill_keeps_every_upstream_section` fails if a section goes missing. The port cannot quietly rot.

## Repository structure

```text
README.md
LICENSE
SKILL.md
MISSION-FORMAT.md
LEARNING-RECORD-FORMAT.md
RESOURCES-FORMAT.md
GLOSSARY-FORMAT.md
agents/openai.yaml
assets/
  duo.css                  canonical design system
  duo-sound.js             canonical feedback sounds
  lesson-template.html     lesson shell with nine placeholders
  build-lesson.py          fills the placeholders
  example-stack-vs-heap.json
  example-pointers-and-dereference.json
references/
  duo-design.md            tokens, shell, sound cues, component contract
  lesson-format.md         question types and rules
example/
  MISSION.md
  RESOURCES.md
  NOTES.md
  assets/duo.css
  assets/duo-sound.js
  lessons/0001-stack-vs-heap.html
  lessons/0002-pointers-and-dereference.html
  reference/cpp-memory-cheatsheet.html
  learning-records/
tests/
  fixtures/upstream-SKILL.md
  test_package.py
```

## Verification

```bash
python -B -m unittest discover -s tests -v
```

Twenty-seven tests, standard library plus Bun for the behaviour suite.

Static: single entrypoint, resolvable doc links, every upstream section present, no more than the two intended edits, the template ships exactly the nine placeholders the generator fills, no lesson has unfilled markers or drifted from `duo.css`, every lesson inlines the sound engine and carries a mute control, every internal link resolves, and answer options are not length-biased.

Behaviour: each lesson's scripts are extracted and run in Bun against a small DOM stub. A perfect run earns 60 XP and loses no hearts, and feedback never appears before a check. Three wrong answers drain hearts and offer Retry at zero. Retry resets XP and hearts. Correct answers play `correct` and `xp`, wrong answers play `wrong` and `heartLost`, and finishing plays `complete`. The mute button flips and restores, and a muted lesson makes no sound. With no `AudioContext` at all the engine reports unsupported and refuses to play instead of throwing.

Unit tests do not verify layout, focus order, or screen-reader behaviour. Open a lesson in a real browser before shipping one.

## Credits and license

The teaching workspace, formats, and philosophy are adapted from [Matt Pocock's `teach` skill](https://github.com/mattpocock/skills/tree/main/skills/productivity/teach). The design system, question types, template, and generator are new work here.

[MIT license](LICENSE).