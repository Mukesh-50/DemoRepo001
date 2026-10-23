import { test, expect } from '@playwright/test';

test('Verify User Can Sign Out After Login', async ({ page }) => {
  // Step 1: Navigate to login page
  await page.goto('https://freelance-learn-automation.vercel.app/login');
  await expect(page).toHaveURL(/.*login/);

  // Step 2: Enter valid email address
  await page.getByPlaceholder('Enter Email').fill('admin@email.com');
  await expect(page.getByPlaceholder('Enter Email')).toHaveValue('admin@email.com');

  // Step 3: Enter valid password
  await page.getByPlaceholder('Enter Password').fill('admin@123');
  await expect(page.getByPlaceholder('Enter Password')).toHaveValue('admin@123');

  // Step 4: Click the Sign in button
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible();

  // Step 5: Click the menu icon
  await page.getByRole('img', { name: 'menu' }).click();
  // Assuming menu opens, no specific element to verify

  // Step 6: Click the "Sign out" button
  await page.getByRole('button', { name: 'Sign out' }).click();

  // Step 7: Verify user is on login page
  await expect(page).toHaveURL(/.*login/);
  await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
});