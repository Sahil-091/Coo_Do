# Phase 13 launch gate — local activity discovery

Phase 13 is code-complete but **not launch-ready**. Local unit tests and a
successful migration do not prove that real-world meetup invitations are safe
to publish. Complete every item below in staging, retain the evidence with the
release record, and have the named operations owner sign it before enabling the
feature for students.

## 1. Verified public-venue catalogue

1. Export every active provider/catalogue ID, display name, map URL, and coarse
   area-cell assignment from the staging configuration. Do not add raw
   addresses to this release record.
2. Two staff members independently verify each entry against the venue's
   official campus, municipal, or business source. Confirm it is a public,
   accessible place—not a residence, hostel room, apartment, private office,
   or temporary pin—and that the map link lands on that venue.
3. Record verifier names, source URLs, date, and approved/rejected result in a
   restricted operations record. Exercise replacement and removal of a bad
   catalogue ID, then confirm core-api rejects that removed ID.
4. From a browser and direct internal request, try free-form `address`, a
   forged venue name/map URL, and a residential-looking venue ID. Each must
   fail, and the stored/returned event must contain only the catalogue venue.

## 2. Meetup-text moderation and staffed decision operations

1. With staging's real safety-service and moderation-service credentials,
   submit representative safe activities plus deliberately held copy: a phone
   number, a residential/address-like instruction, off-platform contact,
   sexual/predatory language, scam wording, harassment, and crisis-indicative
   text. Capture only test-safe disposable content in the release evidence.
2. Confirm every unsafe/unavailable-screening attempt returns an error, creates
   no public `activity_meetups` row, and emits no notification handoff. A safe
   activity must be visible only after a successful screen.
3. Rehearse the Phase 12 reviewer escalation path with the moderator roster:
   who is on duty, timezone coverage, response-time target, escalation owner,
   and how a venue/copy complaint is handled. This is additive to—not a
   replacement for—the pending Phase 12 staffed-review sign-off.
4. Record the reviewer lead's sign-off that the classifier is a conservative
   pre-publication control, not an automated safety verdict.

## 3. Consent, location, and notification fan-out

1. Create disposable accounts covering every filter edge: granted + enabled +
   matching category + same cell; revoked consent; disabled/missing preference;
   another cell; non-overlapping interest; and the creator. Publish a safe
   activity and reconcile the notification-service accepted recipient IDs
   against exactly the one eligible test account. Inspect the handoff payload
   and logs: no latitude, longitude, area-cell value, interest list, profile,
   attendee list, or distance may appear.
2. Confirm revoking `activity_alerts` immediately stops a later matching-cell
   alert even if an old area preference existed. Confirm clearing the area
   removes the stored preference and discovery returns no local activities.
3. Load-test staging's authenticated notification endpoint with disposable
   recipient IDs only. The file must be kept outside version control and must
   contain no user location or contact data:

   ```json
   {"recipient_ids": ["uuid-1", "uuid-2"], "meetup_id": "uuid", "category": "coding"}
   ```

   ```bash
   python scripts/load_test_activity_alerts.py \
     --base-url https://staging-notifications.example \
     --internal-secret "$INTERNAL_SHARED_SECRET" \
     --payload-file /secure/path/phase-13-alert-payload.json \
     --requests 100 --workers 10
   ```

   A pass has zero non-202 responses, bounded latency agreed by the on-call
   owner, no duplicate downstream delivery for a repeated recipient ID, and no
   queue/backlog beyond the published recovery threshold. Save command output,
   service metrics, and delivery-adapter evidence. This endpoint test does not
   replace the filter reconciliation in item 1.

## 4. RSVP and operational sign-off

1. Simultaneously race two disposable accounts for the final seat. Exactly one
   must receive Join; the other must receive the full response. Verify Maybe
   and Ignore do not consume capacity.
2. Check browser/API responses and map embeds: they may show only a verified
   venue pin/link, aggregate Join/Maybe counts, and the signed-in student's own
   RSVP. They must never show attendee lists, people pins, coordinates, or
   person-to-person distances.
3. Record the incident owner for venue removal, harmful meetup reports,
   notification delivery failure, and an emergency feature kill switch. The
   release manager then records pass/fail with the moderation lead and
   notification on-call owner.

Until all four sections are recorded as passed, retain the Phase 13 launch
gate and describe the feature as implemented but pending live verification.
