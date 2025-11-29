
import { test, expect, navigateToSidePanel } from './fixtures';
import { waitForUISettle, forceExpandNavRail } from './test-utils';

test.describe('History CRUD Operations', () => {
  test('should send PATCH request when renaming a folder', async ({ context, extensionId }) => {
    const page = await navigateToSidePanel(context, extensionId);
    
    // Mock the initial fetch to ensure we have an item to rename
    await page.route('**/api/history/folders', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 'folder-1', name: 'Test Folder', parent_id: null, created_at: new Date().toISOString() }
          ])
        });
    });

    // Mock the PATCH request
    let patchRequest: any = null;
    await page.route('**/api/history/folders/folder-1', async route => {
      if (route.request().method() === 'PATCH') {
        patchRequest = route.request();
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ id: 'folder-1', name: 'Renamed Folder', parent_id: null })
        });
      } else {
        await route.continue();
      }
    });

    // Reload to get the mocked data
    await page.reload();
    await waitForUISettle(page, 3000);
    await forceExpandNavRail(page);

    // Handle prompt
    page.on('dialog', async dialog => {
      await dialog.accept('Renamed Folder');
    });

    // Hover to show menu button
    const folderItem = page.locator('[data-testid^="tree-item-"]').filter({ hasText: 'Test Folder' }).first();
    await expect(folderItem).toBeVisible();
    await folderItem.hover();
    
    // Click menu button
    const menuButton = page.locator('[data-testid="menu-button-folder-1"]');
    await menuButton.click({ force: true });
    
    // Click Rename
    await page.getByText('Rename').click();

    // Wait for request
    await page.waitForTimeout(1000);
    
    expect(patchRequest).toBeTruthy();
    // The body sent by updateFolder is { name: updates.name, parent_id: updates.parentId }
    // updates.parentId is undefined in handleRename, so JSON.stringify might omit it or send undefined?
    // JSON.stringify({a: undefined}) results in {}
    // So it should be { name: 'Renamed Folder' }
    expect(patchRequest.postDataJSON()).toEqual({ name: 'Renamed Folder' });
  });
});
