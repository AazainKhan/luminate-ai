/**
 * Global Teardown for Playwright Tests
 * 
 * Runs once after all tests complete
 */

import { FullConfig } from '@playwright/test';
import fs from 'fs';
import path from 'path';

async function globalTeardown(config: FullConfig) {
  console.log('\n');
  console.log('━'.repeat(60));
  console.log('🏁 GLOBAL TEARDOWN: Test Run Complete');
  console.log('━'.repeat(60));
  
  // Read and summarize results
  const resultsPath = path.join(process.cwd(), 'test-output', 'results.json');
  
  if (fs.existsSync(resultsPath)) {
    try {
      const results = JSON.parse(fs.readFileSync(resultsPath, 'utf-8'));
      
      const stats = results.stats || {};
      console.log('\n📊 Test Results Summary:');
      console.log(`   Total:    ${stats.expected || 0}`);
      console.log(`   Passed:   ${(stats.expected || 0) - (stats.unexpected || 0) - (stats.skipped || 0)}`);
      console.log(`   Failed:   ${stats.unexpected || 0}`);
      console.log(`   Skipped:  ${stats.skipped || 0}`);
      console.log(`   Flaky:    ${stats.flaky || 0}`);
      console.log(`   Duration: ${((stats.duration || 0) / 1000).toFixed(1)}s`);
      
      // List failed tests
      if (stats.unexpected > 0 && results.suites) {
        console.log('\n❌ Failed Tests:');
        const failures = findFailures(results.suites);
        failures.forEach(f => console.log(`   • ${f}`));
      }
    } catch (error) {
      console.log('   Could not parse results.json');
    }
  }
  
  console.log('\n📁 Artifacts:');
  console.log('   HTML Report: test-output/playwright-report/index.html');
  console.log('   JSON Results: test-output/results.json');
  console.log('   Screenshots: test-output/results/');
  console.log('━'.repeat(60));
  console.log('');
}

function findFailures(suites: any[], prefix = ''): string[] {
  const failures: string[] = [];
  
  for (const suite of suites) {
    const suiteName = prefix ? `${prefix} › ${suite.title}` : suite.title;
    
    if (suite.specs) {
      for (const spec of suite.specs) {
        if (spec.tests) {
          for (const test of spec.tests) {
            if (test.status === 'unexpected') {
              failures.push(`${suiteName} › ${spec.title}`);
            }
          }
        }
      }
    }
    
    if (suite.suites) {
      failures.push(...findFailures(suite.suites, suiteName));
    }
  }
  
  return failures;
}

export default globalTeardown;
