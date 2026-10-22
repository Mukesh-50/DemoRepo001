import { test, expect } from '@playwright/test';

test('TC_LOGIN_003: Verify New User Signup Link Opens Signup Page', async ({ page }) => {
  // Step 1: Navigate to login page
  await page.goto('https://freelance-learn-automation.vercel.app/login');
  await expect(page).toHaveURL('https://freelance-learn-automation.vercel.app/login');

  // Step 2: Click the "New user? Signup" link
  await page.getByRole('link', { name: 'New user? Signup' }).click();

  // Step 3: Verify signup page URL
  await expect(page).toHaveURL(/.*signup.*/);
});