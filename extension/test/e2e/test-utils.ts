/**
 * Shared Test Utilities for Luminate AI E2E Tests
 * 
 * Provides reliable helper functions for common UI interactions
 * based on the actual nav-rail.tsx component structure.
 */

import { Page, expect } from '@playwright/test';

/**
 * Wait for the UI to fully settle after auth and initial render
 * Also injects 'test-mode' class to body to prevent auto-closing of menus
 */
export async function waitForUISettle(page: Page, timeout = 3000) {
  await page.waitForLoadState('domcontentloaded');
  
  // Inject test-mode class to disable click-outside behavior
  await page.evaluate(() => {
    document.body.classList.add('test-mode');
  });
  
  await page.waitForTimeout(timeout);
}

/**
 * Get the main nav rail container
 */
export function getNavRail(page: Page) {
  return page.getByTestId('nav-rail');
}

/**
 * Check if nav rail is expanded (width > 200px means expanded)
 */
export async function isNavRailExpanded(page: Page): Promise<boolean> {
  const navRail = getNavRail(page);
  const width = await navRail.evaluate((el: HTMLElement) => el.clientWidth);
  return width > 100;
}

/**
 * Expand the nav rail by clicking the expand button
 */
export async function expandNavRail(page: Page) {
  const isExpanded = await isNavRailExpanded(page);
  
  if (!isExpanded) {
    await page.getByTestId('nav-rail-expand').click();
    await page.waitForTimeout(500);
    
    // Verify it expanded
    const newWidth = await getNavRail(page).evaluate((el: HTMLElement) => el.clientWidth);
    if (newWidth < 100) {
      console.log('Warning: Nav rail did not expand after click. Width:', newWidth);
    }
  }
}

/**
 * Collapse the nav rail by clicking the collapse button
 */
export async function collapseNavRail(page: Page) {
  const isExpanded = await isNavRailExpanded(page);
  
  if (isExpanded) {
    await page.getByTestId('nav-rail-collapse').click();
    await page.waitForTimeout(500);
  }
}

/**
 * Force expand nav rail using the reliable test ID
 */
export async function forceExpandNavRail(page: Page) {
  if (await isNavRailExpanded(page)) {
    return;
  }
  
  await expandNavRail(page);
  
  if (!(await isNavRailExpanded(page))) {
    console.log('Warning: Could not expand nav rail');
  }
}

/**
 * Get the search input (only visible when expanded)
 */
export async function getSearchInput(page: Page) {
  await forceExpandNavRail(page);
  return page.locator('input[placeholder*="Search"]');
}

/**
 * Get the sort dropdown (only visible when expanded)
 */
export async function getSortDropdown(page: Page) {
  await forceExpandNavRail(page);
  return page.locator('button[role="combobox"]').first();
}

/**
 * Get the "New" button (+ button)
 */
export function getNewButton(page: Page) {
  return page.getByTestId('new-button');
}

/**
 * Click the New button and wait for dropdown
 */
export async function openNewMenu(page: Page) {
  const newButton = getNewButton(page);
  await newButton.click();
  await page.waitForTimeout(300);
}

/**
 * Get a section header by name (STARRED, RECENT, UNIVERSITY)
 */
export function getSectionHeader(page: Page, sectionName: string) {
  return page.getByTestId(`section-header-${sectionName}`);
}

/**
 * Toggle a section's collapse state
 */
export async function toggleSection(page: Page, sectionName: string) {
  await forceExpandNavRail(page);
  const header = getSectionHeader(page, sectionName);
  await header.click();
  await page.waitForTimeout(300);
}

/**
 * Get a chat/folder item by its label text
 */
export function getChatItem(page: Page, label: string) {
  return page.locator(`text="${label}"`).first();
}

/**
 * Get the star button for a chat item (visible on hover)
 * Note: This requires the item ID, which might be hard to guess in tests.
 * We'll try to find it by label first.
 */
