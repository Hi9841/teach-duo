# Duo design system

Duolingo look built on shadcn structure. This is the fixed design system for every lesson and reference document in a `teach-duo` workspace. The canonical values live in [assets/duo.css](../assets/duo.css). Never improvise them per topic.

## Tokens

| Role | Value | Shadow |
| --- | --- | --- |
| Green, primary action | `#58CC02` | `#58A700` |
| Blue, selection | `#1CB0F6` | `#1899D6` |
| Red, error | `#FF4B4B` | `#D33131` |
| Yellow, XP | `#FFC800` | `#CC9F00` |

Tinted fills: green `#D7FFB8`, blue `#DDF4FF`, red `#FFDFE0`. Neutrals: border `#E5E5E5`, bg `#F7F7F7`, text `#3C3C3C`, muted `#777777`. Code block `#1F2937` with `#111827` bottom edge.

Radius: `16px` for buttons, cards and options. `8px` for the option key badge. `999px` for pills and the progress bar.

Type: Nunito, falling back to system rounded. Headings 800, body 700, supporting text 600. Code is monospace at 15px.

Shadow is a flat bottom border, never a blurred drop shadow. Buttons carry `4px` of it, cards carry `4px`, the option key badge carries `2px`.

## Interactive shell

Every lesson ships the same shell. The learner opens a file and learns, so the shell must not change between topics.

- **Top bar**: an X that restarts, a sound toggle, a progress track with a green fill, three hearts, and an XP counter. Fixed order, fixed positions. Every glyph is inline SVG from `assets/duo-icons.js`.
- **One question per screen.** The question heading is `h1`, the options follow below it. Never two questions on one screen.
- **Bottom bar**: a Check button that stays disabled until the learner selects something. On the intro screen it becomes the start CTA instead.
- **Feedback sheet**: a fixed bottom panel in green-light or red-light, with a heading and a 1-2 sentence explanation of the mechanism, then Continue. Red Continue moves to the next question, not retry in place. One try per question.
- **Final screen**: a trophy, total XP, the questions that were missed as a review list, and Retry.
- **Keyboard**: `1`-`4` select an option, `Enter` checks and then continues. Every interactive element is reachable by keyboard with a visible focus ring.

Progress mechanics: three hearts per run, one lost per wrong answer. `+10` XP per correct first-try answer. Running out of hearts ends the run early with an explanation and the retry path.

## Icons

`assets/duo-icons.js` is the canonical icon set, and every interface glyph is inline SVG.

**Never use emoji.** Emoji render differently on every platform, fall back to a monochrome or colour-mismatched font, and cannot take the tokens from the stylesheet. That is exactly how the lightning bolt ended up as a pale pink glyph on the yellow XP pill. An inline SVG uses `currentColor`, so `--red` or `--yellow-shadow` decides how it looks, on every platform, with no fallback.

Shared geometry is a 24x24 viewBox, a 2px stroke, and round caps and joins, so every icon carries the same optical weight.

| Icon | Use |
| --- | --- |
| `close` | restart in the top bar |
| `volumeOn`, `volumeOff` | the sound toggle |
| `heart` | a life in the top bar |
| `zap` | XP, in the top bar and on the final pill |
| `trophy` | lesson complete |
| `arrowRight` | next lesson or reference on the final screen |
| `external` | the primary source link |

Rules:

- Markup declares the icon by name with `data-icon="heart"`, never by hard-coded glyph. `DuoIcons.hydrate()` fills every slot at load.
- A filled icon sets `fill` on the path so CSS can override it. That is how a spent heart becomes a hollow outline without a second asset.
- Keep icons at `1em` and scale with the font size, so they track the type scale automatically.
- Do not add an icon as a bullet, a separator, or decoration. An icon that carries no meaning is noise.

## Sound

`assets/duo-sound.js` is the canonical feedback engine, and every outcome gets a sound as well as a colour. Sound is the fastest feedback channel a learner has, and it reinforces the right answer before they have read it.

| Cue | When | Shape |
| --- | --- | --- |
| `select` | an answer is chosen | soft tick, short sine |
| `correct` | right answer | rising two-tone, E5 then B5 |
| `wrong` | wrong answer | falling square slide, then a low tone |
| `heartLost` | a heart is spent | long falling triangle |
| `xp` | XP is awarded, after `correct` | quick coin double-blip, C6 then F6 |
| `complete` | lesson finished | four-note fanfare, C5 E5 G5 C6 with a held top note |
| `fail` | hearts reach zero | low sawtooth fall |

Rules:

- Sounds are synthesised with the Web Audio API. No audio files, so a lesson stays a single self-contained HTML file with no binary assets and no network fetch.
- Never construct an `AudioContext` eagerly. Browsers block audio before a user gesture, so the context is created on the first `play()` call and resumed if it starts suspended.
- Mute is a real gate, not an icon swap. `play()` returns `false` while muted, and the preference persists in `localStorage` under `teach-duo:muted`.
- Every entry point must be safe when audio is unavailable. `isSupported()` reports it, `play()` returns `false`, and the lesson keeps working silently.
- Call `sound("correct")` and friends from the feedback path, never from a click handler. The sound belongs to the outcome, not the tap.

## Options

Options are flat rows, not cards in a grid. Each carries a key badge showing its number. States:

- Default: 2px border `#E5E5E5`, white fill.
- Hover: `#F7F7F7` fill.
- Selected: blue border, blue-light fill, blue badge.
- Correct: green border, green-light fill.
- Wrong: red border, red-light fill.

When checking, mark the correct option green and the chosen wrong option red, so the learner sees both.

## Code and diagrams

Code blocks are dark, monospace, `16px` radius, with the flat bottom border. Long lines scroll horizontally rather than wrap, so indentation stays readable. Mark the relevant line with `.hl` when the question is about one specific line.

Memory diagrams are two bordered boxes side by side: stack on the left, heap on the right. Stack cells use green, heap cells use blue. Redraw the diagram per step and add one arrow or label at a time. Never one crowded diagram.

## Reference documents

Reference documents use the same tokens but read as prose, not as a quiz. They keep the `main` column at `620px` max width, the `.prose` heading scale, and the flat border-and-radius language. They add no hearts, no progress bar and no XP.

## Contract markers

Keep these ids and classes so tests, retries and the shared stylesheet keep working:

`progress-fill`, `checkBtn`, `nextBtn`, `sheet`, `sheetTitle`, `sheetBody`, `soundBtn`, `xp`, `h1` to `h3` for hearts, the `choice` class on options, and `data-icon` slots rather than glyphs.