# Section contract

Everything a section author needs. The shell (`src/shell.html`) owns tokens, base CSS, shared components, the icon sprite, the header and footer, the presenter bar and the `DT` API. A section only adds its own fragment. Do not edit `shell.html`; ask the orchestrator if something shared is missing.

## Changes (round 4)

- **Dialog guard** looks only at the current section: a visible (not hidden, in the viewport) `dialog[open]`, `[role=dialog]` or `[aria-modal=true]` there suspends the presenter keys; one left open in another section never does. Escape with focus outside an open dialog is re-dispatched to the dialog, so the section's own Escape handler closes it. Close your dialog on `dt:jump` when the person leaves.
- Every presenter key calls `preventDefault()` (even at the first or last section). Bar and part buttons activated from the keyboard move focus to the new heading; mouse clicks keep focus on the button.
- Tall sections step by scroll once they exceed the usable height by about 24px. Buttons, switches, links and the bar use `touch-action: manipulation`. Space scrolls natively.

## Changes (round 3)

- **Top-anchored slides**: `.slide` now starts its content at the top (`padding-top: clamp(56px, 10vh, 120px)`), so every `.secnum` sits at the same height. `.split` aligns its columns to the top. Add `.slide--center` to keep vertical centring (hero, openers, s-12 and s-21 use it).
- **Headings**: `.h2`, `.h3`, `.h-display` balance their line breaks; `.h2` has a built-in bottom margin (`clamp(20px, 3vh, 32px)`), so do not add your own.
- **`.note`** (new): sans 400 sentence for small notes and captions, `--fs-ui` (18px or more), `--ink-label` (`--ink-on-dark-muted` on navy outside cards). **`.mono-note` is deprecated**; mono stays for short UPPERCASE labels (`.eyebrow`, `.secnum`, `.tag`, `.callout__kicker`, `.term__tech`) only.
- **`.keyline`** (new): the section's one takeaway sentence (serif 400, `--fs-lead`, `--ink-heading`, 40ch, left-aligned, light on navy). Serif is otherwise for headings, card titles and `.term__word` only; never use it for running text.
- **`.btn--choice`**: symmetric padding, with the check icon positioned absolutely at the left, so labels are truly centred. Markup is unchanged.
- **`.replay` and `.btn-reset`** are 56px tall like other buttons and are never primary. Use `.btn-reset` labelled "Start again" for anything interactive (quizzes, games, pickers) and `.replay` labelled "Replay" for animations.
- **Footer** is navy (`--dragonfly-dark`) and continues from the navy s-21 closing with no hairline; credit in `--ink-on-dark`, disclaimer as `.note`.
- **Icons**: every sprite symbol uses a 2px stroke on a 24 viewBox (your own symbols must too).
- **Copy**: the page title and header label both read "APIs and MCP, explained". The `s-safe` opener line is "Two ways to stay in control of what an AI does."
- **`.tag--corner`**: works on any `position: relative` container (`.card`, `.panel`, `.callout`, `.result` already are; add `.tagged` to anything else). Convention: **one tag per visual, top-right of the visual container**, with only two wordings: "Example" (data, screens, answers) or "For illustration" (diagrams, simulations).
- **Site-wide conventions**:
  - Curly quotes and apostrophes everywhere (’ “ ” ‘).
  - Instructions say "Press" for buttons and "Choose" for options; never click, select, pick or toggle.
  - `.term` is the plain word big plus the tech word small; only tech words go in the small slot.
  - Lens colours only where colour carries meaning (s-06 keys, s-07 bins, s-09 and s-11 adapters, s-19 Venn), with one mapping: Weather and Email `--dragonfly`, Maps and Calendar `--lens-geo`, Statistics `--lens-systems`, Files `--lens-scenario`.
  - Coloured borders are 2px at most.
  - No bold body runs: emphasise with weight 500 plus `--ink-heading`.

## Changes (round 2)

