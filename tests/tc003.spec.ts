import { test, expect } from '@playwright/test';

test('Verify New User Signup Link Opens Signup Page', async ({ page }) => {
  await page.goto('https://freelance-learn-automation.vercel.app/login');
  await expect(page).toHaveURL('https://freelance-learn-automation.vercel.app/login');
  
  const signupLink = page.getByRole('link', { name: 'New user? Signup' });
  await signupLink.click();
  
  await expect(page).toHaveURL(/signup/);
});