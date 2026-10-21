import { test, expect } from '@playwright/test';

test('Verify User Can Sign Out After Login', async ({ page }) => {
    await page.goto('https://freelance-learn-automation.vercel.app/login');
    await expect(page).toHaveURL(/login/);
    await expect(page.getByRole('heading', { name: 'Sign In' })).toBeVisible();

    await page.getByPlaceholder('Enter Email').fill('admin@email.com');
    await expect(page.getByPlaceholder('Enter Email')).toHaveValue('admin@email.com');

    await page.getByPlaceholder('Enter Password').fill('admin@123');
    await expect(page.getByPlaceholder('Enter Password')).toHaveValue('admin@123');

    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible();

    await page.getByRole('img', { name: 'menu' }).click();
    await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible();

    await page.getByRole('button', { name: 'Sign out' }).click();
    await expect(page).toHaveURL(/login/);
    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
});