- **Navy cards**: `.card`, `.panel`, `.callout` inside `.slide--navy` are light-ground islands; everything inside them keeps its light-ground colours (buttons, switches, lead, eyebrow, term, links, focus ring). Navy recolouring never reaches inside them. Outside cards, `.btn--primary` on navy now renders light automatically (`.btn--on-dark` still works).
- **Presenter counter**: numbered sections show `04 / 21` (from the id `s-04`; total = number of numbered sections); the hero shows `Start`, s-part1 `Part 1`, s-part2 `Part 2`, s-safe `Safety`. Prev/next buttons are labelled `Next: <data-label>` and `Previous: <data-label>`, so keep `data-label` short and clear. Phones show the part (or the section label) in the middle.
- **Keys**: held keys do not repeat. Presenter keys are suspended while focus is inside, or any visible element matches, `dialog[open]`, `[role=dialog]:not([hidden])` or `[aria-modal=true]:not([hidden])`; Escape is left to the dialog while focus is inside one. On screens 1024px and wider, a section taller than the screen is scrolled through in steps (about 85% of the usable height) by Right and PageDown (Left and PageUp scroll back) before the next jump.
- **Focus**: only key-driven jumps move focus to the section heading. The Prev/Next/Part buttons keep focus and announce the new section with `DT.announce`.
- **`DT.onEnter`** ignores intersections while a presenter jump is scrolling and fires only after the element has stayed in view for about 300ms; `once:false` fires again only after it has left and come back. `DT.announce` queues, so two messages sent in the same tick are read together.
- **No CSS smooth scrolling**: never set `scroll-behavior` (lint ERROR); the presenter script scrolls. The URL hash follows the current section (`replaceState`, no history entries); a reload at `#s-xx` lands there instantly.
- **Contrast**: unselected `.btn--choice`, `.btn--secondary`, `.replay`, `.btn-reset` and the `.switch` track use a `--ink-muted` border (3:1 or better). Cards keep the hairline.
- **Facets** are confined to the right 40% of a slide and hidden on phones.
- **New shared patterns**: `.btn-reset`, `.result` (`--ok`, `--warn`), `.tag--corner`, `.full` (see the class table).
- **Lint additions** (section 2): single-IIFE scripts, banned URL schemes, no shadows/`position:fixed`/scroll-snap/`scroll-behavior`, `<use>` targets must exist, warnings for hex colours, gradients, bold headings, tiny type, key/wheel listeners on document or window, `-ize` spellings, and `!` or US spellings inside `DT.announce`/`textContent` strings.
- **Fonts** load without blocking first paint (preload plus `noscript` fallback); fallback stacks are unchanged, so test text may reflow slightly when Plex arrives.

## 1. Fragment format

File: `src/sections/NNN-slug.html` (order = filename order). One root `<section>`, nothing outside it.

```html
<section id="s-04" class="slide" data-part="apis" data-label="Build a weather order" aria-labelledby="s04-title">
  <div class="wrap">
    <div class="split">
      <div class="stack">
        <p class="secnum"><b>04</b> Build a weather order</p>
        <h2 id="s04-title" class="h2">Pick a place and a day.</h2>
        <p>One or two short sentences.</p>
      </div>
      <div> <!-- the one visual or interaction --> </div>
    </div>
  </div>
  <style>#s-04 .foo{...} @media (max-width:640px){#s-04 .foo{...}}</style>
  <script>(()=>{ const root = document.getElementById('s-04'); /* query only inside root */ })();</script>
</section>
```

- `id="s-XXX"`; `data-part` is one of `intro apis mcp safe close`; `data-label` is required; `class` must include `slide`.
- The first heading (the `aria-labelledby` target) receives focus after a presenter jump. Use `<h2>` (the hero uses `<h1>`).
- Section files: `000-hero` (s-hero) · `100-part1` (s-part1) · `101-s01`..`108-s08` · `200-part2` (s-part2) · `201-s09`..`210-s18` · `300-safe` (s-safe) · `301-s19`, `302-s20` · `400-s21` (close, navy).
- Fragment scripts run while the page is parsed, before the presenter bar exists. `DT` is already defined. Do not rely on other sections. A fragment `<script>` must be one IIFE and nothing else (`(()=>{ ... })();` or `(function(){ ... })();`), so no variable leaks into the page.

## 2. Lint rules (`python3 -I src/build.py` prints them and exits 1 on any ERROR)

