import { describe, expect, it } from "vitest";
import { createSession, newSessionId } from "./session";

describe("newSessionId", () => {
  it("is a random value the API accepts: 8 to 64 letters, digits or dashes", () => {
    for (let i = 0; i < 50; i++) expect(newSessionId()).toMatch(/^[A-Za-z0-9-]{8,64}$/);
  });

  it("is different every time", () => {
    expect(new Set(Array.from({ length: 50 }, () => newSessionId())).size).toBe(50);
  });
});

describe("createSession", () => {
  it("gives the same id for the whole visit", () => {
    const session = createSession(() => "abc-12345678");
    expect([session(), session(), session()]).toEqual(["abc-12345678", "abc-12345678", "abc-12345678"]);
  });

  it("does not make the id until it is asked for, and makes it once", () => {
    let made = 0;
    const session = createSession(() => `id-${++made}-12345678`);
    expect(made).toBe(0);
    session();
    session();
    expect(made).toBe(1);
  });

  it("gives another visit another id", () => {
    let n = 0;
    const next = () => `id-${++n}-12345678`;
    expect(createSession(next)()).not.toBe(createSession(next)());
  });
});
