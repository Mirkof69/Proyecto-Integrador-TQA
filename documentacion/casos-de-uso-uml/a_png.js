// Convierte diagramas/*.svg en PNG (2× de resolución) con el Chromium de Playwright.
//   node a_png.js
const fs = require('fs');
const path = require('path');
const { chromium } = require(path.join(__dirname, '..', '..', '..', '..', 'Backend', 'e2e', 'node_modules', 'playwright'));

const CHROME = 'C:/Users/Miscar/AppData/Local/ms-playwright/chromium-1228/chrome-win64/chrome.exe';
const DIR = path.join(__dirname, 'diagramas');

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME });
  const page = await browser.newPage({ deviceScaleFactor: 2 });
  for (const archivo of fs.readdirSync(DIR).filter((f) => f.endsWith('.svg'))) {
    const svg = fs.readFileSync(path.join(DIR, archivo), 'utf8');
    await page.setContent(`<html><body style="margin:0;background:#fff">${svg}</body></html>`);
    await page.locator('svg').screenshot({ path: path.join(DIR, archivo.replace('.svg', '.png')) });
    console.log('png', archivo);
  }
  await browser.close();
})();
