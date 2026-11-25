import { describe, expect, it } from "vitest";
import { en } from "./en";
import { es } from "./es";

describe("shareMessage", () => {
  it("invites the friend to the show with its venue and day, in Spanish", () => {
    expect(es.shareMessage("Babasónicos", "Movistar Arena", "Jueves 26 de noviembre")).toBe(
      "¡Mirá este show! 🎶 Babasónicos en Movistar Arena, el jueves 26 de noviembre.",
    );
  });

  it("does the same in English, keeping the day as written", () => {
    expect(en.shareMessage("Babasónicos", "Movistar Arena", "Thursday, November 26")).toBe(
      "Check out this show! 🎶 Babasónicos at Movistar Arena, Thursday, November 26.",
    );
  });
});
