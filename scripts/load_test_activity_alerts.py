"""Run a controlled Phase 13 activity-alert handoff burst against staging.

This checks the authenticated notification-service boundary only. It uses
disposable recipient UUIDs supplied outside the repository and deliberately
accepts no coordinates, area cells, profiles, or contact destinations.
"""
import argparse
import concurrent.futures
import json
import sys
import time
import urllib.error
import urllib.request


def post_json(url: str, secret: str, payload: dict) -> tuple[int, float, dict]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"Content-Type": "application/json", "X-Internal-Secret": secret},
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=20) as response:  # nosec B310 - explicit staging URL
            body = response.read().decode()
            return response.status, time.perf_counter() - started, json.loads(body) if body else {}
    except urllib.error.HTTPError as error:
        body = error.read().decode()
        return error.code, time.perf_counter() - started, json.loads(body) if body else {}
    except urllib.error.URLError as error:
        return 0, time.perf_counter() - started, {"error": str(error.reason)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True, help="notification-service staging URL")
    parser.add_argument("--internal-secret", required=True)
    parser.add_argument(
        "--payload-file",
        required=True,
        help="restricted JSON object: recipient_ids, meetup_id, category; no location or contact data",
    )
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()
    if args.requests < 1 or args.workers < 1:
        parser.error("--requests and --workers must be positive")
    try:
        with open(args.payload_file, encoding="utf-8") as source:
            payload = json.load(source)
        expected = {"recipient_ids", "meetup_id", "category"}
        forbidden = {"latitude", "longitude", "area_cell", "interests", "profile", "address"}
        if (
            not isinstance(payload, dict)
            or set(payload) != expected
            or not isinstance(payload["recipient_ids"], list)
            or not payload["recipient_ids"]
            or any(not isinstance(value, str) for value in payload["recipient_ids"])
            or not isinstance(payload["meetup_id"], str)
            or not isinstance(payload["category"], str)
            or forbidden & set(payload)
        ):
            raise ValueError
    except (OSError, ValueError, json.JSONDecodeError):
        parser.error("--payload-file must be a location-free object with recipient_ids, meetup_id, and category")

    url = f"{args.base_url.rstrip('/')}/internal/activity-alerts"
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        results = list(executor.map(lambda _: post_json(url, args.internal_secret, payload), range(args.requests)))
    accepted = [(elapsed, body) for status, elapsed, body in results if status == 202]
    failures = [{"status": status, "body": body} for status, _elapsed, body in results if status != 202]
    latencies = sorted(elapsed for elapsed, _body in accepted)
    percentile_95 = latencies[max(0, int(len(latencies) * 0.95) - 1)] if latencies else None
    print(json.dumps({
        "submitted": args.requests,
        "accepted": len(accepted),
        "p95_seconds": percentile_95,
        "failures": failures,
    }, indent=2))
    return 0 if len(accepted) == args.requests else 1


if __name__ == "__main__":
    sys.exit(main())
