import { test, expect } from '@playwright/test';

test.describe('Graph Explorer', () => {
  test('loads the main page with three-panel layout', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h3').filter({ hasText: 'Graph' })).toBeVisible();
    await expect(page.getByRole('textbox')).toBeVisible();
    await expect(page.locator('h3').filter({ hasText: 'Details' })).toBeVisible();
  });

  test('can type in search input', async ({ page }) => {
    await page.goto('/');
    const input = page.getByRole('textbox');
    await expect(input).toHaveAttribute('placeholder', 'Search genes, proteins, diseases...');
    await input.fill('BRCA1');
    await expect(input).toHaveValue('BRCA1');
  });

  test('filter buttons are present', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('All')).toBeVisible();
    await expect(page.getByText('Genes')).toBeVisible();
    await expect(page.getByText('Proteins')).toBeVisible();
  });
});
