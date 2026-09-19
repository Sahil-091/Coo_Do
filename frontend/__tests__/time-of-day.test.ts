import { describe, expect, test } from "vitest";
import { getTimeOfDay } from "../src/lib/checkin/time-of-day";

function atHour(hour: number): Date {
  const d = new Date(2026, 0, 15, hour, 0, 0);
  return d;
}

describe("getTimeOfDay", () => {
  test.each([
    [4, "night"],
    [5, "morning"],
    [11, "morning"],
    [12, "afternoon"],
    [16, "afternoon"],
    [17, "evening"],
    [20, "evening"],
    [21, "night"],
    [23, "night"],
    [0, "night"],
  ])("hour %i -> %s", (hour, expected) => {
    expect(getTimeOfDay(atHour(hour))).toBe(expected);
  });
});
