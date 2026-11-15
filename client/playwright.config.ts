import { defineConfig, devices } from "@playwright/test";

// Accessibility checks of the web build (npm run test:a11y). The build talks to a fake API host that the
// tests answer with fixed data, so results never depend on the database or a running server.
const PORT = 8790;
export const FAKE_API = "http://a11y-api.test";

export default defineConfig({
  testDir: "./a11y",
  testMatch: "**/*.a11y.ts",
  fullyParallel: true,
  workers: 2,
  // First load downloads the whole web bundle and fonts.
  expect: { timeout: 15_000 },
  forbidOnly: !!process.env.CI,
  retries: 0,
  // Short output: one line per test, failures with the broken rule and element only.
  reporter: [["line"]],
  quiet: true,
  use: {
    baseURL: `http://localhost:${PORT}`,
    locale: "es-AR",
    reducedMotion: "reduce",
    trace: "off",
    screenshot: "off",
    video: "off",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 900 } } },
    { name: "phone", use: { ...devices["Pixel 7"] } },
  ],
  webServer: {
    // Builds into dist/ (git-ignored build output) and serves it with Expo's own static server.
    command: `npx expo export --platform web > /dev/null 2>&1 && npx expo serve --port ${PORT}`,
    env: { EXPO_PUBLIC_API_URL: FAKE_API },
    url: `http://localhost:${PORT}`,
    reuseExistingServer: false,
    timeout: 180_000,
    stdout: "ignore",
    stderr: "ignore",
  },
});