ERROR:
- structure: not exactly one root `<section id="s-XXX" class="slide">` with valid `data-part` and a `data-label`; duplicate section ids; any inner `id` not starting with the prefix (`s-04` gives `s04-`, `s-hero` gives `shero-`, `s-part1` gives `spart1-`); `@keyframes` name without the prefix.
- CSS scope: any selector not starting with `#s-XXX` (comma lists, `@media`, `@supports` are checked; `#s-04 + x` and `#s-04 ~ x` also fail); `@import` and `@font-face`; `box-shadow` other than `none`; `position: fixed`; `scroll-snap-*`; `scroll-behavior`; `image-set()` with URLs.
- URLs: external `http(s)://`, `//` or `/\` URL in `src`, `href`, `srcset`, `action`, `url()` or `@import` (whitespace and control characters are stripped before matching); `javascript:`, `data:`, `vbscript:`, `mailto:` hrefs; `<script src>`; `<img>`, `<iframe>`, `<object>`, `<embed>`, `<link>`, `<base>`, `<meta>` in a fragment.
- `<use href="#x">` whose id exists in neither the shell sprite nor your fragment.
- A `<script>` that is not a single IIFE.

WARN:
- text: `!` in visible text, in `aria-label`/`title`/`alt` and in `DT.announce("...")` / `textContent = "..."` strings; emoji; American spellings (color, center, organization, analyze, favorite, behavior, gray, anything ending -ize/-ization) in text, those attributes and those strings.
- style: hex colours in CSS or SVG `fill`/`stroke` (use tokens or `currentColor`); `linear-gradient`/`radial-gradient` (only `.grad` in s-hero and s-12 is exempt); bold weight on `h1`-`h3`, `.h2`, `.h3`, `.h-display`; `font-size` under 15px; `drop-shadow()`.
- scripts: `document`/`window`/`document.body` `addEventListener` for `keydown`, `keyup`, `keypress` or `wheel`; `fetch`/`XMLHttpRequest`/`WebSocket`; `document.querySelector` (use `root.`); `getElementById` of an unprefixed id; inline `onclick=` style handlers; missing `aria-labelledby`.

The only external link allowed is a citation `<a href="https://datacommons.org/..." target="_blank" rel="noopener">` (section 17; paths and query strings are fine, the host must be exactly `datacommons.org` or `www.datacommons.org` over https); everything else stays plain text. Fragment SVG ids (gradients, clipPaths, markers) must be prefixed too. Add your own icons as `<symbol id="s04-i-foo">` inside your fragment's own `<svg>`.

## 3. Test a fragment

```
python3 -I src/build.py --only '000-*,1NN-*' --out <scratch>/preview/<name>/index.html
cd <scratch>/harness
node shoot.js --page <scratch>/preview/<name>/index.html --out <scratch>/shots/<name> [--ids s-04] [--reduced] [--viewports 1920x1080,1280x800,390x844]
node axe.js   --page <scratch>/preview/<name>/index.html [--ids s-04]
node keys.js  --page <scratch>/preview/<name>/index.html
```
`shoot.js` fails on console errors or horizontal overflow, and lists text under 18px. `axe.js` must report 0 violations (normal and reduced motion). Look at the PNGs yourself at all three sizes and with `--reduced`. Also click through every interaction by mouse and keyboard.

## 4. Shared classes

| Class | Use |
|---|---|
| `.slide` | The section. Min height is the screen minus the presenter bar; content is top-anchored; padding and hairline between light slides are built in. |
| `.slide--center` | Vertically centres the content (hero, openers, s-12, s-21). |
| `.slide--navy` | Dark ground (`--dragonfly-dark`) for openers and the closing slide. Headings, `.lead`, `.eyebrow`, `.secnum`, links, `.term` and buttons recolour themselves, except inside `.card`, `.panel` and `.callout`, which stay light-ground. |
| `.slide--sky` | Pale `--dragonfly-light` ground (section 12 only). |
| `.wrap` | Centred column, max 1240px of content, gutter 16px (phone) up to 48px. Put it directly inside `.slide`. |
| `.split` | Two columns at 1024px and up (text 5/12, visual 7/12); stacks below. Put text first. |
| `.full` | Single column, full width (`<div class="full">`): the alternative to `.split` when the visual needs the whole row. |
| `.stack` / `.stack-lg` | Vertical rhythm between children (24px / fluid 28-48px). Override with `style="--stack:16px"`. |
| `.narrow` | `max-width: 60ch`. Plain `<p>` is already capped at 60ch. |
| `.facets` | Decorative dot lattice, `<div class="facets" aria-hidden="true"></div>` as first child of a slide. Occupies the right 40% only, fading out leftwards, hidden on phones. Hero and openers use it; avoid elsewhere. |
| `.eyebrow` | Mono uppercase label above a headline (`dragonfly`; `dragonfly-light` on navy; `cobalt` on sky). |
| `.secnum` | `<p class="secnum"><b>04</b> Build a weather order</p>`. Use on sections 1-21 instead of `.eyebrow`. |
| `.h-display` | Hero and opener size only. `.h2` section title (max 24ch), `.h3` card/step title. Plain `h1`/`h2`/`h3` already match. Never bold. |
| `.lead` | Larger sans line under a headline (max 52ch). |
| `.note` | Small note or caption sentence in sans, `--fs-ui`, `--ink-label`. Replaces `.mono-note` (deprecated, still works). |
| `.keyline` | The one takeaway sentence of a section: serif, `--fs-lead`, 40ch, left-aligned. |
| `.grad` | `<em class="grad">your other apps.</em>` Italic gradient phrase. Allowed in the hero and section 12 only. Never on navy. |
| `.term` | `<div class="term"><p class="term__word">The menu</p><p class="term__tech">Documentation</p></div>`. Big everyday word, small tech word. |
| `.btn` | Base button (56px min). Always add a variant. Works on `<button>` and `<a>`. |
| `.btn--primary` | Ink fill, light text, optional trailing `<svg class="icon">` arrow. The main action on light grounds. |
| `.btn--secondary` | White, `--ink-muted` border. |
| `.btn--on-dark` | Near-white fill for the main action on navy (an ink button disappears on navy). |
| `.btn--choice` | Selectable option: `<button class="btn btn--choice" aria-pressed="false"><svg class="icon btn__check" aria-hidden="true"><use href="#i-check"/></svg>Sydney</button>`. Keep the check icon in the markup; toggle only `aria-pressed`. |
| `.btn--small` | 48px min, tighter padding. |
| `.btn-reset` | The standard "Start again" button (secondary, small): `<button class="btn-reset"><svg class="icon" aria-hidden="true"><use href="#i-rotate-ccw"/></svg>Start again</button>`. Use it for games and quizzes; use `.replay` for animations. |
| `.btn-row` | Wrapping row of buttons, 16px gap. |
| `.seg` | `<div class="seg" role="group" aria-label="Place">` holding `.btn--choice` buttons. Tab between buttons; do not add arrow-key handling. |
| `.switch` | `<button class="switch" role="switch" aria-checked="false"><span class="switch__track"><span class="switch__thumb"></span></span><span class="switch__label">Allow actions</span></button>`. Toggle `aria-checked`; the track shows "On" or "Off" itself. |
| `.card` / `.card--active` | White box with hairline, radius 8px / the same with a 2px `--dragonfly` border (current step, selection). Dark text even inside navy slides. |
| `.panel` | `--surface-muted` box, no border. |
| `.callout` | Aside or story: muted box, `<p class="callout__kicker">A real story</p>` then text. No coloured edge. |
| `.callout--warn` | White box, `--lens-risk` hairline and kicker. |
| `.result` | Feedback box: `<div class="result result--ok" aria-live="polite"><svg class="icon icon--lg result__icon" aria-hidden="true"><use href="#i-check"/></svg><p class="result__text">Words first.</p></div>`. `result--ok` has a `--dragonfly` icon (use check or info); `result--warn` is a white box with a `--lens-risk` hairline and icon (use shield-alert or x). Always icon plus words; set `hidden` until there is a result. |
| `.tag` | Mono uppercase chip: "Example data", "For illustration". Put one on every simulated panel: either `.tag--corner` as the first child of a `.panel`/`.card` (top-right corner; the box gains top padding), or directly under the heading. |
| `.replay` | `<button class="replay"><svg class="icon" aria-hidden="true"><use href="#i-rotate-ccw"/></svg>Replay</button>`. Every animation needs one. |
| `.sr-only` | Visually hidden text. |
| `.icon` / `.icon--lg` | `<svg class="icon" aria-hidden="true"><use href="#i-key"/></svg>`, 1em or 1.5em, inherits text colour. |

Icons in the sprite: arrow-right, arrow-left, check, x, lock, unlock, key, rotate-ccw, phone, smartphone, cloud-sun, map-pin, user-check, landmark, mail, calendar, folder, bar-chart, plug, shield-alert, search, zap, door-closed, door-open, chef-hat, info (all `#i-NAME`).

