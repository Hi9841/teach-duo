# Live lesson session

Use [scripts/lesson.py](../scripts/lesson.py), resolved from the directory that contains the loaded `SKILL.md`. It is one Python 3.10+ standard-library helper. No packages. The page it writes is the lesson. Do not hand-write lesson HTML.

## Build

Write the lesson JSON in the teaching workspace, then:

```text
python <skill-directory>/scripts/lesson.py build <data.json> <lessons/NNNN-name.html> --wait
```

Number from the highest existing lesson. Run it in the background. The helper prints a short status on stdout:

```text
status: "wrote"
path: "<absolute output path>"
screens: "7"
```

`--wait` serves the workspace on `127.0.0.1`, opens the lesson there, and prints `status: "waiting"` with the URL. When the learner presses Next after a run with no skips, it prints the result and exits 0:

```text
status: "done"
lesson: "<title>"
xp: "40"
misses: "[\"<question title>\"]"
answers: "[{\"question\": \"<title>\", \"answer\": \"<what they wrote>\", \"graded\": \"got it\"}]"
```

That exit is your cue. `answers` has one entry for each graded `write` attempt. The learner graded it, so check it yourself. Write the learning record if they earned one, then build the next lesson with `--wait`. Use `--open` instead to only open the file.

It refuses emoji, an unknown screen type, uneven options, a missing explanation, a `write` screen without a model answer or points, and any output path inside the skill directory. A bad lesson exits 1 with `status: "error"`. Fix the JSON and run the command again. Do not patch the generated HTML.

## Lesson JSON

```json
{
  "title": "Stack, heap, and who deletes",
  "reference": "../reference/memory.html",
  "referenceLabel": "Memory cheatsheet",
  "source": {"label": "cppreference: new and delete", "url": "https://example.com"},
  "screens": [
    {"type": "intro", "title": "Stack is automatic. Heap is manual.", "text": "Two sentences.", "code": "int x = 5;", "cta": "Start"},
    {"type": "pick", "title": "Where does score live?", "choices": [{"t": "On the stack", "ok": true}, {"t": "On the heap", "ok": false}], "why": "A local dies when the function returns."},
    {"type": "write", "title": "Free the buffer from line 1.", "file": "main.cpp", "code": "int* buf = new int[n];\nuse(buf);", "answer": "delete[] buf;", "points": ["Uses delete[], not delete", "Frees buf exactly once"], "why": "An array from new[] must go back through delete[]."}
  ]
}
```

The first screen is `intro` or `info`. Later screens are `info`, `pick`, `truefalse`, `mem`, or `write`. Interleave `info` concept screens with retrieval questions. Read [design.md](design.md) before writing them.

## Reference page

```text
python <skill-directory>/scripts/lesson.py reference <fragment.html> <reference/name.html> --title "Name"
```

The fragment is inner HTML only. The helper supplies the stylesheet from `assets/lesson.html`.

## Check

```text
python -B -m unittest discover -s tests -v
```

Unit tests do not open a browser. Open a generated lesson before treating a layout change as done.
