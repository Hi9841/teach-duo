---
name: teach-duo
description: Teach any concept as short interactive browser lessons in one fixed design. Use when the user wants to learn something over multiple sessions, or asks for teach-duo.
disable-model-invocation: true
---

# Teach Duo

Teach one tightly scoped idea at a time as a browser lesson. The workspace remembers why they are learning and what they already know. You write the lesson content. [scripts/lesson.py](scripts/lesson.py) writes the page. Python 3.10+ and a browser. No packages, no CDN, no second template.

Knowledge comes from trusted sources. Skills come from short retrieval practice. Wisdom comes from a real community, and you point at one instead of pretending to be it. Fluency is in-the-moment recall. Storage strength is the goal: retrieval, spacing, interleaving. Coverage is not learning.

## Run a session

If there is no clear topic, ask what they want to learn and nothing else. The teaching workspace is their project directory, not this skill.

1. If `MISSION.md` is missing or vague, ask why before teaching. One concrete outcome. Confirm before you change a mission that already exists.
2. Read the mission, `NOTES.md`, resources, learning records, glossary, and lessons already there. Take claims from the resources. Do not teach a fact from memory when a source should back it.
3. Pick the next lesson inside their zone of proximal development. Skip what they have shown they can do. One idea. A few minutes.
4. Write one JSON file and run `python "<skill>/scripts/lesson.py" build <data.json> <lessons/NNNN-name.html> --open`. Number from the highest existing lesson. They finish it in the browser and come back with what was unclear.
5. When they can use the idea, write a learning record. Add a glossary term only then. Write a reference page when they will look the idea up later.

## Workspace

`MISSION.md` is why they are learning. One per workspace. Concrete, under a screen.

```md
# Mission: {Topic}

## Why
{1-3 sentences. What changes when they have this skill?}

## Success looks like
- {A specific thing they will be able to do}

## Constraints
- {Time, prior commitments, how they want to practice}

## Out of scope
- {Adjacent topics they do not want right now}
```

`RESOURCES.md` is the trusted sources. Annotate every entry in one line. Prune a shallow one. If they do not want a community, write that here.

```md
# {Topic} Resources

## Knowledge

- [Title by Author](https://example.com)
  What it covers, and when to reach for it.

## Wisdom (Communities)

- [Forum name](https://example.com)
  What it is good for.

## Gaps

- {Something the mission needs and no good source covers yet}
```

`learning-records/0001-slug.md`, numbered from the highest file. One short record when they demonstrate a non-obvious idea, tell you prior knowledge and its depth, correct a misconception, or shift the mission. Do not record mere coverage. Supersede with `Status: superseded by LR-NNNN`. Do not delete.

`GLOSSARY.md` gets a term only when they can use it. One or two sentences on what it is. List the other names under `_Avoid_`. Revise in place.

`NOTES.md` is how they want to be taught. Not a second mission.

## Lesson file

The helper refuses a page that would leak the answer. Do not hand-write lesson HTML, add a stylesheet, or use emoji. Icons and sound are already in the page.

```json
{
  "title": "Stack, heap, and who deletes",
  "next": "0002-pointers.html",
  "nextLabel": "Next: pointers",
  "reference": "../reference/memory.html",
  "referenceLabel": "Memory cheatsheet",
  "source": {"label": "cppreference: new and delete", "url": "https://example.com"},
  "screens": [
    {"type": "intro", "title": "Stack is automatic. Heap is manual.", "text": "Two sentences.", "code": "int x = 5;", "cta": "Start"},
    {"type": "pick", "title": "Where does score live?", "choices": [{"t": "On the stack", "ok": true}, {"t": "On the heap", "ok": false}], "why": "A local dies when the function returns."}
  ]
}
```

Intro plus five to eight questions. The first screen is an `intro`: title, two sentences in `text`, optional `code`, `cta` such as `Start`. Every later screen has a `why` of one or two sentences about the mechanism.

- `pick`: one correct option and distractors from bugs they actually write.
- `truefalse`: one sharp invariant. Same choice rules as `pick`.
- `mem`: `stack` and `heap` lists of short cell labels. Optional `teach` is one sentence under the diagram. Add one cell at a time.
- `build`: `tokens` in bank order, `answer` in tap order.
- `hl`: a 1-based line number inside `code`. Not HTML.

Options on one screen stay within two words of each other. The prompt is one sentence. Quiz the mechanism that causes the bug. A link needs its label. `source` is the best page you actually found.

The shell is fixed: restart, mute, progress, three hearts, XP, one question, Check, then the feedback sheet. Three hearts. 10 XP for a first-try correct answer. Keys `1`-`4` select, Enter checks, Enter continues. Colours stay green `#58CC02`, blue `#1CB0F6`, red `#FF4B4B`, yellow `#FFC800`. Do not restyle them.

A reference page is prose in the same design. Write the inner HTML only, with code in `<div class="code"><pre>...</pre></div>`, then run `python "<skill>/scripts/lesson.py" reference <fragment.html> <reference/name.html> --title "Name"`. No script, style, or link tags in the fragment.

## Finish

The page already tells them to ask you. Answer the unclear part, then decide the next record or the next lesson. Do not start implementation work unless they ask for it.
