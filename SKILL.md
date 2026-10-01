---
name: teach-duo
description: Teach any concept as short interactive browser lessons in one fixed design. Use when the user wants to learn something over multiple sessions, or asks for teach-duo.
disable-model-invocation: true
---

# Teach Duo

Teach one tightly scoped idea at a time as a browser lesson. The workspace remembers why they are learning and what they already know. You write the lesson content. The bundled helper writes the page.

## Foundations

Knowledge comes from trusted sources. Skills come from short retrieval practice. Wisdom comes from a real community, and you point at one instead of pretending to be it.

Fluency is in-the-moment recall. Storage strength is the goal. Build it with retrieval, spacing, and interleaving. A lesson that feels easy to read and hard to answer is doing it right. Coverage is not learning.

Read [references/workspace.md](references/workspace.md) before creating or editing `MISSION.md`, `RESOURCES.md`, learning records, or a glossary. Read [references/design.md](references/design.md) before writing a lesson. Read [references/live-session.md](references/live-session.md) for the helper commands. Do not invent a second design, a second template, or hand-written lesson HTML.

The helper is [scripts/lesson.py](scripts/lesson.py). It fills [assets/lesson.html](assets/lesson.html). Python 3.10+ and a browser on the same machine. No packages and no CDN.

## Run a session

If there is no clear topic, ask what they want to learn and nothing else. The teaching workspace is their project directory, not this skill.

1. If `MISSION.md` is missing or vague, ask why they want this before teaching. One concrete outcome. Confirm before you change a mission that already exists.
2. Read the workspace: mission, `NOTES.md`, resources, learning records, glossary, and the lessons already there. Take claims from the resources. Do not teach a fact from memory when a source should back it.
3. Pick the next lesson inside their zone of proximal development. Use the mission and the records. Skip what they have already shown they can do. One idea. A few minutes.
4. Write one JSON file and run the helper's `build` command with `--open`. Number from the highest existing lesson. Tell them to finish it in the browser and come back with what was unclear.
5. When they show they can use the idea, write a learning record. Add a glossary term only once they can use it. Write a reference page when the idea is something they will look up later.

Record how they want to be taught in `NOTES.md`.

## Finish

The page already tells them to ask you. After the lesson, answer the unclear part, then decide the next record or the next lesson. Do not start implementation work unless they ask for it.