Tokens: all brand tokens from `tokens.css` are on `:root`. Also `--fs-display` (48-104px), `--fs-h2` (36-64), `--fs-h3` (26-36), `--fs-lead` (22-30), `--fs-body` (20-24), `--fs-label` (15-18), `--fs-ui` (18-20); `--dur-1/2/3` (200/450/800ms, 1ms under reduced motion), `--ease`; `--bar-h` (presenter bar, 64px, 56px on phone), `--gutter`, `--slide-pad`. Use these; do not invent sizes below `--fs-label`, and use `--fs-body` or larger for sentences.

## 5. The `DT` API (`window.DT`, ready before any section script)

- `DT.reduced` (getter): live `prefers-reduced-motion: reduce`.
- `DT.dur(ms)`: `0` if reduced, else `ms`. `DT.wait(ms)`: promise that resolves after `DT.dur(ms)`.
- `DT.announce(text)`: polite screen-reader announcement (use for every result, answer or state change that is only visual). Messages sent in the same tick are queued and read together.
- `DT.onEnter(el, cb, {threshold = 0.5, once = true})`: calls `cb(entry)` once `el` has been that visible for about 300ms and no presenter jump is scrolling past it; with `once:false` it fires again only after `el` has left and come back. Returns a stop function. Works for elements taller than the screen. Do not rely on it firing for a section the presenter jumps over.
- `DT.travel(dotEl, pathEl, ms, {reverse = false})`: moves an SVG `<circle>` or `<g>` along a `<path>` by setting `transform="translate(x y)"`. Draw the dot centred on 0,0 and put it in the same `<g>` as the path (same coordinate space). Returns a promise: `true` on arrival, `false` if a newer `travel` on the same dot cancelled it (safe to click repeatedly). Reduced motion: jumps to the end at once.
- `DT.sections`, `DT.current()` (index), `DT.goTo(idOrIndex, {focus, instant})`: available after load; rarely needed. Events on `document`: `dt:jump` (a `CustomEvent`, `detail: {from, to}` = section ids) fires whenever the presenter scrolls, whether by keys, the bar buttons, the part buttons, a hash link or `DT.goTo`; `from === to` when it is only stepping through one tall section, so a section that must reset when the person leaves (for example s-16 closing its sign-in window) listens with `document.addEventListener('dt:jump', e => { if (e.detail.from === 's-16' && e.detail.to !== 's-16') close(); })`. `dt:settle` fires when the scrolling stops.

