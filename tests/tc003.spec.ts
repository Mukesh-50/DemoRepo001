import { test, expect } from '@playwright/test';

test('Verify New User Signup Link Opens Signup Page', async ({ page }) => {
  await page.goto('https://freelance-learn-automation.vercel.app/login');
  await expect(page.getByRole('heading', { name: 'Sign In' })).toBeVisible();
  
  await page.getByRole('link', { name: 'New user? Signup' }).click();
  await expect(page).toHaveURL(/.*signup/);
});