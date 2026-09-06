"""
Seeds the tiny_actions table with a real starter content library.

Idempotent: if the table already has any rows, this is a no-op — it's
meant for a fresh environment (local dev, CI, first deploy), not for
patching content in place. Editing seeded copy later is a deliberate,
separate operation (query + update the specific rows), not something
this script tries to reconcile automatically.

Ladder model (see R&D doc Section 5.3 and this phase's build notes):
  - Each ladder is 3 rungs: difficulty_level 3 (hardest) -> 2 (default
    starting point, shown first) -> 1 (easiest).
  - `ladder_parent_id` always points toward the HARDER neighbor, so the
    hardest rung in each ladder is the root (ladder_parent_id = NULL).
  - "Make it bigger" = follow ladder_parent_id directly (O(1) lookup).
    "Make it smaller" = find the row whose ladder_parent_id is the
    current row's id.

Run with:
    DATABASE_URL=postgresql+psycopg2://postgres:<pw>@localhost/campus_connect \
        python seed_tiny_actions.py
(superuser connection needed for the initial insert; the app_core_api
role's own grants already cover it for read/write once seeded.)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.orm import Session  # noqa: E402

from db.base import SessionLocal  # noqa: E402
from db.models.core import TinyAction  # noqa: E402

# Each tuple: (category, ladder_name, [(difficulty_level, title, description), ...])
# Rungs listed hardest-first — matches how they're inserted (root first).
LADDERS: list[tuple[str, str, list[tuple[int, str, str]]]] = [
    # ---------------- SOCIAL ----------------
    (
        "social",
        "connect_with_a_classmate",
        [
            (
                3,
                "Message one classmate",
                "Send a message to someone from one of your classes — even just "
                "asking about an assignment. You don't need the perfect opener.",
            ),
            (
                2,
                "Go where people are",
                "Head somewhere on campus where other students tend to be — the "
                "library, a common room, anywhere with people around. You don't "
                "have to talk to anyone.",
            ),
            (
                1,
                "Step outside for 2 minutes",
                "Just open your door and step outside for two minutes. That's "
                "the whole thing.",
            ),
        ],
    ),
    (
        "social",
        "reach_out_to_someone_you_trust",
        [
            (
                3,
                "Call someone you trust",
                "Call — actually call, not text — one person you trust. You "
                "don't need a reason. \"Just wanted to hear your voice\" is enough.",
            ),
            (
                2,
                "Text someone you trust",
                "Send one text to someone you trust. It doesn't need to be "
                "deep — \"thinking of you\" or \"how's your week going\" both count.",
            ),
            (
                1,
                "Open a chat you've been meaning to reply to",
                "Just open one conversation you've been meaning to get back "
                "to. You don't have to send anything yet.",
            ),
        ],
    ),
    (
        "social",
        "join_something_happening",
        [
            (
                3,
                "Attend one campus activity",
                "Show up to one club meeting, study group, or campus event "
                "that's already happening today. You can leave whenever you want.",
            ),
            (
                2,
                "Look up what's happening today",
                "Spend two minutes looking up what's on today — a club "
                "meeting, a talk, anything. You don't have to go.",
            ),
            (
                1,
                "Think of one thing you'd maybe want to try",
                "Just think of one activity, club, or event you've been "
                "mildly curious about. Nothing to do yet — just notice it.",
            ),
        ],
    ),
    # ---------------- STUDY ----------------
    (
        "study",
        "start_the_thing_youre_avoiding",
        [
            (
                3,
                "Work for 15 real minutes",
                "Set a timer for 15 minutes and work on the thing you've "
                "been avoiding. When the timer ends, you're done if you want to be.",
            ),
            (
                2,
                "Open the material",
                "Just open the document, book, or app for whatever you've "
                "been avoiding. You don't have to do anything with it yet.",
            ),
            (
                1,
                "Put it where you'll see it",
                "Put the book, laptop, or notes somewhere you'll actually "
                "see them — your desk, your bag by the door. That's it.",
            ),
        ],
    ),
    (
        "study",
        "study_with_people_around",
        [
            (
                3,
                "Join a study room",
                "Find or start a study session with other people nearby — a "
                "study room, a library table, a group chat. Working near "
                "others often makes it easier than working alone.",
            ),
            (
                2,
                "Go somewhere people study",
                "Go to a space where other students study — a library, a "
                "study lounge — even if you end up sitting alone.",
            ),
            (
                1,
                "Move to a different room",
                "Just move from where you are now to a different room. "
                "Sometimes the space itself is the problem.",
            ),
        ],
    ),
    (
        "study",
        "get_unstuck_on_one_thing",
        [
            (
                3,
                "Ask one question",
                "Ask one specific question — to a classmate, a TA, an "
                "online forum — about whatever's confusing you. One "
                "question, that's the whole task.",
            ),
            (
                2,
                "Write down what's confusing you",
                "Write one sentence describing exactly what you're stuck "
                "on. You don't have to solve it yet.",
            ),
            (
                1,
                "Reread the confusing part once",
                "Just reread the part that's confusing you, one more time. "
                "No pressure to understand it yet.",
            ),
        ],
    ),
    # ---------------- MOVEMENT ----------------
    (
        "movement",
        "get_outside",
        [
            (
                3,
                "Take a 10-minute walk",
                "Go for a walk — no destination needed, just ten minutes "
                "of moving outside.",
            ),
            (
                2,
                "Walk to somewhere nearby",
                "Walk to one specific nearby place — a coffee shop, a "
                "mailbox, anywhere a few minutes away.",
            ),
            (
                1,
                "Stand up and stretch",
                "Just stand up and stretch for a minute, wherever you are "
                "right now.",
            ),
        ],
    ),
    (
        "movement",
        "move_your_body_low_effort",
        [
            (
                3,
                "Do 10 minutes of any movement",
                "Ten minutes of anything physical — a walk, stretching, "
                "dancing badly in your room, whatever counts as movement "
                "to you.",
            ),
            (
                2,
                "Do a few minutes of stretching",
                "A few minutes of stretching, right where you are. No "
                "equipment, no plan needed.",
            ),
            (
                1,
                "Roll your shoulders a few times",
                "Just roll your shoulders back a few times. Ten seconds, "
                "that's it.",
            ),
        ],
    ),
    # ---------------- REST ----------------
    (
        "rest",
        "actually_rest_not_scroll",
        [
            (
                3,
                "Take a real 20-minute break",
                "Twenty minutes away from screens — read, nap, sit "
                "outside, stare at the wall. Actual rest, not scrolling.",
            ),
            (
                2,
                "Put your phone in another room",
                "Put your phone somewhere you can't easily reach it for "
                "ten minutes.",
            ),
            (
                1,
                "Close your eyes for one minute",
                "Just close your eyes for one minute, wherever you're "
                "sitting.",
            ),
        ],
    ),
    (
        "rest",
        "wind_down",
        [
            (
                3,
                "Do a proper wind-down routine",
                "Spend 15 minutes on whatever actually helps you wind "
                "down — music, a shower, journaling, quiet time. Whatever "
                "that is for you.",
            ),
            (
                2,
                "Dim the lights and slow down",
                "Turn down the lights around you and let yourself slow "
                "down for a few minutes, no specific task.",
            ),
            (
                1,
                "Take five slow breaths",
                "Five slow breaths, in and out. That's the whole thing.",
            ),
        ],
    ),
]


def seed(db: Session) -> int:
    existing_count = db.query(TinyAction).count()
    if existing_count > 0:
        print(f"tiny_actions already has {existing_count} rows — skipping (idempotent no-op).")
        return 0

    inserted = 0
    for category, _ladder_name, rungs in LADDERS:
        # Insert hardest-first so each subsequent rung's parent already exists.
        parent_id = None
        for difficulty_level, title, description in sorted(rungs, key=lambda r: -r[0]):
            action = TinyAction(
                category=category,
                difficulty_level=difficulty_level,
                ladder_parent_id=parent_id,
                title=title,
                description=description,
            )
            db.add(action)
            db.flush()  # populate action.id for the next rung's parent
            parent_id = action.id
            inserted += 1

    db.commit()
    return inserted


if __name__ == "__main__":
    session = SessionLocal()
    try:
        count = seed(session)
        print(f"Seeded {count} tiny_actions rows across {len(LADDERS)} ladders.")
    finally:
        session.close()
