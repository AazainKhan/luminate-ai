/**
 * Global Setup for Playwright Tests
 * 
 * Runs once before all tests to verify environment is ready
 */

import { FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('\n🚀 GLOBAL SETUP: Starting Luminate AI E2E Tests\n');
  console.log('━'.repeat(60));
  
  // Check backend health
  console.log('📡 Checking backend health...');
  try {
    const response = await fetch('http://localhost:8000/health');
    if (response.ok) {
      const data = await response.json();
      console.log(`   ✅ Backend: ${data.status}`);
    } else {
      console.log(`   ⚠️ Backend returned ${response.status}`);
    }
  } catch (error) {
    console.log('   ❌ Backend not reachable - some tests may fail');
  }
  
  // Check ChromaDB (v2 API)
  console.log('🧠 Checking ChromaDB...');
  try {
    const response = await fetch('http://localhost:8001/api/v2/heartbeat');
    if (response.ok) {
      console.log('   ✅ ChromaDB: healthy');
    } else {
      console.log(`   ⚠️ ChromaDB returned ${response.status}`);
    }
  } catch (error) {
    console.log('   ❌ ChromaDB not reachable');
  }
  
  // Check Langfuse
  console.log('📊 Checking Langfuse...');
  try {
    const response = await fetch('http://localhost:3000/api/public/health');
    if (response.ok) {
      console.log('   ✅ Langfuse: healthy');
    } else {
      console.log(`   ⚠️ Langfuse returned ${response.status}`);
    }
  } catch (error) {
    console.log('   ❌ Langfuse not reachable');
  }
  
  // Check Redis
  console.log('📦 Checking Redis...');
  try {
    // Redis doesn't have HTTP, just note it's expected to be running
    console.log('   ℹ️ Redis expected at localhost:6379');
  } catch (error) {
    // Redis check via backend health
  }
  
  console.log('━'.repeat(60));
  console.log('📋 Test Environment Summary:');
  console.log(`   Node: ${process.version}`);
  console.log(`   Platform: ${process.platform}`);
  console.log(`   CWD: ${process.cwd()}`);
  console.log('━'.repeat(60));
  console.log('');
}

export default globalSetup;