Presenter keys (already wired, do not duplicate): Left and PageUp = previous section, Right and PageDown = next (tall sections on screens 1024px and wider are scrolled through first); the heading of the new section takes focus; Escape blurs (but not inside a dialog); Space, Home, End are untouched; held keys do not repeat. The keys are ignored with any modifier held, in `input`/`textarea`/`select`/contenteditable, inside any element with `data-own-arrows`, inside a dialog, and while any visible `dialog[open]`, `[role=dialog]:not([hidden])` or `[aria-modal=true]:not([hidden])` is in the page. Toggle a custom dialog with the `hidden` attribute and give it `role="dialog"`, and the guard works with no extra code. If a widget needs arrow keys, put `data-own-arrows` on it; prefer plain Tab and Enter and avoid arrow keys altogether. Do not add `keydown` handlers on `document` or `window`, and do not hijack the wheel or add scroll snapping.

The presenter bar is built from `main > section.slide`: three parts ("Part 1 · APIs" = `apis` sections incl. s-part1, "Part 2 · MCP", "Staying safe" = `safe` plus `close`), one tick per section, a counter (see Changes), and the visited ticks fill after about 600ms on a section. Jumping to the first section scrolls to the page top so the header shows.

## 6. Colour rules (every pair is AA; keep it that way)

