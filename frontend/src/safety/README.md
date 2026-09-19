# `safety/` — isolated safety module

**This module is the single sanctioned path for anything touching crisis-language
detection or its results.** It exists as its own top-level module (a sibling of
`features/`, not nested inside it) specifically to make the dependency boundary
visible and enforceable.

## Rules (see R&D doc Section 10, Section 18)

1. **One-directional dependency only.** `features/*` may import from `safety/`.
   `safety/` must never import from `features/*`. If you find yourself wanting
   to do that, the logic belongs somewhere else.
2. **No feature module implements its own crisis-detection logic.** Every
   AI-facing or free-text-input feature (AI Navigator, Journal if ever opted
   into scanning, Community posts) routes text through this module's client
   before that text reaches an LLM call or is persisted/displayed.
3. **The real classifier is server-side**, in the `safety-service` backend
   (see `/backend/services/safety-service`). This frontend module is a thin,
   typed client plus shared UI primitives that every gated screen mounts —
   it does not itself decide what is or isn't a crisis. Client-side keyword
   matching is explicitly NOT an acceptable substitute for the server-side
   classifier; nothing here should attempt to replicate that logic.
4. **Fails safe, not silent.** If `checkText()` cannot reach the
   safety-service (network error, timeout), the caller must treat that as
   "could not verify" and fall back to always-visible crisis resources
   rather than silently proceeding as if the text were clear.

## Status

Scaffold only (Phase 0). Real detection logic, the response flow, and the
crisis-resource UI ship in **Phase 5**, and must exist and be reviewed before
**Phase 6** (AI Navigator) is allowed to make its first LLM call. Do not
build Phase 6 ahead of this module being real.
