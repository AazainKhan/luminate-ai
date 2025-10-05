/**
 * Background service worker for Luminate AI Chrome Extension
 * Manages side panel availability based on URL
 * 
 * Side panel is enabled ONLY on:
 * https://luminate.centennialcollege.ca/ultra/*
 * (Any page under the /ultra/ path - courses, calendar, stream, etc.)
 */

const BLACKBOARD_PATTERN = /^https:\/\/luminate\.centennialcollege\.ca\/ultra\//;

// Initialize side panel behavior
async function initializeSidePanel() {
  try {
    console.log('🔧 Initializing side panel...');
    
    // Enable side panel for any currently open Blackboard tabs
    const tabs = await chrome.tabs.query({});
    console.log(`📋 Found ${tabs.length} tabs`);
    
    for (const tab of tabs) {
      if (tab.id && tab.url) {
        const matches = BLACKBOARD_PATTERN.test(tab.url);
        console.log(`   Tab ${tab.id}: ${tab.url} - Match: ${matches}`);
        
        if (matches) {
          await chrome.sidePanel.setOptions({
            tabId: tab.id,
            enabled: true
          });
          console.log(`   ✅ Enabled side panel for tab ${tab.id}`);
        }
      }
    }
    
    console.log('✨ Side panel initialization complete');
  } catch (error) {
    console.error('❌ Failed to initialize side panel:', error);
  }
}

// Listen for extension installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('✨ Luminate AI extension installed');
  initializeSidePanel();
});

// Initialize on service worker startup (handles reloads)
console.log('🚀 Background service worker starting...');
initializeSidePanel();

// Handle extension icon clicks - manually open side panel
chrome.action.onClicked.addListener((tab) => {
  console.log('🖱️ Extension icon clicked');
  
  if (!tab.id) {
    console.error('❌ No tab ID available');
    return;
  }
  
  if (!tab.url) {
    console.error('❌ No URL available');
    return;
  }
  
  const matches = BLACKBOARD_PATTERN.test(tab.url);
  console.log(`   Current URL: ${tab.url}`);
  console.log(`   Pattern match: ${matches}`);
  
  if (matches) {
    // Must call open() synchronously within the user gesture
    // Use windowId to open in the current window
    chrome.sidePanel.open({ windowId: tab.windowId })
      .then(() => {
        console.log('✅ Side panel opened successfully');
        // Enable it after opening to ensure it stays enabled
        return chrome.sidePanel.setOptions({
          tabId: tab.id!,
          enabled: true
        });
      })
      .catch((error) => {
        console.error('❌ Failed to open side panel:', error);
      });
  } else {
    console.warn('⚠️ Cannot open side panel - not on a /ultra/ page');
    console.warn('   Please navigate to https://luminate.centennialcollege.ca/ultra/...');
  }
});

// Monitor tab updates to enable/disable side panel based on URL
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  // Only check when URL changes
  if (changeInfo.url) {
    const url = changeInfo.url;
    const matches = BLACKBOARD_PATTERN.test(url);
    
    console.log(`🔍 URL changed: ${url}`);
    console.log(`   Pattern match: ${matches}`);
    
    // Enable or disable the side panel based on URL
    if (matches) {
      // Enable side panel on Blackboard /ultra/ pages
      try {
        await chrome.sidePanel.setOptions({
          tabId: tabId,
          enabled: true
        });
        console.log(`✅ Side panel ENABLED for tab ${tabId}`);
      } catch (error) {
        console.error('❌ Failed to enable side panel:', error);
      }
    } else {
      // Disable and close side panel when leaving Blackboard
      try {
        await chrome.sidePanel.setOptions({
          tabId: tabId,
          enabled: false
        });
        console.log(`🚪 Side panel DISABLED (not on /ultra/)`);
        
        // Try to close the panel if it's open
        if (tab.windowId) {
          try {
            // Close side panel by setting path to empty or disabling globally
            await chrome.sidePanel.setOptions({
              tabId: tabId,
              enabled: false
            });
            console.log(`   🔒 Attempted to close side panel`);
          } catch (closeError) {
            // Panel might not be open, ignore
            console.log(`   ℹ️ Panel may not have been open`);
          }
        }
      } catch (error) {
        // Ignore errors when disabling
      }
    }
  }
});

// Monitor active tab changes to enable/disable based on URL
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  const tab = await chrome.tabs.get(activeInfo.tabId);
  
  if (tab.url) {
    const matches = BLACKBOARD_PATTERN.test(tab.url);
    console.log(`🔄 Tab activated: ${tab.url}`);
    console.log(`   Pattern match: ${matches}`);
    
    // Enable or disable based on current tab URL
    if (matches) {
      await chrome.sidePanel.setOptions({
        tabId: activeInfo.tabId,
        enabled: true
      });
      console.log(`✅ Side panel ENABLED for tab ${activeInfo.tabId}`);
    } else {
      await chrome.sidePanel.setOptions({
        tabId: activeInfo.tabId,
        enabled: false
      });
      console.log(`🚪 Side panel DISABLED (not on /ultra/)`);
    }
  }
});

// Export for type safety
export {};
