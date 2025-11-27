import type { Options } from '@wdio/types'
import path from 'path'

const extensionPath = path.join(__dirname, 'build', 'chrome-mv3-prod')

export const config: Options.Testrunner = {
  //
  // ====================
  // Runner Configuration
  // ====================
  runner: 'local',
  autoCompileOpts: {
    autoCompile: true,
    tsNodeOpts: {
      project: './tsconfig.json',
      transpileOnly: true
    }
  },

  //
  // ==================
  // Specify Test Files
  // ==================
  specs: [
    './test/e2e/**/*.spec.ts'
  ],
  exclude: [],

  //
  // ============
  // Capabilities
  // ============
  maxInstances: 1,
  capabilities: [{
    browserName: 'chrome',
    'goog:chromeOptions': {
      args: [
        `--disable-extensions-except=${extensionPath}`,
        `--load-extension=${extensionPath}`,
        '--no-sandbox',
        '--disable-gpu',
        '--disable-dev-shm-usage'
      ]
    }
  }],

  //
  // ===================
  // Test Configurations
  // ===================
  logLevel: 'info',
  bail: 0,
  baseUrl: '',
  waitforTimeout: 10000,
  connectionRetryTimeout: 120000,
  connectionRetryCount: 3,

  //
  // Test runner services
  services: [],

  //
  // Framework
  framework: 'mocha',
  reporters: ['spec'],
  mochaOpts: {
    ui: 'bdd',
    timeout: 60000
  },

  //
  // Hooks
  // =====
  /**
   * Gets executed once before all workers get launched.
   */
  onPrepare: function () {
    console.log('🚀 Starting Luminate AI E2E Tests')
    console.log(`📦 Extension path: ${extensionPath}`)
  },

  /**
   * Gets executed before a worker process is spawned
   */
  onWorkerStart: function () {
    console.log('🔧 Worker started')
  },

  /**
   * Gets executed after all workers got shut down
   */
  onComplete: function () {
    console.log('✅ All E2E tests completed')
  },
}
