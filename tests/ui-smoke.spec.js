// @ts-check
const { test, expect } = require("@playwright/test");
const { openApp, loadBlocks, blockTypes } = require("./helpers");

// Tool-button actions that pop a panel open (#chartedit is shared by chart & carousel).
const PANEL_ACTIONS = { chartedit: "#chartedit", caredit: "#chartedit" };
// Actions we don't click in the generic sweep (native file dialogs / destructive / no-op UI).
const SKIP_ACTIONS = new Set(["media", "herobg", "herobgclear", "dup", "del"]);

test("loads without console errors and passes the self-test", async ({ page }) => {
  const errors = await openApp(page);
  const result = await page.evaluate(() => window.__hatlierSelfTest());
  expect(result.failed, JSON.stringify(result.results.filter((r) => !r.pass), null, 2)).toBe(0);
  expect(errors, errors.join("\n")).toEqual([]);
});

test("carousel 表示 button opens the settings panel (regression)", async ({ page }) => {
  const errors = await openApp(page);
  await loadBlocks(page, ["carousel"]);
  const btn = page.locator('.bw:has(.b-carousel) [data-act="caredit"]');
  await expect(btn).toHaveCount(1);
  await btn.click();
  // The bug: the panel opened then instantly closed on the same click.
  await expect(page.locator("#chartedit")).toBeVisible();
  await expect(page.locator('#chartedit [data-car-opt="loop"]')).toBeVisible();
  expect(errors, errors.join("\n")).toEqual([]);
});

test("chart データ button opens the data panel", async ({ page }) => {
  const errors = await openApp(page);
  await loadBlocks(page, ["chart"]);
  const btn = page.locator('.bw:has(.b-chart) [data-act="chartedit"]');
  await expect(btn).toHaveCount(1);
  await btn.click();
  await expect(page.locator("#chartedit")).toBeVisible();
  expect(errors, errors.join("\n")).toEqual([]);
});

test("design panel opens and profile switching works", async ({ page }) => {
  const errors = await openApp(page);
  await page.locator("#btn-design").click();
  await expect(page.locator("#design")).toBeVisible();
  const profiles = page.locator("#design [data-profile-id]");
  await expect(profiles).toHaveCount(3);
  await page.locator('#design [data-profile-id="standard"]').click();
  const profile = await page.evaluate(() => window.__hatlier.doc.profile);
  expect(profile).toBe("standard");
  expect(errors, errors.join("\n")).toEqual([]);
});

test("carousel loop toggle requires standard profile and adds nav arrows", async ({ page }) => {
  const errors = await openApp(page);
  await loadBlocks(page, ["carousel"], "standard");
  await page.locator('.bw:has(.b-carousel) [data-act="caredit"]').click();
  await expect(page.locator("#chartedit")).toBeVisible();
  await page.locator('#chartedit [data-car-opt="loop"]').check();
  await expect(page.locator(".b-carousel .car-nav")).toHaveCount(2);
  const loop = await page.evaluate(() => window.__hatlier.doc.blocks[0].props.loop);
  expect(loop).toBe(true);
  expect(errors, errors.join("\n")).toEqual([]);
});

test("every block type inserts and renders without errors", async ({ page }) => {
  const errors = await openApp(page);
  const types = await blockTypes(page);
  await loadBlocks(page, types);
  await expect(page.locator(".bw[data-id]")).toHaveCount(types.length);
  await expect(page.locator(".bw[data-id] .blk").first()).toBeVisible();
  expect(errors, errors.join("\n")).toEqual([]);
});

test("clicking every tool button keeps the console clean and panels behave", async ({ page }) => {
  const errors = await openApp(page);
  const types = await blockTypes(page);

  for (const type of types) {
    await loadBlocks(page, [type]);
    const bw = page.locator(".bw").first();

    // Array +/- ops.
    const ops = bw.locator("[data-op]");
    for (let i = 0; i < (await ops.count()); i++) {
      await ops.nth(i).click();
    }

    // Panel / misc actions.
    const actionEls = bw.locator("[data-act]");
    const count = await actionEls.count();
    for (let i = 0; i < count; i++) {
      const el = actionEls.nth(i);
      const action = await el.getAttribute("data-act");
      if (!action || SKIP_ACTIONS.has(action)) continue;
      await el.click();
      if (PANEL_ACTIONS[action]) {
        await expect(page.locator(PANEL_ACTIONS[action])).toBeVisible();
        // Toggle closed again so the next block starts clean.
        await el.click();
      }
    }
    expect(errors, `errors while testing "${type}":\n` + errors.join("\n")).toEqual([]);
  }
});
