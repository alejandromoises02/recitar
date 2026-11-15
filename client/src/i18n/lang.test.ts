import { describe, expect, it } from "vitest";
import { langFromCode, storedLang } from "./lang";

describe("langFromCode", () => {
  it("is Spanish for any Spanish variant", () => {
    expect(langFromCode("es")).toBe("es");
    expect(langFromCode("ES")).toBe("es");
  });

  it("is English for every other language", () => {
    expect(langFromCode("en")).toBe("en");
    expect(langFromCode("pt")).toBe("en");
    expect(langFromCode("fr")).toBe("en");
  });

  it("falls back to Spanish when the device reports no language", () => {
    expect(langFromCode(null)).toBe("es");
    expect(langFromCode(undefined)).toBe("es");
  });
});

describe("storedLang", () => {
  it("reads a saved choice", () => {
    expect(storedLang("es")).toBe("es");
    expect(storedLang("en")).toBe("en");
  });

  it("ignores anything else, so the device language applies", () => {
    expect(storedLang(null)).toBeNull();
    expect(storedLang("")).toBeNull();
    expect(storedLang("fr")).toBeNull();
  });
});
