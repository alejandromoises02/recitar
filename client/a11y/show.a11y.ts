import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { withFakeApi } from "./fixtures";

const WCAG_AA = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

async function violations(page: import("@playwright/test").Page): Promise<string[]> {
  const { violations: found } = await new AxeBuilder({ page }).withTags(WCAG_AA).analyze();
  return found.map((v) => `${v.id} (${v.impact}): ${v.nodes.slice(0, 3).map((n) => n.target.join(" ")).join(" | ")}`);
}

test.beforeEach(async ({ page }) => withFakeApi(page));

test("a show with several dates: no WCAG 2.2 AA violations, tiles pick the date the button buys", async ({ page }) => {
  await page.goto("/show/s4");
  await expect(page.getByRole("heading", { level: 1, name: "Die Walküre" })).toBeVisible();
  expect(await violations(page)).toEqual([]);
  // Only the date tiles: the ES / EN language switch is a radio group too.
  const tiles = page.getByRole("radiogroup", { name: "Elegí una fecha" }).getByRole("radio");
  await expect(tiles).toHaveCount(3);
  await expect(tiles.first()).toHaveAttribute("aria-checked", "true");
  await tiles.nth(1).focus();
  await page.keyboard.press("Enter");
  await expect(tiles.nth(1)).toHaveAttribute("aria-checked", "true");
  const ticket = page.getByRole("link", { name: /^Entradas/ }).first();
  await expect(ticket).toHaveAttribute("href", "https://tickets.example/s4");
  await expect(ticket).toHaveAttribute("target", "_blank");
});

test("a show with one date has no tiles and a ticket link", async ({ page }) => {
  await page.goto("/show/s1");
  await expect(page.getByRole("heading", { level: 1, name: "Jazz Quartet" })).toBeVisible();
  await expect(page.getByRole("radiogroup", { name: "Elegí una fecha" })).toHaveCount(0);
  await expect(page.getByRole("link", { name: /^Entradas/ }).first()).toHaveAttribute("href", /^https:\/\//);
  expect(await violations(page)).toEqual([]);
});

test("an unknown show says so and offers the listing", async ({ page }) => {
  await page.goto("/show/nobody");
  await expect(page.getByRole("heading", { level: 1, name: "No encontramos este show" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Ver toda la cartelera" })).toBeVisible();
  expect(await violations(page)).toEqual([]);
});

test("a card on the home opens its show page", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: /La tempestad/ }).first().click();
  await expect(page).toHaveURL(/\/show\/s2$/);
  await expect(page.getByRole("heading", { level: 1, name: "La tempestad" })).toBeVisible();
});
