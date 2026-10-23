import { test, expect } from '@playwright/test';

test('Verify Login Fails with Invalid Password', async ({ page }) => {
  // Step 1: Navigate to login page
  await page.goto('https://freelance-learn-automation.vercel.app/login');
  await expect(page).toHaveURL(/.*login/);

  // Step 2: Enter valid email address
  await page.getByPlaceholder('Enter Email').fill('admin@email.com');
  await expect(page.getByPlaceholder('Enter Email')).toHaveValue('admin@email.com');

  // Step 3: Enter invalid password
  await page.getByPlaceholder('Enter Password').fill('wrong@123');
  await expect(page.getByPlaceholder('Enter Password')).toHaveValue('wrong@123');

  // Step 4: Click the Sign in button
  await page.getByRole('button', { name: 'Sign in' }).click();

  // Step 5: Verify user is still on login
  await expect(page).toHaveURL(/.*login/);
});