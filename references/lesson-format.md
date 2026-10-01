# Lesson format

One lesson teaches one tightly-scoped thing. Keep it short enough to finish in one sitting, ideally a few minutes.

## Shape

1. **Intro screen.** Two sentences max, one small code sample, and the mascot line. Then Start. No lecture.
2. **Question screens.** Five to eight, rotating the types below. Each screen teaches the smallest piece it needs, then asks about it.
3. **Final screen.** Trophy, total XP, missed questions as a review list, Retry.

## Question types

- `pick`: multiple choice. One correct option plus three distractors built from bugs the learner actually writes.
- `predict`: given code, ask what prints, where the value lives, or what leaks.
- `spot`: ask which line leaks, dangles, or double-frees. Highlight that line with `.hl`.
- `build`: assemble the fix from word blocks in the token bank. The learner taps tokens in order.
- `truefalse`: one sharp invariant, for example "After `delete p`, `p` still holds an address."

## Rules

- The prompt is one sentence. Add code or a diagram only when the question needs it.
- Every question carries a 1-2 sentence explanation of the concrete mechanism. State what actually happens, not an analogy.
- Distractors come from real misconceptions. Never write trivia.
- Quiz the mechanism that causes bugs, not the name of a syntax detail.
- Each option should be the same number of words, and the same number of characters if you can. Formatting must not leak the answer.
- Teaching happens before testing. Teach the knowledge the question needs inside that screen, then ask.
- Follow the design system in [duo-design.md](duo-design.md). Do not vary it per topic.

## Spacing over time

Number sequentially and check the existing files before writing:

```text
lessons/
  0001-stack-vs-heap.html
  0002-pointers-and-dereference.html
```

Each lesson links to the next one and to relevant files in `reference/`. Recommend one primary source. End with a line telling the learner to ask the agent about anything unclear.

## When the mission is unclear

If `MISSION.md` is missing or vague, question the user about their reason before writing a lesson. Lessons grounded in a real goal land far better, and the mission is what tells you what to teach next.