export async function getStarButton(page: Page, itemLabel: string) {
  const item = getChatItem(page, itemLabel);
  await item.hover();
  await page.waitForTimeout(200);
  
  // Find the button with star-button- prefix in the same container
  const container = item.locator('xpath=ancestor::div[contains(@data-testid, "tree-item-")]');
  return container.locator('[data-testid^="star-button-"]');
}

/**
 * Toggle star status for an item
 */
export async function toggleItemStar(page: Page, itemLabel: string) {
  const starButton = await getStarButton(page, itemLabel);
  await starButton.click();
  await page.waitForTimeout(300);
}

/**
 * Check if an item is starred (has filled yellow star)
 */
export async function isItemStarred(page: Page, itemLabel: string) {
  const starButton = await getStarButton(page, itemLabel);
  const starIcon = starButton.locator('svg');
  const classes = await starIcon.getAttribute('class') || '';
  return classes.includes('fill-yellow') || classes.includes('text-yellow');
}

/**
 * Get the user profile/footer area
 */
export function getUserProfileButton(page: Page) {
  return page.getByTestId('user-profile-trigger');
}

/**
 * Open the user dropdown menu
 */
export async function openUserMenu(page: Page) {
  const profileButton = getUserProfileButton(page);
  await profileButton.click();
  await page.waitForTimeout(300);
}

/**
 * Get the theme submenu trigger
 */
export function getThemeMenuItem(page: Page) {
  return page.getByTestId('theme-submenu-trigger');
}

/**
 * Change theme via user menu
 */
export async function changeTheme(page: Page, theme: 'light' | 'dark' | 'system') {
  await openUserMenu(page);
  
  const themeItem = getThemeMenuItem(page);
  await themeItem.hover();
  await page.waitForTimeout(300);
  
  const themeOption = page.getByTestId(`theme-${theme}`);
  await themeOption.click();
  await page.waitForTimeout(300);
}

/**
 * Create a new chat via the + button
 */
export async function createNewChat(page: Page) {
  await forceExpandNavRail(page);
  await openNewMenu(page);
  
  const newChatOption = page.getByTestId('new-chat-item');
  await newChatOption.click();
  await page.waitForTimeout(300);
}

/**
 * Create a new folder via the + button
 */
export async function createNewFolder(page: Page) {
  await forceExpandNavRail(page);
  await openNewMenu(page);
  
  const newFolderOption = page.getByTestId('new-folder-item');
  await newFolderOption.click();
  await page.waitForTimeout(300);
}

/**
 * Type a message in the chat input and send it
 */
export async function sendChatMessage(page: Page, message: string) {
  const textarea = page.locator('textarea[placeholder*="message"], textarea[placeholder*="Ask"]').first();
  await textarea.fill(message);
  
  // Click send button
  const sendButton = page.locator('button[type="submit"], button:has(svg)').last();
  await sendButton.click();
}

/**
 * Wait for a response message to appear
 */
export async function waitForResponse(page: Page, timeout = 30000) {
  // Wait for either an assistant message or a thinking indicator
  await page.waitForSelector('[data-role="assistant"], [class*="ChatMessage"], [class*="thinking"]', { timeout });
}

/**
 * Take a debug screenshot with timestamp
 */
export async function takeDebugScreenshot(page: Page, name: string) {
  const timestamp = Date.now();
  await page.screenshot({ 
    path: `test-output/debug-screenshots/${name}-${timestamp}.png`,
    fullPage: true 
  });
}

/**
 * Log current UI state for debugging
 */
export async function logUIState(page: Page) {
  const navRail = getNavRail(page);
  const width = await navRail.evaluate((el: HTMLElement) => el.clientWidth);
  const isExpanded = width > 100;
  
  console.log('--- UI State ---');
  console.log(`Nav Rail Width: ${width}px`);
  console.log(`Nav Rail Expanded: ${isExpanded}`);
  
  if (isExpanded) {
    const searchVisible = await page.locator('input[placeholder*="Search"]').isVisible();
    const sortVisible = await page.locator('button[role="combobox"]').isVisible();
    console.log(`Search Input Visible: ${searchVisible}`);
    console.log(`Sort Dropdown Visible: ${sortVisible}`);
  }
  console.log('----------------');
}
