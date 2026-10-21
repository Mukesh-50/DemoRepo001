import { test, expect } from '@playwright/test';

test('Verify Successful Login with Valid Credentials', async ({ page }) => {
  await page.goto('https://freelance-learn-automation.vercel.app/login');
  await expect(page.getByRole('heading', { name: 'Sign In' })).toBeVisible();

  await page.fill('input[placeholder="Enter Email"]', 'admin@email.com');
  await expect(page.locator('input[placeholder="Enter Email"]')).toHaveValue('admin@email.com');

  await page.fill('input[placeholder="Enter Password"]', 'admin@123');
  await expect(page.locator('input[placeholder="Enter Password"]')).toHaveValue('admin@123');

  await page.click('button:has-text("Sign in")');
  await expect(page).toHaveURL(/^(?!.*login).*/);
});