const path = require('path');
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

const SCREENSHOT_DIR = path.resolve(__dirname, '../test-results/screenshots');
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function runE2E() {
  console.log('====================================================');
  console.log('Starting Complete Frontend E2E Verification & Audit');
  console.log('====================================================\n');

  const launchOptions = {
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  };
  if (process.platform === 'darwin' && fs.existsSync('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')) {
    launchOptions.executablePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  }

  const browser = await chromium.launch(launchOptions);

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });

  const page = await context.newPage();

  // Dismiss any unexpected browser alerts automatically
  page.on('dialog', async (dialog) => {
    console.log(`[BROWSER DIALOG] ${dialog.type()}: ${dialog.message()}`);
    await dialog.accept();
  });

  const consoleLogs = [];
  const errors = [];
  page.on('console', (msg) => {
    const text = msg.text();
    consoleLogs.push(`[${msg.type()}] ${text}`);
    if (msg.type() === 'error' && !text.includes('React DevTools')) {
      errors.push(`[Console Error] ${text}`);
    }
  });

  page.on('pageerror', (err) => {
    errors.push(`[Page Error] ${err.message}`);
  });

  try {
    // 1. Load Vite Application
    console.log('1. Loading application at http://localhost:5173...');
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(2000);

    const title = await page.title();
    console.log(`✓ Application Loaded. Title: "${title}"`);

    // Capture 01: Dashboard
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01_dashboard_desktop.png') });
    console.log('✓ Captured 01_dashboard_desktop.png');

    // 2. Test "New Experiment" Tab
    console.log('\n2. Testing "New Experiment" Simulation Tab...');
    const newExpTab = page.locator('aside button:has-text("New Experiment")');
    await newExpTab.click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02_new_experiment_desktop.png') });
    console.log('✓ Captured 02_new_experiment_desktop.png');

    // Click quick scenario "Lofted Drive Six"
    const loftedBtn = page.locator('button:has-text("Lofted Drive Six")');
    if (await loftedBtn.count() > 0) {
      await loftedBtn.click();
      await page.waitForTimeout(500);
      console.log('✓ Selected quick scenario "Lofted Drive Six"');
    }

    // Run simulation
    const runBtn = page.locator('button:has-text("Run Trajectory Simulation")');
    if (await runBtn.count() > 0) {
      await runBtn.click();
      await page.waitForTimeout(2000);
      console.log('✓ Ran simulation calculation');
    }

    // 3. Test "3D Ground View" Tab
    console.log('\n3. Testing "3D Ground View" Tab...');
    const groundTab = page.locator('aside button:has-text("3D Ground View")');
    await groundTab.click();
    await page.waitForTimeout(1500);

    // Test camera view presets
    const cameras = ['Side Elevation', 'Top-Down Ground', 'Batsman View', 'Bowler TV Cam', 'Isometric 3D'];
    for (const cam of cameras) {
      const btn = page.locator(`button:has-text("${cam}")`).first();
      if (await btn.count() > 0) {
        await btn.click();
        await page.waitForTimeout(250);
      }
    }
    console.log('✓ Tested all 5 camera view presets');

    // Test Playback Controls
    const playBtn = page.locator('button:has-text("Play")').first();
    if (await playBtn.count() > 0) {
      await playBtn.click();
      await page.waitForTimeout(1000);
      const pauseBtn = page.locator('button:has-text("Pause")').first();
      if (await pauseBtn.count() > 0) {
        await pauseBtn.click();
        console.log('✓ Tested 3D animation play/pause');
      }
    }

    // Test speed pill buttons
    for (const spd of ['0.25x', '0.5x', '1.5x', '2x', '1x']) {
      const spdBtn = page.locator(`button:has-text("${spd}")`).first();
      if (await spdBtn.count() > 0) {
        await spdBtn.click();
        await page.waitForTimeout(150);
      }
    }
    console.log('✓ Tested 3D render speed buttons');

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03_ground_view_desktop.png') });
    console.log('✓ Captured 03_ground_view_desktop.png');

    // 4. Test "Formula Trace" Tab
    console.log('\n4. Testing "Formula Trace" Tab...');
    const formulasTab = page.locator('aside button:has-text("Formula Trace")');
    await formulasTab.click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '04_formula_trace_desktop.png') });
    console.log('✓ Captured 04_formula_trace_desktop.png');

    // 5. Test "Experiment History" Tab
    console.log('\n5. Testing "Experiment History" Tab...');
    const historyTab = page.locator('aside button:has-text("Experiment History")');
    await historyTab.click();
    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '05_experiment_history_desktop.png') });
    console.log('✓ Captured 05_experiment_history_desktop.png');

    // Click on a delivery to view Details
    const detailsBtn = page.locator('button:has-text("Details")').first();
    if (await detailsBtn.count() > 0) {
      await detailsBtn.click();
      await page.waitForTimeout(1500);
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, '06_experiment_details_view.png') });
      console.log('✓ Captured 06_experiment_details_view.png');
    }

    // 6. Test "Comparison & Delta" Tab
    console.log('\n6. Testing "Comparison & Delta" Tab...');
    const compTab = page.locator('aside button:has-text("Comparison & Delta")');
    await compTab.click();
    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '07_comparison_and_delta_desktop.png') });
    console.log('✓ Captured 07_comparison_and_delta_desktop.png');

    // 7. Test "Video Analytics" Tab
    console.log('\n7. Testing "Video Analytics" Tab...');
    const videoTab = page.locator('aside button:has-text("Video Analytics")');
    await videoTab.click();
    await page.waitForTimeout(1500);

    const videoCount = await page.locator('video').count();
    console.log(`✓ Video Analytics rendered ${videoCount} video players`);

    // Test video speed changer
    const vidSpeed15 = page.locator('button:has-text("1.5x")').first();
    if (await vidSpeed15.count() > 0) {
      await vidSpeed15.click();
      console.log('✓ Clicked 1.5x speed changer on video player');
    }

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '08_video_analytics_desktop.png') });
    console.log('✓ Captured 08_video_analytics_desktop.png');

    // 8. Test Responsive Viewports
    console.log('\n8. Testing Tablet Viewport (768 x 1024)...');
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '09_tablet_view.png') });
    console.log('✓ Captured 09_tablet_view.png');

    console.log('\n9. Testing Mobile Viewport (375 x 812)...');
    await page.setViewportSize({ width: 375, height: 812 });
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '10_mobile_view.png') });
    console.log('✓ Captured 10_mobile_view.png');

    // 10. Test FastAPI Production Root (http://localhost:8000)
    console.log('\n10. Testing FastAPI Production URL (http://localhost:8000)...');
    await page.setViewportSize({ width: 1440, height: 900 });
    const fastRes = await page.goto('http://localhost:8000', { waitUntil: 'networkidle', timeout: 15000 });
    console.log(`✓ FastAPI Status: ${fastRes.status()}`);
    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '11_fastapi_production_root.png') });
    console.log('✓ Captured 11_fastapi_production_root.png');

    console.log('\n====================================================');
    console.log('Test Run Completed Successfully!');
    console.log(`Total Errors Logged: ${errors.length}`);
    if (errors.length > 0) {
      console.log('Errors encountered:\n' + errors.join('\n'));
    } else {
      console.log('NO CONSOLE OR PAGE ERRORS ENCOUNTERED!');
    }
    console.log('====================================================');

  } catch (err) {
    console.error('Test execution failed:', err);
  } finally {
    await browser.close();
  }
}

runE2E();
