/**
 * Background script for Chrome Extension
 * Handles side panel management and admin routing
 */

// Open admin side panel when extension icon is clicked (for admins)
chrome.action.onClicked.addListener(async (tab) => {
  // Check if user is admin (this would need to check storage)
  // For now, we'll use the default side panel
  chrome.sidePanel.open({ windowId: tab.windowId })
})

// Set up side panel options
chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel.setOptions({
    path: "sidepanel.html",
    enabled: true,
  })
})

