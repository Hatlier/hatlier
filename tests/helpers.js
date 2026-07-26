// @ts-check
const path = require("path");
const { pathToFileURL } = require("url");

const APP_URL = pathToFileURL(path.resolve(__dirname, "..", "hatlier.html")).href;

/**
 * Open the app with a clean slate and start collecting console/page errors.
 * Returns an `errors` array that accumulates any error-level console messages
 * and uncaught exceptions during the test.
 */
async function openApp(page) {
  const errors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push("console: " + msg.text());
  });
  page.on("pageerror", (err) => {
    errors.push("pageerror: " + (err && err.message ? err.message : String(err)));
  });
  // Native file dialogs would otherwise hang some clicks; dismiss them.
  page.on("filechooser", (fc) => {
    fc.setFiles([]).catch(() => {});
  });
  // Skip the first-run template modal so tests are deterministic.
  await page.addInitScript(() => {
    try {
      localStorage.setItem("hatlier.seen", "1");
    } catch (e) {}
  });
  await page.goto(APP_URL);
  await page.waitForFunction(() => !!window.__hatlier);
  return errors;
}

/** Replace the current document with one containing exactly the given block types. */
async function loadBlocks(page, types, profile = "standard") {
  await page.evaluate(
    ({ types, profile }) => {
      const H = window.__hatlier;
      const doc = {
        theme: "paper",
        bg: "plain",
        font: "elegant",
        profile,
        blocks: types.map((t) => ({
          id: H.uid(),
          type: t,
          props: H.REG[t].defaults(),
        })),
      };
      H.loadDoc(doc);
    },
    { types, profile }
  );
}

async function blockTypes(page) {
  return page.evaluate(() => Object.keys(window.__hatlier.REG));
}

module.exports = { APP_URL, openApp, loadBlocks, blockTypes };