- Light grounds (`--surface-page`, `--surface-card`, `--surface-muted`): text `--ink`, `--ink-heading`, `--ink-secondary`, `--ink-label`; `--dragonfly` for small accents and tech words (4.6:1 or better); `--ink-muted` on page or white only and for captions; `--lens-risk` as text only on white or page (fails on muted).
- Navy: `--ink-on-dark`, `--ink-on-dark-muted`, accent `--dragonfly-light`. Never `--dragonfly` text on navy. Ink buttons vanish on navy; use `.btn--on-dark`.
- Sky: `--ink`, `--ink-heading`, `--ink-label`, accent `--cobalt`. Never `--dragonfly` text on sky (3.9:1).
- `--lens-*` colours are fills, borders and diagram strokes beside a text label, never body text. Use them only where lenses or roles need telling apart, and never as the only signal.
- Confirmed: section 8 "Try later" tickets use `--lens-business` (orange) as a 2px border plus a light tint, with `--ink` text (tint: `color-mix(in srgb, var(--lens-business) 12%, var(--surface-card))`). Orange text fails contrast. Accepted tickets are blue (`--dragonfly` border or fill with a white or ink label).
- Flat: no shadows, no gradients except `.grad`, hairline `--border`, radius 6px (buttons) and 8px (cards). No coloured left borders. No new hex values; reuse tokens (opacity on a token is fine).
- Focus rings are global (3px `--dragonfly`, `--dragonfly-light` on navy outside cards). Never remove them. Meaningful borders on controls use `--ink-muted` or darker (3:1); hairlines are for cards and dividers. Make interactive SVG parts real `<button>`s.

## 7. Audience rules

- Body text 20px or more (`--fs-body`); mono labels only for short uppercase labels; nothing meaningful under 15px. Headlines large, serif, regular weight.
- Plain words first, the tech word small beside it (`.term`). 2-3 short sentences per section at most.
- Click, tap and keyboard only. No drag (if you must, add a click alternative). Buttons 56px tall (48px for `.btn--small`), generous gaps.
- Nothing auto-advances and nothing loops forever. Animations start on a click (or `DT.onEnter` for one gentle play) and have a Replay button. Never hide information that only appears on hover.
- Reduced motion: use `DT.dur`, `DT.wait`, `DT.travel`, or a CSS `transition`/`animation` driven by `--dur-*` (they collapse to 1ms), so the end state still appears at once. State must never be conveyed by motion alone.
- Results, answers and state changes are announced with `DT.announce` (or an `aria-live="polite"` region inside your section) and shown in text, not colour alone.
- Everything simulated carries a `.tag` ("Example data" or "For illustration"). No real network calls, logins or live data.

## 8. Layout target

All content, with the headline and one visual, must fit on one screen above the presenter bar at 1920x1080 (usable height 1016px); aim to fit at 1280x800 (736px). Taller is allowed only when it is unavoidable and the key action stays visible. At 390px everything stacks and may scroll, with no horizontal overflow (use `min-width: 0`, wrapping flex, `max-width: 100%` on SVG with a `viewBox`). Phone buttons may go full width.

## 9. Copy rules

Australian spelling (colour, centre, organisation, analyse, behaviour). No emoji. No exclamation marks. No hype words. No real people except Simon Willison (trifecta credit in section 19) and the footer credit line. Every number comes from the brief or is labelled example or for illustration. Section 17 shows no unemployment figure (use "[figure]"). Section 18 timeline facts are exactly as in the brief.

## 10. Decisions already confirmed

- Section 15 note reads exactly: "In Claude: tap + then Connectors to add, manage or turn them on. Menus move around, so look for 'Connectors'." Do not mention ChatGPT.
- Section 8 "Try later" tickets: orange border and light tint, ink text (see colour rules).
- No favicon. The dragonfly mark appears only in the header and footer (the shell does this); never use the full wordmark logo.
- The gradient budget is the hero plus section 12.
- Section 17 may link its named source to https://datacommons.org (new tab, `rel="noopener"`); no other external links.
