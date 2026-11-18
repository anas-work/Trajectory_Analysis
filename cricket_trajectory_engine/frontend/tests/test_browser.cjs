const fs = require('fs');

let chromium;
try {
  ({ chromium } = require('playwright'));
} catch (e) {
  try {
    ({ chromium } = require('/Users/anasazizkhan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright'));
  } catch (err) {
    console.error('Playwright not available directly.');
    process.exit(0);
  }
}

async function testUrl(url, screenshotName) {
  console.log(`Testing URL: ${url}...`);
  const launchOptions = {
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  };
  if (process.platform === 'darwin' && fs.existsSync('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')) {
    launchOptions.executablePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  }

  const browser = await chromium.launch(launchOptions);
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  const consoleLogs = [];
  page.on('console', msg => consoleLogs.push(`[${msg.type()}] ${msg.text()}`));
  page.on('pageerror', err => consoleLogs.push(`[PAGE_ERROR] ${err.message}`));

  try {
    const response = await page.goto(url, { waitUntil: 'networkidle', timeout: 15000 });
    console.log(`Status for ${url}: ${response ? response.status() : 'null'}`);
    await page.waitForTimeout(2000);
    const title = await page.title();
    console.log(`Page title: ${title}`);
    const rootHtml = await page.evaluate(() => document.getElementById('root')?.innerHTML || 'NO_ROOT');
    console.log(`Root HTML length: ${rootHtml.length}`);
    console.log(`Console logs:\n${consoleLogs.join('\n') || 'None'}`);

    const screenshotPath = `cricket_trajectory_engine/frontend/test-results/screenshots/${screenshotName}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`Saved screenshot to ${screenshotPath}`);
  } catch (err) {
    console.error(`Error loading ${url}:`, err.message);
    console.log(`Console logs so far:\n${consoleLogs.join('\n') || 'None'}`);
  } finally {
    await browser.close();
  }
}

async function run() {
  await testUrl('http://localhost:5173', 'vite_port_5173');
  await testUrl('http://localhost:8000', 'fastapi_port_8000');
}

run();

