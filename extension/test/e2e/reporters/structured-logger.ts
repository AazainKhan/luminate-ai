import { Reporter } from '@playwright/test/reporter';
export default class StructuredLogger implements Reporter {
    onBegin(config, suite) {
        console.log(`Starting test run with ${suite.allTests().length} tests`);
    }
}