# Design plan — Phase 1

Written before building, per the studio process: plan, self-critique
against generic defaults, then build to the revised plan. Keep this
updated if a later phase revisits a token — don't let the code and this
doc drift apart.

## Grounding

Subject: a platform whose entire mechanism is *small, achievable,
real-world actions* (the Tiny Action Engine is the product's spine —
R&D doc Section 29). Audience: college students who are lonely,
often at night or in unstructured time, who need something that feels
like a steady, low-key companion — not a hospital dashboard, not a
gamified wellness app, not a generic AI-startup UI. The page's job, for
this shell specifically: get someone to the thing they need (a check-in,
a tiny action, a room, a crisis resource) without making them feel
diagnosed, judged, or marketed to.

## Color — 6 named tokens

| Token | Hex | Role |
|---|---|---|
| `paper` | `#F3EEE3` | Page background — warm, not the specific cream (`#F4F1EA`) the generic-AI-design cluster defaults to; shifted grayer/flatter on purpose. |
| `paper-raised` | `#FAF7F0` | Card/surface background — a hair lighter than `paper` for quiet elevation, no drop shadows needed. |
| `ink` | `#2B2A27` | Primary text — warm near-black, not cold pure black. |
| `ink-muted` | `#6E6759` | Secondary text. |
| `lamp` | `#8F6427` | **The signature accent.** A warm, muted gold/amber — "a light left on for you," not teal (avoids the wellness-app default) and not the terracotta/clay near `#D97757` that reads as an AI-generated-design tell. Used deliberately and sparingly: active states, primary actions, focus rings. |
| `moss` | `#4F6B52` | Secondary accent — muted forest green, used only for progress/success states (ties to "small steps growing over time"). Never competes with `lamp` for attention. |
| `clay` | `#A1583F` | Muted error/warning. Deliberately desaturated — this is not alarm-red, per the brief's explicit constraint, and is visually distinct from `lamp`. |

Every text/background pairing above was verified against WCAG AA
(≥4.5:1 for text, ≥3:1 for functional UI borders per SC 1.4.11) with
`/home/claude/contrast_check.py` before being committed — see that
script's output in the Phase 1 build log for the full pass/fail table.

## Type — 2 roles, deliberately paired

- **Display: Fraunces Variable, `soft.css` axis build.** A warm,
  soft-terminal serif — used *only* for headings and empty-state
  headlines, dialed toward its `SOFT` axis (warmth) at a mid-high
  optical size (headline character), `WONK` off (kept legible/composed
  rather than quirky — this is a support product, not a playful one).
  Chosen specifically because it is NOT the high-contrast editorial
  serif the generic-AI-design cluster reaches for — Fraunces at a high
  `SOFT` value has rounder, warmer strokes, structurally different
  personality.
- **Body/UI: Karla Variable.** A humanist grotesque with genuine warmth
  in its details (slightly rounded terminals) without being a
  wellness-app cliché or the ubiquitous "Inter everywhere" default.
  Used for everything functional: nav labels, buttons, body copy, form
  fields.

Both are self-hosted via `@fontsource-variable` (npm-distributed, no
external font-CDN dependency at build time — see Phase 0's README for
why that matters in this specific environment).

## Layout concept

**Mobile** — bottom tab bar, 5 primary destinations + a "More" sheet:

```
┌───────────────────────────┐
│ [wordmark]            ⚙   │  slim header
│                            │
│      [ screen content ]   │
│                            │
│ ┌────────────────────────┐│
│ │ ⓘ Not a therapist. Tap ││  persistent disclosure — tappable → Safety
│ │   for support options ›││
│ └────────────────────────┘│
│  ⌂    ✓    ○    ◐    ▤  ⋯ │  Home·Checkin·TinyAction·Community·Journal·More
└───────────────────────────┘
```

**Desktop** — sidebar shows everything directly, no collapsing needed:

```
┌────────────┬──────────────────────────────┐
│ [wordmark] │                              │
│ ⌂ Home     │                              │
│ ✓ Check-in │      [ screen content ]      │
│ ○ Tiny Act │                              │
│ ◐ Community│                              │
│ ▤ Journal  │                              │
│ ───────── │                              │
│ ♥ Pro Help │                              │
│ ⛨ Safety   │                              │
│ ⚙ Settings │                              │
│ ───────── │                              │
│ ⓘ Not a    │                              │
│  therapist›│                              │
└────────────┴──────────────────────────────┘
```

Why 5 primary + "More" rather than all 8 in the tab bar: 8 icons in a
mobile bottom bar fails the brief's own "calm, not clinical-dashboard"
goal before a single feature is built — cramped nav reads as busy, not
calm. Professional Help and Safety Center specifically don't lose
reachability by being one tap into "More": Safety Center is *also*
reachable in one tap from the persistent disclosure bar on every screen
(R&D doc Section 16's requirement that professional help never be
gated behind a check-in is satisfied by "More" being one tap, same as
every primary tab).

Same nav config array drives both — see `src/lib/nav-config.ts` — no
separate mobile/desktop component trees.

## Signature element

**The "lamp glow"** — a soft, warm radial highlight marking the active
nav destination and focus states, using `lamp-tint` as a soft background
wash behind the active icon rather than a generic filled pill or bold
underline. It's the one place boldness is spent (per the skill's
"spend your boldness in one place, keep everything else quiet"); the
persistent disclosure bar stays visually calm on purpose so it doesn't
compete with it.

## Self-critique against the generic-AI-design clusters

- **Cluster 1 (cream + terracotta `#D97757`)**: avoided — different
  background value, and `lamp` is a muted gold/amber, not
  orange-clay. Fraunces-at-high-SOFT is structurally different from the
  high-contrast editorial serif that cluster reaches for.
- **Cluster 2 (near-black + acid accent)**: not applicable — this is a
  warm, light-forward palette throughout.
- **Cluster 3 (broadsheet, zero-radius, hairline rules)**: avoided —
  moderate radius scale (6/10/16/24px), no hairline-heavy newspaper
  layout.
- **The wellness-app default (teal/sage + cream, rounded-everything)**:
  the real risk for *this* brief specifically, since "calm mental-health
  product" pattern-matches to it immediately. Avoided by going
  warm-gold-forward instead of teal-forward, and by keeping `moss`
  (the only green in the palette) restricted to progress/success states
  rather than being the dominant hue.

## Deferred, not forgotten

Dark mode is intentionally not built in Phase 1 — better to ship one
excellent, verified theme than two half-considered ones. Revisit with
the same contrast-verification rigor when there's a real reason to
prioritize it.
