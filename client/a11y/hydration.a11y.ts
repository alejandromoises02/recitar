import type { Page } from "@playwright/test";
import { expect, test } from "@playwright/test";
import { withFakeApi } from "./fixtures";

/**
 * The web build pre-renders each page; the browser's first render must match it, or React throws the
 * pre-rendered HTML away and paints the whole page again (minified React error #418 / #423 / #425).
 */
const HYDRATION = /Minified React error #(418|423|425)|[Hh]ydrat/;

async function hydrationErrors(page: Page, path: string, ready: () => Promise<void>): Promise<string[]> {
  const found: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error" && HYDRATION.test(message.text())) found.push(message.text().slice(0, 200));
  });
  page.on("pageerror", (error) => {
    if (HYDRATION.test(error.message)) found.push(error.message.slice(0, 200));
  });
  await withFakeApi(page);
  await page.goto(path);
  await ready();
  return found;
}

test("the home hydrates the pre-rendered page without a mismatch", async ({ page }) => {
  const errors = await hydrationErrors(page, "/", () => expect(page.getByText("Jazz Quartet").first()).toBeVisible());
  expect(errors).toEqual([]);
});

test("a show page hydrates the pre-rendered page without a mismatch", async ({ page }) => {
  const errors = await hydrationErrors(page, "/show/s4", () => expect(page.getByRole("heading", { level: 1, name: "Die Walküre" })).toBeVisible());
  expect(errors).toEqual([]);
});
