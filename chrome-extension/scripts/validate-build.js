#!/usr/bin/env node
/**
 * Post-build validation for Chrome Extension
 * Runs after `npm run build` to ensure dist/ folder is ready for Chrome
 */

import { readFileSync, existsSync, statSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Colors for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  bold: '\x1b[1m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function error(message) {
  log(`❌ ${message}`, 'red');
}

function success(message) {
  log(`✅ ${message}`, 'green');
}

function info(message) {
  log(`ℹ️  ${message}`, 'blue');
}

function warn(message) {
  log(`⚠️  ${message}`, 'yellow');
}

// Test configuration
const distPath = resolve(__dirname, '../dist');
const manifestPath = resolve(distPath, 'manifest.json');

let hasErrors = false;
let hasWarnings = false;

log('\n' + '='.repeat(60), 'bold');
log('  Chrome Extension Build Validation', 'bold');
log('='.repeat(60) + '\n', 'bold');

// Test 1: Check if dist folder exists
info('Test 1: Checking dist folder...');
if (!existsSync(distPath)) {
  error('dist/ folder does not exist!');
  hasErrors = true;
} else {
  success('dist/ folder exists');
}

// Test 2: Check required files
info('\nTest 2: Checking required files...');
const requiredFiles = [
  'manifest.json',
  'sidepanel.html',
  'popup.html',
  'popup.js',
  'background.js',
  'sidepanel.js', // Side panel bundle
];

for (const file of requiredFiles) {
  const filePath = resolve(distPath, file);
  if (!existsSync(filePath)) {
    error(`Missing: ${file}`);
    hasErrors = true;
  } else {
    success(`Found: ${file}`);
  }
}

// Test 3: Validate manifest.json
info('\nTest 3: Validating manifest.json...');
try {
  const manifestContent = readFileSync(manifestPath, 'utf-8');
  const manifest = JSON.parse(manifestContent);

  // Check manifest version
  if (manifest.manifest_version !== 3) {
    error('manifest_version should be 3');
    hasErrors = true;
  } else {
    success('Manifest version: 3');
  }

  // Check required fields
  const requiredManifestFields = ['name', 'version', 'description', 'side_panel', 'background'];
  for (const field of requiredManifestFields) {
    if (!manifest[field]) {
      error(`Missing manifest field: ${field}`);
      hasErrors = true;
    } else {
      success(`Manifest field present: ${field}`);
    }
  }

  // Check side_panel configuration
  if (manifest.side_panel) {
    if (manifest.side_panel.default_path === 'sidepanel.html') {
      success('Side panel configured correctly');
    } else {
      error('side_panel.default_path should be sidepanel.html');
      hasErrors = true;
    }
  }

  // Check sidePanel permission
  if (manifest.permissions && manifest.permissions.includes('sidePanel')) {
    success('sidePanel permission present');
  } else {
    error('Missing sidePanel permission');
    hasErrors = true;
  }

} catch (err) {
  error(`Failed to parse manifest.json: ${err.message}`);
  hasErrors = true;
}

// Test 4: Check sidepanel.html exists
info('\nTest 4: Validating sidepanel.html...');
try {
  const sidepanelPath = resolve(distPath, 'sidepanel.html');
  if (!existsSync(sidepanelPath)) {
    error('sidepanel.html not found in dist/');
    hasErrors = true;
  } else {
    success('sidepanel.html exists');
  }
} catch (err) {
  error(`Failed to check sidepanel.html: ${err.message}`);
  hasErrors = true;
}

// Test 5: (Skip old loader.js validation)

// Test 6: Check bundle sizes
info('\nTest 6: Checking bundle sizes...');
try {
  const sidepanelPath = resolve(distPath, 'sidepanel.js');
  if (existsSync(sidepanelPath)) {
    const sidepanelStats = statSync(sidepanelPath);
    const sidepanelSizeKB = (sidepanelStats.size / 1024).toFixed(2);
    
    if (sidepanelStats.size > 300 * 1024) {
      warn(`sidepanel.js is large: ${sidepanelSizeKB} KB`);
      hasWarnings = true;
    } else {
      success(`sidepanel.js size: ${sidepanelSizeKB} KB`);
    }
  }

  const backgroundPath = resolve(distPath, 'background.js');
  if (existsSync(backgroundPath)) {
    const backgroundStats = statSync(backgroundPath);
    const backgroundSizeKB = (backgroundStats.size / 1024).toFixed(2);
    success(`background.js size: ${backgroundSizeKB} KB`);
  }

} catch (err) {
  error(`Failed to check bundle sizes: ${err.message}`);
  hasErrors = true;
}

// Summary
log('\n' + '='.repeat(60), 'bold');
if (hasErrors) {
  log('  ❌ BUILD VALIDATION FAILED', 'red');
  log('='.repeat(60) + '\n', 'bold');
  error('Extension has ERRORS and may not work correctly in Chrome!');
  error('Please fix the errors above before loading the extension.');
  process.exit(1);
} else if (hasWarnings) {
  log('  ⚠️  BUILD VALIDATION PASSED WITH WARNINGS', 'yellow');
  log('='.repeat(60) + '\n', 'bold');
  warn('Extension built successfully but has some warnings.');
  warn('It should work, but review warnings above.');
  info('\n✨ Extension ready to load in Chrome:');
  info(`   1. Go to chrome://extensions/`);
  info(`   2. Enable "Developer mode"`);
  info(`   3. Click "Load unpacked"`);
  info(`   4. Select: ${distPath}`);
  info(`   5. Navigate to: https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline`);
  info(`   6. Click the extension icon to open side panel`);
  process.exit(0);
} else {
  log('  ✅ BUILD VALIDATION PASSED', 'green');
  log('='.repeat(60) + '\n', 'bold');
  success('All tests passed! Extension is ready to load in Chrome.');
  info('\n✨ Next steps:');
  info(`   1. Go to chrome://extensions/`);
  info(`   2. Enable "Developer mode"`);
  info(`   3. Click "Load unpacked"`);
  info(`   4. Select: ${distPath}`);
  info(`   5. Navigate to: https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline`);
  info(`   6. Click the extension icon to open side panel`);  info(`   5. Navigate to: https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline`);
  process.exit(0);
}
