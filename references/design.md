# Lesson design

The page is [assets/lesson.html](../assets/lesson.html). You do not restyle it. You fill a JSON file and the helper stamps it in. A learner who opens lesson 0007 should not be able to tell which topic it came from.

## Shell

Top bar, fixed order: restart, mute, progress, three hearts, XP. One question on screen. Check stays disabled until they answer. The feedback sheet is one or two sentences on the mechanism, then Continue. A wrong answer loses a heart and moves on. Zero hearts ends the run with Retry. The last screen shows XP, the misses, the reference, and one primary source. The next lesson is a link only when every question in that run was correct. Any miss or skip leaves it disabled, with the line "Answer every question correctly to open the next lesson."

Hearts: 3. First-try correct answers: 10 XP. Keys `1`-`4` select, Enter checks, Enter again continues.

Icons are inline SVG in the template. Never emoji. Sound is synthesised in the page. Mute is a real gate and it persists. Do not add audio files or a font CDN.

## Tokens

| Role | Value |
| --- | --- |
| Green, primary | `#58CC02` |
| Blue, selection | `#1CB0F6` |
| Red, error | `#FF4B4B` |
| Yellow, XP | `#FFC800` |

Neutrals are border `#E5E5E5`, background `#F7F7F7`, text `#3C3C3C`. Radius is 16px. Shadow is a flat 4px bottom edge, never a blur.

## Screens

One idea per lesson. An intro plus five to eight questions.

1. **intro.** Title, two sentences in `text`, optional `code`, and `cta` such as `Start`. No lecture.
2. **pick.** One correct option and distractors from bugs the learner actually writes.
3. **truefalse.** One sharp invariant. Same choice rules as pick.
4. **mem.** `stack` and `heap` lists of short cell labels. Optional `teach` is one sentence under the diagram. Add one cell at a time.
5. **build.** `tokens` in bank order, `answer` in tap order.

`why` is required after the intro. One or two sentences on the mechanism. `hl` is a 1-based line number inside `code`, not HTML. The helper escapes every string.

Options on one screen stay within two words of each other. The prompt is one sentence. Quiz the mechanism that causes the bug. A link needs its label. `source` is the best page you actually found.

## Reference pages

Same tokens, prose instead of a quiz. No hearts and no XP. Write the inner HTML only and let `lesson.py reference` wrap it. Use headings, short paragraphs, tables, and code in `<div class="code"><pre>...</pre></div>`. No script, style, or link tags in the fragment.
