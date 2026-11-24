import AxeBuilder from "@axe-core/playwright";
import type { Page } from "@playwright/test";
import { expect, test } from "@playwright/test";
import { withFakeApi } from "./fixtures";

const WCAG_AA = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

/** WCAG 2.2 AA violations as short lines: rule, impact, and the first elements it hit. */
async function violations(page: Page, include?: string): Promise<string[]> {
  const builder = new AxeBuilder({ page }).withTags(WCAG_AA);
  if (include) builder.include(include);
  const { violations: found } = await builder.analyze();
  return found.map((v) => `${v.id} (${v.impact}): ${v.nodes.slice(0, 3).map((n) => n.target.join(" ")).join(" | ")}`);
}

async function openHome(page: Page) {
  await withFakeApi(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 2, name: "Toda la cartelera" })).toBeVisible();
  await expect(page.getByText("Jazz Quartet").first()).toBeVisible();
}

test.beforeEach(async ({ page }) => openHome(page));

test("home has no WCAG 2.2 AA violations", async ({ page }) => {
  expect(await violations(page)).toEqual([]);
});

test("page names its language and title", async ({ page }) => {
  await expect(page.locator("html")).toHaveAttribute("lang", "es");
  await expect(page).toHaveTitle("recitAR");
});

test("one page heading, then section headings", async ({ page }) => {
  await expect(page.getByRole("heading", { level: 1 })).toHaveCount(1);
  for (const name of ["Destacados", "Recién anunciados", "Próximos", "Toda la cartelera"]) {
    await expect(page.getByRole("heading", { level: 2, name })).toBeVisible();
  }
});

test("skip link is the first stop and moves focus to the listing", async ({ page }) => {
  await page.keyboard.press("Tab");
  await expect(page.getByRole("button", { name: "Saltar a la cartelera" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#cartelera")).toBeFocused();
});

test("ticket button is a real link that opens in a new tab", async ({ page }) => {
  const link = page.getByRole("link", { name: /Ver fechas y entradas/ });
  await expect(link).toHaveAttribute("href", /^http:\/\/a11y-api\.test\/go\/[^?]+\?(v=[^&]+&)?from=(show|spotlight)$/);
  await expect(link).toHaveAttribute("target", "_blank");
  await expect(link).toHaveAttribute("rel", /noopener/);
});

test("group titles fold from the keyboard and report it", async ({ page }) => {
  const group = page.getByRole("button", { name: /Sábado 14 de noviembre/ });
  await expect(group).toHaveAttribute("aria-expanded", "true");
  await group.focus();
  await page.keyboard.press("Enter");
  await expect(group).toHaveAttribute("aria-expanded", "false");
});

test("filter chips are radios that report the choice", async ({ page }) => {
  const weekend = page.getByRole("radio", { name: "Este finde" }).first();
  await weekend.focus();
  await page.keyboard.press("Enter");
  await expect(weekend).toHaveAttribute("aria-checked", "true");
});

test("calendar dialog: no violations, Escape closes and focus returns", async ({ page }) => {
  const more = page.getByRole("button", { name: /Elegir otra fecha/ }).first();
  await more.focus();
  await page.keyboard.press("Enter");
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  expect(await violations(page, "[role=dialog]")).toEqual([]);
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await expect(more).toBeFocused();
});

test("phone filter sheet has no violations", async ({ page }, info) => {
  test.skip(info.project.name !== "phone", "the compact bar exists on phones only");
  await page.locator("#cartelera").scrollIntoViewIfNeeded();
  await page.mouse.wheel(0, 2000);
  const open = page.getByRole("button", { name: /^Filtros/ });
  await expect(open).toBeVisible();
  await open.click();
  await expect(page.getByRole("dialog")).toBeVisible();
  expect(await violations(page, "[role=dialog]")).toEqual([]);
});

test("the spotlight's Spotify sample is a named frame and the card has no violations", async ({ page }) => {
  const frame = page.locator('iframe[title="Spotify Embed"]').first();
  await expect(frame).toBeAttached();
  expect(await violations(page)).toEqual([]);
});
