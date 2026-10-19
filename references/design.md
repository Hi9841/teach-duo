# Lesson design

The page is [assets/lesson.html](../assets/lesson.html). You do not restyle it. You fill a JSON file and the helper stamps it in. A learner who opens lesson 0007 should not be able to tell which topic it came from.

## Shell

Top bar, fixed order: restart, mute, progress, three hearts, XP. One question on screen. Check stays disabled until they answer. The feedback sheet is one or two sentences on the mechanism, then Continue. A wrong answer loses a heart, marks only the wrong pick, and the button says Try again. The same question comes back with its choices in a new order, so the learner never repeats the whole lesson for one miss. Zero hearts does not end the run. The last screen shows XP, the misses, the reference, and one primary source. Next lesson is enabled once every question was answered correctly, retries included. It reports to the helper, and the agent writes the next lesson. A skip leaves it disabled, with the line "Answer every question correctly to open the next lesson."

Hearts: 3. First-try correct answers: 10 XP. Keys `1`-`4` select, Enter checks, Enter again continues. A handled key never also clicks the focused button.

Icons are Hugeicons, inline SVG in the template at stroke 2.5. Never emoji. Sound is synthesised in the page. Mute is a real gate and it persists. Do not add audio files or a font CDN. Nunito and Nunito Sans are embedded in the template.

## Tokens

The page is the ShadLingo design system, 1:1: a shadcn theme in style maia with light and dark tokens. The template's `:root` owns the values. Do not restyle per topic.

| Role | Token | Light |
| --- | --- | --- |
| Primary, progress, Check | `--primary` | `oklch(0.585 0.18 139)` |
| Selection, links, outline text | `--spark-blue` | `oklch(0.716 0.135 239)` |
| Error, hearts | `--destructive` | `oklch(0.64 0.22 25)` |
| Correct sheet | `--accent` | `oklch(0.96 0.08 130)` |
| XP | `--chart-3` | `oklch(0.76 0.17 62)` |
| Text | `--foreground` | `oklch(0.3134 0.0687 239.411)` |
| Border, input | `--border` | `oklch(0.86 0.022 239)` |

Type is Nunito, extrabold for buttons, labels, and titles. Buttons and choices use a 16px radius, a 2px border, and a flat 4px edge in the shadow color. Cards use rounded-2xl with a flat 6px border edge. Never use a blur.

## Screens

One idea per lesson. An intro or info screen plus practice questions. Interleave reading with retrieval: present a clear, tight `info` screen to read first, then one or two questions testing that exact mechanism, then the next concept screen. Never dump everything up front.

1. **intro.** Overview for the first screen. Title, two sentences in `text`, optional `code`, and `cta` such as `Start`.
2. **info.** Concept explanation to read before practicing. Title, concise `text`, optional `code`, optional `cta` (`Continue`). Teach one atomic mechanism before quizzing it.
3. **pick.** One correct option and distractors from bugs the learner actually writes. Choices are automatically randomized upon display.
4. **truefalse.** One sharp invariant. Same choice rules as pick. Choices are randomized upon display.
5. **mem.** `stack` and `heap` lists of short cell labels. Optional `teach` is one sentence under the diagram. Add one cell at a time. Choices are randomized upon display.
6. **build.** `tokens` in bank order, `answer` in tap order. Tokens in the bank are randomized upon display so the learner actively assembles them.

`why` is required on question screens. One or two sentences on the mechanism. `hl` is a 1-based line number inside `code`, not HTML. The helper escapes every string.

Options on one screen stay within two words of each other. The prompt is one sentence. Quiz the mechanism that causes the bug. A link needs its label. `source` is the best page you actually found.

## Reference pages

Same tokens, prose instead of a quiz. No hearts and no XP. Write the inner HTML only and let `lesson.py reference` wrap it. Use headings, short paragraphs, tables, and code in `<div class="code"><pre>...</pre></div>`. No script, style, or link tags in the fragment.
