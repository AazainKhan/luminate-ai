/**
 * Structured Logger Reporter for Playwright
 * 
 * Provides enhanced console output with:
 * - Test category badges
 * - Timing information
 * - Clear pass/fail indicators
 * - Error summaries
 */

import type {
  FullConfig,
  FullResult,
  Reporter,
  Suite,
  TestCase,
  TestResult,
  TestStep
} from '@playwright/test/reporter';

class StructuredLogger implements Reporter {
  private startTime: number = 0;
  private passedCount = 0;
  private failedCount = 0;
  private skippedCount = 0;
  private currentSuite = '';
  
  onBegin(config: FullConfig, suite: Suite) {
    this.startTime = Date.now();
    const testCount = suite.allTests().length;
    
    console.log('\n' + '═'.repeat(70));
    console.log('  🧪 LUMINATE AI E2E TESTS');
    console.log('═'.repeat(70));
    console.log(`  📋 ${testCount} tests across ${config.projects.length} projects`);
    console.log(`  ⏱️  Started at ${new Date().toLocaleTimeString()}`);
    console.log('─'.repeat(70) + '\n');
  }
  
  onTestBegin(test: TestCase, result: TestResult) {
    const suiteName = test.parent.title;
    
    // Print suite header when entering new suite
    if (suiteName !== this.currentSuite) {
      this.currentSuite = suiteName;
      console.log(`\n📁 ${suiteName}`);
    }
  }
  
  onTestEnd(test: TestCase, result: TestResult) {
    const duration = result.duration;
    const durationStr = duration > 1000 
      ? `${(duration / 1000).toFixed(1)}s` 
      : `${duration}ms`;
    
    let statusIcon: string;
    let statusColor: string;
    
    switch (result.status) {
      case 'passed':
        statusIcon = '✅';
        this.passedCount++;
        break;
      case 'failed':
      case 'timedOut':
        statusIcon = '❌';
        this.failedCount++;
        break;
      case 'skipped':
        statusIcon = '⏭️';
        this.skippedCount++;
        break;
      case 'interrupted':
        statusIcon = '⚠️';
        this.failedCount++;
        break;
      default:
        statusIcon = '❓';
    }
    
    // Get test category from file path
    const filePath = test.location.file;
    const category = this.getCategoryBadge(filePath);
    
    console.log(`   ${statusIcon} ${test.title} ${category} (${durationStr})`);
    
    // Print error summary for failures
    if (result.status === 'failed' || result.status === 'timedOut') {
      const error = result.errors[0];
      if (error) {
        const message = error.message?.split('\n')[0] || 'Unknown error';
        console.log(`      └─ ${message.substring(0, 80)}...`);
      }
    }
  }
  
  onEnd(result: FullResult) {
    const duration = Date.now() - this.startTime;
    const durationStr = duration > 60000
      ? `${(duration / 60000).toFixed(1)}m`
      : `${(duration / 1000).toFixed(1)}s`;
    
    console.log('\n' + '─'.repeat(70));
    console.log('  📊 RESULTS SUMMARY');
    console.log('─'.repeat(70));
    console.log(`  ✅ Passed:  ${this.passedCount}`);
    console.log(`  ❌ Failed:  ${this.failedCount}`);
    console.log(`  ⏭️  Skipped: ${this.skippedCount}`);
    console.log(`  ⏱️  Duration: ${durationStr}`);
    console.log('─'.repeat(70));
    
    if (result.status === 'passed') {
      console.log('  🎉 ALL TESTS PASSED!');
    } else if (result.status === 'failed') {
      console.log('  ⚠️  SOME TESTS FAILED - Check report for details');
    } else if (result.status === 'interrupted') {
      console.log('  🛑 TEST RUN INTERRUPTED');
    }
    
    console.log('═'.repeat(70) + '\n');
  }
  
  private getCategoryBadge(filePath: string): string {
    if (filePath.includes('backend-integration')) return '[API]';
    if (filePath.includes('sidebar')) return '[SIDEBAR]';
    if (filePath.includes('user-menu')) return '[USER]';
    if (filePath.includes('folders')) return '[FOLDERS]';
    if (filePath.includes('starring')) return '[STAR]';
    if (filePath.includes('chat')) return '[CHAT]';
    if (filePath.includes('auth')) return '[AUTH]';
    if (filePath.includes('debug')) return '[DEBUG]';
    return '[UI]';
  }
}

export default StructuredLogger;
