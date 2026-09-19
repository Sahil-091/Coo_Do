"""Run a controlled flagged-post burst against a live Phase 12 environment.

This is a launch gate, not a synthetic unit test. It requires an authenticated
internal service endpoint and disposable test users/rooms; it deliberately
does not target production by default.
"""
import argparse
import concurrent.futures
import json
import sys
import urllib.error
import urllib.request


def post_json(url: str, secret: str, payload: dict) -> tuple[int, dict]:
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json", "X-Internal-Secret": secret},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:  # nosec B310 - user-supplied test endpoint
            raw_body = response.read().decode()
            return response.status, json.loads(raw_body) if raw_body else {}
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode() or "{}")


def get_json(url: str, headers: dict[str, str]) -> tuple[int, dict | list]:
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:  # nosec B310 - user-supplied test endpoint
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode() or "{}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True, help="moderation-service URL, e.g. http://localhost:8003")
    parser.add_argument("--internal-secret", required=True)
    parser.add_argument("--reviewer-token", required=True)
    parser.add_argument(
        "--subjects-file", required=True,
        help="JSON file with at least one {user_id, room_id} object; use enough users to stay below new-account limits",
    )
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--workers", type=int, default=5)
    args = parser.parse_args()
    if args.requests < 1 or args.workers < 1:
        parser.error("--requests and --workers must be positive")
    try:
        with open(args.subjects_file, encoding="utf-8") as source:
            subjects = json.load(source)
        if not isinstance(subjects, list) or not subjects or any(
            not isinstance(item, dict) or not isinstance(item.get("user_id"), str) or not isinstance(item.get("room_id"), str)
            for item in subjects
        ):
            raise ValueError
    except (OSError, ValueError, json.JSONDecodeError):
        parser.error("--subjects-file must contain a non-empty array of {user_id, room_id} objects")

    base_url = args.base_url.rstrip("/")
    for subject in subjects:
        accept_status, _ = post_json(
            f"{base_url}/internal/community/guidelines/accept",
            args.internal_secret,
            {"user_id": subject["user_id"], "guidelines_version": "community-guidelines-v1"},
        )
        if accept_status not in {200, 204}:
            print(json.dumps({"error": "could not accept guidelines", "status": accept_status, "user_id": subject["user_id"]}))
            return 1
    before_status, before_queue = get_json(
        f"{base_url}/internal/review/events", {"X-Moderation-Reviewer-Token": args.reviewer_token}
    )
    if before_status != 200 or not isinstance(before_queue, list):
        print(json.dumps({"error": "could not read review queue before test", "status": before_status}))
        return 1
    payloads = [
        {
            "url": f"{base_url}/internal/community/rooms/{subjects[index % len(subjects)]['room_id']}/posts",
            "payload": {"user_id": subjects[index % len(subjects)]["user_id"], "guidelines_version": "community-guidelines-v1", "body": f"load-test-{index}: Please send nudes"},
        }
        for index in range(args.requests)
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        results = list(executor.map(lambda item: post_json(item["url"], args.internal_secret, item["payload"]), payloads))
    held = sum(status_code == 201 and body.get("held_for_review") is True for status_code, body in results)
    failures = [(code, body) for code, body in results if code != 201]
    queue_status, queue = get_json(
        f"{base_url}/internal/review/events",
        {"X-Moderation-Reviewer-Token": args.reviewer_token},
    )
    queued = len(queue) if queue_status == 200 and isinstance(queue, list) else 0
    queue_growth = queued - len(before_queue)
    print(json.dumps({"submitted": args.requests, "held_for_review": held, "queue_before": len(before_queue), "queue_after": queued, "queue_growth": queue_growth, "queue_status": queue_status, "failures": failures}, indent=2))
    # A passing launch-gate test has enough test subjects to avoid intentional
    # per-account limits, then proves every flagged post stayed invisible and
    # created a distinct pending-review item.
    return 0 if held == args.requests and queue_growth >= held and not failures else 1


if __name__ == "__main__":
    sys.exit(main())
