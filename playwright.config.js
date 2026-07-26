// @ts-check
const { defineConfig, devices } = require("@playwright/test");

/**
 * Hatlier UI smoke tests.
 * The product is a single local HTML file, so tests open it via file:// —
 * no web server, no build step.
 */
module.exports = defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    trace: "on-first-retry",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
});
