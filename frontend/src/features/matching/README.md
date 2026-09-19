# features/matching

**Built in:** Phase 11
**R&D doc reference:** Section 5.5, Section 21
**Note:** Explicitly non-dating. No photo-first UI, no romantic signals in the data model.

The Phase 11 UI lives in `src/app/(app)/matching/`. It only calls a
server-side matching-service adapter. Matching is rules-based around selected
interests, course/year, and activity types; region/language are private
tie-breakers. Block and report history are enforced by matching-service before
any candidate reaches this UI.
